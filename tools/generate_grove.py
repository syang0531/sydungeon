# -*- coding: utf-8 -*-
"""The Mycelium Hollow: a cave under the mushroom fields where nothing wants to kill you.

    python tools/generate_grove.py        (or through make_pieces.py)

Writes data/sydungeon/structure/grove/*.nbt and the pools that join them.

THE FIRST OF THE SMALL ONES
Every dungeon before this one is what concepts.md section 2.8 calls large: a boss on a chain
of single-element pools, a guaranteed signature, thirty to sixty minutes. This is the other
kind. **No boss, no signature, no spawner that means you harm** - a hollow with a mooshroom
pen in it, beds, bowls and as much stew as anyone can eat. Twenty pieces, ten minutes, and the
one thing it gives is somewhere safe to sleep.

That is why it has no trial spawner. A little ruin with a trial spawner in it would turn a
full set of diamond gear from six victories into an afternoon (section 2.8), and this one is
not even a ruin - it is a place to stop.

HOW IT IS BUILT
The prison's machine, shortened: a mouth at the surface, one shaft, a hollow, and a maze of
mycelium cells that plugs itself with a one-block cap at the ends (section 4). The pen and the
camp are on single-element pools so they cannot fail to appear, the same way every boss in
this mod is guaranteed - only what is guaranteed here is a bed.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import nbt  # noqa: E402
from generate_pieces import Piece  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DST = os.path.join(ROOT, 'src', 'main', 'resources', 'data', 'sydungeon', 'structure', 'grove')
POOL_JSON = os.path.join(ROOT, 'src', 'main', 'resources', 'data', 'sydungeon', 'worldgen',
                         'template_pool', 'grove')

NS = 'sydungeon'
BURROW = NS + ':grv_burrow'       # the hollow's connector
DOWN = NS + ':grv_shaft'          # the one way down
PEN = NS + ':grv_pen'             # the pen and the camp, each on its own name so the chain
CAMP = NS + ':grv_camp'           # cannot be entered backwards (section 13)
EMPTY = 'minecraft:empty'
PRIORITY = 10

CELL = 7
MOUTH = 7
SHAFT_H = 14
GROUND = 0                       # the start piece's floor: a start is moved so that
                                 # minY + 1 is the first free block, so y=0 is the
                                 # terrain's own top block (section 30)

HOLE = (MOUTH // 2, MOUTH // 2)  # one column, dead centre of the mouth (section 33)
RUNG = HOLE                      # the ladder is the hole
JIG = (HOLE[0], HOLE[1] + 1)     # the stalk it hangs on, one out of the hole

MYC = 'minecraft:mycelium'
STEM = 'minecraft:mushroom_stem'
BROWN = 'minecraft:brown_mushroom_block'
RED = 'minecraft:red_mushroom_block'
MOSS = 'minecraft:moss_block'
CARPET = 'minecraft:moss_carpet'
ROOTED = 'minecraft:rooted_dirt'
LICHEN = 'minecraft:glow_lichen'
ROOTS = 'minecraft:hanging_roots'
SPORE = 'minecraft:spore_blossom'
DRIP = 'minecraft:dripstone_block'
STONE = 'minecraft:stone'
PLANK = 'minecraft:oak_planks'
FENCE = 'minecraft:oak_fence'
LOG = 'minecraft:oak_log'
AIR = 'minecraft:air'

ALL_SIDES = {'north': 'true', 'south': 'true', 'east': 'true', 'west': 'true',
             'up': 'false', 'down': 'true', 'waterlogged': 'false'}
CAP_UP = {'north': 'false', 'south': 'false', 'east': 'false', 'west': 'false',
          'up': 'true', 'down': 'false', 'waterlogged': 'false'}
MUSHROOM = {'north': 'true', 'south': 'true', 'east': 'true', 'west': 'true',
            'up': 'true', 'down': 'false'}
POST = {'north': 'false', 'south': 'false', 'east': 'false', 'west': 'false',
        'waterlogged': 'false'}

POOL = {k: NS + ':grove/' + k for k in
        ['start', 'down', 'first', 'burrows', 'burrow_caps', 'pen', 'camp']}

ANY_LIGHT = {'block_light_limit': {'min_inclusive': nbt.Int(0), 'max_inclusive': nbt.Int(15)}}


def mob_spawner(entity, count=2):
    """A spawner of something harmless. The light rule is the same as everywhere else in this
    mod (section 6) - a mooshroom will not spawn in the dark on its own either."""
    return {'id': 'minecraft:mob_spawner',
            'SpawnData': {'entity': {'id': entity}, 'custom_spawn_rules': ANY_LIGHT},
            'Delay': nbt.Short(20), 'MinSpawnDelay': nbt.Short(600),
            'MaxSpawnDelay': nbt.Short(1200), 'SpawnCount': nbt.Short(count),
            'MaxNearbyEntities': nbt.Short(4), 'RequiredPlayerRange': nbt.Short(16),
            'SpawnRange': nbt.Short(4)}


def chest(table, facing='north'):
    return ('minecraft:chest', {'facing': facing, 'type': 'single', 'waterlogged': 'false'},
            {'id': 'minecraft:chest', 'LootTable': NS + ':chests/' + table})


def ladder(facing='north'):
    return ('minecraft:ladder', {'facing': facing, 'waterlogged': 'false'})


def bed(p, x, y, z, facing='south', colour='white'):
    p.set(x, y, z, 'minecraft:%s_bed' % colour, {'facing': facing, 'part': 'foot'})
    dz = 1 if facing == 'south' else -1
    p.set(x, y, z + dz, 'minecraft:%s_bed' % colour, {'facing': facing, 'part': 'head'})


def sink(p, y0, y1, off=0, fill=MYC):
    """The way down: one column of ladder, and a ring of solid block round it (section 33)."""
    cx, cz = (v - off for v in HOLE)
    for x in range(cx - 1, cx + 2):
        for z in range(cz - 1, cz + 2):
            for y in range(y0, y1 + 1):
                p.set(x, y, z, fill)
    for y in range(y0, y1 + 1):
        p.set(cx, y, cz, *ladder())


# --------------------------------------------------------------------------- the surface
def mouth():
    """The start: a ring of huge mushrooms round a hole in the mycelium, and a ladder. Eight
    blocks tall and that is all there is above ground - the hollow is the dungeon."""
    n = MOUTH
    p = Piece(n, GROUND + 8, n, AIR)
    g, mid = GROUND, n // 2
    p.box(0, g, 0, n - 1, g, n - 1, MYC)                              # the floor, on the
    p.box(0, g + 1, 0, n - 1, g + 7, n - 1, AIR)
    for x, z in ((0, 0), (0, n - 1), (n - 1, 0), (n - 1, n - 1)):      # the four caps
        for y in range(g + 1, g + 4):
            p.set(x, y, z, STEM, ALL_SIDES)
        p.set(x, g + 4, z, RED if (x + z) % 2 else BROWN, MUSHROOM)
    for i in (1, mid, n - 2):                                          # a fairy ring of small
        for x, z in ((i, 0), (i, n - 1), (0, i), (n - 1, i)):          # mushrooms round it
            if (x + z) % 3:
                p.set(x, g + 1, z, 'minecraft:brown_mushroom')
    p.set(mid + 1, g + 1, mid + 1, CARPET, {'bottom': 'true'})
    p.jigsaw(JIG[0], 0, JIG[1], 'down_east', POOL['down'], ROOTED, joint='aligned',
             priority=PRIORITY, name=DOWN, target=DOWN)
    floor_and_hole(p)
    return p


def floor_and_hole(p):
    g = GROUND
    cx, cz = HOLE
    for x in range(MOUTH):
        for z in range(MOUTH):
            if (x, z) == (cx, cz):
                continue
            if p.grid.get((x, g, z), (AIR,))[0] in (AIR, 'minecraft:ladder'):
                p.set(x, g, z, MYC)
    sink(p, 0, g)
    p.jigsaw(JIG[0], 0, JIG[1], 'down_east', POOL['down'], ROOTED, joint='aligned',
             priority=PRIORITY, name=DOWN, target=DOWN)


def shaft():
    p = Piece(CELL, SHAFT_H, CELL, STONE)
    for y in range(SHAFT_H):
        p.box(0, y, 0, CELL - 1, y, CELL - 1, ROOTED if y % 3 else STONE)
    sink(p, 0, SHAFT_H - 1, fill=ROOTED)
    p.jigsaw(JIG[0], SHAFT_H - 1, JIG[1], 'up_east', EMPTY, ROOTED, joint='aligned',
             name=DOWN, target=DOWN)
    p.jigsaw(JIG[0], 0, JIG[1], 'down_east', POOL['first'], ROOTED, joint='aligned',
             priority=PRIORITY, name=BURROW, target=BURROW)
    return p


# ---------------------------------------------------------------------------- the hollow
def burrow_room(doors, floor=MYC):
    """A cell of the hollow. Rooted dirt and stone outside, mycelium underfoot, glow lichen
    on the ceiling - it is lit by the walls, so nothing here needs a torch."""
    p = Piece(CELL, CELL, CELL, ROOTED)
    for y in range(CELL):
        p.box(0, y, 0, CELL - 1, y, CELL - 1, STONE if y % 3 == 1 else ROOTED)
    p.box(1, 1, 1, CELL - 2, CELL - 2, CELL - 2, AIR)
    p.box(0, 0, 0, CELL - 1, 0, CELL - 1, floor)
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
    for x in range(1, CELL - 1):                                   # the lichen on the roof
        for z in range(1, CELL - 1):
            if (x * 3 + z * 5) % 4 == 0:
                p.set(x, CELL - 2, z, LICHEN, CAP_UP)
    return p


DOOR_AT = {'west': (0, 0, 3, 'west_up'), 'east': (CELL - 1, 0, 3, 'east_up'),
           'north': (3, 0, 0, 'north_up'), 'south': (3, 0, CELL - 1, 'south_up')}


def door(p, side, pool, name=BURROW, target=BURROW, priority=0):
    x, y, z, orientation = DOOR_AT[side]
    p.jigsaw(x, y, z, orientation, pool, ROOTED, priority=priority, name=name, target=target)


def hollow():
    """Where the ladder lands. Two ways into the hollow and two more, each on its own
    connector and placed first, to the pen and the camp - so both are always there."""
    p = burrow_room(['west', 'east', 'north', 'south'])
    hub_wiring(p)
    door(p, 'west', POOL['burrows'])
    door(p, 'north', POOL['pen'], name=BURROW, target=PEN, priority=PRIORITY)
    door(p, 'south', POOL['camp'], name=BURROW, target=CAMP, priority=PRIORITY)
    door(p, 'east', POOL['burrows'])
    p.set(1, 1, 1, SPORE)
    return p


def hub_wiring(p):
    cx, cz = HOLE
    jx, jz = JIG
    for x in range(CELL):
        for z in range(CELL):
            if p.grid.get((x, CELL - 1, z), (AIR,))[0] in (AIR, 'minecraft:ladder'):
                p.set(x, CELL - 1, z, ROOTED)
    for y in range(1, CELL):
        p.set(jx, y, jz, STEM, ALL_SIDES)            # the stalk the ladder hangs on
    for y in range(1, CELL):
        p.set(cx, y, cz, *ladder())                  # the climb, ceiling course included
    p.jigsaw(jx, CELL - 1, jz, 'up_east', EMPTY, STEM, joint='aligned',
             name=BURROW, target=BURROW)


def burrow(kind):
    doors = {'tunnel': ['west', 'east'], 'bend': ['west', 'south'],
             'cross': ['west', 'east', 'north', 'south'],
             'garden': ['west', 'east'], 'grove': ['west'], 'spring': ['west', 'east'],
             'larder': ['west'], 'drip': ['west', 'east']}[kind]
    p = burrow_room(doors)
    for side in doors:
        door(p, side, POOL['burrows'])
    mid = CELL // 2
    if kind == 'garden':
        for x in range(1, CELL - 1):
            for z in range(1, CELL - 1):
                if (x + z) % 2:
                    p.set(x, 1, z, 'minecraft:brown_mushroom' if (x * z) % 2
                          else 'minecraft:red_mushroom')
                else:
                    p.set(x, 0, z, MOSS)
    elif kind == 'grove':
        for y in (1, 2, 3):
            p.set(mid, y, mid, STEM, ALL_SIDES)
        for x, z in ((mid - 1, mid), (mid + 1, mid), (mid, mid - 1), (mid, mid + 1)):
            p.set(x, 4, z, BROWN, MUSHROOM)
        p.set(mid, 4, mid, BROWN, MUSHROOM)
        p.set(1, 1, CELL - 2, *chest('grove_larder', 'north'))
        p.set(CELL - 2, 1, 1, CARPET, {'bottom': 'true'})
    elif kind == 'spring':
        p.box(2, 0, 2, 4, 0, 4, 'minecraft:water', {'level': '0'})
        p.set(3, 0, 3, MOSS)
        for x, z in ((1, 1), (CELL - 2, CELL - 2)):
            p.set(x, 1, z, ROOTS)
    elif kind == 'larder':
        p.set(CELL - 2, 1, mid, *chest('grove_larder', 'west'))
        p.set(1, 1, 1, 'minecraft:barrel', {'facing': 'up', 'open': 'false'})
        p.set(1, 1, CELL - 2, 'minecraft:composter', {'level': '0'})
        p.set(mid, 1, 1, 'minecraft:crafting_table')
    elif kind == 'drip':
        for x, z in ((2, 2), (4, 4), (3, 5)):
            p.set(x, CELL - 2, z, DRIP)
            p.set(x, CELL - 3, z, 'minecraft:pointed_dripstone',
                  {'thickness': 'tip', 'vertical_direction': 'down', 'waterlogged': 'false'})
        p.box(1, 0, 1, CELL - 2, 0, CELL - 2, DRIP)
    return p


def pen():
    """The mooshroom pen: a fence, a trough of hay, and a spawner that is the whole point of
    the place. Stew forever, and nothing in here wants to fight."""
    p = burrow_room(['south'], floor=MYC)
    p.jigsaw(3, 0, CELL - 1, 'south_up', EMPTY, ROOTED, name=PEN, target=PEN)
    mid = CELL // 2
    for i in range(1, CELL - 1):                                   # the fence, gate at south
        for x, z in ((i, 1), (1, i), (CELL - 2, i)):
            if not (z == 1 and x in (mid - 1, mid, mid + 1)):
                p.set(x, 1, z, FENCE, POST)
    p.box(2, 0, 2, CELL - 3, 0, CELL - 3, MOSS)
    p.set(mid, 1, mid, 'minecraft:spawner', None, mob_spawner('minecraft:mooshroom', 2))
    p.set(2, 1, CELL - 3, 'minecraft:hay_block', {'axis': 'z'})
    p.set(CELL - 3, 1, CELL - 3, 'minecraft:hay_block', {'axis': 'z'})
    for x, z in ((2, 2), (CELL - 3, 2)):
        p.set(x, 1, z, 'minecraft:red_mushroom')
    return p


def camp():
    """Beds, a table and a chest of bowls. The only room in this mod whose point is stopping."""
    p = burrow_room(['north'], floor=MOSS)
    p.jigsaw(3, 0, 0, 'north_up', EMPTY, ROOTED, name=CAMP, target=CAMP)
    mid = CELL // 2
    p.box(1, 0, 1, CELL - 2, 0, CELL - 2, PLANK)
    bed(p, 2, 1, 2, 'south')
    bed(p, CELL - 3, 1, 2, 'south')
    p.set(mid, 1, CELL - 2, *chest('grove_camp', 'north'))
    p.set(1, 1, CELL - 2, 'minecraft:crafting_table')
    p.set(CELL - 2, 1, CELL - 2, 'minecraft:barrel', {'facing': 'up', 'open': 'false'})
    p.set(mid, 1, mid, 'minecraft:campfire',
          {'facing': 'north', 'lit': 'true', 'signal_fire': 'false', 'waterlogged': 'false'})
    for x, z in ((1, 1), (CELL - 2, 1)):
        p.set(x, 1, z, LOG, {'axis': 'y'})
        p.set(x, 2, z, LOG, {'axis': 'y'})
    p.set(mid, 4, mid, SPORE)
    return p


def burrow_cap():
    p = Piece(1, CELL, CELL, ROOTED)
    for y in range(CELL):
        p.box(0, y, 0, 0, y, CELL - 1, STONE if y % 3 == 1 else ROOTED)
    p.jigsaw(0, 0, 3, 'west_up', POOL['burrow_caps'], ROOTED, name=BURROW, target=BURROW)
    return p


# ---------------------------------------------------------------------------------- pools
def element(location, weight):
    return ('    { "weight": %d, "element": { "element_type": "minecraft:single_pool_element",'
            '\n        "location": "%s:grove/%s", "projection": "rigid", '
            '"processors": "%s:grove_weathering" } }' % (weight, NS, location, NS))


def write_pool(name, elements, fallback):
    if not os.path.isdir(POOL_JSON):
        os.makedirs(POOL_JSON)
    text = ('{\n  "fallback": "%s",\n  "elements": [\n%s\n  ]\n}\n'
            % (fallback, ',\n'.join(elements)))
    with open(os.path.join(POOL_JSON, name + '.json'), 'w', encoding='utf-8', newline='\n') as f:
        f.write(text)


# ---------------------------------------------------------------------------------- checks
HANGS = {'minecraft:ladder', 'minecraft:glow_lichen', 'minecraft:hanging_roots',
         'minecraft:spore_blossom', 'minecraft:oak_fence', 'minecraft:moss_carpet',
         'minecraft:red_mushroom', 'minecraft:brown_mushroom', 'minecraft:pointed_dripstone',
         'minecraft:water'}
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
            if block.endswith('bed') or block.endswith('_mushroom') \
                    or block in ('minecraft:campfire', 'minecraft:crafting_table',
                                 'minecraft:composter', 'minecraft:barrel',
                                 'minecraft:hay_block'):
                if not solid((pos[0], pos[1] - 1, pos[2])):
                    problems.append('%s: the %s at %s stands on nothing'
                                    % (name, block.split(':')[-1], pos))
            if block.endswith('chest'):
                if 'LootTable' not in (piece.extra.get(pos) or {}):
                    problems.append('%s: the chest at %s has no loot table' % (name, pos))
                if not solid((pos[0], pos[1] - 1, pos[2])):
                    problems.append('%s: the chest at %s stands on nothing' % (name, pos))
    return problems


def ladder_problems(pieces):
    at = {'mouth': (0, 0, 0), 'shaft': (0, -SHAFT_H, 0),
          'hollow': (0, -SHAFT_H - CELL, 0)}
    cx, cz = HOLE
    cased = at['hollow'][1] + CELL - 1
    problems = []
    for y in range(at['hollow'][1] + 1, GROUND + 1):
        for dx in (-1, 0, 1):
            for dz in (-1, 0, 1):
                if (dx, dz) != (0, 0) and y < cased:
                    continue               # inside the hollow the ring is the room itself
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
                    problems.append('%s leaves %s at %s: the ring round the shaft has to be '
                                    'solid the whole way down (section 33)'
                                    % (name, block.split(':')[-1], (x, y, z)))
    return problems


def verify(pieces):
    problems = ladder_problems(pieces) + fitting_problems(pieces)
    for name, piece in pieces.items():
        if max(piece.size) > 48:
            problems.append('%s is %s: too big to rebuild by hand' % (name, piece.size))
        for entry in (PEN, CAMP):
            count = sum(1 for pos, (block, _) in piece.grid.items()
                        if block == 'minecraft:jigsaw'
                        and (piece.extra.get(pos) or {}).get('name') == entry)
            if count > 1:
                problems.append('%s carries %d jigsaws named %s; a piece placed by geometry '
                                'must carry exactly one (section 13)' % (name, count, entry))
        if any(block == 'minecraft:trial_spawner' for block, _ in piece.grid.values()):
            problems.append('%s has a trial spawner: this dungeon has no boss and gives no '
                            'signature, and a small one that pays out like a large one '
                            'breaks the promise that gear comes one piece per boss '
                            '(section 2.8)' % name)
    for line in problems:
        print('  PROBLEM  ' + line)
    if problems:
        raise SystemExit('the hollow does not hold together')
    print('  checked: the ladder unbroken from the mouth to the hollow, nothing hangs in '
          'mid-air, every chest has a table, no boss and no trial spawner')


def main():
    if not os.path.isdir(DST):
        os.makedirs(DST)
    pieces = {
        'mouth': mouth(), 'shaft': shaft(), 'hollow': hollow(),
        'pen': pen(), 'camp': camp(),
        'tunnel': burrow('tunnel'), 'bend': burrow('bend'), 'cross': burrow('cross'),
        'garden': burrow('garden'), 'grove': burrow('grove'), 'spring': burrow('spring'),
        'larder': burrow('larder'), 'drip': burrow('drip'),
        'cap': burrow_cap(),
    }
    verify(pieces)
    for name, piece in sorted(pieces.items()):
        piece.write(os.path.join(DST, name + '.nbt'))
        print('  %-16s %s' % (name, list(piece.size)))

    write_pool('start', [element('mouth', 1)], EMPTY)
    write_pool('down', [element('shaft', 1)], EMPTY)
    write_pool('first', [element('hollow', 1)], EMPTY)
    write_pool('pen', [element('pen', 1)], EMPTY)
    write_pool('camp', [element('camp', 1)], EMPTY)
    write_pool('burrows', [element('tunnel', 10), element('bend', 9),
                           element('cross', 4), element('garden', 8),
                           element('grove', 6), element('spring', 5),
                           element('larder', 6), element('drip', 5)],
               POOL['burrow_caps'])
    write_pool('burrow_caps', [element('cap', 1)], EMPTY)
    print('  pools -> %s' % os.path.relpath(POOL_JSON, ROOT))


if __name__ == '__main__':
    main()
