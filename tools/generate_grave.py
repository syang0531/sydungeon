# -*- coding: utf-8 -*-
"""The Cursed Graveyard: plots spreading from a ruined chapel, and an ossuary beneath.

    python tools/generate_grave.py        (or through make_pieces.py)

Writes data/sydungeon/structure/grave/*.nbt and the pools that join them.

THE SWAMP'S MACHINE, NOT THE FORTRESS'S
The ice fortress and the warlord's camp are rings: a wall of deterministic pieces closing on
itself. A graveyard is the other kind. The chapel is the start and the plots grow outward from
it wherever there is room - the loosest use of the jigsaw in this mod, the same as the swamp's
boardwalks (CLAUDE.md section 17) - and the fallback is a single panel of iron railing, so a
row of graves never ends in mid-air.

WHAT IS UNDER IT IS CUT OUT OF ROCK
The ossuary follows section 5.2: its shells are cobble and stone banded like the ground, and
the stone brick, the bone and the candles are all on the inside. Dark forest is not badlands,
but a crypt surfacing on a hillside would read as a box of masonry all the same. The shaft
goes down twenty-eight.

THE HORSE
The concept promised a tamed skeleton horse for beating the boss. A trial spawner is done when
what it spawned is dead, so a mounted boss means killing the mount - which is the reward. So
the captain fights on foot, his stable stands in the same hall as an ordinary spawner of
**tame** skeleton horses, and the saddle is one of the guaranteed drops. Win and the horses are
still standing.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import nbt  # noqa: E402
from generate_pieces import Piece  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DST = os.path.join(ROOT, 'src', 'main', 'resources', 'data', 'sydungeon', 'structure', 'grave')
POOL_JSON = os.path.join(ROOT, 'src', 'main', 'resources', 'data', 'sydungeon', 'worldgen',
                         'template_pool', 'grave')

NS = 'sydungeon'
YARD = NS + ':grv_path'          # the graveyard's connector
CRYPT = NS + ':grv_crypt'        # the ossuary's
DOWN = NS + ':grv_down'          # the one way between them
CAPTAIN = NS + ':grv_captain'    # the boss branch, its own name so it cannot run backwards
EMPTY = 'minecraft:empty'
PRIORITY = 10

CELL = 7
CHAPEL = 21                      # the chapel is three cells across
FOOT = 5                         # courses of footing under the chapel and the plots
SHAFT_H = 28
BOSS = (21, 14, 21)
MIN_BOSS_STEPS = 3

# the way down, in the chapel's coordinates: the middle of the floor, the ladder against the
# south wall of the hole with its own row left solid as a landing (section 24)
HOLE = (CHAPEL // 2 - 1, CHAPEL // 2 + 1, CHAPEL // 2 - 1, CHAPEL // 2 + 1)
RUNG = (CHAPEL // 2 - 1, CHAPEL // 2 + 1)
JIG = (RUNG[0], RUNG[1] + 1)
SHAFT_AT = CELL

BRICK = 'minecraft:stone_bricks'
CRACKED = 'minecraft:cracked_stone_bricks'
MOSSY = 'minecraft:mossy_stone_bricks'
CHISEL = 'minecraft:chiseled_stone_bricks'
WALL = 'minecraft:mossy_cobblestone_wall'
COBBLE = 'minecraft:cobblestone'
ROCK = 'minecraft:stone'         # what the ossuary is cut out of, and therefore what shows
BAND = 'minecraft:andesite'      # a course of it every few, so an exposed face reads as ground
BONE = 'minecraft:bone_block'
SOUL = 'minecraft:soul_soil'
PALE = 'minecraft:pale_oak_log'
PALE_PLANK = 'minecraft:pale_oak_planks'
PALE_FENCE = 'minecraft:pale_oak_fence'
MOSS_HANG = 'minecraft:pale_hanging_moss'
DARK = 'minecraft:dark_oak_log'
BARS = 'minecraft:iron_bars'
PODZOL = 'minecraft:podzol'
DIRT = 'minecraft:coarse_dirt'
GRAVEL = 'minecraft:gravel'
SKULL = 'minecraft:skeleton_skull'
CANDLE = 'minecraft:black_candle'
SOUL_LANTERN = 'minecraft:soul_lantern'
WEB = 'minecraft:cobweb'
BUSH = 'minecraft:dead_bush'
AIR = 'minecraft:air'

HANGING = {'hanging': 'true', 'waterlogged': 'false'}
GRID = {'north': 'true', 'south': 'true', 'east': 'true', 'west': 'true',
        'waterlogged': 'false'}
POST = {'north': 'false', 'south': 'false', 'east': 'false', 'west': 'false',
        'up': 'true', 'waterlogged': 'false'}
LIT_CANDLE = {'candles': '2', 'lit': 'true', 'waterlogged': 'false'}

POOL = {k: NS + ':grave/' + k for k in
        ['start', 'plots', 'plot_caps', 'down', 'crypt_first', 'crypts', 'crypt_caps',
         'captain_approach'] +
        ['captain_approach_%d' % i for i in range(1, MIN_BOSS_STEPS + 1)]}

TRIAL_STATE = {'trial_spawner_state': 'inactive', 'ominous': 'false'}
ANY_LIGHT = {'block_light_limit': {'min_inclusive': nbt.Int(0), 'max_inclusive': nbt.Int(15)}}


def trial_spawner(config):
    return {'id': 'minecraft:trial_spawner',
            'normal_config': NS + ':grave/' + config,
            'ominous_config': NS + ':grave/' + config,
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


def bedrock(p, sx, sy, sz):
    """Fill a piece with the ground's own stone, banded. This is what an exposed piece looks
    like from outside, and it is why the ossuary's shell is not stone brick (section 5.2)."""
    for y in range(sy):
        p.box(0, y, 0, sx - 1, y, sz - 1, ROCK if y % 4 else BAND)


# ------------------------------------------------------------------------- the way down
def sink(p, y0, y1, off=0, fill=BRICK, landing=None):
    """The hole and the ladder in it. `off` converts the chapel's coordinates into this
    piece's, so the three pieces that share the column cannot drift apart."""
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


# ---------------------------------------------------------------------------- the surface
PATH_AT = {'west': (0, FOOT, 3, 'west_up'), 'east': (CELL - 1, FOOT, 3, 'east_up'),
           'north': (3, FOOT, 0, 'north_up'), 'south': (3, FOOT, CELL - 1, 'south_up')}


def ground(sx, sz, top=PODZOL):
    """A plot of the graveyard: a footing that reaches down so the plot does not stand on
    stumps where the forest floor falls away (section 18), turf at the chapel's level, and
    air carved out above it."""
    p = Piece(sx, FOOT + 9, sz, AIR)
    p.box(0, 0, 0, sx - 1, FOOT - 1, sz - 1, DIRT)
    p.box(0, FOOT, 0, sx - 1, FOOT, sz - 1, top)
    p.box(0, FOOT + 1, 0, sx - 1, FOOT + 8, sz - 1, AIR)
    return p


def path(p, side, pool, name=YARD, target=YARD, priority=0):
    x, y, z, orientation = PATH_AT[side]
    p.jigsaw(x, y, z, orientation, pool, PODZOL, priority=priority, name=name, target=target)


def headstone(p, x, z, y=FOOT + 1, skull=False):
    p.set(x, y, z, WALL, POST)
    if skull:
        p.set(x, y + 1, z, SKULL, {'rotation': '8', 'powered': 'false'})


def plot(kind):
    """One cell of the graveyard. The doorways are the paths between plots, and they are cut
    like every other doorway in this mod - three wide and four tall (section 2)."""
    doors = {'row': ['west', 'east'], 'corner': ['west', 'south'],
             'cross': ['west', 'east', 'north', 'south'],
             'open_grave': ['west', 'east'], 'tomb': ['west'], 'tree': ['west', 'east'],
             'shrine': ['west'], 'watch': ['west', 'east', 'north', 'south']}[kind]
    p = ground(CELL, CELL)
    g = FOOT
    for side in doors:
        path(p, side, POOL['plots'])
    mid = CELL // 2
    # the railing round the plot, opened where a path leaves it
    for i in range(CELL):
        for x, z, side in ((0, i, 'west'), (CELL - 1, i, 'east'),
                           (i, 0, 'north'), (i, CELL - 1, 'south')):
            lane = (side in doors and mid - 1 <= (z if side in ('west', 'east') else x)
                    <= mid + 1)
            if not lane:
                p.set(x, g + 1, z, BARS, GRID)
    if kind == 'row':
        for x in (2, 4):
            for z in (2, 4):
                headstone(p, x, z, skull=(x + z) % 3 == 0)
                p.set(x, g, z, DIRT)
    elif kind == 'corner':
        for z in (2, 3, 4):
            headstone(p, 2, z)
        p.set(4, g + 1, 4, BUSH)
    elif kind == 'cross':
        p.box(1, g, 1, CELL - 2, g, CELL - 2, GRAVEL)
        p.set(mid, g + 1, mid, PALE, {'axis': 'y'})
        p.set(mid, g + 2, mid, PALE, {'axis': 'y'})
        p.set(mid, g + 3, mid, SOUL_LANTERN, {'hanging': 'false', 'waterlogged': 'false'})
    elif kind == 'open_grave':
        # dug out and never filled in. No trigger: it is a hole, and it is there whether a
        # mob walks past it first or not (section 12)
        p.box(2, g - 1, 2, 4, g, 4, AIR)
        p.box(2, g - 2, 2, 4, g - 2, 4, COBBLE)
        p.set(3, g - 1, 3, 'minecraft:spawner', None, mob_spawner('minecraft:skeleton', 1))
        headstone(p, 3, 1, skull=True)
        p.set(1, g + 1, 5, BUSH)
    elif kind == 'tomb':
        p.box(1, g + 1, 1, CELL - 2, g + 4, CELL - 2, COBBLE)
        p.box(2, g + 1, 2, CELL - 3, g + 3, CELL - 3, AIR)
        p.box(2, g + 1, 1, 4, g + 3, 1, AIR)                 # its doorway, facing the path
        p.box(1, g + 5, 1, CELL - 2, g + 5, CELL - 2, BRICK)
        p.set(mid, g + 1, CELL - 3, *chest('grave_tomb', 'north'))
        p.set(mid, g + 1, mid, CANDLE, LIT_CANDLE)
        p.set(2, g + 1, CELL - 3, BONE, {'axis': 'y'})
    elif kind == 'tree':
        p.box(mid - 1, g, mid - 1, mid + 1, g, mid + 1, PODZOL)
        for y in range(g + 1, g + 6):
            p.set(mid, y, mid, PALE, {'axis': 'y'})
        for x, z in ((mid - 1, mid), (mid + 1, mid), (mid, mid - 1), (mid, mid + 1)):
            p.set(x, g + 5, z, PALE, {'axis': 'x' if x != mid else 'z'})
            p.set(x, g + 4, z, MOSS_HANG, {'tip': 'true'})
        # a creaking heart only wakes if pale oak surrounds it, and if it never wakes it is
        # a knot of wood in a dead tree, which is all it needs to be
        p.set(mid, g + 3, mid, 'minecraft:creaking_heart',
              {'axis': 'y', 'creaking': 'disabled', 'natural': 'false'})
    elif kind == 'shrine':
        p.box(2, g + 1, 2, 4, g + 1, 4, BRICK)
        p.set(mid, g + 2, mid, CHISEL)
        p.set(mid, g + 3, mid, CANDLE, LIT_CANDLE)
        p.set(CELL - 2, g + 1, CELL - 2, *chest('grave_yard', 'west'))
        p.set(1, g + 1, 1, WEB)
    elif kind == 'watch':
        p.box(1, g, 1, CELL - 2, g, CELL - 2, GRAVEL)
        p.set(mid, g + 1, mid, 'minecraft:spawner', None, mob_spawner('minecraft:zombie', 1))
        for x, z in ((1, 1), (CELL - 2, CELL - 2)):
            headstone(p, x, z)
    return p


def plot_cap():
    """The plug at the end of a path: one panel of railing, so a row of graves never ends in
    mid-air. One block thick, so it fits at any depth (section 4)."""
    p = ground(1, CELL)
    for z in range(CELL):
        p.set(0, FOOT + 1, z, BARS, GRID)
    p.jigsaw(0, FOOT, 3, 'west_up', POOL['plot_caps'], PODZOL, name=YARD, target=YARD)
    return p


def chapel():
    """The start: what is left of the chapel. Three walls, a fallen roof, an altar, and the
    hole in the floor that is the only way into the ossuary."""
    n = CHAPEL
    p = Piece(n, FOOT + 16, n, AIR)
    g, mid = FOOT, n // 2
    p.box(0, 0, 0, n - 1, g - 1, n - 1, DIRT)                      # footing
    p.box(0, g, 0, n - 1, g, n - 1, BRICK)                         # the floor
    p.box(0, g + 1, 0, n - 1, g + 9, n - 1, COBBLE)                # walls
    p.box(1, g + 1, 1, n - 2, g + 9, n - 2, AIR)
    for x in range(n):                                             # the roof, half fallen
        for z in range(n):
            if (x * 3 + z * 5) % 7 < 4:
                p.set(x, g + 10, z, BRICK)
    for y in range(g + 1, g + 10):                                 # the corner buttresses
        for x, z in ((0, 0), (0, n - 1), (n - 1, 0), (n - 1, n - 1)):
            p.set(x, y, z, MOSSY)
    for a in (5, mid, n - 6):                                      # the windows, long broken
        for x, z in ((0, a), (n - 1, a), (a, 0), (a, n - 1)):
            p.box(x, g + 4, z, x, g + 6, z, AIR)
            p.set(x, g + 4, z, BARS, GRID)

    for side in ('west', 'east', 'north', 'south'):                # the four gates
        if side == 'west':
            p.box(0, g + 1, mid - 1, 0, g + 4, mid + 1, AIR)
            p.jigsaw(0, g, mid, 'west_up', POOL['plots'], BRICK, priority=PRIORITY,
                     name=YARD, target=YARD)
        elif side == 'east':
            p.box(n - 1, g + 1, mid - 1, n - 1, g + 4, mid + 1, AIR)
            p.jigsaw(n - 1, g, mid, 'east_up', POOL['plots'], BRICK, priority=PRIORITY,
                     name=YARD, target=YARD)
        elif side == 'north':
            p.box(mid - 1, g + 1, 0, mid + 1, g + 4, 0, AIR)
            p.jigsaw(mid, g, 0, 'north_up', POOL['plots'], BRICK, priority=PRIORITY,
                     name=YARD, target=YARD)
        else:
            p.box(mid - 1, g + 1, n - 1, mid + 1, g + 4, n - 1, AIR)
            p.jigsaw(mid, g, n - 1, 'south_up', POOL['plots'], BRICK, priority=PRIORITY,
                     name=YARD, target=YARD)

    p.box(mid - 2, g + 1, 2, mid + 2, g + 1, 3, BRICK)             # the altar
    p.set(mid, g + 2, 2, CHISEL)
    p.set(mid, g + 3, 2, CANDLE, LIT_CANDLE)
    p.set(mid - 2, g + 2, 3, CANDLE, LIT_CANDLE)
    p.set(mid + 2, g + 2, 3, CANDLE, LIT_CANDLE)
    p.set(2, g + 1, n - 3, 'minecraft:lectern',
          {'facing': 'east', 'has_book': 'false', 'powered': 'false'})
    p.set(n - 3, g + 1, n - 3, *chest('grave_chapel', 'west'))
    p.set(2, g + 1, 2, *chest('grave_chapel', 'south'))
    for x, z in ((4, 4), (n - 5, 4), (4, n - 5), (n - 5, n - 5)):
        p.set(x, g + 1, z, SOUL_LANTERN, {'hanging': 'false', 'waterlogged': 'false'})
    p.set(mid + 3, g + 1, mid + 3, 'minecraft:spawner', None,
          mob_spawner('minecraft:skeleton', 1))
    for x, z in ((1, 5), (n - 2, n - 6)):                          # webs in the corners
        p.set(x, g + 1, z, WEB)

    floor_and_hole(p)
    return p


def floor_and_hole(p):
    """The chapel's floor is solid except for the one way down."""
    g = FOOT
    x0, x1, z0, z1 = HOLE
    for x in range(CHAPEL):
        for z in range(CHAPEL):
            if x0 <= x <= x1 and z0 <= z <= z1:
                continue
            if p.grid.get((x, g, z), (AIR,))[0] in (AIR, 'minecraft:ladder'):
                p.set(x, g, z, BRICK)
    sink(p, 0, g, landing=g)
    p.jigsaw(JIG[0], 0, JIG[1], 'down_east', POOL['down'], MOSSY, joint='aligned',
             priority=PRIORITY, name=DOWN, target=DOWN)


# --------------------------------------------------------------------------- the ossuary
def shaft():
    p = Piece(CELL, SHAFT_H, CELL, ROCK)
    bedrock(p, CELL, SHAFT_H, CELL)
    shaft_wiring(p, SHAFT_H - 1)
    return p


def shaft_wiring(p, top):
    for x in range(CELL):
        for y in range(top + 1):
            for z in range(CELL):
                if p.grid.get((x, y, z), (AIR,))[0] in (AIR, 'minecraft:ladder'):
                    p.set(x, y, z, ROCK)
    sink(p, 0, top, off=SHAFT_AT, fill=ROCK)
    p.jigsaw(JIG[0] - SHAFT_AT, top, JIG[1] - SHAFT_AT, 'up_east', EMPTY, ROCK,
             joint='aligned', name=DOWN, target=DOWN)
    p.jigsaw(JIG[0] - SHAFT_AT, 0, JIG[1] - SHAFT_AT, 'down_east', POOL['crypt_first'], ROCK,
             joint='aligned', priority=PRIORITY, name=CRYPT, target=CRYPT)


def vault_room(doors):
    """A cell of the ossuary, cut into rock: one wall thick, the seven cubed of every other
    cell in this mod (section 2). The shell is the ground's own stone so that a cell
    surfacing on a slope reads as rock (section 5.2); the floor and the dressing inside are
    what make it a crypt.

    A two-block wall was the first try, and it left a three by three room with a four-tall
    doorway opening into it - there was nowhere to stand that was not under the hole."""
    p = Piece(CELL, CELL, CELL, ROCK)
    bedrock(p, CELL, CELL, CELL)
    p.box(1, 1, 1, CELL - 2, CELL - 2, CELL - 2, AIR)
    p.box(0, 0, 0, CELL - 1, 0, CELL - 1, MOSSY)                   # the floor
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


VAULT_AT = {'west': (0, 0, 3, 'west_up'), 'east': (CELL - 1, 0, 3, 'east_up'),
            'north': (3, 0, 0, 'north_up'), 'south': (3, 0, CELL - 1, 'south_up')}


def vault_door(p, side, pool, name=CRYPT, target=CRYPT, priority=0):
    x, y, z, orientation = VAULT_AT[side]
    p.jigsaw(x, y, z, orientation, pool, ROCK, priority=priority, name=name, target=target)


def crypt_hub():
    p = vault_room(['west', 'north', 'south'])
    hub_wiring(p)
    vault_door(p, 'west', POOL['crypts'])
    vault_door(p, 'north', POOL['crypts'])
    vault_door(p, 'south', POOL['captain_approach_1'], name=CRYPT, target=CAPTAIN,
               priority=PRIORITY)
    p.set(1, 1, 1, CANDLE, LIT_CANDLE)
    return p


def hub_wiring(p):
    """The hole in the ceiling and the pillar the ladder hangs on (section 24)."""
    x0, x1, z0, z1 = (v - SHAFT_AT for v in HOLE)
    jx, jz = JIG[0] - SHAFT_AT, JIG[1] - SHAFT_AT
    for x in range(CELL):
        for z in range(CELL):
            if p.grid.get((x, CELL - 1, z), (AIR,))[0] in (AIR, 'minecraft:ladder'):
                p.set(x, CELL - 1, z, ROCK)
    for y in range(1, CELL):
        p.set(jx, y, jz, BRICK)                    # the pillar the ladder hangs on
    p.box(x0, CELL - 1, z0, x1, CELL - 1, z1, AIR)
    p.jigsaw(jx, CELL - 1, jz, 'up_east', EMPTY, BRICK, joint='aligned',
             name=CRYPT, target=CRYPT)
    for y in range(1, CELL):
        p.set(RUNG[0] - SHAFT_AT, y, RUNG[1] - SHAFT_AT, *ladder())


def crypt(kind):
    doors = {'passage': ['west', 'east'], 'corner': ['west', 'south'],
             'cross': ['west', 'east', 'north', 'south'],
             'guard': ['west', 'east', 'north', 'south'],
             'niche': ['west'], 'coffin': ['west', 'east'],
             'ossuary': ['west'], 'soul': ['west', 'east']}[kind]
    p = vault_room(doors)
    for side in doors:
        vault_door(p, side, POOL['crypts'])
    mid = CELL // 2
    if kind == 'niche':
        for y in (1, 2):
            p.box(CELL - 2, y, 1, CELL - 2, y, CELL - 2, BONE, {'axis': 'z'})
        p.set(CELL - 2, 3, mid, *chest('grave_crypt', 'west'))
        p.set(1, 1, 1, CANDLE, LIT_CANDLE)
    elif kind == 'ossuary':
        for x in (1, CELL - 2):
            for y in (1, 2, 3):
                p.box(x, y, 1, x, y, CELL - 2, BONE, {'axis': 'z'})
        p.set(mid, 1, CELL - 2, *chest('grave_crypt', 'north'))
        p.set(mid, CELL - 2, mid, SOUL_LANTERN, HANGING)
    elif kind == 'coffin':
        # sealed coffins. Breaking one open is the player's own doing, which is the only
        # kind of trap this mod keeps (section 12)
        for z in (1, CELL - 2):
            p.box(1, 1, z, CELL - 2, 1, z, CHISEL)
            p.box(1, 2, z, CELL - 2, 2, z, BRICK)
        p.set(mid, 1, 1, 'minecraft:spawner', None, mob_spawner('minecraft:skeleton', 1))
        p.set(mid, 3, CELL - 2, SKULL, {'rotation': '0', 'powered': 'false'})
    elif kind == 'soul':
        p.box(1, 0, 1, CELL - 2, 0, CELL - 2, SOUL)     # slow going, and no trigger at all
        p.set(1, 1, 1, 'minecraft:soul_torch')
        p.set(CELL - 2, 1, CELL - 2, 'minecraft:soul_torch')
    elif kind == 'guard':
        p.set(mid, 1, mid, 'minecraft:spawner', None, mob_spawner('minecraft:skeleton', 1))
        p.set(1, 1, 1, WEB)
        p.set(CELL - 2, 1, CELL - 2, WEB)
    return p


def crypt_cap():
    p = Piece(1, CELL, CELL, ROCK)
    bedrock(p, 1, CELL, CELL)
    p.jigsaw(0, 0, 3, 'west_up', POOL['crypt_caps'], ROCK, name=CRYPT, target=CRYPT)
    return p


def approach(step):
    p = vault_room(['west', 'east', 'north'])
    p.jigsaw(0, 0, 3, 'west_up', POOL['crypts'], ROCK, name=CAPTAIN, target=CRYPT)
    nxt = ('captain_approach_%d' % (step + 1)) if step < MIN_BOSS_STEPS else 'captain_approach'
    vault_door(p, 'east', POOL[nxt], name=CRYPT, target=CAPTAIN, priority=PRIORITY)
    vault_door(p, 'north', POOL['crypts'])
    return p


def captain_hall():
    """His hall, and his stable. The horses are tame and they are not part of the fight, so
    they are still standing when it is over - that is the promise the concept made."""
    sx, sy, sz = BOSS
    p = Piece(sx, sy, sz, ROCK)
    bedrock(p, sx, sy, sz)
    p.box(1, 1, 1, sx - 2, sy - 2, sz - 2, AIR)
    p.box(0, 0, 0, sx - 1, 0, sz - 1, MOSSY)
    p.jigsaw(0, 0, sz // 2, 'west_up', EMPTY, ROCK, name=CAPTAIN, target=CRYPT)
    p.box(0, 1, sz // 2 - 1, 0, 4, sz // 2 + 1, AIR)

    for x0, z0 in ((4, 4), (4, sz - 6), (sx - 6, 4), (sx - 6, sz - 6)):
        for y in range(1, sy - 1):
            p.box(x0, y, z0, x0 + 1, y, z0 + 1, BONE, {'axis': 'y'})
    c = sx // 2
    p.box(c - 3, 1, 3, c + 3, 1, 7, CHISEL)                 # the dais, north of the middle
    p.box(c - 1, 2, 4, c + 1, 2, 6, BRICK)
    p.set(c, 3, 5, 'minecraft:trial_spawner', TRIAL_STATE, trial_spawner('captain'))
    for x, z in ((5, 12), (sx - 6, 12), (5, sz - 4), (sx - 6, sz - 4)):
        p.set(x, 1, z, 'minecraft:trial_spawner', TRIAL_STATE, trial_spawner('grave_guards'))
    # the stable: ordinary spawners, so the horses are not part of the fight and are still
    # standing when it is over. They come out tame; the saddle is in the boss's loot.
    for x in (c - 5, c + 5):
        p.box(x - 1, 1, sz - 6, x + 1, 1, sz - 6, 'minecraft:hay_block', {'axis': 'y'})
        p.set(x, 1, sz - 4, 'minecraft:spawner', None,
              mob_spawner('minecraft:skeleton_horse', 1, {'Tame': nbt.Byte(1)}))
    for x, z in ((c, 9), (4, c), (sx - 5, c), (c, sz - 4)):
        p.set(x, sy - 2, z, SOUL_LANTERN, HANGING)   # the ceiling is the course above
    return p


# ---------------------------------------------------------------------------------- pools
def element(location, weight):
    return ('    { "weight": %d, "element": { "element_type": "minecraft:single_pool_element",'
            '\n        "location": "%s:grave/%s", "projection": "rigid", '
            '"processors": "%s:grave_weathering" } }' % (weight, NS, location, NS))


def write_pool(name, elements, fallback):
    if not os.path.isdir(POOL_JSON):
        os.makedirs(POOL_JSON)
    text = ('{\n  "fallback": "%s",\n  "elements": [\n%s\n  ]\n}\n'
            % (fallback, ',\n'.join(elements)))
    with open(os.path.join(POOL_JSON, name + '.json'), 'w', encoding='utf-8', newline='\n') as f:
        f.write(text)


# ---------------------------------------------------------------------------------- checks
HANGS = {'minecraft:lantern', 'minecraft:soul_lantern', 'minecraft:ladder',
         'minecraft:iron_bars', 'minecraft:cobweb', 'minecraft:pale_hanging_moss',
         'minecraft:black_candle', 'minecraft:soul_torch', 'minecraft:dead_bush',
         'minecraft:skeleton_skull'}
AROUND = ((1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1))
BEHIND = {'north': (0, 0, 1), 'south': (0, 0, -1), 'east': (-1, 0, 0), 'west': (1, 0, 0)}


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
            if block.endswith('candle') or block == 'minecraft:skeleton_skull':
                if not solid((pos[0], pos[1] - 1, pos[2])):
                    problems.append('%s: the %s at %s stands on nothing'
                                    % (name, block.split(':')[-1], pos))
            if block.endswith('lantern') and props.get('hanging') == 'true':
                if not solid((pos[0], pos[1] + 1, pos[2])):
                    problems.append('%s: the lantern at %s hangs on nothing' % (name, pos))
            if block.endswith('chest'):
                if 'LootTable' not in (piece.extra.get(pos) or {}):
                    problems.append('%s: the chest at %s has no loot table' % (name, pos))
                if not solid((pos[0], pos[1] - 1, pos[2])):
                    problems.append('%s: the chest at %s stands on nothing' % (name, pos))
    return problems


def ladder_problems(pieces):
    at = {'chapel': (0, 0, 0), 'shaft': (SHAFT_AT, -SHAFT_H, SHAFT_AT),
          'crypt_hub': (SHAFT_AT, -SHAFT_H - CELL, SHAFT_AT)}
    x0, x1, z0, z1 = HOLE
    problems = []
    for y in range(at['crypt_hub'][1] + 2, FOOT + 1):
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
    problems = ladder_problems(pieces) + fitting_problems(pieces)
    for name, piece in pieces.items():
        if max(piece.size) > 48:
            problems.append('%s is %s: too big to rebuild by hand' % (name, piece.size))
        count = sum(1 for pos, (block, _) in piece.grid.items()
                    if block == 'minecraft:jigsaw'
                    and (piece.extra.get(pos) or {}).get('name') == CAPTAIN)
        if count > 1:
            problems.append('%s carries %d jigsaws named %s; the chain could be entered '
                            'through its own continuation' % (name, count, CAPTAIN))
    for line in problems:
        print('  PROBLEM  ' + line)
    if problems:
        raise SystemExit('the graveyard does not hold together')
    print('  checked: the ladder unbroken from the chapel floor to the ossuary, nothing '
          'hangs in mid-air, every chest has a table, one way into the captain')


PASSABLE = {'air', 'ladder', 'soul_lantern', 'black_candle', 'soul_torch', 'cobweb',
            'dead_bush', 'pale_hanging_moss', 'skeleton_skull', 'soul_soil', 'podzol',
            'coarse_dirt', 'gravel'}


def walk_problems():
    """Assemble what was written and walk it: out of the chapel into the graveyard, and down
    the ladder into the ossuary."""
    import gen_level_doc as doc

    pieces, pools = doc.load_family('grave'), doc.load_pools('grave')
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

    g = FOOT
    seen, queue = {(CHAPEL // 2, g + 1, 4)}, [(CHAPEL // 2, g + 1, 4)]
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

    want = {'the ossuary': (RUNG[0], -SHAFT_H - CELL + 2, RUNG[1])}
    problems = []
    for label, spot in want.items():
        if not any((spot[0], spot[1] + dy, spot[2]) in seen for dy in (-1, 0, 1)):
            problems.append('%s cannot be walked to from the chapel' % label)
    return problems


def main():
    if not os.path.isdir(DST):
        os.makedirs(DST)
    pieces = {
        'chapel': chapel(),
        'row': plot('row'), 'plot_corner': plot('corner'), 'plot_cross': plot('cross'),
        'open_grave': plot('open_grave'), 'tomb': plot('tomb'), 'tree': plot('tree'),
        'shrine': plot('shrine'), 'watch': plot('watch'), 'plot_cap': plot_cap(),
        'shaft': shaft(), 'crypt_hub': crypt_hub(),
        'passage': crypt('passage'), 'corner': crypt('corner'), 'cross': crypt('cross'),
        'guard': crypt('guard'), 'niche': crypt('niche'), 'coffin': crypt('coffin'),
        'ossuary': crypt('ossuary'), 'soul': crypt('soul'),
        'cap': crypt_cap(), 'captain_hall': captain_hall(),
    }
    for step in range(1, MIN_BOSS_STEPS + 1):
        pieces['approach_%d' % step] = approach(step)
    verify(pieces)
    for name, piece in sorted(pieces.items()):
        piece.write(os.path.join(DST, name + '.nbt'))
        print('  %-16s %s' % (name, list(piece.size)))

    write_pool('start', [element('chapel', 1)], EMPTY)
    write_pool('down', [element('shaft', 1)], EMPTY)
    write_pool('plots', [element('row', 10), element('plot_corner', 8),
                         element('plot_cross', 6), element('open_grave', 6),
                         element('tomb', 6), element('tree', 6),
                         element('shrine', 5), element('watch', 5)],
               POOL['plot_caps'])
    write_pool('plot_caps', [element('plot_cap', 1)], EMPTY)
    write_pool('crypt_first', [element('crypt_hub', 1)], EMPTY)
    write_pool('crypts', [element('passage', 10), element('corner', 9),
                          element('cross', 4), element('guard', 5),
                          element('niche', 7), element('coffin', 6),
                          element('ossuary', 6), element('soul', 4)],
               POOL['crypt_caps'])
    write_pool('crypt_caps', [element('cap', 1)], EMPTY)
    for step in range(1, MIN_BOSS_STEPS + 1):
        write_pool('captain_approach_%d' % step, [element('approach_%d' % step, 1)],
                   POOL['crypt_caps'])
    write_pool('captain_approach', [element('captain_hall', 1),
                                    element('approach_%d' % MIN_BOSS_STEPS, 1)],
               POOL['crypt_caps'])
    print('  pools -> %s' % os.path.relpath(POOL_JSON, ROOT))
    problems = walk_problems()
    for line in problems:
        print('  PROBLEM  ' + line)
    if problems:
        raise SystemExit('the graveyard is built but you cannot walk it')
    print('  walked: the chapel down into the ossuary')


if __name__ == '__main__':
    main()
