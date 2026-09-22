# -*- coding: utf-8 -*-
"""The Sunken Lighthouse: a broken tower on the shore, and a flooded fortress under it.

    python tools/generate_light.py        (or through make_pieces.py)

Writes data/sydungeon/structure/light/*.nbt and the pools that join them.

THE SHORE, NOT THE OPEN SEA
The concept says beach and ocean. A jigsaw structure has one heightmap and one only: the
shore pieces need WORLD_SURFACE_WG to stand on the sand, and out in the ocean that same
heightmap is the top of the water, which would float the tower on the waves. So this one is
on the beaches and the stony shores, and the sea it belongs to is the one it is standing in.

WATER IS PLACED, NOT INHERITED
The swamp taught the first half of this (CLAUDE.md section 17): a position a template does
not list keeps whatever the world had there, so the way to leave the sea alone is to leave
it out. The fortress needs the other half - it has to be full of water, and water that is
placed has to be walled in exactly like the dwarves' lava, or it drains into the rock around
it and the fortress is full of air.

So every flooded piece records its openings in `ports`, and water_problems() checks that no
water source has air beside or below it and that none of it sits on a face that is not an
opening. Two flooded cells always meet water to water, and the fallback cap is solid.

THE DRY SIDE AND THE WET SIDE MEET WHERE WATER CANNOT CLIMB
Water does not flow upwards, so the join is vertical: the ladder comes down from the
lighthouse into the sump, which is dry, and the sump's floor has a hole in it with the sea
two blocks below the lip. You jump in and swim down. Nothing has to hold the water back,
which is the only kind of seal this mod trusts.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import nbt  # noqa: E402
from generate_pieces import Piece  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DST = os.path.join(ROOT, 'src', 'main', 'resources', 'data', 'sydungeon', 'structure', 'light')
POOL_JSON = os.path.join(ROOT, 'src', 'main', 'resources', 'data', 'sydungeon', 'worldgen',
                         'template_pool', 'light')

NS = 'sydungeon'
SEA = NS + ':lht_sea'            # the connector the flooded fortress uses
DOWN = NS + ':lht_down'          # the vertical chain: tower, shaft, sump, dive
SENTINEL = NS + ':lht_sentinel'  # the boss branch, its own name so it cannot run backwards
EMPTY = 'minecraft:empty'
PRIORITY = 10

CELL = 7
GROUND = 0                       # the start piece's floor: a start is moved so that
                                 # minY + 1 is the first free block, so y=0 is the
                                 # terrain's own top block (section 30)
TOWER = 26                       # how much lighthouse stands above its floor
SHAFT_H = 21
DIVE_H = 14
BOSS = (21, 14, 21)
MIN_BOSS_STEPS = 3

# the column, shared by every piece it runs through (section 11). The dry part has a ladder
# with its own row left solid as a landing (section 24); below the sump the same three by
# three is full of sea and you swim it
HOLE = (CELL // 2, CELL // 2)    # one column, dead centre of the piece (section 33)
RUNG = HOLE                      # the ladder is the hole; below the sump, the sea is
JIG = (HOLE[0], HOLE[1] + 1)     # the pillar it hangs on, one out of the hole

ROCK = 'minecraft:stone'          # what the fortress is cut out of, and therefore what shows
BAND = 'minecraft:andesite'       # a course every few, so an exposed face reads as ground
BRICK = 'minecraft:stone_bricks'
CRACK = 'minecraft:cracked_stone_bricks'
MOSSY = 'minecraft:mossy_stone_bricks'
PRIS = 'minecraft:prismarine'
PRIS_BRICK = 'minecraft:prismarine_bricks'
DARK = 'minecraft:dark_prismarine'
SEA_LANTERN = 'minecraft:sea_lantern'
COPPER = 'minecraft:weathered_copper'
SPONGE = 'minecraft:wet_sponge'
SOUL = 'minecraft:soul_sand'
KELP = 'minecraft:kelp_plant'
LANTERN = 'minecraft:lantern'
CHAIN = 'minecraft:iron_chain'
BARS = 'minecraft:iron_bars'
WATER = 'minecraft:water'
AIR = 'minecraft:air'

SOURCE = {'level': '0'}
HANGING = {'hanging': 'true', 'waterlogged': 'false'}
STANDING = {'hanging': 'false', 'waterlogged': 'false'}
GRID = {'north': 'true', 'south': 'true', 'east': 'true', 'west': 'true',
        'waterlogged': 'true'}
KELP_AGE = {'age': '25'}

POOL = {k: NS + ':light/' + k for k in
        ['start', 'down', 'sump_first', 'dive', 'sea_first', 'seas', 'sea_caps',
         'sentinel_approach'] +
        ['sentinel_approach_%d' % i for i in range(1, MIN_BOSS_STEPS + 1)]}

TRIAL_STATE = {'trial_spawner_state': 'inactive', 'ominous': 'false'}
ANY_LIGHT = {'block_light_limit': {'min_inclusive': nbt.Int(0), 'max_inclusive': nbt.Int(15)}}


def trial_spawner(config):
    return {'id': 'minecraft:trial_spawner',
            'normal_config': NS + ':light/' + config,
            'ominous_config': NS + ':light/' + config,
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


def chest(table, facing='north', water=False):
    return ('minecraft:chest',
            {'facing': facing, 'type': 'single', 'waterlogged': 'true' if water else 'false'},
            {'id': 'minecraft:chest', 'LootTable': NS + ':chests/' + table})


def ladder(facing='north'):
    return ('minecraft:ladder', {'facing': facing, 'waterlogged': 'false'})


def bedrock(p, sx, sy, sz, at=0):
    """Fill with the ground's own stone, banded (section 5.2)."""
    for y in range(sy):
        p.box(0, y, 0, sx - 1, y, sz - 1, ROCK if (y + at) % 4 else BAND)


def sea(p, x, y, z):
    """One block of placed sea, and a note of it if it is on a face."""
    p.set(x, y, z, WATER, SOURCE)
    sx, sy, sz = p.size
    if x in (0, sx - 1) or y in (0, sy - 1) or z in (0, sz - 1):
        p.ports.add((x, y, z))


def flood(p, x0, y0, z0, x1, y1, z1):
    for x in range(x0, x1 + 1):
        for y in range(y0, y1 + 1):
            for z in range(z0, z1 + 1):
                sea(p, x, y, z)


# ------------------------------------------------------------------------- the way down
def sink(p, y0, y1, fill=BRICK):
    """The way down: one column of ladder, and a ring of solid block round it.

    On a beach the ring is the whole point - three wide, patched only where the piece
    happened to have air, it let the sea in (section 33)."""
    cx, cz = HOLE
    for x in range(cx - 1, cx + 2):
        for z in range(cz - 1, cz + 2):
            for y in range(y0, y1 + 1):
                p.set(x, y, z, fill)
    for y in range(y0, y1 + 1):
        p.set(cx, y, cz, *ladder())


# ------------------------------------------------------------------------ the lighthouse
def lighthouse():
    """The start: what is left of the tower. Seven across, so the beach around it is left
    exactly as the world made it - a wider piece would floor the shore with its own stone.

    The lamp room at the top is broken open on the north side, and the ladder inside runs the
    whole way up, because a lighthouse you cannot climb is only a chimney."""
    p = Piece(CELL, GROUND + TOWER + 1, CELL, AIR)
    p.ports = set()
    g, mid = GROUND, CELL // 2
    p.box(0, g, 0, CELL - 1, g, CELL - 1, BRICK)                   # the floor, on the ground
    for y in range(g + 1, g + TOWER):                              # the wall of the tower
        for x in range(CELL):
            for z in range(CELL):
                if x in (0, CELL - 1) or z in (0, CELL - 1):
                    broken = y > g + 16 and (x * 3 + z * 5 + y * 7) % 5 == 0
                    if y > g + 21 and z < mid:
                        broken = True                              # the seaward face is gone
                    if not broken:
                        p.set(x, y, z, MOSSY if (x + z + y) % 7 == 0 else
                              CRACK if (x * 5 + y) % 6 == 0 else BRICK)
    p.box(0, g + 1, 0, 0, g + 4, 0, BRICK)                         # corner posts, unbroken
    for y in range(g + 1, g + TOWER):
        for x, z in ((0, 0), (0, CELL - 1), (CELL - 1, 0), (CELL - 1, CELL - 1)):
            if p.grid[(x, y, z)][0] == AIR and y < g + 22:
                p.set(x, y, z, PRIS_BRICK)

    p.box(0, g + 1, mid - 1, 0, g + 4, mid + 1, AIR)               # the door, facing the sea
    p.set(0, g + 5, mid, PRIS_BRICK)
    for y in range(g + 1, g + 23):                                 # the wall the climb hangs on
        p.set(CELL - 2, y, CELL - 1, BRICK)
    for y in range(g + 1, g + 22):                                 # the climb to the lamp
        p.set(CELL - 2, y, CELL - 2, *ladder('north'))
    for y in (g + 8, g + 15):                                      # windows
        p.box(mid, y, 0, mid, y + 1, 0, AIR)
        p.box(mid, y, CELL - 1, mid, y + 1, CELL - 1, AIR)
    # the lamp: a sea lantern in a ring of weathered copper, mostly fallen in
    p.box(1, g + 22, 1, CELL - 2, g + 22, CELL - 2, DARK)
    for x in range(1, CELL - 1):
        for z in range(1, CELL - 1):
            if (x in (1, CELL - 2) or z in (1, CELL - 2)) and (x * 3 + z) % 4:
                p.set(x, g + 23, z, COPPER)
                p.set(x, g + 24, z, COPPER)
    p.set(mid, g + 23, mid, SEA_LANTERN)
    p.set(mid, g + 24, mid, SEA_LANTERN)
    p.box(1, g + 22, mid - 1, 1, g + 24, mid + 1, AIR)             # the way onto the gallery
    p.set(CELL - 2, g + 22, CELL - 2, AIR)                         # the ladder's own hole
    p.set(CELL - 2, g + 22, CELL - 2, *ladder('north'))

    p.set(1, g + 1, CELL - 2, *chest('light_tower', 'north'))
    p.set(CELL - 2, g + 1, 1, LANTERN, STANDING)
    p.set(1, g + 1, 1, 'minecraft:barrel', {'facing': 'up', 'open': 'false'})

    cx, cz = HOLE
    for x in range(CELL):                                          # the floor, and the hole
        for z in range(CELL):
            if (x, z) != (cx, cz):
                if p.grid.get((x, g, z), (AIR,))[0] in (AIR, 'minecraft:ladder'):
                    p.set(x, g, z, BRICK)
    sink(p, 0, g)
    p.jigsaw(JIG[0], 0, JIG[1], 'down_east', POOL['down'], BRICK, joint='aligned',
             priority=PRIORITY, name=DOWN, target=DOWN)
    return p


def shaft():
    """Dry, twenty-one deep, stone all the way: the sea starts below the sump."""
    p = Piece(CELL, SHAFT_H, CELL, ROCK)
    p.ports = set()
    bedrock(p, CELL, SHAFT_H, CELL, at=SHAFT_H)
    top = SHAFT_H - 1
    for x in range(CELL):
        for y in range(SHAFT_H):
            for z in range(CELL):
                if p.grid.get((x, y, z), (AIR,))[0] in (AIR, 'minecraft:ladder'):
                    p.set(x, y, z, ROCK)
    sink(p, 0, top, fill=ROCK)
    p.jigsaw(JIG[0], top, JIG[1], 'up_east', EMPTY, ROCK, joint='aligned',
             name=DOWN, target=DOWN)
    p.jigsaw(JIG[0], 0, JIG[1], 'down_east', POOL['sump_first'], ROCK, joint='aligned',
             priority=PRIORITY, name=DOWN, target=DOWN)
    return p


def sump():
    """Dry, and the last of it. The ladder lands here and the floor has the sea in it: the
    two halves of this dungeon meet at a surface, which is the one seal water respects."""
    p = Piece(CELL, CELL, CELL, ROCK)
    p.ports = set()
    bedrock(p, CELL, CELL, CELL)
    p.box(1, 1, 1, CELL - 2, CELL - 2, CELL - 2, AIR)
    p.box(0, 0, 0, CELL - 1, 0, CELL - 1, BRICK)
    mid = CELL // 2
    cx, cz = HOLE
    for x in range(CELL):                                          # the ceiling and its hole
        for z in range(CELL):
            if p.grid.get((x, CELL - 1, z), (AIR,))[0] in (AIR, 'minecraft:ladder'):
                p.set(x, CELL - 1, z, ROCK)
    for y in range(1, CELL):
        p.set(JIG[0], y, JIG[1], BRICK)                            # the ladder's pillar
    for y in range(1, CELL):
        p.set(cx, y, cz, *ladder())                                # the climb, ceiling too
    p.jigsaw(JIG[0], CELL - 1, JIG[1], 'up_east', EMPTY, BRICK, joint='aligned',
             name=DOWN, target=DOWN)
    p.set(cx, 0, cz, AIR)                                          # the hole into the sea
    p.jigsaw(JIG[0], 0, JIG[1], 'down_east', POOL['dive'], BRICK, joint='aligned',
             priority=PRIORITY, name=DOWN, target=DOWN)
    p.set(1, 1, 1, *chest('light_tower', 'east'))
    p.set(CELL - 2, 1, 1, LANTERN, STANDING)
    p.set(CELL - 2, 1, CELL - 2, 'minecraft:barrel', {'facing': 'up', 'open': 'false'})
    p.set(mid, CELL - 2, mid + 2, LANTERN, HANGING)
    return p


def dive():
    """The water column. Its top course is the lip: air, so the sea's surface sits two below
    the sump's floor and stays there - water does not climb."""
    p = Piece(CELL, DIVE_H, CELL, ROCK)
    p.ports = set()
    bedrock(p, CELL, DIVE_H, CELL, at=2)
    top = DIVE_H - 1
    cx, cz = HOLE
    p.box(cx, 0, cz, cx, top, cz, AIR)
    flood(p, cx, 0, cz, cx, top - 1, cz)
    for y in range(0, top + 1):
        p.set(JIG[0], y, JIG[1], PRIS_BRICK)                       # the jigsaw's own column
    p.jigsaw(JIG[0], top, JIG[1], 'up_east', EMPTY, PRIS_BRICK, joint='aligned',
             name=DOWN, target=DOWN)
    p.jigsaw(JIG[0], 0, JIG[1], 'down_east', POOL['sea_first'], PRIS_BRICK, joint='aligned',
             priority=PRIORITY, name=SEA, target=SEA)
    return p


# -------------------------------------------------------------------------- the fortress
def sea_room(doors, height=CELL, floor_at=0, air_above=0):
    """A cell of the flooded fortress: one wall of rock thick (section 5.2), prismarine
    floor, sea inside, and every doorway full of sea so two cells always meet water to
    water. `air_above` leaves that many courses at the top as air, which is how the boss
    hall gets somewhere to stand."""
    p = Piece(CELL, height, CELL, ROCK)
    p.ports = set()
    bedrock(p, CELL, height, CELL)
    ceiling = floor_at + CELL - 2
    p.box(1, floor_at + 1, 1, CELL - 2, ceiling, CELL - 2, AIR)
    flood(p, 1, floor_at + 1, 1, CELL - 2, ceiling - air_above, CELL - 2)
    p.box(0, floor_at, 0, CELL - 1, floor_at, CELL - 1, DARK)
    mid = CELL // 2
    for side in doors:
        for y in range(floor_at + 1, floor_at + 5):
            for a in (mid - 1, mid, mid + 1):
                if side == 'west':
                    sea(p, 0, y, a)
                elif side == 'east':
                    sea(p, CELL - 1, y, a)
                elif side == 'north':
                    sea(p, a, y, 0)
                else:
                    sea(p, a, y, CELL - 1)
    return p


SEA_AT = {'west': (0, 3, 'west_up'), 'east': (CELL - 1, 3, 'east_up'),
          'north': (3, 0, 'north_up'), 'south': (3, CELL - 1, 'south_up')}


def sea_door(p, side, pool, y=0, name=SEA, target=SEA, priority=0):
    x, z, orientation = SEA_AT[side]
    p.jigsaw(x, y, z, orientation, pool, ROCK, priority=priority, name=name, target=target)


def sea_hub():
    """Where the dive lands. Three doors, and the hole in the ceiling it came through."""
    p = sea_room(['west', 'north', 'south'])
    cx, cz = HOLE
    for x in range(CELL):
        for z in range(CELL):
            if p.grid.get((x, CELL - 1, z), (AIR,))[0] in (AIR, WATER):
                p.set(x, CELL - 1, z, ROCK)
    for y in range(1, CELL - 1):
        p.set(JIG[0], y, JIG[1], PRIS_BRICK)
    flood(p, cx, CELL - 1, cz, cx, CELL - 1, cz)        # the one column of sea in the roof
    p.jigsaw(JIG[0], CELL - 1, JIG[1], 'up_east', EMPTY, PRIS_BRICK, joint='aligned',
             name=SEA, target=SEA)
    sea_door(p, 'west', POOL['seas'])
    sea_door(p, 'north', POOL['seas'])
    sea_door(p, 'south', POOL['sentinel_approach_1'], name=SEA, target=SENTINEL,
             priority=PRIORITY)
    p.set(1, 1, 1, SEA_LANTERN)
    p.set(CELL - 2, 1, CELL - 2, SEA_LANTERN)
    return p


def cell(kind):
    doors = {'hall': ['west', 'east'], 'bend': ['west', 'south'],
             'junction': ['west', 'east', 'north', 'south'],
             'guard': ['west', 'east', 'north', 'south'],
             'column': ['west', 'east'], 'kelp': ['west', 'east'],
             'sponge': ['west'], 'vault': ['west']}[kind]
    p = sea_room(doors)
    for side in doors:
        sea_door(p, side, POOL['seas'])
    mid = CELL // 2
    if kind == 'hall':
        for z in (1, CELL - 2):
            p.set(1, 1, z, PRIS_BRICK)
            p.set(CELL - 2, 1, z, PRIS)
        p.set(1, CELL - 2, mid, SEA_LANTERN)
    elif kind == 'bend':
        p.set(CELL - 2, 1, 1, PRIS_BRICK)
        p.set(CELL - 2, 2, 1, SEA_LANTERN)
    elif kind == 'junction':
        p.box(mid - 1, 0, mid - 1, mid + 1, 0, mid + 1, PRIS_BRICK)
        p.set(mid, CELL - 2, mid, SEA_LANTERN)
        for x, z in ((1, 1), (1, CELL - 2), (CELL - 2, 1), (CELL - 2, CELL - 2)):
            for y in (1, 2, 3):
                p.set(x, y, z, PRIS)
    elif kind == 'guard':
        p.box(mid - 1, 0, mid - 1, mid + 1, 0, mid + 1, PRIS_BRICK)
        p.set(mid, 1, mid, 'minecraft:spawner', None, mob_spawner('minecraft:guardian', 1))
        p.set(1, 1, 1, BARS, GRID)
        p.set(CELL - 2, 1, CELL - 2, BARS, GRID)
    elif kind == 'column':
        # soul sand under the sea makes a rising column of bubbles and rides you up it. No
        # trigger of any kind: it is on whether anyone is there or not (section 12)
        for x in (mid - 1, mid, mid + 1):
            p.set(x, 1, mid, SOUL)
        p.set(1, 1, 1, PRIS)
        p.set(CELL - 2, CELL - 2, CELL - 2, SEA_LANTERN)
    elif kind == 'kelp':
        for x, z in ((1, 1), (2, CELL - 2), (CELL - 2, 2), (CELL - 3, CELL - 3)):
            for y in (1, 2, 3):
                p.set(x, y, z, KELP, KELP_AGE)
        p.set(mid, 0, mid, PRIS)
    elif kind == 'sponge':
        for x in (1, CELL - 2):
            for y in (1, 2):
                p.set(x, y, CELL - 2, SPONGE)
        p.set(mid, 1, CELL - 2, *chest('light_sponge', 'north', water=True))
        p.set(mid, CELL - 2, mid, SEA_LANTERN)
    elif kind == 'vault':
        p.box(1, 1, 1, CELL - 2, 1, 1, PRIS_BRICK)
        p.set(mid, 2, 1, *chest('light_vault', 'south', water=True))
        p.set(1, 1, CELL - 2, *chest('light_vault', 'north', water=True))
        p.set(1, 2, 1, SEA_LANTERN)
        p.set(CELL - 2, 2, 1, SEA_LANTERN)
    return p


def sea_cap():
    p = Piece(1, CELL, CELL, ROCK)
    p.ports = set()
    bedrock(p, 1, CELL, CELL)
    p.jigsaw(0, 0, 3, 'west_up', POOL['sea_caps'], ROCK, name=SEA, target=SEA)
    return p


def approach(step):
    p = sea_room(['west', 'east', 'north'])
    p.jigsaw(0, 0, 3, 'west_up', POOL['seas'], ROCK, name=SENTINEL, target=SEA)
    nxt = (('sentinel_approach_%d' % (step + 1)) if step < MIN_BOSS_STEPS
           else 'sentinel_approach')
    sea_door(p, 'east', POOL[nxt], name=SEA, target=SENTINEL, priority=PRIORITY)
    sea_door(p, 'north', POOL['seas'])
    p.set(1, 1, 1, PRIS_BRICK)
    p.set(1, 2, 1, SEA_LANTERN)
    return p


def sentinel_hall():
    """His hall, half drained: sea to head height and air above it, so the fight can be won
    without a potion. The guardians' spawners are under the water, where guardians live; the
    sentinel's own is on a dais that breaks the surface."""
    sx, sy, sz = BOSS
    p = Piece(sx, sy, sz, ROCK)
    p.ports = set()
    bedrock(p, sx, sy, sz)
    p.box(1, 1, 1, sx - 2, sy - 2, sz - 2, AIR)
    p.box(0, 0, 0, sx - 1, 0, sz - 1, DARK)
    for y in range(1, 7):                                          # the sea, six deep
        for x in range(1, sx - 1):
            for z in range(1, sz - 1):
                sea(p, x, y, z)
    for y in range(1, 5):                                          # the way in, flooded
        for a in (sz // 2 - 1, sz // 2, sz // 2 + 1):
            sea(p, 0, y, a)
    p.jigsaw(0, 0, sz // 2, 'west_up', EMPTY, ROCK, name=SENTINEL, target=SEA)

    c = sx // 2
    for x0, z0 in ((4, 4), (4, sz - 6), (sx - 6, 4), (sx - 6, sz - 6)):   # the four columns
        for y in range(1, sy - 1):
            p.box(x0, y, z0, x0 + 1, y, z0 + 1, PRIS if y % 4 else DARK)
    p.box(c - 3, 1, 3, c + 3, 7, 8, PRIS_BRICK)                     # the dais, out of the sea
    p.box(c - 2, 8, 4, c + 2, 8, 7, DARK)
    p.set(c, 9, 5, 'minecraft:trial_spawner', TRIAL_STATE, trial_spawner('deep_sentinel'))
    p.set(c - 2, 9, 4, SEA_LANTERN)
    p.set(c + 2, 9, 4, SEA_LANTERN)
    for x, z in ((5, 12), (sx - 6, 12), (5, sz - 4), (sx - 6, sz - 4)):
        p.set(x, 1, z, 'minecraft:trial_spawner', TRIAL_STATE, trial_spawner('sunken_guards'))
    for x, z in ((2, 2), (sx - 3, 2), (2, sz - 3), (sx - 3, sz - 3)):
        p.set(x, 1, z, SEA_LANTERN)
    for x, z in ((c, 12), (4, c), (sx - 5, c)):
        p.set(x, sy - 2, z, SEA_LANTERN)
    return p


# ---------------------------------------------------------------------------------- pools
def element(location, weight):
    return ('    { "weight": %d, "element": { "element_type": "minecraft:single_pool_element",'
            '\n        "location": "%s:light/%s", "projection": "rigid", '
            '"processors": "%s:light_weathering" } }' % (weight, NS, location, NS))


def write_pool(name, elements, fallback):
    if not os.path.isdir(POOL_JSON):
        os.makedirs(POOL_JSON)
    text = ('{\n  "fallback": "%s",\n  "elements": [\n%s\n  ]\n}\n'
            % (fallback, ',\n'.join(elements)))
    with open(os.path.join(POOL_JSON, name + '.json'), 'w', encoding='utf-8',
              newline='\n') as f:
        f.write(text)


# ---------------------------------------------------------------------------------- checks
HANGS = {'minecraft:lantern', 'minecraft:sea_lantern', 'minecraft:ladder',
         'minecraft:iron_bars', 'minecraft:iron_chain', 'minecraft:water',
         'minecraft:kelp_plant'}
AROUND = ((1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1))
BESIDE = ((1, 0, 0), (-1, 0, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1))
BEHIND = {'north': (0, 0, 1), 'south': (0, 0, -1), 'east': (-1, 0, 0), 'west': (1, 0, 0)}
STANDS_ON = ('minecraft:barrel', 'minecraft:spawner', 'minecraft:trial_spawner',
             'minecraft:soul_sand')


def fitting_problems(pieces):
    problems = []
    for name, piece in sorted(pieces.items()):
        size = piece.size

        def solid(pos):
            block = piece.grid.get(pos)
            return bool(block) and block[0] != AIR and block[0] not in HANGS

        for pos, (block, props) in sorted(piece.grid.items()):
            props = dict(props or ())
            if block in (AIR, 'minecraft:jigsaw', WATER):
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
            if block == KELP:
                below = piece.grid.get((pos[0], pos[1] - 1, pos[2]))
                if not (solid((pos[0], pos[1] - 1, pos[2]))
                        or (below and below[0] == KELP)):
                    problems.append('%s: the kelp at %s grows on nothing' % (name, pos))
            if block == LANTERN and props.get('hanging') == 'true':
                if not solid((pos[0], pos[1] + 1, pos[2])):
                    problems.append('%s: the lantern at %s hangs on nothing' % (name, pos))
            if block.endswith('chest') and 'LootTable' not in (piece.extra.get(pos) or {}):
                problems.append('%s: the chest at %s has no loot table' % (name, pos))
    return problems


def water_problems(pieces):
    """Placed water has to be walled in, the same as the dwarves' lava.

    Beside or below a source, air means the fortress drains into itself; a face that is not a
    recorded opening means it drains into the rock and the sea outside. Above is left alone -
    that is a surface, and the whole join between the dry half and the wet half is a surface.
    """
    problems = []
    for name, piece in sorted(pieces.items()):
        sx, sy, sz = piece.size
        ports = getattr(piece, 'ports', set())
        for pos, (block, _) in sorted(piece.grid.items()):
            if block != WATER:
                continue
            x, y, z = pos
            on_face = x in (0, sx - 1) or y in (0, sy - 1) or z in (0, sz - 1)
            if on_face and pos not in ports:
                problems.append('%s: the sea at %s is on a face that is not an opening; it '
                                'would drain into whatever is next to it' % (name, pos))
            for dx, dy, dz in BESIDE:
                side = (x + dx, y + dy, z + dz)
                if not (0 <= side[0] < sx and 0 <= side[1] < sy and 0 <= side[2] < sz):
                    continue
                if piece.grid[side][0] == AIR:
                    problems.append('%s: the sea at %s can run to the air at %s'
                                    % (name, pos, side))
    return problems


def door_problems(pieces):
    """Every doorway of a flooded piece has to be sea, not air: two cells meet water to
    water or the pair of them drains."""
    problems = []
    mid = CELL // 2
    for name, piece in sorted(pieces.items()):
        if not getattr(piece, 'ports', None):
            continue
        sx, sy, sz = piece.size
        if sx != CELL or sz != CELL:
            continue
        for pos, entry in sorted(piece.extra.items()):
            if entry.get('id') != 'minecraft:jigsaw':
                continue
            orientation = dict(piece.grid[pos][1] or ()).get('orientation', '')
            if orientation.split('_')[0] not in ('west', 'east', 'north', 'south'):
                continue
            x, y, z = pos
            for dy in range(1, 5):
                for a in (mid - 1, mid, mid + 1):
                    spot = ((x, y + dy, a) if x in (0, sx - 1) else (a, y + dy, z))
                    if piece.grid[spot][0] != WATER:
                        problems.append('%s: the doorway at %s is %s, and a flooded cell has '
                                        'to meet its neighbour water to water'
                                        % (name, spot, piece.grid[spot][0].split(':')[-1]))
    return problems


def ladder_problems(pieces):
    at = {'lighthouse': (0, 0, 0), 'shaft': (0, -SHAFT_H, 0),
          'sump': (0, -SHAFT_H - CELL, 0)}
    cx, cz = HOLE
    cased = at['sump'][1] + CELL - 1
    problems = []
    for y in range(at['sump'][1] + 1, GROUND + 1):
        for dx in (-1, 0, 1):
            for dz in (-1, 0, 1):
                if (dx, dz) != (0, 0) and y < cased:
                    continue               # inside the sump the ring is the room itself
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
                elif block in (AIR, WATER, 'minecraft:ladder'):
                    problems.append('%s leaves %s at %s: the ring round the shaft has to be '
                                    'solid the whole way down, and on a beach that is what '
                                    'keeps the sea out (section 33)'
                                    % (name, block.split(':')[-1], (x, y, z)))
    return problems


def verify(pieces):
    problems = (ladder_problems(pieces) + fitting_problems(pieces)
                + water_problems(pieces) + door_problems(pieces))
    for name, piece in pieces.items():
        if max(piece.size) > 48:
            problems.append('%s is %s: too big to rebuild by hand' % (name, piece.size))
        count = sum(1 for pos, (block, _) in piece.grid.items()
                    if block == 'minecraft:jigsaw'
                    and (piece.extra.get(pos) or {}).get('name') == SENTINEL)
        if count > 1:
            problems.append('%s carries %d jigsaws named %s; the chain could be entered '
                            'through its own continuation' % (name, count, SENTINEL))
    for line in problems:
        print('  PROBLEM  ' + line)
    if problems:
        raise SystemExit('the sunken lighthouse does not hold together')
    print('  checked: the ladder unbroken from the lamp room down to the sump, the sea '
          'walled in everywhere and every flooded doorway full of it, nothing hangs in '
          'mid-air, every chest has a table, one way into the sentinel')


PASSABLE = {'air', 'water', 'ladder', 'lantern', 'iron_chain', 'kelp_plant'}


def walk_problems():
    """Assemble what was written and travel it the way the game would: down the ladder, off
    the lip, and swim to the fortress."""
    import gen_level_doc as doc

    pieces, pools = doc.load_family('light'), doc.load_pools('light')
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
        # anything outside the pieces is the world's own ground as far as this is concerned:
        # unknown counts as solid, or the walk falls out of the structure and never stops
        return world.get(p) in PASSABLE

    def body(p):
        # room for a player to be: the block and the one over its head
        x, y, z = p
        return open_at(p) and open_at((x, y + 1, z))

    def held(p):
        # something to stand on, or something to hold on to, or water to float in
        x, y, z = p
        return (not open_at((x, y - 1, z)) or world.get(p) in ('water', 'ladder')
                or world.get((x, y - 1, z)) in ('water', 'ladder'))

    g = GROUND
    door = (1, g + 1, CELL // 2)
    seen, queue = {door}, [door]
    while queue:
        x, y, z = queue.pop()
        here, over = world.get((x, y, z)), world.get((x, y + 1, z))
        moves = [(x, y - 1, z)]                          # down: gravity, or swimming down
        if here in ('water', 'ladder') or over in ('water', 'ladder'):
            moves.append((x, y + 1, z))                  # up: only climbing or swimming
        for a, c in ((x + 1, z), (x - 1, z), (x, z + 1), (x, z - 1)):
            if held((x, y, z)):                          # sideways, and a step up
                moves.append((a, y, c))
                moves.append((a, y + 1, c))
        for move in moves:
            if move not in seen and body(move):
                seen.add(move)
                queue.append(move)

    deep = -SHAFT_H - CELL - DIVE_H - CELL + 3
    want = {'the sump': (RUNG[0], -SHAFT_H - CELL + 1, RUNG[1]),
            'the fortress': (RUNG[0], deep, RUNG[1])}
    problems = []
    for label, spot in sorted(want.items()):
        if not any((spot[0], spot[1] + dy, spot[2]) in seen for dy in (-1, 0, 1)):
            problems.append('%s cannot be reached from the lighthouse' % label)
    return problems


def main():
    if not os.path.isdir(DST):
        os.makedirs(DST)
    pieces = {
        'lighthouse': lighthouse(), 'shaft': shaft(), 'sump': sump(), 'dive': dive(),
        'sea_hub': sea_hub(),
        'hall': cell('hall'), 'bend': cell('bend'), 'junction': cell('junction'),
        'guard': cell('guard'), 'column': cell('column'), 'kelp': cell('kelp'),
        'sponge': cell('sponge'), 'vault': cell('vault'),
        'cap': sea_cap(), 'sentinel_hall': sentinel_hall(),
    }
    for step in range(1, MIN_BOSS_STEPS + 1):
        pieces['approach_%d' % step] = approach(step)
    verify(pieces)
    for name, piece in sorted(pieces.items()):
        piece.write(os.path.join(DST, name + '.nbt'))
        print('  %-16s %s' % (name, list(piece.size)))

    write_pool('start', [element('lighthouse', 1)], EMPTY)
    write_pool('down', [element('shaft', 1)], EMPTY)
    write_pool('sump_first', [element('sump', 1)], EMPTY)
    write_pool('dive', [element('dive', 1)], EMPTY)
    write_pool('sea_first', [element('sea_hub', 1)], EMPTY)
    write_pool('seas', [element('hall', 10), element('bend', 9),
                        element('junction', 4), element('guard', 5),
                        element('column', 5), element('kelp', 7),
                        element('sponge', 5), element('vault', 6)],
               POOL['sea_caps'])
    write_pool('sea_caps', [element('cap', 1)], EMPTY)
    for step in range(1, MIN_BOSS_STEPS + 1):
        write_pool('sentinel_approach_%d' % step, [element('approach_%d' % step, 1)],
                   POOL['sea_caps'])
    write_pool('sentinel_approach', [element('sentinel_hall', 1),
                                     element('approach_%d' % MIN_BOSS_STEPS, 1)],
               POOL['sea_caps'])
    print('  pools -> %s' % os.path.relpath(POOL_JSON, ROOT))
    problems = walk_problems()
    for line in problems:
        print('  PROBLEM  ' + line)
    if problems:
        raise SystemExit('the lighthouse is built but you cannot get down it')
    print('  walked: the lighthouse down the ladder, off the lip and into the fortress')


if __name__ == '__main__':
    main()
