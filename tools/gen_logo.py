# -*- coding: utf-8 -*-
"""Generates the CurseForge project logo.

Output: docs/curseforge/logo.png and src/main/resources/logo.png (512x512; CurseForge wants
at least 400x400). Run: python tools/gen_logo.py

Drawn from primitives, like the SY Village logo. The picture is the mod in one look: a
stone-brick archway, the prison bars across it, and a warm light coming up from below -
because every dungeon starts as a doorway in the ground that you climb down into.

Composition rule: it must survive the 64px gallery thumbnail, so there are three shapes
(arch, bars, glow) and nothing finer than a few pixels at full size.
"""
import os

from PIL import Image, ImageDraw, ImageFilter

SS = 4
S = 512 * SS

BG_TOP = (9, 11, 20)
BG_BOTTOM = (24, 28, 44)
GLOW = (255, 150, 60)
BRICK = (112, 114, 118)
BRICK_DARK = (70, 72, 76)
MORTAR = (46, 47, 52)
BRICK_LIT = (150, 146, 136)
BAR = (40, 42, 48)
BAR_HI = (120, 124, 132)
MOSS = (86, 112, 70)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = [os.path.join(ROOT, 'docs', 'curseforge', 'logo.png'),
       os.path.join(ROOT, 'src', 'main', 'resources', 'logo.png')]


def lerp(a, b, t):
    return tuple(round(x + (y - x) * t) for x, y in zip(a, b))


def background(d):
    for y in range(S):
        d.line([(0, y), (S, y)], fill=lerp(BG_TOP, BG_BOTTOM, (y / S) ** 0.8))


def glow(img, cx, cy, radius, colour, peak=1.0, squash=0.6):
    layer = Image.new('RGBA', (S, S), (0, 0, 0, 0))
    ld = ImageDraw.Draw(layer)
    steps = 120
    for i in range(steps, 0, -1):
        t = i / steps
        r = radius * t
        a = int(255 * peak * (1 - t) ** 2)
        ld.ellipse([cx - r, cy - r * squash, cx + r, cy + r * squash], fill=colour + (a,))
    layer = layer.filter(ImageFilter.GaussianBlur(S * 0.02))
    img.alpha_composite(layer)


def arch_mask(x0, y0, x1, y1):
    """A rounded-top opening: a rectangle with a semicircle on top."""
    m = Image.new('L', (S, S), 0)
    md = ImageDraw.Draw(m)
    w = x1 - x0
    md.rectangle([x0, y0 + w // 2, x1, y1], fill=255)
    md.ellipse([x0, y0, x1, y0 + w], fill=255)
    return m


def bricks(img, outer, inner):
    """Stone-brick wall filling `outer` around the `inner` opening."""
    wall = Image.new('RGBA', (S, S), (0, 0, 0, 0))
    wd = ImageDraw.Draw(wall)
    bh = S // 12
    bw = S // 6
    row = 0
    y = outer[1]
    while y < outer[3]:
        off = (bw // 2) if row % 2 else 0
        x = outer[0] - off
        while x < outer[2]:
            shade = BRICK if (row + x // bw) % 3 else BRICK_DARK
            if (row * 7 + x // bw) % 5 == 0:
                shade = lerp(shade, MOSS, 0.45)
            wd.rectangle([x, y, x + bw, y + bh], fill=shade, outline=MORTAR, width=S // 200)
            # highlight along the top edge of each brick
            wd.line([(x + S // 200, y + S // 200), (x + bw - S // 200, y + S // 200)],
                    fill=lerp(shade, BRICK_LIT, 0.5), width=S // 260)
            x += bw
        y += bh
        row += 1
    # cut the opening out of the wall
    hole = arch_mask(*inner)
    wall.putalpha(Image.composite(Image.new('L', (S, S), 0), wall.getchannel('A'), hole))
    # and keep only the wall's own outline
    frame = arch_mask(*outer)
    wall.putalpha(Image.composite(wall.getchannel('A'), Image.new('L', (S, S), 0), frame))
    img.alpha_composite(wall)


def bars(img, inner):
    d = ImageDraw.Draw(img)
    x0, y0, x1, y1 = inner
    n = 4
    step = (x1 - x0) / (n + 1)
    top = y0 + (x1 - x0) // 6
    for i in range(1, n + 1):
        x = int(x0 + step * i)
        w = S // 90
        # the third bar is broken in the middle: the way in
        segments = [(top, y1)] if i != 3 else [(top, int(y0 + (y1 - y0) * 0.42)), (int(y0 + (y1 - y0) * 0.62), y1)]
        for a, b in segments:
            d.rectangle([x - w, a, x + w, b], fill=BAR)
            d.line([(x - w // 2, a), (x - w // 2, b)], fill=BAR_HI, width=S // 300)
    # cross-bar
    d.rectangle([x0, y0 + (y1 - y0) * 0.36, x1, y0 + (y1 - y0) * 0.36 + S // 70], fill=BAR)


def main():
    img = Image.new('RGBA', (S, S))
    d = ImageDraw.Draw(img)
    background(d)

    outer = (int(S * 0.16), int(S * 0.10), int(S * 0.84), int(S * 0.98))
    inner = (int(S * 0.28), int(S * 0.24), int(S * 0.72), int(S * 0.98))

    # the light from below, inside the opening
    inside = Image.new('RGBA', (S, S), (0, 0, 0, 0))
    glow(inside, S // 2, int(S * 0.98), S * 0.42, GLOW, peak=1.0, squash=0.75)
    glow(inside, S // 2, int(S * 1.02), S * 0.22, (255, 220, 150), peak=0.9, squash=0.6)
    inside.putalpha(Image.composite(inside.getchannel('A'), Image.new('L', (S, S), 0), arch_mask(*inner)))
    # darkness at the top of the opening
    dark = Image.new('RGBA', (S, S), (0, 0, 0, 0))
    dd = ImageDraw.Draw(dark)
    dd.rectangle([0, 0, S, int(S * 0.55)], fill=(4, 5, 10, 235))
    dark.putalpha(Image.composite(dark.getchannel('A'), Image.new('L', (S, S), 0), arch_mask(*inner)))
    img.alpha_composite(dark)
    img.alpha_composite(inside)

    bricks(img, outer, inner)
    bars(img, inner)
    # a little of the light spills onto the wall
    glow(img, S // 2, int(S * 0.98), S * 0.30, GLOW, peak=0.35, squash=0.5)

    out = img.resize((512, 512), Image.LANCZOS)
    for path in OUT:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        out.save(path)
        print(path)
    out.resize((64, 64), Image.LANCZOS).save(os.path.join(ROOT, 'build', 'logo_thumb.png')) \
        if os.path.isdir(os.path.join(ROOT, 'build')) else None


if __name__ == '__main__':
    main()
