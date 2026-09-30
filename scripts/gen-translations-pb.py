#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""从 translations.yml 重新生成 translations.pb。

Windows 构建树中 yaml-cpp 未随依赖编译，CMake 里的 emarb_yaml2pb 目标不存在，
yml 的改动不会自动进入 translations.pb。本脚本按
emapp/resources/protobuf/translation.proto 的 protobuf wire format 直接生成，
三个语言单元与 DefaultTranslator::loadFromMemory 的匹配逻辑对应：
  ja_JP -> LC_JAPANESE (1), en_US -> LC_ENGLISH (2), zh_CN -> LC_SIMPLIFIED_CHINESE (3)

用法: python scripts/gen-translations-pb.py
"""

import io
import os
import sys

import yaml

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
YML = os.path.join(ROOT, "emapp", "resources", "translations", "translations.yml")
PB = os.path.join(ROOT, "emapp", "resources", "translations", "translations.pb")

LOCALES = [("ja_JP", 1), ("en_US", 2), ("zh_CN", 3)]


def varint(value):
    out = bytearray()
    while True:
        bits = value & 0x7F
        value >>= 7
        if value:
            out.append(bits | 0x80)
        else:
            out.append(bits)
            return bytes(out)


def tag(field_number, wire_type):
    return varint((field_number << 3) | wire_type)


def string_field(field_number, text):
    data = text.encode("utf-8")
    return tag(field_number, 2) + varint(len(data)) + data


def build():
    with open(YML, encoding="utf-8") as f:
        entries = yaml.safe_load(f)
    if not isinstance(entries, list):
        sys.exit("unexpected translations.yml structure")
    units = []
    for locale, language in LOCALES:
        phrases = []
        for entry in entries:
            key = entry["key"]
            phrase = entry["phrase"]
            if locale not in phrase or phrase[locale] is None:
                sys.exit("missing %s phrase for key: %s" % (locale, key))
            phrases.append(string_field(1, key) + string_field(2, phrase[locale]))
        body = tag(1, 0) + varint(language)
        for phrase in phrases:
            body += tag(2, 2) + varint(len(phrase)) + phrase
        units.append(tag(1, 2) + varint(len(body)) + body)
    return b"".join(units)


def verify(data, expected_counts):
    """按 wire format 解回 (language -> [(id, text)]) 做自检。"""
    pos = 0
    counts = {}
    while pos < len(data):
        field, wire, pos = varint_field(data, pos)
        assert field == 1 and wire == 2, "Bundle expects field 1 (Unit)"
        length, pos = read_varint(data, pos)
        end = pos + length
        language = None
        phrases = []
        while pos < end:
            ufield, uwire, pos = varint_field(data, pos)
            if ufield == 1:
                assert uwire == 0, "Unit.language expects varint"
                language, pos = read_varint(data, pos)
            else:
                assert ufield == 2 and uwire == 2, "Unit expects fields 1/2"
                plen, pos = read_varint(data, pos)
                pend = pos + plen
                phrase_id = phrase_text = None
                while pos < pend:
                    pfield, pwire, pos = varint_field(data, pos)
                    l2, pos = read_varint(data, pos)
                    value = data[pos : pos + l2].decode("utf-8")
                    pos += l2
                    if pfield == 1:
                        phrase_id = value
                    else:
                        phrase_text = value
                assert pos == pend
                phrases.append((phrase_id, phrase_text))
        assert pos == end
        counts[language] = len(phrases)
    assert counts == expected_counts, "phrase count mismatch: %s != %s" % (counts, expected_counts)


def read_varint(data, pos):
    result = 0
    shift = 0
    while True:
        byte = data[pos]
        pos += 1
        result |= (byte & 0x7F) << shift
        if not byte & 0x80:
            return result, pos
        shift += 7


def varint_field(data, pos):
    key, pos = read_varint(data, pos)
    return key >> 3, key & 7, pos


def main():
    with open(YML, encoding="utf-8") as f:
        entries = yaml.safe_load(f)
    data = build()
    verify(data, {language: len(entries) for _, language in LOCALES})
    with open(PB, "wb") as f:
        f.write(data)
    print("wrote %s (%d bytes, %d keys x %d locales)" % (PB, len(data), len(entries), len(LOCALES)))


if __name__ == "__main__":
    main()
