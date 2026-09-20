# -*- coding: utf-8 -*-
"""The Wizard's Tower: seven floors of rooms round a stairwell, a library and a sanctum.

    python tools/generate_tower.py        (or through make_pieces.py)

Writes data/sydungeon/structure/tower/*.nbt and the pools that join them.

THE SHAPE
    shell (39x56x39)  --inside--> core (35x49x35)  --inside--> everything else

`core` is one box for the whole interior, not one per floor, which is what lets a room
twenty-one blocks tall stand in the middle of it while the maze flows round the outside. The
maze is a descendant of core, so no piece can reach the outer wall (CLAUDE.md section 10).

                      floors 5-7   the sanctum, and a gallery round it
                      floors 2-4   the library, and a gallery round it
                      floor 1      the way in, the still room, and rooms

WHAT IS GUARANTEED
A stairwell runs up the west side, one piece per floor, each placed by the one below it:

    core -> well_1 -> well_2 -> ... -> well_7
              |         |                        well_1 east  -> the still room
              |         +--- east -> the library (floors 2-4)
              +--- well_5 east -> the sanctum (floors 5-7)

Every one of those is a single-element pool, so each room is placed exactly once and is
always reachable from the stairwell. Nothing important is left to the maze.

WHY EACH LINK HAS ITS OWN CONNECTOR NAME
Vanilla enters a child through *any* of its jigsaws whose name matches, trying all four
rotations. The castle this replaces gave several jigsaws on one piece the same name, so half
the time the generator came in through the wrong one and the chain went backwards: the boss
room and the observatory ended up with no way in at all. Here every deterministically placed
piece carries exactly one jigsaw with the name its parent targets. Vertical links are safe
without that, since rotation cannot turn an up-facing jigsaw into a down-facing one.
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
RISER = NS + ':tow_riser'      # a stairwell piece's way in
ANCHOR = NS + ':tow_anchor'    # a named room's way in
PLACER = NS + ':tow_placer'    # a jigsaw whose job is to put a fixed piece somewhere; it is
                               # not a door, so it is exempt from the on-a-face check
EMPTY = 'minecraft:empty'

CELL = 7
FLOORS = 7
GRID = 5                       # 5x5 rooms to a floor
WALL = 2
CORE = GRID * CELL             # 35
TOWER = CORE + 2 * WALL        # 39
HEIGHT = FLOORS * CELL         # 49
PRIORITY = 20

STONE = 'minecraft:stone_bricks'
CHISELED = 'minecraft:chiseled_stone_bricks'
DEEP = 'minecraft:deepslate_bricks'
POLISHED = 'minecraft:polished_deepslate'
DARK = 'minecraft:dark_oak_planks'
GLASS = 'minecraft:glass_pane'
BOOKSHELF = 'minecraft:bookshelf'
AIR = 'minecraft:air'
PANE = {'north': 'false', 'south': 'false', 'east': 'false', 'west': 'false',
        'waterlogged': 'false'}

WELL_CELL = (0, 2)             # the stairwell, on the middle of the west side
BIG_CELLS = (1, 3)             # the library and the sanctum fill cells 1..3 both ways

AT = {
    'shell': (0, 0, 0),
    'core': (WALL, 0, WALL),
    'library': (WALL + BIG_CELLS[0] * CELL, CELL, WALL + BIG_CELLS[0] * CELL),
    'sanctum': (WALL + BIG_CELLS[0] * CELL, 4 * CELL, WALL + BIG_CELLS[0] * CELL),
    'alchemy': (WALL + CELL, 0, WALL + WELL_CELL[1] * CELL),
}
SIZE = {
    'shell': (TOWER, HEIGHT + CELL, TOWER),
    'core': (CORE, HEIGHT, CORE),
    'library': (21, 21, 21),
    'sanctum': (21, 21, 21),
    'alchemy': (CELL, CELL, CELL),
}
for i in range(1, FLOORS + 1):
    AT['well_%d' % i] = (WALL + WELL_CELL[0] * CELL, (i - 1) * CELL, WALL + WELL_CELL[1] * CELL)
    SIZE['well_%d' % i] = (CELL, CELL, CELL)

# The stairwell's shaft and the ladder in it, in the well piece's own coordinates. It is in
# the south-east corner, clear of the gate on the west and the way in on the north.
SHAFT = (4, 5, 4, 5)
LADDER = (5, 5)                # hangs on the east wall

POOL = {k: NS + ':tower/' + k for k in
        ['passages', 'caps', 'core', 'library', 'sanctum', 'alchemy'] +
        ['well_%d' % i for i in range(1, FLOORS + 1)]}

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


DOOR_AT = {'west': (0, 0, 3, 'west_up'), 'east': (6, 0, 3, 'east_up'),
           'north': (3, 0, 0, 'north_up'), 'south': (3, 0, 6, 'south_up')}


def door(p, side, pool, name=DOOR, target=DOOR, priority=0):
    x, y, z, orientation = DOOR_AT[side]
    p.jigsaw(x, y, z, orientation, pool, STONE, priority=priority, name=name, target=target)


def opening(p, side, size=CELL):
    """The hole a door's jigsaw stands in."""
    if side == 'west':
        p.box(0, 1, size // 2 - 1, 0, 4, size // 2 + 1, AIR)
    elif side == 'east':
        p.box(size - 1, 1, size // 2 - 1, size - 1, 4, size // 2 + 1, AIR)
    elif side == 'north':
        p.box(size // 2 - 1, 1, 0, size // 2 + 1, 4, 0, AIR)
    else:
        p.box(size // 2 - 1, 1, size - 1, size // 2 + 1, 4, size - 1, AIR)


# --------------------------------------------------------------------------- shell and core

GATE_Z = (AT['well_1'][2] + 2, AT['well_1'][2] + 4)     # lines up with the stairwell's west


def shell():
    """The outer wall, the floor slabs and the roof. The inside of each floor is left solid;
    core claims it and the rooms carve into it."""
    n, h = TOWER, SIZE['shell'][1]
    p = Piece(n, h, n, STONE)
    for y in range(h):
        for x in range(n):
            for z in range(n):
                if y < HEIGHT and y % CELL == CELL - 1:
                    p.set(x, y, z, DEEP if (x + z) % 2 else POLISHED)
    # battlements on top of the last floor
    p.box(WALL, HEIGHT, WALL, n - 1 - WALL, h - 1, n - 1 - WALL, AIR)
    p.box(0, HEIGHT + 3, 0, n - 1, h - 1, n - 1, AIR)
    for i in range(n):
        for x, z in ((0, i), (n - 1, i), (i, 0), (i, n - 1)):
            p.set(x, HEIGHT, z, DEEP)
            p.set(x, HEIGHT + 1, z, STONE)
            if i % 2 == 0:
                p.set(x, HEIGHT + 2, z, CHISELED)
    # windows: one block wide, two tall, cut clean through both courses so they read as
    # openings rather than glass set into a wall
    for floor in range(FLOORS):
        y = floor * CELL + 2
        for i in range(5, n - 4, 8):
            for x, z, dx, dz in ((0, i, 1, 0), (n - 1, i, -1, 0), (i, 0, 0, 1), (i, n - 1, 0, -1)):
                for depth in range(WALL):
                    for dy in (0, 1):
                        p.set(x + dx * depth, y + dy, z + dz * depth, GLASS, PANE)
    # the gate, straight into the stairwell
    p.box(0, 1, GATE_Z[0], WALL - 1, 4, GATE_Z[1], AIR)
    p.set(0, 5, GATE_Z[0] - 1, CHISELED)
    p.set(0, 5, GATE_Z[1] + 1, CHISELED)

    ox, oy, oz = AT['core']
    p.jigsaw(ox - 1, oy, oz + SIZE['core'][2] // 2, 'east_up', POOL['core'], STONE,
             priority=PRIORITY, name=PLACER, target=ANCHOR)
    return p


def core():
    """One solid block for the whole interior. A single box, not one per floor, so the two
    twenty-one-block rooms can stand three floors tall inside it."""
    sx, sy, sz = SIZE['core']
    p = Piece(sx, sy, sz, STONE)
    p.jigsaw(0, 0, sz // 2, 'west_up', EMPTY, STONE, name=ANCHOR, target=ANCHOR)
    # the one jigsaw that starts everything: it places the ground floor of the stairwell
    wx, wy, wz = AT['well_1']
    ox, oy, oz = AT['core']
    p.jigsaw(wx - ox + 3, 0, wz - oz - 1, 'south_up', POOL['well_1'], STONE,
             priority=PRIORITY, name=PLACER, target=RISER)
    return p


# --------------------------------------------------------------------------- the stairwell

def well(floor):
    """One floor of the stairwell. Its way in is the only jigsaw on it with that name, so the
    generator cannot come in through the wrong side and send the chain backwards."""
    p = Piece(CELL, CELL, CELL, STONE)
    p.box(1, 1, 1, 5, 5, 5, AIR)
    p.box(0, 0, 0, 6, 0, 6, DARK)

    if floor == 1:
        opening(p, 'north')
        p.jigsaw(3, 0, 0, 'north_up', EMPTY, STONE, name=RISER, target=RISER)
        p.box(0, 1, 2, 0, 4, 4, AIR)              # the gate, carved to match the shell's
    else:
        p.jigsaw(0, 0, 0, 'down_east', EMPTY, STONE, joint='aligned',
                 name=RISER, target=RISER)

    # east: the still room on the ground floor, the library on 2, the sanctum on 5, and on the
    # floors between, the big rooms' own wall
    if floor == 1:
        opening(p, 'east')
        door(p, 'east', POOL['alchemy'], name=PLACER, target=ANCHOR, priority=PRIORITY)
    elif floor == 2:
        opening(p, 'east')
        door(p, 'east', POOL['library'], name=PLACER, target=ANCHOR, priority=PRIORITY)
    elif floor == 5:
        opening(p, 'east')
        door(p, 'east', POOL['sanctum'], name=PLACER, target=ANCHOR, priority=PRIORITY)

    opening(p, 'south')
    door(p, 'south', POOL['passages'])
    if floor != 1:
        opening(p, 'north')
        door(p, 'north', POOL['passages'])

    # the shaft and its ladder, in the south-east corner, clear of every door
    x0, x1, z0, z1 = SHAFT
    p.box(x0, CELL - 1, z0, x1, CELL - 1, z1, AIR)
    if floor > 1:
        p.box(x0, 0, z0, x1, 0, z1, AIR)
    lo = 0 if floor > 1 else 1
    for y in range(lo, CELL):
        p.set(LADDER[0], y, LADDER[1], 'minecraft:ladder',
              {'facing': 'west', 'waterlogged': 'false'})
    if floor < FLOORS:
        p.jigsaw(0, CELL - 1, 0, 'up_east', POOL['well_%d' % (floor + 1)], STONE,
                 joint='aligned', priority=PRIORITY, name=PLACER, target=RISER)
    else:
        p.box(x0, CELL - 1, z0, x1, CELL - 1, z1, STONE)   # the top floor has no hole
    p.set(2, 4, 2, 'minecraft:lantern', {'hanging': 'true', 'waterlogged': 'false'})
    return p


# --------------------------------------------------------------------------- the rooms

def room(doors):
    p = Piece(CELL, CELL, CELL, STONE)
    p.box(1, 1, 1, 5, 5, 5, AIR)
    p.box(0, 0, 0, 6, 0, 6, DARK)
    for d in doors:
        opening(p, d)
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
    p = room(['west'])
    door(p, 'west', POOL['passages'])
    p.box(4, 1, 1, 5, 2, 5, BOOKSHELF)
    p.set(4, 3, 3, *chest('tower_study', 'west'))
    p.set(3, 1, 5, 'minecraft:lectern',
          {'facing': 'north', 'has_book': 'false', 'powered': 'false'})
    p.set(3, 4, 3, 'minecraft:lantern', {'hanging': 'true', 'waterlogged': 'false'})
    return p


def vex_cage():
    """A cage that stands on the floor, bar to bar, rather than a pane of iron floating in
    mid air - which is what the castle's version looked like."""
    p = room(['west', 'east'])
    door(p, 'west', POOL['passages'])
    door(p, 'east', POOL['passages'])
    bars = {'north': 'true', 'south': 'true', 'east': 'true', 'west': 'true',
            'waterlogged': 'false'}
    for x in range(2, 5):
        for z in range(4, 7):
            if x in (2, 4) or z in (4, 6):
                for y in range(1, 4):
                    p.set(x, y, z, 'minecraft:iron_bars', bars)
    p.box(2, 4, 4, 4, 4, 6, 'minecraft:iron_bars', bars)
    p.set(3, 1, 5, 'minecraft:spawner', None, mob_spawner('minecraft:vex'))
    return p


def lab():
    p = room(['west', 'east'])
    door(p, 'west', POOL['passages'])
    door(p, 'east', POOL['passages'])
    p.set(1, 1, 5, 'minecraft:cauldron', {'level': '0'})
    p.set(5, 1, 5, 'minecraft:cauldron', {'level': '0'})
    p.set(3, 1, 5, 'minecraft:spawner', None, mob_spawner('minecraft:zombie_villager'))
    p.set(3, 4, 3, 'minecraft:soul_lantern', {'hanging': 'true', 'waterlogged': 'false'})
    return p


def cap():
    p = Piece(1, CELL, CELL, STONE)
    p.jigsaw(0, 0, 3, 'west_up', POOL['caps'], STONE, name=DOOR, target=DOOR)
    return p


def alchemy():
    """The still room, off the stairwell's ground floor. A room of its own, not a widening of
    a corridor."""
    p = Piece(CELL, CELL, CELL, STONE)
    p.box(1, 1, 1, 5, 5, 5, AIR)
    p.box(0, 0, 0, 6, 0, 6, DARK)
    opening(p, 'west')
    p.jigsaw(0, 0, 3, 'west_up', EMPTY, STONE, name=ANCHOR, target=ANCHOR)
    p.box(1, 1, 5, 5, 1, 5, POLISHED)
    p.set(3, 2, 5, 'minecraft:brewing_stand',
          {'has_bottle_0': 'false', 'has_bottle_1': 'false', 'has_bottle_2': 'false'})
    p.set(1, 1, 1, 'minecraft:cauldron', {'level': '0'})
    p.set(5, 1, 1, 'minecraft:cauldron', {'level': '0'})
    p.set(1, 2, 5, *chest('tower_study', 'north'))
    p.set(3, 4, 3, 'minecraft:soul_lantern', {'hanging': 'true', 'waterlogged': 'false'})
    return p


# --------------------------------------------------------------------------- library

def library():
    """Three floors of one room: an atrium with galleries round it, shelves to the ceiling,
    and an enchanting table on the floor with the fifteen shelves that level thirty needs."""
    n = SIZE['library'][0]
    p = Piece(n, n, n, STONE)
    p.box(1, 1, 1, n - 2, n - 2, n - 2, AIR)
    p.box(0, 0, 0, n - 1, 0, n - 1, DARK)
    p.jigsaw(0, 0, n // 2, 'west_up', EMPTY, STONE, name=ANCHOR, target=ANCHOR)
    p.box(0, 1, n // 2 - 1, 0, 4, n // 2 + 1, AIR)

    # two galleries, each a five-wide walkway round an open well down the middle
    for gy in (CELL, 2 * CELL):
        p.box(1, gy, 1, n - 2, gy, n - 2, DARK)
        p.box(6, gy, 6, n - 7, gy, n - 7, AIR)
        for x in range(5, n - 5):
            for z in (5, n - 6):
                p.set(x, gy + 1, z, 'minecraft:dark_oak_fence',
                      {'north': 'true', 'south': 'true', 'east': 'true', 'west': 'true',
                       'waterlogged': 'false'})
        for z in range(5, n - 5):
            for x in (5, n - 6):
                p.set(x, gy + 1, z, 'minecraft:dark_oak_fence',
                      {'north': 'true', 'south': 'true', 'east': 'true', 'west': 'true',
                       'waterlogged': 'false'})

    # shelves lining every wall on every level
    for level in (1, CELL + 1, 2 * CELL + 1):
        for i in range(1, n - 1):
            for x, z in ((1, i), (n - 2, i), (i, 1), (i, n - 2)):
                for dy in (0, 1, 2):
                    p.set(x, level + dy, z, BOOKSHELF)

    # the ladders between the galleries, in a corner clear of the shelves
    for y in range(1, 2 * CELL + 6):
        p.set(3, y, 2, 'minecraft:ladder', {'facing': 'south', 'waterlogged': 'false'})
    for gy in (CELL, 2 * CELL):
        p.box(2, gy, 2, 4, gy, 3, AIR)
        p.set(3, gy, 2, 'minecraft:ladder', {'facing': 'south', 'waterlogged': 'false'})
        p.box(2, gy + 1, 1, 4, gy + 3, 1, AIR)

    # the table, and the ring that counts
    c = n // 2
    p.box(c - 3, 1, c - 3, c + 3, 1, c + 3, POLISHED)
    p.set(c, 2, c, 'minecraft:enchanting_table')
    for dx in range(-2, 3):
        for dz in range(-2, 3):
            if max(abs(dx), abs(dz)) != 2 or (dx, dz) == (0, -2):
                continue
            p.set(c + dx, 2, c + dz, BOOKSHELF)
    p.set(c, 6, c, 'minecraft:lantern', {'hanging': 'true', 'waterlogged': 'false'})
    p.set(c + 3, 2, c, *chest('tower_library', 'west'))
    p.set(c - 3, 2, c, *chest('tower_observatory', 'east'))
    p.set(c, 1, c - 4, 'minecraft:lectern',
          {'facing': 'south', 'has_book': 'false', 'powered': 'false'})
    return p


# --------------------------------------------------------------------------- sanctum

def sanctum():
    """The archmage's chamber, three floors tall at the top of the tower, with the gate he
    never lit."""
    n = SIZE['sanctum'][0]
    c = n // 2
    p = Piece(n, n, n, DEEP)
    p.box(1, 1, 1, n - 2, n - 2, n - 2, AIR)
    p.box(0, 0, 0, n - 1, 0, n - 1, POLISHED)
    p.jigsaw(0, 0, c, 'west_up', EMPTY, DEEP, name=ANCHOR, target=ANCHOR)
    p.box(0, 1, c - 1, 0, 4, c + 1, AIR)

    for y in (7, 14):
        for i in range(n):
            for x, z in ((0, i), (n - 1, i), (i, 0), (i, n - 1)):
                p.set(x, y, z, POLISHED)
    for x0, z0 in ((2, 2), (2, n - 4), (n - 4, 2), (n - 4, n - 4)):
        p.box(x0, 1, z0, x0 + 1, n - 2, z0 + 1, POLISHED)

    # the gate on the far wall, and the steel beside it
    fx, fz = c - 2, n - 3
    for dx, dy in ((1, 0), (2, 0), (1, 4), (2, 4),
                   (0, 1), (0, 2), (0, 3), (3, 1), (3, 2), (3, 3)):
        p.set(fx + dx, 1 + dy, fz, 'minecraft:obsidian')
    p.set(fx - 2, 1, fz, *chest('tower_portal', 'west'))

    p.box(c - 3, 1, 3, c + 3, 1, 7, POLISHED)
    p.box(c - 1, 2, 4, c + 1, 2, 6, CHISELED)
    p.set(c, 3, 5, 'minecraft:trial_spawner', TRIAL_STATE, trial_spawner('archmage'))
    for x, z in ((5, 5), (n - 6, 5), (5, n - 6), (n - 6, n - 6)):
        p.set(x, 1, z, 'minecraft:trial_spawner', TRIAL_STATE, trial_spawner('tower_guards'))
    for x, z in ((c, 4), (4, c), (n - 5, c), (c, n - 5)):
        p.set(x, n - 5, z, 'minecraft:soul_lantern', {'hanging': 'true', 'waterlogged': 'false'})
    return p


# --------------------------------------------------------------------------- pools

def element(location, weight):
    return ('    { "weight": %d, "element": { "element_type": "minecraft:single_pool_element",\n'
            '        "location": "%s:tower/%s", "projection": "rigid", '
            '"processors": "%s:tower_weathering" } }' % (weight, NS, location, NS))


def write_pool(name, elements, fallback=NS + ':tower/caps'):
    os.makedirs(POOL_JSON, exist_ok=True)
    text = '{\n  "fallback": "%s",\n  "elements": [\n%s\n  ]\n}\n' % (fallback, ',\n'.join(elements))
    with open(os.path.join(POOL_JSON, name + '.json'), 'w', encoding='utf-8', newline='\n') as f:
        f.write(text)


def verify(pieces):
    problems = []

    def inside(child, parent):
        for axis in range(3):
            lo = AT[child][axis] - AT[parent][axis]
            if lo < 0 or lo + SIZE[child][axis] > SIZE[parent][axis]:
                problems.append('%s is not inside %s on axis %d' % (child, parent, axis))

    inside('core', 'shell')
    for name in ['library', 'sanctum', 'alchemy'] + ['well_%d' % i for i in range(1, FLOORS + 1)]:
        inside(name, 'core')

    # the stairwell stacks with no gap, and the big rooms sit beside the floors that open
    # into them
    for i in range(1, FLOORS):
        a, b = 'well_%d' % i, 'well_%d' % (i + 1)
        if AT[a][1] + CELL != AT[b][1]:
            problems.append('%s does not sit on %s' % (b, a))
    for room_name, floor in (('alchemy', 1), ('library', 2), ('sanctum', 5)):
        wx, wy, wz = AT['well_%d' % floor]
        if AT[room_name][0] != wx + CELL:
            problems.append('%s is not against the stairwell it opens off' % room_name)
        if AT[room_name][1] != wy:
            problems.append('%s does not start on floor %d' % (room_name, floor))
        mid = AT[room_name][2] + SIZE[room_name][2] // 2
        if mid != wz + CELL // 2:
            problems.append('%s\'s door does not line up with the stairwell' % room_name)

    # the library and the sanctum must not overlap, and must stay inside the tower's height
    if AT['library'][1] + SIZE['library'][1] > AT['sanctum'][1]:
        problems.append('the library and the sanctum overlap')
    if AT['sanctum'][1] + SIZE['sanctum'][1] > HEIGHT:
        problems.append('the sanctum goes through the roof')

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

    for line in problems:
        print('  PROBLEM  ' + line)
    if problems:
        raise SystemExit('the tower does not hold together')
    print('  checked: %d floors stacked, rooms against the stairwell, one way into each'
          % FLOORS)


def main():
    os.makedirs(DST, exist_ok=True)
    pieces = {
        'shell': shell(), 'core': core(), 'library': library(), 'sanctum': sanctum(),
        'alchemy': alchemy(), 'passage': passage(), 'corner': corner(), 'cross': cross(),
        'study': study(), 'vex_cage': vex_cage(), 'lab': lab(), 'cap': cap(),
    }
    for i in range(1, FLOORS + 1):
        pieces['well_%d' % i] = well(i)
    verify(pieces)
    for name, piece in sorted(pieces.items()):
        piece.write(os.path.join(DST, name + '.nbt'))
        print('  %-12s %s' % (name, list(piece.size)))

    write_pool('start', [element('shell', 1)], fallback=EMPTY)
    for one in ['core', 'library', 'sanctum', 'alchemy'] + \
               ['well_%d' % i for i in range(1, FLOORS + 1)]:
        write_pool(one, [element(one, 1)], fallback=EMPTY)
    write_pool('passages', [element('passage', 10), element('corner', 9), element('cross', 8),
                            element('study', 8), element('vex_cage', 6), element('lab', 6)])
    write_pool('caps', [element('cap', 1)], fallback=EMPTY)
    print('  pools -> %s' % os.path.relpath(POOL_JSON, ROOT))


if __name__ == '__main__':
    main()
