# -*- coding: utf-8 -*-
"""Dump PMX material info (alpha, flags, textures) for diagnostics."""
import struct
import sys
import os


def parse(path):
    data = open(path, "rb").read()
    pos = [0]

    def u8():
        v = data[pos[0]]
        pos[0] += 1
        return v

    def i32():
        v = struct.unpack_from("<i", data, pos[0])[0]
        pos[0] += 4
        return v

    def f32():
        v = struct.unpack_from("<f", data, pos[0])[0]
        pos[0] += 4
        return v

    def vec(n):
        return [f32() for _ in range(n)]

    assert data[:4] == b"PMX ", "not a PMX file"
    pos[0] = 4
    version = f32()
    count = u8()
    g = [u8() for _ in range(count)]
    encoding, extra_uv, vtx_idx, tex_idx, mat_idx, bone_idx, morph_idx, rb_idx = g
    enc = "utf-16-le" if encoding == 0 else "utf-8"

    def text():
        n = i32()
        s = data[pos[0]:pos[0] + n].decode(enc, errors="replace")
        pos[0] += n
        return s

    def idx(size):
        if size == 1:
            v = data[pos[0]]
            pos[0] += 1
        elif size == 2:
            v = struct.unpack_from("<H", data, pos[0])[0]
            pos[0] += 2
        else:
            v = struct.unpack_from("<i", data, pos[0])[0]
            pos[0] += 4
        return v

    name = text()
    text()
    text()
    text()
    num_vertices = i32()
    for _ in range(num_vertices):
        vec(3); vec(3); vec(2)
        for _ in range(extra_uv):
            vec(4)
        wt = u8()
        if wt == 0:
            idx(vtx_idx)
        elif wt == 1:
            idx(vtx_idx); idx(vtx_idx); f32()
        elif wt in (2, 4):
            for _ in range(4):
                idx(vtx_idx)
            vec(4)
        elif wt == 3:
            idx(vtx_idx); idx(vtx_idx); f32(); vec(3); vec(3); vec(3)
        f32()
    num_indices = i32()
    pos[0] += num_indices * vtx_idx
    num_textures = i32()
    textures = [text() for _ in range(num_textures)]
    num_materials = i32()
    rows = []
    for _ in range(num_materials):
        mname = text()
        text()
        diffuse = vec(4)
        vec(3); f32(); vec(3)
        flag = u8()
        vec(4); f32()
        tex = idx(tex_idx); sph = idx(tex_idx); sph_mode = u8()
        toon_shared = u8()
        if toon_shared == 0:
            idx(tex_idx)
        else:
            u8()
        text()
        nf = i32()
        rows.append((mname, diffuse, flag, tex, sph, sph_mode, nf))
    return dict(name=name, version=version, textures=textures, materials=rows)


if __name__ == "__main__":
    info = parse(sys.argv[1])
    texs = info["textures"]
    print("model:", info["name"], "version", info["version"])
    print("textures:", len(texs), " materials:", len(info["materials"]))
    print("%-22s %6s %5s %-30s %-26s %5s %s" % ("material", "alpha", "flag", "texture", "sphere", "sphMd", "faces"))
    for mname, diffuse, flag, tex, sph, sph_mode, nf in info["materials"]:
        t = os.path.basename(texs[tex]) if 0 <= tex < len(texs) else "-"
        s = os.path.basename(texs[sph]) if 0 <= sph < len(texs) else "-"
        print("%-22s %6.3f %5d %-30s %-26s %5d %d" % (mname[:22], diffuse[3], flag, t[:30], s[:26], sph_mode, nf))
    alphas = sorted(set(round(r[1][3], 3) for r in info["materials"]))
    print("distinct alphas:", alphas)
    print("materials with alpha < 1:", sum(1 for r in info["materials"] if r[1][3] < 0.999))
    print("sphere modes:", sorted(set(r[5] for r in info["materials"])))
