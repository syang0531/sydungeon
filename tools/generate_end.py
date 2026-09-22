# -*- coding: utf-8 -*-
"""The two end dungeons (docs/concepts.md section 6).

    python tools/generate_end.py        (or through make_pieces.py)

    spire    the void spire     - end highlands, a tower that climbs        (6.1)
    chorus   the chorus maze    - end midlands, a maze with no roof on it   (6.2)

TWO SHAPES, NOT ONE
Everything else in this mod goes down. The spire is the one that goes up: the same column of
ladder as every shaft (CLAUDE.md section 33) read the other way, with each storey hung off the
one below by an up jigsaw instead of a down one. The maze does neither - it lies on the
island with no roof at all, which is a thing only the end can get away with, because there is
nothing up there to rain on you.

WHERE THEY STAND
End highlands and midlands are the outer islands, so both are things you meet after the
dragon, which is what section 6 asks for. The heightmap works out here - the islands are
solid with sky over them - so unlike the nether these do project onto it, and they ask for
level ground because an island's edge is a cliff with the void under it.

THE VOID IS THE HAZARD AND IT NEEDS NO TRIGGER
No pressure plates, no tripwire (section 12). The drop off the maze's rim and the spire's
windows is exactly as dangerous to whatever wanders in first as it is to you.
"""
import io
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import nbt  # noqa: E402
from generate_pieces import Piece  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, 'src', 'main', 'resources', 'data', 'sydungeon')

NS = 'sydungeon'
EMPTY = 'minecraft:empty'
PRIORITY = 10
CELL = 7
WIDE = 21
STEPS = 3
FLOORS = 4                       # storeys between the spire's base and its crown
AIR = 'minecraft:air'
LADDER = 'minecraft:ladder'

END = 'minecraft:end_stone'
BRICK = 'minecraft:end_stone_bricks'
PURPUR = 'minecraft:purpur_block'
PILLAR = 'minecraft:purpur_pillar'
SLAB = 'minecraft:purpur_slab'
LAMP = 'minecraft:shroomlight'
LIGHT = 'minecraft:sea_lantern'
CHORUS = 'minecraft:chorus_plant'
FLOWER = 'minecraft:chorus_flower'
OBSIDIAN = 'minecraft:obsidian'

GRID = {'north': 'true', 'south': 'true', 'east': 'true', 'west': 'true',
        'waterlogged': 'false'}
ANY_LIGHT = {'block_light_limit': {'min_inclusive': nbt.Int(0), 'max_inclusive': nbt.Int(15)}}
TRIAL_STATE = {'trial_spawner_state': 'inactive', 'ominous': 'false'}

# the column, in the spire's coordinates: one ladder, the post east of it (section 33)
HOLE = (WIDE // 2, WIDE // 2)
JIG = (HOLE[0] + 1, HOLE[1])

UP = NS + ':spr_up'              # the spire's storeys, stacked
MAZE = NS + ':chr_way'           # the maze's corridors
BOSS = NS + ':chr_boss'          # its one branch, on its own name so it cannot run backwards


def chest(table, facing='north'):
    return ('minecraft:chest', {'facing': facing, 'type': 'single', 'waterlogged': 'false'},
            {'id': 'minecraft:chest', 'LootTable': '%s:chests/%s' % (NS, table)})


def spawner(entity, count=2):
    return ('minecraft:spawner', None,
            {'id': 'minecraft:mob_spawner',
             'SpawnData': {'entity': {'id': entity}, 'custom_spawn_rules': ANY_LIGHT},
             'Delay': nbt.Short(20), 'MinSpawnDelay': nbt.Short(240),
             'MaxSpawnDelay': nbt.Short(900), 'SpawnCount': nbt.Short(count),
             'MaxNearbyEntities': nbt.Short(5), 'RequiredPlayerRange': nbt.Short(14),
             'SpawnRange': nbt.Short(4)})


def trial(family, which):
    return ('minecraft:trial_spawner', TRIAL_STATE,
            {'id': 'minecraft:trial_spawner',
             'normal_config': '%s:%s/%s' % (NS, family, which),
             'ominous_config': '%s:%s/%s' % (NS, family, which),
             'target_cooldown_length': nbt.Int(2_000_000_000),
             'required_player_range': nbt.Int(14)})


def ladder(facing='west'):
    return (LADDER, {'facing': facing, 'waterlogged': 'false'})


def climb(p, y0, y1, post=PILLAR):
    """One column of ladder with the post it hangs on beside it (section 33). Upward here,
    but the column is the same column: walking into it is climbing it."""
    cx, cz = HOLE
    for y in range(y0, y1 + 1):
        p.set(cx + 1, y, cz, post, {'axis': 'y'} if post == PILLAR else None)
        p.set(cx, y, cz, *ladder())


# ---------------------------------------------------------------------------- the spire
def storey(y0, y1, p, windows=True):
    """A hollow box of end stone brick with purpur corners, and slits that look at nothing."""
    n = WIDE
    p.box(0, y0, 0, n - 1, y1, n - 1, BRICK)
    p.box(1, y0, 1, n - 2, y1, n - 2, AIR)
    for x, z in ((0, 0), (0, n - 1), (n - 1, 0), (n - 1, n - 1)):
        for y in range(y0, y1 + 1):
            p.set(x, y, z, PILLAR, {'axis': 'y'})
    if windows:
        for a in (5, n // 2, n - 6):
            for x, z in ((0, a), (n - 1, a), (a, 0), (a, n - 1)):
                p.box(x, y0 + 2, z, x, y0 + 3, z, AIR)


def base():
    """The start: the spire's ground floor, standing on the island. Its floor course is the
    island's own top block (section 30) and the climb starts here."""
    n = WIDE
    p = Piece(n, CELL, n, BRICK)
    p.box(0, 0, 0, n - 1, 0, n - 1, BRICK)
    storey(1, CELL - 1, p)
    p.box(0, 1, n // 2 - 1, 0, 4, n // 2 + 1, AIR)                # the way in, west
    p.box(1, CELL - 1, 1, n - 2, CELL - 1, n - 2, BRICK)          # and the ceiling over it
    climb(p, 1, CELL - 1)
    p.jigsaw(JIG[0], CELL - 1, JIG[1], 'up_east', '%s:spire/floor_1' % NS, PILLAR,
             joint='aligned', priority=PRIORITY, name=UP, target=UP)
    p.set(2, 1, 2, *chest('spire', 'east'))
    p.set(n - 3, 1, n - 3, *spawner('minecraft:endermite', 1))
    for x, z in ((3, n - 4), (n - 4, 3)):
        p.set(x, 1, z, LIGHT)
    return p


def floor(step):
    """One storey. The last of them calls the crown; the others call the next storey, which
    is how the spire is always five high (section 7, stood on its end)."""
    n = WIDE
    p = Piece(n, CELL, n, BRICK)
    storey(0, CELL - 1, p)
    p.box(1, 0, 1, n - 2, 0, n - 2, BRICK)                        # the floor you walk on:
    p.box(1, CELL - 1, 1, n - 2, CELL - 1, n - 2, BRICK)          # the climb cuts its own
    climb(p, 0, CELL - 1)                                         # hole through it (33)
    p.jigsaw(JIG[0], 0, JIG[1], 'down_east', EMPTY, PILLAR, joint='aligned',
             name=UP, target=UP)
    nxt = '%s:spire/floor_%d' % (NS, step + 1) if step < FLOORS else '%s:spire/crown' % NS
    p.jigsaw(JIG[0], CELL - 1, JIG[1], 'up_east', nxt, PILLAR, joint='aligned',
             priority=PRIORITY, name=UP, target=UP)
    mid = n // 2
    if step % 2:
        p.set(2, 1, 2, *chest('spire', 'east'))
        p.set(n - 3, 1, n - 3, LIGHT)
    else:
        p.set(n - 3, 1, 2, *spawner('minecraft:shulker', 1))
        p.set(2, 1, n - 3, LIGHT)
    for x, z in ((mid - 4, mid), (mid + 4, mid)):                 # a purpur rail, for looks
        for y in (1, 2):
            p.set(x, y, z, PURPUR)
    return p


def crown():
    """The top. Six shulkers and the thing this mod's last tier is for."""
    n = WIDE
    p = Piece(n, 14, n, BRICK)
    storey(0, 12, p, windows=False)
    for a in (5, n // 2, n - 6):                                  # tall slits, all four sides
        for x, z in ((0, a), (n - 1, a), (a, 0), (a, n - 1)):
            p.box(x, 3, z, x, 6, z, AIR)
    p.box(1, 0, 1, n - 2, 0, n - 2, BRICK)
    p.box(1, 13, 1, n - 2, 13, n - 2, SLAB, {'type': 'bottom', 'waterlogged': 'false'})
    # the climb first and the jigsaw second: the post goes through the same column, and the
    # other way round it rubs the jigsaw out (section 11)
    climb(p, 0, 1)
    p.jigsaw(JIG[0], 0, JIG[1], 'down_east', EMPTY, PILLAR, joint='aligned',
             name=UP, target=UP)
    mid = n // 2
    p.box(mid - 3, 1, mid - 3, mid + 3, 1, mid + 3, PURPUR)       # the dais
    p.box(mid - 2, 2, mid - 2, mid + 2, 2, mid + 2, BRICK)
    p.set(mid, 3, mid, *trial('spire', 'boss'))
    for x, z in ((4, 4), (4, n - 5), (n - 5, 4), (n - 5, n - 5)):
        p.set(x, 1, z, *trial('spire', 'guards'))
        for y in range(2, 12):
            p.set(x, y, z, PILLAR, {'axis': 'y'})
        p.set(x, 12, z, LAMP)
    return p


# ----------------------------------------------------------------------------- the maze
DOOR_AT = {'west': (0, 3, 'west_up'), 'east': (CELL - 1, 3, 'east_up'),
           'north': (3, 0, 'north_up'), 'south': (3, CELL - 1, 'south_up')}


def open_cell(doors, walls=5):
    """A cell of the maze: a floor, walls, and no roof. The end is the one place a dungeon
    can be open to the sky - there is no weather up here and nothing above to look down."""
    p = Piece(CELL, CELL, CELL, AIR)
    p.box(0, 0, 0, CELL - 1, 0, CELL - 1, BRICK)
    for x in range(CELL):
        for z in range(CELL):
            if x in (0, CELL - 1) or z in (0, CELL - 1):
                for y in range(1, walls + 1):
                    p.set(x, y, z, BRICK if (x + z + y) % 5 else PURPUR)
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


def way(p, side, pool, name=MAZE, target=MAZE, priority=0, size=CELL):
    x, z, orientation = DOOR_AT[side]
    if size != CELL:
        x = 0 if side == 'west' else size - 1 if side == 'east' else size // 2
        z = 0 if side == 'north' else size - 1 if side == 'south' else size // 2
    p.jigsaw(x, 0, z, orientation, pool, BRICK, priority=priority, name=name, target=target)


def plaza():
    """The maze's start: an open court with a pillar at each corner and four ways out."""
    n = WIDE
    p = Piece(n, CELL + 2, n, AIR)
    p.box(0, 0, 0, n - 1, 0, n - 1, BRICK)
    for x in range(n):
        for z in range(n):
            if x in (0, n - 1) or z in (0, n - 1):
                for y in range(1, 6):
                    p.set(x, y, z, BRICK if (x + z + y) % 5 else PURPUR)
    mid = n // 2
    for side in ('west', 'east', 'north', 'south'):
        if side == 'west':
            p.box(0, 1, mid - 1, 0, 4, mid + 1, AIR)
        elif side == 'east':
            p.box(n - 1, 1, mid - 1, n - 1, 4, mid + 1, AIR)
        elif side == 'north':
            p.box(mid - 1, 1, 0, mid + 1, 4, 0, AIR)
        else:
            p.box(mid - 1, 1, n - 1, mid + 1, 4, n - 1, AIR)
    way(p, 'west', '%s:chorus/ways' % NS, priority=PRIORITY, size=n)
    way(p, 'north', '%s:chorus/ways' % NS, priority=PRIORITY, size=n)
    way(p, 'east', '%s:chorus/ways' % NS, priority=PRIORITY, size=n)
    way(p, 'south', '%s:chorus/boss_1' % NS, target=BOSS, priority=PRIORITY, size=n)
    for x, z in ((4, 4), (4, n - 5), (n - 5, 4), (n - 5, n - 5)):  # four pillars and a light
        for y in range(1, 6):
            p.set(x, y, z, PILLAR, {'axis': 'y'})
        p.set(x, 6, z, LAMP)
    p.box(mid - 2, 1, mid - 2, mid + 2, 1, mid + 2, PURPUR)
    p.set(mid, 2, mid, *chest('chorus', 'south'))
    p.set(mid - 2, 2, mid - 2, *spawner('minecraft:enderman', 1))
    return p


def maze(kind):
    doors = {'run': ['west', 'east'], 'bend': ['west', 'south'],
             'fork': ['west', 'east', 'north', 'south'],
             'grove': ['west', 'east'], 'nest': ['west', 'east'],
             'vault': ['west']}[kind]
    p = open_cell(doors)
    for side in doors:
        way(p, side, '%s:chorus/ways' % NS)
    mid = CELL // 2
    if kind == 'run':
        p.set(1, 1, 1, PURPUR)
        p.set(CELL - 2, 1, CELL - 2, PURPUR)
    elif kind == 'bend':
        p.set(CELL - 2, 1, 1, PILLAR, {'axis': 'y'})
        p.set(CELL - 2, 2, 1, LAMP)
    elif kind == 'fork':
        for x, z in ((1, 1), (1, CELL - 2), (CELL - 2, 1), (CELL - 2, CELL - 2)):
            for y in (1, 2):
                p.set(x, y, z, PILLAR, {'axis': 'y'})
    elif kind == 'grove':
        # chorus growing out of the end stone, which is the only thing that grows up here
        for x, z in ((1, 1), (CELL - 2, CELL - 2)):
            p.set(x, 0, z, END)
            for y in range(1, 4):
                p.set(x, y, z, CHORUS, {'up': 'true', 'down': 'true', 'north': 'false',
                                        'south': 'false', 'east': 'false', 'west': 'false'})
            p.set(x, 4, z, FLOWER, {'age': '5'})
    elif kind == 'nest':
        # an endermite nest behind a low wall. It was a hole in the floor first, and the
        # floor is the piece's own bottom face - there is nothing under it to stand on
        for x in range(2, CELL - 2):
            p.set(x, 1, 2, PURPUR)
            p.set(x, 1, CELL - 3, PURPUR)
        p.set(mid, 1, mid, *spawner('minecraft:endermite', 1))
        p.set(mid, 0, mid, END)
    elif kind == 'vault':
        p.box(1, 1, 1, CELL - 2, 1, 1, PURPUR)
        p.set(mid, 2, 1, *chest('chorus', 'south'))
        p.set(1, 2, 1, LIGHT)
    return p


def maze_cap():
    p = Piece(1, CELL, CELL, BRICK)
    for y in range(CELL):
        for z in range(CELL):
            p.set(0, y, z, BRICK if y <= 5 else AIR)
    p.jigsaw(0, 0, 3, 'west_up', '%s:chorus/caps' % NS, BRICK, name=MAZE, target=MAZE)
    return p


def approach(step):
    p = open_cell(['west', 'east', 'north'])
    p.jigsaw(0, 0, 3, 'west_up', '%s:chorus/ways' % NS, BRICK, name=BOSS, target=MAZE)
    nxt = ('%s:chorus/boss_%d' % (NS, step + 1)) if step < STEPS else '%s:chorus/boss' % NS
    way(p, 'east', nxt, target=BOSS, priority=PRIORITY)
    way(p, 'north', '%s:chorus/ways' % NS)
    p.set(1, 1, 1, PILLAR, {'axis': 'y'})
    p.set(1, 2, 1, LAMP)
    return p


def sunken():
    """The maze's one roofed room, and the only fight in it: endermen, which is what the end
    has instead of a boss (section 6.2). Roofed on purpose - an enderman that can see the sky
    has somewhere to teleport to, and a trial spawner is not finished until what it spawned
    is dead (section 26)."""
    n = WIDE
    p = Piece(n, 14, n, BRICK)
    p.box(1, 1, 1, n - 2, 12, n - 2, AIR)
    p.box(0, 0, 0, n - 1, 0, n - 1, BRICK)
    p.box(1, 13, 1, n - 2, 13, n - 2, SLAB, {'type': 'bottom', 'waterlogged': 'false'})
    p.jigsaw(0, 0, n // 2, 'west_up', EMPTY, BRICK, name=BOSS, target=MAZE)
    p.box(0, 1, n // 2 - 1, 0, 4, n // 2 + 1, AIR)
    mid = n // 2
    for x, z in ((4, 4), (4, n - 5), (n - 5, 4), (n - 5, n - 5)):
        for y in range(1, 12):
            p.set(x, y, z, PILLAR, {'axis': 'y'})
        p.set(x, 12, z, LAMP)
    p.box(mid - 3, 1, 3, mid + 3, 1, 8, PURPUR)
    p.box(mid - 2, 2, 4, mid + 2, 2, 7, BRICK)
    p.set(mid, 3, 5, *trial('chorus', 'boss'))
    for x, z in ((5, 12), (n - 6, 12), (5, n - 4), (n - 6, n - 4)):
        p.set(x, 1, z, *trial('chorus', 'guards'))
    for x, z in ((mid, 11), (4, mid), (n - 5, mid)):
        p.set(x, 1, z, OBSIDIAN)
    return p


def build():
    out = {'spire': {'base': base(), 'crown': crown()},
           'chorus': {'plaza': plaza(), 'cap': maze_cap(), 'hall': sunken(),
                      **{k: maze(k) for k in
                         ('run', 'bend', 'fork', 'grove', 'nest', 'vault')}}}
    for step in range(1, FLOORS + 1):
        out['spire']['floor_%d' % step] = floor(step)
    for step in range(1, STEPS + 1):
        out['chorus']['approach_%d' % step] = approach(step)
    return out


# --------------------------------------------------------------------------------- checks
HANGS = {LADDER, 'minecraft:iron_bars', CHORUS, FLOWER, LIGHT, LAMP}
AROUND = ((1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1))
BEHIND = {'north': (0, 0, 1), 'south': (0, 0, -1), 'east': (-1, 0, 0), 'west': (1, 0, 0)}
STANDS_ON = ('minecraft:spawner', 'minecraft:trial_spawner')


def problems_in(family, pieces):
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
                problems.append('%s/%s: %s floats at %s'
                                % (family, name, block.split(':')[-1], pos))
            if block == LADDER:
                d = BEHIND[props.get('facing', 'north')]
                if not solid((pos[0] + d[0], pos[1] + d[1], pos[2] + d[2])):
                    problems.append('%s/%s: the ladder at %s has nothing behind it'
                                    % (family, name, pos))
            if block in STANDS_ON or block.endswith('chest'):
                if not solid((pos[0], pos[1] - 1, pos[2])):
                    problems.append('%s/%s: the %s at %s stands on nothing'
                                    % (family, name, block.split(':')[-1], pos))
            if block.endswith('chest') and 'LootTable' not in (piece.extra.get(pos) or {}):
                problems.append('%s/%s: the chest at %s has no loot table' % (family, name, pos))
        if max(size) > 48:
            problems.append('%s/%s is %s: too big to rebuild by hand' % (family, name, size))
    return problems


def spire_problems(pieces):
    """Climb the spire the way the game stacks it: base, four storeys, the crown. The offsets
    come from the jigsaws, not from a table - which is the lesson the swamp taught (33)."""
    order = ['base'] + ['floor_%d' % i for i in range(1, FLOORS + 1)] + ['crown']
    problems, at, world = [], 0, {}
    for i, name in enumerate(order):
        piece = pieces[name]
        for pos, (block, _) in piece.grid.items():
            world[(pos[0], pos[1] + at, pos[2])] = block
        if i + 1 < len(order):
            ups = [pos for pos in piece.extra
                   if (piece.extra[pos] or {}).get('id') == 'minecraft:jigsaw'
                   and dict(piece.grid[pos][1] or ()).get('orientation') == 'up_east']
            downs = [pos for pos in pieces[order[i + 1]].extra
                     if (pieces[order[i + 1]].extra[pos] or {}).get('id') == 'minecraft:jigsaw'
                     and dict(pieces[order[i + 1]].grid[pos][1] or ()).get('orientation')
                     == 'down_east']
            if len(ups) != 1 or len(downs) != 1:
                problems.append('%s has %d up jigsaws and %s has %d down: the stack is not '
                                'pinned' % (name, len(ups), order[i + 1], len(downs)))
                return problems
            at += ups[0][1] + 1 - downs[0][1]
    cx, cz = HOLE
    ladders = sorted(y for (x, y, z) in world if (x, z) == (cx, cz)
                     and world[(x, y, z)] == LADDER)
    if ladders != list(range(ladders[0], ladders[-1] + 1)):
        gap = next(y for y in range(ladders[0], ladders[-1]) if y + 1 not in ladders) + 1
        problems.append('the climb up the spire stops at y=%d (%s)'
                        % (gap, (world.get((cx, gap, cz)) or 'nothing').split(':')[-1]))
    return problems


# ----------------------------------------------------------------------------------- data
def put(rel, obj):
    path = os.path.join(DATA, rel)
    if not os.path.isdir(os.path.dirname(path)):
        os.makedirs(os.path.dirname(path))
    with io.open(path, 'w', encoding='utf-8', newline='\n') as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)
        f.write('\n')


def item(name, **kw):
    e = {'type': 'minecraft:item',
         'name': name if ':' in name else 'minecraft:' + name}
    e.update(kw)
    return e


def count(lo, hi=None):
    n = lo if hi is None else {'type': 'minecraft:uniform', 'min': lo, 'max': hi}
    return {'function': 'minecraft:set_count', 'count': n}


def enchant(lo, hi):
    return {'function': 'minecraft:enchant_with_levels',
            'levels': {'type': 'minecraft:uniform', 'min': lo, 'max': hi}}


def with_enchants(name, **levels):
    return item(name, functions=[{
        'function': 'minecraft:set_components',
        'components': {'minecraft:enchantments':
                       {'minecraft:' + k: v for k, v in levels.items()}}}])


KEEP = {'rolls': 1, 'entries': [
    item('chorus_fruit', weight=8, functions=[count(4, 10)]),
    item('ender_pearl', weight=6, functions=[count(2, 5)]),
    item('cooked_beef', weight=5, functions=[count(2, 5)]),
    item('golden_apple', weight=3),
    item('experience_bottle', weight=5, functions=[count(3, 8)]),
    item('purpur_block', weight=4, functions=[count(4, 10)])]}


def write_data():
    put('loot_table/chests/spire.json', {'type': 'minecraft:chest', 'pools': [KEEP,
        {'rolls': {'type': 'minecraft:uniform', 'min': 2, 'max': 3}, 'entries': [
            item('ender_pearl', weight=7, functions=[count(2, 6)]),
            item('popped_chorus_fruit', weight=6, functions=[count(3, 8)]),
            item('shulker_shell', weight=3),
            item('diamond', weight=4, functions=[count(1, 3)]),
            item('enchanted_book', weight=4, functions=[enchant(22, 30)]),
            item('experience_bottle', weight=5, functions=[count(4, 9)]),
            item('obsidian', weight=4, functions=[count(2, 6)])]}]})
    put('loot_table/chests/chorus.json', {'type': 'minecraft:chest', 'pools': [KEEP,
        {'rolls': {'type': 'minecraft:uniform', 'min': 2, 'max': 3}, 'entries': [
            item('ender_pearl', weight=8, functions=[count(3, 7)]),
            item('chorus_flower', weight=5, functions=[count(1, 3)]),
            item('end_stone_bricks', weight=5, functions=[count(6, 14)]),
            item('obsidian', weight=5, functions=[count(3, 8)]),
            item('diamond', weight=3, functions=[count(1, 3)]),
            item('enchanted_book', weight=4, functions=[enchant(22, 30)]),
            item('experience_bottle', weight=5, functions=[count(4, 9)])]}]})

    # the signatures, as the first pools of the bosses' own tables: never a matter of luck
    put('loot_table/trial/spire_reward.json', {'type': 'minecraft:chest', 'pools': [
        {'rolls': 1, 'entries': [item('elytra')]},
        {'rolls': 1, 'entries': [item('shulker_shell', functions=[count(2)])]},
        {'rolls': 1, 'entries': [with_enchants('diamond_pickaxe', efficiency=4,
                                               unbreaking=3),
                                 with_enchants('diamond_sword', sharpness=4, looting=2)]},
        {'rolls': {'type': 'minecraft:uniform', 'min': 2, 'max': 3}, 'entries': [
            item('dragon_breath', weight=5, functions=[count(2, 5)]),
            item('shulker_shell', weight=4, functions=[count(1, 2)]),
            item('ender_pearl', weight=5, functions=[count(4, 9)]),
            item('experience_bottle', weight=6, functions=[count(10, 20)]),
            item('enchanted_book', weight=4, functions=[enchant(26, 30)]),
            item('diamond', weight=4, functions=[count(2, 6)])]}]})
    put('loot_table/trial/chorus_reward.json', {'type': 'minecraft:chest', 'pools': [
        {'rolls': 1, 'entries': [item('ender_pearl', functions=[count(16)])]},
        {'rolls': 1, 'entries': [item('obsidian', functions=[count(8)])]},
        {'rolls': 1, 'entries': [with_enchants('diamond_chestplate', protection=4,
                                               unbreaking=3),
                                 with_enchants('diamond_boots', feather_falling=4,
                                               unbreaking=3)]},
        {'rolls': {'type': 'minecraft:uniform', 'min': 2, 'max': 3}, 'entries': [
            item('chorus_flower', weight=5, functions=[count(2, 4)]),
            item('experience_bottle', weight=6, functions=[count(8, 16)]),
            item('enchanted_book', weight=4, functions=[enchant(24, 30)]),
            item('diamond', weight=4, functions=[count(2, 5)]),
            item('ender_eye', weight=3, functions=[count(1, 3)])]}]})
    for family in ('spire', 'chorus'):
        put('loot_table/trial/%s_guard_reward.json' % family,
            {'type': 'minecraft:chest', 'pools': [{'rolls': 1, 'entries': [
                item('ender_pearl', weight=6, functions=[count(1, 4)]),
                item('experience_bottle', weight=5, functions=[count(3, 7)]),
                item('chorus_fruit', weight=5, functions=[count(3, 7)]),
                item('shulker_shell', weight=2),
                item('diamond', weight=2)]}]})

    put('trial_spawner/spire/boss.json', {
        'spawn_range': 6, 'total_mobs': 6.0, 'simultaneous_mobs': 3.0,
        'total_mobs_added_per_player': 2.0, 'simultaneous_mobs_added_per_player': 1.0,
        'ticks_between_spawn': 60,
        'spawn_potentials': [{'weight': 1, 'data': {'entity': {
            'id': 'minecraft:shulker', 'CustomName': '첨탑의 심장',
            'CustomNameVisible': True, 'PersistenceRequired': True, 'Health': 50.0,
            'attributes': [{'id': 'minecraft:max_health', 'base': 50.0},
                           {'id': 'minecraft:armor', 'base': 12.0}]}}}],
        'loot_tables_to_eject': [{'weight': 1, 'data': '%s:trial/spire_reward' % NS}]})
    put('trial_spawner/spire/guards.json', {
        'spawn_range': 5, 'total_mobs': 6.0, 'simultaneous_mobs': 2.0,
        'total_mobs_added_per_player': 2.0, 'simultaneous_mobs_added_per_player': 1.0,
        'ticks_between_spawn': 40,
        'spawn_potentials': [
            {'weight': 4, 'data': {'entity': {'id': 'minecraft:shulker',
                                              'PersistenceRequired': True}}},
            {'weight': 3, 'data': {'entity': {'id': 'minecraft:enderman',
                                              'PersistenceRequired': True}}},
            {'weight': 2, 'data': {'entity': {'id': 'minecraft:endermite',
                                              'PersistenceRequired': True}}}],
        'loot_tables_to_eject': [{'weight': 1, 'data': '%s:trial/spire_guard_reward' % NS}]})
    put('trial_spawner/chorus/boss.json', {
        'spawn_range': 5, 'total_mobs': 8.0, 'simultaneous_mobs': 3.0,
        'total_mobs_added_per_player': 2.0, 'simultaneous_mobs_added_per_player': 1.0,
        'ticks_between_spawn': 40,
        'spawn_potentials': [{'weight': 1, 'data': {'entity': {
            'id': 'minecraft:enderman', 'PersistenceRequired': True, 'Health': 60.0,
            'attributes': [{'id': 'minecraft:max_health', 'base': 60.0},
                           {'id': 'minecraft:armor', 'base': 6.0}]}}}],
        'loot_tables_to_eject': [{'weight': 1, 'data': '%s:trial/chorus_reward' % NS}]})
    put('trial_spawner/chorus/guards.json', {
        'spawn_range': 4, 'total_mobs': 6.0, 'simultaneous_mobs': 2.0,
        'total_mobs_added_per_player': 2.0, 'simultaneous_mobs_added_per_player': 1.0,
        'ticks_between_spawn': 40,
        'spawn_potentials': [
            {'weight': 5, 'data': {'entity': {'id': 'minecraft:enderman',
                                              'PersistenceRequired': True}}},
            {'weight': 3, 'data': {'entity': {'id': 'minecraft:endermite',
                                              'PersistenceRequired': True}}}],
        'loot_tables_to_eject': [{'weight': 1, 'data': '%s:trial/chorus_guard_reward' % NS}]})

    put('tags/worldgen/biome/has_structure/spire.json',
        {'values': ['minecraft:end_highlands']})
    put('tags/worldgen/biome/has_structure/chorus.json',
        {'values': ['minecraft:end_midlands']})

    for key, drop in (('spire', 12), ('chorus', 14)):
        put('worldgen/structure/%s.json' % key, {
            'type': 'sydungeon:ranged_jigsaw',
            'biomes': '#sydungeon:has_structure/%s' % key,
            'step': 'surface_structures',
            'terrain_adaptation': 'beard_thin',
            'spawn_overrides': {},
            'start_pool': '%s:%s/start' % (NS, key),
            'size': {'type': 'minecraft:uniform', 'min_inclusive': 8, 'max_inclusive': 16},
            'start_height': {'absolute': 0},
            'project_start_to_heightmap': 'WORLD_SURFACE_WG',
            'max_distance_from_center': {'horizontal': 56, 'vertical': 64},
            'use_expansion_hack': False,
            'liquid_settings': 'ignore_waterlogging',
            'dimension_padding': {'bottom': 8, 'top': 8},
            'level_ground_drop': drop,
            'level_ground_radius': 10})

    # vanilla's end cities are out here too; a different salt and a zone kept clear of them
    for key, spacing, separation in (('spire', 30, 10), ('chorus', 36, 12)):
        put('worldgen/structure_set/%ss.json' % key, {
            'placement': {'type': 'minecraft:random_spread',
                          'spacing': spacing, 'separation': separation,
                          'salt': 62000000 + sum(ord(c) for c in key) * 5147,
                          'exclusion_zone': {'other_set': 'minecraft:end_cities',
                                             'chunk_count': 8}},
            'structures': [{'structure': '%s:%s' % (NS, key), 'weight': 1}]})

    for key in ('spire', 'chorus'):
        put('worldgen/processor_list/%s_weathering.json' % key, {'processors': [
            {'processor_type': 'minecraft:rule', 'rules': [
                {'input_predicate': {'predicate_type': 'minecraft:random_block_match',
                                     'block': BRICK, 'probability': 0.10},
                 'location_predicate': {'predicate_type': 'minecraft:always_true'},
                 'output_state': {'Name': PURPUR}},
                {'input_predicate': {'predicate_type': 'minecraft:random_block_match',
                                     'block': PURPUR, 'probability': 0.08},
                 'location_predicate': {'predicate_type': 'minecraft:always_true'},
                 'output_state': {'Name': END}}]}]})


def element(family, location, weight):
    return ('    { "weight": %d, "element": { "element_type": "minecraft:single_pool_element",'
            '\n        "location": "%s:%s/%s", "projection": "rigid", '
            '"processors": "%s:%s_weathering" } }'
            % (weight, NS, family, location, NS, family))


def write_pools():
    pools = {
        'spire': {
            'start': ([element('spire', 'base', 1)], EMPTY),
            'crown': ([element('spire', 'crown', 1)], EMPTY),
            **{'floor_%d' % i: ([element('spire', 'floor_%d' % i, 1)], EMPTY)
               for i in range(1, FLOORS + 1)},
        },
        'chorus': {
            'start': ([element('chorus', 'plaza', 1)], EMPTY),
            'caps': ([element('chorus', 'cap', 1)], EMPTY),
            'ways': ([element('chorus', 'run', 10), element('chorus', 'bend', 9),
                      element('chorus', 'fork', 5), element('chorus', 'grove', 6),
                      element('chorus', 'nest', 5), element('chorus', 'vault', 6)],
                     '%s:chorus/caps' % NS),
            'boss': ([element('chorus', 'hall', 1),
                      element('chorus', 'approach_%d' % STEPS, 1)], '%s:chorus/caps' % NS),
            **{'boss_%d' % i: ([element('chorus', 'approach_%d' % i, 1)],
                               '%s:chorus/caps' % NS) for i in range(1, STEPS + 1)},
        },
    }
    for family, table in pools.items():
        out = os.path.join(DATA, 'worldgen', 'template_pool', family)
        if not os.path.isdir(out):
            os.makedirs(out)
        for name, (elements, fallback) in table.items():
            text = ('{\n  "fallback": "%s",\n  "elements": [\n%s\n  ]\n}\n'
                    % (fallback, ',\n'.join(elements)))
            with io.open(os.path.join(out, name + '.json'), 'w', encoding='utf-8',
                         newline='\n') as f:
                f.write(text)


def main():
    families = build()
    problems = []
    for family, pieces in families.items():
        problems += problems_in(family, pieces)
    problems += spire_problems(families['spire'])
    for line in problems:
        print('  PROBLEM  ' + line)
    if problems:
        raise SystemExit('the end dungeons do not hold together')
    built = 0
    for family, pieces in families.items():
        dst = os.path.join(DATA, 'structure', family)
        if not os.path.isdir(dst):
            os.makedirs(dst)
        for name, piece in sorted(pieces.items()):
            piece.write(os.path.join(dst, name + '.nbt'))
            built += 1
        print('  %-7s %d pieces' % (family, len(pieces)))
    write_pools()
    write_data()
    print('  checked: %d pieces, nothing hangs in mid-air, every chest has a table, and the '
          'spire climbs unbroken from its floor to the crown' % built)


if __name__ == '__main__':
    main()
