# -*- coding: utf-8 -*-
"""The Warlord's Camp: a palisade round a longhouse, and a timbered mine under it.

    python tools/generate_camp.py        (or through make_pieces.py)

Writes data/sydungeon/structure/camp/*.nbt and the pools that join them.

THE ICE FORTRESS'S MACHINE, IN ACACIA
The ring is built the way the fortress's curtain wall is (CLAUDE.md section 19): the longhouse
is the start piece and calls a palisade panel on each face, and only the north and south
panels call the watchtowers at their ends, so each tower is called once and its rotation is
known. The boxes leave the middle of the camp alone, which is what lets the way down hang off
the start where nothing has fenced it.

    longhouse 21x14x21   start, the middle of the camp
    palisade  21x21x14   two courses of standing logs, and the yard in front of them
    tower     14x21x14   the outer corner, with the archers on top
    gate      21x21x14   the west way in

WHAT IS DIFFERENT FROM THE FORTRESS
A palisade is thin. The fortress's wall was seven blocks through, so a tower could only open
onto the walkway on top of it; here the wall is two, the yard reaches the towers, and their
doors are at ground level where anyone would put them.

Badlands is the reason every piece carries seven courses of foundation (section 18): mesa
terrain falls away inside a single structure, and a camp standing on stumps looks worse than
a fortress does.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import nbt  # noqa: E402
from generate_pieces import Piece  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DST = os.path.join(ROOT, 'src', 'main', 'resources', 'data', 'sydungeon', 'structure', 'camp')
POOL_JSON = os.path.join(ROOT, 'src', 'main', 'resources', 'data', 'sydungeon', 'worldgen',
                         'template_pool', 'camp')
HAND = os.path.join(ROOT, 'tools', 'handmade', 'camp')

NS = 'sydungeon'
WALL = NS + ':cmp_wall'          # longhouse -> panel
CORNER_A = NS + ':cmp_corner_a'  # the north panel's ends -> the towers
CORNER_B = NS + ':cmp_corner_b'
DOWN = NS + ':cmp_down'          # the one way from the longhouse to the mine
DRIFT = NS + ':cmp_drift'        # the mine's connector
LORD = NS + ':cmp_lord'          # the boss branch, its own name so it cannot run backwards
EMPTY = 'minecraft:empty'
PRIORITY = 10

CELL = 7
HOUSE = 21                       # the longhouse is three cells across
FOOT = 7                         # foundation courses below the yard, on the children
GROUND = 0                       # the start piece's floor: a start is moved so that
                                 # minY + 1 is the first free block, so y=0 is the
                                 # terrain's own top block (section 30)
HIGH = 14                        # box height above it
FENCE_DEPTH = 2                  # how thick the palisade itself is
YARD = 2 * CELL - FENCE_DEPTH    # the yard a panel carries in front of it, so a panel is
                                 # two cells deep all told and the camp comes to 49 across
PANEL = (HOUSE, FOOT + HIGH, YARD + FENCE_DEPTH)
TOWER = (2 * CELL, FOOT + HIGH + CELL, 2 * CELL)
SHAFT_H = 35                     # badlands falls away thirty blocks inside one structure,
                                 # so the workings start below the valley floors, not just
                                 # below the plateau the camp stands on
BOSS = (21, 14, 21)
MIN_BOSS_STEPS = 3
PALE = 5                         # how tall the palisade stands above the yard
TOWER_TOP = 13

# the way down, in the longhouse's coordinates: the middle of the floor, the ladder against
# the south wall of the hole with its own row kept solid as a landing (section 24)
HOLE = (HOUSE // 2, HOUSE // 2) # one column, dead centre of the piece
RUNG = HOLE                      # the ladder is the hole (section 33)
JIG = (HOLE[0], HOLE[1] + 1)     # the post it hangs on, one out of the hole

SHAFT_AT = CELL                  # where the shaft hangs under the longhouse

LOG = 'minecraft:acacia_log'
STRIP = 'minecraft:stripped_acacia_log'
PLANK = 'minecraft:acacia_planks'
FENCE = 'minecraft:acacia_fence'
STAIR = 'minecraft:acacia_stairs'
SLAB = 'minecraft:acacia_slab'
TRAP = 'minecraft:acacia_trapdoor'
DIRT = 'minecraft:coarse_dirt'
MUD = 'minecraft:packed_mud'
COBBLE = 'minecraft:cobblestone'
GRAVEL = 'minecraft:gravel'
CLAY = 'minecraft:terracotta'
ROCK = 'minecraft:stone'         # what the mine is cut out of, and therefore what shows
BAND = 'minecraft:orange_terracotta'   # a course of it every few, so an exposed face reads
                                       # as a layer of the mesa rather than as masonry
BARS = 'minecraft:iron_bars'
LANTERN = 'minecraft:lantern'
WEB = 'minecraft:cobweb'
HAY = 'minecraft:hay_block'
AIR = 'minecraft:air'

HANGING = {'hanging': 'true', 'waterlogged': 'false'}
STANDING = {'hanging': 'false', 'waterlogged': 'false'}
GRID = {'north': 'true', 'south': 'true', 'east': 'true', 'west': 'true',
        'waterlogged': 'false'}
POST = {'north': 'false', 'south': 'false', 'east': 'false', 'west': 'false',
        'waterlogged': 'false'}

POOL = {k: NS + ':camp/' + k for k in
        ['start', 'panels', 'panels_end', 'gate', 'corner_a', 'corner_b', 'down',
         'mine_first', 'drifts', 'drift_caps', 'lord_approach'] +
        ['lord_approach_%d' % i for i in range(1, MIN_BOSS_STEPS + 1)]}

TRIAL_STATE = {'trial_spawner_state': 'inactive', 'ominous': 'false'}
ANY_LIGHT = {'block_light_limit': {'min_inclusive': nbt.Int(0), 'max_inclusive': nbt.Int(15)}}


def trial_spawner(config):
    return {'id': 'minecraft:trial_spawner',
            'normal_config': NS + ':camp/' + config,
            'ominous_config': NS + ':camp/' + config,
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


def ladder(facing='north'):
    return ('minecraft:ladder', {'facing': facing, 'waterlogged': 'false'})


# ------------------------------------------------------------------------- the way down
def sink(p, y0, y1, off=0, fill=PLANK):
    """The way down: one column of ladder, and a ring of solid block round it.

    Three wide was worse than it looked - you stepped in and fell past the ladder, and every
    piece the column ran through had to keep a landing to step off onto (section 24). One
    column is a ladder you simply walk into. The ring is written whatever was there before,
    because a gap in it is where the water gets in (section 33)."""
    cx, cz = (v - off for v in HOLE)
    for x in range(cx - 1, cx + 2):
        for z in range(cz - 1, cz + 2):
            for y in range(y0, y1 + 1):
                p.set(x, y, z, fill)
    for y in range(y0, y1 + 1):
        p.set(cx, y, cz, *ladder())



# -------------------------------------------------------------------------- the longhouse
def longhouse():
    """The start: the warlord's hall in the middle of the camp. Four doors call the palisade
    and the hole in its floor is the only way into the mine."""
    n = HOUSE
    p = Piece(n, GROUND + HIGH, n, AIR)
    g, mid = GROUND, n // 2
    p.box(0, g, 0, n - 1, g, n - 1, PLANK)                        # the floor, on the ground
    p.box(0, g + 1, 0, n - 1, g + 6, n - 1, PLANK)                # walls
    p.box(1, g + 1, 1, n - 2, g + 6, n - 2, AIR)
    for x, z in ((0, 0), (0, n - 1), (n - 1, 0), (n - 1, n - 1)):  # corner posts
        for y in range(g + 1, g + 7):
            p.set(x, y, z, LOG, {'axis': 'y'})
    for i in range(n):                                            # a low roof of slabs
        for j in range(n):
            p.set(i, g + 7, j, SLAB, {'type': 'bottom', 'waterlogged': 'false'})
    for i in range(1, n - 1, 2):                                  # and a ridge of logs
        p.set(i, g + 8, mid, LOG, {'axis': 'x'})
    for y in (g + 3,):                                            # shutters
        for a in (4, mid, n - 5):
            for x, z in ((0, a), (n - 1, a), (a, 0), (a, n - 1)):
                p.set(x, y, z, TRAP, {'facing': 'north', 'half': 'top', 'open': 'false',
                                      'powered': 'false', 'waterlogged': 'false'})

    for side in ('west', 'east', 'north', 'south'):               # the four ways out
        pool = POOL['gate'] if side == 'west' else (
            POOL['panels_end'] if side in ('north', 'south') else POOL['panels'])
        if side == 'west':
            p.box(0, g + 1, mid - 1, 0, g + 4, mid + 1, AIR)
            p.jigsaw(0, g, mid, 'west_up', pool, PLANK, priority=PRIORITY,
                     name=WALL, target=WALL)
        elif side == 'east':
            p.box(n - 1, g + 1, mid - 1, n - 1, g + 4, mid + 1, AIR)
            p.jigsaw(n - 1, g, mid, 'east_up', pool, PLANK, priority=PRIORITY,
                     name=WALL, target=WALL)
        elif side == 'north':
            p.box(mid - 1, g + 1, 0, mid + 1, g + 4, 0, AIR)
            p.jigsaw(mid, g, 0, 'north_up', pool, PLANK, priority=PRIORITY,
                     name=WALL, target=WALL)
        else:
            p.box(mid - 1, g + 1, n - 1, mid + 1, g + 4, n - 1, AIR)
            p.jigsaw(mid, g, n - 1, 'south_up', pool, PLANK, priority=PRIORITY,
                     name=WALL, target=WALL)

    p.set(3, g + 1, 3, 'minecraft:campfire',
          {'facing': 'north', 'lit': 'true', 'signal_fire': 'false', 'waterlogged': 'false'})
    p.box(n - 5, g + 1, 2, n - 3, g + 1, 2, MUD)                  # the war table
    p.set(n - 4, g + 2, 2, 'minecraft:cartography_table')
    p.set(n - 3, g + 1, n - 3, *chest('camp_hall', 'west'))
    p.set(2, g + 1, n - 3, 'minecraft:barrel', {'facing': 'up', 'open': 'false'})
    p.set(n - 3, g + 1, 2, 'minecraft:grindstone', {'face': 'floor', 'facing': 'south'})
    for x, z in ((4, 4), (n - 5, 4), (4, n - 5), (n - 5, n - 5)):
        p.set(x, g + 6, z, LANTERN, HANGING)
    p.set(mid, g + 1, 2, 'minecraft:spawner', None, mob_spawner('minecraft:vindicator', 1))

    floor_and_hole(p)
    return p


def floor_and_hole(p):
    """The hall's floor is solid except for the one way down. Run over a hand-built longhouse
    as well as the code's, so a hole left anywhere else in it gets closed."""
    g = GROUND
    cx, cz = HOLE
    for x in range(HOUSE):
        for z in range(HOUSE):
            if (x, z) == (cx, cz):
                continue
            if p.grid.get((x, g, z), (AIR,))[0] in (AIR, 'minecraft:ladder'):
                p.set(x, g, z, PLANK)
    # through the floor and the foundation both, and out of the bottom of the box: the
    # shaft hangs below the piece, not inside it. The landing is the floor course, which is
    # the one people stand on (section 24).
    sink(p, 0, g)
    p.jigsaw(JIG[0], 0, JIG[1], 'down_east', POOL['down'], DIRT, joint='aligned',
             priority=PRIORITY, name=DOWN, target=DOWN)


# --------------------------------------------------------------------------- the palisade
def yard(p, x0, x1, z0, z1):
    """Beaten earth, with the foundation under it and the air above carved out, so the camp
    has a flat yard however the mesa lies."""
    g = FOOT
    p.box(x0, 0, z0, x1, g - 1, z1, DIRT)
    p.box(x0, g, z0, x1, g, z1, DIRT)
    p.box(x0, g + 1, z0, x1, g + HIGH - 1, z1, AIR)
    for x in range(x0, x1 + 1):
        for z in range(z0, z1 + 1):
            if (x * 5 + z * 3) % 7 == 0:
                p.set(x, g, z, GRAVEL)


def palisade(p, x0, x1, z):
    """Two courses of standing logs with a sharpened top: the fence itself."""
    g = FOOT
    for x in range(x0, x1 + 1):
        for d in range(FENCE_DEPTH):
            p.box(x, 0, z + d, x, g - 1, z + d, DIRT)
            for y in range(g, g + PALE):
                p.set(x, y, z + d, LOG, {'axis': 'y'})
        p.set(x, g + PALE, z, FENCE, POST)
        p.set(x, g + PALE, z + 1, FENCE, POST)
    for x in range(x0, x1 + 1, 4):                       # braces on the inside
        for y in range(g + 1, g + PALE):
            p.set(x, y, z + FENCE_DEPTH, FENCE, POST)


def panel(ends=False, gate=False):
    """One side of the palisade and the yard in front of it."""
    sx, sy, sz = PANEL
    g, mid = FOOT, sx // 2
    p = Piece(sx, sy, sz, AIR)
    palisade(p, 0, sx - 1, 0)
    yard(p, 0, sx - 1, FENCE_DEPTH, sz - 1)

    if gate:
        for z in range(FENCE_DEPTH):                     # the gateway through the logs
            p.box(mid - 1, g + 1, z, mid + 1, g + 4, z, AIR)
        for x in (mid - 2, mid + 2):                     # gate posts, taller than the fence
            for y in range(g, g + PALE + 3):
                p.set(x, y, 0, LOG, {'axis': 'y'})
                p.set(x, y, 1, LOG, {'axis': 'y'})
        p.box(mid - 1, g + 5, 0, mid + 1, g + 5, 1, PLANK)
        p.set(mid, g + 4, 0, LANTERN, HANGING)    # under the lintel, not over it
        p.box(mid - 1, g, FENCE_DEPTH, mid + 1, g, sz - 1, MUD)   # the road in
    if ends:
        p.jigsaw(0, g, sz - 3, 'west_up', POOL['corner_a'], DIRT, priority=PRIORITY,
                 name=CORNER_A, target=CORNER_A)
        p.jigsaw(sx - 1, g, sz - 3, 'east_up', POOL['corner_b'], DIRT, priority=PRIORITY,
                 name=CORNER_B, target=CORNER_B)
    for x in (3, sx - 4):                                # camp fires along the fence
        p.set(x, g + 1, FENCE_DEPTH + 1, 'minecraft:campfire',
              {'facing': 'north', 'lit': 'true', 'signal_fire': 'false',
               'waterlogged': 'false'})
    p.set(mid - 4, g + 1, FENCE_DEPTH + 2, 'minecraft:barrel', {'facing': 'up',
                                                                'open': 'false'})
    p.set(mid + 4, g + 1, FENCE_DEPTH + 2, *chest('camp_supply', 'north'))
    if not gate:
        p.set(mid, g + 1, sz - 3, 'minecraft:spawner', None,
              mob_spawner('minecraft:pillager', 1))
    # last, so nothing written above can rub the entry jigsaw out
    p.jigsaw(mid, g, sz - 1, 'south_up', EMPTY, DIRT, name=WALL, target=WALL)
    return p


def tower():
    """A corner: the watchtower in the outer quarter, the palisade running on along two
    arms, and the corner of the yard in the inner one. Drawn as the north-west; the
    north-east is its mirror."""
    sx, sy, sz = TOWER
    g = FOOT
    p = Piece(sx, sy, sz, AIR)
    palisade(p, CELL, sx - 1, 0)                                   # the arm running east
    for z in range(CELL, sz):                                      # and the one running south
        for d in range(FENCE_DEPTH):
            p.box(d, 0, z, d, g - 1, z, DIRT)
            for y in range(g, g + PALE):
                p.set(d, y, z, LOG, {'axis': 'y'})
        p.set(0, g + PALE, z, FENCE, POST)
        p.set(1, g + PALE, z, FENCE, POST)
    yard(p, CELL, sx - 1, CELL, sz - 1)
    yard(p, FENCE_DEPTH, CELL - 1, CELL, sz - 1)

    p.box(0, 0, 0, CELL - 1, g - 1, CELL - 1, DIRT)                # the tower
    p.box(0, g, 0, CELL - 1, g, CELL - 1, DIRT)
    for x, z in ((1, 1), (1, CELL - 2), (CELL - 2, 1), (CELL - 2, CELL - 2)):
        for y in range(g + 1, g + TOWER_TOP):
            p.set(x, y, z, LOG, {'axis': 'y'})
    p.box(1, g + TOWER_TOP, 1, CELL - 2, g + TOWER_TOP, CELL - 2, PLANK)   # the platform
    for i in range(1, CELL - 1):                                   # its rail
        for x, z in ((i, 1), (i, CELL - 2), (1, i), (CELL - 2, i)):
            p.set(x, g + TOWER_TOP + 1, z, FENCE, POST)
    p.box(2, g + TOWER_TOP + 1, 2, CELL - 3, g + TOWER_TOP + 1, CELL - 3, AIR)
    for x, z in ((1, 1), (1, CELL - 2), (CELL - 2, 1), (CELL - 2, CELL - 2)):
        p.set(x, g + TOWER_TOP + 1, z, LOG, {'axis': 'y'})   # the posts stand proud of the
                                                             # rail, and the ladder's top
                                                             # rung hangs on one of them
    p.set(2, g + TOWER_TOP + 1, CELL - 3, 'minecraft:spawner', None,
          mob_spawner('minecraft:pillager', 1))   # clear of the ladder's way through
    p.set(CELL - 3, g + TOWER_TOP + 1, CELL - 3, *chest('camp_supply', 'north'))
    # The climb goes all the way through the platform - the rail's gap at (3) is where you
    # step off it - because a ladder that stops under the boards leaves you nothing to stand
    # on when you get there (section 24).
    for y in range(g + 1, g + TOWER_TOP + 2):
        p.set(2, y, 1, *ladder('east'))        # hung on the corner post at (1, 1)
    p.set(3, g + TOWER_TOP + 1, 1, AIR)
    p.set(4, g + 1, 4, LANTERN, STANDING)      # on the ground: a watchtower has no ceiling

    # The anchor sits the same distance from the palisade as the panel's end jigsaw does, or
    # the tower lands eight blocks adrift of the ring it is supposed to close.
    p.jigsaw(sx - 1, g, sz - 3, 'east_up', EMPTY, DIRT, name=CORNER_A, target=CORNER_A)
    return p


MIRROR_FACE = {'east': 'west', 'west': 'east', 'north': 'north', 'south': 'south'}
MIRROR_AXIS = {'x': 'x', 'y': 'y', 'z': 'z'}


def mirrored(src, name, target):
    """The other handedness. Vanilla rotates but never mirrors, so this is the one shape we
    make twice (CLAUDE.md section 13)."""
    sx, sy, sz = src.size
    out = Piece(sx, sy, sz, AIR)
    for (x, y, z), (block, props) in src.grid.items():
        flipped = dict(props) if props else None
        if flipped:
            if flipped.get('facing') in MIRROR_FACE:
                flipped['facing'] = MIRROR_FACE[flipped['facing']]
            if 'east' in flipped and 'west' in flipped:
                flipped['east'], flipped['west'] = flipped['west'], flipped['east']
            if 'orientation' in flipped:
                front, up = flipped['orientation'].split('_')
                flipped['orientation'] = '%s_%s' % (MIRROR_FACE.get(front, front),
                                                    MIRROR_FACE.get(up, up))
        out.set(sx - 1 - x, y, z, block, flipped)
    for (x, y, z), extra in src.extra.items():
        entry = dict(extra)
        if entry.get('id') == 'minecraft:jigsaw':
            entry['name'], entry['target'] = name, target
        out.extra[(sx - 1 - x, y, z)] = entry
    return out


# ------------------------------------------------------------------------------- the mine
def shaft():
    """Down from the hall's floor into the workings. Shares the longhouse's x and z, so the
    ladder is one unbroken column - verify() climbs it."""
    p = Piece(CELL, SHAFT_H, CELL, MUD)
    bedrock(p, CELL, SHAFT_H, CELL)
    shaft_wiring(p, SHAFT_H - 1)
    return p


def shaft_wiring(p, top):
    # solid except for the climb: a hand-built shaft that still carries an older hole gets
    # it filled in here
    for x in range(CELL):
        for y in range(top + 1):
            for z in range(CELL):
                if p.grid.get((x, y, z), (AIR,))[0] in (AIR, 'minecraft:ladder'):
                    p.set(x, y, z, ROCK)
    sink(p, 0, top, off=SHAFT_AT, fill=ROCK)
    p.jigsaw(JIG[0] - SHAFT_AT, top, JIG[1] - SHAFT_AT, 'up_east', EMPTY, ROCK,
             joint='aligned', name=DOWN, target=DOWN)
    p.jigsaw(JIG[0] - SHAFT_AT, 0, JIG[1] - SHAFT_AT, 'down_east', POOL['mine_first'], ROCK,
             joint='aligned', priority=PRIORITY, name=DRIFT, target=DRIFT)


def bedrock(p, sx, sy, sz, at=0):
    """Fill a piece with the ground's own stone, banded like a mesa.

    This is what an exposed piece looks like from outside, and it is the whole reason the
    walls are stone rather than the camp's packed mud: a hollow box of masonry sticking out of
    an eroded slope reads as a mistake, and a lump of banded stone reads as the hill
    (2026-09-22 screenshot)."""
    for y in range(sy):
        course = ROCK if (y + at) % 5 else BAND
        p.box(0, y, 0, sx - 1, y, sz - 1, course)


def drift_room(doors, fill=None):
    """A cell of the workings: rock walls, a floor of dirt, and a timber frame inside - the
    camp dug this, and it is held up with what they had."""
    p = Piece(CELL, CELL, CELL, MUD)
    bedrock(p, CELL, CELL, CELL)
    p.box(1, 1, 1, CELL - 2, CELL - 2, CELL - 2, AIR)
    p.box(0, 0, 0, CELL - 1, 0, CELL - 1, DIRT)
    p.box(1, CELL - 2, 1, CELL - 2, CELL - 2, CELL - 2, PLANK)     # the ceiling boards
    mid = CELL // 2
    for side in doors:
        if side == 'west':
            p.box(0, 1, mid - 1, 0, 4, mid + 1, AIR)
        elif side == 'east':
            p.box(CELL - 1, 1, mid - 1, CELL - 1, 4, mid + 1, AIR)
        elif side == 'north':
            p.box(mid - 1, 1, 0, mid + 1, 4, 0, AIR)
        else:
            p.box(mid - 1, 1, CELL - 1, mid + 1, 4, CELL - 1, AIR)
    for x, z in ((1, 1), (1, CELL - 2), (CELL - 2, 1), (CELL - 2, CELL - 2)):
        for y in (1, 2, 3, 4):
            p.set(x, y, z, FENCE, POST)                            # pit props
    return p


DOOR_AT = {'west': (0, 0, 3, 'west_up'), 'east': (CELL - 1, 0, 3, 'east_up'),
           'north': (3, 0, 0, 'north_up'), 'south': (3, 0, CELL - 1, 'south_up')}


def door(p, side, pool, name=DRIFT, target=DRIFT, priority=0):
    x, y, z, orientation = DOOR_AT[side]
    p.jigsaw(x, y, z, orientation, pool, ROCK, priority=priority, name=name, target=target)


def mine_hub():
    """Where the ladder lands. Three drifts and one, on its own connector and placed first,
    to the warlord."""
    p = drift_room(['west', 'north', 'south'])
    hub_wiring(p)
    door(p, 'west', POOL['drifts'])
    door(p, 'north', POOL['drifts'])
    door(p, 'south', POOL['lord_approach_1'], name=DRIFT, target=LORD, priority=PRIORITY)
    p.set(1, 4, 1, LANTERN, HANGING)
    return p


def hub_wiring(p):
    """The hole in the ceiling and the post the ladder hangs on. The ceiling is closed first,
    so a hand-built hub that still carries an older hole does not end up with two; then the
    hole, then the jigsaw - the other way round the hole erases it (section 11)."""
    cx, cz = (v - SHAFT_AT for v in HOLE)
    jx, jz = JIG[0] - SHAFT_AT, JIG[1] - SHAFT_AT
    for x in range(CELL):
        for z in range(CELL):
            for y in (CELL - 2, CELL - 1):
                if p.grid.get((x, y, z), (AIR,))[0] in (AIR, 'minecraft:ladder'):
                    p.set(x, y, z, ROCK)
    for y in range(1, CELL):
        p.set(jx, y, jz, LOG, {'axis': 'y'})   # the post: the ladder hangs on it and the
                                               # jigsaw stands in it
    # through the ceiling boards as well as the ceiling: the drift is roofed with planks and
    # a hole cut only in the top course lands you on them
    for y in range(1, CELL):
        p.set(cx, y, cz, *ladder())            # the climb, up through the ceiling boards
    p.jigsaw(jx, CELL - 1, jz, 'up_east', EMPTY, LOG, joint='aligned',
             name=DRIFT, target=DRIFT)


def drift(kind):
    doors = {'drift': ['west', 'east'], 'drift_corner': ['west', 'south'],
             'drift_cross': ['west', 'east', 'north', 'south'],
             'guard': ['west', 'east', 'north', 'south'],
             'store': ['west'], 'cave_in': ['west', 'east'],
             'cage': ['west'], 'dig': ['west']}[kind]
    p = drift_room(doors)
    for side in doors:
        door(p, side, POOL['drifts'])
    mid = CELL // 2
    if kind == 'store':
        p.set(CELL - 2, 1, mid, *chest('camp_armoury', 'west'))
        p.set(1, 1, 1, 'minecraft:barrel', {'facing': 'up', 'open': 'false'})
        p.set(1, 1, CELL - 2, HAY, {'axis': 'y'})
        p.set(mid, 4, mid, LANTERN, HANGING)
    elif kind == 'cave_in':
        # no trigger: the roof fell in long ago and the drift is half shut
        p.box(1, 1, 1, CELL - 2, 3, 2, GRAVEL)
        p.box(mid - 1, 1, 1, mid + 1, 2, 2, AIR)
        for x, z in ((1, 3), (CELL - 2, 3)):
            p.set(x, 4, z, WEB)
        p.set(mid, 4, 2, WEB)
    elif kind == 'cage':
        # a ravager in an iron cage. Breaking it is the player's own idea, which is the only
        # kind of trap this mod keeps (section 12)
        for x in range(2, CELL - 2):
            for z in range(2, CELL - 2):
                for y in (1, 2, 3, 4):
                    if x in (2, CELL - 3) or z in (2, CELL - 3):
                        p.set(x, y, z, BARS, GRID)
        p.box(3, 1, 3, 3, 3, 3, AIR)
        p.set(3, 1, 3, 'minecraft:spawner', None, mob_spawner('minecraft:ravager', 1))
        p.set(1, 1, 1, HAY, {'axis': 'y'})
        p.set(mid, 4, 1, LANTERN, HANGING)
    elif kind == 'dig':
        p.box(1, 1, 1, CELL - 2, 1, CELL - 2, GRAVEL)
        for x, z in ((2, 2), (4, 3), (3, 4)):
            p.set(x, 1, z, 'minecraft:suspicious_gravel')
        p.set(CELL - 2, 2, CELL - 2, CLAY)
    elif kind == 'guard':
        p.set(mid, 1, mid, 'minecraft:spawner', None, mob_spawner('minecraft:pillager', 1))
        p.set(1, 1, 1, 'minecraft:barrel', {'facing': 'up', 'open': 'false'})
    return p


def drift_cap():
    p = Piece(1, CELL, CELL, ROCK)
    bedrock(p, 1, CELL, CELL)
    p.jigsaw(0, 0, 3, 'west_up', POOL['drift_caps'], ROCK, name=DRIFT, target=DRIFT)
    return p


def approach(step):
    """One link of the chain to the warlord. The way in is the only jigsaw named `lord`, so
    the chain cannot be entered through its own continuation (section 13)."""
    p = drift_room(['west', 'east', 'north'])
    p.jigsaw(0, 0, 3, 'west_up', POOL['drifts'], ROCK, name=LORD, target=DRIFT)
    nxt = ('lord_approach_%d' % (step + 1)) if step < MIN_BOSS_STEPS else 'lord_approach'
    door(p, 'east', POOL[nxt], name=DRIFT, target=LORD, priority=PRIORITY)
    door(p, 'north', POOL['drifts'])
    return p


def warlord_hall():
    """His hall: the deepest working, propped with whole trees, with the warlord on a dais of
    terracotta and his captains in the corners."""
    sx, sy, sz = BOSS
    p = Piece(sx, sy, sz, MUD)
    bedrock(p, sx, sy, sz)
    p.box(1, 1, 1, sx - 2, sy - 2, sz - 2, AIR)
    p.box(0, 0, 0, sx - 1, 0, sz - 1, DIRT)
    p.jigsaw(0, 0, sz // 2, 'west_up', EMPTY, ROCK, name=LORD, target=DRIFT)
    p.box(0, 1, sz // 2 - 1, 0, 4, sz // 2 + 1, AIR)

    for x0, z0 in ((3, 3), (3, sz - 5), (sx - 5, 3), (sx - 5, sz - 5)):
        for y in range(1, sy - 1):
            p.box(x0, y, z0, x0 + 1, y, z0 + 1, LOG, {'axis': 'y'})
    p.box(1, sy - 2, 1, sx - 2, sy - 2, sz - 2, PLANK)
    c = sx // 2
    p.box(c - 3, 1, c - 3, c + 3, 1, c + 3, CLAY)
    p.box(c - 1, 2, c - 1, c + 1, 2, c + 1, MUD)
    p.set(c, 3, c, 'minecraft:trial_spawner', TRIAL_STATE, trial_spawner('warlord'))
    for x, z in ((5, 5), (5, sz - 6), (sx - 6, 5), (sx - 6, sz - 6)):
        p.set(x, 1, z, 'minecraft:trial_spawner', TRIAL_STATE, trial_spawner('camp_guards'))
    for x, z in ((c, 4), (4, c), (sx - 5, c), (c, sz - 5)):
        p.set(x, sy - 3, z, LANTERN, HANGING)
    for x in (2, sx - 3):
        p.set(x, 1, 1, HAY, {'axis': 'y'})
    return p


# ---------------------------------------------------------------------------------- pools
def element(location, weight):
    return ('    { "weight": %d, "element": { "element_type": "minecraft:single_pool_element",'
            '\n        "location": "%s:camp/%s", "projection": "rigid", '
            '"processors": "%s:camp_weathering" } }' % (weight, NS, location, NS))


def write_pool(name, elements, fallback):
    if not os.path.isdir(POOL_JSON):
        os.makedirs(POOL_JSON)
    text = ('{\n  "fallback": "%s",\n  "elements": [\n%s\n  ]\n}\n'
            % (fallback, ',\n'.join(elements)))
    with open(os.path.join(POOL_JSON, name + '.json'), 'w', encoding='utf-8', newline='\n') as f:
        f.write(text)


# ---------------------------------------------------------------------------------- checks
def jigsaws(piece):
    return [(pos, dict(props or ()), piece.extra.get(pos, {}))
            for pos, (block, props) in piece.grid.items() if block == 'minecraft:jigsaw']


def surface_problems(pieces):
    """Put the ring together the way the game does and check that the eight boxes tile the
    forty-nine by forty-nine, with the towers in the outer corners. Only the north side is
    walked: the others are the same pieces rotated."""
    problems = []

    def place(child, jig_local, target):
        ox, oz = target[0] - jig_local[0], target[1] - jig_local[1]
        sx, _, sz = pieces[child].size
        return (ox, ox + sx - 1, oz, oz + sz - 1)

    panel_box = place('panel_end', (PANEL[0] // 2, PANEL[2] - 1), (HOUSE // 2, -1))
    px0, px1, pz0, pz1 = panel_box
    end = PANEL[2] - 3                      # where a panel's end jigsaws sit
    a = place('tower_a', (TOWER[0] - 1, TOWER[2] - 3), (px0 - 1, pz0 + end))
    b = place('tower_b', (0, TOWER[2] - 3), (px1 + 1, pz0 + end))
    want = {'panel_end': (0, HOUSE - 1, -(YARD + FENCE_DEPTH), -1),
            'tower_a': (-2 * CELL, -1, -(YARD + FENCE_DEPTH), -1),
            'tower_b': (HOUSE, HOUSE + 2 * CELL - 1, -(YARD + FENCE_DEPTH), -1)}
    for name, box in (('panel_end', panel_box), ('tower_a', a), ('tower_b', b)):
        if box != want[name]:
            problems.append('%s lands at %s, not %s; the ring would not close'
                            % (name, box, want[name]))
    side = HOUSE + 2 * (YARD + FENCE_DEPTH)
    if side != 49:
        problems.append('the camp is %d across, not 49' % side)

    for name, entry in (('panel', WALL), ('panel_end', WALL), ('gate', WALL),
                        ('tower_a', CORNER_A), ('tower_b', CORNER_B)):
        count = sum(1 for _, _, extra in jigsaws(pieces[name]) if extra.get('name') == entry)
        if count != 1:
            problems.append('%s carries %d jigsaws named %s; a piece placed by geometry must '
                            'carry exactly one (section 13)' % (name, count, entry))
    return problems


def ladder_problems(pieces):
    """Climb the column through whichever piece covers each course: a ladder the whole way
    down the middle, and nothing but solid block in the eight round it - except inside the
    landing piece itself, where the ring is the room you step out into."""
    at = {'longhouse': (0, 0, 0), 'shaft': (SHAFT_AT, -SHAFT_H, SHAFT_AT),
          'mine_hub': (SHAFT_AT, -SHAFT_H - CELL, SHAFT_AT)}
    cx, cz = HOLE
    cased = at['mine_hub'][1] + CELL - 1
    problems = []
    for y in range(at['mine_hub'][1] + 1, GROUND + 1):
        for dx in (-1, 0, 1):
            for dz in (-1, 0, 1):
                if (dx, dz) != (0, 0) and y < cased:
                    continue
                x, z = cx + dx, cz + dz
                for name, (ox, oy, oz) in at.items():
                    piece = pieces[name]
                    if 0 <= y - oy < piece.size[1]:
                        block = piece.grid[(x - ox, y - oy, z - oz)][0]
                        break
                else:
                    problems.append('nothing covers %s on the way down' % ((x, y, z),))
                    continue
                if (dx, dz) == (0, 0):
                    if block != 'minecraft:ladder':
                        problems.append('%s has %s at %s, where the climb needs a ladder'
                                        % (name, block.split(':')[-1], (x, y, z)))
                elif block in (AIR, 'minecraft:water', 'minecraft:ladder'):
                    problems.append('%s leaves %s at %s: the ring round the shaft has to '
                                    'be solid the whole way down (section 33)'
                                    % (name, block.split(':')[-1], (x, y, z)))
    return problems


HANGS = {'minecraft:lantern', 'minecraft:ladder', 'minecraft:iron_bars', 'minecraft:cobweb',
         'minecraft:acacia_fence', 'minecraft:torch', 'minecraft:acacia_trapdoor'}
AROUND = ((1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1))
BEHIND = {'north': (0, 0, 1), 'south': (0, 0, -1), 'east': (-1, 0, 0), 'west': (1, 0, 0)}


def fitting_problems(pieces):
    """Nothing hanging in mid-air, and every chest with a table under the lid."""
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
            if block == 'minecraft:lantern':
                other = 1 if props.get('hanging') == 'true' else -1
                if not solid((pos[0], pos[1] + other, pos[2])):
                    problems.append('%s: the lantern at %s hangs on nothing' % (name, pos))
            if block.endswith('chest'):
                if 'LootTable' not in (piece.extra.get(pos) or {}):
                    problems.append('%s: the chest at %s has no loot table' % (name, pos))
                if not solid((pos[0], pos[1] - 1, pos[2])):
                    problems.append('%s: the chest at %s stands on nothing' % (name, pos))
    return problems


def verify(pieces):
    problems = (surface_problems(pieces) + ladder_problems(pieces)
                + fitting_problems(pieces))
    for name, piece in pieces.items():
        if max(piece.size) > 48:
            problems.append('%s is %s: too big to rebuild by hand (section 16)'
                            % (name, piece.size))
        lords = sum(1 for _, _, extra in jigsaws(piece) if extra.get('name') == LORD)
        if lords > 1:
            problems.append('%s carries %d jigsaws named %s; the chain could be entered '
                            'through its own continuation' % (name, lords, LORD))
    for line in problems:
        print('  PROBLEM  ' + line)
    if problems:
        raise SystemExit('the camp does not hold together')
    print('  checked: the ring closes on 49x49 with the towers in the corners, every piece '
          'fits a structure block, the ladder is unbroken, nothing hangs in mid-air')


PASSABLE = {'air', 'ladder', 'lantern', 'torch', 'acacia_trapdoor', 'suspicious_gravel'}


def walk_problems():
    """Assemble the camp and walk it, from the middle of the hall out to the yard, the gate,
    a tower's platform and the mine. Reads what was written, not what was meant."""
    import gen_level_doc as doc

    pieces, pools = doc.load_family('camp'), doc.load_pools('camp')
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
    seen, queue = {(HOUSE // 2, g + 1, 3)}, [(HOUSE // 2, g + 1, 3)]
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

    far = HOUSE + YARD - 4
    want = {'the yard': (HOUSE // 2, g + 1, -4),
            'the gateway': (-YARD - 1, g + 1, HOUSE // 2),
            "a tower's platform": (-(YARD + FENCE_DEPTH) + 3, g + TOWER_TOP + 1,
                                   -(YARD + FENCE_DEPTH) + 3),
            'the yard across the camp': (far, g + 1, HOUSE // 2),
            'the mine': (RUNG[0], -SHAFT_H - CELL + 1, RUNG[1])}
    problems = []
    for label, spot in want.items():
        if not any((spot[0], spot[1] + dy, spot[2]) in seen for dy in (-1, 0, 1)):
            problems.append('%s cannot be walked to from the hall' % label)
    return problems


def main():
    if not os.path.isdir(DST):
        os.makedirs(DST)
    tower_a = tower()
    pieces = {
        'longhouse': longhouse(),
        'panel': panel(), 'panel_end': panel(ends=True), 'gate': panel(gate=True),
        'tower_a': tower_a, 'tower_b': mirrored(tower_a, CORNER_B, CORNER_B),
        'shaft': shaft(), 'mine_hub': mine_hub(),
        'drift': drift('drift'), 'drift_corner': drift('drift_corner'),
        'drift_cross': drift('drift_cross'), 'guard': drift('guard'),
        'store': drift('store'), 'cave_in': drift('cave_in'),
        'cage': drift('cage'), 'dig': drift('dig'),
        'cap': drift_cap(), 'warlord_hall': warlord_hall(),
    }
    for step in range(1, MIN_BOSS_STEPS + 1):
        pieces['approach_%d' % step] = approach(step)
    verify(pieces)
    for name, piece in sorted(pieces.items()):
        piece.write(os.path.join(DST, name + '.nbt'))
        print('  %-16s %s' % (name, list(piece.size)))

    write_pool('start', [element('longhouse', 1)], EMPTY)
    write_pool('panels', [element('panel', 1)], EMPTY)
    write_pool('panels_end', [element('panel_end', 1)], EMPTY)
    write_pool('gate', [element('gate', 1)], EMPTY)
    write_pool('corner_a', [element('tower_a', 1)], EMPTY)
    write_pool('corner_b', [element('tower_b', 1)], EMPTY)
    write_pool('down', [element('shaft', 1)], EMPTY)
    write_pool('mine_first', [element('mine_hub', 1)], EMPTY)
    write_pool('drifts', [element('drift', 10), element('drift_corner', 9),
                          element('drift_cross', 4), element('guard', 5),
                          element('store', 8), element('cave_in', 5),
                          element('cage', 3), element('dig', 5)],
               POOL['drift_caps'])
    write_pool('drift_caps', [element('cap', 1)], EMPTY)
    for step in range(1, MIN_BOSS_STEPS + 1):
        write_pool('lord_approach_%d' % step, [element('approach_%d' % step, 1)],
                   POOL['drift_caps'])
    write_pool('lord_approach', [element('warlord_hall', 1),
                                 element('approach_%d' % MIN_BOSS_STEPS, 1)],
               POOL['drift_caps'])
    print('  pools -> %s' % os.path.relpath(POOL_JSON, ROOT))
    problems = walk_problems()
    for line in problems:
        print('  PROBLEM  ' + line)
    if problems:
        raise SystemExit('the camp is built but you cannot walk it')
    print('  walked: the yard both sides, the gateway, a tower platform and the mine')


if __name__ == '__main__':
    main()
