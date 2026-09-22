# -*- coding: utf-8 -*-
"""The Witch's Swamp: huts on stilts joined by boardwalks, and a brewery under the big one.

    python tools/generate_swamp.py        (or through make_pieces.py)

Writes data/sydungeon/structure/swamp/*.nbt and the pools that join them.

TWO HALVES, TWO MACHINES
Above the water it is a village: the great hut is the start and boardwalks grow out of it in
whatever direction they find room, the loosest use of the jigsaw in this mod. Below it is a
cellar, and that is the prison's machine - a maze fenced by nothing, plugged at the ends by a
one-block cap, with the boss on a chain of single-element pools so it cannot fail to appear.

STANDING IN WATER
A swamp structure starts at the first free block above the water, so the deck is three courses
up and the stilts go down into it. Everything under the deck except the posts is **left out of
the piece**: a template only places what it lists, so an omitted position keeps whatever the
world had there - water, mud, a tree root. Written as air it would carve a dry hole under
every hut. (Written as structure_void it would be worse; see CLAUDE.md section 2.)

The shaft down is the opposite case and writes its air on purpose: it has to displace the
water it passes through.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import nbt  # noqa: E402
from generate_pieces import Piece  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DST = os.path.join(ROOT, 'src', 'main', 'resources', 'data', 'sydungeon', 'structure', 'swamp')
POOL_JSON = os.path.join(ROOT, 'src', 'main', 'resources', 'data', 'sydungeon', 'worldgen',
                         'template_pool', 'swamp')

NS = 'sydungeon'
DECK = NS + ':swamp_deck'       # the boardwalk's connector
CELLAR = NS + ':swamp_cellar'   # the brewery's
DOWN = NS + ':swamp_down'       # the one way from one to the other
MOTHER = NS + ':swamp_mother'   # the boss branch, its own name so it cannot be entered backwards
EMPTY = 'minecraft:empty'
PRIORITY = 10

CELL = 7
UNDER = 3                       # courses of water between the world's surface and the deck
DECK_Y = UNDER                  # the deck of the great hut, which is the start piece
HUT = 11                        # the great hut is this tall: y 0..10
ABOVE = HUT - UNDER             # and this much of it stands above the deck
DROP = 9                        # how far every other village piece carries its posts down
GREAT = 21                      # the great hut, three cells across
SHAFT_H = 21
BOSS = (21, 14, 21)
MIN_BOSS_STEPS = 3

PLANK = 'minecraft:dark_oak_planks'
LOG = 'minecraft:dark_oak_log'
FENCE = 'minecraft:dark_oak_fence'
SLAB = 'minecraft:dark_oak_slab'
STAIR = 'minecraft:dark_oak_stairs'
TRAPDOOR = 'minecraft:dark_oak_trapdoor'
MUD = 'minecraft:mud_bricks'
PACKED = 'minecraft:packed_mud'
MOSSY = 'minecraft:mossy_cobblestone'
ROOTS = 'minecraft:muddy_mangrove_roots'
WATER = 'minecraft:water'
LANTERN = 'minecraft:lantern'
AIR = 'minecraft:air'

HANGING = {'hanging': 'true', 'waterlogged': 'false'}
RAIL = {'north': 'true', 'south': 'true', 'east': 'true', 'west': 'true',
        'waterlogged': 'false'}
POST = {'north': 'false', 'south': 'false', 'east': 'false', 'west': 'false',
        'waterlogged': 'false'}

POOL = {k: NS + ':swamp/' + k for k in
        ['start', 'decks', 'deck_caps', 'pilings', 'down', 'cellar', 'cellar_first',
         'cellar_caps',
         'mother_approach'] +
        ['mother_approach_%d' % i for i in range(1, MIN_BOSS_STEPS + 1)]}

TRIAL_STATE = {'trial_spawner_state': 'inactive', 'ominous': 'false'}
ANY_LIGHT = {'block_light_limit': {'min_inclusive': nbt.Int(0), 'max_inclusive': nbt.Int(15)}}


def trial_spawner(config):
    return {'id': 'minecraft:trial_spawner',
            'normal_config': NS + ':swamp/' + config,
            'ominous_config': NS + ':swamp/' + config,
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


def stairs(facing, half='bottom'):
    return {'facing': facing, 'half': half, 'shape': 'straight', 'waterlogged': 'false'}


# ------------------------------------------------------------------ the village, on stilts
SIDES = ('west', 'east', 'north', 'south')

# The way down, in the great hut's coordinates. The hole is three by three; the ladder hangs
# in the middle of its east wall (not in a corner of it), and a casing one block thick keeps
# the swamp out - without it the water beside the hole simply pours down into the cellar.
HOLE = (GREAT // 2, GREAT // 2)   # one column, dead centre of the piece (section 33)
RUNG = HOLE                       # the ladder is the hole


def sink(p, y0, y1):
    """The way down, cut into a piece that shares the great hut's coordinates: one column of
    ladder with a ring of planks round it, and the post the jigsaws stand in on its east.

    Three wide with a five-wide casing was the first try. The casing is what keeps the swamp
    out, and one column needs only the eight blocks round it (section 33)."""
    cx, cz = HOLE
    for x in range(cx - 1, cx + 2):
        for z in range(cz - 1, cz + 2):
            for y in range(y0, y1 + 1):
                p.set(x, y, z, PLANK)
    for y in range(y0, y1 + 1):
        p.set(cx + 1, y, cz, LOG, {'axis': 'y'})
        p.set(cx, y, cz, 'minecraft:ladder', {'facing': 'west', 'waterlogged': 'false'})


def deck_door(size, deck_y=DECK_Y):
    """Where a boardwalk's doorway and its jigsaw sit on each face of a piece `size` across."""
    mid = size // 2
    return {'west': ((0, deck_y, mid), 'west_up'), 'east': ((size - 1, deck_y, mid), 'east_up'),
            'north': ((mid, deck_y, 0), 'north_up'),
            'south': ((mid, deck_y, size - 1), 'south_up')}


def open_deck(p, side, size=CELL):
    """Three wide and four tall above the deck - the same doorway as everywhere else, just
    three courses higher because the floor here is a boardwalk over water."""
    mid = size // 2
    lo, hi = p.deck_y + 1, p.deck_y + 4
    if side == 'west':
        p.box(0, lo, mid - 1, 0, hi, mid + 1, AIR)
    elif side == 'east':
        p.box(size - 1, lo, mid - 1, size - 1, hi, mid + 1, AIR)
    elif side == 'north':
        p.box(mid - 1, lo, 0, mid + 1, hi, 0, AIR)
    else:
        p.box(mid - 1, lo, size - 1, mid + 1, hi, size - 1, AIR)


def stilts(p, size=CELL):
    """Posts from just under the deck down to the floor of the piece, and nothing else below
    it: the rest is never written, so the swamp keeps whatever it had there.

    That floor is DROP courses down for every piece but the great hut, because the swamp is
    not flat. A post three long only reaches ground that happens to sit where the start piece
    found it; one bank further and the village stands on stumps in the air. Where the ground
    comes up sooner the extra posts are underground, and nobody sees them."""
    for x, z in ((0, 0), (0, size - 1), (size - 1, 0), (size - 1, size - 1)):
        for y in range(p.deck_y):
            p.set(x, y, z, LOG, {'axis': 'y'})


def deck_piece(doors, size=CELL, roofed=False, drop=DROP):
    """A boardwalk cell: posts, deck, railing where there is no door, and air above.

    `drop` is how far the piece hangs below the water line. A child is placed by the height of
    its jigsaw alone, so hanging lower is free - but not for the start piece, which the game
    pins by its floor (JigsawPlacement moves it until minY + 1 is the surface it found). The
    great hut is the start and passes drop=0; `pilings` carries its posts down instead."""
    deck_y = drop + UNDER
    p = Piece(size, deck_y + ABOVE, size, 'minecraft:structure_void')
    p.deck_y = deck_y
    stilts(p, size)
    p.box(0, deck_y, 0, size - 1, deck_y, size - 1, PLANK)
    p.box(0, deck_y + 1, 0, size - 1, deck_y + ABOVE - 1, size - 1, AIR)
    for i in range(size):                       # railings all round, opened by the doors
        for x, z in ((0, i), (size - 1, i), (i, 0), (i, size - 1)):
            p.set(x, deck_y + 1, z, FENCE, RAIL)
    if roofed:
        p.box(0, deck_y + 1, 0, size - 1, deck_y + 5, size - 1, PLANK)
        p.box(1, deck_y + 1, 1, size - 2, deck_y + 4, size - 2, AIR)
        p.box(0, deck_y + 6, 0, size - 1, deck_y + 6, size - 1, SLAB, {'type': 'bottom',
                                                                      'waterlogged': 'false'})
    for side in doors:
        open_deck(p, side, size)
    return p


def deck_jigsaws(p, doors, pool, size=CELL, name=DECK, target=DECK, priority=0):
    at = deck_door(size, p.deck_y)
    for side in doors:
        (x, y, z), orientation = at[side]
        p.jigsaw(x, y, z, orientation, pool, PLANK, priority=priority, name=name, target=target)


def walk(doors, guard=None):
    p = deck_piece(doors)
    deck_jigsaws(p, doors, POOL['decks'])
    for x, z in ((1, 1), (CELL - 2, CELL - 2)):
        p.set(x, p.deck_y + 1, z, LANTERN, {'hanging': 'false', 'waterlogged': 'false'})
    if guard:
        p.set(CELL // 2, p.deck_y + 1, CELL // 2, 'minecraft:spawner', None,
              mob_spawner(guard, 1))
    return p


def hut(kind):
    """A one-cell hut on the boardwalk: the way in is west, and what is inside is the point."""
    p = deck_piece(['west'], roofed=True)
    deck_jigsaws(p, ['west'], POOL['decks'])
    mid, d = CELL // 2, p.deck_y
    if kind == 'loot':
        p.set(CELL - 2, d + 1, mid, *chest('swamp_hut', 'west'))
        p.set(mid, d + 1, 1, 'minecraft:cauldron', {'level': '0'})
        p.set(mid, d + 4, mid, LANTERN, HANGING)
    elif kind == 'witch':
        p.set(mid, d + 1, mid, 'minecraft:spawner', None, mob_spawner('minecraft:witch', 1))
        p.set(1, d + 1, 1, 'minecraft:cauldron', {'level': '3'})
        p.set(CELL - 2, d + 1, 1, 'minecraft:brewing_stand',
              {'has_bottle_0': 'false', 'has_bottle_1': 'false', 'has_bottle_2': 'false'})
        p.set(CELL - 2, d + 1, CELL - 2, *chest('swamp_hut', 'west'))
    else:
        p.set(mid, d + 1, mid, 'minecraft:spawner', None, mob_spawner('minecraft:slime', 2))
        p.box(1, d + 1, CELL - 2, CELL - 2, d + 1, CELL - 2, ROOTS)
        p.set(1, d + 2, 1, *chest('swamp_hut', 'south'))
    return p


def deck_cap():
    """The plug at the end of a boardwalk: one course of railing, so a run that meets the edge
    of the world stops at a handrail instead of in mid air."""
    p = Piece(1, HUT, CELL, 'minecraft:structure_void')   # a jigsaw's own height places it,
    p.deck_y = DECK_Y                                     # so the plug can stay a short piece
    for z in range(CELL):
        p.set(0, DECK_Y, z, PLANK)
        p.set(0, DECK_Y + 1, z, FENCE, RAIL)
    p.jigsaw(0, DECK_Y, CELL // 2, 'west_up', POOL['deck_caps'], PLANK, name=DECK, target=DECK)
    return p


def great_hut():
    """The start: a hall on stilts with the brewing bench, and the hole down to the cellar.

    Three cells across so the boardwalks leave from the middle of each side, and the only
    jigsaw that is not a boardwalk is the one pointing down."""
    n = GREAT
    p = deck_piece(SIDES, size=n, roofed=True, drop=0)
    deck_jigsaws(p, SIDES, POOL['decks'], size=n)
    mid = n // 2

    for x, z in ((0, 0), (0, n - 1), (n - 1, 0), (n - 1, n - 1)):   # corner posts to the roof
        for y in range(DECK_Y + 1, DECK_Y + 6):
            p.set(x, y, z, LOG, {'axis': 'y'})
    p.box(4, DECK_Y + 1, 4, n - 5, DECK_Y + 1, 4, MUD)              # a brewing bench
    for i in (6, 10, 14):
        p.set(i, DECK_Y + 2, 4, 'minecraft:brewing_stand',
              {'has_bottle_0': 'false', 'has_bottle_1': 'false', 'has_bottle_2': 'false'})
    p.set(5, DECK_Y + 1, 5, 'minecraft:cauldron', {'level': '3'})
    p.set(n - 6, DECK_Y + 1, 5, 'minecraft:cauldron', {'level': '3'})
    p.set(4, DECK_Y + 1, n - 5, *chest('swamp_hut', 'north'))
    p.set(n - 5, DECK_Y + 1, n - 5, *chest('swamp_hut', 'north'))
    for x, z in ((6, 6), (n - 7, 6), (6, n - 7), (n - 7, n - 7)):
        p.set(x, DECK_Y + 4, z, LANTERN, HANGING)

    # the way down: a hole through the deck, cased against the water, and a ladder. The
    # jigsaw sits in the post that holds the casing's east wall up - a jigsaw is a block, it
    # becomes its final_state when the piece is placed, and one standing in the hole reads as
    # a stray block to climb round.
    sink(p, 0, DECK_Y)                                               # the deck course too
    p.set(RUNG[0], DECK_Y, RUNG[1], 'minecraft:ladder', {'facing': 'west',
                                                         'waterlogged': 'false'})
    for x, z in ((mid - 2, mid), (mid + 2, mid)):
        p.set(x, DECK_Y + 1, z, FENCE, RAIL)
    p.jigsaw(mid + 1, 0, mid, 'down_east', POOL['pilings'], LOG, joint='aligned',
             priority=PRIORITY, name=DOWN, target=DOWN)
    return p


def pilings():
    """What the great hut stands on. The hut is the start piece and the game pins a start
    piece by its floor, so its own posts can never reach below the surface it landed on,
    however long they are drawn. This hangs underneath instead: the four corner posts and the
    hatch's post carried DROP further down, with the ladder and its column of air continuing
    so the climb is unbroken. The shaft to the cellar hangs off the bottom of it."""
    n, mid = GREAT, GREAT // 2
    p = Piece(n, DROP, n, 'minecraft:structure_void')
    for x, z in ((0, 0), (0, n - 1), (n - 1, 0), (n - 1, n - 1)):
        for y in range(DROP):
            p.set(x, y, z, LOG, {'axis': 'y'})
    sink(p, 0, DROP - 1)
    # both jigsaws stand in the post east of the climb, which is where every other piece in
    # the chain puts them. They were left at the old three-wide shaft's coordinates once and
    # the whole stack below hung a block out of line: solid plank where the ladder should
    # have been, and the climb picking up again one over (section 33)
    jx, jz = HOLE[0] + 1, HOLE[1]
    p.jigsaw(jx, DROP - 1, jz, 'up_east', EMPTY, LOG, joint='aligned',
             name=DOWN, target=DOWN)
    p.jigsaw(jx, 0, jz, 'down_east', POOL['down'], LOG, joint='aligned',
             priority=PRIORITY, name=DOWN, target=DOWN)
    return p


# ------------------------------------------------------------------------------ the cellar
def cellar_room(doors, fill=MUD):
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


CELLAR_AT = {'west': (0, 0, 3, 'west_up'), 'east': (CELL - 1, 0, 3, 'east_up'),
             'north': (3, 0, 0, 'north_up'), 'south': (3, 0, CELL - 1, 'south_up')}


def cellar_door(p, side, pool, name=CELLAR, target=CELLAR, priority=0):
    x, y, z, orientation = CELLAR_AT[side]
    p.jigsaw(x, y, z, orientation, pool, MUD, priority=priority, name=name, target=target)


def shaft():
    """From under the great hut, through the water, into the mud. Its air is written on
    purpose: it has to push the swamp out of the way."""
    p = Piece(CELL, SHAFT_H, CELL, MUD)
    cx, cz = HOLE[0] - CELL, HOLE[1] - CELL
    for y in range(SHAFT_H):
        p.set(cx, y, cz, 'minecraft:ladder', {'facing': 'west', 'waterlogged': 'false'})
    # both in the wall, clear of the ladder, for the same reason
    p.jigsaw(cx + 1, SHAFT_H - 1, cz, 'up_east', EMPTY, MUD, joint='aligned',
             name=DOWN, target=DOWN)
    p.jigsaw(cx + 1, 0, cz, 'down_east', POOL['cellar_first'], MUD, joint='aligned',
             priority=PRIORITY, name=CELLAR, target=CELLAR)
    return p


def cellar_hub():
    """Where the ladder lands. Three ways into the brewery and one, on its own connector and
    placed first, to the mother."""
    p = cellar_room(['west', 'east', 'south'])
    # the climb comes down the middle of the room on a post of mud brick, and the ceiling is
    # left solid round it: one column, so there is no hole to fall down (section 33)
    cx, cz = HOLE[0] - CELL, HOLE[1] - CELL
    for y in range(1, CELL):
        p.set(cx + 1, y, cz, MUD)
        p.set(cx, y, cz, 'minecraft:ladder', {'facing': 'west', 'waterlogged': 'false'})
    p.jigsaw(cx + 1, CELL - 1, cz, 'up_east', EMPTY, MUD, joint='aligned',
             name=CELLAR, target=CELLAR)
    cellar_door(p, 'west', POOL['cellar'])
    cellar_door(p, 'east', POOL['cellar'])
    cellar_door(p, 'south', POOL['mother_approach_1'], name=CELLAR, target=MOTHER,
                priority=PRIORITY)
    p.set(2, 4, 5, LANTERN, HANGING)      # clear of the hole the ladder comes down
    return p


def cellar(kind):
    doors = {'passage': ['west', 'east'], 'corner': ['west', 'south'],
             'cross': ['west', 'east', 'north', 'south'],
             'brew': ['west'], 'drowned': ['west', 'east'], 'still': ['west'],
             'room': ['west'], 'passage_guard': ['west', 'east'],
             'cross_guard': ['west', 'east', 'north', 'south']}[kind]
    p = cellar_room(doors)
    for side in doors:
        cellar_door(p, side, POOL['cellar'])
    mid = CELL // 2
    if kind == 'brew':
        p.box(1, 1, CELL - 2, CELL - 2, 1, CELL - 2, MOSSY)
        p.set(mid, 2, CELL - 2, 'minecraft:brewing_stand',
              {'has_bottle_0': 'false', 'has_bottle_1': 'false', 'has_bottle_2': 'false'})
        p.set(1, 1, 1, 'minecraft:cauldron', {'level': '3'})
        p.set(CELL - 2, 2, CELL - 2, *chest('swamp_brewery', 'north'))
        p.set(mid, 4, mid, LANTERN, HANGING)
    elif kind == 'drowned':
        p.box(1, 1, 1, CELL - 2, 1, CELL - 2, WATER, {'level': '0'})
        p.set(mid, 2, mid, 'minecraft:spawner', None, mob_spawner('minecraft:drowned', 1))
        p.box(1, 1, 1, 1, 1, 1, ROOTS)
    elif kind == 'still':
        p.set(mid, 1, CELL - 2, 'minecraft:cauldron', {'level': '3'})
        p.set(mid, 1, 1, 'minecraft:spawner', None, mob_spawner('minecraft:witch', 1))
        p.set(CELL - 2, 1, 1, *chest('swamp_brewery', 'west'))
    elif kind == 'room':
        # a room with only one way in and out is a reward, not a corridor: it gets the chest
        p.set(CELL - 2, 1, mid, *chest('swamp_brewery', 'west'))
        p.box(1, 1, 1, 1, 1, CELL - 2, MOSSY)
        p.set(1, 2, 1, 'minecraft:cauldron', {'level': '0'})
        p.set(mid, 4, mid, LANTERN, HANGING)
    elif kind.endswith('_guard'):
        # and a corridor is where the fighting is
        entity = 'minecraft:witch' if kind == 'passage_guard' else 'minecraft:slime'
        p.set(mid, 1, mid, 'minecraft:spawner', None, mob_spawner(entity, 1))
    return p


def cellar_cap():
    p = Piece(1, CELL, CELL, MUD)
    p.jigsaw(0, 0, 3, 'west_up', POOL['cellar_caps'], MUD, name=CELLAR, target=CELLAR)
    return p


def approach(step):
    """One link of the chain to the mother. The way in is the only jigsaw called `mother`, so
    the chain cannot be entered through its own continuation and run backwards (section 13)."""
    p = cellar_room(['west', 'east', 'north'])
    p.jigsaw(0, 0, 3, 'west_up', POOL['cellar'], MUD, name=MOTHER, target=CELLAR)
    nxt = ('mother_approach_%d' % (step + 1)) if step < MIN_BOSS_STEPS else 'mother_approach'
    cellar_door(p, 'east', POOL[nxt], name=CELLAR, target=MOTHER, priority=PRIORITY)
    cellar_door(p, 'north', POOL['cellar'])
    return p


def mother():
    """Her hall: a low, wide cellar with a pool in the middle of it, five trial spawners and
    no other way out."""
    sx, sy, sz = BOSS
    p = Piece(sx, sy, sz, MUD)
    p.box(1, 1, 1, sx - 2, sy - 2, sz - 2, AIR)
    p.box(0, 0, 0, sx - 1, 0, sz - 1, PACKED)
    p.jigsaw(0, 0, sz // 2, 'west_up', EMPTY, MUD, name=MOTHER, target=CELLAR)
    p.box(0, 1, sz // 2 - 1, 0, 4, sz // 2 + 1, AIR)

    for x0, z0 in ((3, 3), (3, sz - 5), (sx - 5, 3), (sx - 5, sz - 5)):    # root pillars
        for y in range(1, sy - 1):
            p.box(x0, y, z0, x0 + 1, y, z0 + 1, ROOTS)
    c = sx // 2
    p.box(c - 4, 0, c - 4, c + 4, 0, c + 4, WATER, {'level': '0'})         # the pool
    p.box(c - 2, 0, c - 2, c + 2, 0, c + 2, PACKED)                        # her island
    p.box(c - 1, 1, c - 1, c + 1, 1, c + 1, MOSSY)
    p.set(c, 2, c, 'minecraft:trial_spawner', TRIAL_STATE, trial_spawner('mother'))
    for x, z in ((5, 5), (5, sz - 6), (sx - 6, 5), (sx - 6, sz - 6)):
        p.set(x, 1, z, 'minecraft:trial_spawner', TRIAL_STATE, trial_spawner('swamp_guards'))
    for x, z in ((c, 4), (4, c), (sx - 5, c), (c, sz - 5)):
        p.set(x, sy - 3, z, LANTERN, HANGING)
    return p


# ---------------------------------------------------------------------------------- pools
def element(location, weight):
    return ('    { "weight": %d, "element": { "element_type": "minecraft:single_pool_element",'
            '\n        "location": "%s:swamp/%s", "projection": "rigid", '
            '"processors": "%s:swamp_weathering" } }' % (weight, NS, location, NS))


def write_pool(name, elements, fallback):
    if not os.path.isdir(POOL_JSON):
        os.makedirs(POOL_JSON)
    text = ('{\n  "fallback": "%s",\n  "elements": [\n%s\n  ]\n}\n'
            % (fallback, ',\n'.join(elements)))
    with open(os.path.join(POOL_JSON, name + '.json'), 'w', encoding='utf-8', newline='\n') as f:
        f.write(text)


def ladder_problems(pieces):
    """Stack the way down as the game stacks it and climb it. Each piece hangs off the one
    above by its own jigsaw, so the four of them have to agree on a single column of blocks -
    and a jigsaw is a block, so one standing in that column is a rung missing. Four of them
    were, once."""
    mid = GREAT // 2
    at = {'great_hut': (0, 0, 0), 'pilings': (0, -DROP, 0),
          'shaft': (CELL, -DROP - SHAFT_H, CELL),
          'cellar_hub': (CELL, -DROP - SHAFT_H - CELL, CELL)}
    bottom = at['cellar_hub'][1] + 1                        # the cellar floor is course 0
    problems = []
    cx, cz = RUNG
    cased = at['cellar_hub'][1] + CELL - 1
    for y in range(bottom, DECK_Y + 1):
        for dx in (-1, 0, 1):
            for dz in (-1, 0, 1):
                if (dx, dz) != (0, 0) and y < cased:
                    continue               # inside the hub the ring is the room itself
                x, z = cx + dx, cz + dz
                for name, (ox, oy, oz) in at.items():
                    piece = pieces[name]
                    local = (x - ox, y - oy, z - oz)
                    if local in piece.grid:
                        block = piece.grid[local][0]
                        break
                else:
                    problems.append('nothing covers %s on the way down' % ((x, y, z),))
                    continue
                if (dx, dz) == (0, 0):
                    if block != 'minecraft:ladder':
                        problems.append('%s has %s at %s, where the climb needs a ladder'
                                        % (name, block.split(':')[-1], (x, y, z)))
                elif block in (AIR, 'minecraft:water', 'minecraft:ladder'):
                    problems.append('%s leaves %s at %s: the ring round the shaft has to be '
                                    'solid the whole way down, and here it is what keeps the '
                                    'swamp out (section 33)'
                                    % (name, block.split(':')[-1], (x, y, z)))
    return problems


def verify(pieces):
    problems = []
    for name, piece in pieces.items():
        counts = {}
        sx, sy, sz = piece.size
        for pos, (block, props) in piece.grid.items():
            if block != 'minecraft:jigsaw':
                continue
            meta = piece.extra.get(pos, {})
            counts[meta.get('name')] = counts.get(meta.get('name'), 0) + 1
        if counts.get(MOTHER, 0) > 1:
            problems.append('%s carries %d jigsaws named %s; the chain could be entered '
                            'through its own continuation' % (name, counts[MOTHER], MOTHER))
        if name.startswith(('walk', 'hut', 'great')):
            deck_y = piece.deck_y
            want = UNDER if name == 'great_hut' else UNDER + DROP
            if deck_y != want:
                problems.append('%s holds its deck %d up; the great hut is pinned at %d and '
                                'every other piece hangs %d lower so its posts reach the '
                                'ground' % (name, deck_y, UNDER, DROP))
            if piece.size[1] != deck_y + ABOVE:
                problems.append('%s is %d tall; a village piece is its deck plus %d'
                                % (name, piece.size[1], ABOVE))
        if name.startswith(('walk', 'hut', 'great', 'pilings')):
            # under the deck only the posts, and the great hut's way down, may be written:
            # everything else has to stay whatever the swamp had there
            allowed = ('minecraft:structure_void', 'minecraft:dark_oak_log', AIR,
                       'minecraft:jigsaw', 'minecraft:ladder')
            floor = getattr(piece, 'deck_y', piece.size[1])
            cx, cz = HOLE                         # the casing round the way down may be built
            below = [p for p in piece.grid
                     if p[1] < floor and piece.grid[p][0] not in allowed
                     and not (piece.grid[p][0] == PLANK and cx - 1 <= p[0] <= cx + 1
                              and cz - 1 <= p[2] <= cz + 1)]
            if below:
                problems.append('%s writes %s under its deck; the swamp should keep what it '
                                'had there' % (name, piece.grid[below[0]][0]))
    problems += ladder_problems(pieces)
    for line in problems:
        print('  PROBLEM  ' + line)
    if problems:
        raise SystemExit('the swamp does not hold together')
    print('  checked: the great hut sits %d over the water and every other piece hangs %d '
          'lower, nothing but posts under any deck, the ladder unbroken from the deck to the '
          'cellar floor, one way into the mother' % (UNDER, DROP))


def main():
    if not os.path.isdir(DST):
        os.makedirs(DST)
    pieces = {
        'great_hut': great_hut(),
        'walk': walk(['west', 'east']),
        'walk_guard': walk(['west', 'east'], guard='minecraft:witch'),
        'walk_corner': walk(['west', 'south']),
        'walk_cross': walk(['west', 'east', 'north', 'south']),
        'hut_loot': hut('loot'), 'hut_witch': hut('witch'), 'hut_slime': hut('slime'),
        'deck_cap': deck_cap(), 'pilings': pilings(),
        'shaft': shaft(), 'cellar_hub': cellar_hub(),
        'cellar_passage': cellar('passage'), 'cellar_corner': cellar('corner'),
        'cellar_cross': cellar('cross'), 'cellar_brew': cellar('brew'),
        'cellar_drowned': cellar('drowned'), 'cellar_still': cellar('still'),
        'cellar_room': cellar('room'), 'cellar_passage_guard': cellar('passage_guard'),
        'cellar_cross_guard': cellar('cross_guard'),
        'cellar_cap': cellar_cap(), 'mother': mother(),
    }
    for step in range(1, MIN_BOSS_STEPS + 1):
        pieces['approach_%d' % step] = approach(step)
    verify(pieces)
    for name, piece in sorted(pieces.items()):
        piece.write(os.path.join(DST, name + '.nbt'))
        print('  %-16s %s' % (name, list(piece.size)))

    write_pool('start', [element('great_hut', 1)], EMPTY)
    write_pool('pilings', [element('pilings', 1)], EMPTY)
    write_pool('down', [element('shaft', 1)], EMPTY)
    write_pool('decks', [element('walk', 9), element('walk_guard', 5),
                         element('walk_corner', 8), element('walk_cross', 6),
                         element('hut_loot', 8), element('hut_witch', 5),
                         element('hut_slime', 4)],
               POOL['deck_caps'])
    write_pool('deck_caps', [element('deck_cap', 1)], EMPTY)
    write_pool('cellar', [element('cellar_passage', 9), element('cellar_passage_guard', 5),
                          element('cellar_corner', 9), element('cellar_cross', 4),
                          element('cellar_cross_guard', 3), element('cellar_room', 8),
                          element('cellar_brew', 6), element('cellar_still', 5),
                          element('cellar_drowned', 5)],
               POOL['cellar_caps'])
    write_pool('cellar_first', [element('cellar_hub', 1)], EMPTY)
    write_pool('cellar_caps', [element('cellar_cap', 1)], EMPTY)
    for step in range(1, MIN_BOSS_STEPS + 1):
        write_pool('mother_approach_%d' % step, [element('approach_%d' % step, 1)],
                   POOL['cellar_caps'])
    write_pool('mother_approach', [element('mother', 1), element('approach_%d' % MIN_BOSS_STEPS, 1)],
               POOL['cellar_caps'])
    print('  pools -> %s' % os.path.relpath(POOL_JSON, ROOT))


if __name__ == '__main__':
    main()
