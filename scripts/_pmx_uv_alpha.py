# -*- coding: utf-8 -*-
"""Sample texture alpha at the UV coordinates actually used by a PMX material."""
import struct
import sys
import os
import zlib


def load_png_rgba(path):
    d = open(path, "rb").read()
    assert d[:8] == b"\x89PNG\r\n\x1a\n"
    pos = 8
    idat = b""
    w = h = bitdepth = colortype = None
    palette = None
    trns = None
    while pos < len(d):
        ln = struct.unpack_from(">I", d, pos)[0]
        typ = d[pos + 4:pos + 8]
        body = d[pos + 8:pos + 8 + ln]
        if typ == b"IHDR":
            w, h, bitdepth, colortype = struct.unpack_from(">IIBB", body, 0)
        elif typ == b"PLTE":
            palette = body
        elif typ == b"tRNS":
            trns = body
        elif typ == b"IDAT":
            idat += body
        elif typ == b"IEND":
            break
        pos += 12 + ln
    raw = zlib.decompress(idat)
    ch = {0: 1, 2: 3, 3: 1, 4: 2, 6: 4}[colortype]
    stride = w * ch
    prev = bytearray(stride)
    out = bytearray(w * h * 4)
    p = 0
    for y in range(h):
        f = raw[p]
        p += 1
        line = bytearray(raw[p:p + stride])
        p += stride
        for i in range(stride):
            a = line[i - ch] if i >= ch else 0
            b = prev[i]
            c = prev[i - ch] if i >= ch else 0
            if f == 1:
                line[i] = (line[i] + a) & 0xFF
            elif f == 2:
                line[i] = (line[i] + b) & 0xFF
            elif f == 3:
                line[i] = (line[i] + ((a + b) >> 1)) & 0xFF
            elif f == 4:
                pp = a + b - c
                pa, pb, pc = abs(pp - a), abs(pp - b), abs(pp - c)
                pr = a if (pa <= pb and pa <= pc) else (b if pb <= pc else c)
                line[i] = (line[i] + pr) & 0xFF
        for x in range(w):
            o = (y * w + x) * 4
            if colortype == 6:
                out[o:o + 4] = line[x * 4:x * 4 + 4]
            elif colortype == 2:
                out[o:o + 3] = line[x * 3:x * 3 + 3]
                out[o + 3] = 255
            elif colortype == 0:
                out[o:o + 3] = bytes([line[x]] * 3)
                out[o + 3] = 255
            elif colortype == 4:
                out[o:o + 3] = bytes([line[x * 2]] * 3)
                out[o + 3] = line[x * 2 + 1]
            elif colortype == 3:
                idx = line[x]
                out[o:o + 3] = palette[idx * 3:idx * 3 + 3]
                out[o + 3] = trns[idx] if (trns and idx < len(trns)) else 255
        prev = line
    return w, h, out


def parse_pmx(path):
    data = open(path, "rb").read()
    pos = [4]

    def u8():
        v = data[pos[0]]; pos[0] += 1; return v

    def i32():
        v = struct.unpack_from("<i", data, pos[0])[0]; pos[0] += 4; return v

    def f32():
        v = struct.unpack_from("<f", data, pos[0])[0]; pos[0] += 4; return v

    def vec(n):
        return [f32() for _ in range(n)]

    f32()
    count = u8()
    g = [u8() for _ in range(count)]
    encoding, extra_uv, vtx_idx, tex_idx = g[0], g[1], g[2], g[3]
    enc = "utf-16-le" if encoding == 0 else "utf-8"

    def text():
        n = i32()
        s = data[pos[0]:pos[0] + n].decode(enc, errors="replace"); pos[0] += n
        return s

    def idx(size):
        v = data[pos[0]] if size == 1 else (struct.unpack_from("<H", data, pos[0])[0] if size == 2
                                            else struct.unpack_from("<i", data, pos[0])[0])
        pos[0] += size
        return v

    name = text(); text(); text(); text()
    num_vertices = i32()
    uvs = []
    for _ in range(num_vertices):
        vec(3); vec(3)
        uvs.append(vec(2))
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
    indices = [idx(vtx_idx) for _ in range(num_indices)]
    num_textures = i32()
    textures = [text() for _ in range(num_textures)]
    num_materials = i32()
    materials = []
    for _ in range(num_materials):
        mname = text(); text()
        diffuse = vec(4)
        vec(3); f32(); vec(3)
        u8()
        vec(4); f32()
        tex = idx(tex_idx); sph = idx(tex_idx); sph_mode = u8()
        toon_shared = u8()
        idx(tex_idx) if toon_shared == 0 else u8()
        text()
        nf = i32()
        materials.append((mname, diffuse, tex, sph, sph_mode, nf))
    return uvs, indices, textures, materials


def main():
    pmx, material_name = sys.argv[1], sys.argv[2]
    uvs, indices, textures, materials = parse_pmx(pmx)
    base = os.path.dirname(pmx)
    offset = 0
    target = None
    for mname, diffuse, tex, sph, sph_mode, nf in materials:
        if mname == material_name:
            target = (offset, nf, tex, diffuse)
            break
        offset += nf
    if target is None:
        print("material not found"); return
    start, nf, tex, diffuse = target
    texpath = os.path.join(base, textures[tex])
    print("material=%s alpha=%.3f texture=%s" % (material_name, diffuse[3], textures[tex]))
    if not os.path.exists(texpath):
        print("texture missing:", texpath); return
    w, h, rgba = load_png_rgba(texpath)
    print("texture size %dx%d" % (w, h))
    alphas = []
    step = max(1, nf // 3 // 5000)
    tris = list(range(start, start + nf - 2, 3 * step))
    for t in tris:
        for k in range(3):
            vi = indices[t + k]
            u, v = uvs[vi][0], uvs[vi][1]
            x = min(w - 1, max(0, int(u * w)))
            y = min(h - 1, max(0, int(v * h)))
            alphas.append(rgba[(y * w + x) * 4 + 3])
    n = len(alphas)
    zeros = sum(1 for a in alphas if a == 0)
    print("sampled texels: %d  min=%d max=%d mean=%.1f  zero=%.1f%%" %
          (n, min(alphas), max(alphas), sum(alphas) / float(n), 100.0 * zeros / n))


if __name__ == "__main__":
    main()
