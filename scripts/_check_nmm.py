# -*- coding: utf-8 -*-
"""验证生成的 .nmm 是否满足 project.proto 所有 required 字段。"""
import sys

REQUIRED = {
    "Project": {
        5: "language", 6: "screen", 7: "timeline", 8: "audio", 9: "camera", 10: "grid",
        11: "light", 12: "physics_simulation", 13: "confirmation", 14: "axis_type",
        15: "draw_type", 16: "editing_mode", 17: "transform_type",
        18: "is_vertex_shader_skinning_enabled", 19: "is_compute_shader_skinning_enabled",
        20: "is_effect_plugin_enabled", 21: "is_multiple_bone_selection_enabled",
        22: "is_motion_merge_enabled",
    },
    "Screen": {2: "viewport", 3: "color", 4: "samples"},
    "Timeline": {2: "duration", 3: "current_frame_index", 4: "fps", 5: "is_loop_enabled"},
    "Audio": {2: "volume"},
    "Camera": {2: "angle", 3: "look_at", 4: "distance", 5: "fov", 6: "is_perspective", 7: "is_shared"},
    "Grid": {2: "visible", 3: "opacity", 4: "cell"},
    "Light": {2: "color", 3: "direction", 4: "motion_path", 5: "projective_shadow", 6: "self_shadow"},
    "ProjectiveShadow": {2: "enabled"},
    "SelfShadow": {2: "enabled", 3: "size", 4: "distance", 5: "mode"},
    "PhysicSimulation": {2: "enabled", 3: "debug"},
    "Confirmation": {1: "a", 2: "b", 3: "c", 4: "d", 5: "e"},
    "Model": {2: "name", 3: "path_for_legacy_compatibility", 4: "is_active", 5: "draw_order_index",
              6: "transform_order_index"},
}

SUBMSG = {
    ("Project", 6): "Screen", ("Project", 7): "Timeline", ("Project", 8): "Audio",
    ("Project", 9): "Camera", ("Project", 10): "Grid", ("Project", 11): "Light",
    ("Project", 12): "PhysicSimulation", ("Project", 13): "Confirmation",
    ("Project", 3): "Model", ("Light", 5): "ProjectiveShadow", ("Light", 6): "SelfShadow",
    ("Grid", 4): "Size", ("Screen", 2): "Rect", ("Screen", 3): "Color",
    ("Camera", 2): "Vector3", ("Camera", 3): "Vector3", ("Light", 2): "Color",
    ("Light", 3): "Vector3", ("Rect", 1): "Point", ("Rect", 2): "Size",
}


def read_varint(data, pos):
    result, shift = 0, 0
    while True:
        b = data[pos]
        pos += 1
        result |= (b & 0x7F) << shift
        if not b & 0x80:
            return result, pos
        shift += 7


def parse(data):
    fields = []
    pos = 0
    while pos < len(data):
        key, pos = read_varint(data, pos)
        fn, wt = key >> 3, key & 7
        if wt == 0:
            val, pos = read_varint(data, pos)
        elif wt == 1:
            val, pos = data[pos : pos + 8], pos + 8
        elif wt == 2:
            ln, pos = read_varint(data, pos)
            val, pos = data[pos : pos + ln], pos + ln
        elif wt == 5:
            val, pos = data[pos : pos + 4], pos + 4
        else:
            raise ValueError("wire %d" % wt)
        fields.append((fn, wt, val))
    return fields


def check(data, msg, path):
    fields = parse(data)
    present = {}
    for fn, wt, val in fields:
        present.setdefault(fn, []).append((wt, val))
    req = REQUIRED.get(msg, {})
    for fn, name in req.items():
        if fn not in present:
            print("MISSING %s.%s (field %d)" % (path, name, fn))
    for fn, values in present.items():
        wt, val = values[0]
        key = (msg, fn)
        if key in SUBMSG:
            check(val, SUBMSG[key], "%s.%d" % (path, fn))


data = open(sys.argv[1], "rb").read()
print("size", len(data))
check(data, "Project", "Project")
print("CHECK_DONE")
