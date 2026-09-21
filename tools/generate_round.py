# -*- coding: utf-8 -*-
"""The round tower: the hand-built mock-up in tools/handmade/round/, made into a structure.

    python tools/generate_round.py

For now this does the one thing the mock-up left undone: the ring. It was drawn as a single
course of floor - the outline of the circle - and one segment, the west door, built to full
height. Here the twelve segments are laid back into one 29x29 plan with the block of air
between them closed, and extruded to a floor's height.

    ring_floor   29x7x29   the wall for one floor, a 21x21 hole in the middle for the rooms
    ring_ground  29x7x29   the same with the doorway, for floor one

Both are inside a structure block's forty-eight, so they are **source pieces**: build a better
one by hand in the workshop and this will stack that instead of its own (the same bargain as
tower/shaft_floor).

The plan:

    29 x 29 footprint      ring 4 blocks thick at the compass points, cut back at the corners
    21 x 21 inside         3 x 3 cells of seven, which the rooms carve
    8 floors x 7 = 56      the ring is identical on every floor; the door is floor one only
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import nbt  # noqa: E402
from generate_pieces import Piece  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HAND = os.path.join(ROOT, 'tools', 'handmade', 'round')

CELL = 7
GRID = 3                                  # rooms across
CORE = GRID * CELL                        # 21
BAND = 4                                  # how far the ring reaches past the rooms
WIDE = CORE + 2 * BAND                    # 29
FLOORS = 8
HEIGHT = FLOORS * CELL                    # 56

# where each segment of the mock-up's five-by-five grid lands once the gaps are closed
OFFSET = [0, BAND, BAND + CELL, BAND + 2 * CELL, BAND + 3 * CELL]
SPAN = [BAND, CELL, CELL, CELL, BAND]

STONE = 'minecraft:stone_bricks'
CHISELED = 'minecraft:chiseled_stone_bricks'
MOSSY = 'minecraft:mossy_stone_bricks'
AIR = 'minecraft:air'


def load(name):
    """A saved piece as {(x, y, z): (block, props)}, or None if it was never built."""
    path = os.path.join(HAND, name + '.nbt')
    if not os.path.exists(path):
        return None
    root = nbt.read(path)
    palette = [(nbt.palette_name(e), dict(nbt.palette_props(e) or {})) for e in root['palette']]
    out = {}
    for b in root['blocks']:
        x, y, z = (int(v) for v in b['pos'])
        name, props = palette[int(b['state'])]
        if name != AIR:
            out[(x, y, z)] = (name, props or None)
    return {'size': tuple(int(v) for v in root['size']), 'blocks': out}


def plan():
    """The ring's footprint, as {(x, z)} in the 29x29, read off the mock-up's twelve pieces."""
    out = set()
    for zi in range(5):
        for xi in range(5):
            if 1 <= xi <= 3 and 1 <= zi <= 3:
                continue
            piece = load('ring_%d%d' % (xi, zi))
            if piece is None:
                continue                  # a corner the circle never reaches
            for (x, y, z) in piece['blocks']:
                if y == 0:
                    out.add((OFFSET[xi] + x, OFFSET[zi] + z))
    return out


def ring_floor(door=None):
    """One floor of the ring: the footprint stood up seven blocks, banded at the top so the
    floors can be counted from outside. Deliberately plain - it is a starting point."""
    p = Piece(WIDE, CELL, WIDE, AIR)
    for x, z in plan():
        for y in range(CELL):
            n = (x * 7 + z * 11 + y * 5) % 9
            p.set(x, y, z, MOSSY if n == 0 else STONE)
        p.set(x, CELL - 1, z, CHISELED)
    if door:
        for (x, y, z), (block, props) in door['blocks'].items():
            p.set(OFFSET[0] + x, y, OFFSET[2] + z, block, props)
        for (x, y, z) in [(x, y, z) for x in range(door['size'][0])
                          for y in range(door['size'][1]) for z in range(door['size'][2])
                          if (x, y, z) not in door['blocks']]:
            p.set(OFFSET[0] + x, y, OFFSET[2] + z, AIR)
        # the mock-up's doorway was cut three tall; ours are four (CLAUDE.md section 2)
        for x in range(door['size'][0]):
            for z in range(door['size'][2]):
                at = (OFFSET[0] + x, 4, OFFSET[2] + z)
                below = [(at[0], y, at[2]) for y in (1, 2, 3)]
                if all(p.grid[c][0] == AIR for c in below):
                    p.set(at[0], at[1], at[2], AIR)
    return p


def shell():
    """The ring for all eight floors, with the door on the ground one. Its inside is left
    solid: `core` claims it and the rooms carve it (CLAUDE.md section 10)."""
    p = Piece(WIDE, HEIGHT, WIDE, STONE)
    ground, upper = ring_floor(load('ring_02')), ring_floor()
    for floor in range(FLOORS):
        source = ground if floor == 0 else upper
        for (x, y, z), (block, props) in source.grid.items():
            p.set(x, floor * CELL + y, z, block, dict(props) if props else None)
    return p


