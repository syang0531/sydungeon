# -*- coding: utf-8 -*-
"""The Mountain Shrine: a path of gates through the cherry grove to a place to rest.

    python tools/generate_shrine.py        (or through make_pieces.py)

Writes data/sydungeon/structure/shrine/*.nbt and the pools that join them.

THE SECOND SMALL ONE, AND THE ONLY CHEST THAT MATTERS
No boss (concepts.md section 4.11 says so) and nothing hostile in it. What makes it worth
finding is the **altar chest**, and that chest breaks section 2.1 on purpose: progression
items are not supposed to sit in chests, because a chest can be opened without a fight. Six
ender pearls and eight bottles of experience are in this one anyway, because the shrine's
whole idea is that it asks nothing of you. It is written down as an exception in the concept
and it stays an exception - the only one in the mod.

WHY IT DOES NOT CLIMB A MOUNTAIN
The concept has stone steps and gates climbing a mountainside to a shrine at the top. A chain
of flights would do it, but each link is placed by the height of its own jigsaw rather than by
the ground (CLAUDE.md section 18), so the top of the climb lands wherever the arithmetic puts
it and the last flights stand in the air on anything but the one slope that happens to match.

So the climb is inside the compound, where its geometry is ours: the path runs level through
the grove, the compound stands at the end of it, and the steps up to the altar are cut into a
plinth the piece builds itself. A shrine on a mount, which is what one looks like anyway.

THE HIDDEN ROOM
The puzzle in the concept was a lantern order. What is here instead is the wizard's tower's
sealed room (section 15): a cellar under the altar with no way in, its jigsaw buried in the
wall, so the only way to it is to notice that the plinth is bigger than the room on top of it.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import nbt  # noqa: E402
from generate_pieces import Piece  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DST = os.path.join(ROOT, 'src', 'main', 'resources', 'data', 'sydungeon', 'structure', 'shrine')
POOL_JSON = os.path.join(ROOT, 'src', 'main', 'resources', 'data', 'sydungeon', 'worldgen',
                         'template_pool', 'shrine')

NS = 'sydungeon'
PATH = NS + ':shr_path'          # the path's connector
SEALED = NS + ':shr_sealed'      # the cellar's, buried in the plinth's wall
EMPTY = 'minecraft:empty'
PRIORITY = 10

CELL = 7
COURT = 21                       # the compound is three cells across
FOOT = 5                         # footing under everything, so a path does not stand on stumps
PLINTH = 7                       # how high the altar stands above the court

CHERRY = 'minecraft:cherry_log'
STRIP = 'minecraft:stripped_cherry_log'
PLANK = 'minecraft:cherry_planks'
FENCE = 'minecraft:cherry_fence'
LEAF = 'minecraft:cherry_leaves'
PETAL = 'minecraft:pink_petals'
SAPLING = 'minecraft:cherry_sapling'
SMOOTH = 'minecraft:smooth_stone'
SLAB = 'minecraft:smooth_stone_slab'
STONE = 'minecraft:stone'
POLISH = 'minecraft:polished_andesite'
ANDESITE = 'minecraft:andesite'
WALL = 'minecraft:andesite_wall'
STAIR = 'minecraft:stone_stairs'
LANTERN = 'minecraft:lantern'
MAGMA = 'minecraft:magma_block'
WATER = 'minecraft:water'
CHAIN = 'minecraft:iron_chain'
AIR = 'minecraft:air'

HANGING = {'hanging': 'true', 'waterlogged': 'false'}
STANDING = {'hanging': 'false', 'waterlogged': 'false'}
POST = {'north': 'false', 'south': 'false', 'east': 'false', 'west': 'false',
        'up': 'true', 'waterlogged': 'false'}
LEAVES = {'distance': '7', 'persistent': 'true', 'waterlogged': 'false'}
PETALS = {'flower_amount': '3', 'facing': 'north'}

POOL = {k: NS + ':shrine/' + k for k in ['start', 'paths', 'path_caps', 'cellar']}


def chest(table, facing='north'):
    return ('minecraft:chest', {'facing': facing, 'type': 'single', 'waterlogged': 'false'},
            {'id': 'minecraft:chest', 'LootTable': NS + ':chests/' + table})


def stairs(facing, half='bottom'):
    return {'facing': facing, 'half': half, 'shape': 'straight', 'waterlogged': 'false'}


def ground(sx, sz, top=STONE, height=14):
    """Footing that reaches down, a surface at the start's level, and air carved out above."""
    p = Piece(sx, height, sz, AIR)
    p.box(0, 0, 0, sx - 1, FOOT - 1, sz - 1, STONE)
    p.box(0, FOOT, 0, sx - 1, FOOT, sz - 1, top)
    p.box(0, FOOT + 1, 0, sx - 1, height - 1, sz - 1, AIR)
    return p


PATH_AT = {'west': (0, FOOT, 3, 'west_up'), 'east': (CELL - 1, FOOT, 3, 'east_up'),
           'north': (3, FOOT, 0, 'north_up'), 'south': (3, FOOT, CELL - 1, 'south_up')}


def way(p, side, pool, name=PATH, target=PATH, priority=0):
    x, y, z, orientation = PATH_AT[side]
    p.jigsaw(x, y, z, orientation, pool, STONE, priority=priority, name=name, target=target)


def torii(p, x, z, axis='x', height=4):
    """A gate: two posts, a lintel over them and a second beam under it. The path runs
    through, so nothing is written in the two blocks between the posts."""
    dx, dz = (1, 0) if axis == 'x' else (0, 1)
    for s in (-2, 2):
        for y in range(FOOT + 1, FOOT + height):
            p.set(x + dx * s, y, z + dz * s, CHERRY, {'axis': 'y'})
    for s in range(-3, 4):
        p.set(x + dx * s, FOOT + height, z + dz * s, STRIP, {'axis': axis})
    for s in range(-2, 3):
        p.set(x + dx * s, FOOT + height - 1, z + dz * s, PLANK)
    for s in (-3, 3):
        p.set(x + dx * s, FOOT + height + 1, z + dz * s, SLAB,
              {'type': 'bottom', 'waterlogged': 'false'})


def path(kind):
    """One cell of the way there. Level, footed, and lit by lanterns on posts - the walk is
    the point, so nothing on it is dangerous."""
    doors = {'run': ['west', 'east'], 'bend': ['west', 'south'],
             'cross': ['west', 'east', 'north', 'south'],
             'gate': ['west', 'east'], 'rest': ['west'], 'garden': ['west', 'east'],
             'spring': ['west'], 'lantern': ['west', 'east', 'north', 'south']}[kind]
    p = ground(CELL, CELL)
    g, mid = FOOT, CELL // 2
    for side in doors:
        way(p, side, POOL['paths'])
    p.box(mid - 1, g, 0, mid + 1, g, CELL - 1, POLISH)          # the paving
    if 'north' in doors or 'south' in doors or kind in ('cross', 'lantern'):
        p.box(0, g, mid - 1, CELL - 1, g, mid + 1, POLISH)
    if kind == 'gate':
        torii(p, mid, mid, axis='z')
    elif kind == 'bend':
        p.box(mid - 1, g, mid - 1, CELL - 1, g, mid + 1, POLISH)
        p.set(1, g + 1, 1, SAPLING, {'stage': '0'})
    elif kind == 'rest':
        p.box(1, g + 1, 1, 1, g + 1, CELL - 2, SLAB, {'type': 'top', 'waterlogged': 'false'})
        p.set(CELL - 2, g + 1, mid, *chest('shrine_rest', 'west'))
        p.set(mid, g + 1, 1, 'minecraft:composter', {'level': '0'})
        for y in (g + 1, g + 2):
            p.set(CELL - 2, y, 1, CHERRY, {'axis': 'y'})
        p.set(CELL - 2, g + 3, 1, LANTERN, STANDING)
    elif kind == 'garden':
        for x in (1, CELL - 2):
            for y in range(g + 1, g + 4):
                p.set(x, y, 1, CHERRY, {'axis': 'y'})
            for dx in (-1, 0, 1):
                p.set(x + dx, g + 4, 1, LEAF, LEAVES)
            p.set(x, g + 4, 2, LEAF, LEAVES)
        p.set(mid, g + 1, CELL - 2, 'minecraft:pink_tulip')
    elif kind == 'spring':
        p.box(2, g, 2, 4, g, 4, WATER, {'level': '0'})
        p.box(2, g - 1, 2, 4, g - 1, 4, SMOOTH)
        p.set(3, g - 1, 3, MAGMA)                                # the steam, and you cannot
        p.box(1, g, 1, 1, g, CELL - 2, SLAB, {'type': 'top', 'waterlogged': 'false'})
        for x, z in ((1, 1), (CELL - 2, CELL - 2)):              # stand on it: water above,
            p.set(x, g + 1, z, WALL, POST)                       # stone all round
    elif kind == 'lantern':
        for y in range(g + 1, g + 4):
            p.set(mid, y, mid, CHERRY, {'axis': 'y'})
        p.set(mid, g + 4, mid, LANTERN, STANDING)
        for x, z in ((mid - 1, mid), (mid + 1, mid), (mid, mid - 1), (mid, mid + 1)):
            p.set(x, g + 3, z, CHAIN, {'axis': 'x' if x != mid else 'z',
                                       'waterlogged': 'false'})
    # petals last, and only where the ground under them is a whole block: a bench is a slab
    # and nothing grows on a slab
    for x in range(CELL):
        for z in range(CELL):
            if (p.grid[(x, g, z)][0] == STONE and p.grid[(x, g + 1, z)][0] == AIR
                    and (x * 3 + z * 7) % 4 == 0):
                p.set(x, g + 1, z, PETAL, PETALS)
    return p


def path_cap():
    """A closed gate at the end of a path: a low wall between two posts, so the way always
    finishes on something (section 4)."""
    p = ground(1, CELL)
    g = FOOT
    for z in range(CELL):
        p.set(0, g + 1, z, WALL, POST)
    for z in (2, 4):
        for y in (g + 1, g + 2):
            p.set(0, y, z, CHERRY, {'axis': 'y'})
    p.jigsaw(0, g, 3, 'west_up', POOL['path_caps'], STONE, name=PATH, target=PATH)
    return p


# ------------------------------------------------------------------------- the compound
def court():
    """The start: a walled compound with the altar on a plinth in the middle of it, and the
    paths leaving by all four gates."""
    n = COURT
    p = ground(n, n, top=STONE, height=FOOT + 18)
    g, mid = FOOT, n // 2
    for i in range(n):                                            # the compound wall
        for x, z in ((0, i), (n - 1, i), (i, 0), (i, n - 1)):
            if not (mid - 1 <= (z if x in (0, n - 1) else x) <= mid + 1):
                p.set(x, g + 1, z, WALL, POST)
                p.set(x, g + 2, z, WALL, POST)
    for x, z in ((0, 0), (0, n - 1), (n - 1, 0), (n - 1, n - 1)):  # corner posts
        for y in range(g + 1, g + 4):
            p.set(x, y, z, CHERRY, {'axis': 'y'})
        p.set(x, g + 4, z, LANTERN, STANDING)

    for side in ('west', 'east', 'north', 'south'):               # four gates, four paths
        if side == 'west':
            p.jigsaw(0, g, mid, 'west_up', POOL['paths'], STONE, priority=PRIORITY,
                     name=PATH, target=PATH)
            torii(p, 0, mid, axis='z')
        elif side == 'east':
            p.jigsaw(n - 1, g, mid, 'east_up', POOL['paths'], STONE, priority=PRIORITY,
                     name=PATH, target=PATH)
            torii(p, n - 1, mid, axis='z')
        elif side == 'north':
            p.jigsaw(mid, g, 0, 'north_up', POOL['paths'], STONE, priority=PRIORITY,
                     name=PATH, target=PATH)
            torii(p, mid, 0, axis='x')
        else:
            p.jigsaw(mid, g, n - 1, 'south_up', POOL['paths'], STONE, priority=PRIORITY,
                     name=PATH, target=PATH)
            torii(p, mid, n - 1, axis='x')

    # the plinth: seven up, and the climb the concept wanted cut into the court instead of
    # into a mountainside (see the note at the top). The flight runs along the south face one
    # block clear of it, not into it, because the inside of the plinth belongs to the cellar:
    # a block of rise per block of run, from the south-east corner to the north-west.
    p.box(mid - 4, g, mid - 4, mid + 4, g + PLINTH - 1, mid + 4, SMOOTH)
    p.box(mid - 4, g + PLINTH, mid - 4, mid + 4, g + PLINTH, mid + 4, POLISH)
    for i in range(1, PLINTH + 1):
        x = mid + 4 - i
        p.box(x, g, mid + 5, x, g + i - 1, mid + 5, SMOOTH)     # the mass under the flight
        p.set(x, g + i, mid + 5, STAIR, stairs('west'))

    # the shrine itself: four posts, a roof of slabs, the altar under it
    for x, z in ((mid - 2, mid - 2), (mid - 2, mid + 2), (mid + 2, mid - 2),
                 (mid + 2, mid + 2)):
        for y in range(g + PLINTH + 1, g + PLINTH + 4):
            p.set(x, y, z, CHERRY, {'axis': 'y'})
    for x in range(mid - 3, mid + 4):
        for z in range(mid - 3, mid + 4):
            p.set(x, g + PLINTH + 4, z, PLANK)
            if abs(x - mid) == 3 or abs(z - mid) == 3:
                p.set(x, g + PLINTH + 4, z, SLAB, {'type': 'bottom', 'waterlogged': 'false'})
    p.set(mid, g + PLINTH + 1, mid - 1, POLISH)                   # the altar
    p.set(mid, g + PLINTH + 2, mid - 1, *chest('shrine_altar', 'south'))
    p.set(mid - 1, g + PLINTH + 1, mid - 1, LANTERN, STANDING)
    p.set(mid + 1, g + PLINTH + 1, mid - 1, LANTERN, STANDING)
    for x in (mid - 2, mid + 2):                                  # hung from the roof boards
        p.set(x, g + PLINTH + 3, mid, LANTERN, HANGING)
    p.set(mid, g + PLINTH + 3, mid + 2, 'minecraft:bell',
          {'attachment': 'ceiling', 'facing': 'north', 'powered': 'false'})
    for x, z in ((mid - 2, mid + 1), (mid + 2, mid + 1)):
        p.set(x, g + PLINTH + 1, z, PETAL, PETALS)

    # and the sealed cellar: inside the plinth, with its jigsaw in the wall (section 15)
    p.jigsaw(mid + 4, g + 1, mid, 'west_up', POOL['cellar'], SMOOTH, priority=PRIORITY,
             name=PATH, target=SEALED)
    return p


def cellar():
    """Under the altar, with no way in. The jigsaw that places it is buried in the plinth, so
    from the court the plinth simply looks bigger than the shrine standing on it - and the
    only way in is to notice and dig (section 15)."""
    p = Piece(CELL, CELL, CELL, SMOOTH)
    p.box(1, 1, 1, CELL - 2, CELL - 2, CELL - 2, AIR)
    p.box(0, 0, 0, CELL - 1, 0, CELL - 1, POLISH)
    mid = CELL // 2
    p.jigsaw(CELL - 1, 1, mid, 'east_up', EMPTY, SMOOTH, name=SEALED, target=SEALED)
    p.set(1, 1, mid, *chest('shrine_cellar', 'west'))
    p.set(mid, 1, 1, POLISH)
    p.set(mid, 2, 1, LANTERN, STANDING)
    for x, z in ((1, 1), (CELL - 2, CELL - 2)):
        p.set(x, 1, z, WALL, POST)
    p.set(mid, 1, CELL - 2, PETAL, PETALS)
    return p


# ---------------------------------------------------------------------------------- pools
def element(location, weight):
    return ('    { "weight": %d, "element": { "element_type": "minecraft:single_pool_element",'
            '\n        "location": "%s:shrine/%s", "projection": "rigid", '
            '"processors": "%s:shrine_weathering" } }' % (weight, NS, location, NS))


def write_pool(name, elements, fallback):
    if not os.path.isdir(POOL_JSON):
        os.makedirs(POOL_JSON)
    text = ('{\n  "fallback": "%s",\n  "elements": [\n%s\n  ]\n}\n'
            % (fallback, ',\n'.join(elements)))
    with open(os.path.join(POOL_JSON, name + '.json'), 'w', encoding='utf-8', newline='\n') as f:
        f.write(text)


# ---------------------------------------------------------------------------------- checks
HANGS = {'minecraft:lantern', 'minecraft:iron_chain', 'minecraft:pink_petals',
         'minecraft:cherry_sapling', 'minecraft:pink_tulip', 'minecraft:andesite_wall',
         'minecraft:cherry_leaves', 'minecraft:water', 'minecraft:bell',
         'minecraft:smooth_stone_slab'}
AROUND = ((1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1))


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
            if block == 'minecraft:lantern' and props.get('hanging') == 'false':
                if not solid((pos[0], pos[1] - 1, pos[2])):
                    problems.append('%s: the lantern at %s stands on nothing' % (name, pos))
            if block in ('minecraft:pink_petals', 'minecraft:cherry_sapling',
                         'minecraft:pink_tulip', 'minecraft:composter'):
                if not solid((pos[0], pos[1] - 1, pos[2])):
                    problems.append('%s: the %s at %s grows on nothing'
                                    % (name, block.split(':')[-1], pos))
            if block.endswith('chest'):
                if 'LootTable' not in (piece.extra.get(pos) or {}):
                    problems.append('%s: the chest at %s has no loot table' % (name, pos))
                if not solid((pos[0], pos[1] - 1, pos[2])):
                    problems.append('%s: the chest at %s stands on nothing' % (name, pos))
    return problems


# Anything a walker can stand in. Everything else stops them: stairs and slabs and walls
# included, which is conservative - you can stand on a stair but not walk through one.
PASSABLE = {AIR, PETAL, WATER, SAPLING, CHAIN, 'minecraft:pink_tulip'}
FRONT = {'west_up': (-1, 0, 0), 'east_up': (1, 0, 0),
         'north_up': (0, 0, -1), 'south_up': (0, 0, 1)}


def jigsaws(piece):
    """Every jigsaw in a piece: position, which way it points, and what it is wired to."""
    out = []
    for pos, entry in piece.extra.items():
        if entry.get('id') == 'minecraft:jigsaw':
            props = dict(piece.grid[pos][1] or ())
            out.append((pos, props['orientation'], entry))
    return out


def cellar_problems(pieces):
    """Where the cellar actually lands.

    A child is placed in front of the parent's jigsaw, not behind it, so a jigsaw on the near
    wall of the plinth hangs the cellar out over the court - and one block past the court's
    edge is one block too far, because a child that does not fit inside its parent's box is
    dropped without a word (section 10). The cellar is supposed to end up inside the plinth,
    which is the only place it can be: the plinth is what hides it."""
    problems = []
    court, hollow = pieces['court'], pieces['cellar']
    n, g, mid = COURT, FOOT, COURT // 2
    src = [(pos, o) for pos, o, e in jigsaws(court) if e['target'] == SEALED]
    dst = [(pos, o) for pos, o, e in jigsaws(hollow) if e['name'] == SEALED]
    if len(src) != 1 or len(dst) != 1:
        return ['the cellar is wired by %d jigsaws in the court and %d in the cellar; it '
                'wants exactly one of each (section 13)' % (len(src), len(dst))]
    (sp, so), (dp, do) = src[0], dst[0]
    if FRONT[so] != tuple(-v for v in FRONT[do]):
        problems.append("the cellar's jigsaw faces %s and the court's faces %s; they "
                        "have to face each other" % (do, so))
    front = tuple(a + b for a, b in zip(sp, FRONT[so]))
    lo = tuple(f - l for f, l in zip(front, dp))
    hi = tuple(a + b - 1 for a, b in zip(lo, hollow.size))
    for axis, size in zip(range(3), (n, FOOT + 18, n)):
        if lo[axis] < 0 or hi[axis] > size - 1:
            problems.append('the cellar lands at %s..%s, which is outside the court %s: the '
                            'game would drop it and nobody would ever find it'
                            % (lo, hi, (n, FOOT + 18, n)))
            return problems
    want_lo, want_hi = (mid - 4, g, mid - 4), (mid + 4, g + PLINTH - 1, mid + 4)
    if any(lo[i] < want_lo[i] or hi[i] > want_hi[i] for i in range(3)):
        problems.append('the cellar lands at %s..%s, which sticks out of the plinth %s..%s: '
                        'the plinth is the only thing hiding it (section 15)'
                        % (lo, hi, want_lo, want_hi))
    return problems


def walk_problems(pieces):
    """Walk the court, from each of its four gates to the altar.

    The climb is cut by hand, and a hand-cut climb is exactly the thing that quietly stops
    being a climb - a tread written into solid stone with no air over it, a top step a block
    short of the floor it lands on. So this steps through it the way a player does: stand on
    something solid, two blocks of room for your head, and up one or down two at a time."""
    court = pieces['court']
    n, g, mid = COURT, FOOT, COURT // 2
    grid = court.grid

    def block(pos):
        return grid.get(pos, (AIR, None))[0]

    def stands(pos):
        x, y, z = pos
        return (block((x, y - 1, z)) not in PASSABLE
                and block(pos) in PASSABLE and block((x, y + 1, z)) in PASSABLE)

    def reach(start):
        seen, queue = {start}, [start]
        while queue:
            x, y, z = queue.pop()
            for dx, dz in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                for dy in (1, 0, -1, -2):
                    nxt = (x + dx, y + dy, z + dz)
                    if nxt in seen or not 0 <= nxt[1] < FOOT + 18:
                        continue
                    if stands(nxt):
                        seen.add(nxt)
                        queue.append(nxt)
                        break
        return seen

    altar = (mid, g + PLINTH + 1, mid)
    problems = []
    for side, pos in (('west', (1, g + 1, mid)), ('east', (n - 2, g + 1, mid)),
                      ('north', (mid, g + 1, 1)), ('south', (mid, g + 1, n - 2))):
        if not stands(pos):
            problems.append('the %s gate at %s is not somewhere you can stand' % (side, pos))
        elif altar not in reach(pos):
            problems.append('from the %s gate you cannot walk up to the altar: the steps up '
                            'the plinth do not connect' % side)
    return problems


def verify(pieces):
    problems = fitting_problems(pieces) + cellar_problems(pieces)
    problems += walk_problems(pieces)
    for name, piece in pieces.items():
        if max(piece.size) > 48:
            problems.append('%s is %s: too big to rebuild by hand' % (name, piece.size))
        if any(block == 'minecraft:trial_spawner' for block, _ in piece.grid.values()):
            problems.append('%s has a trial spawner: this shrine has no boss (section 4.11)'
                            % name)
        if any(block == 'minecraft:spawner' for block, _ in piece.grid.values()):
            problems.append('%s has a mob spawner: nothing in the shrine is hostile' % name)
    # the sealed cellar must have no doorway: the only way in is to dig
    hollow = pieces['cellar']
    sx, sy, sz = hollow.size
    for y in range(1, 5):
        for a in range(sz):
            for pos in ((0, y, a), (sx - 1, y, a), (a, y, 0), (a, y, sz - 1)):
                if hollow.grid[pos][0] == AIR:
                    problems.append('the cellar has an opening at %s; it is supposed to have '
                                    'none at all (section 15)' % (pos,))
    for line in problems:
        print('  PROBLEM  ' + line)
    if problems:
        raise SystemExit('the shrine does not hold together')
    print('  checked: nothing hangs in mid-air, every chest has a table, no boss and no '
          'spawner of any kind, the cellar is hidden inside the plinth with no way in, '
          'and all four gates walk up to the altar')


def main():
    if not os.path.isdir(DST):
        os.makedirs(DST)
    pieces = {
        'court': court(), 'cellar': cellar(), 'path_cap': path_cap(),
        'run': path('run'), 'bend': path('bend'), 'cross': path('cross'),
        'gate': path('gate'), 'rest': path('rest'), 'garden': path('garden'),
        'spring': path('spring'), 'lantern': path('lantern'),
    }
    verify(pieces)
    for name, piece in sorted(pieces.items()):
        piece.write(os.path.join(DST, name + '.nbt'))
        print('  %-16s %s' % (name, list(piece.size)))

    write_pool('start', [element('court', 1)], EMPTY)
    write_pool('cellar', [element('cellar', 1)], EMPTY)
    write_pool('paths', [element('run', 10), element('bend', 8), element('cross', 4),
                         element('gate', 7), element('rest', 6), element('garden', 7),
                         element('spring', 5), element('lantern', 5)],
               POOL['path_caps'])
    write_pool('path_caps', [element('path_cap', 1)], EMPTY)
    print('  pools -> %s' % os.path.relpath(POOL_JSON, ROOT))


if __name__ == '__main__':
    main()
