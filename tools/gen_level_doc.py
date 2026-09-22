# -*- coding: utf-8 -*-
"""Write the level-design documents from the shipped pieces.

    python tools/gen_level_doc.py                # all three
    python tools/gen_level_doc.py tower          # one family

For each family this writes `docs/levels/<family>.md` and one SVG sheet per piece under
`docs/levels/img/<family>/`. The sheet draws every Y layer of the piece block by block,
north up, with the 7x7 cell grid overlaid and the jigsaws marked with the direction they
face, then two vertical sections through the middle.

Everything except the prose is read back out of the files the game actually loads - the
`.nbt` pieces and the worldgen JSON - so the document cannot drift from the mod. The prose
lives in `NOTES` and `INTRO` below; that is the part a human edits.
"""
import glob
import io
import json
import os
import re
import sys
from collections import Counter, OrderedDict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import nbt  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, 'src', 'main', 'resources', 'data', 'sydungeon')
OUT = os.path.join(ROOT, 'docs', 'levels')

FAMILIES = ('dungeon', 'pyramid', 'tower', 'swamp', 'ice', 'temple')


# --- how each block is drawn ------------------------------------------------------------
# glyph, fill, korean label. The glyph is what the ASCII maps use, the fill is what the SVG
# uses. Anything missing falls back to a grey box and '?', and `check_style` reports it.
STYLE = OrderedDict([
    ('stone_bricks',          ('#', '#8f8f8f', '돌벽돌')),
    ('chiseled_stone_bricks', ('%', '#74747a', '조각한 돌벽돌')),
    ('stone_brick_stairs',    ('/', '#a6a6a6', '돌벽돌 계단')),
    ('mossy_stone_bricks',    ('m', '#7c8a72', '이끼 낀 돌벽돌')),
    ('mossy_cobblestone',     ('n', '#6f7c66', '이끼 낀 조약돌')),
    ('deepslate_bricks',      ('D', '#4b4b52', '심층암 벽돌')),
    ('polished_deepslate',    ('d', '#3a3a40', '윤나는 심층암')),
    ('sandstone',             ('=', '#ddd0a1', '사암')),
    ('cut_sandstone',         ('-', '#d0c28c', '깎은 사암')),
    ('chiseled_sandstone',    ('&', '#c6b77e', '조각한 사암')),
    ('smooth_sandstone',      ('~', '#e9dfb8', '매끄러운 사암')),
    ('sand',                  (':', '#f2e4a6', '모래')),
    ('suspicious_sand',       ('?', '#cdbb7e', '수상한 모래')),
    ('obsidian',              ('O', '#17121f', '흑요석')),
    ('bookshelf',             ('B', '#8d6a43', '책장')),
    ('enchanting_table',      ('E', '#b0332f', '마법 부여대')),
    ('lectern',               ('L', '#ab7f4c', '독서대')),
    ('brewing_stand',         ('Y', '#9c8f6f', '양조기')),
    ('cauldron',              ('U', '#4e4e52', '가마솥')),
    ('chest',                 ('c', '#b9852f', '상자')),
    ('spawner',               ('S', '#25403f', '몬스터 스포너')),
    ('trial_spawner',         ('T', '#2f7d74', '트라이얼 스포너')),
    ('iron_bars',             ('|', '#6e7478', '철창')),
    ('ladder',                ('H', '#b8863f', '사다리')),
    ('lantern',               ('*', '#ffc94d', '랜턴')),
    ('soul_lantern',          ('s', '#5fd8f0', '영혼 랜턴')),
    ('iron_chain',            ('i', '#8b9096', '쇠사슬')),
    ('glass_pane',            ('g', '#bfe9ee', '유리판')),
    ('dark_oak_planks',       ('w', '#4a2f18', '짙은 참나무 판자')),
    ('dark_oak_log',          ('L', '#3a2a16', '짙은 참나무 원목')),
    ('dark_oak_slab',         ('_', '#5a3a1e', '짙은 참나무 반 블록')),
    ('mud_bricks',            ('N', '#8a6a52', '진흙 벽돌')),
    ('packed_mud',            ('n', '#9a7a5e', '굳은 진흙')),
    ('muddy_mangrove_roots',  ('R', '#4a3a2a', '진흙 맹그로브 뿌리')),
    ('water',                 ('~', '#3f76e4', '물')),
    ('dark_oak_fence',        ('f', '#6b452a', '짙은 참나무 울타리')),
    ('spruce_planks',         ('w', '#6b4f2c', '가문비나무 판자')),
    ('spruce_fence',          ('f', '#7d5e36', '가문비나무 울타리')),
    ('spruce_log',            ('l', '#4b3a22', '가문비나무 원목')),
    ('oxidized_copper',       ('K', '#4f9e86', '산화 구리')),
    ('oxidized_cut_copper',   ('k', '#57a98f', '깎은 산화 구리')),
    ('oxidized_cut_copper_stairs', ('r', '#6bbda2', '산화 구리 계단')),
    ('oxidized_chiseled_copper', ('R', '#448d78', '조각한 산화 구리')),
    ('oxidized_copper_grate', ('G', '#3f8270', '산화 구리 격자')),
    ('oxidized_copper_chain', ('j', '#5aa893', '산화 구리 사슬')),
    ('oxidized_lightning_rod', ('!', '#8fe0c8', '피뢰침')),
    ('mossy_cobblestone',     ('#', '#6f7c66', '이끼 낀 조약돌')),
    ('cobblestone',           (',', '#828282', '조약돌')),
    ('moss_block',            ('m', '#5a7040', '이끼 블록')),
    ('vine',                  ('v', '#3f6b2a', '덩굴')),
    ('jungle_planks',         ('w', '#9a6b43', '정글 판자')),
    ('jungle_log',            ('L', '#5a4322', '정글 원목')),
    ('jungle_fence',          ('f', '#8a5f3c', '정글 울타리')),
    ('jungle_leaves',         ('l', '#2e6b1e', '정글 잎')),
    ('jungle_sapling',        ('Y', '#3f8a2a', '정글 묘목')),
    ('infested_stone_bricks', ('X', '#7a7a6a', '좀벌레 돌벽돌')),
    ('gravel',                ('g', '#8d8888', '자갈')),
    ('suspicious_gravel',     ('?', '#a39a8c', '수상한 자갈')),
    ('cobweb',                ('*', '#d8dde2', '거미줄')),
    ('iron_door',             ('D', '#c8c8c8', '철문')),
    ('lever',                 ('!', '#8a7a5e', '레버')),
    ('mossy_cobblestone_stairs', ('<', '#788566', '이끼 조약돌 계단')),
    ('mossy_cobblestone_slab', ('_', '#7e8b6c', '이끼 조약돌 반 블록')),
    ('polished_diorite',      ('#', '#d8d8d8', '윤나는 섬록암')),
    ('diorite',               ('d', '#c9c9c9', '섬록암')),
    ('diorite_stairs',        ('<', '#cfcfcf', '섬록암 계단')),
    ('diorite_slab',          ('_', '#d2d2d2', '섬록암 반 블록')),
    ('quartz_bricks',         ('%', '#f2ece1', '석영 벽돌')),
    ('chiseled_quartz_block', ('Q', '#efe7d8', '조각한 석영')),
    ('deepslate_tiles',       ('V', '#3c3c42', '심층암 타일')),
    ('cracked_deepslate_tiles', ('x', '#45454b', '금 간 심층암 타일')),
    ('chiseled_deepslate',    ('y', '#37373c', '조각한 심층암')),
    ('cobbled_deepslate',     (',', '#4a4a50', '조약 심층암')),
    ('deepslate_tile_stairs', ('u', '#43434a', '심층암 타일 계단')),
    ('deepslate_tile_slab',   ('U', '#46464d', '심층암 타일 반 블록')),
    ('white_bed',             ('B', '#e8e8e8', '침대')),
    ('anvil',                 ('A', '#4a4a4f', '모루')),
    ('grindstone',            ('G', '#8a7a5e', '숫돌')),
    ('smithing_table',        ('M', '#3c3f4a', '대장장이 탁자')),
    ('fletching_table',       ('F', '#c9b48a', '화살 제작대')),
    ('cartography_table',     ('P', '#7a6a55', '지도 제작대')),
    ('loom',                  ('W', '#a08a62', '베틀')),
    ('bookshelf',             ('B', '#8d6a43', '책장')),
    ('chiseled_bookshelf',    ('K', '#9a7a4a', '조각한 책장')),
    ('white_banner',          ('N', '#f0f0f0', '깃발')),
    ('white_candle',          ('c', '#f6f1e3', '양초')),
    ('decorated_pot',         ('O', '#b9714b', '장식 항아리')),
    ('tuff_bricks',           ('t', '#6d6b64', '응회암 벽돌')),
    ('polished_tuff',         ('T', '#7b7a73', '윤나는 응회암')),
    ('chiseled_tuff',         ('y', '#5f5e58', '조각한 응회암')),
    ('calcite',               ('C', '#dfded9', '방해석')),
    ('deepslate_tiles',       ('V', '#3c3c42', '심층암 타일')),
    ('cobbled_deepslate',     ('v', '#4a4a50', '조약 심층암')),
    ('spruce_stairs',         ('/', '#7d5e36', '가문비나무 계단')),
    ('spruce_trapdoor',       ('=', '#8a6a40', '가문비나무 다락문')),
    ('tuff_brick_stairs',     ('u', '#79776f', '응회암 벽돌 계단')),
    ('tuff_brick_slab',       ('U', '#85837a', '응회암 벽돌 반 블록')),
    ('snow_block',            ('o', '#f0f5f9', '눈 블록')),
    ('packed_ice',            ('I', '#a6c9e8', '다진 얼음')),
    ('blue_ice',              ('b', '#74a7e0', '푸른 얼음')),
    ('ice',                   ('i', '#c4ddf2', '얼음')),
    ('powder_snow',           ('p', '#e4eef6', '가루눈')),
    ('stone',                 ('.', '#7a7a7a', '돌')),
    ('cracked_stone_bricks',  ('x', '#82827f', '금 간 돌벽돌')),
    ('stone_brick_slab',      ('_', '#9a9a9a', '돌벽돌 반 블록')),
    ('campfire',              ('^', '#c86a2b', '모닥불')),
    ('barrel',                ('a', '#a07743', '통')),
    ('jigsaw',                ('J', '#ff2fa0', '직소')),
    ('structure_void',        (' ', '#ffffff', '구조물 공백')),
    ('air',                   ('.', None, '공기')),
])

FACE_KO = OrderedDict([('west', '서'), ('east', '동'), ('north', '북'),
                       ('south', '남'), ('up', '위'), ('down', '아래')])


# --- reading ----------------------------------------------------------------------------
def load(path):
    root = nbt.read(path)
    sx, sy, sz = [int(v) for v in root['size']]
    palette = [(nbt.palette_name(e).replace('minecraft:', ''), dict(nbt.palette_props(e) or {}))
               for e in root['palette']]
    grid = {}
    jigsaws = []
    for b in root['blocks']:
        x, y, z = [int(v) for v in b['pos']]
        state = int(b['state'])
        grid[(x, y, z)] = state
        if palette[state][0] == 'jigsaw':
            meta = b.get('nbt') or {}
            jigsaws.append({
                'pos': (x, y, z),
                'orientation': str(palette[state][1].get('orientation', '')),
                'name': str(meta.get('name', '')),
                'target': str(meta.get('target', '')),
                'pool': str(meta.get('pool', '')),
                'final_state': str(meta.get('final_state', '')),
            })
    return {'name': os.path.splitext(os.path.basename(path))[0], 'size': (sx, sy, sz),
            'palette': palette, 'grid': grid, 'jigsaws': jigsaws,
            'entities': len(root.get('entities') or [])}


def block_at(piece, x, y, z):
    """The block name at a coordinate, or None for air and for anything not saved."""
    state = piece['grid'].get((x, y, z))
    if state is None:
        return None
    name = piece['palette'][state][0]
    return None if name == 'air' else name


def load_family(family):
    pieces = OrderedDict()
    for path in sorted(glob.glob(os.path.join(DATA, 'structure', family, '*.nbt'))):
        piece = load(path)
        pieces[piece['name']] = piece
    return pieces


def load_pools(family):
    pools = OrderedDict()
    for path in sorted(glob.glob(os.path.join(DATA, 'worldgen', 'template_pool', family, '*.json'))):
        with io.open(path, encoding='utf-8') as fh:
            raw = json.load(fh)
        elements = [(int(e.get('weight', 1)), e['element'].get('location', '?'))
                    for e in raw.get('elements', [])]
        pools[os.path.splitext(os.path.basename(path))[0]] = {
            'fallback': raw.get('fallback', 'minecraft:empty'), 'elements': elements}
    return pools


def load_json(*parts):
    with io.open(os.path.join(DATA, *parts), encoding='utf-8') as fh:
        return json.load(fh)


# --- geometry read back out of the blocks -----------------------------------------------
def openings(piece):
    """Where each face of the piece is open, as the bounding box of its air.

    This is what decides whether two pieces that meet actually let a player through, and it
    is not written down anywhere else - the pool JSON only says which pieces may meet.
    """
    sx, sy, sz = piece['size']
    found = OrderedDict()
    planes = {
        'west':  [(0, y, z) for y in range(sy) for z in range(sz)],
        'east':  [(sx - 1, y, z) for y in range(sy) for z in range(sz)],
        'north': [(x, y, 0) for x in range(sx) for y in range(sy)],
        'south': [(x, y, sz - 1) for x in range(sx) for y in range(sy)],
        'down':  [(x, 0, z) for x in range(sx) for z in range(sz)],
        'up':    [(x, sy - 1, z) for x in range(sx) for z in range(sz)],
    }
    for face, cells in planes.items():
        air = [c for c in cells if block_at(piece, *c) is None]
        if not air:
            continue
        axes = {'west': (2, 1), 'east': (2, 1), 'north': (0, 1), 'south': (0, 1),
                'down': (0, 2), 'up': (0, 2)}[face]
        first = sorted({c[axes[0]] for c in air})
        second = sorted({c[axes[1]] for c in air})
        label = {'west': 'z', 'east': 'z', 'north': 'x', 'south': 'x',
                 'down': 'x', 'up': 'x'}[face]
        label2 = {'west': 'y', 'east': 'y', 'north': 'y', 'south': 'y',
                  'down': 'z', 'up': 'z'}[face]
        found[face] = '%s %d–%d, %s %d–%d (%d칸)' % (
            label, first[0], first[-1], label2, second[0], second[-1], len(air))
    return found


def counts(piece):
    tally = Counter()
    for state in piece['grid'].values():
        name = piece['palette'][state][0]
        if name != 'air':
            tally[name] += 1
    return tally


# --- panels: one 2D picture each --------------------------------------------------------
def facing(orientation):
    """A jigsaw's orientation is `<front>_<top>`; only the front decides who may attach."""
    return orientation.split('_')[0] if orientation else ''


def layer_panels(piece):
    """Every Y layer, north up, x to the east. Identical neighbours collapse into a range."""
    sx, sy, sz = piece['size']
    out = []
    for y in range(sy):
        rows = [[block_at(piece, x, y, z) for x in range(sx)] for z in range(sz)]
        marks = [(j['pos'][0], j['pos'][2], facing(j['orientation']), j['name'])
                 for j in piece['jigsaws'] if j['pos'][1] == y]
        out.append({'key': (repr(rows), repr(sorted(marks))), 'rows': rows, 'marks': marks,
                    'y': y, 'axes': ('x →동', 'z ↓남')})
    merged = []
    for panel in out:
        if merged and merged[-1]['key'] == panel['key']:
            merged[-1]['upto'] = panel['y']
        else:
            panel['upto'] = panel['y']
            merged.append(panel)
    for panel in merged:
        panel['label'] = ('y = %d' % panel['y'] if panel['upto'] == panel['y']
                          else 'y = %d–%d' % (panel['y'], panel['upto']))
    return merged


def section_panels(piece):
    """Two vertical cuts through the middle of the piece, sky up."""
    sx, sy, sz = piece['size']
    cx, cz = sx // 2, sz // 2
    east = {'rows': [[block_at(piece, x, y, cz) for x in range(sx)] for y in range(sy - 1, -1, -1)],
            'marks': [(j['pos'][0], sy - 1 - j['pos'][1], facing(j['orientation']), j['name'])
                      for j in piece['jigsaws'] if j['pos'][2] == cz],
            'label': '단면 z = %d' % cz, 'axes': ('x →동', 'y ↑하늘')}
    south = {'rows': [[block_at(piece, cx, y, z) for z in range(sz)] for y in range(sy - 1, -1, -1)],
             'marks': [(j['pos'][2], sy - 1 - j['pos'][1], facing(j['orientation']), j['name'])
                       for j in piece['jigsaws'] if j['pos'][0] == cx],
             'label': '단면 x = %d' % cx, 'axes': ('z →남', 'y ↑하늘')}
    return [east, south]


# --- the skeleton: the part of the structure that is not random --------------------------
STEP = {'north': (0, 0, -1), 'south': (0, 0, 1), 'west': (-1, 0, 0), 'east': (1, 0, 0),
        'up': (0, 1, 0), 'down': (0, -1, 0)}
OPPOSITE = {'north': 'south', 'south': 'north', 'west': 'east', 'east': 'west',
            'up': 'down', 'down': 'up'}


ROT = {'north': 'east', 'east': 'south', 'south': 'west', 'west': 'north'}


def rotated(piece, k):
    """The piece turned k quarter turns, the way vanilla turns a child to meet its parent.

    Only positions and jigsaw facings are turned: the drawing colours by block name, which a
    rotation does not change."""
    grid, jigsaws, size = piece['grid'], piece['jigsaws'], piece['size']
    for _ in range(k):
        sx, sy, sz = size
        grid = {(sz - 1 - z, y, x): v for (x, y, z), v in grid.items()}
        turned = []
        for j in jigsaws:
            x, y, z = j['pos']
            spin = dict(j)
            spin['pos'] = (sz - 1 - z, y, x)
            front, top = (j['orientation'].split('_') + ['up'])[:2]
            spin['orientation'] = '%s_%s' % (ROT.get(front, front), ROT.get(top, top))
            turned.append(spin)
        jigsaws, size = turned, (sz, sy, sx)
    out = dict(piece)
    out['grid'], out['jigsaws'], out['size'] = grid, jigsaws, size
    return out


def assemble(pieces, pools, start_pool, limit=64):
    """Walk the chains that can only come out one way, and note where each piece lands.

    A jigsaw whose pool holds a single element, pointed at a child that has a single jigsaw
    able to receive it, leaves nothing to chance: the child lands at a fixed offset. Vanilla
    puts the child's jigsaw right against the parent's, facing back at it, so the offset is
    `parent + jigsaw + 그 방향 한 칸 - 자식 직소`. Whole-structure rotation moves all of them
    together, so the relative picture drawn from this is the one the game builds.

    Everything else - which passage follows which - is the random part, and it is left out.
    """
    start = pools.get(start_pool, {}).get('elements', [])
    if len(start) != 1:
        return []
    placed = [{'name': start[0][1].split('/')[-1], 'at': (0, 0, 0), 'via': '시작 풀', 'by': ''}]
    queue = [0]
    while queue and len(placed) < limit:
        parent = placed[queue.pop(0)]
        piece = pieces.get(parent['name'])
        if piece is None:
            continue
        for j in piece['jigsaws']:
            pool = pools.get(j['pool'].split('/')[-1])
            if not pool or len(pool['elements']) != 1:
                continue
            child_name = pool['elements'][0][1].split('/')[-1]
            child = pieces.get(child_name)
            if child is None or child_name == parent['name']:
                continue                       # a cap that calls its own pool never ends
            front = facing(j['orientation'])
            able = []
            for turn in range(4):              # vanilla turns the child until the two meet
                spun = rotated(child, turn)
                able = [c for c in spun['jigsaws'] if c['name'] == j['target']
                        and facing(c['orientation']) == OPPOSITE[front]]
                if able:
                    child = spun
                    break
            if len(able) != 1:
                continue                       # ambiguous: vanilla would pick one at random
            step, mine = STEP[front], able[0]['pos']
            at = tuple(parent['at'][k] + j['pos'][k] + step[k] - mine[k] for k in range(3))
            if any(p['name'] == child_name and p['at'] == at for p in placed):
                continue
            placed.append({'name': child_name, 'at': at, 'by': parent['name'],
                           'via': '%s %s' % (FACE_KO[front], j['name'].split(':')[-1]),
                           'piece': child})
            queue.append(len(placed) - 1)
    return placed


def composite(placed, pieces):
    """Lay the placed pieces down in order, a later one writing over an earlier one."""
    blocks, owner = {}, {}
    for spot in placed:
        piece = spot.get('piece') or pieces[spot['name']]
        ox, oy, oz = spot['at']
        for (x, y, z), state in piece['grid'].items():
            name = piece['palette'][state][0]
            if name == 'structure_void':       # "leave whatever is already here"
                continue
            key = (ox + x, oy + y, oz + z)
            blocks[key] = None if name == 'air' else name
            if name == 'air':
                owner.pop(key, None)      # colour the shape, not the box
            else:
                owner[key] = spot['name']
    return blocks, owner


PIECE_COLORS = ['#4e79a7', '#f28e2b', '#59a14f', '#e15759', '#b07aa1', '#76b7b2',
                '#edc948', '#9c755f', '#ff9da7', '#8cd17d', '#d37295', '#499894']


def piece_styles(placed):
    names = []
    for spot in placed:
        if spot['name'] not in names:
            names.append(spot['name'])
    return OrderedDict((n, (chr(ord('a') + i % 26), PIECE_COLORS[i % len(PIECE_COLORS)], n))
                       for i, n in enumerate(names))


def assembly_panels(placed, pieces, floors=()):
    """Sections and floor plans of the skeleton, once as blocks and once coloured by piece."""
    blocks, owner = composite(placed, pieces)
    xs = [k[0] for k in blocks]
    ys = [k[1] for k in blocks]
    zs = [k[2] for k in blocks]
    x0, x1, y0, y1, z0, z1 = min(xs), max(xs), min(ys), max(ys), min(zs), max(zs)
    cx, cz = (x0 + x1) // 2, (z0 + z1) // 2

    def cut(source, label, kind, fixed):
        if kind == 'z':
            rows = [[source.get((x, y, fixed)) for x in range(x0, x1 + 1)]
                    for y in range(y1, y0 - 1, -1)]
            axes = ('x →동', 'y ↑하늘')
        elif kind == 'x':
            rows = [[source.get((fixed, y, z)) for z in range(z0, z1 + 1)]
                    for y in range(y1, y0 - 1, -1)]
            axes = ('z →남', 'y ↑하늘')
        else:
            rows = [[source.get((x, fixed, z)) for x in range(x0, x1 + 1)]
                    for z in range(z0, z1 + 1)]
            axes = ('x →동', 'z ↓남')
        return {'rows': rows, 'marks': [], 'label': label, 'axes': axes}

    block_panels = [cut(blocks, '단면 z = %d' % cz, 'z', cz),
                    cut(blocks, '단면 x = %d' % cx, 'x', cx)]
    owner_panels = [cut(owner, '조각 지도  단면 z = %d' % cz, 'z', cz),
                    cut(owner, '조각 지도  단면 x = %d' % cx, 'x', cx)]
    for label, y in floors:
        block_panels.append(cut(blocks, '%s  y = %d' % (label, y), 'y', y))
        owner_panels.append(cut(owner, '조각 지도  %s  y = %d' % (label, y), 'y', y))
    return block_panels, owner_panels, (x1 - x0 + 1, y1 - y0 + 1, z1 - z0 + 1)


# --- SVG --------------------------------------------------------------------------------
ARROW = {'north': '▲', 'south': '▼', 'west': '◀', 'east': '▶', 'up': '◆', 'down': '◇'}


def esc(text):
    return (text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;'))


def cell_size(panels):
    biggest = max(max(len(p['rows']), len(p['rows'][0])) for p in panels)
    for limit, size in ((8, 22), (14, 18), (24, 12), (40, 8), (64, 6), (200, 4)):
        if biggest <= limit:
            return size
    return 3


def draw_panel(out, panel, ox, oy, cs, grid_step, styles=STYLE):
    rows = panel['rows']
    height, width = len(rows), len(rows[0])
    out.append('<text x="%d" y="%d" class="cap">%s</text>'
               % (ox, oy - 18, esc(panel['label'])))
    out.append('<rect x="%d" y="%d" width="%d" height="%d" fill="#fbfbfb" stroke="#bbb"/>'
               % (ox, oy, width * cs, height * cs))
    # One path per colour, not one rect per block: a 39x56 piece is 85k blocks and the
    # browser should not be asked to lay out 85k elements.
    paths = OrderedDict()
    for r, row in enumerate(rows):
        c = 0
        while c < width:
            name = row[c]
            run = 1
            while c + run < width and row[c + run] == name:
                run += 1
            if name is not None:
                fill = styles.get(name, ('?', '#cc00cc', name))[1]
                if fill:
                    paths.setdefault(fill, []).append('M%d %dh%dv1h-%dz' % (c, r, run, run))
            c += run
    for fill, data in paths.items():
        out.append('<path transform="translate(%d,%d) scale(%d)" fill="%s" d="%s"/>'
                   % (ox, oy, cs, fill, ''.join(data)))
    if cs >= 8:                       # one line per block, so blocks can be counted off
        fine = ['M%d %dv%d' % (ox + g * cs, oy, height * cs) for g in range(1, width)]
        fine += ['M%d %dh%d' % (ox, oy + g * cs, width * cs) for g in range(1, height)]
        out.append('<path class="fine" d="%s"/>' % ''.join(fine))
    for g in range(0, width + 1, grid_step):
        out.append('<line x1="%d" y1="%d" x2="%d" y2="%d" class="grid"/>'
                   % (ox + g * cs, oy, ox + g * cs, oy + height * cs))
    for g in range(0, height + 1, grid_step):
        out.append('<line x1="%d" y1="%d" x2="%d" y2="%d" class="grid"/>'
                   % (ox, oy + g * cs, ox + width * cs, oy + g * cs))
    if cs >= 12:                      # rulers, so a block can be named by coordinate
        for g in range(width):
            out.append('<text x="%.1f" y="%d" class="tick">%d</text>'
                       % (ox + g * cs + cs / 2.0, oy - 3, g))
        for g in range(height):
            out.append('<text x="%d" y="%.1f" class="tick" text-anchor="end">%d</text>'
                       % (ox - 4, oy + g * cs + cs * 0.72, g))
    for col, row, face, _name in panel['marks']:
        cx, cy = ox + col * cs + cs / 2.0, oy + row * cs + cs / 2.0
        out.append('<circle cx="%.1f" cy="%.1f" r="%.1f" fill="#ff2fa0" stroke="#fff"/>'
                   % (cx, cy, cs * 0.5))
        out.append('<text x="%.1f" y="%.1f" class="arrow" font-size="%.1f">%s</text>'
                   % (cx, cy + cs * 0.32, cs * 0.9, ARROW.get(face, '?')))
    return width * cs, height * cs


def write_svg(path, title, subtitle, panels, used, grid_step=7, max_width=1320,
              styles=STYLE):
    cs = cell_size(panels)
    left = 30 if cs >= 12 else 12     # room for the row ruler
    widths = [len(p['rows'][0]) * cs for p in panels]
    heights = [len(p['rows']) * cs for p in panels]
    gap, top = 30, 78
    out = []
    x, y, row_h, placed = 0, 0, 0, []
    for i, panel in enumerate(panels):
        if x and x + widths[i] + left > max_width:
            x, y, row_h = 0, y + row_h + gap, 0
        placed.append((panel, x, y))
        x += widths[i] + gap + left
        row_h = max(row_h, heights[i] + 30)
    total_w = max(px + left + w for (_, px, _), w in zip(placed, widths)) + 20
    total_h = y + row_h + top + 30

    legend = [n for n in styles if n in used]
    legend_rows = (len(legend) + 3) // 4
    total_h += legend_rows * 20 + 26

    body = []
    for panel, px, py in placed:
        draw_panel(body, panel, px + left, py + top, cs, grid_step, styles)

    ly = y + row_h + top + 26
    body.append('<text x="12" y="%d" class="cap">범례</text>' % ly)
    for i, name in enumerate(legend):
        glyph, fill, label = styles[name]
        lx = 12 + (i % 4) * 290
        yy = ly + 16 + (i // 4) * 20
        if fill:
            body.append('<rect x="%d" y="%d" width="12" height="12" fill="%s" stroke="#999"/>'
                        % (lx, yy, fill))
        body.append('<text x="%d" y="%d" class="leg">%s  %s  %s</text>'
                    % (lx + 18, yy + 11, esc(glyph), esc(label), esc(name)))

    head = ('<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d" '
            'viewBox="0 0 %d %d" shape-rendering="crispEdges" '
            'font-family="Consolas,\'Malgun Gothic\',\'Noto Sans KR\',monospace">'
            % (total_w, total_h, total_w, total_h))
    style = ('<style>text{fill:#222;shape-rendering:auto}.cap{font-size:13px;font-weight:bold}'
             '.leg{font-size:12px}.sub{font-size:12px;fill:#666}'
             '.tick{font-size:8px;fill:#999;text-anchor:middle}'
             '.arrow{font-size:10px;fill:#fff;text-anchor:middle}'
             '.fine{stroke:#000;stroke-opacity:.07;stroke-width:1;fill:none}'
             '.grid{stroke:#000;stroke-opacity:.30;stroke-width:1}</style>')
    head += style
    head += '<rect width="100%" height="100%" fill="#fff"/>'
    head += '<text x="12" y="22" class="cap" font-size="16">%s</text>' % esc(title)
    head += '<text x="12" y="40" class="sub">%s</text>' % esc(subtitle)
    with io.open(path, 'w', encoding='utf-8') as fh:
        fh.write(head + ''.join(out) + ''.join(body) + '</svg>')


# --- ASCII ------------------------------------------------------------------------------
def ascii_panel(panel, styles=STYLE):
    lines = ['%s   %s, %s' % (panel['label'], panel['axes'][0], panel['axes'][1])]
    marks = {(c, r): f for c, r, f, _n in panel['marks']}
    for r, row in enumerate(panel['rows']):
        text = ''
        for c, name in enumerate(row):
            if (c, r) in marks:
                text += 'J'
            elif name is None:
                text += '.'
            else:
                text += styles.get(name, ('?',))[0]
        lines.append('  %s' % text)
    return '\n'.join(lines)


# --- the document ------------------------------------------------------------------------
def mermaid(family, pieces, pools, start_pool):
    """Which pool hands out which piece, and which pool each of that piece's jigsaws calls."""
    def pid(name):
        return 'P_' + re.sub(r'\W', '_', name)

    def eid(name):
        return 'E_' + re.sub(r'\W', '_', name)

    lines = ['```mermaid', 'flowchart LR']
    for pool, body in pools.items():
        shape = '(["%s"])' % pool
        lines.append('  %s%s' % (pid(pool), shape))
    for name in pieces:
        lines.append('  %s["%s"]' % (eid(name), name))
    seen = set()
    for pool, body in pools.items():
        for weight, location in body['elements']:
            piece = location.split('/')[-1]
            edge = (pid(pool), eid(piece), weight)
            if edge in seen:
                continue
            seen.add(edge)
            lines.append('  %s -- %d --> %s' % (pid(pool), weight, eid(piece)))
    for name, piece in pieces.items():
        for j in piece['jigsaws']:
            if j['pool'] not in pools and j['pool'].split('/')[-1] not in pools:
                continue                       # minecraft:empty - the jigsaw calls nobody
            pool = j['pool'].split('/')[-1]
            edge = (eid(name), pid(pool))
            if edge in seen:
                continue
            seen.add(edge)
            lines.append('  %s -.-> %s' % (eid(name), pid(pool)))
    lines.append('  %s:::start' % pid(start_pool))
    lines.append('  classDef start fill:#ffe9a8,stroke:#c99a00,stroke-width:2px')
    lines.append('```')
    return '\n'.join(lines)


def piece_section(family, name, piece, pools, note):
    sx, sy, sz = piece['size']
    cells = (' — %d×%d×%d 셀' % (sx // 7, sy // 7, sz // 7)
             if sx % 7 == sy % 7 == sz % 7 == 0 else '')
    lines = ['### `%s` — %d×%d×%d%s' % (name, sx, sy, sz, cells), '']
    if note:
        lines += [note.strip(), '']

    holders = ['`%s` (가중치 %d)' % (pool, w)
               for pool, body in pools.items()
               for w, loc in body['elements'] if loc.split('/')[-1] == name]
    lines.append('**어느 풀에 있나** — %s' % (', '.join(holders) if holders else '없음 (풀에 안 들어 있다)'))
    lines.append('')

    if piece['jigsaws']:
        lines += ['| 직소 위치 | 향 | name | target | pool |', '|---|---|---|---|---|']
        for j in sorted(piece['jigsaws'], key=lambda j: (j['pos'][1], j['pos'][2], j['pos'][0])):
            lines.append('| %s | %s %s | `%s` | `%s` | `%s` |' % (
                '(%d, %d, %d)' % j['pos'], ARROW.get(facing(j['orientation']), '?'),
                FACE_KO.get(facing(j['orientation']), '?'),
                j['name'].split(':')[-1], j['target'].split(':')[-1],
                j['pool'].split(':')[-1] if j['pool'] != 'minecraft:empty' else '—'))
        lines.append('')

    holes = openings(piece)
    if holes:
        lines.append('**뚫린 면** — %s' % ' / '.join(
            '%s: %s' % (FACE_KO[f], v) for f, v in holes.items()))
        lines.append('')

    tally = counts(piece)
    top = ', '.join('%s %d' % (STYLE.get(n, ('?', '', n))[2], c) for n, c in tally.most_common(8))
    lines.append('**블록** — %s' % top)
    lines.append('')
    lines.append('![%s](img/%s/%s.svg)' % (name, family, name))
    lines.append('')

    panels = layer_panels(piece)
    sections = section_panels(piece)
    if sx <= 21 and sz <= 21:
        lines += ['<details><summary>층별 지도 (텍스트)</summary>', '', '```']
        lines += [ascii_panel(p) for p in panels]
        lines += ['```', '', '</details>', '']
    if sx <= 45 and sz <= 45 and sy <= 60 and (sy > 7 or sx > 21):
        lines += ['<details><summary>세로 단면 (텍스트)</summary>', '', '```']
        lines += [ascii_panel(p) for p in sections]
        lines += ['```', '', '</details>', '']
    return '\n'.join(lines)


def build(family):
    pieces = load_family(family)
    pools = load_pools(family)
    structure = load_json('worldgen', 'structure', '%s.json' % family)
    sets = {'dungeon': 'dungeons', 'pyramid': 'pyramids', 'tower': 'towers',
            'swamp': 'swamps', 'ice': 'fortresses', 'temple': 'temples'}
    placement = load_json('worldgen', 'structure_set', '%s.json' % sets[family])['placement']
    start_pool = structure['start_pool'].split('/')[-1]

    img_dir = os.path.join(OUT, 'img', family)
    if not os.path.isdir(img_dir):
        os.makedirs(img_dir)
    unknown = set()
    for name, piece in pieces.items():
        used = set(counts(piece))
        unknown |= {n for n in used if n not in STYLE}
        panels = layer_panels(piece) + section_panels(piece)
        for panel in panels:
            panel.setdefault('label', '')
        sx, sy, sz = piece['size']
        write_svg(os.path.join(img_dir, '%s.svg' % name),
                  '%s / %s   %d×%d×%d' % (family, name, sx, sy, sz),
                  '북쪽이 위, 오른쪽이 동쪽. 옅은 선은 7칸 격자. 분홍 점은 직소이고 '
                  '화살표는 그 직소가 보는 방향이다.',
                  panels, used)

    intro = INTRO[family]
    doc = [intro['title'], '',
           '> 이 문서는 `python tools/gen_level_doc.py %s`가 만든다. 조각을 고치면 다시 돌린다. '
           '그림과 표는 게임이 읽는 파일(`structure/%s/*.nbt`, `worldgen/**`)에서 그대로 읽어 '
           '온 것이라 모드와 어긋날 수 없다. 설명 문장만 사람이 쓴다 '
           '(`tools/gen_level_doc.py`의 `INTRO`·`NOTES`).' % (family, family), '',
           '## 1. 한눈에', '', intro['summary'].strip(), '',
           '| 항목 | 값 |', '|---|---|',
           '| 생성 단계 | `%s` |' % structure['step'],
           '| 바이옴 | `%s` |' % structure['biomes'],
           '| 간격 / 최소거리 | spacing %d / separation %d |' % (
               placement['spacing'], placement['separation']),
           '| 직소 깊이 | %d ~ %d (`sydungeon:ranged_jigsaw`) |' % (
               structure['size']['min_inclusive'], structure['size']['max_inclusive']),
           '| 시작 풀 | `%s` |' % start_pool,
           '| 조각 / 풀 | %d개 / %d개 |' % (len(pieces), len(pools)), '',
           '## 2. 조립 원리', '', intro['principle'].strip(), '',
           '## 3. 풀 배선', '',
           '풀이 어떤 조각을 내놓는지(실선, 숫자는 가중치)와 그 조각의 직소가 다시 어떤 풀을 '
           '부르는지(점선)다. 직소 생성은 이 그래프를 깊이만큼 따라간다.', '',
           mermaid(family, pieces, pools, start_pool), '',
           '| 풀 | fallback | 원소 (가중치) |', '|---|---|---|']
    for pool, body in pools.items():
        elements = ', '.join('`%s` %d' % (loc.split('/')[-1], w) for w, loc in body['elements'])
        doc.append('| `%s` | `%s` | %s |' % (
            pool, body['fallback'].split('/')[-1] if '/' in body['fallback'] else body['fallback'],
            elements))
    skeleton = assemble(pieces, pools, start_pool)
    if len(skeleton) > 2:
        blocks, owners, span = assembly_panels(skeleton, pieces, intro.get('floors', ()))
        marks = piece_styles(skeleton)
        write_svg(os.path.join(img_dir, '_assembly.svg'),
                  '%s / 뼈대   %d×%d×%d' % (family, span[0], span[1], span[2]),
                  '무작위 조각을 뺀, 반드시 이렇게 놓이는 부분만 그린 것이다.',
                  blocks, {n for row in blocks for line in row['rows'] for n in line if n})
        write_svg(os.path.join(img_dir, '_assembly_pieces.svg'),
                  '%s / 뼈대 — 어느 조각인가' % family,
                  '같은 단면을 조각별로 칠했다. 색이 바뀌는 자리가 조각의 경계다.',
                  owners, {n for row in owners for line in row['rows'] for n in line if n},
                  styles=marks)
        doc += ['', '## 4. 뼈대 — 반드시 이렇게 놓이는 부분', '', intro['skeleton'].strip(), '',
                '| 조각 | 놓이는 자리 (시작 조각 기준) | 누가 놓나 |', '|---|---|---|']
        for spot in skeleton:
            doc.append('| `%s` | (%d, %d, %d) | %s |' % (
                (spot['name'],) + spot['at'] +
                ('%s의 %s 직소' % (spot['by'], spot['via']) if spot['by'] else '시작 풀',)))
        doc += ['', '![뼈대](img/%s/_assembly.svg)' % family, '',
                '![조각 지도](img/%s/_assembly_pieces.svg)' % family, '',
                '## 5. 조각', '']
    else:
        doc += ['', '## 4. 조각', '']
    doc += ['',
            '그림은 조각 하나를 **층마다 한 장씩** 블록 단위로 그린 것이다. 같은 층이 이어지면 '
            '`y = 2–5`처럼 묶었고, 마지막 두 장은 가운데를 자른 세로 단면이다. '
            '분홍 점이 직소, 화살표가 그 직소가 보는 방향이다 — **마주 본 직소끼리만 붙는다.**', '']
    for name in intro.get('order', list(pieces)):
        if name not in pieces:
            continue
        doc.append(piece_section(family, name, pieces[name], pools,
                                 NOTES.get('%s/%s' % (family, name), '')))
        doc.append('')
    for name in pieces:
        if name not in intro.get('order', list(pieces)):
            doc.append(piece_section(family, name, pieces[name], pools,
                                     NOTES.get('%s/%s' % (family, name), '')))
            doc.append('')

    if intro.get('outro'):
        doc += [intro['outro'].strip(), '']

    path = os.path.join(OUT, '%s.md' % family)
    with io.open(path, 'w', encoding='utf-8') as fh:
        fh.write('\n'.join(doc).rstrip() + '\n')
    print('%-8s %2d pieces, %2d pools -> %s' % (family, len(pieces), len(pools),
                                                os.path.relpath(path, ROOT)))
    if unknown:
        print('  !! STYLE has no entry for: %s' % ', '.join(sorted(unknown)))
    return unknown


# --- prose --------------------------------------------------------------------------------
# The only hand-written part of the document. Kept in its own module so that editing a
# room's description never risks the code that draws it.
from level_notes import INTRO, NOTES  # noqa: E402


if __name__ == '__main__':
    wanted = sys.argv[1:] or list(FAMILIES)
    bad = set()
    for family in wanted:
        if family not in FAMILIES:
            raise SystemExit('unknown family %r; one of %s' % (family, ', '.join(FAMILIES)))
        bad |= build(family)
    raise SystemExit(1 if bad else 0)
