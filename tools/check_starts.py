# -*- coding: utf-8 -*-
"""How high does each dungeon's start piece stand above the ground it is put on?

    python tools/check_starts.py

`JigsawPlacement` moves the start piece so that `minY + getGroundLevelDelta()` lands on the
heightmap, and `StructurePoolElement.getGroundLevelDelta()` is 1 (26.2, checked). The
heightmap is the first **free** block, so after the move:

    piece y = 0   the top solid block of the terrain - our floor belongs here
    piece y = 1   the first block of air - where the player stands

Courses of footing under the floor therefore do not go underground. They stand up out of the
grass as a plinth, they carry the doorway up with them, and `beard_thin` then fills a skirt
of stone all the way out to twelve blocks to meet them, which is the flat grey plaza in the
screenshots of 2026-09-22.

So this measures the one number that matters: the lowest place inside the start piece where a
player can stand. It has to be 1. Footing belongs on the **children** - they hang from their
jigsaws and the ground under them really can fall away (CLAUDE.md section 18).
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
PASSABLE = {AIR, 'minecraft:water', 'minecraft:ladder', 'minecraft:lantern',
            'minecraft:torch', 'minecraft:jigsaw', 'minecraft:pink_petals',
            'minecraft:brown_mushroom', 'minecraft:red_mushroom', 'minecraft:moss_carpet',
            'minecraft:iron_chain', 'minecraft:rail', 'minecraft:kelp_plant'}


# The one start that is meant to stand over the ground it is placed on: the swamp's deck is
# three courses above the water and the stilts hang from it (CLAUDE.md sections 17 and 18).
EXCEPT = {'swamp': 'the deck stands over water and the stilts hang from it (section 17)'}


def read(path):
    with io.open(path, encoding='utf-8') as f:
        return json.load(f)


def load(location):
    family, name = location.split(':')[-1].split('/')
    tag = nbt.read(os.path.join(DATA, 'structure', family, name + '.nbt'))
    size = [int(v) for v in tag['size']]
    palette = [entry['Name'] for entry in tag['palette']]
    grid = {}
    for block in tag['blocks']:
        x, y, z = (int(v) for v in block['pos'])
        grid[(x, y, z)] = palette[int(block['state'])]
    return size, grid


def lowest_stand(size, grid):
    """The lowest spot a player can stand: something solid under the feet, and two blocks of
    room. Positions the piece does not list are the world's own ground, so they count as
    solid and never as air."""
    sx, sy, sz = size

    def solid(pos):
        return grid.get(pos, 'unlisted') not in PASSABLE

    best = None
    for (x, y, z), block in grid.items():
        if y < 1 or block not in (AIR, 'minecraft:water'):
            continue
        if grid.get((x, y + 1, z)) not in (AIR, 'minecraft:water'):
            continue
        if not solid((x, y - 1, z)):
            continue
        if best is None or y < best:
            best = y
    return best


def main():
    rows = []
    for name in sorted(os.listdir(os.path.join(DATA, 'worldgen', 'structure'))):
        structure = read(os.path.join(DATA, 'worldgen', 'structure', name))
        if 'project_start_to_heightmap' not in structure:
            continue
        pool = structure['start_pool'].split(':')[-1]
        family, pool_name = pool.split('/')
        elements = read(os.path.join(DATA, 'worldgen', 'template_pool', family,
                                     pool_name + '.json'))['elements']
        location = elements[0]['element']['location']
        size, grid = load(location)
        rows.append((family, location.split('/')[-1], size, lowest_stand(size, grid)))

    bad = []
    print('%-9s %-12s %-14s %s' % ('family', 'start', 'size', 'lowest place to stand'))
    for family, piece, size, stand in rows:
        note = ''
        if stand is None:
            note = '(solid: nothing to stand in)'
        elif stand > 1 and family in EXCEPT:
            note = '+%d on purpose: %s' % (stand - 1, EXCEPT[family])
        elif stand > 1:
            note = '<- stands %d above the ground' % (stand - 1)
            bad.append((family, piece, stand))
        print('%-9s %-12s %-14s %-4s %s'
              % (family, piece, 'x'.join(str(v) for v in size), stand, note))
    if bad:
        print('\n%d start piece(s) stand on a plinth of their own footing. The floor course '
              'of a start piece belongs at y=0; footing belongs on the children.' % len(bad))
    return 1 if bad else 0


if __name__ == '__main__':
    raise SystemExit(main())
