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

Three things the mock-up does that the pieces must not:

  - cells whose shared walls were cut away are one room, not four. They are stitched back
    into a single piece (the gap between them closes too)
  - the stair climbs through two floors, so its two cells are stitched into one 7x14x7
  - doorways were cut three tall; the mod's are three wide by four. Every doorway is opened
    one course further up on the way out

A cell that is still the plain hollow box was never filled in, and is dropped.

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


TURN = {'west': 'north', 'north': 'east', 'east': 'south', 'south': 'west'}


def turned(props):
    if not props or 'facing' not in props or props['facing'] not in TURN:
        return props
    out = dict(props)
    out['facing'] = TURN[out['facing']]
    return out


def rotations(cell):
    """The same piece turned four ways. Vanilla does this itself, so only one is kept.

    A block's own facing turns with it, or a staircase compares equal to itself pointing the
    wrong way and the wrong one of the two gets written out."""
    out = []
    grid = dict(cell)
    for _ in range(4):
        out.append(tuple(sorted(grid.items())))
        grid = {(CELL - 1 - z, y, x): (v[0], turned(v[1])) for (x, y, z), v in grid.items()}
    return out


def take(blocks, x0, y0, z0, sx=CELL, sy=CELL, sz=CELL):
    return {(dx, dy, dz): blocks[(x0 + dx, y0 + dy, z0 + dz)]
            for dx in range(sx) for dy in range(sy) for dz in range(sz)
            if (x0 + dx, y0 + dy, z0 + dz) in blocks}


def write(name, cell, sx=CELL, sy=CELL, sz=CELL):
    piece = Piece(sx, sy, sz, 'minecraft:air')
    for (x, y, z), (block, props) in cell.items():
        piece.set(x, y, z, 'minecraft:' + block, props)
    if not os.path.isdir(OUT):
        os.makedirs(OUT)
    piece.write(os.path.join(OUT, name + '.nbt'))
    return piece


MERGED = [(2, (0, 0), 2, 2)]        # floor 2's north-west four cells are one room
STAIRWAY = (1, (2, 1), 2)           # floor 1 cell (2,1) and the floor above it are one stair
BLANK = 218                         # a hollow 7-cube: a cell nobody got round to filling in


def widen_doors(cell, sx, sy, sz):
    """The mock-up cut doorways three tall; ours are four (CLAUDE.md section 2)."""
    faces = {'W': [(0, z) for z in range(sz)], 'E': [(sx - 1, z) for z in range(sz)],
             'N': [(x, 0) for x in range(sx)], 'S': [(x, sz - 1) for x in range(sx)]}
    for side, line in faces.items():
        for a, b in line:
            at = (lambda y: (a, y, b)) if side in 'WE' else (lambda y: (a, y, b))
            if all(at(y) not in cell for y in (1, 2, 3)) and at(4) in cell:
                del cell[at(4)]
    return cell


def stitch(blocks, floor, cell, wide, deep=1, tall=1):
    """Several cells of the mock-up as one piece, with the block of air between them closed."""
    cx, cz = cell
    out = {}
    for fz in range(deep if tall == 1 else 1):
        pass
    for ty in range(tall):
        for tz in range(deep):
            for tx in range(wide):
                x0, z0 = X0[cx + tx], Z0[cz + tz]
                y0 = Y0[floor - 1 + ty]
                for (dx, dy, dz), block in take(blocks, x0, y0, z0).items():
                    out[(tx * CELL + dx, ty * CELL + dy, tz * CELL + dz)] = block
    return out


def main():
    world = world_folder(sys.argv[1] if len(sys.argv) > 1 else None)
    print('world: %s' % os.path.relpath(world, ROOT))
    raw = read_box(world, (-20, -64, -24), (30, 8, 24))
    blocks = {p: v for p, v in raw.items() if v[0] not in NATURAL}

    skip = set()
    for floor, (cx, cz), wide, deep in MERGED:
        for tx in range(wide):
            for tz in range(deep):
                skip.add((floor, cx + tx, cz + tz))
    sf, (scx, scz), stall = STAIRWAY
    for ty in range(stall):
        skip.add((sf + ty, scx, scz))

    kinds = OrderedDict()
    for f, y0 in enumerate(Y0):
        for cz, z0 in enumerate(Z0):
            for cx, x0 in enumerate(X0):
                if (f + 1, cx, cz) in skip:
                    continue
                cell = take(blocks, x0, y0, z0)
                if len(cell) == BLANK:
                    continue                    # never filled in, not a piece
                key = min(rotations(cell))
                kinds.setdefault(key, {'cell': cell, 'where': [], 'sig': signature(set(cell))})
                kinds[key]['where'].append((f + 1, cx, cz))

    print('\n손으로 지은 칸 -> 회전을 접으면 조각 %d개' % len(kinds))
    counts = Counter()
    for key, info in sorted(kinds.items(), key=lambda kv: -len(kv[1]['where'])):
        open_faces = set(info['sig']) & set('WENS')
        base = {4: 'cross', 3: 'tee', 1: 'dead_end', 0: 'sealed'}.get(len(open_faces))
        if base is None:
            base = 'straight' if open_faces in ({'W', 'E'}, {'N', 'S'}) else 'corner'
        counts[base] += 1
        name = base if counts[base] == 1 else '%s_%d' % (base, counts[base])
        cell = widen_doors(dict(info['cell']), CELL, CELL, CELL)
        print('  %-11s %-5s %3d블록  %2d곳  %s' % (name, info['sig'], len(cell),
                                                 len(info['where']), info['where'][:4]))
        write(name, cell)

    for floor, cell, wide, deep in MERGED:
        big = stitch(blocks, floor, cell, wide, deep)
        big = widen_doors(big, wide * CELL, CELL, deep * CELL)
        print('\n%-11s %dx%dx%-2d %3d블록  %d층 %s에서 네 칸이 한 방'
              % ('room4', wide * CELL, CELL, deep * CELL, len(big), floor, cell))
        write('room4', big, wide * CELL, CELL, deep * CELL)

    stairs = stitch(blocks, sf, (scx, scz), 1, 1, stall)
    stairs = widen_doors(stairs, CELL, stall * CELL, CELL)
    print('  %-11s %dx%dx%-2d %3d블록  %d층 %s에서 두 층을 오른다'
          % ('stair', CELL, stall * CELL, CELL, len(stairs), sf, (scx, scz)))
    write('stair', stairs, CELL, stall * CELL, CELL)

    print('\n원형 테두리 (1층, y=-60):')
    for zi, (za, zb) in enumerate(RING_Z):
        for xi, (xa, xb) in enumerate(RING_X):
            if 1 <= xi <= 3 and 1 <= zi <= 3:
                continue
            sx, sz = xb - xa + 1, zb - za + 1
            cell = take(blocks, xa, -60, za, sx, CELL, sz)
            if not cell:
                continue
            tall = max(p[1] for p in cell) + 1
            name = 'ring_%d%d' % (xi, zi)
            print('  %-9s %2dx%dx%-2d  %3d블록  높이 %d%s'
                  % (name, sx, CELL, sz, len(cell), tall, '   <- 입구' if tall > 1 else ''))
            write(name, cell, sx, CELL, sz)
    print('\n-> %s' % os.path.relpath(OUT, ROOT))


if __name__ == '__main__':
    main()
