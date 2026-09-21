# -*- coding: utf-8 -*-
"""The Wizard's Tower: a slender shaft on a plinth, under a copper roof.

    python tools/generate_tower.py        (or through make_pieces.py)

Writes data/sydungeon/structure/tower/*.nbt and the pools that join them.

THE SHAPE
    plinth  39x 7x39   floor 1       core_base  35x 7x35   5x5 rooms
    shaft   25x49x25   floors 2..8   core_shaft 21x49x21   3x3 rooms
    crown   39x 9x39   the terrace, hanging seven blocks out past the shaft on every side
    roof    39x21x39   tapers 39 -> 1, oxidized copper, a lightning rod on the point

The crown carries its own room rather than handing one to a core: there is nothing up there
for a maze to do, and an open gallery is the point of the shape.

Four shells stack on one another through single vertical anchors, the way the pyramid's three
skins do, and each hands its own interior to a core that fences everything inside it
(CLAUDE.md section 10). The shells are stacked rather than made one box because the tower is
not the same width all the way up, and that taper is the whole point of the silhouette.

WHAT IS GUARANTEED
Floors 2 to 8 are joined by stair rooms, not ladders, and the stair stands in a different
cell on every floor, so each floor has to be crossed to find the way up:

    floor 2  land (1,1) -> stair (1,0)      floor 6  land (1,1) -> stair (0,1)
    floor 3  land (1,0) -> stair (2,0)      floor 7  land (0,1) -> stair (0,2)
    floor 4  land (2,0) -> stair (2,1)      floor 8  land (0,2) -> the crown stair
    floor 5  land (2,1) -> stair (1,1)

Each landing is placed by the stair below it and each stair by its landing, all single-element
pools, so the climb cannot break. The library hangs off floor 3's landing and the sanctum off
floor 7's, both against the route. On top of that the maze pool carries a stair of its own, so
most towers have short cuts as well, and those are different every time.

The two ends of the climb cross a shell boundary, where a jigsaw cannot reach, so they are cut
into both pieces from one table of coordinates instead (CLAUDE.md section 11): the great stair
from the entrance hall up into floor 2, and the stair from floor 8 out onto the terrace.

WHY EACH LINK HAS ITS OWN CONNECTOR NAME
Vanilla enters a child through *any* of its jigsaws whose name matches, trying all four
rotations. The castle this replaces gave several jigsaws on one piece the same name, so half
the time the generator came in through the wrong one and the chain ran backwards: the boss
room ended up with no way in at all. Every deterministically placed piece here carries exactly
one jigsaw with the name its parent targets, and verify() counts them.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
import nbt  # noqa: E402
from generate_pieces import Piece  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DST = os.path.join(ROOT, 'src', 'main', 'resources', 'data', 'sydungeon', 'structure', 'tower')
POOL_JSON = os.path.join(ROOT, 'src', 'main', 'resources', 'data', 'sydungeon', 'worldgen',
                         'template_pool', 'tower')

NS = 'sydungeon'
DOOR = NS + ':tow_door'        # the maze's connector, and only the maze's
RISER = NS + ':tow_riser'      # a climb piece's way in
ANCHOR = NS + ':tow_anchor'    # a named room's or a shell's way in
PLACER = NS + ':tow_placer'    # a jigsaw whose job is to put a fixed piece somewhere; it is
                               # not a door, so it is exempt from the on-a-face check
EMPTY = 'minecraft:empty'

# --------------------------------------------------------------------------------- geometry
CELL = 7
WALL = 2
PRIORITY = 20

BASE_GRID, SHAFT_GRID = 5, 3
BASE = BASE_GRID * CELL                    # 35
SHAFT = SHAFT_GRID * CELL                  # 21
BASE_W = BASE + 2 * WALL                   # 39
SHAFT_W = SHAFT + 2 * WALL                 # 25
INSET = (BASE_W - SHAFT_W) // 2            # 7, how far the crown hangs out past the shaft

FLOORS = 7                                 # floors 2..8, the ones inside the shaft
BASE_H = CELL                              # y 0..6
SHAFT_H = FLOORS * CELL                    # y 7..55
CROWN_H = CELL + 2                         # y 56..64: corbels, deck, gallery, plate
ROOF_H = (BASE_W - 1) // 2 + 2             # y 65..85, tapering two to a course

BASE_Y = 0
SHAFT_Y = BASE_Y + BASE_H
CROWN_Y = SHAFT_Y + SHAFT_H
ROOF_Y = CROWN_Y + CROWN_H

AT = {
    'base': (0, BASE_Y, 0),
    'shaft': (INSET, SHAFT_Y, INSET),
    'crown': (0, CROWN_Y, 0),
    'roof': (0, ROOF_Y, 0),
    'core_base': (WALL, BASE_Y, WALL),
    'core_shaft': (INSET + WALL, SHAFT_Y, INSET + WALL),
}
SIZE = {
    'base': (BASE_W, BASE_H, BASE_W),
    'shaft': (SHAFT_W, SHAFT_H, SHAFT_W),
    'crown': (BASE_W, CROWN_H, BASE_W),
    'roof': (BASE_W, ROOF_H, BASE_W),
    'core_base': (BASE, BASE_H, BASE),
    'core_shaft': (SHAFT, SHAFT_H, SHAFT),
}

# The climb, floor by floor: the cell you arrive in and the cell the stair up stands in.
#
# The stair is a spiral inside a single 7x7x7 cell. Its top steps come out through its own
# ceiling, so you surface in the cell directly above it - which is why every floor's landing
# cell is the floor below's stair cell, and why a stair only has to find one free cell on one
# floor. A stair room two floors tall would need two free cells in a row, and on the floors
# the library and the sanctum eat there are not two to spare.
ROUTE = {
    2: ((1, 1), (1, 0)),
    3: ((1, 0), (2, 0)),
    4: ((2, 0), (2, 1)),
    5: ((2, 1), (1, 1)),
    6: ((1, 1), (0, 1)),
    7: ((0, 1), (0, 2)),
    8: ((0, 2), None),                     # floor 8 climbs to the terrace through the shell
}
FIRST_FLOOR, LAST_FLOOR = 2, 8

# The two big rooms are 2x2 cells and two floors tall, and each one is entered straight off a
# landing, never through the maze.
#   name: (floor, north-west cell, the landing face that opens into it)
BIG = {
    'library': (3, (0, 1), 'south'),
    'sanctum': (7, (1, 1), 'east'),
}
BIG_SIZE = 2 * CELL                        # 14
for _name, (_floor, _cell, _face) in BIG.items():
    AT[_name] = (AT['core_shaft'][0] + _cell[0] * CELL,
                 AT['core_shaft'][1] + (_floor - FIRST_FLOOR) * CELL,
                 AT['core_shaft'][2] + _cell[1] * CELL)
    SIZE[_name] = (BIG_SIZE, BIG_SIZE, BIG_SIZE)

# Floor one, in core_base's own 5x5 grid. The way in and the great stair are fixed pieces on
# a chain of single-element pools, so the door always leads somewhere and the stair is always
# found: hall -> corridor -> great stair, and the great stair sits directly under floor two's
# landing so the two can be cut to meet.
HALL_CELL = (0, 2)
CORR_CELL = (1, 2)
GREAT_CELL = (2, 2)

STEP = {'north': (0, -1), 'south': (0, 1), 'west': (-1, 0), 'east': (1, 0)}
OPPOSITE = {'north': 'south', 'south': 'north', 'west': 'east', 'east': 'west'}

# --------------------------------------------------------------------------------- palette
STONE = 'minecraft:stone_bricks'
MOSSY = 'minecraft:mossy_stone_bricks'
CHISELED = 'minecraft:chiseled_stone_bricks'
COBBLE = 'minecraft:mossy_cobblestone'
DEEP = 'minecraft:deepslate_bricks'
POLISHED = 'minecraft:polished_deepslate'
COPPER = 'minecraft:oxidized_copper'
COPPER_CUT = 'minecraft:oxidized_cut_copper'
COPPER_STAIR = 'minecraft:oxidized_cut_copper_stairs'
COPPER_SLAB = 'minecraft:oxidized_cut_copper_slab'
COPPER_CHISELED = 'minecraft:oxidized_chiseled_copper'
COPPER_GRATE = 'minecraft:oxidized_copper_grate'
COPPER_CHAIN = 'minecraft:oxidized_copper_chain'
ROD = 'minecraft:oxidized_lightning_rod'
WOOD = 'minecraft:spruce_planks'
WOOD_SLAB = 'minecraft:spruce_slab'
WOOD_STAIR = 'minecraft:spruce_stairs'
FENCE = 'minecraft:spruce_fence'
LOG = 'minecraft:spruce_log'
BOOKSHELF = 'minecraft:bookshelf'
GLASS = 'minecraft:glass_pane'
STAIR = 'minecraft:stone_brick_stairs'
VINE = 'minecraft:vine'
AIR = 'minecraft:air'

PANE = {'north': 'false', 'south': 'false', 'east': 'false', 'west': 'false',
        'waterlogged': 'false'}
BARS = {'north': 'true', 'south': 'true', 'east': 'true', 'west': 'true',
        'waterlogged': 'false'}
RAIL = {'north': 'true', 'south': 'true', 'east': 'true', 'west': 'true',
        'waterlogged': 'false'}
HANGING = {'hanging': 'true', 'waterlogged': 'false'}
STANDING = {'hanging': 'false', 'waterlogged': 'false'}


def stair_props(facing, half='bottom', shape='straight'):
    return {'facing': facing, 'half': half, 'shape': shape, 'waterlogged': 'false'}


def slab_props(half='bottom'):
    return {'type': half, 'waterlogged': 'false'}


def vine_props(side):
    """A vine holds on to the block on the named side of it."""
    props = {'north': 'false', 'south': 'false', 'east': 'false', 'west': 'false',
             'up': 'false'}
    props[side] = 'true'
    return props


POOL = {k: NS + ':tower/' + k for k in
        ['passages', 'caps', 'core_base', 'core_shaft', 'shaft', 'crown', 'roof',
         'library', 'sanctum', 'alchemy', 'hall', 'corridor', 'great_stair'] +
        ['land_%d' % f for f in ROUTE] +
        ['stair_%d' % f for f in ROUTE if ROUTE[f][1] is not None]}

TRIAL_STATE = {'trial_spawner_state': 'inactive', 'ominous': 'false'}
ANY_LIGHT = {'block_light_limit': {'min_inclusive': nbt.Int(0), 'max_inclusive': nbt.Int(15)}}


def trial_spawner(config):
    return {'id': 'minecraft:trial_spawner',
            'normal_config': NS + ':tower/' + config,
            'ominous_config': NS + ':tower/' + config,
            'target_cooldown_length': nbt.Int(2_000_000_000),
            'required_player_range': nbt.Int(14)}


def mob_spawner(entity, count=2):
    return {'id': 'minecraft:mob_spawner',
            'SpawnData': {'entity': {'id': entity}, 'custom_spawn_rules': ANY_LIGHT},
            'Delay': nbt.Short(20), 'MinSpawnDelay': nbt.Short(240),
            'MaxSpawnDelay': nbt.Short(900), 'SpawnCount': nbt.Short(count),
            'MaxNearbyEntities': nbt.Short(5), 'RequiredPlayerRange': nbt.Short(14),
            'SpawnRange': nbt.Short(4)}


def chest(table, facing='north'):
    return ('minecraft:chest', {'facing': facing, 'type': 'single', 'waterlogged': 'false'},
            {'id': 'minecraft:chest', 'LootTable': NS + ':chests/' + table})


DOOR_AT = {'west': (0, 0, 3, 'west_up'), 'east': (CELL - 1, 0, 3, 'east_up'),
           'north': (3, 0, 0, 'north_up'), 'south': (3, 0, CELL - 1, 'south_up')}


def door(p, side, pool, name=DOOR, target=DOOR, priority=0):
    x, y, z, orientation = DOOR_AT[side]
    p.jigsaw(x, y, z, orientation, pool, STONE, priority=priority, name=name, target=target)


def opening(p, side, size=CELL, y0=1, y1=4):
    """The hole a door's jigsaw stands in: three wide, four tall, centred on the face."""
    mid = size // 2
    if side == 'west':
        p.box(0, y0, mid - 1, 0, y1, mid + 1, AIR)
    elif side == 'east':
        p.box(size - 1, y0, mid - 1, size - 1, y1, mid + 1, AIR)
    elif side == 'north':
        p.box(mid - 1, y0, 0, mid + 1, y1, 0, AIR)
    else:
        p.box(mid - 1, y0, size - 1, mid + 1, y1, size - 1, AIR)


# A flight of five steps along z=1 rising east, then one more turning south through the hole
# in the ceiling. Both ends of the climb that cross a shell boundary are cut with this, the
# piece below carrying the flight and the piece above the hole and one last step, so the two
# have to agree on the coordinates - which is why they are written down once, here.
# Two of them, mirror images, so that a cell can hold one flight in its floor and another in
# its ceiling without the two holes landing on top of each other - which is what floor eight
# needs, taking the climb from floor seven and handing it to the terrace.
#   run: the five steps, going up; top: the sixth, turning through the ceiling course
#   hole: x0, x1, z0, z1, cut in the ceiling below and the floor above alike
#   step: the one block in that floor that lifts you out of the hole
FLIGHTS = {
    False: {'run': [(x, x, 1) for x in range(1, 6)], 'facing': 'east',
            'top': (5, CELL - 1, 2), 'turn': 'south',
            'hole': (3, 5, 1, 3), 'step': (5, 3), 'out': 1},
    True:  {'run': [(CELL - 1 - x, x, CELL - 2) for x in range(1, 6)], 'facing': 'west',
            'top': (1, CELL - 1, CELL - 3), 'turn': 'north',
            'hole': (1, 3, 3, 5), 'step': (1, 3), 'out': -1},
}
FLIGHT_TOP = FLIGHTS[False]['top']


def cut_flight(p, cell_x=0, cell_z=0, mirror=False):
    """The lower half: the flight itself and the hole it climbs through."""
    f = FLIGHTS[mirror]
    for x, y, z in f['run']:
        p.set(cell_x + x, y, cell_z + z, STAIR, stair_props(f['facing']))
    x0, x1, z0, z1 = f['hole']
    p.box(cell_x + x0, CELL - 1, cell_z + z0, cell_x + x1, CELL - 1, cell_z + z1, AIR)
    fx, fy, fz = f['top']
    p.set(cell_x + fx, fy, cell_z + fz, STAIR, stair_props(f['turn']))


def cut_landing(p, y, cell_x=0, cell_z=0, mirror=False, out=0):
    """The upper half: the same hole in the floor above, and the step out of it. `out` shifts
    that step away from the hole, for the second course of a two-course floor."""
    f = FLIGHTS[mirror]
    x0, x1, z0, z1 = f['hole']
    p.box(cell_x + x0, y, cell_z + z0, cell_x + x1, y, cell_z + z1, AIR)
    hx, hz = f['step']
    p.set(cell_x + hx, y, cell_z + hz + out * f['out'], STAIR, stair_props(f['turn']))


# ------------------------------------------------------------------------------ the shells

def weather(p, x, y, z, stone=STONE):
    """Freckle the outer skin with moss. The processor adds more at generation time; this is
    what stops the tower reading as one flat grey surface in a screenshot."""
    n = (x * 7 + z * 11 + y * 5) % 9
    p.set(x, y, z, MOSSY if n == 0 else (COBBLE if n == 1 else stone))


def ring(p, y, lo, hi, block, props=None):
    for i in range(lo, hi + 1):
        for x, z in ((lo, i), (hi, i), (i, lo), (i, hi)):
            p.set(x, y, z, block, props)


def base():
    """The plinth: floor one, wider than the shaft, with the door in the middle of its west
    face and a copper cornice where the shaft takes over."""
    n, h = BASE_W, BASE_H
    p = Piece(n, h, n, STONE)
    for y in range(h):
        for x in range(n):
            for z in range(n):
                if x < WALL or x >= n - WALL or z < WALL or z >= n - WALL:
                    weather(p, x, y, z)
    ring(p, 0, 0, n - 1, COBBLE)                       # a footing course on the ground
    ring(p, h - 1, 0, n - 1, COPPER_CUT)               # and copper where the shaft starts
    ring(p, h - 2, 0, n - 1, CHISELED)

    # corner piers, so the plinth has some relief instead of four flat walls
    for cx, cz in ((0, 0), (0, n - 3), (n - 3, 0), (n - 3, n - 3)):
        for y in range(h):
            for x in range(cx, cx + 3):
                for z in range(cz, cz + 3):
                    if x < WALL or x >= n - WALL or z < WALL or z >= n - WALL:
                        p.set(x, y, z, COBBLE if y < h - 2 else LOG,
                              None if y < h - 2 else {'axis': 'y'})

    # the doorway, recessed a block so it reads as a porch, with a lantern either side
    mid = n // 2
    p.box(0, 1, mid - 1, WALL - 1, 4, mid + 1, AIR)
    p.box(0, 5, mid - 2, 0, 5, mid + 2, CHISELED)
    for dz in (-2, 2):
        p.box(0, 1, mid + dz, 0, 4, mid + dz, LOG, {'axis': 'y'})
        p.set(1, 4, mid + dz, 'minecraft:lantern', HANGING)
    p.set(0, 5, mid, COPPER_CHISELED)

    # the arrow slits of the ground floor
    for i in (9, 19, 29):
        for x, z, dx, dz in ((0, i, 1, 0), (n - 1, i, -1, 0), (i, 0, 0, 1), (i, n - 1, 0, -1)):
            if (x, z) == (0, mid) or (z, x) == (0, mid):
                continue
            for depth in range(WALL):
                for dy in (2, 3):
                    p.set(x + dx * depth, dy, z + dz * depth, GLASS, PANE)

    ox, oy, oz = AT['core_base']
    p.jigsaw(ox - 1, 0, oz + SIZE['core_base'][2] // 2, 'east_up', POOL['core_base'], STONE,
             priority=PRIORITY, name=PLACER, target=ANCHOR)
    p.jigsaw(INSET, h - 1, INSET, 'up_east', POOL['shaft'], STONE, joint='aligned',
             priority=PRIORITY, name=PLACER, target=ANCHOR)
    return p


def shaft_floor():
    """One floor of the tall part's outer wall: two courses of wall, a copper band at the top,
    slit windows, quoins at the corners. The inside is left solid for core_shaft to hand to
    the rooms.

    **This is a source piece.** `shaft` is this stacked seven times, so the forty-nine-block
    tower wall - which no structure block can save, being one over the limit of forty-eight -
    can still be built by hand: edit this one floor in the workshop and the generator repeats
    it. The generator writes it only when it is missing, so an edited one is never clobbered.
    """
    n = SHAFT_W
    p = Piece(n, CELL, n, STONE)
    for y in range(CELL):
        for x in range(n):
            for z in range(n):
                if x < WALL or x >= n - WALL or z < WALL or z >= n - WALL:
                    weather(p, x, y, z)
    ring(p, CELL - 1, 0, n - 1, COPPER_CUT)
    ring(p, CELL - 2, 0, n - 1, CHISELED)
    # windows: one wide, three tall, cut through both courses so they read as openings
    for i in (6, 12, 18):
        for x, z, dx, dz in ((0, i, 1, 0), (n - 1, i, -1, 0), (i, 0, 0, 1), (i, n - 1, 0, -1)):
            for depth in range(WALL):
                for dy in range(2, 5):
                    p.set(x + dx * depth, dy, z + dz * depth, GLASS, PANE)
    for cx, cz in ((0, 0), (0, n - 1), (n - 1, 0), (n - 1, n - 1)):
        for y in range(0, CELL, 2):
            p.set(cx, y, cz, CHISELED)
    return p


def shaft(floor_piece):
    """Seven copies of one floor, and the three jigsaws that join the shells."""
    n, h = SHAFT_W, SHAFT_H
    p = Piece(n, h, n, STONE)
    for floor in range(FLOORS):
        for (x, y, z), (block, props) in floor_piece.grid.items():
            p.set(x, floor * CELL + y, z, block, dict(props) if props else None)

    p.jigsaw(0, 0, 0, 'down_east', EMPTY, STONE, joint='aligned', name=ANCHOR, target=ANCHOR)
    p.jigsaw(WALL - 1, 0, SIZE['shaft'][2] // 2, 'east_up', POOL['core_shaft'], STONE,
             priority=PRIORITY, name=PLACER, target=ANCHOR)
    p.jigsaw(0, h - 1, 0, 'up_east', POOL['crown'], STONE, joint='aligned',
             priority=PRIORITY, name=PLACER, target=ANCHOR)
    return p


def load_piece(path):
    """Read a saved piece back into a Piece, so a hand-built source can be stacked."""
    root = nbt.read(path)
    sx, sy, sz = [int(v) for v in root['size']]
    p = Piece(sx, sy, sz, AIR)
    palette = [(nbt.palette_name(e), dict(nbt.palette_props(e) or {})) for e in root['palette']]
    for b in root['blocks']:
        x, y, z = [int(v) for v in b['pos']]
        name, props = palette[int(b['state'])]
        p.set(x, y, z, name, props or None, b.get('nbt'))
    return p


def crown():
    """The gallery that hangs out past the shaft, and the terrace floor eight climbs on to.

    It carries its own room rather than handing one to a core: there is nothing up here for a
    maze to do, and an open deck is the point of the shape."""
    n, h = BASE_W, CROWN_H
    p = Piece(n, h, n, AIR)
    lo, hi = INSET - WALL * 2, n - 1 - (INSET - WALL * 2)     # the chamfer course, 33 wide
    p.box(lo, 0, lo, hi, 0, hi, COPPER_CUT)
    for i in range(lo, hi + 1):                               # its outward-sloping soffit
        for x, z, facing in ((lo, i, 'west'), (hi, i, 'east'), (i, lo, 'north'), (i, hi, 'south')):
            p.set(x, 0, z, COPPER_STAIR, stair_props(facing, half='top'))
    p.box(0, 1, 0, n - 1, 1, n - 1, WOOD)                     # the deck, full width
    ring(p, 1, 0, n - 1, COPPER_CUT)
    ring(p, 1, 1, n - 2, COPPER_CUT)

    # the gallery: piers at the corners and the middle of each side, a rail between them
    for y in range(2, h - 2):
        for cx, cz in ((0, 0), (0, n - 3), (n - 3, 0), (n - 3, n - 3)):
            p.box(cx, y, cz, cx + 2, y, cz + 2, STONE)
        for i in (n // 2 - 1, n // 2, n // 2 + 1):
            for x, z in ((0, i), (n - 1, i), (i, 0), (i, n - 1)):
                p.set(x, y, z, LOG, {'axis': 'y'})
    for i in range(n):
        for x, z in ((0, i), (n - 1, i), (i, 0), (i, n - 1)):
            if p.grid[(x, 2, z)][0] == AIR:
                p.set(x, 2, z, FENCE, RAIL)
    p.box(0, h - 2, 0, n - 1, h - 2, n - 1, WOOD)             # the gallery ceiling
    ring(p, h - 2, 0, n - 1, COPPER_CUT)
    p.box(0, h - 1, 0, n - 1, h - 1, n - 1, COPPER_CUT)       # the eave the roof sits on
    for i in range(n):
        for x, z, facing in ((0, i, 'west'), (n - 1, i, 'east'),
                             (i, 0, 'north'), (i, n - 1, 'south')):
            p.set(x, h - 1, z, COPPER_STAIR, stair_props(facing))

    # where floor eight comes up, and what is worth the climb
    cx, cz = ROUTE[LAST_FLOOR][0]
    ox = AT['core_shaft'][0] - AT['crown'][0] + cx * CELL
    oz = AT['core_shaft'][2] - AT['crown'][2] + cz * CELL
    for y in (0, 1):                      # two courses of deck, a step through each
        cut_landing(p, y, ox, oz, mirror=True, out=y)
    hx, hz = FLIGHTS[True]['step']
    p.set(ox + hx + 2, 2, oz + hz - 1, *chest('tower_observatory', 'north'))
    for x, z in ((n // 2, 3), (3, n // 2), (n - 4, n // 2), (n // 2, n - 4)):
        p.set(x, h - 3, z, 'minecraft:lantern', HANGING)
    p.set(n // 2, 2, n // 2, COPPER_CHISELED)
    p.set(n // 2, 3, n // 2, COPPER_GRATE, {'waterlogged': 'false'})

    p.jigsaw(INSET, 0, INSET, 'down_east', EMPTY, STONE, joint='aligned',
             name=ANCHOR, target=ANCHOR)
    p.jigsaw(0, h - 1, 0, 'up_east', POOL['roof'], COPPER_CUT, joint='aligned',
             priority=PRIORITY, name=PLACER, target=ANCHOR)
    return p


def roof():
    """A hip roof of oxidized copper, one course in for every course up, with a lightning rod
    on the point. It is a shell, not a solid: nothing ever stands inside it."""
    n, h = BASE_W, ROOF_H
    p = Piece(n, h, n, AIR)
    k = 0
    while True:
        lo, hi = k, n - 1 - k
        if lo >= hi:
            break
        for i in range(lo, hi + 1):
            for x, z, facing in ((lo, i, 'west'), (hi, i, 'east'),
                                 (i, lo, 'north'), (i, hi, 'south')):
                p.set(x, k, z, COPPER_STAIR, stair_props(facing))
        for x, z in ((lo, lo), (lo, hi), (hi, lo), (hi, hi)):
            p.set(x, k, z, COPPER)
        k += 1
    top = k
    p.box(top - 1, top - 1, top - 1, n - top, top - 1, n - top, COPPER)
    for y in range(top, h - 1):
        p.set(n // 2, y, n // 2, COPPER_CHISELED if y % 2 else COPPER_GRATE,
              None if y % 2 else {'waterlogged': 'false'})
    p.set(n // 2, h - 1, n // 2, ROD, {'facing': 'up', 'powered': 'false',
                                       'waterlogged': 'false'})
    p.jigsaw(0, 0, 0, 'down_east', EMPTY, COPPER_CUT, joint='aligned',
             name=ANCHOR, target=ANCHOR)
    return p


# ------------------------------------------------------------------------------- the cores

def core_base():
    """Floor one, solid, for its rooms to carve. It places the entrance hall itself so the
    way in is never left to the maze."""
    sx, sy, sz = SIZE['core_base']
    p = Piece(sx, sy, sz, STONE)
    p.jigsaw(0, 0, sz // 2, 'west_up', EMPTY, STONE, name=ANCHOR, target=ANCHOR)
    hx, hz = HALL_CELL
    p.jigsaw(hx * CELL + 3, 0, hz * CELL - 1, 'south_up', POOL['hall'], STONE,
             priority=PRIORITY, name=PLACER, target=RISER)
    return p


def core_shaft():
    """Floors two to eight, solid, and the one jigsaw that starts the climb."""
    sx, sy, sz = SIZE['core_shaft']
    p = Piece(sx, sy, sz, STONE)
    p.jigsaw(0, 0, sz // 2, 'west_up', EMPTY, STONE, name=ANCHOR, target=ANCHOR)
    cx, cz = ROUTE[FIRST_FLOOR][0]
    p.jigsaw(cx * CELL - 1, 0, cz * CELL + 3, 'east_up', POOL['land_%d' % FIRST_FLOOR], STONE,
             priority=PRIORITY, name=PLACER, target=RISER)
    return p


# ------------------------------------------------------------------------- the rooms' shell

def room(doors=(), floor=WOOD, wall=STONE):
    p = Piece(CELL, CELL, CELL, wall)
    p.box(1, 1, 1, CELL - 2, CELL - 2, CELL - 2, AIR)
    p.box(0, 0, 0, CELL - 1, 0, CELL - 1, floor)
    for side in doors:
        opening(p, side)
    return p


def side_between(here, there):
    """Which face of `here` looks at the cell `there`."""
    dx, dz = there[0] - here[0], there[1] - here[1]
    for side, step in STEP.items():
        if step == (dx, dz):
            return side
    raise SystemExit('cells %s and %s are not neighbours' % (here, there))


def in_grid(cell):
    return 0 <= cell[0] < SHAFT_GRID and 0 <= cell[1] < SHAFT_GRID


def big_cells(name):
    (x, z) = BIG[name][1]
    return {(x + dx, z + dz) for dx in (0, 1) for dz in (0, 1)}


def blocked(floor):
    """Cells a floor cannot use for anything else: the two big rooms take four each, and a
    stair takes the cell it stands in."""
    taken = set()
    for name, (start, _cell, _face) in BIG.items():
        if start <= floor <= start + 1:
            taken |= big_cells(name)
    return taken


# --------------------------------------------------------------------------- floor one

def hall():
    """Straight inside the front door: the only piece of floor one whose place is fixed by
    the shell, so the door can never open on to solid rock."""
    p = room(['west', 'east', 'south'])
    p.jigsaw(3, 0, 0, 'north_up', EMPTY, STONE, name=RISER, target=RISER)
    door(p, 'east', POOL['corridor'], name=PLACER, target=RISER, priority=PRIORITY)
    door(p, 'south', POOL['passages'])
    p.box(1, 0, 1, 5, 0, 5, WOOD)
    for z in (2, 4):
        p.set(1, 1, z, LOG, {'axis': 'y'})
        p.set(1, 2, z, LOG, {'axis': 'y'})
    p.set(3, 4, 3, 'minecraft:lantern', HANGING)
    p.set(5, 1, 1, *chest('tower_study', 'south'))
    return p


def corridor():
    """Hall to great stair, with the still room off its north side."""
    p = room(['west', 'east', 'north'])
    p.jigsaw(0, 0, 3, 'west_up', EMPTY, STONE, name=RISER, target=RISER)
    door(p, 'east', POOL['great_stair'], name=PLACER, target=RISER, priority=PRIORITY)
    door(p, 'north', POOL['alchemy'], name=PLACER, target=ANCHOR, priority=PRIORITY)
    p.set(3, 4, 3, 'minecraft:lantern', HANGING)
    return p


def great_stair():
    """The flight out of floor one. Its top half is cut into floor two's landing, which sits
    directly above it, from the same table of coordinates (CLAUDE.md section 11)."""
    p = room(['west', 'south'])
    p.jigsaw(0, 0, 3, 'west_up', EMPTY, STONE, name=RISER, target=RISER)
    door(p, 'south', POOL['passages'])
    cut_flight(p)
    p.set(1, 4, 5, 'minecraft:lantern', HANGING)
    return p


# ------------------------------------------------------------------------------- the climb

def land(floor):
    """Where a floor is entered. Exactly one jigsaw carries the name its parent targets."""
    land_cell, stair_cell = ROUTE[floor]
    p = room()
    p.box(0, 0, 0, CELL - 1, 0, CELL - 1, WOOD)
    used = set()

    if floor == FIRST_FLOOR:
        p.jigsaw(0, 0, 3, 'west_up', EMPTY, STONE, name=RISER, target=RISER)
        used.add('west')
    else:
        p.jigsaw(0, 0, 0, 'down_east', EMPTY, STONE, joint='aligned',
                 name=RISER, target=RISER)
    cut_landing(p, 0)                          # the hole the stair below comes up through

    if stair_cell is None:
        cut_flight(p, mirror=True)             # the last climb, out on to the terrace
    else:
        side = side_between(land_cell, stair_cell)
        opening(p, side)
        door(p, side, POOL['stair_%d' % floor], name=PLACER, target=RISER, priority=PRIORITY)
        used.add(side)

    for name, (start, cell, face) in BIG.items():
        if start == floor:
            opening(p, face)
            door(p, face, POOL[name], name=PLACER, target=ANCHOR, priority=PRIORITY)
            used.add(face)

    taken = blocked(floor)
    for side, step in STEP.items():
        if side in used:
            continue
        neighbour = (land_cell[0] + step[0], land_cell[1] + step[1])
        if not in_grid(neighbour) or neighbour in taken:
            continue
        opening(p, side)
        door(p, side, POOL['passages'])
    p.set(3, 4, 3, 'minecraft:lantern', HANGING)
    return p


def stair(floor):
    """A stair room: a flight and a half up one wall, out through its own ceiling into the
    cell above, which is the next floor's landing."""
    land_cell, stair_cell = ROUTE[floor]
    p = room()
    p.box(0, 0, 0, CELL - 1, 0, CELL - 1, WOOD)
    back = side_between(stair_cell, land_cell)
    opening(p, back)
    p.jigsaw(*DOOR_AT[back][:3], DOOR_AT[back][3], EMPTY, STONE, name=RISER, target=RISER)
    cut_flight(p)
    p.jigsaw(0, CELL - 1, 0, 'up_east', POOL['land_%d' % (floor + 1)], STONE, joint='aligned',
             priority=PRIORITY, name=PLACER, target=RISER)
    p.set(1, 4, 5, 'minecraft:lantern', HANGING)
    return p


# -------------------------------------------------------------------------- the big rooms

def library():
    """Two floors of one room: shelves to the ceiling, a gallery to walk them from, and an
    enchanting table on the floor with the fifteen shelves that level thirty needs."""
    n = BIG_SIZE
    p = Piece(n, n, n, STONE)
    p.box(1, 1, 1, n - 2, n - 2, n - 2, AIR)
    p.box(0, 0, 0, n - 1, 0, n - 1, WOOD)
    p.jigsaw(10, 0, 0, 'north_up', EMPTY, STONE, name=ANCHOR, target=ANCHOR)
    p.box(9, 1, 0, 11, 4, 0, AIR)

    # the gallery: a three-wide walkway round an open well
    gy = CELL
    p.box(1, gy, 1, n - 2, gy, n - 2, WOOD)
    p.box(4, gy, 4, n - 5, gy, n - 5, AIR)
    for i in range(3, n - 3):
        for x, z in ((3, i), (n - 4, i), (i, 3), (i, n - 4)):
            p.set(x, gy + 1, z, FENCE, RAIL)
    # shelves on every wall, both levels
    for level in (1, gy + 1):
        for i in range(1, n - 1):
            for x, z in ((1, i), (n - 2, i), (i, 1), (i, n - 2)):
                for dy in range(3):
                    p.set(x, level + dy, z, BOOKSHELF)
    # the flight up to the gallery, against the east wall
    for k in range(CELL):
        p.set(n - 3, 1 + k, 2 + k, STAIR, stair_props('south'))
        p.box(n - 4, 2 + k, 2 + k, n - 3, 5 + k, 3 + k, AIR)
    p.box(n - 4, gy, 2, n - 3, gy, CELL + 2, AIR)

    # the table and the ring that counts: fifteen shelves at range two, one gap to walk in
    c = n // 2
    p.box(c - 3, 1, c - 3, c + 3, 1, c + 3, POLISHED)
    p.set(c, 2, c, 'minecraft:enchanting_table')
    for dx in range(-2, 3):
        for dz in range(-2, 3):
            if max(abs(dx), abs(dz)) == 2 and (dx, dz) != (0, -2):
                p.set(c + dx, 2, c + dz, BOOKSHELF)
    p.set(c, 1, c - 4, 'minecraft:lectern',
          {'facing': 'south', 'has_book': 'false', 'powered': 'false'})
    p.set(c + 3, 2, c, *chest('tower_library', 'west'))
    p.set(c - 3, 2, c, *chest('tower_study', 'east'))
    # a chandelier down the well, so the middle of the room is not just air
    for y in range(gy + 4, n - 2):
        p.set(c, y, c, COPPER_CHAIN, {'axis': 'y', 'waterlogged': 'false'})
    p.set(c, gy + 3, c, 'minecraft:lantern', HANGING)
    for x, z in ((3, 3), (3, n - 4), (n - 4, 3), (n - 4, n - 4)):
        p.set(x, gy + 5, z, 'minecraft:lantern', HANGING)
    return p


def sanctum():
    """The archmage's chamber, two floors tall, with the gate he never lit."""
    n = BIG_SIZE
    c = n // 2
    p = Piece(n, n, n, DEEP)
    p.box(1, 1, 1, n - 2, n - 2, n - 2, AIR)
    p.box(0, 0, 0, n - 1, 0, n - 1, POLISHED)
    p.jigsaw(0, 0, 3, 'west_up', EMPTY, DEEP, name=ANCHOR, target=ANCHOR)
    p.box(0, 1, 2, 0, 4, 4, AIR)

    for x0, z0 in ((2, 2), (2, n - 4), (n - 4, 2), (n - 4, n - 4)):      # four piers
        p.box(x0, 1, z0, x0 + 1, n - 2, z0 + 1, POLISHED)
        p.set(x0, 1, z0, CHISELED)
    ring(p, CELL, 0, n - 1, POLISHED)                                    # a band at the gallery
    # a circle cut into the floor, so the room reads as a working room and not a box
    for dx in range(-4, 5):
        for dz in range(-4, 5):
            if 3 <= max(abs(dx), abs(dz)) <= 4 and abs(dx) + abs(dz) <= 6:
                p.set(c + dx, 0, c + dz, CHISELED)
    p.box(c - 2, 0, c - 2, c + 2, 0, c + 2, CHISELED)
    p.box(c - 1, 1, c - 1, c + 1, 1, c + 1, POLISHED)
    p.set(c, 2, c, 'minecraft:trial_spawner', TRIAL_STATE, trial_spawner('archmage'))
    for x, z in ((3, 3), (3, n - 4), (n - 4, 3), (n - 4, n - 4)):
        p.set(x, 1, z, 'minecraft:trial_spawner', TRIAL_STATE, trial_spawner('tower_guards'))

    fx, fz = c - 2, n - 2                                                # the gate, unlit
    for dx, dy in ((1, 0), (2, 0), (1, 4), (2, 4),
                   (0, 1), (0, 2), (0, 3), (3, 1), (3, 2), (3, 3)):
        p.set(fx + dx, 1 + dy, fz - 1, 'minecraft:obsidian')
    p.set(fx - 1, 1, fz - 1, *chest('tower_portal', 'north'))
    for x, z in ((c, 2), (2, c), (n - 3, c), (c, n - 3)):
        p.set(x, n - 3, z, 'minecraft:soul_lantern', HANGING)
        p.set(x, n - 4, z, COPPER_CHAIN, {'axis': 'y', 'waterlogged': 'false'})
    return p


def alchemy():
    """The still room, off the corridor on floor one: a room of its own, not a widening of
    a passage, which is what it looked like in the castle."""
    p = room()
    p.jigsaw(3, 0, CELL - 1, 'south_up', EMPTY, STONE, name=ANCHOR, target=ANCHOR)
    opening(p, 'south')
    p.box(1, 1, 1, 5, 1, 1, POLISHED)
    p.set(3, 2, 1, 'minecraft:brewing_stand',
          {'has_bottle_0': 'false', 'has_bottle_1': 'false', 'has_bottle_2': 'false'})
    p.set(1, 1, 5, 'minecraft:cauldron', {'level': '0'})
    p.set(5, 1, 5, 'minecraft:cauldron', {'level': '0'})
    p.set(1, 2, 1, *chest('tower_study', 'south'))
    p.set(5, 1, 1, BOOKSHELF)
    p.set(3, 4, 3, 'minecraft:soul_lantern', HANGING)
    return p


# ------------------------------------------------------------------------------- the maze

def maze_room(doors):
    p = room(doors)
    for side in doors:
        door(p, side, POOL['passages'])
    return p


def passage():
    p = maze_room(['west', 'east'])
    for z in (1, 5):
        p.set(1, 1, z, LOG, {'axis': 'y'})
        p.set(5, 1, z, LOG, {'axis': 'y'})
    return p


def corner():
    return maze_room(['west', 'south'])


def cross():
    return maze_room(['west', 'east', 'north', 'south'])


def study():
    p = maze_room(['west'])
    p.box(4, 1, 1, 5, 2, 5, BOOKSHELF)
    p.set(4, 3, 3, *chest('tower_study', 'west'))
    p.set(3, 1, 5, 'minecraft:lectern',
          {'facing': 'north', 'has_book': 'false', 'powered': 'false'})
    p.set(3, 4, 3, 'minecraft:lantern', HANGING)
    return p


def vex_cage():
    """A cage standing on the floor, bar to bar, not a pane of iron floating in mid air."""
    p = maze_room(['west', 'east'])
    for x in range(2, 5):
        for z in range(4, 7):
            if x in (2, 4) or z in (4, 6):
                for y in range(1, 4):
                    p.set(x, y, z, 'minecraft:iron_bars', BARS)
    p.box(2, 4, 4, 4, 4, 6, 'minecraft:iron_bars', BARS)
    p.set(3, 1, 5, 'minecraft:spawner', None, mob_spawner('minecraft:vex'))
    return p


def lab():
    p = maze_room(['west', 'east'])
    p.set(1, 1, 5, 'minecraft:cauldron', {'level': '0'})
    p.set(5, 1, 5, 'minecraft:cauldron', {'level': '0'})
    p.set(3, 1, 5, 'minecraft:spawner', None, mob_spawner('minecraft:zombie_villager'))
    p.set(3, 4, 3, 'minecraft:soul_lantern', HANGING)
    return p


def stair_maze():
    """A short cut: an ordinary maze piece that happens to climb a floor, the way the prison's
    stair does. It is two cells tall, so near the top of the shaft it will not fit and the
    fallback plugs the doorway instead - which is exactly what should happen."""
    p = Piece(CELL, 2 * CELL, CELL, STONE)
    p.box(1, 1, 1, CELL - 2, 2 * CELL - 2, CELL - 2, AIR)
    p.box(0, 0, 0, CELL - 1, 0, CELL - 1, WOOD)
    p.box(0, CELL, 0, CELL - 1, CELL, CELL - 1, WOOD)
    opening(p, 'west')
    p.box(0, CELL + 1, 2, 0, CELL + 4, 4, AIR)
    cut_flight(p)
    cut_landing(p, CELL)
    p.jigsaw(0, 0, 3, 'west_up', POOL['passages'], STONE, name=DOOR, target=DOOR)
    p.jigsaw(0, CELL, 3, 'west_up', POOL['passages'], STONE, name=DOOR, target=DOOR)
    p.set(1, 4, 5, 'minecraft:lantern', HANGING)
    return p


def cap():
    p = Piece(1, CELL, CELL, STONE)
    p.jigsaw(0, 0, 3, 'west_up', POOL['caps'], STONE, name=DOOR, target=DOOR)
    return p


# ---------------------------------------------------------------------------------- pools

def element(location, weight):
    return ('    { "weight": %d, "element": { "element_type": "minecraft:single_pool_element",\n'
            '        "location": "%s:tower/%s", "projection": "rigid", '
            '"processors": "%s:tower_weathering" } }' % (weight, NS, location, NS))


def write_pool(name, elements, fallback=NS + ':tower/caps'):
    os.makedirs(POOL_JSON, exist_ok=True)
    text = '{\n  "fallback": "%s",\n  "elements": [\n%s\n  ]\n}\n' % (fallback, ',\n'.join(elements))
    with open(os.path.join(POOL_JSON, name + '.json'), 'w', encoding='utf-8', newline='\n') as f:
        f.write(text)


# ---------------------------------------------------------------------------------- checks

def verify(pieces):
    problems = []

    def inside(child, parent):
        for axis in range(3):
            lo = AT[child][axis] - AT[parent][axis]
            if lo < 0 or lo + SIZE[child][axis] > SIZE[parent][axis]:
                problems.append('%s is not inside %s on axis %d' % (child, parent, axis))

    inside('core_base', 'base')
    inside('core_shaft', 'shaft')
    for name in BIG:
        inside(name, 'core_shaft')

    # the shells stack with nothing between them and nothing overlapping: a child whose box
    # runs into its parent's is simply refused, and the tower would lose everything above it
    for lower, upper in (('base', 'shaft'), ('shaft', 'crown'), ('crown', 'roof')):
        if AT[lower][1] + SIZE[lower][1] != AT[upper][1]:
            problems.append('%s does not sit exactly on %s' % (upper, lower))

    # the climb: each floor's landing is the floor below's stair, they are neighbours, and
    # neither stands where a big room does
    for floor in sorted(ROUTE):
        land_cell, stair_cell = ROUTE[floor]
        taken = blocked(floor)
        if not in_grid(land_cell):
            problems.append('floor %d lands outside the shaft' % floor)
        if land_cell in taken:
            problems.append('floor %d lands inside a big room' % floor)
        if stair_cell is None:
            continue
        if abs(stair_cell[0] - land_cell[0]) + abs(stair_cell[1] - land_cell[1]) != 1:
            problems.append('floor %d\'s stair is not next to its landing' % floor)
        if stair_cell in taken or stair_cell in blocked(floor + 1):
            problems.append('floor %d\'s stair stands where a big room does' % floor)
        if ROUTE[floor + 1][0] != stair_cell:
            problems.append('floor %d does not come up in floor %d\'s stair cell'
                            % (floor + 1, floor))
    if len({ROUTE[f][1] for f in ROUTE if ROUTE[f][1]}) < 3:
        problems.append('the climb barely moves; it may as well be a ladder')

    # every big room is entered off a landing, never through the maze
    for name, (floor, cell, face) in BIG.items():
        land_cell = ROUTE[floor][0]
        step = STEP[face]
        if (land_cell[0] + step[0], land_cell[1] + step[1]) not in big_cells(name):
            problems.append('%s is not through floor %d\'s %s door' % (name, floor, face))

    # floor one's fixed chain has to be a chain, and end under floor two's landing
    for a, b in ((HALL_CELL, CORR_CELL), (CORR_CELL, GREAT_CELL)):
        if abs(a[0] - b[0]) + abs(a[1] - b[1]) != 1:
            problems.append('floor one\'s chain breaks between %s and %s' % (a, b))
    great_x = AT['core_base'][0] + GREAT_CELL[0] * CELL
    land_x = AT['core_shaft'][0] + ROUTE[FIRST_FLOOR][0][0] * CELL
    great_z = AT['core_base'][2] + GREAT_CELL[1] * CELL
    land_z = AT['core_shaft'][2] + ROUTE[FIRST_FLOOR][0][1] * CELL
    if (great_x, great_z) != (land_x, land_z):
        problems.append('the great stair is not under floor two\'s landing')
    if AT['core_base'][2] + HALL_CELL[1] * CELL + 3 != AT['base'][2] + BASE_W // 2:
        problems.append('the front door of the shell does not line up with the hall')

    # exactly one jigsaw per piece may carry each of the names a parent targets, or the
    # generator can enter the piece through the wrong one and run the chain backwards
    for name, piece in pieces.items():
        counts = {}
        sx, sy, sz = piece.size
        for pos, (block, props) in piece.grid.items():
            if block != 'minecraft:jigsaw':
                continue
            meta = piece.extra.get(pos, {})
            counts[meta.get('name')] = counts.get(meta.get('name'), 0) + 1
            if meta.get('name') != DOOR:
                continue
            facing = dict(props or ()).get('orientation', '').split('_')[0]
            x, y, z = pos
            on = {'west': x == 0, 'east': x == sx - 1,
                  'north': z == 0, 'south': z == sz - 1}.get(facing)
            if on is False:
                problems.append('%s has a %s door at %s, not on that face' % (name, facing, pos))
        for connector in (RISER, ANCHOR):
            if counts.get(connector, 0) > 1:
                problems.append('%s carries %d jigsaws named %s; a parent could come in '
                                'through the wrong one' % (name, counts[connector], connector))

    # the two cuts that cross a shell boundary have to meet
    for lower, upper, mirror in (('great_stair', 'land_%d' % FIRST_FLOOR, False),
                                 ('land_%d' % LAST_FLOOR, 'crown', True)):
        below, above = pieces[lower], pieces[upper]
        fx, fy, fz = FLIGHTS[mirror]['top']
        if below.grid[(fx, fy, fz)][0] != STAIR:
            problems.append('%s has no step at the top of its flight' % lower)
        ox, oz = (0, 0)
        if upper == 'crown':
            ox = AT['core_shaft'][0] - AT['crown'][0] + ROUTE[LAST_FLOOR][0][0] * CELL
            oz = AT['core_shaft'][2] - AT['crown'][2] + ROUTE[LAST_FLOOR][0][1] * CELL
        if above.grid[(ox + fx, 0, oz + fz)][0] != AIR:
            problems.append('%s does not open above %s\'s last step' % (upper, lower))

    for line in problems:
        print('  PROBLEM  ' + line)
    if problems:
        raise SystemExit('the tower does not hold together')
    print('  checked: %d shells stacked, %d floors climbed by stair, both big rooms off the '
          'route' % (4, FLOORS))


# ----------------------------------------------------------------------------------- main

def main():
    os.makedirs(DST, exist_ok=True)
    # the one source piece: kept if it is already there, so a hand-built floor survives
    floor_path = os.path.join(DST, 'shaft_floor.nbt')
    hand_built = os.path.exists(floor_path)
    floor_piece = load_piece(floor_path) if hand_built else shaft_floor()
    pieces = {
        'base': base(), 'shaft': shaft(floor_piece), 'crown': crown(), 'roof': roof(),
        'shaft_floor': floor_piece,
        'core_base': core_base(), 'core_shaft': core_shaft(),
        'hall': hall(), 'corridor': corridor(), 'great_stair': great_stair(),
        'alchemy': alchemy(), 'library': library(), 'sanctum': sanctum(),
        'passage': passage(), 'corner': corner(), 'cross': cross(), 'study': study(),
        'vex_cage': vex_cage(), 'lab': lab(), 'stair_maze': stair_maze(), 'cap': cap(),
    }
    for floor in sorted(ROUTE):
        pieces['land_%d' % floor] = land(floor)
        if ROUTE[floor][1] is not None:
            pieces['stair_%d' % floor] = stair(floor)
    verify(pieces)
    for name, piece in sorted(pieces.items()):
        if name == 'shaft_floor' and hand_built:
            print('  %-12s %s  kept (built by hand)' % (name, list(piece.size)))
            continue
        piece.write(os.path.join(DST, name + '.nbt'))
        print('  %-12s %s' % (name, list(piece.size)))

    write_pool('start', [element('base', 1)], fallback=EMPTY)
    for one in ['shaft', 'crown', 'roof', 'core_base', 'core_shaft', 'hall', 'corridor',
                'great_stair', 'alchemy', 'library', 'sanctum']:
        write_pool(one, [element(one, 1)], fallback=EMPTY)
    for floor in sorted(ROUTE):
        write_pool('land_%d' % floor, [element('land_%d' % floor, 1)], fallback=EMPTY)
        if ROUTE[floor][1] is not None:
            write_pool('stair_%d' % floor, [element('stair_%d' % floor, 1)], fallback=EMPTY)
    write_pool('passages', [element('passage', 10), element('corner', 9), element('cross', 8),
                            element('study', 8), element('vex_cage', 6), element('lab', 6),
                            element('stair_maze', 5)])
    write_pool('caps', [element('cap', 1)], fallback=EMPTY)
    print('  pools -> %s' % os.path.relpath(POOL_JSON, ROOT))


if __name__ == '__main__':
    main()
