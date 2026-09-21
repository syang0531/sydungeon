# -*- coding: utf-8 -*-
"""Cut a hand-built grid of cells out of a world and write them as structure pieces.

    python tools/grab_cells.py                # read the mock-up, write tools/handmade/round/

A floor plan drawn in the dev client is faster to make than a piece at a time, but it is not
a set of pieces until something cuts it up. This does that: it knows the grid the mock-up was
laid out on - cells seven across with a block of air between them, floors eight apart - takes
each cell, drops the gap, and writes a 7x7x7 piece.

Identical cells are written once. Rotations are written once too: vanilla turns a piece to
meet the jigsaw it attaches to, so a corridor that bends left is the same piece whichever way
it faces, and a floor plan that shows four of them only has one.

The result lands in tools/handmade/, the same place tools/orig_yame/ holds the first
prototype: a read-only record of what a person built, for a generator to read.
"""
import io
import os
import sys
from collections import Counter, OrderedDict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import nbt  # noqa: E402
from generate_pieces import Piece  # noqa: E402
from scan_world import NATURAL, read_box, world_folder  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, 'tools', 'handmade', 'round')

CELL = 7
# the mock-up's grid, read off the world: three cells across, eight floors, a block of air
# between every piece so the eye (and this) can tell where one ends
X0, Z0 = [-7, 1, 9], [-11, -3, 5]
Y0 = [-60 + 8 * f for f in range(8)]
RING_X = [(-12, -9), (-7, -1), (1, 7), (9, 15), (17, 20)]
RING_Z = [(-16, -13), (-11, -5), (-3, 3), (5, 11), (13, 16)]

SIDES = (('W', [(0, y, z) for y in range(1, 6) for z in range(1, 6)]),
         ('E', [(CELL - 1, y, z) for y in range(1, 6) for z in range(1, 6)]),
         ('N', [(x, y, 0) for y in range(1, 6) for x in range(1, 6)]),
         ('S', [(x, y, CELL - 1) for y in range(1, 6) for x in range(1, 6)]))


def signature(solid):
    """Which faces are open, which is what decides what a piece is."""
    out = ''
    for side, face in SIDES:
        if sum(1 for c in face if c not in solid) >= 6:
            out += side
    return out or 'X'


def rotations(cell):
    """The same piece turned four ways. Vanilla does this itself, so only one is kept."""
    out = []
    grid = dict(cell)
    for _ in range(4):
        out.append(tuple(sorted(grid.items())))
        grid = {(CELL - 1 - z, y, x): v for (x, y, z), v in grid.items()}
    return out


def take(blocks, x0, y0, z0, sx=CELL, sy=CELL, sz=CELL):
    return {(dx, dy, dz): blocks[(x0 + dx, y0 + dy, z0 + dz)]
            for dx in range(sx) for dy in range(sy) for dz in range(sz)
            if (x0 + dx, y0 + dy, z0 + dz) in blocks}


def write(name, cell, sx=CELL, sy=CELL, sz=CELL):
    piece = Piece(sx, sy, sz, 'minecraft:air')
    for (x, y, z), block in cell.items():
        piece.set(x, y, z, 'minecraft:' + block)
    if not os.path.isdir(OUT):
        os.makedirs(OUT)
    piece.write(os.path.join(OUT, name + '.nbt'))
    return piece


def main():
    world = world_folder(sys.argv[1] if len(sys.argv) > 1 else None)
    print('world: %s' % os.path.relpath(world, ROOT))
    raw = read_box(world, (-20, -64, -24), (30, 8, 24))
    blocks = {p: n for p, n in raw.items() if n not in NATURAL}

    # one entry per distinct piece, rotations folded together
    kinds = OrderedDict()
    for f, y0 in enumerate(Y0):
        for cz, z0 in enumerate(Z0):
            for cx, x0 in enumerate(X0):
                cell = take(blocks, x0, y0, z0)
                key = min(rotations(cell))
                kinds.setdefault(key, {'cell': cell, 'where': [], 'sig': signature(set(cell))})
                kinds[key]['where'].append((f + 1, cx, cz))

    print('\n72칸 -> 회전을 접으면 서로 다른 조각 %d개' % len(kinds))
    names = {}
    counts = Counter()
    for key, info in sorted(kinds.items(), key=lambda kv: -len(kv[1]['where'])):
        sig = info['sig']
        open_faces = set(sig) & set('WENS')
        base = {4: 'cross', 3: 'tee', 1: 'dead_end', 0: 'blank'}.get(len(open_faces))
        if base is None:                       # two ways out: through, or round a corner
            base = 'straight' if open_faces in ({'W', 'E'}, {'N', 'S'}) else 'corner'
        stairs = sum(1 for v in info['cell'].values() if v.endswith('_stairs'))
        if stairs > 4:
            base = 'stair_lower'
        elif stairs:
            base = 'stair_upper'
        counts[base] += 1
        name = base if counts[base] == 1 else '%s_%d' % (base, counts[base])
        names[key] = name
        print('  %-13s %-5s %3d블록  %2d곳  %s' % (name, sig, len(info['cell']),
                                                 len(info['where']), info['where'][:4]))
        write(name, info['cell'])

    # the ring: the circle round the rooms, on the same grid, mostly one course of floor
    print('\n원형 테두리 (1층, y=-60):')
    for zi, (za, zb) in enumerate(RING_Z):
        for xi, (xa, xb) in enumerate(RING_X):
            if 1 <= xi <= 3 and 1 <= zi <= 3:
                continue
            sx, sz = xb - xa + 1, zb - za + 1
            cell = take(blocks, xa, -60, za, sx, CELL, sz)
            tall = max([p[1] for p in cell], default=-1) + 1
            if not cell:
                continue
            name = 'ring_%d%d' % (xi, zi)
            print('  %-9s %2dx%dx%-2d  %3d블록  높이 %d' % (name, sx, CELL, sz, len(cell), tall))
            write(name, cell, sx, CELL, sz)
    print('\n-> %s' % os.path.relpath(OUT, ROOT))


if __name__ == '__main__':
    main()
