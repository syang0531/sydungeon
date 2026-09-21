# -*- coding: utf-8 -*-
"""The round tower: the hand-built mock-up in tools/handmade/tower/, made into a structure.

    python tools/generate_tower.py

For now this does the one thing the mock-up left undone: the ring. It was drawn as a single
course of floor - the outline of the circle - and one segment, the west door, built to full
height. Here the twelve segments are laid back into one 29x29 plan with the block of air
between them closed, and extruded to a floor's height.

    ring_floor   29x7x29   the wall for one floor, a 21x21 hole in the middle for the rooms
    ring_ground  29x7x29   the same with the doorway, for floor one

Both are inside a structure block's forty-eight, so they are **source pieces**: build a better
one by hand in the workshop and this will stack that instead of its own (the same bargain the retired
tower's shaft_floor made).

The plan:

    29 x 29 footprint      ring 4 blocks thick at the compass points, cut back at the corners
    21 x 21 inside         3 x 3 cells of seven, which the rooms carve
    8 floors x 7 = 56      the ring is identical on every floor; the door is floor one only
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import nbt  # noqa: E402
from generate_pieces import Piece  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HAND = os.path.join(ROOT, 'tools', 'handmade', 'tower')

CELL = 7
GRID = 3                                  # rooms across
CORE = GRID * CELL                        # 21
BAND = 4                                  # how far the ring reaches past the rooms
WIDE = CORE + 2 * BAND                    # 29
FLOORS = 8
HEIGHT = FLOORS * CELL                    # 56

# where each segment of the mock-up's five-by-five grid lands once the gaps are closed
OFFSET = [0, BAND, BAND + CELL, BAND + 2 * CELL, BAND + 3 * CELL]
SPAN = [BAND, CELL, CELL, CELL, BAND]

STONE = 'minecraft:stone_bricks'
CHISELED = 'minecraft:chiseled_stone_bricks'
MOSSY = 'minecraft:mossy_stone_bricks'
AIR = 'minecraft:air'
VOID = 'minecraft:structure_void'      # "leave whatever is already here"



def load(name):
    """A saved piece as {(x, y, z): (block, props)}, or None if it was never built."""
    path = os.path.join(HAND, name + '.nbt')
    if not os.path.exists(path):
        return None
    root = nbt.read(path)
    palette = [(nbt.palette_name(e), dict(nbt.palette_props(e) or {})) for e in root['palette']]
    out = {}
    for b in root['blocks']:
        x, y, z = (int(v) for v in b['pos'])
        name, props = palette[int(b['state'])]
        if name != AIR:
            out[(x, y, z)] = (name, props or None)
    return {'size': tuple(int(v) for v in root['size']), 'blocks': out}


def plan():
    """The ring's footprint, as {(x, z)} in the 29x29, read off the mock-up's twelve pieces."""
    out = set()
    for zi in range(5):
        for xi in range(5):
            if 1 <= xi <= 3 and 1 <= zi <= 3:
                continue
            piece = load('ring_%d%d' % (xi, zi))
            if piece is None:
                continue                  # a corner the circle never reaches
            for (x, y, z) in piece['blocks']:
                if y == 0:
                    out.add((OFFSET[xi] + x, OFFSET[zi] + z))
    return out


def ring_floor(door=None):
    """One floor of the ring: the footprint stood up seven blocks, banded at the top so the
    floors can be counted from outside. Deliberately plain - it is a starting point.

    Everything that is not the ring is `structure_void`, not air. The piece is a square and
    the tower is a circle, so the four corners fall outside it - and a `rigid` piece writes
    its air, which would carve the turf off the ground and leave a squared-off apron of bare
    dirt round the foot of a round tower. Void leaves the world alone. The middle is void too;
    `core` fills it."""
    p = Piece(WIDE, CELL, WIDE, VOID)
    for x, z in plan():
        for y in range(CELL):
            n = (x * 7 + z * 11 + y * 5) % 9
            p.set(x, y, z, MOSSY if n == 0 else STONE)
        p.set(x, CELL - 1, z, CHISELED)
    if door:
        for (x, y, z), (block, props) in door['blocks'].items():
            p.set(OFFSET[0] + x, y, OFFSET[2] + z, block, props)
        for (x, y, z) in [(x, y, z) for x in range(door['size'][0])
                          for y in range(door['size'][1]) for z in range(door['size'][2])
                          if (x, y, z) not in door['blocks']]:
            p.set(OFFSET[0] + x, y, OFFSET[2] + z, AIR)
        # the mock-up's doorway was cut three tall; ours are four (CLAUDE.md section 2)
        for x in range(door['size'][0]):
            for z in range(door['size'][2]):
                at = (OFFSET[0] + x, 4, OFFSET[2] + z)
                below = [(at[0], y, at[2]) for y in (1, 2, 3)]
                if all(p.grid[c][0] == AIR for c in below):
                    p.set(at[0], at[1], at[2], AIR)
    return p


def shell():
    """The ring for all eight floors, with the door on the ground one. Its inside is left
    solid: `core` claims it and the rooms carve it (CLAUDE.md section 10)."""
    p = Piece(WIDE, HEIGHT, WIDE, STONE)
    ground, upper = ring_floor(load('ring_02')), ring_floor()
    for floor in range(FLOORS):
        source = ground if floor == 0 else upper
        for (x, y, z), (block, props) in source.grid.items():
            p.set(x, floor * CELL + y, z, block, dict(props) if props else None)
    return p




# ------------------------------------------------------------------------ turning pieces
# A piece is stored with its way in on the WEST face, because vanilla turns a child until
# that jigsaw faces the one that placed it. So the stored piece is the north-up drawing and
# every rotation of it comes free.
TURN = {'west': 'north', 'north': 'east', 'east': 'south', 'south': 'west'}
MIRROR = {'north': 'south', 'south': 'north', 'east': 'east', 'west': 'west'}
FACE_PROPS = ('facing',)


def turn_props(props, table):
    if not props:
        return props
    out = dict(props)
    for key in FACE_PROPS:
        if out.get(key) in table:
            out[key] = table[out[key]]
    return out


def rot_cw(blocks, size):
    """One quarter turn: (x, z) -> (sz - 1 - z, x), so the west face becomes the north one."""
    sx, sy, sz = size
    out = {}
    for (x, y, z), value in blocks.items():
        out[(sz - 1 - z, y, x)] = (value[0], turn_props(value[1], TURN))
    return out, (sz, sy, sx)


def mirror_z(blocks, size):
    """Reflect north to south, which turns a corridor that bends left into one that bends
    right - the one shape the mock-up has only one handedness of."""
    sx, sy, sz = size
    return ({(x, y, sz - 1 - z): (v[0], turn_props(v[1], MIRROR))
             for (x, y, z), v in blocks.items()}, size)


def faces_open(blocks, size):
    """Which faces have a doorway, by the hole rather than by anything written down."""
    sx, sy, sz = size
    out = set()
    for side, cells in (('west', [(0, y, z) for y in range(1, 5) for z in range(sz)]),
                        ('east', [(sx - 1, y, z) for y in range(1, 5) for z in range(sz)]),
                        ('north', [(x, y, 0) for y in range(1, 5) for x in range(sx)]),
                        ('south', [(x, y, sz - 1) for y in range(1, 5) for x in range(sx)])):
        if sum(1 for c in cells if c not in blocks) >= 8:
            out.add(side)
    return out


def orient(blocks, size, anchor_face):
    """Turn a piece until the face its way in is on points west."""
    while anchor_face != 'west':
        blocks, size = rot_cw(blocks, size)
        anchor_face = TURN[anchor_face]
    return blocks, size


# ------------------------------------------------------------------- wiring the seventy-two
import tower_layout as L  # noqa: E402

NS = 'sydungeon'
ANCHOR = NS + ':tow_anchor'     # the one jigsaw a room piece has: its way in
PLACER = NS + ':tow_placer'     # core's side of it, one per cell
EMPTY = 'minecraft:empty'
PRIORITY = 20

# where core's jigsaw stands to place a cell from a given side, and which way it looks
PLACER_AT = {
    'west': (lambda cx, cz: (cx * CELL - 1, cz * CELL + 3), 'east_up', lambda cx, cz: cx >= 1),
    'east': (lambda cx, cz: (cx * CELL + CELL, cz * CELL + 3), 'west_up',
             lambda cx, cz: cx <= GRID - 2),
    'north': (lambda cx, cz: (cx * CELL + 3, cz * CELL - 1), 'south_up', lambda cx, cz: cz >= 1),
    'south': (lambda cx, cz: (cx * CELL + 3, cz * CELL + CELL), 'north_up',
              lambda cx, cz: cz <= GRID - 2),
}


def can_place(cell, side):
    return PLACER_AT[side][2](cell[0], cell[1])


def wire(plan, big):
    """For every cell: which side core places it from, and which pool it draws from.

    The side decides the piece's rotation, so it is chosen first - normally the way you came
    in, so the piece's own doorway is the one you walk through. The pool is then whatever has
    a door every way this cell has to open."""
    out = []
    for floor in sorted(plan):
        info = plan[floor]
        route, stair = info['route'], info['stair']
        need = {cell: set() for cell in info['free']}
        anchor = {}

        for i, cell in enumerate(route):
            if i:
                back = L.side_between(cell, route[i - 1])
            elif floor == 1:
                back = 'west'                 # the ring's door, which is outside core
            else:
                back = L.side_between(cell, plan[floor - 1]['stair'])
            ahead = (L.side_between(cell, route[i + 1]) if i + 1 < len(route)
                     else (L.side_between(cell, stair) if stair else None))
            need[cell] |= {s for s in (back, ahead) if s}
            anchor[cell] = back if can_place(cell, back) else next(
                s for s in L.DIRS if can_place(cell, s))

        for cell in sorted(set(info['free']) - set(route)):
            near = next(s for s in L.DIRS if L.step(cell, s) in set(route)
                        and can_place(cell, s))
            anchor[cell] = near
            need[L.step(cell, near)].add(L.OPPOSITE[near])

        if floor in big:
            bx, bz = big[floor]
            need[(bx - 1, bz)].add('east')

        for cell in info['free']:
            out.append({'floor': floor, 'cell': cell, 'side': anchor[cell],
                        'pool': L.pool_for(anchor[cell], need[cell]),
                        'kind': 'route' if cell in route else 'leaf'})

        if stair:
            back = L.side_between(stair, route[-1])
            out.append({'floor': floor, 'cell': stair, 'side': back,
                        'pool': 'stair', 'kind': 'stair'})
        if floor in big:
            bx, bz = big[floor]
            # the big room opens east; pick the row whose neighbour is on the route, and
            # make that neighbour open back
            out.append({'floor': floor, 'cell': (bx, bz), 'side': 'west', 'row': 0,
                        'pool': 'sanctum' if floor == L.FLOORS else 'library',
                        'kind': 'big'})
    return out


# ---------------------------------------------------------------------------- the pieces
DST = os.path.join(ROOT, 'src', 'main', 'resources', 'data', 'sydungeon', 'structure', 'tower')
POOL_JSON = os.path.join(ROOT, 'src', 'main', 'resources', 'data', 'sydungeon',
                         'worldgen', 'template_pool', 'tower')

WANT = {'cross': {'west', 'east', 'north', 'south'},
        'tee': {'west', 'north', 'south'},
        'straight': {'west', 'east'},
        'corner': {'west', 'north'},
        'dead_end': {'west'}}


def canonical(name, piece):
    """Turn a piece so its way in is west, the way every stored piece is written.

    Which face is the way in is not written down anywhere, so it is deduced: the one that
    leaves the piece looking like what it is. A tee is entered through its stem, a corner
    through the arm that makes the other arm point left."""
    blocks, size = piece['blocks'], piece['size']
    doors = faces_open(blocks, size)
    for face in (sorted(doors) or ['west']):
        turned, new_size = orient(dict(blocks), size, face)
        if faces_open(turned, new_size) == WANT.get(name, faces_open(turned, new_size)):
            return turned, new_size
    return orient(dict(blocks), size, sorted(doors)[0] if doors else 'west')


def normalise_doors(blocks, size, wall=STONE):
    """Put a big room's doorways where the grid expects them.

    The mock-up's two-by-two was drawn with its doors a block off the cell centre, which would
    leave a two-wide slot where it meets a neighbour. Which faces have a door is the design and
    is kept; where along the face is not, so each is walled up and cut again at the centre."""
    sx, sy, sz = size
    out = dict(blocks)
    faces = {'west': (lambda i, y: (0, y, i), sz), 'east': (lambda i, y: (sx - 1, y, i), sz),
             'north': (lambda i, y: (i, y, 0), sx), 'south': (lambda i, y: (i, y, sz - 1), sx)}
    for side, (at, span) in faces.items():
        for c in range(span // CELL):
            reach = range(c * CELL, (c + 1) * CELL)
            if not any(at(i, y) not in blocks for i in reach for y in range(1, 5)):
                continue
            for i in reach:
                for y in range(1, 5):
                    out[at(i, y)] = (wall, None)
            for i in range(c * CELL + 2, c * CELL + 5):
                for y in range(1, 5):
                    out.pop(at(i, y), None)
    return out


def as_piece(blocks, size, anchor=True, final=STONE):
    p = Piece(size[0], size[1], size[2], AIR)
    for (x, y, z), (block, props) in blocks.items():
        p.set(x, y, z, block, props)
    if anchor:
        p.jigsaw(0, 0, 3, 'west_up', EMPTY, final, name=ANCHOR, target=ANCHOR)
    return p


def chest(table, facing='south'):
    return ('minecraft:chest', {'facing': facing, 'type': 'single', 'waterlogged': 'false'},
            {'id': 'minecraft:chest', 'LootTable': NS + ':chests/' + table})


def sealed():
    """A room with no doors at all and a chest in it. Its jigsaw stands in the wall, so a
    neighbour's doorway meets stone: what the player sees is a bricked-up door, and the only
    way in is to notice the floor is a cell short and dig."""
    p = Piece(CELL, CELL, CELL, STONE)
    p.box(1, 1, 1, CELL - 2, CELL - 2, CELL - 2, AIR)
    p.set(3, 1, 3, *chest('tower_observatory'))
    p.jigsaw(0, 0, 3, 'west_up', EMPTY, STONE, name=ANCHOR, target=ANCHOR)
    return p


def build_pieces():
    """Every room piece, turned to face west and given its one jigsaw."""
    out = {}
    for name in ('cross', 'tee', 'straight', 'corner', 'dead_end', 'room4', 'stair'):
        piece = load(name)
        if piece is None:
            continue
        blocks, size = canonical(name, piece)
        if max(size[0], size[2]) > CELL:
            blocks = normalise_doors(blocks, size)
        out[name] = as_piece(blocks, size)
        if name == 'corner':
            flipped, flipped_size = mirror_z(blocks, size)
            out['corner_right'] = as_piece(flipped, flipped_size)
    out['corner_left'] = out.pop('corner')
    out['cross_guard'] = guarded(out['cross'], 'minecraft:vex')
    out['tee_guard'] = guarded(out['tee'], 'minecraft:zombie_villager')
    out['dead_end'] = rewarded(out['dead_end'], 'tower_study')
    out['sealed'] = sealed()
    big = load('room4')
    shape, shape_size = canonical('room4', big)
    shape = normalise_doors(shape, shape_size)
    out.pop('room4', None)
    out['library'] = furnish_library(shape, shape_size)
    out['sanctum'] = furnish_sanctum(shape, shape_size)
    return out


# ------------------------------------------------------------------------- core, and main
def core(placements):
    """Twenty-one by fifty-six by twenty-one of solid stone with a jigsaw for every cell.

    Nothing grows here: core reaches every one of the seventy-two itself, so no cell can be
    left unbuilt, and the pool a jigsaw names is the only thing left to chance."""
    p = Piece(CORE, HEIGHT, CORE, STONE)
    p.jigsaw(0, 0, CORE // 2, 'west_up', EMPTY, STONE, name=ANCHOR, target=ANCHOR)
    for spot in placements:
        cx, cz = spot['cell']
        y = (spot['floor'] - 1) * CELL
        if spot['kind'] == 'big':
            x, z = cx * CELL - 1, cz * CELL + spot['row'] * CELL + 3
            orientation = 'east_up'
        else:
            where, orientation, _ = PLACER_AT[spot['side']]
            x, z = where(cx, cz)
        p.jigsaw(x, y, z, orientation, NS + ':tower/' + spot['pool'], STONE,
                 priority=PRIORITY, name=PLACER, target=ANCHOR)
    return p


def element(location, weight):
    return ('    { "weight": %d, "element": { "element_type": "minecraft:single_pool_element",'
            '\n        "location": "%s:tower/%s", "projection": "rigid", '
            '"processors": "%s:tower_weathering" } }' % (weight, NS, location, NS))


def write_pool(name, elements, fallback=EMPTY):
    if not os.path.isdir(POOL_JSON):
        os.makedirs(POOL_JSON)
    text = ('{\n  "fallback": "%s",\n  "elements": [\n%s\n  ]\n}\n'
            % (fallback, ',\n'.join(elements)))
    with open(os.path.join(POOL_JSON, name + '.json'), 'w', encoding='utf-8', newline='\n') as f:
        f.write(text)


# which pieces may stand in a cell that must open a given way. Every one of them has the door
# the pool promises; what differs is what else it has, and what is in it.
POOL_PIECES = {
    'link_through': [('straight', 10), ('cross', 3), ('cross_guard', 2)],
    'link_left': [('corner_left', 9), ('tee', 4), ('tee_guard', 3), ('cross', 2),
                  ('cross_guard', 1)],
    'link_right': [('corner_right', 9), ('tee', 4), ('tee_guard', 3), ('cross', 2),
                   ('cross_guard', 1)],
    'link_cross': [('cross', 2), ('cross_guard', 1)],
    'leaf': [('dead_end', 10), ('sealed', 4)],
    'stair': [('stair', 1)],
    'library': [('library', 1)],
    'sanctum': [('sanctum', 1)],
    'core': [('core', 1)],
    'start': [('shell', 1)],
}


def main():
    plan, big, _ = L.best_plan([4, L.FLOORS])
    placements = wire(plan, big)
    pieces = build_pieces()
    pieces['shell'] = shell()
    pieces['shell'].jigsaw(BAND - 1, 0, BAND + CORE // 2, 'east_up', NS + ':tower/core',
                           STONE, priority=PRIORITY, name=PLACER, target=ANCHOR)
    pieces['core'] = core(placements)

    if not os.path.isdir(DST):
        os.makedirs(DST)
    for name, piece in sorted(pieces.items()):
        piece.write(os.path.join(DST, name + '.nbt'))
    print('조각 %d개 -> %s' % (len(pieces), os.path.relpath(DST, ROOT)))
    for name in sorted(pieces):
        print('  %-13s %s' % (name, list(pieces[name].size)))

    for name, members in POOL_PIECES.items():
        write_pool(name, [element(n, w) for n, w in members])
    print('풀 %d개 -> %s' % (len(POOL_PIECES), os.path.relpath(POOL_JSON, ROOT)))

    verify(pieces, placements, plan, big)
    kinds = {}
    for spot in placements:
        kinds[spot['kind']] = kinds.get(spot['kind'], 0) + 1
    print('칸 %d개 = %s' % (sum(kinds.values()),
                           ', '.join('%s %d' % kv for kv in sorted(kinds.items()))))
    return plan, big, placements, pieces




# --------------------------------------------------------------------------------- checks
def rotate_piece(piece, k):
    blocks = {p: (v[0], dict(v[1]) if v[1] else None) for p, v in piece.grid.items()}
    size = piece.size
    for _ in range(k):
        blocks, size = rot_cw(blocks, size)
    return blocks, size


TURNS_TO = {'west': 0, 'north': 1, 'east': 2, 'south': 3}
FACING = {'east_up': 'east', 'west_up': 'west', 'north_up': 'north', 'south_up': 'south'}
OPP = {'north': 'south', 'south': 'north', 'east': 'west', 'west': 'east'}
DELTA = {'north': (0, 0, -1), 'south': (0, 0, 1), 'east': (1, 0, 0), 'west': (-1, 0, 0)}


def stamp(world, blocks, at):
    for (x, y, z), value in blocks.items():
        world[(at[0] + x, at[1] + y, at[2] + z)] = value[0]


def assemble(pieces, placements, leaf='dead_end'):
    """Put the tower together the way the game would, and hand back its blocks.

    Every child sits where its own jigsaw meets its parent's, turned until the two face each
    other - which is the whole of vanilla's placement, and enough to walk the result."""
    world = {}
    stamp(world, {p: (v[0], v[1]) for p, v in pieces['shell'].grid.items()}, (0, 0, 0))
    core_at = (BAND, 0, BAND)
    stamp(world, {p: (v[0], v[1]) for p, v in pieces['core'].grid.items()}, core_at)

    choice = {'leaf': leaf, 'link_through': 'straight', 'link_left': 'corner_left',
              'link_right': 'corner_right', 'link_cross': 'cross', 'stair': 'stair',
              'library': 'library', 'sanctum': 'sanctum'}
    for spot in placements:
        cx, cz = spot['cell']
        y = (spot['floor'] - 1) * CELL
        if spot['kind'] == 'big':
            px, pz, orientation = cx * CELL - 1, cz * CELL + 3, 'east_up'
        else:
            where, orientation, _ = PLACER_AT[spot['side']]
            px, pz = where(cx, cz)
        facing = FACING[orientation]
        dx, dy, dz = DELTA[facing]
        target = (core_at[0] + px + dx, core_at[1] + y + dy, core_at[2] + pz + dz)
        piece = pieces[choice[spot['pool']]]
        blocks, _size = rotate_piece(piece, TURNS_TO[OPP[facing]])
        anchor = next(p for p, v in blocks.items() if v[0] == 'minecraft:jigsaw')
        stamp(world, blocks, tuple(target[i] - anchor[i] for i in range(3)))
    return world


def walk(world, start):
    """Everywhere a player could reach from the front door, inside the tower's own box.

    Bounded on purpose: outside it is open sky, and a flood fill that escapes has nothing to
    stop it."""
    from collections import deque

    def air(p):
        return (0 <= p[0] < WIDE and 0 <= p[1] < HEIGHT and 0 <= p[2] < WIDE
                and world.get(p, 'minecraft:air') == 'minecraft:air')

    seen, queue = {start}, deque([start])
    while queue:
        x, y, z = queue.popleft()
        for d in ((1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1)):
            n = (x + d[0], y + d[1], z + d[2])
            if n not in seen and air(n):
                seen.add(n)
                queue.append(n)
    return seen


def verify(pieces, placements, plan, big):
    problems = []
    world = assemble(pieces, placements)
    door = (1, 2, BAND + CORE // 2)
    if world.get(door, 'minecraft:air') != 'minecraft:air':
        problems.append('현관이 막혀 있다 %s' % (door,))
    reached = walk(world, door)

    def cell_seen(floor, cell, span=1):
        y = (floor - 1) * CELL + 2
        for dx in range(span):
            for dz in range(span):
                x = BAND + (cell[0] + dx) * CELL + 3
                z = BAND + (cell[1] + dz) * CELL + 3
                if (x, y, z) in reached:
                    return True
        return False

    for floor in sorted(plan):
        for cell in plan[floor]['route']:
            if not cell_seen(floor, cell):
                problems.append('%d층 경로 칸 %s에 못 간다' % (floor, cell))
        for cell in sorted(set(plan[floor]['free']) - set(plan[floor]['route'])):
            if not cell_seen(floor, cell):
                problems.append('%d층 곁방 %s에 못 간다' % (floor, cell))
        if plan[floor]['stair'] and not cell_seen(floor, plan[floor]['stair']):
            problems.append('%d층 계단에 못 간다' % floor)
        if floor in big and not cell_seen(floor, big[floor], 2):
            problems.append('%d층 큰 방에 못 간다' % floor)

    sealed_world = assemble(pieces, placements, leaf='sealed')
    sealed_reached = walk(sealed_world, door)
    if (BAND + plan[L.FLOORS]['route'][-1][0] * CELL + 3,
            (L.FLOORS - 1) * CELL + 2,
            BAND + plan[L.FLOORS]['route'][-1][1] * CELL + 3) not in sealed_reached:
        problems.append('곁방이 전부 비밀방이면 꼭대기에 못 간다')

    for line in problems:
        print('  문제  ' + line)
    if problems:
        raise SystemExit('탑이 이어지지 않는다')
    print('검사 통과: 현관에서 %d칸이 이어지고, 72칸 전부 도달 가능하다 '
          '(곁방을 전부 비밀방으로 바꿔도 꼭대기까지 간다)' % len(reached))




# ---------------------------------------------------------------- what goes in the big rooms
DEEP = 'minecraft:deepslate_bricks'
POLISHED = 'minecraft:polished_deepslate'
BOOKSHELF = 'minecraft:bookshelf'
TRIAL_STATE = {'trial_spawner_state': 'inactive', 'ominous': 'false'}
INNER = 1, 12                      # the walkable ring inside a big room
MID = 6                            # where its middle is


def trial_spawner(config):
    """Clearing a room is the trial spawner's job: a chest can be opened without a fight, and
    telling whether everything is dead would take Java. It pays each player who fought."""
    return {'id': 'minecraft:trial_spawner',
            'normal_config': NS + ':tower/' + config,
            'ominous_config': NS + ':tower/' + config,
            'target_cooldown_length': nbt.Int(2_000_000_000),
            'required_player_range': nbt.Int(14)}


def doorways(piece):
    """The block in front of every doorway, which must stay clear of furniture."""
    sx, sy, sz = piece.size
    out = set()
    for z in range(sz):
        if piece.grid[(0, 2, z)][0] == AIR:
            out |= {(1, y, z) for y in range(1, 5)}
        if piece.grid[(sx - 1, 2, z)][0] == AIR:
            out |= {(sx - 2, y, z) for y in range(1, 5)}
    for x in range(sx):
        if piece.grid[(x, 2, 0)][0] == AIR:
            out |= {(x, y, 1) for y in range(1, 5)}
        if piece.grid[(x, 2, sz - 1)][0] == AIR:
            out |= {(x, y, sz - 2) for y in range(1, 5)}
    return out


def line_walls(p, block, height=3, skip=()):
    lo, hi = INNER
    for i in range(lo, hi + 1):
        for x, z in ((lo, i), (hi, i), (i, lo), (i, hi)):
            for y in range(1, height + 1):
                if (x, y, z) not in skip:
                    p.set(x, y, z, block)


def furnish_library(blocks, size):
    """Shelves to the ceiling and a table with the fifteen that level thirty needs.

    The ring of shelves sits at the table's own height with air between, which is what the
    game counts; one place in it is left out so there is a way in to stand at the table."""
    p = as_piece(blocks, size)
    clear = doorways(p)
    line_walls(p, BOOKSHELF, 3, clear)
    p.box(MID - 2, 1, MID - 2, MID + 2, 1, MID + 2, CHISELED)
    p.set(MID, 2, MID, 'minecraft:enchanting_table')
    shelves = 0
    for dx in range(-2, 3):
        for dz in range(-2, 3):
            if max(abs(dx), abs(dz)) != 2 or (dx, dz) == (-2, 0):
                continue               # the gap you walk in through
            p.set(MID + dx, 2, MID + dz, BOOKSHELF)
            shelves += 1
    assert shelves == 15, shelves
    p.set(MID, 1, MID - 4, 'minecraft:lectern',
          {'facing': 'south', 'has_book': 'false', 'powered': 'false'})
    p.set(MID, 1, MID + 4, 'minecraft:lectern',
          {'facing': 'north', 'has_book': 'false', 'powered': 'false'})
    p.set(INNER[1] - 1, 1, 3, *chest('tower_library', 'west'))
    p.set(INNER[1] - 1, 1, 10, *chest('tower_study', 'west'))
    for x, z in ((3, 3), (3, 10), (10, 3), (10, 10)):
        p.set(x, 5, z, 'minecraft:lantern', {'hanging': 'true', 'waterlogged': 'false'})
    return p


def furnish_sanctum(blocks, size):
    """The archmage's room. Same walls as the library, re-skinned in deepslate so it reads as
    somewhere else the moment the door opens, and the gate he never lit on the far wall."""
    skin = {STONE: DEEP, MOSSY: DEEP, CHISELED: POLISHED}
    p = as_piece({pos: (skin.get(v[0], v[0]), v[1]) for pos, v in blocks.items()}, size,
                 final=DEEP)
    for x, z in ((2, 2), (2, 11), (11, 2), (11, 11)):
        for y in range(1, 6):
            p.set(x, y, z, POLISHED)
    p.box(MID - 1, 1, MID - 1, MID + 1, 1, MID + 1, CHISELED)
    p.set(MID, 2, MID, 'minecraft:trial_spawner', TRIAL_STATE, trial_spawner('archmage'))
    for x, z in ((4, 4), (4, 9), (9, 4), (9, 9)):
        p.set(x, 1, z, 'minecraft:trial_spawner', TRIAL_STATE, trial_spawner('tower_guards'))
    for dx, dy in ((1, 0), (2, 0), (1, 4), (2, 4),
                   (0, 1), (0, 2), (0, 3), (3, 1), (3, 2), (3, 3)):
        p.set(4 + dx, 1 + dy, 11, 'minecraft:obsidian')
    p.set(9, 1, 11, *chest('tower_portal', 'west'))
    for x, z in ((3, 6), (10, 6), (6, 3), (6, 10)):
        p.set(x, 5, z, 'minecraft:soul_lantern', {'hanging': 'true', 'waterlogged': 'false'})
    return p




# ------------------------------------------------------- what goes in the corridors and rooms
ANY_LIGHT = {'block_light_limit': {'min_inclusive': nbt.Int(0), 'max_inclusive': nbt.Int(15)}}


def mob_spawner(entity, count=2):
    """A spawner that ignores light. Without the rule it obeys the mob's own, and a lit
    corridor would make it scenery (CLAUDE.md section 6)."""
    return {'id': 'minecraft:mob_spawner',
            'SpawnData': {'entity': {'id': entity}, 'custom_spawn_rules': ANY_LIGHT},
            'Delay': nbt.Short(20), 'MinSpawnDelay': nbt.Short(240),
            'MaxSpawnDelay': nbt.Short(900), 'SpawnCount': nbt.Short(count),
            'MaxNearbyEntities': nbt.Short(5), 'RequiredPlayerRange': nbt.Short(14),
            'SpawnRange': nbt.Short(4)}


def copy_piece(piece):
    out = Piece(piece.size[0], piece.size[1], piece.size[2], AIR)
    for pos, (block, props) in piece.grid.items():
        out.set(pos[0], pos[1], pos[2], block, dict(props) if props else None)
        if pos in piece.extra:
            out.extra[pos] = piece.extra[pos]
    return out


def guarded(piece, entity):
    """A junction with something standing in it. The streets are where the fighting is; the
    rooms are where the reward is."""
    out = copy_piece(piece)
    out.set(3, 1, 3, 'minecraft:spawner', None, mob_spawner(entity))
    return out


def rewarded(piece, table, facing='west'):
    """A room worth walking into: a chest against the far wall and a light to find it by."""
    out = copy_piece(piece)
    out.set(5, 1, 3, *chest(table, facing))
    out.set(1, 1, 1, 'minecraft:bookshelf')
    out.set(1, 1, 5, 'minecraft:bookshelf')
    out.set(3, 5, 3, 'minecraft:lantern', {'hanging': 'true', 'waterlogged': 'false'})
    return out


if __name__ == '__main__':
    main()
