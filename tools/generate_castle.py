# -*- coding: utf-8 -*-
"""The Wizard's Castle: keep, tower, library, and the sanctum buried under it.

    python tools/generate_castle.py        (or through make_pieces.py)

Writes data/sydungeon/structure/castle/*.nbt and the pools that join them.

SHAPE, THE SAME WAY THE PYRAMID DOES IT
`keep` is the building's shell - walls, floors, roof, battlements - and its bounding box is
the fence for everything inside it (CLAUDE.md section 10):

    keep (39x21x39)  --inside--> core_l1 (35x7x35)  --inside--> the ground floor maze
                     --inside--> core_l2 (35x7x35)  --inside--> library, alchemy, maze
                     --inside--> tower_1, and the tower chain carries on above it
                     --below---> sanctum (21x21x21)

WHAT IS GUARANTEED TO EXIST
Everything the castle is for. Each of these is a single-element pool reached by a chain of
single-element pools, so it is placed exactly once and always:

    gate -> spine_l1 -> hall_l1 -> (ladder down) sanctum: the archmage and a nether portal
    hall_l2 -> library: a real enchanting table with fifteen bookshelves round it
    hall_l2 -> alchemy: a brewing stand
    tower_1 -> tower_2 -> tower_3 -> observatory

The three halls sit on the same cell of every floor, so one ladder column runs from the
sanctum's floor to the top of the tower. That column is carved into each piece from one table
of coordinates, because pieces joined by a single anchor jigsaw always land in the same
relative position.

The ladder hangs on a buttress on each piece's north wall, which is why no hall has a north
door: a doorway there would be a hole behind the ladder.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
import nbt  # noqa: E402
from generate_pieces import Piece  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DST = os.path.join(ROOT, 'src', 'main', 'resources', 'data', 'sydungeon', 'structure', 'castle')
POOL_JSON = os.path.join(ROOT, 'src', 'main', 'resources', 'data', 'sydungeon', 'worldgen',
                         'template_pool', 'castle')

NS = 'sydungeon'
DOOR = NS + ':cas_door'        # the maze's connector
WAY = NS + ':cas_way'          # the guaranteed route: gate -> spine -> hall -> rooms
ANCHOR = NS + ':cas_anchor'    # keep -> core / tower / sanctum
EMPTY = 'minecraft:empty'

CELL = 7
KEEP = 39                      # the keep's footprint
WALL = 2                       # how thick its outer wall is
GRID = 5                       # 5x5 interior cells
PRIORITY = 20

STONE = 'minecraft:stone_bricks'
MOSSY = 'minecraft:mossy_stone_bricks'
CRACKED = 'minecraft:cracked_stone_bricks'
CHISELED = 'minecraft:chiseled_stone_bricks'
DEEP = 'minecraft:deepslate_bricks'
POLISHED = 'minecraft:polished_deepslate'
DARK = 'minecraft:dark_oak_planks'
GLASS = 'minecraft:glass_pane'
AIR = 'minecraft:air'
VOID = 'minecraft:structure_void'

AT = {
    'keep': (0, 0, 0),
    'core_l1': (WALL, 0, WALL),
    'core_l2': (WALL, 7, WALL),
    'sanctum': (9, -21, 9),
    'library': (2, 7, 9),
    'alchemy': (16, 7, 23),
    'tower_1': (16, 14, 16),
    'tower_2': (16, 21, 16),
    'tower_3': (16, 28, 16),
    'observatory': (16, 35, 16),
}
SIZE = {
    'keep': (KEEP, 21, KEEP),
    'core_l1': (GRID * CELL, 7, GRID * CELL),
    'core_l2': (GRID * CELL, 7, GRID * CELL),
    'sanctum': (21, 21, 21),
    'library': (14, 7, 14),
    'alchemy': (CELL, CELL, CELL),
    'tower_1': (CELL, CELL, CELL),
    'tower_2': (CELL, CELL, CELL),
    'tower_3': (CELL, CELL, CELL),
    'observatory': (CELL, CELL, CELL),
}

HALL_CELL = (2, 2)             # the halls, on every floor, in castle coordinates
HALL_AT = (WALL + HALL_CELL[0] * CELL, WALL + HALL_CELL[1] * CELL)   # (16, 16)
SHAFT = (18, 20, 18, 20)       # the well through every floor: x0, x1, z0, z1
LADDER_X, LADDER_Z = 19, 18    # and the ladder in it, hanging on the buttress at z-1

POOL = {k: NS + ':castle/' + k for k in (
    'passages', 'caps', 'core_l1', 'core_l2', 'sanctum', 'library', 'alchemy',
    'spine_l1', 'hall_l1', 'hall_l2', 'tower_1', 'tower_2', 'tower_3', 'observatory')}

TRIAL_COOLDOWN = 2_000_000_000
TRIAL_STATE = {'trial_spawner_state': 'inactive', 'ominous': 'false'}
ANY_LIGHT = {'block_light_limit': {'min_inclusive': nbt.Int(0), 'max_inclusive': nbt.Int(15)}}


def trial_spawner(config):
    return {'id': 'minecraft:trial_spawner',
            'normal_config': NS + ':castle/' + config,
            'ominous_config': NS + ':castle/' + config,
            'target_cooldown_length': nbt.Int(TRIAL_COOLDOWN),
            'required_player_range': nbt.Int(14)}


def mob_spawner(entity, count=3):
    return {'id': 'minecraft:mob_spawner',
            'SpawnData': {'entity': {'id': entity}, 'custom_spawn_rules': ANY_LIGHT},
            'Delay': nbt.Short(20), 'MinSpawnDelay': nbt.Short(240),
            'MaxSpawnDelay': nbt.Short(900), 'SpawnCount': nbt.Short(count),
            'MaxNearbyEntities': nbt.Short(5), 'RequiredPlayerRange': nbt.Short(14),
            'SpawnRange': nbt.Short(4)}


def chest(table, facing='north'):
    return ('minecraft:chest', {'facing': facing, 'type': 'single', 'waterlogged': 'false'},
            {'id': 'minecraft:chest', 'LootTable': NS + ':chests/' + table})


# --------------------------------------------------------------------------- joins

def anchor_into(p, parent, child):
    """The jigsaw on `parent` that places `child` to its east. Horizontal, so only the
    identity rotation leaves the child's west-facing anchor pointing back."""
    ox, oy, oz = AT[parent]
    cx, cy, cz = AT[child]
    az = SIZE[child][2] // 2
    p.jigsaw(cx - 1 - ox, cy - oy, cz + az - oz, 'east_up', POOL[child], STONE,
             priority=PRIORITY, name=WAY, target=ANCHOR)


def stack_onto(p, parent, child):
    ox, oy, oz = AT[parent]
    cx, cy, cz = AT[child]
    p.jigsaw(cx - ox, cy - 1 - oy, cz - oz, 'up_east', POOL[child], STONE,
             joint='aligned', priority=PRIORITY, name=WAY, target=ANCHOR)


def drop_to(p, parent, child):
    ox, oy, oz = AT[parent]
    cx, cy, cz = AT[child]
    sy = SIZE[child][1]
    p.jigsaw(cx - ox, cy + sy - oy, cz - oz, 'down_east', POOL[child], STONE,
             joint='aligned', priority=PRIORITY, name=WAY, target=ANCHOR)


def side_anchor(p, child):
    p.jigsaw(0, 0, SIZE[child][2] // 2, 'west_up', EMPTY, STONE, name=ANCHOR, target=ANCHOR)


def under_anchor(p):
    p.jigsaw(0, 0, 0, 'down_east', EMPTY, STONE, joint='aligned', name=ANCHOR, target=ANCHOR)


def over_anchor(p, child):
    p.jigsaw(0, SIZE[child][1] - 1, 0, 'up_east', EMPTY, STONE, joint='aligned',
             name=ANCHOR, target=ANCHOR)


DOOR_AT = {'west': (0, 0, 3, 'west_up'), 'east': (6, 0, 3, 'east_up'),
           'north': (3, 0, 0, 'north_up'), 'south': (3, 0, 6, 'south_up')}


def door(p, side, pool, name=DOOR, target=DOOR, priority=0):
    x, y, z, orientation = DOOR_AT[side]
    p.jigsaw(x, y, z, orientation, pool, STONE, priority=priority, name=name, target=target)


# --------------------------------------------------------------------------- the keep

GATE_Z = (18, 20)              # the gate, through the middle of the east wall


def keep():
    """Walls, floors, roof and battlements. The inside of each storey is left solid; the core
    pieces claim it and the rooms carve into it, so whatever nothing reaches stays as the
    castle's own thick masonry."""
    n = KEEP
    p = Piece(n, 21, n, STONE)
    for y in range(21):
        for x in range(n):
            for z in range(n):
                if y in (6, 13):                      # the floor slabs between storeys
                    p.set(x, y, z, DEEP if (x + z) % 2 else POLISHED)
                elif y % 7 == 5:
                    p.set(x, y, z, CHISELED)
    # the battlement storey is open except for its parapet and the tower's footprint
    p.box(WALL, 14, WALL, n - 1 - WALL, 20, n - 1 - WALL, AIR)
    p.box(0, 17, 0, n - 1, 20, n - 1, AIR)
    for i in range(n):
        for x, z in ((0, i), (n - 1, i), (i, 0), (i, n - 1)):
            p.set(x, 14, z, DEEP)
            p.set(x, 15, z, STONE)
            if i % 2 == 0:
                p.set(x, 16, z, STONE)
    p.box(14, 14, 14, 24, 16, 24, STONE)              # the tower's base on the roof
    # windows down the two storeys
    for y in (3, 10):
        for i in range(6, n - 6, 6):
            for x, z in ((0, i), (n - 1, i), (i, 0), (i, n - 1)):
                for depth in range(WALL):
                    wx = x + depth if x == 0 else (x - depth if x == n - 1 else x)
                    wz = z + depth if z == 0 else (z - depth if z == n - 1 else z)
                    for dy in (0, 1):
                        p.set(wx, y + dy, wz, GLASS,
                              {'north': 'false', 'south': 'false', 'east': 'false',
                               'west': 'false', 'waterlogged': 'false'})
    # the gate, through the east wall
    p.box(n - WALL, 1, GATE_Z[0], n - 1, 4, GATE_Z[1], AIR)
    p.set(n - 1, 5, GATE_Z[0] - 1, CHISELED)
    p.set(n - 1, 5, GATE_Z[1] + 1, CHISELED)

    anchor_into(p, 'keep', 'core_l1')
    anchor_into(p, 'keep', 'core_l2')
    stack_onto(p, 'keep', 'tower_1')
    drop_to(p, 'keep', 'sanctum')
    return p


# --------------------------------------------------------------------------- the storeys

def core(name, extra=None):
    """One storey's interior: a solid block five cells a side that the rooms carve into."""
    sx, sy, sz = SIZE[name]
    p = Piece(sx, sy, sz, STONE)
    side_anchor(p, name)
    if extra:
        extra(p)
    return p


def core_l1():
    def gate_corridor(p):
        # the way in runs from the gate through the outermost cell, then a jigsaw hands over
        # to the spine, so the corridor can have rooms off it
        x0 = (GRID - 1) * CELL
        p.box(x0, 1, 16, x0 + CELL - 1, 4, 18, AIR)
        p.jigsaw(x0, 0, 17, 'west_up', POOL['spine_l1'], STONE,
                 priority=PRIORITY, name=WAY, target=WAY)
    return core('core_l1', gate_corridor)


def core_l2():
    def place_hall(p):
        # nothing to carve up here; this jigsaw only fixes where the upper hall lands
        p.jigsaw((HALL_CELL[0] + 1) * CELL, 0, HALL_CELL[1] * CELL + 3, 'west_up',
                 POOL['hall_l2'], STONE, priority=PRIORITY, name=WAY, target=WAY)
    return core('core_l2', place_hall)


# --------------------------------------------------------------------------- rooms

def room(doors, size=CELL, floor=DARK):
    p = Piece(size, CELL, size, STONE)
    p.box(1, 1, 1, size - 2, 5, size - 2, AIR)
    p.box(0, 0, 0, size - 1, 0, size - 1, floor)
    for d in doors:
        x, _, z, _ = DOOR_AT[d]
        if d == 'east':
            x = size - 1
        if d == 'south':
            z = size - 1
        if d in ('west', 'east'):
            p.box(x, 1, size // 2 - 1, x, 4, size // 2 + 1, AIR)
        else:
            p.box(size // 2 - 1, 1, z, size // 2 + 1, 4, z, AIR)
    return p


def passage():
    p = room(['west', 'east'])
    door(p, 'west', POOL['passages'])
    door(p, 'east', POOL['passages'])
    return p


def corner():
    p = room(['west', 'south'])
    door(p, 'west', POOL['passages'])
    door(p, 'south', POOL['passages'])
    return p


def cross():
    p = room(['west', 'east', 'north', 'south'])
    for side in ('west', 'east', 'north', 'south'):
        door(p, side, POOL['passages'])
    return p


def study():
    """A dead end with a desk: a lectern, candles and a chest of the wizard's papers."""
    p = room(['west'])
    door(p, 'west', POOL['passages'])
    p.box(4, 1, 1, 5, 1, 5, 'minecraft:bookshelf')
    p.set(4, 2, 3, *chest('castle_study', 'west'))
    p.set(4, 2, 2, 'minecraft:lectern', {'facing': 'west', 'has_book': 'false', 'powered': 'false'})
    p.set(3, 4, 3, 'minecraft:lantern', {'hanging': 'true', 'waterlogged': 'false'})
    return p


def vex_cage():
    """The servants' room. Vexes fly through walls, which is the point of putting them in a
    castle you have to walk through."""
    p = room(['west', 'east'])
    door(p, 'west', POOL['passages'])
    door(p, 'east', POOL['passages'])
    p.box(2, 1, 2, 4, 4, 2, 'minecraft:iron_bars',
          {'north': 'false', 'south': 'false', 'east': 'true', 'west': 'true', 'waterlogged': 'false'})
    p.set(3, 1, 1, 'minecraft:spawner', None, mob_spawner('minecraft:vex', 2))
    return p


def lab():
    """What the wizard did to the villagers he took in."""
    p = room(['west', 'east'])
    door(p, 'west', POOL['passages'])
    door(p, 'east', POOL['passages'])
    p.set(1, 1, 5, 'minecraft:cauldron', {'level': '0'})
    p.set(5, 1, 5, 'minecraft:cauldron', {'level': '0'})
    p.set(3, 1, 5, 'minecraft:spawner', None, mob_spawner('minecraft:zombie_villager', 2))
    p.set(3, 4, 3, 'minecraft:soul_lantern', {'hanging': 'true', 'waterlogged': 'false'})
    return p


def cap():
    p = Piece(1, CELL, CELL, STONE)
    p.jigsaw(0, 0, 3, 'west_up', POOL['caps'], STONE, name=DOOR, target=DOOR)
    return p


# --------------------------------------------------------------------------- the route

def buttress_and_ladder(p, origin, top, up=True, down=True):
    """The ladder column every piece on the route shares. `origin` is the piece's position in
    castle coordinates; the buttress is the row of blocks just north of the ladder, and it is
    why none of these pieces has a north door."""
    ox, oy, oz = origin
    x0, x1, z0, z1 = SHAFT
    p.box(x0 - ox, 1, LADDER_Z - 1 - oz, x1 - ox, top - 1, LADDER_Z - 1 - oz, CHISELED)
    if up:
        p.box(x0 - ox, top, z0 - oz, x1 - ox, top, z1 - oz, AIR)
    if down:
        p.box(x0 - ox, 0, z0 - oz, x1 - ox, 0, z1 - oz, AIR)
    lo = 0 if down else 1
    hi = top if up else top - 1
    for y in range(lo, hi + 1):
        p.set(LADDER_X - ox, y, LADDER_Z - oz, 'minecraft:ladder',
              {'facing': 'south', 'waterlogged': 'false'})


def hall(level):
    """The landing on each storey. East is the way in, north is the buttress, and the rest
    open onto whatever that storey holds."""
    p = room(['west', 'east', 'south'])
    door(p, 'east', EMPTY, name=WAY, target=WAY)
    if level == 1:
        door(p, 'west', POOL['passages'])
        door(p, 'south', POOL['passages'])
        origin = (HALL_AT[0], 0, HALL_AT[1])
    else:
        door(p, 'west', POOL['library'], name=WAY, target=ANCHOR, priority=PRIORITY)
        door(p, 'south', POOL['alchemy'], name=WAY, target=ANCHOR, priority=PRIORITY)
        origin = (HALL_AT[0], 7, HALL_AT[1])
    buttress_and_ladder(p, origin, CELL - 1)
    p.set(2, 4, 4, 'minecraft:lantern', {'hanging': 'true', 'waterlogged': 'false'})
    return p


def spine_l1():
    """One room of the entrance corridor, with the maze hanging off both sides."""
    p = room(['west', 'east', 'north', 'south'])
    door(p, 'east', EMPTY, name=WAY, target=WAY)
    door(p, 'west', POOL['hall_l1'], name=WAY, target=WAY, priority=PRIORITY)
    door(p, 'north', POOL['passages'])
    door(p, 'south', POOL['passages'])
    p.set(3, 4, 3, 'minecraft:lantern', {'hanging': 'true', 'waterlogged': 'false'})
    return p


# --------------------------------------------------------------------------- what it is for

def library():
    """Fifteen bookshelves in a ring two blocks out from an enchanting table, which is what
    level thirty asks for, with one gap in the ring to walk in through. The shelves lining the
    walls are for the look of the place; only the ring counts."""
    n = SIZE['library'][0]
    p = Piece(n, CELL, n, STONE)
    p.jigsaw(n - 1, 0, 10, 'east_up', EMPTY, STONE, name=ANCHOR, target=ANCHOR)
    p.box(1, 1, 1, n - 2, 5, n - 2, AIR)
    p.box(0, 0, 0, n - 1, 0, n - 1, DARK)
    p.box(n - 1, 1, 9, n - 1, 4, 11, AIR)             # the door back to the hall
    p.box(1, 1, n - 1, n - 2, 4, n - 1, STONE)
    for x in range(1, n - 1):                          # shelves along the walls
        for z in (1, n - 2):
            p.set(x, 1, z, 'minecraft:bookshelf')
            p.set(x, 2, z, 'minecraft:bookshelf')
    for z in range(2, n - 2):
        p.set(1, 1, z, 'minecraft:bookshelf')
        p.set(1, 2, z, 'minecraft:bookshelf')
    cx, cz = 6, 6
    p.set(cx, 1, cz, 'minecraft:enchanting_table')
    for dx in range(-2, 3):                            # the ring that counts
        for dz in range(-2, 3):
            if max(abs(dx), abs(dz)) != 2:
                continue
            if (dx, dz) == (0, -2):                    # the way in to the table
                continue
            p.set(cx + dx, 1, cz + dz, 'minecraft:bookshelf')
    p.set(cx, 4, cz, 'minecraft:lantern', {'hanging': 'true', 'waterlogged': 'false'})
    p.set(2, 1, 10, 'minecraft:lectern', {'facing': 'east', 'has_book': 'false', 'powered': 'false'})
    p.set(10, 2, 10, *chest('castle_library', 'south'))
    # its own south door, at this piece's scale - DOOR_AT describes a 7-cell face and would
    # have put this jigsaw in the middle of the room
    p.box(5, 1, n - 1, 7, 4, n - 1, AIR)
    p.jigsaw(6, 0, n - 1, 'south_up', POOL['passages'], STONE, name=DOOR, target=DOOR)
    return p


def alchemy():
    """The still room: a brewing stand that works, cauldrons, and the makings."""
    p = room(['north', 'south'])
    p.jigsaw(3, 0, 0, 'north_up', EMPTY, STONE, name=ANCHOR, target=ANCHOR)
    door(p, 'south', POOL['passages'])
    p.box(1, 1, 5, 5, 1, 5, POLISHED)
    p.set(3, 2, 5, 'minecraft:brewing_stand',
          {'has_bottle_0': 'false', 'has_bottle_1': 'false', 'has_bottle_2': 'false'})
    p.set(1, 1, 1, 'minecraft:cauldron', {'level': '0'})
    p.set(5, 1, 1, 'minecraft:cauldron', {'level': '0'})
    p.set(1, 2, 5, *chest('castle_study', 'north'))
    p.set(3, 4, 3, 'minecraft:soul_lantern', {'hanging': 'true', 'waterlogged': 'false'})
    return p


def tower(step):
    """A storey of the tower: a landing on the ladder, with arrow slits."""
    p = Piece(CELL, CELL, CELL, DEEP)
    under_anchor(p)
    p.box(1, 1, 1, 5, 5, 5, AIR)
    for z in (1, 5):
        p.set(0, 3, z, GLASS, {'north': 'false', 'south': 'false', 'east': 'false',
                               'west': 'false', 'waterlogged': 'false'})
        p.set(6, 3, z, GLASS, {'north': 'false', 'south': 'false', 'east': 'false',
                               'west': 'false', 'waterlogged': 'false'})
    origin = AT['tower_%d' % step]
    buttress_and_ladder(p, origin, CELL - 1)
    nxt = 'observatory' if step == 3 else 'tower_%d' % (step + 1)
    stack_onto(p, 'tower_%d' % step, nxt)
    if step == 2:
        p.set(2, 1, 4, 'minecraft:spawner', None, mob_spawner('minecraft:vex', 2))
    return p


def observatory():
    """The top of the tower, and the only room in the castle with a view."""
    p = Piece(CELL, CELL, CELL, DEEP)
    under_anchor(p)
    p.box(1, 1, 1, 5, 5, 5, AIR)
    for x, z in ((0, 3), (6, 3), (3, 0), (3, 6)):
        for y in (2, 3):
            p.set(x, y, z, GLASS, {'north': 'false', 'south': 'false', 'east': 'false',
                                   'west': 'false', 'waterlogged': 'false'})
    buttress_and_ladder(p, AT['observatory'], CELL - 1, up=False)
    p.box(2, 1, 4, 4, 1, 4, 'minecraft:amethyst_block')
    p.set(3, 2, 4, *chest('castle_observatory', 'north'))
    p.set(1, 1, 1, 'minecraft:end_stone')
    p.set(5, 1, 1, 'minecraft:end_stone')
    p.set(3, 5, 3, 'minecraft:soul_lantern', {'hanging': 'true', 'waterlogged': 'false'})
    return p


def sanctum():
    """The chamber under the castle: the archmage, his guards, and the gate he was building.

    The ladder comes down the middle on a pillar, so you arrive in the open with the spawners
    already around you - the same arrival as the pyramid's burial hall."""
    ox, oy, oz = AT['sanctum']
    n = SIZE['sanctum'][0]
    c = n // 2
    p = Piece(n, n, n, DEEP)
    over_anchor(p, 'sanctum')
    p.box(1, 1, 1, n - 2, n - 2, n - 2, AIR)
    for y in (7, 14):
        for i in range(n):
            for x, z in ((0, i), (n - 1, i), (i, 0), (i, n - 1)):
                p.set(x, y, z, POLISHED)
    for x0, z0 in ((2, 2), (2, n - 4), (n - 4, 2), (n - 4, n - 4)):
        p.box(x0, 1, z0, x0 + 1, n - 2, z0 + 1, POLISHED)
    for x in range(1, n - 1):
        for z in range(1, n - 1):
            if x % 4 == 1 and z % 4 == 1:
                p.set(x, 0, z, POLISHED)

    # the pillar the ladder comes down, and the hole above it
    x0, x1, z0, z1 = SHAFT
    p.box(x0 - ox, 1, LADDER_Z - 1 - oz, x1 - ox, n - 2, LADDER_Z - 1 - oz, CHISELED)
    p.box(x0 - ox, n - 1, z0 - oz, x1 - ox, n - 1, z1 - oz, AIR)
    for y in range(1, n):
        p.set(LADDER_X - ox, y, LADDER_Z - oz, 'minecraft:ladder',
              {'facing': 'south', 'waterlogged': 'false'})

    # the gate he never lit, on the south wall, with the steel beside it
    fx, fy, fz = c - 2, 1, n - 3
    for dx, dy in ((1, 0), (2, 0), (1, 4), (2, 4),
                   (0, 1), (0, 2), (0, 3), (3, 1), (3, 2), (3, 3)):
        p.set(fx + dx, fy + dy, fz, 'minecraft:obsidian')
    p.set(fx - 2, 1, fz, *chest('castle_portal', 'west'))

    # the archmage on the dais at the north end, his guards in the quarters
    p.box(c - 3, 1, 3, c + 3, 1, 7, POLISHED)
    p.box(c - 1, 2, 4, c + 1, 2, 6, CHISELED)
    p.set(c, 3, 5, 'minecraft:trial_spawner', TRIAL_STATE, trial_spawner('archmage'))
    for x, z in ((5, 5), (n - 6, 5), (5, n - 6), (n - 6, n - 6)):
        p.set(x, 1, z, 'minecraft:trial_spawner', TRIAL_STATE, trial_spawner('castle_guards'))
    for x, z in ((c, 4), (4, c), (n - 5, c), (c, n - 5)):
        p.set(x, n - 5, z, 'minecraft:soul_lantern', {'hanging': 'true', 'waterlogged': 'false'})
    return p


# --------------------------------------------------------------------------- pools

def element(location, weight):
    return ('    { "weight": %d, "element": { "element_type": "minecraft:single_pool_element",\n'
            '        "location": "%s:castle/%s", "projection": "rigid", '
            '"processors": "%s:castle_weathering" } }' % (weight, NS, location, NS))


def write_pool(name, elements, fallback=NS + ':castle/caps'):
    os.makedirs(POOL_JSON, exist_ok=True)
    text = '{\n  "fallback": "%s",\n  "elements": [\n%s\n  ]\n}\n' % (fallback, ',\n'.join(elements))
    with open(os.path.join(POOL_JSON, name + '.json'), 'w', encoding='utf-8', newline='\n') as f:
        f.write(text)


def verify(pieces):
    """The alignments that are invisible until you are standing in the castle."""
    problems = []
    for child, parent in (('core_l1', 'keep'), ('core_l2', 'keep'), ('tower_1', 'keep')):
        for axis in range(3):
            lo = AT[child][axis] - AT[parent][axis]
            if lo < 0 or lo + SIZE[child][axis] > SIZE[parent][axis]:
                problems.append('%s is not inside %s on axis %d' % (child, parent, axis))
    for child in ('library', 'alchemy'):
        for axis in (0, 2):
            lo = AT[child][axis] - AT['core_l2'][axis]
            if lo < 0 or lo + SIZE[child][axis] > SIZE['core_l2'][axis]:
                problems.append('%s is not inside core_l2 on axis %d' % (child, axis))

    # the shaft has to be inside every piece it passes through
    x0, x1, z0, z1 = SHAFT
    for name, at, size in (('hall', (HALL_AT[0], 0, HALL_AT[1]), (CELL, CELL, CELL)),
                           ('sanctum', AT['sanctum'], SIZE['sanctum']),
                           ('tower_1', AT['tower_1'], SIZE['tower_1']),
                           ('observatory', AT['observatory'], SIZE['observatory'])):
        for axis, lo, hi in ((0, x0, x1), (2, z0, z1)):
            if not (at[axis] < lo and hi < at[axis] + size[axis] - 1):
                problems.append('the shaft touches %s\'s wall on axis %d' % (name, axis))
    if not (x0 <= LADDER_X <= x1 and z0 <= LADDER_Z <= z1):
        problems.append('the ladder is not in the shaft')

    # the towers stack without a gap
    for a, b in (('tower_1', 'tower_2'), ('tower_2', 'tower_3'), ('tower_3', 'observatory')):
        if AT[a][1] + SIZE[a][1] != AT[b][1]:
            problems.append('%s does not sit on %s' % (b, a))
    if AT['keep'][1] + SIZE['keep'][1] != AT['tower_1'][1] + CELL:
        problems.append('the tower does not start at the keep roof')

    # A maze connector has to sit on one of its piece's own faces. The structural jigsaws -
    # the ones that place a child inside the parent's own box, which is how the shape is
    # fenced - deliberately sit in the interior, so only DOOR is checked. The library is
    # fourteen blocks across and the shared DOOR_AT table describes a seven-block face, so
    # its south door once landed in the middle of the room pointing at the far wall.
    for name, piece in pieces.items():
        sx, sy, sz = piece.size
        for (x, y, z), (block, props) in piece.grid.items():
            if not (0 <= x < sx and 0 <= y < sy and 0 <= z < sz):
                problems.append('%s writes outside itself at %s' % (name, (x, y, z)))
                break
            if block != 'minecraft:jigsaw':
                continue
            meta = piece.extra.get((x, y, z), {})
            if DOOR not in (meta.get('name'), meta.get('target')):
                continue
            facing = dict(props or ()).get('orientation', '').split('_')[0]
            on = {'west': x == 0, 'east': x == sx - 1,
                  'north': z == 0, 'south': z == sz - 1}.get(facing)
            if on is False:
                problems.append('%s has a %s door at %s, not on that face'
                                % (name, facing, (x, y, z)))

    for line in problems:
        print('  PROBLEM  ' + line)
    if problems:
        raise SystemExit('the castle does not hold together')
    print('  checked: storeys nested, shaft clear of every wall, tower stacked')


def main():
    os.makedirs(DST, exist_ok=True)
    pieces = {
        'keep': keep(), 'core_l1': core_l1(), 'core_l2': core_l2(),
        'spine_l1': spine_l1(), 'hall_l1': hall(1), 'hall_l2': hall(2),
        'library': library(), 'alchemy': alchemy(), 'sanctum': sanctum(),
        'observatory': observatory(),
        'passage': passage(), 'corner': corner(), 'cross': cross(),
        'study': study(), 'vex_cage': vex_cage(), 'lab': lab(), 'cap': cap(),
    }
    for i in (1, 2, 3):
        pieces['tower_%d' % i] = tower(i)
    verify(pieces)
    for name, piece in sorted(pieces.items()):
        piece.write(os.path.join(DST, name + '.nbt'))
        print('  %-12s %s' % (name, list(piece.size)))

    write_pool('start', [element('keep', 1)], fallback=EMPTY)
    for one in ('core_l1', 'core_l2', 'sanctum', 'library', 'alchemy', 'spine_l1',
                'hall_l1', 'hall_l2', 'tower_1', 'tower_2', 'tower_3', 'observatory'):
        write_pool(one, [element(one, 1)], fallback=EMPTY)
    write_pool('passages', [element('passage', 10), element('corner', 8), element('cross', 8),
                            element('study', 8), element('vex_cage', 6), element('lab', 6)])
    write_pool('caps', [element('cap', 1)], fallback=EMPTY)
    print('  pools -> %s' % os.path.relpath(POOL_JSON, ROOT))


if __name__ == '__main__':
    main()
