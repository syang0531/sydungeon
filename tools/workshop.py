# -*- coding: utf-8 -*-
"""A workbench in the dev client: every piece laid out, ready to edit and save back.

    python tools/workshop.py                 # write the pack into every dev world
    python tools/workshop.py tower           # only that family
    python tools/workshop.py --list          # just print the layout

Then in the game:

    /reload
    /function workshop:tower                 (or workshop:all)

It builds, starting from where you stand and running east and south, a plot for every piece:
the piece itself placed from the mod, and a **structure block already set to SAVE it back**
under the same name, with its bounding box showing. Edit the piece in place, press SAVE on
its structure block, leave the game, and:

    python tools/import_piece.py tower/hall

which holds the new one against the wiring of the old (see that file). So the loop is:

    /function workshop:tower  ->  build  ->  SAVE  ->  import_piece.py  ->  ./gradlew build

WHAT IS WORTH EDITING BY HAND
A structure block saves at most 48 blocks a side, so `shaft` (25x49x25) and `core_shaft`
(21x49x21) cannot come back this way and stay in the generator. Everything else can, and that
includes the three pieces the tower's look actually lives in - `base`, `crown` and `roof`.

The cores are solid blocks of stone on purpose: the rooms carve them. There is nothing to
edit in one, so they are skipped.
"""
import glob
import io
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import nbt  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SAVES = os.path.join(ROOT, 'run', 'saves')
SRC = os.path.join(ROOT, 'src', 'main', 'resources', 'data', 'sydungeon', 'structure')
PACK = 'sydungeon_workshop'
MAX_SIDE = 48                      # a structure block cannot save more than this
GAP = 5                            # blocks of air between plots, so boxes never touch
ROW = 160                          # start a new row of plots past this many blocks east

SKIP = {'core_base', 'core_shaft'}  # solid blocks the rooms carve; nothing to edit


def families():
    return sorted(d for d in os.listdir(SRC) if os.path.isdir(os.path.join(SRC, d)))


def pieces(family):
    out = []
    for path in sorted(glob.glob(os.path.join(SRC, family, '*.nbt'))):
        name = os.path.splitext(os.path.basename(path))[0]
        size = tuple(int(v) for v in nbt.read(path)['size'])
        out.append((name, size, max(size) <= MAX_SIDE and name not in SKIP))
    return out


def layout(family):
    """Plots left to right, wrapping into rows, each row as deep as its tallest plot."""
    plots, x, z, deepest = [], 0, 0, 0
    for name, size, editable in pieces(family):
        sx, sy, sz = size
        if x and x + sx > ROW:
            x, z, deepest = 0, z + deepest + GAP, 0
        plots.append((name, size, editable, x, z))
        x += sx + GAP
        deepest = max(deepest, sz)
    return plots


def commands(family):
    """One `place` and one structure block a plot. Coordinates are relative to whoever runs
    the function, so you fly somewhere empty and run it there."""
    out = ['say workshop: %s - structure blocks are set to SAVE under the same name' % family]
    for name, size, editable, x, z in layout(family):
        sx, sy, sz = size
        out.append('place template sydungeon:%s/%s ~%d ~ ~%d' % (family, name, x, z))
        if not editable:
            continue
        block = ('structure_block[mode=save]{mode:"SAVE",name:"sydungeon:%s/%s",'
                 'sizeX:%d,sizeY:%d,sizeZ:%d,posX:1,posY:1,posZ:1,'
                 'showboundingbox:1b,ignoreEntities:0b,author:"%s"}'
                 % (family, name, sx, sy, sz, 'sydungeon'))
        out.append('setblock ~%d ~-1 ~%d %s' % (x - 1, z - 1, block))
    return out


def write(world, wanted):
    root = os.path.join(world, 'datapacks', PACK)
    os.makedirs(os.path.join(root, 'data', 'workshop', 'function'), exist_ok=True)
    with io.open(os.path.join(root, 'pack.mcmeta'), 'w', encoding='utf-8', newline='\n') as fh:
        json.dump({'pack': {'pack_format': 88, 'description': 'SY Dungeon piece workshop'}},
                  fh, indent=2)
    every = []
    for family in wanted:
        path = os.path.join(root, 'data', 'workshop', 'function', family + '.mcfunction')
        with io.open(path, 'w', encoding='utf-8', newline='\n') as fh:
            fh.write('\n'.join(commands(family)) + '\n')
        every.append('function workshop:%s' % family)
    with io.open(os.path.join(root, 'data', 'workshop', 'function', 'all.mcfunction'),
                 'w', encoding='utf-8', newline='\n') as fh:
        fh.write('\n'.join(every) + '\n')
    return root


def show(family):
    print('%s:' % family)
    for name, size, editable, x, z in layout(family):
        print('   %-14s %-12s at ~%-4d ~ ~%-4d %s'
              % (name, '%dx%dx%d' % size, x, z,
                 '' if editable else ('(%s, no structure block)' %
                                      ('solid core' if name in SKIP else 'over 48 a side'))))


def main():
    args = [a for a in sys.argv[1:] if a != '--list']
    wanted = args or families()
    for family in wanted:
        if family not in families():
            raise SystemExit('unknown family %r' % family)
        show(family)
    if '--list' in sys.argv[1:]:
        return
    worlds = [d for d in glob.glob(os.path.join(SAVES, '*')) if os.path.isdir(d)]
    if not worlds:
        print('\nno dev world yet - run ./gradlew runClient, make a creative world, then '
              'run this again')
        return
    for world in worlds:
        print('\n-> %s' % os.path.relpath(write(world, wanted), ROOT))
    print('\nin the game:  /reload   then   /function workshop:%s' % wanted[0])


if __name__ == '__main__':
    main()
