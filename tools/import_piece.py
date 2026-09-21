# -*- coding: utf-8 -*-
"""Bring pieces saved in the dev client into the mod.

    python tools/import_piece.py                 # list what the dev worlds have saved
    python tools/import_piece.py tower/hall      # import one (or several) into the mod
    python tools/import_piece.py --all           # import everything

In the dev client (./gradlew runClient) a structure block in SAVE mode named
`sydungeon:tower/hall` writes run/saves/<world>/generated/sydungeon/structure/tower/hall.nbt.
That file is already in the mod's format - the dev client *is* Minecraft 26.2 - so importing
is a copy into src/main/resources/data/sydungeon/structure/.

The point of the check is this: **how a piece looks is yours, how it is wired is not.** A
redecorated room that has lost a jigsaw, moved one, or bricked up a doorway will still build
a structure, just a broken one - a chain that runs backwards, a room with no way in. So the
piece already in the mod is treated as the contract, and the new one is held against it:

  - same size
  - the same jigsaws, block for block: position, facing, name, target, pool, joint
  - every doorway a jigsaw stands in is still open (three wide, four tall)
  - whole 7-block cells, or one block thin (a plug)

Everything else - blocks, furniture, light, the shape of the room inside its walls - is free.
Use `tools/workshop.py` to lay the pieces out in a creative world with their structure blocks
already set up, edit them there, then bring them back with this.

A failed check is printed, not fatal: the file is still copied so you can look at it with
dump_structure.py. The pool JSON is your job either way - this does not edit it.
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


def jigsaws(root):
    """{position: what decides who attaches here}, which is what must survive an edit."""
    out = {}
    palette = root['palette']
    for b in root['blocks']:
        if nbt.palette_name(palette[b['state']]) != 'minecraft:jigsaw':
            continue
        meta = b.get('nbt', {})
        out[tuple(int(v) for v in b['pos'])] = (
            str(nbt.palette_props(palette[b['state']]).get('orientation', '')),
            str(meta.get('name')), str(meta.get('target')), str(meta.get('pool')),
            str(meta.get('joint', 'rollable')))
    return out


def is_air(root, x, y, z):
    palette = root['palette']
    for b in root['blocks']:
        if tuple(int(v) for v in b['pos']) == (x, y, z):
            return nbt.palette_name(palette[b['state']]) == 'minecraft:air'
    return True


def doorway(root, pos, orientation, size):
    """The three-wide, four-tall hole a face jigsaw stands in. Vertical jigsaws are anchors
    rather than doors - the way through those is cut into both pieces by hand - so they are
    not checked here."""
    facing = orientation.split('_')[0]
    x, y, z = pos
    sx, sy, sz = size
    if facing in ('up', 'down'):
        return []
    span = {'west': [(0, y + dy, z + dz) for dy in range(1, 5) for dz in (-1, 0, 1)],
            'east': [(sx - 1, y + dy, z + dz) for dy in range(1, 5) for dz in (-1, 0, 1)],
            'north': [(x + dx, y + dy, 0) for dy in range(1, 5) for dx in (-1, 0, 1)],
            'south': [(x + dx, y + dy, sz - 1) for dy in range(1, 5) for dx in (-1, 0, 1)]}[facing]
    return [c for c in span
            if 0 <= c[0] < sx and 0 <= c[1] < sy and 0 <= c[2] < sz and not is_air(root, *c)]


def check(name, new, old):
    problems = []
    sx, sy, sz = [int(v) for v in new['size']]
    if (sx % CELL or sz % CELL or sy % CELL) and 1 not in (sx, sy, sz):
        problems.append('size %dx%dx%d is not whole 7-cells (nor a 1-block plug)' % (sx, sy, sz))

    mine = jigsaws(new)
    if not mine:
        problems.append('no jigsaw at all - nothing can attach to it')
    known = pools()
    for pos, wiring in sorted(mine.items()):
        if wiring[3] not in known and wiring[3] != 'minecraft:empty':
            problems.append('jigsaw at %s: pool %s is not one of ours' % (pos, wiring[3]))
        blocked = doorway(new, pos, wiring[0], (sx, sy, sz))
        if blocked:
            problems.append('jigsaw at %s: its doorway is walled up at %s'
                            % (pos, ', '.join(str(c) for c in blocked[:4])))

    if old is None:
        problems.append('nothing of this name in the mod yet, so there is no wiring to hold '
                        'it against - check it by hand, and add it to a pool')
        return problems
    if [int(v) for v in old['size']] != [sx, sy, sz]:
        problems.append('size changed: was %s, now %s' % (list(old['size']), [sx, sy, sz]))
    theirs = jigsaws(old)
    for pos in sorted(set(theirs) - set(mine)):
        problems.append('jigsaw gone from %s (was %s -> %s)' % (pos, theirs[pos][1], theirs[pos][3]))
    for pos in sorted(set(mine) - set(theirs)):
        problems.append('jigsaw added at %s (%s -> %s); the generator does not know about it'
                        % (pos, mine[pos][1], mine[pos][3]))
    for pos in sorted(set(mine) & set(theirs)):
        if mine[pos] != theirs[pos]:
            for field, was, now in zip(('facing', 'name', 'target', 'pool', 'joint'),
                                       theirs[pos], mine[pos]):
                if was != now:
                    problems.append('jigsaw at %s: %s was %s, now %s' % (pos, field, was, now))
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
        old = nbt.read(dst) if os.path.exists(dst) else None
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        shutil.copyfile(have[name], dst)
        root = nbt.read(dst)
        problems = check(name, root, old)
        print('%s -> %s  (DataVersion %s, size %s)%s' % (
            name, os.path.relpath(dst, ROOT), root['DataVersion'], list(root['size']),
            '' if problems else '   wiring intact'))
        for p in problems:
            print('   ! ' + p)


if __name__ == '__main__':
    main()
