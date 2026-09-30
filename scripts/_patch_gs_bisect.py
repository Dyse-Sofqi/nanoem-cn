# -*- coding: utf-8 -*-
"""Patch G_Shader fxsub copies for bisect tests (byte-level, keeps Shift-JIS)."""

gsA = "F:/_Software/nanoem-cn-diag/gsA/_GSCommon.fxsub"
gsB = "F:/_Software/nanoem-cn-diag/gsB/_GSCommon.fxsub"

# Variant A: early return right after the texture/sphere sampling, skipping the lighting math
d = open(gsA, "rb").read()
anchor = b"    float3 LightBase = {1,0,0};"
i = d.find(anchor)
assert i > 0, "A anchor not found"
d = d[:i] + b"    return Color; /* bisect A: skip lighting math */\r\n\r\n" + d[i:]
open(gsA, "wb").write(d)
print("gsA patched at", i)

# Variant B: force alpha to 1 at the end (keep everything else)
d = open(gsB, "rb").read()
# find the final "return Color;" of BufferShadow_PS: the one before the object technique block
marker = b"// \x83I\x83u\x83W\x83F\x83N\x83g\x95b\x89f"  # "// オブジェクト描画" in Shift-JIS
j = d.find(marker)
assert j > 0, "B marker not found"
k = d.rfind(b"return Color;", 0, j)
assert k > 0, "B return not found"
line_start = d.rfind(b"\n", 0, k) + 1
d = d[:line_start] + b"    Color.a = 1.0; /* bisect B: force opaque alpha */\r\n" + d[line_start:]
open(gsB, "wb").write(d)
print("gsB patched at", line_start)
