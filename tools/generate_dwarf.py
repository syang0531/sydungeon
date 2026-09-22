# -*- coding: utf-8 -*-
"""The Dwarven Hall: a gate in the mountain, and everything else under it.

    python tools/generate_dwarf.py        (or through make_pieces.py)

Writes data/sydungeon/structure/dwarf/*.nbt and the pools that join them.

ALL OF IT IS UNDERGROUND BUT THE DOOR
The graveyard's machine with the graveyard's surface taken off (generate_grave.py): a start
piece, a ladder down, a hub, a maze of cells cut out of rock, and the boss on a chain of
single-element pools. What is different is that the only thing standing in daylight is the
gatehouse. Peaks are the steepest ground in the game and a piece that spreads across them
either floats or buries itself, so nothing spreads across them - the hall is inside the rock,
which is where a dwarf hall belongs anyway.

THAT IS ALSO WHY THE SHAFT IS TWO PIECES
Mountain surface runs from y 110 to y 200 and the maze has to be clear of whichever slope it
started on. One shaft is 21; two of them chained by single-element pools put the hall 42
below the door, and the maze has no stairs at all, so it cannot climb back into the
mountainside (CLAUDE.md section 5.1). The shells are the ground's own stone banded with
granite (section 5.2) - deepslate brick, iron and lava are all on the inside.

THE HAZARDS ARE THE ONES NOBODY CAN SET OFF
Section 12: no pressure plates, no tripwire, nothing a wandering zombie can spring before the
player arrives. A lava chasm is not a trap, it is a hole with lava in it, and it is exactly
as dangerous whoever walks in first. Same for the narrow middle of the span, and for the ore
that only a pick can reach.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import nbt  # noqa: E402
from generate_pieces import Piece  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DST = os.path.join(ROOT, 'src', 'main', 'resources', 'data', 'sydungeon', 'structure', 'dwarf')
POOL_JSON = os.path.join(ROOT, 'src', 'main', 'resources', 'data', 'sydungeon', 'worldgen',
                         'template_pool', 'dwarf')

NS = 'sydungeon'
HALL = NS + ':dwf_hall'          # the connector everything underground uses
DOWN = NS + ':dwf_down'          # the vertical chain: gate, two shafts, hub
KING = NS + ':dwf_king'          # the boss branch, its own name so it cannot run backwards
EMPTY = 'minecraft:empty'
PRIORITY = 10

CELL = 7
GATE = 21                        # the gatehouse is three cells across
GROUND = 0                       # the start piece's floor: a start is moved so that
                                 # minY + 1 is the first free block, so y=0 is the
                                 # terrain's own top block (section 30)
SHAFT_H = 21
BOSS = (21, 14, 21)
MIN_BOSS_STEPS = 3

# the way down, in the gatehouse's coordinates, shared by the four pieces the column runs
# through (section 11). The ladder is against the south wall of the hole and its own row is
# left solid at each floor, so there is somewhere to step off (section 24)
HOLE = (GATE // 2 - 1, GATE // 2 + 1, GATE // 2 - 1, GATE // 2 + 1)
RUNG = (HOLE[0], HOLE[3])
JIG = (RUNG[0], RUNG[1] + 1)
SHAFT_AT = CELL

ROCK = 'minecraft:stone'          # what the hall is cut out of, and therefore what shows
BAND = 'minecraft:granite'        # a course of it every few, so an exposed face reads as rock
DEEP = 'minecraft:deepslate_bricks'
TILE = 'minecraft:deepslate_tiles'
POLISH = 'minecraft:polished_deepslate'
CHISEL = 'minecraft:chiseled_deepslate'
TUFF = 'minecraft:tuff_bricks'
IRON = 'minecraft:iron_block'
GOLD = 'minecraft:gold_block'
LAVA = 'minecraft:lava'
MAGMA = 'minecraft:magma_block'
ANVIL = 'minecraft:anvil'
FURNACE = 'minecraft:blast_furnace'
SMITH = 'minecraft:smithing_table'
GRINDSTONE = 'minecraft:grindstone'
BARREL = 'minecraft:barrel'
CAULDRON = 'minecraft:lava_cauldron'
RAIL = 'minecraft:rail'
LANTERN = 'minecraft:lantern'
CHAIN = 'minecraft:iron_chain'
BARS = 'minecraft:iron_bars'
CAMPFIRE = 'minecraft:campfire'
LOG = 'minecraft:spruce_log'
PLANK = 'minecraft:spruce_planks'
AIR = 'minecraft:air'

HANGING = {'hanging': 'true', 'waterlogged': 'false'}
STANDING = {'hanging': 'false', 'waterlogged': 'false'}
GRID = {'north': 'true', 'south': 'true', 'east': 'true', 'west': 'true',
        'waterlogged': 'false'}
FIRE = {'facing': 'north', 'lit': 'true', 'signal_fire': 'false', 'waterlogged': 'false'}
SOURCE = {'level': '0'}

POOL = {k: NS + ':dwarf/' + k for k in
        ['start', 'down', 'deep', 'hall_first', 'halls', 'hall_caps', 'king_approach'] +
        ['king_approach_%d' % i for i in range(1, MIN_BOSS_STEPS + 1)]}

TRIAL_STATE = {'trial_spawner_state': 'inactive', 'ominous': 'false'}
ANY_LIGHT = {'block_light_limit': {'min_inclusive': nbt.Int(0), 'max_inclusive': nbt.Int(15)}}


def trial_spawner(config):
    return {'id': 'minecraft:trial_spawner',
            'normal_config': NS + ':dwarf/' + config,
            'ominous_config': NS + ':dwarf/' + config,
            'target_cooldown_length': nbt.Int(2_000_000_000),
            'required_player_range': nbt.Int(14)}


def mob_spawner(entity, count=2, extra=None):
    data = {'entity': dict({'id': entity}, **(extra or {}))}
    data['custom_spawn_rules'] = ANY_LIGHT
    return {'id': 'minecraft:mob_spawner', 'SpawnData': data,
            'Delay': nbt.Short(20), 'MinSpawnDelay': nbt.Short(240),
            'MaxSpawnDelay': nbt.Short(900), 'SpawnCount': nbt.Short(count),
            'MaxNearbyEntities': nbt.Short(5), 'RequiredPlayerRange': nbt.Short(14),
            'SpawnRange': nbt.Short(4)}


def chest(table, facing='north'):
    return ('minecraft:chest', {'facing': facing, 'type': 'single', 'waterlogged': 'false'},
            {'id': 'minecraft:chest', 'LootTable': NS + ':chests/' + table})


def ladder(facing='north'):
    return ('minecraft:ladder', {'facing': facing, 'waterlogged': 'false'})


def bedrock(p, sx, sy, sz, at=0):
    """Fill with the mountain's own stone, banded. This is what an exposed piece looks like
    from outside, and it is why none of the shells are masonry (section 5.2)."""
    for y in range(sy):
        p.box(0, y, 0, sx - 1, y, sz - 1, ROCK if (y + at) % 4 else BAND)


# ------------------------------------------------------------------------- the way down
def sink(p, y0, y1, off=0, fill=DEEP, landing=None):
    """The hole and the ladder in it. `off` turns the gatehouse's coordinates into this
    piece's, so the four pieces the column runs through cannot drift apart (section 11)."""
    x0, x1, z0, z1 = (v - off for v in HOLE)
    for x in range(x0 - 1, x1 + 2):
        for z in range(z0 - 1, z1 + 2):
            for y in range(y0, y1 + 1):
                if p.grid.get((x, y, z), (AIR,))[0] == AIR:
                    p.set(x, y, z, fill)
    for x in range(x0, x1 + 1):
        for y in range(y0, y1 + 1):
            for z in range(z0, z1 + 1):
                if z == RUNG[1] - off and x != RUNG[0] - off and y == landing:
                    continue
                p.set(x, y, z, AIR)
    for y in range(y0, y1 + 1):
        p.set(RUNG[0] - off, y, RUNG[1] - off, *ladder())


# ------------------------------------------------------------------------- the gatehouse
def gatehouse():
    """The start, and the only piece of this dungeon above ground: a squat hall of deepslate
    with a great arch in its north face, two towers beside it, and the shaft in the floor.

    Nothing branches from it. A ring of wall pieces or a spread of yards is what the fortress
    and the graveyard do, and on jagged peaks either one stands on stilts of its own footing.
    """
    n = GATE
    p = Piece(n, GROUND + 17, n, AIR)
    g, mid = GROUND, n // 2
    p.box(0, g, 0, n - 1, g, n - 1, POLISH)                        # the floor, on the ground
    p.box(0, g + 1, 0, n - 1, g + 10, n - 1, DEEP)                 # the walls
    p.box(1, g + 1, 1, n - 2, g + 10, n - 2, AIR)
    for x in range(n):                                             # a course of tuff at foot
        for z in range(n):
            if x in (0, n - 1) or z in (0, n - 1):
                p.set(x, g + 1, z, TUFF)
    p.box(0, g + 11, 0, n - 1, g + 11, n - 1, TILE)                # the roof
    for y in range(g + 1, g + 12):                                 # corner buttresses
        for x, z in ((0, 0), (0, n - 1), (n - 1, 0), (n - 1, n - 1)):
            p.set(x, y, z, POLISH)

    # the great arch, north face. No jigsaw: it is a door you walk through, not a socket
    p.box(mid - 2, g + 1, 0, mid + 2, g + 4, 0, AIR)
    p.box(mid - 1, g + 5, 0, mid + 1, g + 5, 0, AIR)
    p.set(mid, g + 6, 0, CHISEL)
    for x in (mid - 3, mid + 3):                                   # the towers beside it
        for y in range(g + 1, g + 15):
            for z in (0, 1):
                p.set(x, y, z, POLISH if y % 4 == 0 else DEEP)
        p.set(x, g + 15, 0, LANTERN, STANDING)
        p.set(x, g + 15, 1, LANTERN, STANDING)
    for a in (4, n - 5):                                           # slit windows
        for x, z in ((0, a), (n - 1, a)):
            p.box(x, g + 5, z, x, g + 7, z, AIR)
            p.set(x, g + 5, z, BARS, GRID)

    for x in (4, n - 5):                                           # two rows of pillars
        for z in (5, mid, n - 6):
            for y in range(g + 1, g + 10):
                p.set(x, y, z, CHISEL if y in (g + 1, g + 9) else POLISH)
            p.set(x, g + 10, z, CHAIN, {'axis': 'y', 'waterlogged': 'false'})

    # the smithy along the south wall: furnaces, an anvil, a grindstone, chests
    p.box(2, g + 1, n - 3, n - 3, g + 1, n - 3, TUFF)
    for x in (6, 8):
        p.set(x, g + 2, n - 3, FURNACE, {'facing': 'north', 'lit': 'true'})
    p.set(mid + 2, g + 2, n - 3, ANVIL, {'facing': 'north'})
    p.set(mid + 4, g + 2, n - 3, SMITH)
    p.set(3, g + 2, n - 3, GRINDSTONE, {'face': 'floor', 'facing': 'north'})
    p.set(2, g + 1, 2, *chest('dwarf_gate', 'south'))
    p.set(n - 3, g + 1, 2, *chest('dwarf_gate', 'south'))
    for x, z in ((3, 6), (n - 4, 6)):                              # braziers by the door
        p.set(x, g + 1, z, TUFF)
        p.set(x, g + 2, z, CAMPFIRE, FIRE)
    p.set(2, g + 1, n - 6, BARREL, {'facing': 'up', 'open': 'false'})
    p.set(n - 3, g + 1, n - 6, *chest('dwarf_gate', 'west'))

    floor_and_hole(p)
    return p


def floor_and_hole(p):
    """The gatehouse floor is solid except for the one way down."""
    g = GROUND
    x0, x1, z0, z1 = HOLE
    for x in range(GATE):
        for z in range(GATE):
            if x0 <= x <= x1 and z0 <= z <= z1:
                continue
            if p.grid.get((x, g, z), (AIR,))[0] in (AIR, 'minecraft:ladder'):
                p.set(x, g, z, POLISH)
    for x in range(x0 - 1, x1 + 2):                                # a kerb round the hole
        for z in range(z0 - 1, z1 + 2):
            if not (x0 <= x <= x1 and z0 <= z <= z1):
                p.set(x, g, z, CHISEL)
    sink(p, 0, g, landing=g)
    p.jigsaw(JIG[0], 0, JIG[1], 'down_east', POOL['down'], POLISH, joint='aligned',
             priority=PRIORITY, name=DOWN, target=DOWN)


# ------------------------------------------------------------------------------ the shafts
def shaft(step):
    """One of two, chained by single-element pools so the hall is always 42 below the door.

    Both carry a jigsaw at each end and both of those are named the same, which section 13
    warns about - but a vertical joint is safe, because rotation is about the y axis and a
    jigsaw that points down can never be turned to point up."""
    p = Piece(CELL, SHAFT_H, CELL, ROCK)
    bedrock(p, CELL, SHAFT_H, CELL, at=step * SHAFT_H)
    top = SHAFT_H - 1
    jx, jz = JIG[0] - SHAFT_AT, JIG[1] - SHAFT_AT
    for x in range(CELL):
        for y in range(SHAFT_H):
            for z in range(CELL):
                if p.grid.get((x, y, z), (AIR,))[0] in (AIR, 'minecraft:ladder'):
                    p.set(x, y, z, ROCK)
    sink(p, 0, top, off=SHAFT_AT, fill=ROCK)
    p.jigsaw(jx, top, jz, 'up_east', EMPTY, ROCK, joint='aligned', name=DOWN, target=DOWN)
    if step == 1:
        p.jigsaw(jx, 0, jz, 'down_east', POOL['deep'], ROCK, joint='aligned',
                 priority=PRIORITY, name=DOWN, target=DOWN)
    else:
        p.jigsaw(jx, 0, jz, 'down_east', POOL['hall_first'], ROCK, joint='aligned',
                 priority=PRIORITY, name=HALL, target=HALL)
    return p


# -------------------------------------------------------------------------------- the hall
def rock_room(doors, height=CELL, floor_at=0):
    """A cell of the hall, cut into rock: one wall thick, seven cubed like every other cell
    in this mod (section 2). The shell is the mountain's stone; the deepslate is inside."""
    p = Piece(CELL, height, CELL, ROCK)
    bedrock(p, CELL, height, CELL)
    p.box(1, floor_at + 1, 1, CELL - 2, floor_at + CELL - 2, CELL - 2, AIR)
    p.box(0, floor_at, 0, CELL - 1, floor_at, CELL - 1, TILE)
    mid = CELL // 2
    for side in doors:
        if side == 'west':
            p.box(0, floor_at + 1, mid - 1, 0, floor_at + 4, mid + 1, AIR)
        elif side == 'east':
            p.box(CELL - 1, floor_at + 1, mid - 1, CELL - 1, floor_at + 4, mid + 1, AIR)
        elif side == 'north':
            p.box(mid - 1, floor_at + 1, 0, mid + 1, floor_at + 4, 0, AIR)
        else:
            p.box(mid - 1, floor_at + 1, CELL - 1, mid + 1, floor_at + 4, CELL - 1, AIR)
    return p


HALL_AT = {'west': (0, 3, 'west_up'), 'east': (CELL - 1, 3, 'east_up'),
           'north': (3, 0, 'north_up'), 'south': (3, CELL - 1, 'south_up')}


def hall_door(p, side, pool, y=0, name=HALL, target=HALL, priority=0):
    x, z, orientation = HALL_AT[side]
    p.jigsaw(x, y, z, orientation, pool, ROCK, priority=priority, name=name, target=target)


def hall_hub():
    """Where the ladder lands. Three doors, and the pillar the ladder hangs on (section 24)."""
    p = rock_room(['west', 'north', 'south'])
    x0, x1, z0, z1 = (v - SHAFT_AT for v in HOLE)
    jx, jz = JIG[0] - SHAFT_AT, JIG[1] - SHAFT_AT
    for x in range(CELL):
        for z in range(CELL):
            if p.grid.get((x, CELL - 1, z), (AIR,))[0] in (AIR, 'minecraft:ladder'):
                p.set(x, CELL - 1, z, ROCK)
    for y in range(1, CELL):
        p.set(jx, y, jz, DEEP)
    p.box(x0, CELL - 1, z0, x1, CELL - 1, z1, AIR)
    p.jigsaw(jx, CELL - 1, jz, 'up_east', EMPTY, DEEP, joint='aligned',
             name=HALL, target=HALL)
    for y in range(1, CELL):
        p.set(RUNG[0] - SHAFT_AT, y, RUNG[1] - SHAFT_AT, *ladder())
    hall_door(p, 'west', POOL['halls'])
    hall_door(p, 'north', POOL['halls'])
    hall_door(p, 'south', POOL['king_approach_1'], name=HALL, target=KING, priority=PRIORITY)
    p.set(1, 1, 1, POLISH)
    p.set(1, 2, 1, LANTERN, STANDING)
    p.set(CELL - 2, 1, 1, *chest('dwarf_gate', 'west'))
    return p


def chasm():
    """Two cells tall: the walkway on top, lava at the bottom, and the span across it three
    wide at the doors and one in the middle.

    Not a trap - a hole with lava in it is the same hazard whoever arrives first, which is
    the only kind this mod keeps (section 12)."""
    floor = CELL
    p = rock_room(['west', 'east'], height=CELL * 2, floor_at=floor)
    mid = CELL // 2
    p.box(1, 1, 1, CELL - 2, floor - 1, CELL - 2, AIR)             # the pit
    p.box(1, 1, 1, CELL - 2, 1, CELL - 2, LAVA, SOURCE)            # walled in, so it stays
    for x in range(1, CELL - 1):
        for z in range(1, CELL - 1):
            span = (mid - 1 <= z <= mid + 1) if x in (1, CELL - 2) else (z == mid)
            if not span:
                p.set(x, floor, z, AIR)
    for x, z in ((1, 1), (CELL - 2, CELL - 2)):                    # chains into the dark
        for y in range(floor + 2, floor + CELL - 1):
            p.set(x, y, z, CHAIN, {'axis': 'y', 'waterlogged': 'false'})
    p.set(mid, floor + CELL - 2, mid, LANTERN, HANGING)
    hall_door(p, 'west', POOL['halls'], y=floor)
    hall_door(p, 'east', POOL['halls'], y=floor)
    return p


def hall(kind):
    doors = {'passage': ['west', 'east'], 'corner': ['west', 'south'],
             'cross': ['west', 'east', 'north', 'south'],
             'guard': ['west', 'east', 'north', 'south'],
             'forge': ['west', 'east'], 'drift': ['west', 'east'],
             'vein': ['west'], 'store': ['west']}[kind]
    p = rock_room(doors)
    for side in doors:
        hall_door(p, side, POOL['halls'])
    mid = CELL // 2
    if kind == 'passage':
        for z in (1, CELL - 2):
            p.set(1, 1, z, POLISH)
            p.set(1, 2, z, LANTERN, STANDING)
        p.box(CELL - 2, 1, 1, CELL - 2, 3, 1, DEEP)
    elif kind == 'corner':
        p.set(CELL - 2, 1, 1, POLISH)
        p.set(CELL - 2, 2, 1, LANTERN, STANDING)
        p.set(1, 1, CELL - 2, MAGMA)
    elif kind == 'cross':
        p.box(mid - 1, 0, mid - 1, mid + 1, 0, mid + 1, POLISH)
        for x, z in ((1, 1), (1, CELL - 2), (CELL - 2, 1), (CELL - 2, CELL - 2)):
            for y in (1, 2, 3):
                p.set(x, y, z, CHISEL if y == 3 else POLISH)
            p.set(x, 4, z, LANTERN, STANDING)
    elif kind == 'guard':
        p.box(mid - 1, 0, mid - 1, mid + 1, 0, mid + 1, TUFF)
        p.set(mid, 1, mid, 'minecraft:spawner', None, mob_spawner('minecraft:skeleton', 1))
        p.set(1, 1, 1, BARS, GRID)
        p.set(CELL - 2, 1, CELL - 2, BARS, GRID)
    elif kind == 'forge':
        # the forge hall in miniature. The trough runs along the north wall, where there is
        # no doorway, flush with the floor and behind a rim of tuff - so it is something you
        # step over rather than something that runs into the maze
        p.box(1, 1, 1, CELL - 2, 1, 1, LAVA, SOURCE)
        p.box(1, 1, 2, CELL - 2, 1, 2, TUFF)
        p.set(1, 1, CELL - 2, ANVIL, {'facing': 'north'})
        for x in (2, CELL - 3):
            p.set(x, 1, CELL - 2, FURNACE, {'facing': 'north', 'lit': 'true'})
        p.set(mid, 1, CELL - 2, *chest('dwarf_forge', 'north'))
        p.set(CELL - 2, 1, CELL - 2, IRON)
        p.set(mid, CELL - 2, mid, LANTERN, HANGING)
    elif kind == 'drift':
        # the mine cart road: rails, timbering, a lamp on the props
        for x in range(CELL):
            p.set(x, 1, mid, RAIL, {'shape': 'east_west', 'waterlogged': 'false'})
        for z in (1, CELL - 2):
            for x in (1, CELL - 2):
                p.set(x, 1, z, LOG, {'axis': 'y'})
                p.set(x, 2, z, LOG, {'axis': 'y'})
                p.set(x, 3, z, PLANK)
        p.box(2, 3, 1, CELL - 3, 3, 1, PLANK)
        p.box(2, 3, CELL - 2, CELL - 3, 3, CELL - 2, PLANK)
        p.set(1, 4, 1, LANTERN, STANDING)
        p.set(CELL - 2, 1, CELL - 2, *chest('dwarf_drift', 'west'))
    elif kind == 'vein':
        # what they were digging for. The cell is filled back in with rock and only the adit
        # is cut, so the ore sits in stone rather than floating in a room - and a pick is the
        # only way further in, which is the one interaction a wandering mob cannot do for you
        # (section 12)
        p.box(1, 1, 1, CELL - 2, CELL - 2, CELL - 2, ROCK)
        for x in range(1, CELL - 1):
            for y in range(1, CELL - 1):
                for z in range(1, CELL - 1):
                    if (x * 5 + y * 3 + z * 7) % 6 == 0:
                        p.set(x, y, z, 'minecraft:iron_ore' if (x + z) % 3 else
                              'minecraft:gold_ore' if (x + y) % 5 else
                              'minecraft:diamond_ore')
                    elif (x * 3 + z) % 4 == 0 and y < 3:
                        p.set(x, y, z, 'minecraft:coal_ore')
        p.box(1, 1, mid - 1, mid, 4, mid + 1, AIR)                 # the adit and its face
        p.set(mid, 1, mid, *chest('dwarf_drift', 'west'))
        p.set(mid - 1, 4, mid, LANTERN, HANGING)
    elif kind == 'store':
        p.box(1, 1, 1, CELL - 2, 1, 1, TUFF)
        p.set(1, 2, 1, BARREL, {'facing': 'up', 'open': 'false'})
        p.set(CELL - 2, 2, 1, BARREL, {'facing': 'up', 'open': 'false'})
        p.set(mid, 1, CELL - 2, *chest('dwarf_forge', 'north'))
        p.set(mid, 2, 1, *chest('dwarf_drift', 'south'))
        p.set(1, 1, CELL - 2, CAULDRON)
        p.set(mid, CELL - 2, mid, LANTERN, HANGING)
    return p


def hall_cap():
    p = Piece(1, CELL, CELL, ROCK)
    bedrock(p, 1, CELL, CELL)
    p.jigsaw(0, 0, 3, 'west_up', POOL['hall_caps'], ROCK, name=HALL, target=HALL)
    return p


def approach(step):
    p = rock_room(['west', 'east', 'north'])
    p.jigsaw(0, 0, 3, 'west_up', POOL['halls'], ROCK, name=KING, target=HALL)
    nxt = ('king_approach_%d' % (step + 1)) if step < MIN_BOSS_STEPS else 'king_approach'
    hall_door(p, 'east', POOL[nxt], name=HALL, target=KING, priority=PRIORITY)
    hall_door(p, 'north', POOL['halls'])
    p.set(1, 1, 1, POLISH)
    p.set(1, 2, 1, LANTERN, STANDING)
    return p


def forge_hall():
    """His hall: a forge with a barred trough of lava at the far end, the king on the dais,
    and his smiths in the four corners."""
    sx, sy, sz = BOSS
    p = Piece(sx, sy, sz, ROCK)
    bedrock(p, sx, sy, sz)
    p.box(1, 1, 1, sx - 2, sy - 2, sz - 2, AIR)
    p.box(0, 0, 0, sx - 1, 0, sz - 1, TILE)
    p.jigsaw(0, 0, sz // 2, 'west_up', EMPTY, ROCK, name=KING, target=HALL)
    p.box(0, 1, sz // 2 - 1, 0, 4, sz // 2 + 1, AIR)

    c = sx // 2
    for x0, z0 in ((4, 4), (4, sz - 6), (sx - 6, 4), (sx - 6, sz - 6)):   # the four columns
        for y in range(1, sy - 1):
            p.box(x0, y, z0, x0 + 1, y, z0 + 1, POLISH if y % 4 else CHISEL)
    p.box(c - 2, 1, sz - 9, c + 2, 1, sz - 2, TUFF)                 # the trough and its rim
    p.box(c - 1, 1, sz - 8, c + 1, 1, sz - 3, LAVA, SOURCE)
    p.box(c - 3, 1, 3, c + 3, 1, 8, TUFF)                           # the dais
    p.box(c - 2, 2, 4, c + 2, 2, 7, POLISH)
    p.set(c, 3, 5, 'minecraft:trial_spawner', TRIAL_STATE, trial_spawner('smith_king'))
    p.set(c - 2, 3, 4, ANVIL, {'facing': 'south'})
    p.set(c + 2, 3, 4, ANVIL, {'facing': 'south'})
    p.set(c - 3, 2, 8, SMITH)
    p.set(c + 3, 2, 8, GRINDSTONE, {'face': 'floor', 'facing': 'north'})
    for x, z in ((5, 12), (sx - 6, 12), (5, sz - 4), (sx - 6, sz - 4)):
        p.set(x, 1, z, 'minecraft:trial_spawner', TRIAL_STATE, trial_spawner('forge_guards'))
    for x in (3, sx - 4):                                           # furnaces along the walls
        for z in (6, 10, 14):
            p.set(x, 1, z, FURNACE, {'facing': 'west' if x > c else 'east', 'lit': 'true'})
    for x, z in ((c, 10), (4, c), (sx - 5, c), (c, sz - 4)):
        p.set(x, sy - 2, z, LANTERN, HANGING)
    for x, z in ((2, 2), (sx - 3, 2), (2, sz - 3), (sx - 3, sz - 3)):
        p.set(x, 1, z, GOLD if (x + z) % 2 else IRON)
    return p


# ---------------------------------------------------------------------------------- pools
def element(location, weight):
    return ('    { "weight": %d, "element": { "element_type": "minecraft:single_pool_element",'
            '\n        "location": "%s:dwarf/%s", "projection": "rigid", '
            '"processors": "%s:dwarf_weathering" } }' % (weight, NS, location, NS))


def write_pool(name, elements, fallback):
    if not os.path.isdir(POOL_JSON):
        os.makedirs(POOL_JSON)
    text = ('{\n  "fallback": "%s",\n  "elements": [\n%s\n  ]\n}\n'
            % (fallback, ',\n'.join(elements)))
    with open(os.path.join(POOL_JSON, name + '.json'), 'w', encoding='utf-8',
              newline='\n') as f:
        f.write(text)


# ---------------------------------------------------------------------------------- checks
HANGS = {'minecraft:lantern', 'minecraft:ladder', 'minecraft:iron_bars',
         'minecraft:iron_chain', 'minecraft:rail', 'minecraft:lava', 'minecraft:campfire'}
AROUND = ((1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1))
BEHIND = {'north': (0, 0, 1), 'south': (0, 0, -1), 'east': (-1, 0, 0), 'west': (1, 0, 0)}
STANDS_ON = ('minecraft:anvil', 'minecraft:blast_furnace', 'minecraft:smithing_table',
             'minecraft:grindstone', 'minecraft:barrel', 'minecraft:campfire',
             'minecraft:lava_cauldron', 'minecraft:rail', 'minecraft:spawner',
             'minecraft:trial_spawner')


def fitting_problems(pieces):
    problems = []
    for name, piece in sorted(pieces.items()):
        size = piece.size

        def solid(pos):
            block = piece.grid.get(pos)
            return bool(block) and block[0] != AIR and block[0] not in HANGS

        for pos, (block, props) in sorted(piece.grid.items()):
            props = dict(props or ())
            if block in (AIR, 'minecraft:jigsaw'):
                continue
            inside = all(0 < pos[i] < size[i] - 1 for i in range(3))
            if block not in HANGS and inside and not any(
                    solid((pos[0] + d[0], pos[1] + d[1], pos[2] + d[2])) for d in AROUND):
                problems.append('%s: %s floats at %s' % (name, block.split(':')[-1], pos))
            if block == 'minecraft:ladder':
                d = BEHIND[props.get('facing', 'north')]
                if not solid((pos[0] + d[0], pos[1] + d[1], pos[2] + d[2])):
                    problems.append('%s: the ladder at %s has nothing behind it' % (name, pos))
            if block in STANDS_ON or block.endswith('chest'):
                if not solid((pos[0], pos[1] - 1, pos[2])):
                    problems.append('%s: the %s at %s stands on nothing'
                                    % (name, block.split(':')[-1], pos))
            if block == LANTERN and props.get('hanging') == 'true':
                if not solid((pos[0], pos[1] + 1, pos[2])):
                    problems.append('%s: the lantern at %s hangs on nothing' % (name, pos))
            if block.endswith('chest') and 'LootTable' not in (piece.extra.get(pos) or {}):
                problems.append('%s: the chest at %s has no loot table' % (name, pos))
    return problems


def lava_problems(pieces):
    """Lava that is not walled in runs, and a piece that leaks lava into the maze around it
    keeps leaking for as long as the world lasts. Every source block has to be able to see
    nothing but solid blocks, sideways and downwards."""
    problems = []
    for name, piece in sorted(pieces.items()):
        sx, sy, sz = piece.size
        for pos, (block, _) in sorted(piece.grid.items()):
            if block != LAVA:
                continue
            x, y, z = pos
            for dx, dy, dz in ((1, 0, 0), (-1, 0, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1)):
                side = (x + dx, y + dy, z + dz)
                if not (0 <= side[0] < sx and 0 <= side[1] < sy and 0 <= side[2] < sz):
                    problems.append("%s: the lava at %s is against the piece's own face and "
                                    "would run into whatever is placed next to it"
                                    % (name, pos))
                elif piece.grid[side][0] == AIR:
                    problems.append('%s: the lava at %s can run to %s' % (name, pos, side))
    return problems


def ladder_problems(pieces):
    at = {'gatehouse': (0, 0, 0), 'shaft_1': (SHAFT_AT, -SHAFT_H, SHAFT_AT),
          'shaft_2': (SHAFT_AT, -2 * SHAFT_H, SHAFT_AT),
          'hall_hub': (SHAFT_AT, -2 * SHAFT_H - CELL, SHAFT_AT)}
    x0, x1, z0, z1 = HOLE
    problems = []
    for y in range(at['hall_hub'][1] + 2, GROUND + 1):
        for x in range(x0, x1 + 1):
            for z in range(z0, z1 + 1):
                if z == RUNG[1] and x != RUNG[0]:
                    continue                    # the landing: solid on purpose
                for name, (ox, oy, oz) in at.items():
                    piece = pieces[name]
                    if 0 <= y - oy < piece.size[1]:
                        block = piece.grid[(x - ox, y - oy, z - oz)][0]
                        break
                else:
                    problems.append('nothing covers %s on the way down' % ((x, y, z),))
                    continue
                want = 'minecraft:ladder' if (x, z) == RUNG else AIR
                if block != want:
                    problems.append('%s has %s at %s in the shaft, where the climb needs %s'
                                    % (name, block.split(':')[-1], (x, y, z),
                                       want.split(':')[-1]))
    return problems


def verify(pieces):
    problems = ladder_problems(pieces) + fitting_problems(pieces) + lava_problems(pieces)
    for name, piece in pieces.items():
        if max(piece.size) > 48:
            problems.append('%s is %s: too big to rebuild by hand' % (name, piece.size))
        count = sum(1 for pos, (block, _) in piece.grid.items()
                    if block == 'minecraft:jigsaw'
                    and (piece.extra.get(pos) or {}).get('name') == KING)
        if count > 1:
            problems.append('%s carries %d jigsaws named %s; the chain could be entered '
                            'through its own continuation' % (name, count, KING))
    for line in problems:
        print('  PROBLEM  ' + line)
    if problems:
        raise SystemExit('the dwarven hall does not hold together')
    print('  checked: the ladder unbroken from the gatehouse floor to the hall 42 below, '
          'nothing hangs in mid-air, no lava can run, every chest has a table, one way into '
          'the king')


PASSABLE = {'air', 'ladder', 'lantern', 'iron_chain', 'rail', 'campfire'}


def walk_problems():
    """Assemble what was written and walk it the way the game would: in at the arch, down two
    shafts, into the hall."""
    import gen_level_doc as doc

    pieces, pools = doc.load_family('dwarf'), doc.load_pools('dwarf')
    start = pools['start']['elements'][0][1].split('/')[-1]
    placed, queue = [(start, (0, 0, 0), pieces[start])], [0]
    while queue:
        name, at, piece = placed[queue.pop(0)]
        for j in piece['jigsaws']:
            pool = pools.get(j['pool'].split('/')[-1])
            if not pool or len(pool['elements']) != 1:
                continue
            child_name = pool['elements'][0][1].split('/')[-1]
            child = pieces.get(child_name)
            if child is None or child_name == name:
                continue
            front, able = doc.facing(j['orientation']), []
            for turn in range(4):
                spun = doc.rotated(child, turn)
                able = [c for c in spun['jigsaws'] if c['name'] == j['target']
                        and doc.facing(c['orientation']) == doc.OPPOSITE[front]]
                if able:
                    child = spun
                    break
            if len(able) != 1:
                continue
            pos = tuple(at[k] + j['pos'][k] + doc.STEP[front][k] - able[0]['pos'][k]
                        for k in range(3))
            if any(p[0] == child_name and p[1] == pos for p in placed):
                continue
            placed.append((child_name, pos, child))
            queue.append(len(placed) - 1)

    world = {}
    for name, at, piece in placed:
        for (x, y, z), i in piece['grid'].items():
            world[(x + at[0], y + at[1], z + at[2])] = piece['palette'][i][0]

    def open_at(p):
        block = world.get(p)
        return block is None or block in PASSABLE

    def stand(p):
        x, y, z = p
        return open_at(p) and open_at((x, y + 1, z)) and not open_at((x, y - 1, z))

    g = GROUND
    door = (GATE // 2, g + 1, 1)
    seen, queue = {door}, [door]
    while queue:
        x, y, z = queue.pop()
        flat = [(x + 1, y, z), (x - 1, y, z), (x, y, z + 1), (x, y, z - 1)]
        moves = flat + [(a, y + 1, c) for a, _, c in flat] + [(a, y - 1, c) for a, _, c in flat]
        if world.get((x, y, z)) == 'ladder' or world.get((x, y + 1, z)) == 'ladder':
            moves.append((x, y + 1, z))
        if world.get((x, y - 1, z)) == 'ladder':
            moves.append((x, y - 1, z))
        for move in moves:
            if move not in seen and (world.get(move) == 'ladder' or stand(move)):
                seen.add(move)
                queue.append(move)

    want = {'the hall': (RUNG[0], -2 * SHAFT_H - CELL + 2, RUNG[1])}
    problems = []
    for label, spot in want.items():
        if not any((spot[0], spot[1] + dy, spot[2]) in seen for dy in (-1, 0, 1)):
            problems.append('%s cannot be walked to from the gatehouse' % label)
    return problems


def main():
    if not os.path.isdir(DST):
        os.makedirs(DST)
    pieces = {
        'gatehouse': gatehouse(),
        'shaft_1': shaft(1), 'shaft_2': shaft(2), 'hall_hub': hall_hub(),
        'passage': hall('passage'), 'corner': hall('corner'), 'cross': hall('cross'),
        'guard': hall('guard'), 'forge': hall('forge'), 'drift': hall('drift'),
        'vein': hall('vein'), 'store': hall('store'), 'chasm': chasm(),
        'cap': hall_cap(), 'forge_hall': forge_hall(),
    }
    for step in range(1, MIN_BOSS_STEPS + 1):
        pieces['approach_%d' % step] = approach(step)
    verify(pieces)
    for name, piece in sorted(pieces.items()):
        piece.write(os.path.join(DST, name + '.nbt'))
        print('  %-16s %s' % (name, list(piece.size)))

    write_pool('start', [element('gatehouse', 1)], EMPTY)
    write_pool('down', [element('shaft_1', 1)], EMPTY)
    write_pool('deep', [element('shaft_2', 1)], EMPTY)
    write_pool('hall_first', [element('hall_hub', 1)], EMPTY)
    write_pool('halls', [element('passage', 10), element('corner', 9),
                         element('cross', 4), element('guard', 5),
                         element('forge', 6), element('drift', 7),
                         element('vein', 5), element('store', 5),
                         element('chasm', 5)],
               POOL['hall_caps'])
    write_pool('hall_caps', [element('cap', 1)], EMPTY)
    for step in range(1, MIN_BOSS_STEPS + 1):
        write_pool('king_approach_%d' % step, [element('approach_%d' % step, 1)],
                   POOL['hall_caps'])
    write_pool('king_approach', [element('forge_hall', 1),
                                 element('approach_%d' % MIN_BOSS_STEPS, 1)],
               POOL['hall_caps'])
    print('  pools -> %s' % os.path.relpath(POOL_JSON, ROOT))
    problems = walk_problems()
    for line in problems:
        print('  PROBLEM  ' + line)
    if problems:
        raise SystemExit('the dwarven hall is built but you cannot walk it')
    print('  walked: the gatehouse down two shafts into the hall')


if __name__ == '__main__':
    main()
