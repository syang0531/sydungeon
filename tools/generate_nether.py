# -*- coding: utf-8 -*-
"""The three nether dungeons: one machine, a skin each (docs/concepts.md section 5).

    python tools/generate_nether.py        (or through make_pieces.py)

    fort      the blaze fortress   - nether wastes, basalt deltas   (5.1)
    vault     the piglin vault     - crimson and warped forest      (5.2)
    sanctum   the soul sanctum     - soul sand valley               (5.3)

NO HEIGHTMAP DOWN HERE
The nether has no surface: `WORLD_SURFACE_WG` measures to the bedrock roof, so projecting a
start piece onto it would hang every dungeon from the ceiling. Vanilla's bastion does the
only thing that works - `start_height` as a plain range and no projection - and so do these.
The start is dropped into the rock at a height and the pieces carve their own room out of it,
which is what a fortress buried in netherrack is.

THE GHASTS ARE NOT HERE
Concept 5.3 wanted ghasts in the sanctum's boss fight. A ghast's fireball breaks blocks, and
the blocks it would break are the hall being fought in - the same objection as the pyramid's
TNT (CLAUDE.md section 12), arriving from a different direction. The sanctum's voice is a
wither skeleton with its own waves instead, and the ghast tears are in the chests.

EVERYTHING ELSE IS THE RULES AS THEY STAND
One column of ladder where there is a ladder at all (section 33), shells of the ground's own
banded rock (5.2), a boss on a chain of single-element pools with priority so it is placed
before the maze (7), lava walled in on five sides (28), and no trigger traps (12).
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
GATE = 21
BOSS = (21, 14, 21)
STEPS = 3                        # how many corridors the boss is forced behind (section 7)
AIR = 'minecraft:air'
LAVA = 'minecraft:lava'
SOURCE = {'level': '0'}
GRID = {'north': 'true', 'south': 'true', 'east': 'true', 'west': 'true',
        'waterlogged': 'false'}
HANGING = {'hanging': 'true', 'waterlogged': 'false'}
STANDING = {'hanging': 'false', 'waterlogged': 'false'}
ANY_LIGHT = {'block_light_limit': {'min_inclusive': nbt.Int(0), 'max_inclusive': nbt.Int(15)}}
TRIAL_STATE = {'trial_spawner_state': 'inactive', 'ominous': 'false'}

SKINS = [
    dict(key='fort', title='불꽃 요소', boss='화염의 군주',
         biomes=['nether_wastes', 'basalt_deltas'],
         rock='netherrack', band='basalt', brick='nether_bricks',
         trim='chiseled_nether_bricks', floor='blackstone', light='shroomlight',
         mob='minecraft:blaze', special='forge', spacing=32, separation=10),
    dict(key='vault', title='피글린 금고', boss='금고지기',
         biomes=['crimson_forest', 'warped_forest'],
         rock='netherrack', band='blackstone', brick='polished_blackstone_bricks',
         trim='chiseled_polished_blackstone', floor='gilded_blackstone',
         light='glowstone', mob='minecraft:piglin_brute', special='strongroom',
         spacing=36, separation=12),
    dict(key='sanctum', title='영혼 성소', boss='성소의 목소리',
         biomes=['soul_sand_valley'],
         rock='netherrack', band='soul_soil', brick='polished_basalt',
         trim='bone_block', floor='soul_soil', light='soul_lantern',
         mob='minecraft:wither_skeleton', special='ossuary', spacing=40, separation=14),
]

CELLS = ('passage', 'corner', 'cross', 'guard', 'span', 'store')


def mc(name):
    return name if ':' in name else 'minecraft:' + name


def B(skin):
    return {k: mc(skin[k]) for k in ('rock', 'band', 'brick', 'trim', 'floor', 'light')}


def pool(skin, name):
    return '%s:%s/%s' % (NS, skin['key'], name)


def door_name(skin):
    return '%s:%s_door' % (NS, skin['key'])


def boss_name(skin):
    return '%s:%s_boss' % (NS, skin['key'])


def chest(skin, facing='north', table=None):
    return ('minecraft:chest', {'facing': facing, 'type': 'single', 'waterlogged': 'false'},
            {'id': 'minecraft:chest',
             'LootTable': '%s:chests/%s' % (NS, table or skin['key'])})


def spawner(entity, count=2):
    return ('minecraft:spawner', None,
            {'id': 'minecraft:mob_spawner',
             'SpawnData': {'entity': {'id': entity}, 'custom_spawn_rules': ANY_LIGHT},
             'Delay': nbt.Short(20), 'MinSpawnDelay': nbt.Short(240),
             'MaxSpawnDelay': nbt.Short(900), 'SpawnCount': nbt.Short(count),
             'MaxNearbyEntities': nbt.Short(5), 'RequiredPlayerRange': nbt.Short(14),
             'SpawnRange': nbt.Short(4)})


def trial(skin, which):
    return ('minecraft:trial_spawner', TRIAL_STATE,
            {'id': 'minecraft:trial_spawner',
             'normal_config': '%s:%s/%s' % (NS, skin['key'], which),
             'ominous_config': '%s:%s/%s' % (NS, skin['key'], which),
             'target_cooldown_length': nbt.Int(2_000_000_000),
             'required_player_range': nbt.Int(14)})


def bedrock(p, skin, sy, at=0):
    """The nether's own rock, banded: what an exposed piece reads as (section 5.2)."""
    b = B(skin)
    sx, _, sz = p.size
    for y in range(sy):
        p.box(0, y, 0, sx - 1, y, sz - 1, b['rock'] if (y + at) % 4 else b['band'])


# --------------------------------------------------------------------------------- rooms
DOOR_AT = {'west': (0, 3, 'west_up'), 'east': (CELL - 1, 3, 'east_up'),
           'north': (3, 0, 'north_up'), 'south': (3, CELL - 1, 'south_up')}


def room(skin, doors, size=CELL, height=CELL):
    b = B(skin)
    p = Piece(size, height, size, b['rock'])
    bedrock(p, skin, height)
    p.box(1, 1, 1, size - 2, height - 2, size - 2, AIR)
    p.box(0, 0, 0, size - 1, 0, size - 1, b['floor'])
    mid = size // 2
    for side in doors:
        if side == 'west':
            p.box(0, 1, mid - 1, 0, 4, mid + 1, AIR)
        elif side == 'east':
            p.box(size - 1, 1, mid - 1, size - 1, 4, mid + 1, AIR)
        elif side == 'north':
            p.box(mid - 1, 1, 0, mid + 1, 4, 0, AIR)
        else:
            p.box(mid - 1, 1, size - 1, mid + 1, 4, size - 1, AIR)
    return p


def door(p, skin, side, pool_id, name=None, target=None, priority=0, size=CELL):
    x, z, orientation = DOOR_AT[side]
    if size != CELL:
        x = 0 if side == 'west' else size - 1 if side == 'east' else size // 2
        z = 0 if side == 'north' else size - 1 if side == 'south' else size // 2
    p.jigsaw(x, 0, z, orientation, pool_id, B(skin)['rock'], priority=priority,
             name=name or door_name(skin), target=target or door_name(skin))


def gate(skin):
    """The start. There is no surface in the nether, so this is simply the room the dungeon
    begins in: three ways into the corridors and one, placed first, to the boss."""
    b = B(skin)
    n = GATE
    p = room(skin, [], size=n, height=n)
    mid = n // 2
    p.box(1, 1, 1, n - 2, 9, n - 2, AIR)                          # a hall, ten high
    p.box(1, 10, 1, n - 2, n - 2, n - 2, b['rock'])
    for x, z in ((4, 4), (4, n - 5), (n - 5, 4), (n - 5, n - 5)):  # four columns
        for y in range(1, 10):
            p.set(x, y, z, b['brick'] if y % 4 else b['trim'])
        p.set(x, 9, z, b['light'])
    for side in ('west', 'east', 'north', 'south'):                # the four ways out
        if side == 'west':
            p.box(0, 1, mid - 1, 0, 4, mid + 1, AIR)
        elif side == 'east':
            p.box(n - 1, 1, mid - 1, n - 1, 4, mid + 1, AIR)
        elif side == 'north':
            p.box(mid - 1, 1, 0, mid + 1, 4, 0, AIR)
        else:
            p.box(mid - 1, 1, n - 1, mid + 1, 4, n - 1, AIR)
    door(p, skin, 'west', pool(skin, 'cells'), priority=PRIORITY, size=n)
    door(p, skin, 'east', pool(skin, 'cells'), priority=PRIORITY, size=n)
    door(p, skin, 'north', pool(skin, 'cells'), priority=PRIORITY, size=n)
    door(p, skin, 'south', pool(skin, 'boss_1'), target=boss_name(skin),
         priority=PRIORITY, size=n)
    p.box(mid - 2, 1, 2, mid + 2, 1, 3, b['trim'])                 # a dais and a chest
    p.set(mid, 2, 2, *chest(skin, 'south'))
    p.set(mid - 2, 2, 2, b['light'])
    p.set(mid + 2, 2, 2, b['light'])
    p.set(3, 1, n - 4, *spawner(skin['mob'], 1))
    return p


def cell(skin, kind):
    b = B(skin)
    doors = {'passage': ['west', 'east'], 'corner': ['west', 'south'],
             'cross': ['west', 'east', 'north', 'south'],
             'guard': ['west', 'east', 'north', 'south'],
             'span': ['west', 'east'], 'store': ['west']}[kind]
    p = room(skin, doors)
    for side in doors:
        door(p, skin, side, pool(skin, 'cells'))
    mid = CELL // 2
    if kind == 'passage':
        for z in (1, CELL - 2):
            p.set(1, 1, z, b['brick'])
        p.set(CELL - 2, CELL - 2, mid, b['light'])
    elif kind == 'corner':
        p.set(CELL - 2, 1, 1, b['trim'])
        p.set(CELL - 2, 2, 1, b['light'])
    elif kind == 'cross':
        for x, z in ((1, 1), (1, CELL - 2), (CELL - 2, 1), (CELL - 2, CELL - 2)):
            for y in (1, 2, 3):
                p.set(x, y, z, b['brick'])
        p.set(mid, CELL - 2, mid, b['light'])
    elif kind == 'guard':
        p.box(mid - 1, 0, mid - 1, mid + 1, 0, mid + 1, b['trim'])
        p.set(mid, 1, mid, *spawner(skin['mob'], 1))
        p.set(1, 1, 1, 'minecraft:iron_bars', GRID)
    elif kind == 'span':
        # a channel of lava with a walkway over it: no trigger, and as dangerous to whatever
        # wanders in first as it is to you (section 12). Walled in on five sides (section 28)
        p.box(1, 1, 1, CELL - 2, 1, 1, LAVA, SOURCE)
        p.box(1, 1, 2, CELL - 2, 1, 2, b['brick'])
        p.box(1, 1, CELL - 2, CELL - 2, 1, CELL - 2, LAVA, SOURCE)
        p.box(1, 1, CELL - 3, CELL - 2, 1, CELL - 3, b['brick'])
        p.set(mid, CELL - 2, mid, b['light'])
    elif kind == 'store':
        p.box(1, 1, 1, CELL - 2, 1, 1, b['trim'])
        p.set(mid, 2, 1, *chest(skin, 'south'))
        p.set(1, 2, 1, b['light'])
        p.set(CELL - 2, 1, CELL - 2, 'minecraft:barrel',
              {'facing': 'up', 'open': 'false'})
    return p


def special(skin):
    """The one room each of them has that the others do not."""
    b = B(skin)
    kind = skin['special']
    p = room(skin, ['west', 'east'])
    for side in ('west', 'east'):
        door(p, skin, side, pool(skin, 'cells'))
    mid = CELL // 2
    if kind == 'forge':          # the blaze fortress: a lava trough and furnaces
        # along the NORTH wall, where this cell has no doorway: the west one would have
        # poured it straight out into the corridor
        p.box(1, 1, 1, CELL - 2, 1, 1, LAVA, SOURCE)
        p.box(1, 1, 2, CELL - 2, 1, 2, b['brick'])
        for x in (2, CELL - 3):
            p.set(x, 1, CELL - 2, 'minecraft:blast_furnace',
                  {'facing': 'north', 'lit': 'true'})
        p.set(mid, 1, CELL - 2, *chest(skin, 'north'))
        p.set(mid, CELL - 2, mid, b['light'])
    elif kind == 'strongroom':   # the piglin vault: gold in the walls, and what guards it
        for x in (1, CELL - 2):
            for y in (1, 2, 3):
                p.set(x, y, 1, 'minecraft:gold_block')
        p.set(mid, 1, 1, *chest(skin, 'south'))
        p.set(mid, 3, 1, 'minecraft:gold_block')
        p.set(mid, 1, CELL - 2, *spawner('minecraft:piglin', 1))
        p.set(mid, CELL - 2, mid, b['light'])
    else:                        # the soul sanctum: a bone shelf and blue fire under glass
        for x in (1, CELL - 2):
            for y in (1, 2):
                p.box(x, y, 1, x, y, CELL - 2, 'minecraft:bone_block', {'axis': 'z'})
        p.set(mid, 1, CELL - 2, *chest(skin, 'north'))
        p.set(mid, 1, mid, 'minecraft:soul_sand')
        p.set(mid, 2, mid, 'minecraft:soul_fire')
        p.set(mid, CELL - 2, mid, b['light'])
    return p


def cap(skin):
    b = B(skin)
    p = Piece(1, CELL, CELL, b['rock'])
    bedrock(p, skin, CELL)
    p.jigsaw(0, 0, 3, 'west_up', pool(skin, 'caps'), b['rock'],
             name=door_name(skin), target=door_name(skin))
    return p


def approach(skin, step):
    """One link of the chain that holds the boss away from the start (section 7)."""
    p = room(skin, ['west', 'east', 'north'])
    p.jigsaw(0, 0, 3, 'west_up', pool(skin, 'cells'), B(skin)['rock'],
             name=boss_name(skin), target=door_name(skin))
    nxt = 'boss_%d' % (step + 1) if step < STEPS else 'boss'
    door(p, skin, 'east', pool(skin, nxt), target=boss_name(skin), priority=PRIORITY)
    door(p, skin, 'north', pool(skin, 'cells'))
    p.set(1, 1, 1, B(skin)['light'])
    return p


def hall(skin):
    """The boss. Four columns, the trial spawner on a dais, four more in the corners, and a
    channel of lava down one side with a rail of brick between it and the floor."""
    b = B(skin)
    sx, sy, sz = BOSS
    p = Piece(sx, sy, sz, b['rock'])
    bedrock(p, skin, sy)
    p.box(1, 1, 1, sx - 2, sy - 2, sz - 2, AIR)
    p.box(0, 0, 0, sx - 1, 0, sz - 1, b['floor'])
    p.jigsaw(0, 0, sz // 2, 'west_up', EMPTY, b['rock'], name=boss_name(skin),
             target=door_name(skin))
    p.box(0, 1, sz // 2 - 1, 0, 4, sz // 2 + 1, AIR)

    c = sx // 2
    for x0, z0 in ((4, 4), (4, sz - 6), (sx - 6, 4), (sx - 6, sz - 6)):
        for y in range(1, sy - 1):
            p.box(x0, y, z0, x0 + 1, y, z0 + 1, b['brick'] if y % 4 else b['trim'])
    p.box(c - 3, 1, 3, c + 3, 1, 8, b['trim'])                     # the dais
    p.box(c - 2, 2, 4, c + 2, 2, 7, b['brick'])
    p.set(c, 3, 5, *trial(skin, 'boss'))
    for x, z in ((5, 12), (sx - 6, 12), (5, sz - 4), (sx - 6, sz - 4)):
        p.set(x, 1, z, *trial(skin, 'guards'))
    p.box(c - 2, 1, sz - 7, c + 2, 1, sz - 2, b['trim'])            # the trough and its rim:
    p.box(c - 1, 1, sz - 6, c + 1, 1, sz - 3, LAVA, SOURCE)         # a course up, never on
                                                                    # the piece's own floor
                                                                    # face (section 28)
    for x, z in ((c, 10), (4, c), (sx - 5, c), (c, sz - 4)):
        p.set(x, sy - 2, z, b['light'])
    return p


def build(skin):
    out = {'gate': gate(skin), 'cap': cap(skin), 'hall': hall(skin),
           'special': special(skin), **{k: cell(skin, k) for k in CELLS}}
    for step in range(1, STEPS + 1):
        out['approach_%d' % step] = approach(skin, step)
    return out


# --------------------------------------------------------------------------------- checks
HANGS = {'minecraft:soul_lantern', 'minecraft:lantern', 'minecraft:ladder',
         'minecraft:iron_bars', 'minecraft:iron_chain', LAVA, 'minecraft:soul_fire',
         'minecraft:chain'}
AROUND = ((1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1))
BESIDE = ((1, 0, 0), (-1, 0, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1))
STANDS_ON = ('minecraft:barrel', 'minecraft:spawner', 'minecraft:trial_spawner',
             'minecraft:blast_furnace', 'minecraft:soul_fire', 'minecraft:soul_sand')


def problems_in(skin, pieces):
    problems = []
    for name, piece in sorted(pieces.items()):
        size = piece.size

        def solid(pos):
            block = piece.grid.get(pos)
            return bool(block) and block[0] != AIR and block[0] not in HANGS

        for pos, (block, props) in sorted(piece.grid.items()):
            if block in (AIR, 'minecraft:jigsaw'):
                continue
            inside = all(0 < pos[i] < size[i] - 1 for i in range(3))
            if block not in HANGS and inside and not any(
                    solid((pos[0] + d[0], pos[1] + d[1], pos[2] + d[2])) for d in AROUND):
                problems.append('%s/%s: %s floats at %s'
                                % (skin['key'], name, block.split(':')[-1], pos))
            if block in STANDS_ON or block.endswith('chest'):
                if not solid((pos[0], pos[1] - 1, pos[2])):
                    problems.append('%s/%s: the %s at %s stands on nothing'
                                    % (skin['key'], name, block.split(':')[-1], pos))
            if block.endswith('chest') and 'LootTable' not in (piece.extra.get(pos) or {}):
                problems.append('%s/%s: the chest at %s has no loot table'
                                % (skin['key'], name, pos))
            if block == LAVA:                                  # section 28
                for dx, dy, dz in BESIDE:
                    at = (pos[0] + dx, pos[1] + dy, pos[2] + dz)
                    if not all(0 <= at[i] < size[i] for i in range(3)):
                        problems.append('%s/%s: the lava at %s is on the piece\'s own face'
                                        % (skin['key'], name, pos))
                    elif piece.grid[at][0] == AIR:
                        problems.append('%s/%s: the lava at %s can run to %s'
                                        % (skin['key'], name, pos, at))
        if max(size) > 48:
            problems.append('%s/%s is %s: too big to rebuild by hand'
                            % (skin['key'], name, size))
        count = sum(1 for pos, (block, _) in piece.grid.items()
                    if block == 'minecraft:jigsaw'
                    and (piece.extra.get(pos) or {}).get('name') == boss_name(skin))
        if count > 1:
            problems.append('%s/%s carries %d jigsaws named %s; the chain could be entered '
                            'through its own continuation (section 13)'
                            % (skin['key'], name, count, boss_name(skin)))
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
    e = {'type': 'minecraft:item', 'name': mc(name)}
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


def potion(kind, weight=1):
    return item('potion', weight=weight, functions=[{
        'function': 'minecraft:set_components',
        'components': {'minecraft:potion_contents': {'potion': mc(kind)}}}])


def book(enchantment, level):
    return item('enchanted_book', functions=[{
        'function': 'minecraft:set_components',
        'components': {'minecraft:stored_enchantments': {mc(enchantment): level}}}])


# section 8, in a place with no farms and no daylight: the first roll is what keeps you alive
KEEP = {'rolls': 1, 'entries': [
    potion('fire_resistance', weight=8),
    item('cooked_porkchop', weight=6, functions=[count(3, 6)]),
    item('golden_carrot', weight=5, functions=[count(2, 5)]),
    item('gold_ingot', weight=5, functions=[count(3, 7)]),
    item('torch', weight=4, functions=[count(6, 12)]),
    item('magma_cream', weight=4, functions=[count(2, 4)])]}

CHEST = {
    'fort': [('nether_wart', 7, (3, 8)), ('blaze_powder', 5, (2, 5)),
             ('magma_cream', 5, (2, 5)), ('gold_ingot', 5, (3, 8)),
             ('glowstone_dust', 4, (4, 9)), ('diamond', 2, (1, 2))],
    'vault': [('gold_ingot', 8, (5, 12)), ('golden_carrot', 6, (3, 7)),
              ('gold_block', 3, (1, 2)), ('crying_obsidian', 4, (1, 4)),
              ('magma_cream', 4, (2, 5)), ('diamond', 2, (1, 2))],
    'sanctum': [('bone', 7, (4, 10)), ('soul_sand', 6, (4, 10)),
                ('glass_bottle', 5, (3, 7)), ('ghast_tear', 4, (1, 3)),
                ('glowstone_dust', 4, (4, 9)), ('diamond', 2, (1, 2))],
}

# the signature is the first pool of the boss's own table, so it is never a matter of luck
REWARD = {
    'fort': [
        {'rolls': 1, 'entries': [item('blaze_rod', functions=[count(8)])]},
        {'rolls': 1, 'entries': [item('wither_skeleton_skull')]},
        {'rolls': 1, 'entries': [with_enchants('diamond_sword', fire_aspect=2, sharpness=4),
                                 with_enchants('diamond_chestplate', protection=3),
                                 with_enchants('diamond_boots', feather_falling=3)]},
        {'rolls': {'type': 'minecraft:uniform', 'min': 2, 'max': 3}, 'entries': [
            potion('long_fire_resistance', weight=6),
            item('gold_block', weight=4, functions=[count(1, 3)]),
            item('nether_wart', weight=5, functions=[count(6, 12)]),
            item('experience_bottle', weight=6, functions=[count(8, 16)]),
            item('enchanted_book', weight=4, functions=[enchant(24, 30)]),
            item('diamond', weight=4, functions=[count(2, 5)])]}],
    'vault': [
        {'rolls': 1, 'entries': [item('netherite_scrap', functions=[count(4)])]},
        {'rolls': 1, 'entries': [item('netherite_upgrade_smithing_template')]},
        {'rolls': 1, 'entries': [item('ancient_debris', functions=[count(1, 2)])]},
        {'rolls': 1, 'entries': [with_enchants('golden_axe', sharpness=4, unbreaking=3),
                                 with_enchants('golden_chestplate', protection=4)]},
        {'rolls': {'type': 'minecraft:uniform', 'min': 2, 'max': 3}, 'entries': [
            item('netherite_ingot', weight=1),
            item('gold_block', weight=6, functions=[count(2, 5)]),
            item('golden_carrot', weight=5, functions=[count(4, 9)]),
            item('experience_bottle', weight=6, functions=[count(8, 16)]),
            item('enchanted_book', weight=4, functions=[enchant(24, 30)]),
            item('diamond', weight=4, functions=[count(2, 5)])]}],
    'sanctum': [
        {'rolls': 1, 'entries': [book('soul_speed', 3)]},
        {'rolls': 1, 'entries': [item('enchanted_golden_apple')]},
        {'rolls': 1, 'entries': [with_enchants('diamond_leggings', protection=3),
                                 with_enchants('diamond_helmet', respiration=3,
                                               protection=2)]},
        {'rolls': {'type': 'minecraft:uniform', 'min': 2, 'max': 3}, 'entries': [
            potion('regeneration', weight=5),
            item('ghast_tear', weight=5, functions=[count(2, 5)]),
            item('bone_block', weight=5, functions=[count(3, 8)]),
            item('experience_bottle', weight=6, functions=[count(8, 16)]),
            item('enchanted_book', weight=4, functions=[enchant(24, 30)]),
            item('diamond', weight=4, functions=[count(2, 5)])]}],
}

BOSS_MOB = {
    'fort': ('minecraft:blaze', 60.0, {'mainhand': None}),
    'vault': ('minecraft:piglin_brute', 100.0,
              {'mainhand': {'id': 'minecraft:golden_axe', 'count': 1, 'components': {
                  'minecraft:enchantments': {'minecraft:sharpness': 3}}}}),
    'sanctum': ('minecraft:wither_skeleton', 90.0,
                {'mainhand': {'id': 'minecraft:stone_sword', 'count': 1, 'components': {
                    'minecraft:enchantments': {'minecraft:sharpness': 2}}}}),
}

GUARDS = {
    'fort': [('minecraft:blaze', 4), ('minecraft:wither_skeleton', 3),
             ('minecraft:magma_cube', 2)],
    'vault': [('minecraft:piglin_brute', 3), ('minecraft:piglin', 4),
              ('minecraft:hoglin', 2)],
    'sanctum': [('minecraft:wither_skeleton', 4), ('minecraft:skeleton', 4),
                ('minecraft:magma_cube', 2)],
}


def write_data(skin):
    key = skin['key']
    put('loot_table/chests/%s.json' % key, {'type': 'minecraft:chest', 'pools': [
        KEEP,
        {'rolls': {'type': 'minecraft:uniform', 'min': 2, 'max': 4},
         'entries': [item(n, weight=w, functions=[count(*c)]) for n, w, c in CHEST[key]] +
                    [item('experience_bottle', weight=5, functions=[count(3, 8)]),
                     item('enchanted_book', weight=3, functions=[enchant(20, 30)])]}]})

    put('loot_table/trial/%s_reward.json' % key,
        {'type': 'minecraft:chest', 'pools': REWARD[key]})
    put('loot_table/trial/%s_guard_reward.json' % key, {'type': 'minecraft:chest', 'pools': [
        {'rolls': 1, 'entries': [
            item('gold_ingot', weight=6, functions=[count(2, 5)]),
            item('experience_bottle', weight=5, functions=[count(2, 5)]),
            item('magma_cream', weight=4, functions=[count(1, 3)]),
            item('glowstone_dust', weight=4, functions=[count(3, 7)]),
            item('diamond', weight=2)]}]})

    mob, health, gear = BOSS_MOB[key]
    entity = {'id': mob, 'CustomName': skin['boss'], 'CustomNameVisible': True,
              'PersistenceRequired': True, 'Health': health,
              'attributes': [{'id': 'minecraft:max_health', 'base': health},
                             {'id': 'minecraft:armor', 'base': 10.0},
                             {'id': 'minecraft:follow_range', 'base': 32.0},
                             {'id': 'minecraft:knockback_resistance', 'base': 0.6}]}
    if gear.get('mainhand'):
        entity['equipment'] = {'mainhand': gear['mainhand']}
        entity['drop_chances'] = {'mainhand': 0.1}
    put('trial_spawner/%s/boss.json' % key, {
        'spawn_range': 4, 'total_mobs': 1.0, 'simultaneous_mobs': 1.0,
        'total_mobs_added_per_player': 0.0, 'simultaneous_mobs_added_per_player': 0.0,
        'ticks_between_spawn': 20,
        'spawn_potentials': [{'weight': 1, 'data': {'entity': entity}}],
        'loot_tables_to_eject': [{'weight': 1,
                                  'data': '%s:trial/%s_reward' % (NS, key)}]})
    put('trial_spawner/%s/guards.json' % key, {
        'spawn_range': 4, 'total_mobs': 7.0, 'simultaneous_mobs': 2.0,
        'total_mobs_added_per_player': 2.0, 'simultaneous_mobs_added_per_player': 1.0,
        'ticks_between_spawn': 40,
        'spawn_potentials': [{'weight': w, 'data': {'entity': {
            'id': m, 'PersistenceRequired': True}}} for m, w in GUARDS[key]],
        'loot_tables_to_eject': [{'weight': 1,
                                  'data': '%s:trial/%s_guard_reward' % (NS, key)}]})

    put('tags/worldgen/biome/has_structure/%s.json' % key,
        {'values': [mc(b) for b in skin['biomes']]})

    # no heightmap: in the nether it measures to the bedrock roof. The start is dropped at a
    # height and the pieces carve their own room, the way a bastion does.
    put('worldgen/structure/%s.json' % key, {
        'type': 'sydungeon:ranged_jigsaw',
        'biomes': '#sydungeon:has_structure/%s' % key,
        'step': 'underground_structures',
        'terrain_adaptation': 'beard_thin',
        'spawn_overrides': {},
        'start_pool': pool(skin, 'start'),
        'size': {'type': 'minecraft:uniform', 'min_inclusive': 12, 'max_inclusive': 18},
        'start_height': {'type': 'minecraft:uniform',
                         'min_inclusive': {'absolute': 38},
                         'max_inclusive': {'absolute': 78}},
        'max_distance_from_center': {'horizontal': 56, 'vertical': 48},
        'use_expansion_hack': False,
        'liquid_settings': 'ignore_waterlogging',
        'dimension_padding': {'bottom': 12, 'top': 12}})

    # the nether already has fortresses and bastions in it; concepts.md section 5 asks for
    # ours to keep out of their way, and vanilla groups both in one set for exactly this
    put('worldgen/structure_set/%ss.json' % key, {
        'placement': {'type': 'minecraft:random_spread',
                      'spacing': skin['spacing'], 'separation': skin['separation'],
                      'salt': 51000000 + sum(ord(c) for c in key) * 6151,
                      'exclusion_zone': {'other_set': 'minecraft:nether_complexes',
                                         'chunk_count': 8}},
        'structures': [{'structure': '%s:%s' % (NS, key), 'weight': 1}]})

    b = B(skin)
    put('worldgen/processor_list/%s_weathering.json' % key, {'processors': [
        {'processor_type': 'minecraft:rule', 'rules': [
            {'input_predicate': {'predicate_type': 'minecraft:random_block_match',
                                 'block': b['brick'], 'probability': 0.14},
             'location_predicate': {'predicate_type': 'minecraft:always_true'},
             'output_state': {'Name': b['band']}},
            {'input_predicate': {'predicate_type': 'minecraft:random_block_match',
                                 'block': b['trim'], 'probability': 0.10},
             'location_predicate': {'predicate_type': 'minecraft:always_true'},
             'output_state': {'Name': b['brick']}},
            {'input_predicate': {'predicate_type': 'minecraft:random_block_match',
                                 'block': b['rock'], 'probability': 0.10},
             'location_predicate': {'predicate_type': 'minecraft:always_true'},
             'output_state': {'Name': b['band']}}]}]})


def element(skin, location, weight):
    return ('    { "weight": %d, "element": { "element_type": "minecraft:single_pool_element",'
            '\n        "location": "%s:%s/%s", "projection": "rigid", '
            '"processors": "%s:%s_weathering" } }'
            % (weight, NS, skin['key'], location, NS, skin['key']))


def write_pools(skin):
    out = os.path.join(DATA, 'worldgen', 'template_pool', skin['key'])
    if not os.path.isdir(out):
        os.makedirs(out)
    caps = pool(skin, 'caps')
    pools = {
        'start': ([element(skin, 'gate', 1)], EMPTY),
        'caps': ([element(skin, 'cap', 1)], EMPTY),
        'cells': ([element(skin, 'passage', 10), element(skin, 'corner', 9),
                   element(skin, 'cross', 5), element(skin, 'guard', 6),
                   element(skin, 'span', 5), element(skin, 'store', 6),
                   element(skin, 'special', 5)], caps),
        'boss': ([element(skin, 'hall', 1), element(skin, 'approach_%d' % STEPS, 1)], caps),
    }
    for step in range(1, STEPS + 1):
        pools['boss_%d' % step] = ([element(skin, 'approach_%d' % step, 1)], caps)
    for name, (elements, fallback) in pools.items():
        text = ('{\n  "fallback": "%s",\n  "elements": [\n%s\n  ]\n}\n'
                % (fallback, ',\n'.join(elements)))
        with io.open(os.path.join(out, name + '.json'), 'w', encoding='utf-8',
                     newline='\n') as f:
            f.write(text)


def main():
    problems, built = [], 0
    for skin in SKINS:
        pieces = build(skin)
        problems += problems_in(skin, pieces)
        dst = os.path.join(DATA, 'structure', skin['key'])
        if not os.path.isdir(dst):
            os.makedirs(dst)
        for name, piece in sorted(pieces.items()):
            piece.write(os.path.join(dst, name + '.nbt'))
            built += 1
        write_pools(skin)
        write_data(skin)
        print('  %-8s %-12s %d pieces, %d biomes, spacing %d'
              % (skin['key'], skin['title'], len(pieces), len(skin['biomes']),
                 skin['spacing']))
    for line in problems:
        print('  PROBLEM  ' + line)
    if problems:
        raise SystemExit('the nether dungeons do not hold together')
    print('  checked: %d pieces, nothing hangs in mid-air, no lava can run, every chest has '
          'a table, one way into each boss' % built)


if __name__ == '__main__':
    main()
