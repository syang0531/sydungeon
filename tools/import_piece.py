# -*- coding: utf-8 -*-
"""Bring pieces saved in the dev client into the mod.

    python tools/import_piece.py                 # list what the dev worlds have saved
    python tools/import_piece.py dungeon/foo     # import one (or several) into the mod
    python tools/import_piece.py --all           # import everything

In the dev client (./gradlew runClient) a structure block in SAVE mode with the name
`sydungeon:dungeon/foo` writes run/saves/<world>/generated/sydungeon/structure/dungeon/foo.nbt.
That file is already in the mod's format - the dev client *is* Minecraft 26.2 - so importing is
a copy into src/main/resources/data/sydungeon/structure/. This does the copy and, because a
piece that looks right can still be wired wrong, checks what cannot be seen in the world:

  - every jigsaw is named `sydungeon:door` or `sydungeon:boss_door` and targets one of them
  - every jigsaw points at one of our pools
  - the piece is a whole number of 7-block cells, or one block thin (a plug)
  - a horizontal jigsaw sits on a cell floor at the centre of its face; a vertical one sits
    on the top or bottom layer in the shaft column (x 3, z 2)

A failed check is printed, not fatal: the file is still copied so you can look at it with
dump_structure.py, but the pool JSON is your job either way - this does not edit it.
"""
import glob
import os
import shutil
import sys

sys.path.insert(0, os.path.dirname(__file__))
import nbt  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SAVES = os.path.join(ROOT, 'run', 'saves')
DST = os.path.join(ROOT, 'src', 'main', 'resources', 'data', 'sydungeon', 'structure')
POOLS_DIR = os.path.join(ROOT, 'src', 'main', 'resources', 'data', 'sydungeon', 'worldgen', 'template_pool')
CELL = 7
DOOR = 'sydungeon:door'
BOSS_DOOR = 'sydungeon:boss_door'
NAMES = (DOOR, BOSS_DOOR)


def saved():
    """{piece name: path} over every dev world; a newer file wins when two worlds have one."""
    found = {}
    for path in glob.glob(os.path.join(SAVES, '*', 'generated', 'sydungeon', 'structure', '**', '*.nbt'),
                          recursive=True):
        rel = os.path.relpath(path, os.path.join(path.split('generated')[0], 'generated', 'sydungeon',
                                                 'structure'))
        name = rel[:-4].replace(os.sep, '/')
        if name not in found or os.path.getmtime(path) > os.path.getmtime(found[name]):
            found[name] = path
    return found


def pools():
    out = set()
    for path in glob.glob(os.path.join(POOLS_DIR, '**', '*.json'), recursive=True):
        rel = os.path.relpath(path, POOLS_DIR)[:-5].replace(os.sep, '/')
        out.add('sydungeon:' + rel)
    return out


def check(name, root):
    problems = []
    sx, sy, sz = root['size']
    if (sx % CELL or sz % CELL or sy % CELL) and 1 not in (sx, sy, sz):
        problems.append('size %dx%dx%d is not whole 7-cells (nor a 1-block plug)' % (sx, sy, sz))
    palette = root['palette']
    known = pools()
    jigsaws = 0
    for b in root['blocks']:
        if nbt.palette_name(palette[b['state']]) != 'minecraft:jigsaw':
            continue
        jigsaws += 1
        x, y, z = b['pos']
        meta = b.get('nbt', {})
        where = 'jigsaw at (%d,%d,%d)' % (x, y, z)
        if meta.get('name') not in NAMES or meta.get('target') not in NAMES:
            problems.append('%s: name/target %s/%s, expected one of %s' % (
                where, meta.get('name'), meta.get('target'), NAMES))
        if meta.get('pool') not in known:
            problems.append('%s: pool %s is not one of %s' % (where, meta.get('pool'), sorted(known)))
        orientation = nbt.palette_props(palette[b['state']]).get('orientation', '')
        vertical = orientation.startswith(('up_', 'down_'))
        if vertical:
            if y not in (0, sy - 1):
                problems.append('%s: vertical jigsaw not on the top or bottom layer' % where)
            if (x, z) != (3, 2):
                problems.append('%s: vertical jigsaw not in the shaft column (3, _, 2)' % where)
            if meta.get('joint') != 'aligned':
                problems.append('%s: vertical jigsaw should be joint=aligned' % where)
        else:
            if y % CELL:
                problems.append('%s: not on a cell floor (y %% 7 != 0)' % where)
            on_face = x in (0, sx - 1) or z in (0, sz - 1)
            centred = (x % CELL == 3) or (z % CELL == 3)
            if not (on_face and centred):
                problems.append('%s: not at the centre of a face' % where)
    if jigsaws == 0:
        problems.append('no jigsaw at all - nothing can attach to it')
    return problems


def main():
    have = saved()
    if not have:
        sys.exit('no pieces saved yet under %s' % SAVES)
    args = sys.argv[1:]
    if not args:
        print('saved in the dev client (import with: python tools/import_piece.py <name>):')
        for name, path in sorted(have.items()):
            print('  %-28s %s' % (name, os.path.relpath(path, ROOT)))
        return
    names = sorted(have) if args == ['--all'] else args
    for name in names:
        if name not in have:
            print('%s: not saved in any dev world' % name)
            continue
        dst = os.path.join(DST, *name.split('/')) + '.nbt'
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        shutil.copyfile(have[name], dst)
        root = nbt.read(dst)
        problems = check(name, root)
        print('%s -> %s  (DataVersion %s, size %s)' % (name, os.path.relpath(dst, ROOT),
                                                      root['DataVersion'], list(root['size'])))
        for p in problems:
            print('   ! ' + p)


if __name__ == '__main__':
    main()
