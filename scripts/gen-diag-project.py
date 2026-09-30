# -*- coding: utf-8 -*-
"""生成用于诊断 G_Shader 效果的 nanoem .nmm 工程（protobuf wire format）。

用法: python scripts/gen-diag-project.py <模型.pmx> <效果.fx> <输出目录>
会生成 out/diag/baseline.nmm（不挂效果）与 out/diag/with_effect.nmm（全材质挂效果）。
"""

import hashlib
import os
import struct
import sys


def varint(value):
    out = bytearray()
    value &= 0xFFFFFFFFFFFFFFFF
    while True:
        b = value & 0x7F
        value >>= 7
        if value:
            out.append(b | 0x80)
        else:
            out.append(b)
            return bytes(out)


def tag(field, wire):
    return varint((field << 3) | wire)


def vfield(field, value):
    return tag(field, 0) + varint(value)


def ffield(field, value):
    return tag(field, 5) + struct.pack("<f", value)


def dfield(field, value):
    return tag(field, 1) + struct.pack("<d", value)


def sfield(field, text):
    data = text.encode("utf-8")
    return tag(field, 2) + varint(len(data)) + data


def bfield(field, value):
    return vfield(field, 1 if value else 0)


def ldelim(field, payload):
    return tag(field, 2) + varint(len(payload)) + payload


def vec3(x, y, z):
    return ffield(1, x) + ffield(2, y) + ffield(3, z)


def color(r, g, b, a):
    return ffield(1, r) + ffield(2, g) + ffield(3, b) + ffield(4, a)


def size(w, h):
    return ffield(1, w) + ffield(2, h)


def point(x, y):
    return ffield(1, x) + ffield(2, y)


def rect(x, y, w, h):
    return ldelim(1, point(x, y)) + ldelim(2, size(w, h))


def uri(absolute_path):
    return sfield(1, absolute_path)  # field 1: absolute_path


def sha256_of(path):
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).digest()


def confirmation():
    # required bools 1..5 all false
    return bfield(1, False) + bfield(2, False) + bfield(3, False) + bfield(4, False) + bfield(5, False)


def physic_simulation():
    return bfield(2, True) + vfield(3, 0) + vfield(10, 0)  # enabled=true, debug=0, mode=0


def self_shadow():
    return bfield(2, False) + ldelim(3, size(1024, 1024)) + ffield(4, 100.0) + vfield(5, 1)


def projective_shadow():
    return bfield(2, False)


def light():
    return (
        ldelim(2, color(1, 1, 1, 1))
        + ldelim(3, vec3(-0.566, -1.0, -0.424))
        + sfield(4, "")
        + ldelim(5, projective_shadow())
        + ldelim(6, self_shadow())
    )


def grid():
    return bfield(2, True) + ffield(3, 1.0) + ldelim(4, size(5, 5))


def camera():
    return (
        ldelim(2, vec3(0.5, 0.6, 0))
        + ldelim(3, vec3(0, 10, 0))
        + ffield(4, 60.0)
        + ffield(5, 30.0)
        + bfield(6, True)
        + bfield(7, False)
    )


def audio():
    return ffield(2, 1.0)


def timeline():
    return dfield(2, 0.0) + dfield(3, 0.0) + ffield(4, 30.0) + bfield(5, False)


def screen():
    return ldelim(2, rect(0, 0, 1280, 720)) + ldelim(3, color(0.15, 0.25, 0.35, 1.0)) + vfield(4, 0)


def material_attachment(fx_path):
    payload = vfield(1, 0) + sfield(2, "") + ldelim(3, uri(fx_path)) + tag(4, 2) + varint(32) + sha256_of(fx_path)
    return payload


def model_message(pmx_path, fx_path):
    msg = sfield(2, "DiagModel")
    msg += sfield(3, pmx_path)
    msg += bfield(4, True)  # is_active
    msg += vfield(5, 0)  # draw_order_index
    msg += vfield(6, 0)  # transform_order_index
    msg += vfield(8, 1)  # model_handle
    if fx_path:
        for offset in range(16):
            att = vfield(1, offset) + sfield(2, "") + ldelim(3, uri(fx_path))
            att += tag(4, 2) + varint(32) + sha256_of(fx_path)
            msg += ldelim(9, att)
    msg += ldelim(10, uri(pmx_path))
    msg += tag(11, 2) + varint(32) + sha256_of(pmx_path)
    return msg


def project_message(model_path, fx_path):
    msg = sfield(1, "")  # annotations placeholder (repeated, skip -> omit entirely)
    msg = b""
    msg += ldelim(3, model_message(model_path, fx_path))
    msg += vfield(5, 2)  # language = LC_ENGLISH
    msg += ldelim(6, screen())
    msg += ldelim(7, timeline())
    msg += ldelim(8, audio())
    msg += ldelim(9, camera())
    msg += ldelim(10, grid())
    msg += ldelim(11, light())
    msg += ldelim(12, physic_simulation())
    msg += ldelim(13, confirmation())
    msg += vfield(14, 0)  # axis_type
    msg += vfield(15, 0)  # draw_type
    msg += vfield(16, 0)  # editing_mode
    msg += vfield(17, 0)  # transform_type
    msg += bfield(18, False)  # is_vertex_shader_skinning_enabled
    msg += bfield(19, False)  # is_compute_shader_skinning_enabled
    msg += bfield(20, True)  # is_effect_plugin_enabled
    msg += bfield(21, False)  # is_multiple_bone_selection_enabled
    msg += bfield(22, False)  # is_motion_merge_enabled
    return msg


def main():
    if len(sys.argv) != 4:
        print(__doc__)
        sys.exit(1)
    model_path, fx_path, out_dir = sys.argv[1], sys.argv[2], sys.argv[3]
    os.makedirs(out_dir, exist_ok=True)
    # nanoem 内部路径分隔符统一为 '/'
    model_path = model_path.replace("\\", "/")
    fx_path = fx_path.replace("\\", "/")
    with open(os.path.join(out_dir, "baseline.nmm"), "wb") as f:
        f.write(project_message(model_path, None))
    with open(os.path.join(out_dir, "with_effect.nmm"), "wb") as f:
        f.write(project_message(model_path, fx_path))
    print("generated baseline.nmm / with_effect.nmm in", out_dir)


if __name__ == "__main__":
    main()
