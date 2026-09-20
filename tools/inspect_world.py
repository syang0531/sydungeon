# -*- coding: utf-8 -*-
"""What did the game actually generate? Read it out of a world's region files.

    python tools/inspect_world.py                 # every world under run/saves/
    python tools/inspect_world.py <world folder>

For each SY Dungeon structure start found in the overworld this prints the number of pieces,
how many of each template, the Y levels the pieces sit on, and where the entrance is. It is
the answer to "is this dungeon really one level?" - the eye sees the corridor it is standing
in; this sees all of them. Only chunks the game has generated are on disk, so a dungeon far
from anywhere the player has been will not appear.

Reads the Anvil region format directly (zlib chunks, NBT inside) with tools/nbt.py.
"""
import glob
import gzip
import os
import struct
import sys
import zlib
from collections import Counter

sys.path.insert(0, os.path.dirname(__file__))
import nbt  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def chunks(region_file):
    data = open(region_file, 'rb').read()
    if len(data) < 8192:
        return
    for i in range(1024):
        offset = struct.unpack('>I', b'\x00' + data[i * 4:i * 4 + 3])[0]
        if offset == 0:
            continue
        start = offset * 4096
        length, ctype = struct.unpack('>IB', data[start:start + 5])
        raw = data[start + 5:start + 4 + length]
        try:
            raw = zlib.decompress(raw) if ctype == 2 else gzip.decompress(raw) if ctype == 1 else raw
        except Exception:
            continue
        r = nbt._Reader(raw)
        r.take('b')
        r.string()
        yield r.payload(nbt.COMPOUND)


def starts(world):
    region_dir = os.path.join(world, 'dimensions', 'minecraft', 'overworld', 'region')
    if not os.path.isdir(region_dir):
        region_dir = os.path.join(world, 'region')
    for rf in sorted(glob.glob(os.path.join(region_dir, '*.mca'))):
        for c in chunks(rf):
            for key, s in c.get('structures', {}).get('starts', {}).items():
                if key.startswith('sydungeon:') and s.get('id') != 'INVALID':
                    yield key, c.get('xPos'), c.get('zPos'), s


def report(world):
    print('=' * 78)
    print(world)
    n = 0
    for key, cx, cz, s in starts(world):
        n += 1
        kids = s.get('Children', [])
        names = Counter()
        levels = Counter()
        entrance = None
        for k in kids:
            loc = k.get('pool_element', {}).get('location', '?')
            short = loc.split('/')[-1]
            names[short] += 1
            bb = k.get('BB')
            if bb is not None and short not in ('cell', 'cap', 'shaft', 'shaft_cap', 'entrance'):
                levels[bb[1]] += 1
            if short == 'entrance' and bb is not None:
                entrance = (bb[0], bb[1], bb[2])
        print('\n%s  start chunk (%d, %d)  entrance at %s  %d pieces' % (key, cx, cz, entrance, len(kids)))
        print('  templates: ' + ', '.join('%s %d' % kv for kv in names.most_common()))
        print('  maze levels (min Y: pieces): ' + ', '.join('%d: %d' % kv for kv in sorted(levels.items())))
    if n == 0:
        print('  no SY Dungeon starts in the generated chunks')


def main():
    worlds = sys.argv[1:] or sorted(glob.glob(os.path.join(ROOT, 'run', 'saves', '*')))
    for w in worlds:
        if os.path.isfile(os.path.join(w, 'level.dat')):
            report(w)


if __name__ == '__main__':
    main()
