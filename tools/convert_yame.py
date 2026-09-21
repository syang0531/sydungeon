# -*- coding: utf-8 -*-
"""Turn the `yame` practice pieces into SY Dungeon pieces.

    python tools/convert_yame.py

Reads the read-only snapshot in tools/orig_yame/ (copied from the practice world; the world
itself is never touched) and writes data/sydungeon/structure/dungeon/*.nbt with:

  - the file renamed to what the piece is (st_passage_1 -> passage_cell); st_gate is left
    out, the surface entrance and the hub took its place
  - every jigsaw's name/target set to the single connector `sydungeon:door`
  - every jigsaw's pool pointed at our pools (passages / cells)
  - the palette and DataVersion brought down from 26.3 to 26.2

The practice world is 26.3 and the mod is 26.2. Between the two the
structure palette changed its keys (`id`/`properties` -> `Name`/`Properties`, DataVersion
5023 -> 4903); the blocks themselves - stone bricks, iron bars, a lantern, a jigsaw - did not,
so renaming the keys is the whole downgrade. Everything else is written back unchanged.
Generated pieces (cap, shaft, ...) are generate_pieces.py's job.

The connector name is one on purpose: which pieces may attach is decided by the *pool* a
jigsaw points at, so a second name would only cost a second plug in the caps pool.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
import nbt  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, 'tools', 'orig_yame')
DST = os.path.join(ROOT, 'src', 'main', 'resources', 'data', 'sydungeon', 'structure', 'dungeon')

NS = 'sydungeon'
DOOR = NS + ':door'

TARGET_DATA_VERSION = nbt.Int(4903)   # Minecraft 26.2


def downgrade_palette(palette):
    """26.3 palette entries to 26.2 ones. Idempotent: 26.2 entries pass through."""
    out = nbt.List(nbt.COMPOUND)
    for entry in palette:
        e = {'Name': nbt.palette_name(entry)}
        props = nbt.palette_props(entry)
        if props:
            e['Properties'] = props
        out.append(e)
    return out

RENAME = {
    'st_passage': 'passage',
    'st_passage_1': 'passage_cell',
    'st_passage_2': 'passage_cells',
    'st_cross': 'cross',
    'st_stair': 'stair',
    'st_cap': 'dead_end',
    'st_room': 'cell',
}

POOL = {
    'yame:pl_passage': NS + ':dungeon/passages',
    'yame:pl_room': NS + ':dungeon/cells',
}


def convert(src, dst):
    root = nbt.read(src)
    palette = root['palette']
    changed = 0
    for block in root['blocks']:
        if nbt.palette_name(palette[block['state']]) != 'minecraft:jigsaw':
            continue
        meta = block['nbt']
        meta['name'] = DOOR
        meta['target'] = DOOR
        meta['pool'] = POOL[meta['pool']]
        changed += 1
    root['palette'] = downgrade_palette(palette)
    root['DataVersion'] = TARGET_DATA_VERSION
    nbt.write(dst, root)
    return changed, root['size']


def main():
    os.makedirs(DST, exist_ok=True)
    for old, new in RENAME.items():
        src = os.path.join(SRC, old + '.nbt')
        dst = os.path.join(DST, new + '.nbt')
        n, size = convert(src, dst)
        print('%-14s -> %-14s %d jigsaw(s), size %s' % (old, new, n, list(size)))


if __name__ == '__main__':
    main()
