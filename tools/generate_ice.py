# -*- coding: utf-8 -*-
"""The Ice Fortress: a curtain wall round a keep, and ice cellars under it.

    python tools/generate_ice.py        (or through make_pieces.py)

Writes data/sydungeon/structure/ice/*.nbt and the pools that join them.

WHY THE WALL IS EIGHT PIECES AND NOT ONE
A curtain wall wants to be a single 49x49 piece. It cannot be. When a jigsaw points inside
its own piece's box the child inherits that box as its free space, and so does everything the
child places after it (26.2 JigsawPlacement.tryPlacingChildren; CLAUDE.md section 10). The
pyramid uses that on purpose to fence its maze in. Here it would fence the cellars in too: a
keep hung inside the wall's box could never dig, because the shaft would be judged against the
wall's box and refused. So the wall is four panels and four corner towers whose boxes leave the
middle alone, the keep is the start piece, and the way down hangs off the start, where nothing
has fenced it.

HOW THE RING CLOSES
Everything on the surface is deterministic geometry (section 11): the keep calls a panel on
each face, and the north and south panels call the towers at their ends. Only those two do, so
each tower is called exactly once and its rotation is known - a tower has a thick corner and
two arms, and a piece rotated into the wrong quarter turn would put the tower inside the
courtyard. The two handednesses are one piece and its mirror, as in the wizard's tower.

STANDING ON A SLOPE
Snowy slopes, frozen peaks and groves are mountain biomes, so the ground is not flat. The keep
is the start piece and the game pins that by its floor, but panels and towers are children and
a child is placed by the height of its jigsaw alone, so they carry FOOT courses of foundation
below the courtyard (CLAUDE.md section 18, learnt from the swamp's stilts).
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import nbt  # noqa: E402
from generate_pieces import Piece  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DST = os.path.join(ROOT, 'src', 'main', 'resources', 'data', 'sydungeon', 'structure', 'ice')
HAND = os.path.join(ROOT, 'tools', 'handmade', 'ice')
POOL_JSON = os.path.join(ROOT, 'src', 'main', 'resources', 'data', 'sydungeon', 'worldgen',
                         'template_pool', 'ice')

NS = 'sydungeon'
WALL = NS + ':ice_wall'          # keep -> panel
CORNER_A = NS + ':ice_corner_a'  # north panel's left end -> tower, and the mirror of it
CORNER_B = NS + ':ice_corner_b'
DOWN = NS + ':ice_down'          # the one way from the keep to the cellars
CELLAR = NS + ':ice_door'        # the cellar maze
LORD = NS + ':ice_lord'          # the boss branch, its own name so it cannot run backwards
EMPTY = 'minecraft:empty'
PRIORITY = 10

CELL = 7
KEEP = 21                        # the keep is three cells across
FOOT = 7                         # foundation courses below the courtyard
HIGH = 18                        # box height above it
WARD = 7                         # the courtyard strip a panel carries in front of itself
PANEL = (KEEP, FOOT + HIGH, WARD + CELL)      # 21 x 25 x 14
TOWER = (2 * CELL, FOOT + HIGH, 2 * CELL)     # 14 x 25 x 14
SHAFT_H = 42                     # six cells of ladder. The fortress stands on mountain
                                 # flanks, which fall further than anything else this mod
                                 # builds on, and a cellar that surfaces on a slope reads as
                                 # a box of masonry stuck in the hill (2026-09-22)
BOSS = (21, 14, 21)
MIN_BOSS_STEPS = 3

WALL_TOP = 6                     # the walkway, measured from the courtyard
CRENEL = 8
TOWER_TOP = 15

# The way down, in the keep's coordinates: a three by three hole in the middle of the hall,
# the ladder in the middle of its east wall - not in a corner of it - and the jigsaws in that
# wall rather than in the hole, because a jigsaw becomes a block. SHAFT_AT is where the shaft
# hangs under the keep, and it is chosen so the hole lands in the middle of that piece too.
SHAFT_AT = CELL
HOLE = (KEEP // 2 - 1, KEEP // 2 + 1, KEEP // 2 - 1, KEEP // 2 + 1)      # x0 x1 z0 z1
RUNG = (KEEP // 2 + 1, KEEP // 2)
JIG = (KEEP // 2 + 2, KEEP // 2)

# Above ground the fortress is white, because the ground is: polished diorite is speckled
# enough that a wall of it does not read flat, and quartz bricks are the crisper white for
# frames, bands and crenellations. Below ground it turns to deepslate, so the cellars are
# their own place and the ice in them has something dark to sit against.
BRICK = 'minecraft:polished_diorite'
CHISEL = 'minecraft:quartz_bricks'
STONE = 'minecraft:cobbled_deepslate'
CELLAR_BRICK = 'minecraft:deepslate_tiles'
STAIR = 'minecraft:diorite_stairs'
SNOW = 'minecraft:snow_block'
PACKED = 'minecraft:packed_ice'
BLUE = 'minecraft:blue_ice'
POWDER = 'minecraft:powder_snow'
PLANK = 'minecraft:spruce_planks'
LOG = 'minecraft:spruce_log'
SLAB = 'minecraft:stone_brick_slab'
BARS = 'minecraft:iron_bars'
LANTERN = 'minecraft:lantern'
SOUL = 'minecraft:soul_lantern'
AIR = 'minecraft:air'

HANGING = {'hanging': 'true', 'waterlogged': 'false'}
STANDING = {'hanging': 'false', 'waterlogged': 'false'}
BOTTOM = {'type': 'bottom', 'waterlogged': 'false'}
GRID = {'north': 'true', 'south': 'true', 'east': 'true', 'west': 'true', 'waterlogged': 'false'}

UNDERGROUND = {'shaft', 'cellar_hub', 'cap', 'frost_hall', 'passage', 'passage_guard',
               'corner', 'cross', 'cross_guard', 'store', 'larder', 'powder', 'slick',
               'bear_den'} | {'approach_%d' % i for i in range(1, 4)}

POOL = {k: NS + ':ice/' + k for k in
        ['start', 'panels', 'panels_end', 'gate', 'corner_a', 'corner_b', 'down',
         'cellar_first', 'cellars', 'cellar_caps', 'lord_approach'] +
        ['lord_approach_%d' % i for i in range(1, MIN_BOSS_STEPS + 1)]}

TRIAL_STATE = {'trial_spawner_state': 'inactive', 'ominous': 'false'}
ANY_LIGHT = {'block_light_limit': {'min_inclusive': nbt.Int(0), 'max_inclusive': nbt.Int(15)}}


def trial_spawner(config):
    return {'id': 'minecraft:trial_spawner',
            'normal_config': NS + ':ice/' + config,
            'ominous_config': NS + ':ice/' + config,
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


def ladder(facing='west'):
    return ('minecraft:ladder', {'facing': facing, 'waterlogged': 'false'})


# ------------------------------------------------------------------------------ the keep
def sink(p, y0, y1, off=0, fill=BRICK):
    """The hole down and the ladder in it. `off` is what to subtract to go from the keep's
    coordinates to this piece's, so the four pieces that share the column cannot drift apart.

    The frame round the hole is only written where the piece had nothing, so a hand-built
    floor keeps its own blocks. Carve before writing the jigsaws: the other way round the
    hole erases them, which is the order trap CLAUDE.md section 11 records."""
    x0, x1, z0, z1 = (v - off for v in HOLE)
    for x in range(x0 - 1, x1 + 2):
        for z in range(z0 - 1, z1 + 2):
            for y in range(y0, y1 + 1):
                if p.grid.get((x, y, z), (AIR,))[0] == AIR:
                    p.set(x, y, z, fill)
    p.box(x0, y0, z0, x1, y1, z1, AIR)
    for y in range(y0, y1 + 1):
        p.set(RUNG[0] - off, y, RUNG[1] - off, *ladder())


def keep():
    """The start: a three storey hall in the middle of the courtyard. Its floor is pinned one
    block under the surface, its four faces call the curtain wall, and the hole in its floor
    is the only way to the cellars."""
    n = KEEP
    p = Piece(n, n, n, BRICK)
    mid = n // 2
    for floor, top in ((1, 6), (8, 13), (15, 19)):                 # three hollow storeys
        p.box(1, floor, 1, n - 2, top, n - 2, AIR)
    p.box(0, 0, 0, n - 1, 0, n - 1, BRICK)                         # ground floor
    for y in (7, 14):
        p.box(1, y, 1, n - 2, y, n - 2, PLANK)
    for x, z in ((0, 0), (0, n - 1), (n - 1, 0), (n - 1, n - 1)):  # corner columns
        for y in range(1, n - 1):
            p.set(x, y, z, LOG, {'axis': 'y'})
    p.box(0, n - 1, 0, n - 1, n - 1, n - 1, AIR)                   # the roof is open sky
    for i in range(0, n, 2):                                       # crenellated parapet
        p.set(i, n - 1, 0, BRICK)
        p.set(i, n - 1, n - 1, BRICK)
        p.set(0, n - 1, i, BRICK)
        p.set(n - 1, n - 1, i, BRICK)
    for side in range(n):                                          # the parapet's floor
        p.set(side, n - 2, 0, BRICK)
        p.set(side, n - 2, n - 1, BRICK)
        p.set(0, n - 2, side, BRICK)
        p.set(n - 1, n - 2, side, BRICK)

    for y in (3, 10):                                              # windows of blue ice
        for a in (5, mid, n - 6):
            for x, z in ((0, a), (n - 1, a), (a, 0), (a, n - 1)):
                p.set(x, y, z, BLUE)
                p.set(x, y + 1, z, BLUE)

    for side in ('west', 'east', 'north', 'south'):                # the four ways out
        if side == 'west':
            p.box(0, 1, mid - 1, 0, 4, mid + 1, AIR)
            p.jigsaw(0, 0, mid, 'west_up', POOL['gate'], BRICK, priority=PRIORITY,
                     name=WALL, target=WALL)
        elif side == 'east':
            p.box(n - 1, 1, mid - 1, n - 1, 4, mid + 1, AIR)
            p.jigsaw(n - 1, 0, mid, 'east_up', POOL['panels'], BRICK, priority=PRIORITY,
                     name=WALL, target=WALL)
        elif side == 'north':
            p.box(mid - 1, 1, 0, mid + 1, 4, 0, AIR)
            p.jigsaw(mid, 0, 0, 'north_up', POOL['panels_end'], BRICK, priority=PRIORITY,
                     name=WALL, target=WALL)
        else:
            p.box(mid - 1, 1, n - 1, mid + 1, 4, n - 1, AIR)
            p.jigsaw(mid, 0, n - 1, 'south_up', POOL['panels_end'], BRICK, priority=PRIORITY,
                     name=WALL, target=WALL)

    # stairs between the storeys, in opposite corners so the climb crosses the hall
    for y0, x, z in ((1, n - 2, 1), (8, 1, n - 2)):
        for y in range(y0, y0 + 7):
            p.set(x, y, z, *ladder('west' if x > mid else 'east'))
    p.box(n - 4, 7, 1, n - 2, 7, 3, AIR)
    p.box(1, 14, n - 4, 3, 14, n - 2, AIR)

    p.set(5, 2, 5, 'minecraft:campfire',                           # clear of the hole
          {'facing': 'north', 'lit': 'true', 'signal_fire': 'false', 'waterlogged': 'false'})
    for x, z in ((4, 4), (n - 5, 4), (4, n - 5), (n - 5, n - 5)):
        p.set(x, 6, z, LANTERN, HANGING)
        p.set(x, 13, z, LANTERN, HANGING)

    floor_and_hole(p)
    return p


def floor_and_hole(p):
    """The ground floor is solid except for the one way down.

    Run over the hand-built keep as well as the code's, which is how the first pass's hole -
    cut in a corner, before it moved to the middle of the hall - gets filled in without anyone
    having to remember it."""
    x0, x1, z0, z1 = HOLE
    for x in range(KEEP):
        for z in range(KEEP):
            if x0 <= x <= x1 and z0 <= z <= z1:
                continue
            if p.grid.get((x, 0, z), (AIR,))[0] in (AIR, 'minecraft:ladder'):
                p.set(x, 0, z, BRICK)
    sink(p, 0, 0)
    p.jigsaw(JIG[0], 0, JIG[1], 'down_east', POOL['down'], BRICK, joint='aligned',
             priority=PRIORITY, name=DOWN, target=DOWN)


# ------------------------------------------------------------------------- the curtain wall
def curtain(p, x0, x1, z0, z1, walk_from='south'):
    """One run of wall inside a piece: foundation, a solid body, a walkway on top of it and a
    crenellated parapet on the outer face. `walk_from` is the side the courtyard is on."""
    g = FOOT
    p.box(x0, 0, z0, x1, g - 1, z1, STONE)                 # foundation, below the courtyard
    p.box(x0, g, z0, x1, g + WALL_TOP - 1, z1, BRICK)      # the body
    p.box(x0, g + WALL_TOP, z0, x1, g + HIGH - 1, z1, AIR)
    p.box(x0, g + WALL_TOP, z0, x1, g + WALL_TOP, z1, BRICK)   # the walkway's floor
    outer = {'south': (z0, z0), 'north': (z1, z1),
             'east': (x0, x0), 'west': (x1, x1)}[walk_from]
    if walk_from in ('south', 'north'):
        p.box(x0, g + WALL_TOP + 1, outer[0], x1, g + CREN_TOP, outer[1], BRICK)
        for i in range(x0, x1 + 1, 2):
            p.set(i, g + CRENEL, outer[0], BRICK)
    else:
        p.box(outer[0], g + WALL_TOP + 1, z0, outer[1], g + CREN_TOP, z1, BRICK)
        for i in range(z0, z1 + 1, 2):
            p.set(outer[0], g + CRENEL, i, BRICK)


CREN_TOP = CRENEL - 1


def ward(p, x0, x1, z0, z1):
    """The courtyard strip: foundation under it, paving at the keep's level, and air carved
    out above so the fortress has a flat ward however the mountain lies."""
    g = FOOT
    p.box(x0, 0, z0, x1, g - 1, z1, STONE)
    p.box(x0, g, z0, x1, g, z1, BRICK)
    p.box(x0, g + 1, z0, x1, g + HIGH - 1, z1, AIR)
    for x in range(x0, x1 + 1):                            # snow drifts against the wall
        for z in range(z0, z1 + 1):
            if (x * 7 + z * 3) % 5 == 0:
                p.set(x, g, z, SNOW)


def steps(p, x0, z):
    """A flight against the inside of the wall, from the courtyard up to the walkway. Without
    it the ring is a picture: the towers are only enterable from the top of the wall."""
    g = FOOT
    for i in range(WALL_TOP):
        x = x0 + i
        p.set(x, g + 1 + i, z, STAIR,
              {'facing': 'east', 'half': 'bottom', 'shape': 'straight',
               'waterlogged': 'false'})
        for y in range(g + 1, g + 1 + i):                  # the flight is solid underneath
            p.set(x, y, z, BRICK)
        for y in range(g + 2 + i, g + WALL_TOP + 4):       # and clear overhead
            p.set(x, y, z, AIR)


def panel(ends=False, gate=False):
    """One side of the curtain wall plus the courtyard in front of it. The entry jigsaw is on
    the inner face; only the panel with `ends` calls the towers, so each tower is called once
    and its rotation is known (section 13)."""
    sx, sy, sz = PANEL
    g, mid = FOOT, sx // 2
    p = Piece(sx, sy, sz, AIR)
    curtain(p, 0, sx - 1, 0, CELL - 1, walk_from='south')
    ward(p, 0, sx - 1, CELL, sz - 1)

    if gate:                                               # an arch through the wall
        p.box(mid - 1, g + 1, 0, mid + 1, g + 4, CELL - 1, AIR)
        p.box(mid - 1, g + 5, 0, mid + 1, g + 5, CELL - 1, BRICK)
        for z in range(CELL):
            p.set(mid - 2, g + 1, z, CHISEL)
            p.set(mid + 2, g + 1, z, CHISEL)
        for x in (mid - 2, mid + 2):                       # gate towers flanking the arch
            p.box(x - 1, g + WALL_TOP + 1, 0, x + 1, g + CRENEL + 2, CELL - 1, BRICK)
            p.box(x - 1, g + WALL_TOP + 1, 1, x + 1, g + CRENEL + 1, CELL - 2, AIR)
        for z in (1, CELL - 2):
            p.set(mid, g + 5, z, LANTERN, HANGING)
        p.box(mid - 1, g, CELL, mid + 1, g, sz - 1, PACKED)   # the road in
    if ends:
        p.jigsaw(0, g, 3, 'west_up', POOL['corner_a'], BRICK, priority=PRIORITY,
                 name=CORNER_A, target=CORNER_A)
        p.jigsaw(sx - 1, g, 3, 'east_up', POOL['corner_b'], BRICK, priority=PRIORITY,
                 name=CORNER_B, target=CORNER_B)
    steps(p, sx - 8, CELL)                                 # up onto the walkway
    for x in (4, sx - 5):                                  # braziers on the walkway
        p.set(x, g + WALL_TOP + 1, CELL - 2, LANTERN, STANDING)
    # last, so that nothing written above can rub the entry jigsaw out - the gate's road did
    p.jigsaw(mid, g, sz - 1, 'south_up', EMPTY, BRICK, name=WALL, target=WALL)
    return p


def tower():
    """A corner: a thick tower in the outer quarter, two arms of wall, and the corner of the
    courtyard in the inner quarter. Drawn as the north-west one; the north-east is its
    mirror."""
    sx, sy, sz = TOWER
    g = FOOT
    p = Piece(sx, sy, sz, AIR)
    curtain(p, CELL, sx - 1, 0, CELL - 1, walk_from='south')        # the arm running east
    curtain(p, 0, CELL - 1, CELL, sz - 1, walk_from='east')         # the arm running south
    ward(p, CELL, sx - 1, CELL, sz - 1)

    p.box(0, 0, 0, CELL - 1, g - 1, CELL - 1, STONE)                # the tower itself
    p.box(0, g, 0, CELL - 1, g + TOWER_TOP, CELL - 1, BRICK)
    p.box(1, g + 1, 1, CELL - 2, g + TOWER_TOP - 1, CELL - 2, AIR)
    p.box(0, g + TOWER_TOP, 0, CELL - 1, g + TOWER_TOP, CELL - 1, AIR)
    for i in range(0, CELL, 2):                                     # its crown
        p.set(i, g + TOWER_TOP, 0, BRICK)
        p.set(i, g + TOWER_TOP, CELL - 1, BRICK)
        p.set(0, g + TOWER_TOP, i, BRICK)
        p.set(CELL - 1, g + TOWER_TOP, i, BRICK)
    for y in (g + 3, g + 9):                                        # arrow slits
        for i in (2, 4):
            p.set(i, y, 0, BARS, GRID)
            p.set(0, y, i, BARS, GRID)
    # doors at walkway height onto both arms, so the patrol can walk the whole ring. At
    # ground level there is nothing to open onto: an arm is seven solid blocks of wall.
    p.box(CELL - 1, g + WALL_TOP + 1, 2, CELL - 1, g + WALL_TOP + 3, 4, AIR)
    p.box(2, g + WALL_TOP + 1, CELL - 1, 4, g + WALL_TOP + 3, CELL - 1, AIR)
    # floors, or the patrol walks in at walkway height and falls to the bottom. The ladder is
    # written after them and passes through both: a rung is not something you stand on.
    p.box(1, g + WALL_TOP, 1, CELL - 2, g + WALL_TOP, CELL - 2, BRICK)
    p.box(1, g + TOWER_TOP - 1, 1, CELL - 2, g + TOWER_TOP - 1, CELL - 2, BRICK)
    for y in range(g + 1, g + TOWER_TOP):                           # the climb inside
        p.set(1, y, 1, *ladder('east'))
    p.set(3, g + 5, 3, LANTERN, HANGING)
    p.set(4, g + 1, 4, 'minecraft:spawner', None, mob_spawner('minecraft:stray', 1))

    p.jigsaw(sx - 1, g, 3, 'east_up', EMPTY, BRICK, name=CORNER_A, target=CORNER_A)
    return p


MIRROR_FACE = {'east': 'west', 'west': 'east', 'north': 'north', 'south': 'south'}


def mirrored(src, name, target):
    """The other handedness. Reflecting x turns the north-west corner into the north-east one;
    vanilla will rotate but it will not mirror, so this is the one shape we make twice."""
    sx, sy, sz = src.size
    out = Piece(sx, sy, sz, AIR)
    for (x, y, z), (block, props) in src.grid.items():
        flipped = dict(props) if props else None
        if flipped:
            if flipped.get('facing') in MIRROR_FACE:
                flipped['facing'] = MIRROR_FACE[flipped['facing']]
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


# ---------------------------------------------------------------------------- the cellars
def shaft():
    """From the keep's floor down into the rock. It shares the keep's x and z, so the ladder
    is one unbroken column - verify() climbs it."""
    p = Piece(CELL, SHAFT_H, CELL, CELLAR_BRICK)
    shaft_wiring(p, SHAFT_H - 1)
    return p


def shaft_wiring(p, top):
    # solid except for the climb. A hand-built shaft that still carries the first pass's hole
    # - cut in a corner, before it moved to the middle - gets it filled in here.
    for x in range(CELL):
        for y in range(top + 1):
            for z in range(CELL):
                if p.grid.get((x, y, z), (AIR,))[0] in (AIR, 'minecraft:ladder'):
                    p.set(x, y, z, BRICK)
    sink(p, 0, top, off=SHAFT_AT)
    p.jigsaw(JIG[0] - SHAFT_AT, top, JIG[1] - SHAFT_AT, 'up_east', EMPTY, BRICK,
             joint='aligned', name=DOWN, target=DOWN)
    p.jigsaw(JIG[0] - SHAFT_AT, 0, JIG[1] - SHAFT_AT, 'down_east', POOL['cellar_first'],
             BRICK, joint='aligned', priority=PRIORITY, name=CELLAR, target=CELLAR)


def room(doors, fill=CELLAR_BRICK):
    p = Piece(CELL, CELL, CELL, fill)
    p.box(1, 1, 1, CELL - 2, CELL - 2, CELL - 2, AIR)
    p.box(0, 0, 0, CELL - 1, 0, CELL - 1, PACKED)
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
    return p


DOOR_AT = {'west': (0, 0, 3, 'west_up'), 'east': (CELL - 1, 0, 3, 'east_up'),
           'north': (3, 0, 0, 'north_up'), 'south': (3, 0, CELL - 1, 'south_up')}


def door(p, side, pool, name=CELLAR, target=CELLAR, priority=0):
    x, y, z, orientation = DOOR_AT[side]
    p.jigsaw(x, y, z, orientation, pool, BRICK, priority=priority, name=name, target=target)


def cellar_hub():
    """Where the ladder lands. Three ways into the cellars and one, on its own connector and
    placed first, to the frost lord."""
    p = room(['west', 'north', 'south'])          # no east door: the ladder's post is there
    hub_wiring(p)
    door(p, 'west', POOL['cellars'])
    door(p, 'north', POOL['cellars'])
    door(p, 'south', POOL['lord_approach_1'], name=CELLAR, target=LORD, priority=PRIORITY)
    p.set(1, 4, 1, LANTERN, HANGING)
    return p


def hub_wiring(p):
    """The hole in the ceiling, in the middle of the cell, and the ladder that comes through it.

    The hole is in the middle now, which means the ladder is too, and a ladder needs a wall.
    So the post it hangs on runs floor to ceiling, and the jigsaw sits at the top of that post.
    The room's east door is gone: it would have opened straight into the post.

    The ceiling is closed first, so a hand-built hub that still carries the first pass's hole
    does not end up with two. Then the hole, then the jigsaw - the other way round the hole
    erases it (section 11)."""
    x0, x1, z0, z1 = (v - SHAFT_AT for v in HOLE)
    jx, jz = JIG[0] - SHAFT_AT, JIG[1] - SHAFT_AT
    for x in range(CELL):
        for z in range(CELL):
            if p.grid.get((x, CELL - 1, z), (AIR,))[0] in (AIR, 'minecraft:ladder'):
                p.set(x, CELL - 1, z, BRICK)
    for y in range(1, CELL):                      # the post
        p.set(jx, y, jz, BRICK)
    p.box(x0, CELL - 1, z0, x1, CELL - 1, z1, AIR)
    p.jigsaw(jx, CELL - 1, jz, 'up_east', EMPTY, BRICK, joint='aligned',
             name=CELLAR, target=CELLAR)
    for y in range(1, CELL):
        p.set(RUNG[0] - SHAFT_AT, y, RUNG[1] - SHAFT_AT, *ladder())


def cellar(kind):
    doors = {'passage': ['west', 'east'], 'corner': ['west', 'south'],
             'cross': ['west', 'east', 'north', 'south'],
             'cross_guard': ['west', 'east', 'north', 'south'],
             'passage_guard': ['west', 'east'],
             'store': ['west'], 'powder': ['west', 'east'], 'slick': ['west', 'east'],
             'bear_den': ['west'], 'larder': ['west']}[kind]
    p = room(doors)
    for side in doors:
        door(p, side, POOL['cellars'])
    mid = CELL // 2
    if kind == 'powder':
        # no trigger: it is simply a hole full of snow, and it is there whether a mob walks
        # in first or not (section 12)
        p.box(1, 0, 1, CELL - 2, 0, CELL - 2, POWDER)
        p.box(mid - 1, 0, mid - 1, mid + 1, 0, mid + 1, POWDER)
        p.set(1, 0, 1, PACKED)
        p.set(CELL - 2, 0, CELL - 2, PACKED)
    elif kind == 'slick':
        p.box(1, 0, 1, CELL - 2, 0, CELL - 2, BLUE)
        p.set(mid, 4, mid, LANTERN, HANGING)
    elif kind == 'bear_den':
        p.box(1, 1, 1, CELL - 2, 1, CELL - 2, SNOW)
        p.set(mid, 1, mid, 'minecraft:spawner', None, mob_spawner('minecraft:polar_bear', 1))
        p.set(CELL - 2, 2, 1, *chest('ice_store', 'west'))
    elif kind == 'store':
        p.set(CELL - 2, 1, mid, *chest('ice_store', 'west'))
        p.box(1, 1, 1, 1, 2, CELL - 2, PACKED)
        p.set(mid, 4, mid, LANTERN, HANGING)
    elif kind == 'larder':
        p.box(1, 1, CELL - 2, CELL - 2, 3, CELL - 2, PACKED)
        p.set(mid, 1, 1, *chest('ice_store', 'north'))
        p.set(1, 1, 1, 'minecraft:barrel', {'facing': 'up', 'open': 'false'})
        p.set(mid, 4, mid, SOUL, HANGING)
    elif kind.endswith('_guard'):
        entity = 'minecraft:stray' if kind == 'passage_guard' else 'minecraft:skeleton'
        p.set(mid, 1, mid, 'minecraft:spawner', None, mob_spawner(entity, 1))
    return p


def cellar_cap():
    p = Piece(1, CELL, CELL, CELLAR_BRICK)
    p.jigsaw(0, 0, 3, 'west_up', POOL['cellar_caps'], CELLAR_BRICK, name=CELLAR, target=CELLAR)
    return p


def approach(step):
    """One link of the chain to the frost lord. The way in is the only jigsaw named `lord`, so
    the chain cannot be entered through its own continuation (section 13)."""
    p = room(['west', 'east', 'north'])
    p.jigsaw(0, 0, 3, 'west_up', POOL['cellars'], BRICK, name=LORD, target=CELLAR)
    nxt = ('lord_approach_%d' % (step + 1)) if step < MIN_BOSS_STEPS else 'lord_approach'
    door(p, 'east', POOL[nxt], name=CELLAR, target=LORD, priority=PRIORITY)
    door(p, 'north', POOL['cellars'])
    p.box(1, 0, 1, CELL - 2, 0, CELL - 2, BLUE)
    return p


def frost_hall():
    """His hall: a frozen cistern with the lord on an island of blue ice, four guards in the
    quarters, and no other way out."""
    sx, sy, sz = BOSS
    p = Piece(sx, sy, sz, CELLAR_BRICK)
    p.box(1, 1, 1, sx - 2, sy - 2, sz - 2, AIR)
    p.box(0, 0, 0, sx - 1, 0, sz - 1, PACKED)
    p.jigsaw(0, 0, sz // 2, 'west_up', EMPTY, BRICK, name=LORD, target=CELLAR)
    p.box(0, 1, sz // 2 - 1, 0, 4, sz // 2 + 1, AIR)

    for x0, z0 in ((3, 3), (3, sz - 5), (sx - 5, 3), (sx - 5, sz - 5)):     # ice pillars
        for y in range(1, sy - 1):
            p.box(x0, y, z0, x0 + 1, y, z0 + 1, PACKED)
    c = sx // 2
    p.box(c - 4, 0, c - 4, c + 4, 0, c + 4, BLUE)                           # the frozen floor
    p.box(c - 2, 1, c - 2, c + 2, 1, c + 2, PACKED)                         # his dais
    p.box(c - 1, 2, c - 1, c + 1, 2, c + 1, CHISEL)
    p.set(c, 3, c, 'minecraft:trial_spawner', TRIAL_STATE, trial_spawner('frost_lord'))
    for x, z in ((5, 5), (5, sz - 6), (sx - 6, 5), (sx - 6, sz - 6)):
        p.set(x, 1, z, 'minecraft:trial_spawner', TRIAL_STATE, trial_spawner('ice_guards'))
    for x, z in ((c, 4), (4, c), (sx - 5, c), (c, sz - 5)):
        p.set(x, sy - 3, z, SOUL, HANGING)
    for i in range(2, sx - 2, 4):                                           # a band of ice
        p.set(i, sy - 2, 1, BLUE)
        p.set(i, sy - 2, sz - 2, BLUE)
    return p


# ---------------------------------------------------------------------------------- pools
def element(location, weight):
    return ('    { "weight": %d, "element": { "element_type": "minecraft:single_pool_element",'
            '\n        "location": "%s:ice/%s", "projection": "rigid", '
            '"processors": "%s:ice_weathering" } }' % (weight, NS, location, NS))


def write_pool(name, elements, fallback):
    if not os.path.isdir(POOL_JSON):
        os.makedirs(POOL_JSON)
    text = ('{\n  "fallback": "%s",\n  "elements": [\n%s\n  ]\n}\n'
            % (fallback, ',\n'.join(elements)))
    with open(os.path.join(POOL_JSON, name + '.json'), 'w', encoding='utf-8', newline='\n') as f:
        f.write(text)


# ---------------------------------------------------------------------------------- checks
def jigsaws(piece):
    out = []
    for pos, (block, props) in piece.grid.items():
        if block == 'minecraft:jigsaw':
            out.append((pos, dict(props or ()), piece.extra.get(pos, {})))
    return out


def surface_problems(pieces):
    """Put the ring together the way the game does - a child's box is its parent's jigsaw
    target minus the child's own jigsaw position - and check that the eight boxes tile the
    forty-nine by forty-nine exactly, with the towers in the outer corners.

    Only the north side is walked. The other three are the same pieces rotated, and vanilla
    turns a child until its jigsaw faces the parent's; if north lines up they all do."""
    problems = []
    boxes = {'keep': (0, KEEP - 1, 0, KEEP - 1)}

    def place(child, jig_local, target):
        ox, oz = target[0] - jig_local[0], target[1] - jig_local[1]
        sx, _, sz = pieces[child].size
        return (ox, ox + sx - 1, oz, oz + sz - 1)

    boxes['panel_end'] = place('panel_end', (PANEL[0] // 2, PANEL[2] - 1), (KEEP // 2, -1))
    px0, px1, pz0, pz1 = boxes['panel_end']
    boxes['tower_a'] = place('tower_a', (TOWER[0] - 1, 3), (px0 - 1, pz0 + 3))
    boxes['tower_b'] = place('tower_b', (0, 3), (px1 + 1, pz0 + 3))

    want = {'panel_end': (0, KEEP - 1, -(WARD + CELL), -1),
            'tower_a': (-2 * CELL, -1, -(WARD + CELL), -1),
            'tower_b': (KEEP, KEEP + 2 * CELL - 1, -(WARD + CELL), -1)}
    for name, box in want.items():
        if boxes[name] != box:
            problems.append('%s lands at %s, not %s; the ring would not close'
                            % (name, boxes[name], box))
    side = KEEP + 2 * (WARD + CELL)
    if side != 49:
        problems.append('the fortress is %d across, not 49' % side)

    for name, entry in (('panel', WALL), ('panel_end', WALL), ('gate', WALL),
                        ('tower_a', CORNER_A), ('tower_b', CORNER_B)):
        count = sum(1 for _, _, extra in jigsaws(pieces[name]) if extra.get('name') == entry)
        if count != 1:
            problems.append('%s carries %d jigsaws named %s; a piece placed by geometry must '
                            'carry exactly one, or vanilla may enter it through the wrong '
                            'face (section 13)' % (name, count, entry))
    return problems


def ladder_problems(pieces):
    """Climb from the cellar floor to the keep's, through all three pieces that share the
    column. A jigsaw is a block, so one standing in the hole is a rung missing."""
    at = {'keep': (0, 0, 0), 'shaft': (SHAFT_AT, -SHAFT_H, SHAFT_AT),
          'cellar_hub': (SHAFT_AT, -SHAFT_H - CELL, SHAFT_AT)}
    x0, x1, z0, z1 = HOLE
    problems = []
    for y in range(at['cellar_hub'][1] + 1, 1):
        for x in range(x0, x1 + 1):
            for z in range(z0, z1 + 1):
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


# ------------------------------------------------------------------- dressing the rooms
# Furniture is placed by search, not by coordinate: a spot has to be empty, have something
# solid under it and headroom above. That way a room rebuilt by hand keeps whatever was put
# in it and the dressing goes wherever it still fits - and nothing ends up in mid-air, which
# is the one thing hand-editing and code-editing both keep doing (section 21).
def free(p, region, head=2):
    x0, x1, y, z0, z1 = region
    for x in range(x0, x1 + 1):
        for z in range(z0, z1 + 1):
            below = p.grid.get((x, y - 1, z), (AIR,))[0]
            if below == AIR or below in HANGS:
                continue
            if any(p.grid.get((x, y + h, z), (AIR,))[0] != AIR for h in range(head)):
                continue
            yield (x, y, z)


def put(p, region, block, props=None, extra=None):
    for at in free(p, region):
        p.set(at[0], at[1], at[2], block, props, extra)
        return at
    return None


def put_bed(p, region):
    """Two blocks, and they have to be next to each other."""
    spots = set(free(p, region))
    for x, y, z in sorted(spots):
        if (x, y, z + 1) in spots:
            p.set(x, y, z, 'minecraft:white_bed', {'facing': 'south', 'part': 'foot'})
            p.set(x, y, z + 1, 'minecraft:white_bed', {'facing': 'south', 'part': 'head'})
            return (x, y, z)
    return None


CORNERS = ((1, 6, 1, 6), (14, 19, 1, 6), (1, 6, 14, 19), (14, 19, 14, 19))
FACE = {'facing': 'south'}
LIT = {'facing': 'south', 'lit': 'true', 'signal_fire': 'false', 'waterlogged': 'false'}


def furnish_keep(p):
    """Three floors of a castle: the hall, the barracks and the lord's room.

    The hall's corners are a hearth, an armoury, a store and a writing nook; each is a corner
    of its own so nothing crowds the doors, which are in the middle of every wall."""
    nw, ne, sw, se = ((x0, x1, 1, z0, z1) for x0, x1, z0, z1 in CORNERS)
    put(p, nw, 'minecraft:campfire', LIT)                       # the hearth
    put(p, nw, 'minecraft:cauldron', {'level': '0'})
    put(p, nw, 'minecraft:barrel', {'facing': 'up', 'open': 'false'})
    put(p, nw, 'minecraft:white_banner', {'rotation': '8'})
    put(p, ne, 'minecraft:anvil', FACE)                          # the armoury
    put(p, ne, 'minecraft:grindstone', {'face': 'floor', 'facing': 'south'})
    put(p, ne, 'minecraft:smithing_table')
    put(p, ne, 'minecraft:fletching_table')
    put(p, ne, 'minecraft:white_banner', {'rotation': '0'})
    put(p, sw, *chest('ice_store', 'north')[:2], extra=chest('ice_store', 'north')[2])
    put(p, sw, 'minecraft:barrel', {'facing': 'up', 'open': 'false'})
    put(p, sw, 'minecraft:loom', FACE)                           # the stores
    put(p, sw, 'minecraft:cartography_table')
    put(p, se, 'minecraft:bookshelf')                            # the writing nook
    put(p, se, 'minecraft:bookshelf')
    put(p, se, 'minecraft:chiseled_bookshelf', dict(FACE, **{
        'slot_0_occupied': 'true', 'slot_1_occupied': 'true', 'slot_2_occupied': 'false',
        'slot_3_occupied': 'true', 'slot_4_occupied': 'false', 'slot_5_occupied': 'true'}))
    put(p, se, 'minecraft:lectern', dict(FACE, **{'has_book': 'false', 'powered': 'false'}))
    put(p, se, *chest('ice_store', 'west')[:2], extra=chest('ice_store', 'west')[2])

    barracks = [(x0, x1, 8, z0, z1) for x0, x1, z0, z1 in CORNERS]
    for region in barracks[:2]:
        put_bed(p, region)
    put(p, barracks[0], 'minecraft:white_candle', {'candles': '2', 'lit': 'false',
                                                   'waterlogged': 'false'})
    put(p, barracks[1], 'minecraft:barrel', {'facing': 'up', 'open': 'false'})
    put(p, barracks[2], *chest('ice_store', 'north')[:2],
        extra=chest('ice_store', 'north')[2])
    put(p, barracks[2], 'minecraft:bookshelf')
    put(p, barracks[3], 'minecraft:spawner', None, mob_spawner('minecraft:stray', 1))
    put(p, barracks[3], 'minecraft:decorated_pot', {'facing': 'south', 'cracked': 'false',
                                                    'waterlogged': 'false'})

    lord = [(x0, x1, 15, z0, z1) for x0, x1, z0, z1 in CORNERS]
    put(p, lord[0], *chest('ice_keep', 'south')[:2], extra=chest('ice_keep', 'south')[2])
    put(p, lord[1], 'minecraft:lectern', dict(FACE, **{'has_book': 'false',
                                                       'powered': 'false'}))
    put(p, lord[2], 'minecraft:cauldron', {'level': '0'})
    put(p, lord[3], 'minecraft:white_candle', {'candles': '3', 'lit': 'false',
                                               'waterlogged': 'false'})
    put(p, lord[3], 'minecraft:white_banner', {'rotation': '8'})


def furnish(pieces):
    """The garrison and its stores, in the wall, the courtyard and the keep."""
    furnish_keep(pieces['keep'])
    g = FOOT
    for name in ('panel', 'panel_end', 'gate'):
        p = pieces[name]
        ward = (1, 5, g + 1, CELL + 1, PANEL[2] - 2)             # the courtyard side
        far = (PANEL[0] - 6, PANEL[0] - 2, g + 1, CELL + 1, PANEL[2] - 2)
        put(p, ward, *chest('ice_store', 'east')[:2], extra=chest('ice_store', 'east')[2])
        put(p, ward, 'minecraft:barrel', {'facing': 'up', 'open': 'false'})
        if name != 'gate':                                       # not in the gateway itself
            put(p, far, 'minecraft:spawner', None, mob_spawner('minecraft:stray', 1))
        put(p, far, 'minecraft:campfire', LIT)
    for name in ('tower_a', 'tower_b'):
        p = pieces[name]
        watch = (1, TOWER[0] - 2, g + WALL_TOP + 1, 1, TOWER[2] - 2)
        put(p, watch, *chest('ice_store', 'south')[:2], extra=chest('ice_store', 'south')[2])
        put(p, watch, 'minecraft:barrel', {'facing': 'up', 'open': 'false'})


HANGS = {'minecraft:lantern', 'minecraft:soul_lantern', 'minecraft:iron_chain',
         'minecraft:ladder', 'minecraft:torch', 'minecraft:iron_bars', 'minecraft:vine'}
AROUND = ((1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1))
BEHIND = {'north': (0, 0, 1), 'south': (0, 0, -1), 'east': (-1, 0, 0), 'west': (1, 0, 0)}


def fitting_problems(pieces):
    """Blocks with nothing holding them up, and chests with nothing in them.

    Worth running on every piece and not only the ones this file builds: a hand-built room
    comes back with whatever was left mid-air in it, and a chest opened in the workshop comes
    back holding its roll instead of its table."""
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
    problems = surface_problems(pieces) + ladder_problems(pieces) + fitting_problems(pieces)
    for name, piece in pieces.items():
        if max(piece.size) > 48:
            problems.append('%s is %s; a structure block saves 48 to a side, so this one '
                            'could never be rebuilt by hand (section 16)' % (name, piece.size))
        lords = sum(1 for _, _, extra in jigsaws(piece) if extra.get('name') == LORD)
        if lords > 1:
            problems.append('%s carries %d jigsaws named %s; the chain could be entered '
                            'through its own continuation' % (name, lords, LORD))
    for line in problems:
        print('  PROBLEM  ' + line)
    if problems:
        raise SystemExit('the fortress does not hold together')
    print('  checked: the ring closes on 49x49 with the towers in the corners, every piece '
          'fits a structure block, the ladder is unbroken from the keep to the cellar, '
          'nothing hangs in mid-air and every chest has a table')


# a jigsaw is a block once placed, and a stair is something you stand on, so neither is air
PASSABLE = {'air', 'ladder', 'lantern', 'soul_lantern', 'powder_snow', 'torch', 'snow'}


def walk_problems():
    """Assemble the fortress the way the game does and walk it.

    Reads what was just written, so it costs a second and it checks the files rather than the
    intent. It has earned its keep twice: the towers had no floor at walkway height, so the
    patrol walked in at the top of the wall and fell fifteen blocks, and before the stair went
    in there was no way up from the courtyard at all - a ring you could only look at."""
    import gen_level_doc as doc

    pieces, pools = doc.load_family('ice'), doc.load_pools('ice')
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

    seen, queue = {(KEEP // 2, 1, KEEP // 2)}, [(KEEP // 2, 1, KEEP // 2)]
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

    far = KEEP + WARD + 3                       # a step inside the far wall's walkway
    want = {'the courtyard': (-WARD + 3, 1, KEEP // 2),
            'the gate arch': (-CELL - 4, 1, KEEP // 2),
            'the walkway, north': (KEEP // 2, WALL_TOP + 1, -CELL - 4),
            'the walkway, east': (far, WALL_TOP + 1, KEEP // 2),
            'a tower top': (-CELL - 4, TOWER_TOP + 1, -CELL - 4),
            'a tower floor': (far, 1, far),
            'the cellar': (RUNG[0] - 1, -SHAFT_H - CELL + 1, RUNG[1])}
    problems = []
    for label, spot in want.items():
        if not any((spot[0], spot[1] + dy, spot[2]) in seen for dy in (-1, 0, 1)):
            problems.append('%s cannot be walked to from the keep' % label)
    return problems


SWAP = {'minecraft:stone_bricks': BRICK,
        'minecraft:stone_brick_stairs': STAIR,
        'minecraft:stone_brick_slab': 'minecraft:diorite_slab',
        'minecraft:chiseled_stone_bricks': CHISEL,
        'minecraft:stone': STONE}
SWAP_UNDER = dict(SWAP, **{'minecraft:stone_bricks': CELLAR_BRICK,
                           'minecraft:stone_brick_stairs': 'minecraft:deepslate_tile_stairs',
                           'minecraft:stone_brick_slab': 'minecraft:deepslate_tile_slab',
                           'minecraft:chiseled_stone_bricks': 'minecraft:chiseled_deepslate'})


def repalette(name, piece):
    """Put the fortress into its own stone.

    The first pass was built out of stone bricks, and so is everything that came back from the
    workshop, because that is what was standing there to copy. This swaps the family over in
    one place rather than asking anyone to replace it block by block: above the courtyard to
    diorite and quartz, below it to deepslate. Nothing else about the piece changes."""
    table = SWAP_UNDER if name in UNDERGROUND else SWAP
    for pos, (block, props) in list(piece.grid.items()):
        if block in table:
            piece.set(pos[0], pos[1], pos[2], table[block],
                      dict(props) if props else None, piece.extra.get(pos))
    return piece


def handmade(name, built):
    """A piece rebuilt by hand in the workshop, if there is one, wearing the code's wiring.

    The looks are the human's and the wiring is the generator's (section 16), so what comes
    out of tools/handmade/ice/ is used for every block except the jigsaws, which are stamped
    back on from the piece this file would have built. `grab_workshop.py` puts them there,
    straight out of the world - nobody has to press SAVE."""
    path = os.path.join(HAND, name + '.nbt')
    if not os.path.isfile(path):
        return built
    root = nbt.read(path)
    size = tuple(int(v) for v in root['size'])
    if size != built.size:
        raise SystemExit('%s was rebuilt at %s but the mod wires it as %s; the box is the one '
                         'thing that cannot change' % (name, size, built.size))
    out = Piece(size[0], size[1], size[2], AIR)
    palette = [(nbt.palette_name(e), nbt.palette_props(e)) for e in root['palette']]
    for b in root['blocks']:
        x, y, z = (int(v) for v in b['pos'])
        block, props = palette[int(b['state'])]
        out.set(x, y, z, block, dict(props) if props else None,
                dict(b['nbt']) if 'nbt' in b else None)
    for pos, (block, props) in built.grid.items():          # the wiring goes back on
        if block == 'minecraft:jigsaw':
            out.set(pos[0], pos[1], pos[2], block, dict(props) if props else None,
                    built.extra.get(pos))
            continue
        # Chests, spawners and trial spawners carry nbt, and nbt is the generator's - there
        # is no way to set a loot table from inside the game (CLAUDE.md section 1). So the
        # code's furniture goes back wherever the hand-built piece left the space empty, and
        # where the piece kept the same block, at least the table does: a chest opened in the
        # workshop comes back holding one roll of it instead.
        was, now = built.extra.get(pos), out.extra.get(pos)
        if not was:
            continue
        here = out.grid.get(pos, (AIR,))[0]
        if here == AIR:
            out.set(pos[0], pos[1], pos[2], block, dict(props) if props else None, dict(was))
        elif here == block and 'LootTable' in was and (not now or 'LootTable' not in now):
            out.extra[pos] = dict(was)
    return out


def main():
    if not os.path.isdir(DST):
        os.makedirs(DST)
    tower_a = tower()
    pieces = {
        'keep': keep(),
        'panel': panel(),
        'panel_end': panel(ends=True),
        'gate': panel(gate=True),
        'tower_a': tower_a,
        'tower_b': mirrored(tower_a, CORNER_B, CORNER_B),
        'shaft': shaft(), 'cellar_hub': cellar_hub(),
        'passage': cellar('passage'), 'passage_guard': cellar('passage_guard'),
        'corner': cellar('corner'), 'cross': cellar('cross'),
        'cross_guard': cellar('cross_guard'), 'store': cellar('store'),
        'powder': cellar('powder'), 'slick': cellar('slick'),
        'bear_den': cellar('bear_den'), 'larder': cellar('larder'),
        'cap': cellar_cap(), 'frost_hall': frost_hall(),
    }
    for step in range(1, MIN_BOSS_STEPS + 1):
        pieces['approach_%d' % step] = approach(step)
    hand = 0
    for name in list(pieces):
        swapped = handmade(name, pieces[name])
        if swapped is not pieces[name]:
            pieces[name], hand = swapped, hand + 1
    if hand:
        print('  %d pieces came from tools/handmade/ice, wearing this file\'s wiring' % hand)
        floor_and_hole(pieces['keep'])          # wherever the hall's floor was left open
        shaft_wiring(pieces['shaft'], SHAFT_H - 1)
        hub_wiring(pieces['cellar_hub'])
    for name in pieces:
        repalette(name, pieces[name])
    furnish(pieces)
    verify(pieces)
    for name, piece in sorted(pieces.items()):
        piece.write(os.path.join(DST, name + '.nbt'))
        print('  %-16s %s' % (name, list(piece.size)))

    write_pool('start', [element('keep', 1)], EMPTY)
    write_pool('panels', [element('panel', 1)], EMPTY)
    write_pool('panels_end', [element('panel_end', 1)], EMPTY)
    write_pool('gate', [element('gate', 1)], EMPTY)
    write_pool('corner_a', [element('tower_a', 1)], EMPTY)
    write_pool('corner_b', [element('tower_b', 1)], EMPTY)
    write_pool('down', [element('shaft', 1)], EMPTY)
    write_pool('cellar_first', [element('cellar_hub', 1)], EMPTY)
    write_pool('cellars', [element('passage', 9), element('passage_guard', 5),
                           element('corner', 9), element('cross', 4),
                           element('cross_guard', 3), element('store', 8),
                           element('larder', 6), element('powder', 5),
                           element('slick', 5), element('bear_den', 4)],
               POOL['cellar_caps'])
    write_pool('cellar_caps', [element('cap', 1)], EMPTY)
    for step in range(1, MIN_BOSS_STEPS + 1):
        write_pool('lord_approach_%d' % step, [element('approach_%d' % step, 1)],
                   POOL['cellar_caps'])
    write_pool('lord_approach', [element('frost_hall', 1),
                                 element('approach_%d' % MIN_BOSS_STEPS, 1)],
               POOL['cellar_caps'])
    print('  pools -> %s' % os.path.relpath(POOL_JSON, ROOT))
    problems = walk_problems()
    for line in problems:
        print('  PROBLEM  ' + line)
    if problems:
        raise SystemExit('the fortress is built but you cannot walk it')
    print('  walked: courtyard, gate, both walkways, a tower top and floor, and the cellar')


if __name__ == '__main__':
    main()
