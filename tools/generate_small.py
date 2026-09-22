# -*- coding: utf-8 -*-
"""The small dungeons: one machine, a skin per biome (docs/concepts.md section 2.8).

    python tools/generate_small.py        (or through make_pieces.py)

Writes data/sydungeon/structure/<skin>/*.nbt and the pools, and prints what it built.

WHY THEY ARE ALL THE SAME MACHINE
A small dungeon is ten minutes: a way in, a ladder, a room the ladder lands in, a short maze
and a chest or two. That is the prison with the numbers turned down, and writing it eight
times would be eight places to fix the same bug. So the shape is written once and the SKINS
table says what it is made of, what it stands in, and what lives in it.

WHAT A SMALL ONE IS NOT
No boss and no signature (section 2.8). A trial spawner here would break "one piece of gear
per boss" (2.4) the moment these start turning up every three hundred blocks - `verify()`
refuses one, the same as the hollow's does. What they give is what the first night of a
farmless world actually needs: a bed, torches, food, and enough iron to get moving.

WHY THEY SIT ON TOP OF THE BIG ONES
Each skin shares its biomes with whichever large dungeon owns them, and its structure set
carries an exclusion zone against that set, so the two never land in the same few chunks.
The large one is the day out; this is the thing you fall into on the way there.
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
SHAFT_H = 21                     # deep enough that the maze is not the hillside's business
AIR = 'minecraft:air'
LADDER = 'minecraft:ladder'

# the column, in every piece's own coordinates: one ladder dead centre, the post east of it
HOLE = (CELL // 2, CELL // 2)
JIG = (HOLE[0] + 1, HOLE[1])

HANGING = {'hanging': 'true', 'waterlogged': 'false'}
STANDING = {'hanging': 'false', 'waterlogged': 'false'}
ANY_LIGHT = {'block_light_limit': {'min_inclusive': nbt.Int(0), 'max_inclusive': nbt.Int(15)}}


# ---------------------------------------------------------------------------------- skins
# head: which way in gets built. rock/band: the shell, which is what shows if the maze is
# ever cut open (section 5.2). brick/trim/floor: the inside. mob: what the den spawns.
SKINS = [
    dict(key='well', title='숨은 우물', head='well', mob='minecraft:zombie',
         biomes=['plains', 'sunflower_plains', 'meadow', 'forest', 'flower_forest',
                 'birch_forest', 'old_growth_birch_forest'],
         rock='stone', band='andesite', brick='cobblestone', trim='stone_bricks',
         floor='gravel', wood='oak', avoid='dungeons'),
    dict(key='tomb', title='모래 아래 무덤', head='mound', mob='minecraft:husk',
         biomes=['desert'],
         rock='sandstone', band='cut_sandstone', brick='cut_sandstone',
         trim='chiseled_sandstone', floor='sand', wood='acacia', avoid='pyramids'),
    dict(key='cabin', title='사냥꾼의 오두막', head='hut', mob='minecraft:skeleton',
         biomes=['taiga', 'old_growth_pine_taiga', 'old_growth_spruce_taiga'],
         rock='stone', band='granite', brick='cobblestone', trim='spruce_planks',
         floor='coarse_dirt', wood='spruce', avoid='towers'),
    dict(key='cairn', title='눈 속 돌무덤', head='cairn', mob='minecraft:stray',
         biomes=['snowy_plains', 'ice_spikes', 'snowy_taiga', 'snowy_slopes',
                 'frozen_peaks', 'grove'],
         rock='stone', band='diorite', brick='cobblestone', trim='polished_diorite',
         floor='packed_ice', wood='spruce', avoid='fortresses'),
    dict(key='dryw', title='마른 우물', head='well', mob='minecraft:husk',
         biomes=['savanna', 'savanna_plateau', 'windswept_savanna', 'badlands',
                 'eroded_badlands', 'wooded_badlands'],
         rock='stone', band='orange_terracotta', brick='cut_red_sandstone',
         trim='terracotta', floor='coarse_dirt', wood='acacia', avoid='camps'),
    dict(key='canopy', title='덩굴 밑 저장고', head='mound', mob='minecraft:cave_spider',
         biomes=['jungle', 'sparse_jungle', 'bamboo_jungle'],
         rock='stone', band='andesite', brick='mossy_cobblestone',
         trim='mossy_stone_bricks', floor='podzol', wood='jungle', avoid='temples'),
    dict(key='lodge', title='숲지기의 지하실', head='hut', mob='minecraft:zombie_villager',
         biomes=['dark_forest', 'pale_garden'],
         rock='stone', band='andesite', brick='cobblestone', trim='dark_oak_planks',
         floor='podzol', wood='dark_oak', avoid='graveyards'),
    dict(key='mire', title='물에 잠긴 저장고', head='mound', mob='minecraft:drowned',
         biomes=['swamp', 'mangrove_swamp'],
         rock='stone', band='clay', brick='mud_bricks', trim='packed_mud',
         floor='mud', wood='mangrove', avoid='swamps'),
    # and two with no way in from the surface at all: a maze in the rock, dropped at a
    # depth instead of on the ground. The cheapest small dungeon there is - no entrance to
    # build and no slope to stand on - and the cave biomes had nothing (concepts.md 4.0).
    dict(key='lush', title='이끼 낀 굴', head=None, deep=(-40, 8),
         mob='minecraft:cave_spider', biomes=['lush_caves'],
         rock='stone', band='moss_block', brick='mossy_cobblestone',
         trim='mossy_stone_bricks', floor='moss_block', wood='oak', avoid=None),
    dict(key='drip', title='점적석 굴', head=None, deep=(-48, 0),
         mob='minecraft:skeleton', biomes=['dripstone_caves'],
         rock='stone', band='dripstone_block', brick='cobblestone',
         trim='stone_bricks', floor='dripstone_block', wood='oak', avoid=None),
]

CELLS = ('passage', 'corner', 'cross', 'den', 'nook')


def mc(name):
    return name if ':' in name else 'minecraft:' + name


def skin_blocks(skin):
    return {k: mc(skin[k]) for k in ('rock', 'band', 'brick', 'trim', 'floor')}


def wood(skin, part):
    return 'minecraft:%s_%s' % (skin['wood'], part)


def pool_name(skin, name):
    return '%s:%s/%s' % (NS, skin['key'], name)


# ---------------------------------------------------------------------------- the furniture
def chest(skin, facing='north'):
    return ('minecraft:chest', {'facing': facing, 'type': 'single', 'waterlogged': 'false'},
            {'id': 'minecraft:chest', 'LootTable': '%s:chests/%s' % (NS, skin['key'])})


def spawner(entity):
    return ('minecraft:spawner', None,
            {'id': 'minecraft:mob_spawner',
             'SpawnData': {'entity': {'id': entity}, 'custom_spawn_rules': ANY_LIGHT},
             'Delay': nbt.Short(20), 'MinSpawnDelay': nbt.Short(240),
             'MaxSpawnDelay': nbt.Short(900), 'SpawnCount': nbt.Short(2),
             'MaxNearbyEntities': nbt.Short(5), 'RequiredPlayerRange': nbt.Short(14),
             'SpawnRange': nbt.Short(4)})


def ladder(facing='west'):
    return (LADDER, {'facing': facing, 'waterlogged': 'false'})


def bedrock(p, skin, sy, at=0):
    """The ground's own stone, banded: what an exposed piece reads as (section 5.2)."""
    b = skin_blocks(skin)
    sx, _, sz = p.size
    for y in range(sy):
        p.box(0, y, 0, sx - 1, y, sz - 1, b['rock'] if (y + at) % 4 else b['band'])


def sink(p, skin, y0, y1, fill=None):
    """One column of ladder and a ring of solid block round it (CLAUDE.md section 33)."""
    fill = fill or skin_blocks(skin)['brick']
    cx, cz = HOLE
    for x in range(cx - 1, cx + 2):
        for z in range(cz - 1, cz + 2):
            for y in range(y0, y1 + 1):
                p.set(x, y, z, fill)
    for y in range(y0, y1 + 1):
        p.set(cx, y, cz, *ladder())


# -------------------------------------------------------------------------------- the way in
def head(skin):
    """The piece in daylight. Seven across and no footing under it: a start piece's floor
    course belongs on the terrain's own top block (section 30), and what falls away beside it
    is the beard's business, not ours."""
    b = skin_blocks(skin)
    p = Piece(CELL, 8, CELL, AIR)
    mid = CELL // 2
    p.box(0, 0, 0, CELL - 1, 0, CELL - 1, b['floor'])
    kind = skin['head']

    if kind == 'well':
        for x in range(CELL):                                   # a kerb ring, one course up
            for z in range(CELL):
                if max(abs(x - mid), abs(z - mid)) == 2:
                    p.set(x, 0, z, b['brick'])
                    p.set(x, 1, z, b['brick'])
        for x in (mid - 2, mid + 2):                            # two posts and a beam over
            for y in range(2, 5):
                p.set(x, y, mid, wood(skin, 'log'), {'axis': 'y'})
        for d in range(-2, 3):
            p.set(mid + d, 4, mid, wood(skin, 'log'), {'axis': 'x'})
        p.set(mid, 3, mid, 'minecraft:iron_chain', {'axis': 'y', 'waterlogged': 'false'})
    elif kind == 'mound':
        for x in range(CELL):                                   # a low mound, cut open north
            for z in range(CELL):
                far = max(abs(x - mid), abs(z - mid))
                for y in range(1, 5 - far):
                    p.set(x, y, z, b['brick'] if far else b['trim'])
        p.box(mid - 1, 1, 0, mid + 1, 2, mid, AIR)              # the mouth, two tall
    elif kind == 'hut':
        p.box(0, 1, 0, CELL - 1, 4, CELL - 1, wood(skin, 'planks'))
        p.box(1, 1, 1, CELL - 2, 4, CELL - 2, AIR)
        for x, z in ((0, 0), (0, CELL - 1), (CELL - 1, 0), (CELL - 1, CELL - 1)):
            for y in range(1, 5):
                p.set(x, y, z, wood(skin, 'log'), {'axis': 'y'})
        p.box(0, 1, mid - 1, 0, 3, mid + 1, AIR)                # the doorway, west
        for x in range(CELL):                                   # a roof of slabs
            for z in range(CELL):
                p.set(x, 5, z, wood(skin, 'slab'),
                      {'type': 'bottom', 'waterlogged': 'false'})
        p.set(CELL - 2, 1, 1, 'minecraft:crafting_table')
        p.set(1, 1, CELL - 2, *chest(skin, 'north'))
    else:  # cairn
        for x in range(CELL):
            for z in range(CELL):
                far = max(abs(x - mid), abs(z - mid))
                for y in range(1, 5 - far):
                    p.set(x, y, z, b['rock'] if (x + z) % 3 else b['band'])
        p.box(mid, 1, mid - 2, mid, 2, mid, AIR)                # the mouth, two tall

    for x in range(CELL):                                       # the floor, and the one hole
        for z in range(CELL):
            if (x, z) != HOLE and p.grid[(x, 0, z)][0] == AIR:
                p.set(x, 0, z, b['floor'])
    sink(p, skin, 0, 0)
    p.jigsaw(JIG[0], 0, JIG[1], 'down_east', pool_name(skin, 'down'), b['brick'],
             joint='aligned', priority=PRIORITY, name=down_name(skin), target=down_name(skin))
    return p


def down_name(skin):
    return '%s:%s_down' % (NS, skin['key'])


def cell_name(skin):
    return '%s:%s_cell' % (NS, skin['key'])


def shaft(skin):
    b = skin_blocks(skin)
    p = Piece(CELL, SHAFT_H, CELL, b['rock'])
    bedrock(p, skin, SHAFT_H, at=1)
    sink(p, skin, 0, SHAFT_H - 1, fill=b['rock'])
    p.jigsaw(JIG[0], SHAFT_H - 1, JIG[1], 'up_east', EMPTY, b['rock'], joint='aligned',
             name=down_name(skin), target=down_name(skin))
    p.jigsaw(JIG[0], 0, JIG[1], 'down_east', pool_name(skin, 'first'), b['rock'],
             joint='aligned', priority=PRIORITY, name=cell_name(skin), target=cell_name(skin))
    return p


# --------------------------------------------------------------------------------- the maze
DOOR_AT = {'west': (0, 3, 'west_up'), 'east': (CELL - 1, 3, 'east_up'),
           'north': (3, 0, 'north_up'), 'south': (3, CELL - 1, 'south_up')}


def room(skin, doors):
    """A cell of the maze, cut out of the ground's own stone with the brick on the inside."""
    b = skin_blocks(skin)
    p = Piece(CELL, CELL, CELL, b['rock'])
    bedrock(p, skin, CELL)
    p.box(1, 1, 1, CELL - 2, CELL - 2, CELL - 2, AIR)
    p.box(0, 0, 0, CELL - 1, 0, CELL - 1, b['brick'])
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


def door(p, skin, side, pool, name=None, target=None, priority=0):
    x, z, orientation = DOOR_AT[side]
    p.jigsaw(x, 0, z, orientation, pool, skin_blocks(skin)['rock'], priority=priority,
             name=name or cell_name(skin), target=target or cell_name(skin))


def hub(skin):
    """Where the ladder lands. West and south open into the maze; north calls the store room
    on its own single-element pool, so every one of these has a chest in it.

    The deep ones have no ladder and no way in: this piece is their start, dropped at a depth
    into whatever rock is there, so it opens east as well and the maze is the whole dungeon.
    """
    b = skin_blocks(skin)
    if skin.get('deep'):
        p = room(skin, ['west', 'north', 'south', 'east'])
        for side in ('west', 'south', 'east'):
            door(p, skin, side, pool_name(skin, 'cells'), priority=PRIORITY)
        door(p, skin, 'north', pool_name(skin, 'store'), priority=PRIORITY)
        p.set(1, 1, 1, 'minecraft:lantern', STANDING)
        p.set(CELL - 2, 1, CELL - 2, *chest(skin, 'west'))
        return p
    p = room(skin, ['west', 'north', 'south'])
    cx, cz = HOLE
    for x in range(CELL):                                        # close the ceiling first
        for z in range(CELL):
            if p.grid[(x, CELL - 1, z)][0] in (AIR, LADDER):
                p.set(x, CELL - 1, z, b['rock'])
    for y in range(1, CELL):
        p.set(JIG[0], y, JIG[1], b['trim'])                      # the post it hangs on
        p.set(cx, y, cz, *ladder())
    p.jigsaw(JIG[0], CELL - 1, JIG[1], 'up_east', EMPTY, b['trim'], joint='aligned',
             name=cell_name(skin), target=cell_name(skin))
    door(p, skin, 'west', pool_name(skin, 'cells'))
    door(p, skin, 'south', pool_name(skin, 'cells'))
    door(p, skin, 'north', pool_name(skin, 'store'), priority=PRIORITY)
    p.set(1, 1, 1, 'minecraft:lantern', STANDING)                # the only light down here
    return p


def store(skin):
    """The one room that is always there: the chest, and something to stand a bed on."""
    b = skin_blocks(skin)
    p = room(skin, ['south'])
    door(p, skin, 'south', pool_name(skin, 'cells'))
    mid = CELL // 2
    p.box(1, 1, 1, CELL - 2, 1, 1, b['trim'])
    p.set(mid, 2, 1, *chest(skin, 'south'))
    p.set(1, 2, 1, 'minecraft:lantern', STANDING)
    p.set(CELL - 2, 1, 1, 'minecraft:barrel', {'facing': 'up', 'open': 'false'})
    p.set(1, 1, CELL - 2, wood(skin, 'fence'),
          {'north': 'false', 'south': 'false', 'east': 'false', 'west': 'false',
           'waterlogged': 'false'})
    return p


def cell(skin, kind):
    doors = {'passage': ['west', 'east'], 'corner': ['west', 'south'],
             'cross': ['west', 'east', 'north', 'south'],
             'den': ['west', 'east'], 'nook': ['west']}[kind]
    b = skin_blocks(skin)
    p = room(skin, doors)
    for side in doors:
        door(p, skin, side, pool_name(skin, 'cells'))
    mid = CELL // 2
    if kind == 'passage':
        for z in (1, CELL - 2):
            p.set(1, 1, z, b['trim'])
    elif kind == 'corner':
        p.set(CELL - 2, 1, 1, b['trim'])
        p.set(CELL - 2, 2, 1, 'minecraft:lantern', STANDING)
    elif kind == 'cross':
        for x, z in ((1, 1), (1, CELL - 2), (CELL - 2, 1), (CELL - 2, CELL - 2)):
            for y in (1, 2, 3):
                p.set(x, y, z, b['trim'])
    elif kind == 'den':
        p.box(mid - 1, 0, mid - 1, mid + 1, 0, mid + 1, b['trim'])
        p.set(mid, 1, mid, *spawner(skin['mob']))
        p.set(1, 1, 1, 'minecraft:cobweb')
    elif kind == 'nook':
        p.box(1, 1, 1, CELL - 2, 1, 1, b['floor'])
        p.set(mid, 1, 1, *chest(skin, 'south'))
        p.set(CELL - 2, 2, 1, 'minecraft:lantern', STANDING)
    return p


def cap(skin):
    b = skin_blocks(skin)
    p = Piece(1, CELL, CELL, b['rock'])
    bedrock(p, skin, CELL)
    p.jigsaw(0, 0, 3, 'west_up', pool_name(skin, 'caps'), b['rock'],
             name=cell_name(skin), target=cell_name(skin))
    return p


def build(skin):
    out = {'hub': hub(skin), 'store': store(skin), 'cap': cap(skin),
           **{k: cell(skin, k) for k in CELLS}}
    if not skin.get('deep'):
        out['head'] = head(skin)
        out['shaft'] = shaft(skin)
    return out


# ---------------------------------------------------------------------------------- checks
HANGS = {'minecraft:lantern', LADDER, 'minecraft:iron_chain', 'minecraft:cobweb',
         'minecraft:torch'}
AROUND = ((1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1))
BEHIND = {'north': (0, 0, 1), 'south': (0, 0, -1), 'east': (-1, 0, 0), 'west': (1, 0, 0)}
STANDS_ON = ('minecraft:barrel', 'minecraft:spawner', 'minecraft:crafting_table')


def problems_in(skin, pieces):
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
                                % (skin['key'], name, block.split(':')[-1], pos))
            if block == LADDER:
                d = BEHIND[props.get('facing', 'north')]
                if not solid((pos[0] + d[0], pos[1] + d[1], pos[2] + d[2])):
                    problems.append('%s/%s: the ladder at %s has nothing behind it'
                                    % (skin['key'], name, pos))
            if block in STANDS_ON or block.endswith('chest'):
                if not solid((pos[0], pos[1] - 1, pos[2])):
                    problems.append('%s/%s: the %s at %s stands on nothing'
                                    % (skin['key'], name, block.split(':')[-1], pos))
            if block == 'minecraft:trial_spawner':
                problems.append('%s/%s has a trial spawner: a small dungeon has no boss, and '
                                'one that pays out like a large one breaks "one piece of gear '
                                'per boss" (section 2.8)' % (skin['key'], name))
            if block.endswith('chest') and 'LootTable' not in (piece.extra.get(pos) or {}):
                problems.append('%s/%s: the chest at %s has no loot table'
                                % (skin['key'], name, pos))
        if max(size) > 48:
            problems.append('%s/%s is %s: too big to rebuild by hand'
                            % (skin['key'], name, size))
    if not any(block.endswith('chest') for piece in (pieces['store'],)
               for block, _ in piece.grid.values()):
        problems.append('%s: the store room has no chest, and it is the one room that is '
                        'always placed' % skin['key'])
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


# section 8: the first roll is survival kit, and in a small dungeon that is the whole point
KEEP = {'rolls': 1, 'entries': [
    item('torch', weight=8, functions=[count(6, 14)]),
    item('bread', weight=6, functions=[count(3, 6)]),
    item('white_bed', weight=5),
    item('coal', weight=6, functions=[count(4, 10)]),
    item('cooked_beef', weight=4, functions=[count(2, 4)]),
    item('iron_ingot', weight=4, functions=[count(2, 4)])]}

EXTRA = {
    'well': ['wheat_seeds', 'iron_nugget', 'bucket', 'oak_sapling', 'apple'],
    'tomb': ['gold_nugget', 'sand', 'dead_bush', 'bone_meal', 'gold_ingot'],
    'cabin': ['arrow', 'spruce_sapling', 'leather', 'bow', 'cooked_rabbit'],
    'cairn': ['snowball', 'ice', 'leather_boots', 'arrow', 'blue_ice'],
    'dryw': ['gold_nugget', 'acacia_sapling', 'red_sand', 'copper_ingot', 'emerald'],
    'canopy': ['cocoa_beans', 'jungle_sapling', 'melon_slice', 'bamboo', 'emerald'],
    'lodge': ['brown_mushroom', 'red_mushroom', 'dark_oak_sapling', 'bowl', 'book'],
    'mire': ['slime_ball', 'clay_ball', 'lily_pad', 'mangrove_propagule', 'kelp'],
    'lush': ['glow_berries', 'moss_block', 'bone_meal', 'azalea', 'emerald'],
    'drip': ['pointed_dripstone', 'copper_ingot', 'raw_iron', 'flint', 'emerald'],
}


def write_data(skin):
    key = skin['key']
    put('loot_table/chests/%s.json' % key, {'type': 'minecraft:chest', 'pools': [
        KEEP,
        {'rolls': {'type': 'minecraft:uniform', 'min': 2, 'max': 3}, 'entries':
            [item(name, weight=w, functions=[count(2, 6)])
             for w, name in zip((7, 6, 5, 4, 3), EXTRA[key])] +
            [item('experience_bottle', weight=5, functions=[count(2, 6)]),
             item('iron_ingot', weight=5, functions=[count(1, 4)]),
             item('book', weight=3),
             item('diamond', weight=1)]}]})

    put('tags/worldgen/biome/has_structure/%s.json' % key,
        {'values': [mc(b) for b in skin['biomes']]})

    structure = {
        'type': 'sydungeon:ranged_jigsaw',
        'biomes': '#sydungeon:has_structure/%s' % key,
        'step': 'underground_structures',
        'terrain_adaptation': 'none',
        'spawn_overrides': {},
        'start_pool': pool_name(skin, 'start'),
        'size': {'type': 'minecraft:uniform', 'min_inclusive': 6, 'max_inclusive': 10},
        'start_height': {'absolute': 0},
        'project_start_to_heightmap': 'WORLD_SURFACE_WG',
        'max_distance_from_center': {'horizontal': 40, 'vertical': 48},
        'use_expansion_hack': False,
        'liquid_settings': 'ignore_waterlogging',
        'dimension_padding': {'bottom': 8, 'top': 0},
        'level_ground_drop': 8,
        'level_ground_radius': 6}
    if skin.get('deep'):
        # no heightmap: the start is dropped at a depth, into whatever rock is there. Which
        # is why there is no level ground to ask for and nothing for the beard to do either.
        low, high = skin['deep']
        structure.pop('project_start_to_heightmap')
        structure.pop('level_ground_drop')
        structure.pop('level_ground_radius')
        structure['start_height'] = {'type': 'minecraft:uniform',
                                     'min_inclusive': {'absolute': low},
                                     'max_inclusive': {'absolute': high}}
        structure['dimension_padding'] = {'bottom': 16, 'top': 16}
    put('worldgen/structure/%s.json' % key, structure)

    # close together, because a small one is meant to be tripped over rather than sought
    # (section 2.8), and kept away from the large dungeon that owns the same biomes
    placement = {'type': 'minecraft:random_spread',
                 'spacing': 18, 'separation': 7,
                 'salt': 40000000 + sum(ord(c) for c in key) * 7919}
    if skin['avoid']:
        placement['exclusion_zone'] = {'other_set': '%s:%s' % (NS, skin['avoid']),
                                       'chunk_count': 6}
    put('worldgen/structure_set/%ss.json' % key, {
        'placement': placement,
        'structures': [{'structure': '%s:%s' % (NS, key), 'weight': 1}]})

    b = skin_blocks(skin)
    put('worldgen/processor_list/%s_weathering.json' % key, {'processors': [
        {'processor_type': 'minecraft:rule', 'rules': [
            {'input_predicate': {'predicate_type': 'minecraft:random_block_match',
                                 'block': b['brick'], 'probability': 0.14},
             'location_predicate': {'predicate_type': 'minecraft:always_true'},
             'output_state': {'Name': b['rock']}},
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
    caps = pool_name(skin, 'caps')
    pools = {
        'start': ([element(skin, 'hub' if skin.get('deep') else 'head', 1)], EMPTY),
        'down': ([element(skin, 'shaft', 1)], EMPTY),
        'first': ([element(skin, 'hub', 1)], EMPTY),
        'store': ([element(skin, 'store', 1)], caps),
        'cells': ([element(skin, 'passage', 10), element(skin, 'corner', 8),
                   element(skin, 'cross', 4), element(skin, 'den', 5),
                   element(skin, 'nook', 6)], caps),
        'caps': ([element(skin, 'cap', 1)], EMPTY),
    }
    if skin.get('deep'):
        # no shaft and no hub-below-a-shaft: the hub IS the start, so those two pools would
        # point at pieces that do not exist
        for gone in ('down', 'first'):
            pools.pop(gone)
            stale = os.path.join(out, gone + '.json')
            if os.path.exists(stale):
                os.remove(stale)
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
        print('  %-7s %-16s %d pieces, %d biomes'
              % (skin['key'], skin['title'], len(pieces), len(skin['biomes'])))
    for line in problems:
        print('  PROBLEM  ' + line)
    if problems:
        raise SystemExit('the small dungeons do not hold together')
    print('  checked: %d pieces, nothing hangs in mid-air, every chest has a table, a store '
          'room on every one, and not a trial spawner anywhere' % built)


if __name__ == '__main__':
    main()
