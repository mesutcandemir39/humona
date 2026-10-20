#!/usr/bin/env python3
"""Render docs/logo.svg to the PNG sizes a plugin listing and a README need.

    python3 tools/make_icons.py

A listing icon must be PNG (SVG is not accepted), so the mark lives in `docs/logo.svg` and this
redraws the same geometry with Pillow at 4x and downsamples — no rasteriser dependency, and the
two stay in step because they are the same numbers. Dev-only: Pillow is not needed to run humona.
"""
import math
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
GREEN, HILITE = (16, 185, 129), (236, 253, 245)
SS = 4


def lens(amp, n=360, pad=0):
    """The eye outline: two sine arcs meeting at the corners, as one closed polygon."""
    pts, x0, x1 = [], 24 + pad, 488 - pad
    for i in range(n + 1):
        t = i / n
        pts.append((x0 + t * (x1 - x0), 256 - amp * math.sin(math.pi * t)))
    for i in range(n + 1):
        t = 1 - i / n
        pts.append((x0 + t * (x1 - x0), 256 + amp * math.sin(math.pi * t)))
    return pts


def render(size, bg=None):
    from PIL import Image, ImageDraw
    S = size * SS
    k = S / 512.0
    img = Image.new("RGBA", (S, S), bg or (0, 0, 0, 0))

    def mask(points):
        m = Image.new("L", (S, S), 0)
        ImageDraw.Draw(m).polygon([(x * k, y * k) for x, y in points], fill=255)
        return m

    outer, inner = mask(lens(120)), mask(lens(97, pad=17))
    ring = Image.composite(outer, Image.new("L", (S, S), 0), Image.eval(inner, lambda v: 255 - v))
    img.paste(Image.new("RGBA", (S, S), GREEN + (255,)), (0, 0), ring)

    facts = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    fd = ImageDraw.Draw(facts)
    for y, segs, op in ((196, [(118, 58), (336, 58)], .45), (224, [(150, 54), (308, 54)], .7),
                        (256, [(96, 46), (370, 46)], .35), (288, [(150, 54), (308, 54)], .7),
                        (316, [(118, 58), (336, 58)], .45)):
        for x, w in segs:
            fd.rounded_rectangle([x * k, (y - 5) * k, (x + w) * k, (y + 5) * k], radius=5 * k,
                                 fill=GREEN + (int(255 * op),))
    img.paste(facts, (0, 0), Image.composite(facts.split()[3], Image.new("L", (S, S), 0), inner))

    d = ImageDraw.Draw(img)
    r = c = 62 * k, 256 * k
    r, c = 62 * k, 256 * k
    d.ellipse([c - r, c - r, c + r, c + r], fill=GREEN + (255,))
    hr, h = 15 * k, 234 * k
    d.ellipse([h - hr, h - hr, h + hr, h + hr], fill=HILITE + (235,))
    return img.resize((size, size), Image.LANCZOS)


def main():
    try:
        import PIL  # noqa: F401
    except ImportError:
        print("this dev tool needs Pillow:  pip install pillow", file=sys.stderr)
        return 1
    render(1024, (10, 15, 13, 255)).save(REPO / ".claude-plugin" / "icon.png", optimize=True)
    render(512).save(REPO / "docs" / "logo-512.png", optimize=True)
    print("wrote .claude-plugin/icon.png and docs/logo-512.png")
    return 0


if __name__ == "__main__":
    sys.exit(main())
