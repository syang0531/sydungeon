# -*- coding: utf-8 -*-
"""Print a saved structure (.nbt) layer by layer, as text, and list its jigsaws.

    python tools/dump_structure.py <file.nbt> [<file.nbt> ...]
    python tools/dump_structure.py src/main/resources/data/sydungeon/structure/dungeon/*.nbt

Each Y layer is printed north-up (z increasing downward, x increasing to the right), one
character per block type, with a legend. Air is '.', all-air layers are skipped. Jigsaws are
listed with their orientation, name, target and pool, because that is what decides whether
two pieces connect and it cannot be seen from the blocks.

Reads both the 26.2 palette (`Name`/`Properties`) and the 26.3 one (`id`/`properties`).
"""
import os
import sys
from collections import Counter, OrderedDict

sys.path.insert(0, os.path.dirname(__file__))
import nbt  # noqa: E402


def state_name(entry):
    name = nbt.palette_name(entry).replace('minecraft:', '')
    props = nbt.palette_props(entry)
    if props:
        name += '[' + ','.join('%s=%s' % kv for kv in props.items()) + ']'
    return name


def dump(path):
    root = nbt.read(path)
    sx, sy, sz = root['size']
    palette = root['palette']
    names = [state_name(p) for p in palette]
    grid = {}
    jigsaws = []
    for b in root['blocks']:
        x, y, z = b['pos']
        grid[(x, y, z)] = b['state']
        if nbt.palette_name(palette[b['state']]) == 'minecraft:jigsaw':
            m = b.get('nbt', {})
            jigsaws.append(((x, y, z), nbt.palette_props(palette[b['state']]).get('orientation'),
                            m.get('name'), m.get('target'), m.get('pool'), m.get('final_state')))

    solid = [(p, s) for p, s in grid.items() if not names[s].startswith('air')]
    print('=' * 78)
    print(path)
    print('size %dx%dx%d, DataVersion %s, %d blocks saved, %d entities' % (
        sx, sy, sz, root.get('DataVersion'), len(root['blocks']), len(root.get('entities', []))))
    for pos, orient, name, target, pool, final in jigsaws:
        print('  jigsaw %-12s %-10s name=%s target=%s pool=%s final=%s' % (
            pos, orient, name, target, pool, final))
    if not solid:
        print('nothing but air')
        return

    counts = Counter(names[s] for _, s in solid)
    by_type = OrderedDict()
    for name, n in counts.most_common():
        by_type.setdefault(name.split('[')[0], []).append((name, n))
    chars = '#=+*o%&@$xXvVnN^~-:;abcdefghijklmpqrstuwyz'
    glyph = {base: (chars[k] if k < len(chars) else '?') for k, base in enumerate(by_type)}
    glyph['jigsaw'] = 'J'

    print()
    for y in range(sy):
        rows = []
        any_block = False
        for z in range(sz):
            row = ''
            for x in range(sx):
                s = grid.get((x, y, z))
                if s is None or names[s].startswith('air'):
                    row += '.'
                else:
                    row += glyph[names[s].split('[')[0]]
                    any_block = True
            rows.append(row)
        if not any_block:
            continue
        print('--- y = %d   north is up, x -> east' % y)
        for z, row in enumerate(rows):
            print('  z=%2d  %s' % (z, row))
    print()
    print('legend:')
    for base, states in by_type.items():
        print('  %s  %-22s %4d' % (glyph[base], base, sum(n for _, n in states)))
        if len(states) > 1 or '[' in states[0][0]:
            for name, n in states:
                print('        %-44s %4d' % (name, n))


if __name__ == '__main__':
    for p in sys.argv[1:]:
        dump(p)
