# -*- coding: utf-8 -*-
"""Assemble every dungeon's way down out of its own jigsaws, and climb it.

    python tools/check_shafts.py

Each generator already checks its own ladder, but it does it against a table of offsets
written by hand - which is a table of where the pieces are *supposed* to land. The swamp's
pilings kept the old three-wide shaft's jigsaw coordinates through the move to one column
(2026-09-22): every piece's ladder was perfect, the hand-written table agreed with itself,
and in the game the stack below the great hut hung a block out of line. Solid plank where the
ladder should have been, and the climb picking up again one over.

So this one never says where a piece goes. It reads the pools, follows the down jigsaw to the
single piece its pool holds, finds the up jigsaw on that piece that answers it, and lets the
subtraction decide - which is all the game does. Then it climbs: a ladder the whole way down
one column, and nothing but solid block in the eight round it until the room at the bottom.
"""
import io
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import nbt  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, 'src', 'main', 'resources', 'data', 'sydungeon')

AIR = 'minecraft:air'
LADDER = 'minecraft:ladder'
OPEN = {AIR, 'minecraft:water', LADDER, 'minecraft:structure_void'}
FRONT = {'west': (-1, 0, 0), 'east': (1, 0, 0), 'north': (0, 0, -1), 'south': (0, 0, 1),
         'up': (0, 1, 0), 'down': (0, -1, 0)}


def read(path):
    with io.open(path, encoding='utf-8') as f:
        return json.load(f)


def load(location):
    """One piece: its size, its blocks, and its jigsaws with where they look."""
    family, name = location.split(':')[-1].split('/')
    tag = nbt.read(os.path.join(DATA, 'structure', family, name + '.nbt'))
    palette = [nbt.palette_name(e) for e in tag['palette']]
    props = [dict(nbt.palette_props(e) or {}) for e in tag['palette']]
    grid, jigsaws = {}, []
    for block in tag['blocks']:
        x, y, z = (int(v) for v in block['pos'])
        state = int(block['state'])
        grid[(x, y, z)] = palette[state]
        if palette[state] == 'minecraft:jigsaw':
            data = block.get('nbt') or {}
            jigsaws.append({'pos': (x, y, z),
                            'facing': props[state].get('orientation', '').split('_')[0],
                            'pool': str(data.get('pool', '')),
                            'name': str(data.get('name', '')),
                            'target': str(data.get('target', ''))})
    return {'size': tuple(int(v) for v in tag['size']), 'grid': grid, 'jigsaws': jigsaws,
            'name': name}


def only_element(family, pool):
    """The piece a pool holds, if it holds exactly one - which is how a chain is forced."""
    path = os.path.join(DATA, 'worldgen', 'template_pool', family, pool + '.json')
    if not os.path.exists(path):
        return None
    elements = read(path)['elements']
    if len(elements) != 1:
        return None
    return elements[0]['element']['location']


def chain(family, start):
    """Stack the pieces the way the game does: a down jigsaw, the one piece its pool holds,
    and the up jigsaw on that piece that answers it. Vertical joints do not rotate."""
    placed = [((0, 0, 0), start)]
    piece = start
    at = (0, 0, 0)
    while True:
        down = [j for j in piece['jigsaws'] if j['facing'] == 'down']
        step = None
        for jigsaw in down:
            location = only_element(family, jigsaw['pool'].split('/')[-1])
            if not location:
                continue
            child = load(location)
            up = [j for j in child['jigsaws']
                  if j['facing'] == 'up' and j['name'] == jigsaw['target']]
            if len(up) != 1:
                continue
            front = tuple(a + b for a, b in zip(jigsaw['pos'], FRONT['down']))
            origin = tuple(at[i] + front[i] - up[0]['pos'][i] for i in range(3))
            step = (origin, child)
            break
        if not step:
            return placed
        at, piece = step
        placed.append(step)
        if len(placed) > 12:
            return placed


def climb(placed, jigsaw):
    """Walk down the shaft's own ladder and say where it stops.

    Which column that is comes from the jigsaw that started the chain, not from the tallest
    ladder in the world: the lighthouse has a second ladder up the inside of the tower, and
    it is not the way down."""
    world = {}
    for origin, piece in placed:
        for pos, block in piece['grid'].items():
            world[tuple(origin[i] + pos[i] for i in range(3))] = block
    ladders = [pos for pos, block in world.items() if block == LADDER]
    if not ladders:
        return []
    near = [(jigsaw[0] + dx, jigsaw[2] + dz)
            for dx, dz in ((1, 0), (-1, 0), (0, 1), (0, -1))]
    counted = [(sum(1 for pos in ladders if (pos[0], pos[2]) == c), c) for c in near]
    best, column = max(counted)
    if not best:
        return ['no ladder stands beside the jigsaw at %s that starts the way down' % (jigsaw,)]
    top = max((pos for pos in ladders if (pos[0], pos[2]) == column), key=lambda p: p[1])
    floor = min(origin[1] for origin, _ in placed)
    problems = []
    for y in range(top[1], floor, -1):
        here = world.get((column[0], y, column[1]))
        # ladder, sea, or the air of the lighthouse's lip - anything you can pass through.
        # A block is the fault this is here for; nothing at all means a piece is missing.
        if here is None or here not in (LADDER, 'minecraft:water', AIR):
            problems.append('the climb stops at %s: %s'
                            % ((column[0], y, column[1]), (here or 'nothing at all')
                               .split(':')[-1]))
            break
        # How many of the eight are open tells you what this course is. All of them and the
        # column is passing through a room, which is the point of a room. One or two and it
        # is a hole in the casing, which is where the water gets in.
        open_at = [(column[0] + dx, y, column[1] + dz)
                   for dx in (-1, 0, 1) for dz in (-1, 0, 1)
                   if (dx, dz) != (0, 0) and world.get((column[0] + dx, y, column[1] + dz),
                                                       AIR) in OPEN]
        if 1 <= len(open_at) <= 4:
            problems.append('the ring is open at %s (%s): %d of the eight'
                            % (open_at[0], (world.get(open_at[0]) or 'nothing').split(':')[-1],
                               len(open_at)))
    return problems[:6]


def main():
    bad = 0
    print('%-9s %-24s %s' % ('family', 'the way down', 'result'))
    for name in sorted(os.listdir(os.path.join(DATA, 'worldgen', 'structure'))):
        structure = read(os.path.join(DATA, 'worldgen', 'structure', name))
        family = structure['start_pool'].split(':')[-1].split('/')[0]
        pool = structure['start_pool'].split('/')[-1]
        elements = read(os.path.join(DATA, 'worldgen', 'template_pool', family,
                                     pool + '.json'))['elements']
        start = load(elements[0]['element']['location'])
        placed = chain(family, start)
        if len(placed) < 2:
            print('%-9s %-24s no shaft' % (family, '-'))
            continue
        down = next(j['pos'] for j in start['jigsaws'] if j['facing'] == 'down'
                    and only_element(family, j['pool'].split('/')[-1]))
        problems = climb(placed, down)
        route = ' -> '.join(piece['name'] for _, piece in placed)
        print('%-9s %-24s %s' % (family, route[:24], 'ok' if not problems else 'BROKEN'))
        for line in problems:
            print('              ' + line)
            bad += 1
    if bad:
        print('\nA shaft is only as good as where its pieces actually land: the offsets above '
              'come from the jigsaws, not from a table (section 33).')
    return 1 if bad else 0


if __name__ == '__main__':
    raise SystemExit(main())
