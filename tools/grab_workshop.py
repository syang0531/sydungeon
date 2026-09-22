# -*- coding: utf-8 -*-
"""Take pieces back out of the workshop world, without anyone pressing SAVE.

    python tools/grab_workshop.py ice              # newest world
    python tools/grab_workshop.py ice "<world>"

`workshop.py` lays every piece of a family on the ground with a structure block set to SAVE
at its corner. That block is an ordinary block entity, and it carries the piece's name and
the box it covers - so the world itself says where each piece is and how big it is, and the
blocks can be read straight out of the region files (`scan_world.py`). Pressing SAVE in game
only writes the same thing to a file; this skips the step people forget.

What comes back is the **looks**: blocks and the nbt on chests, spawners and signs. Jigsaws
are left behind, because the wiring is the generator's (CLAUDE.md section 16) and it puts its
own back. Files land in tools/handmade/<family>/, which the generator prefers over anything
it would build itself.
"""
import glob
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import nbt  # noqa: E402
import scan_world as scan  # noqa: E402
from generate_pieces import Piece  # noqa: E402
from inspect_world import chunks  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HAND = os.path.join(ROOT, 'tools', 'handmade')
DATA = os.path.join(ROOT, 'src', 'main', 'resources', 'data', 'sydungeon', 'structure')
AIR = 'minecraft:air'


def structure_blocks(world, family):
    """Every SAVE block in the world that names a piece of this family, with its box."""
    want = 'sydungeon:%s/' % family
    out = {}
    for path in sorted(glob.glob(os.path.join(scan.region_dir(world), '*.mca'))):
        for chunk in chunks(path):
            for be in chunk.get('block_entities', []) or []:
                if not str(be.get('id', '')).endswith('structure_block'):
                    continue
                name = str(be.get('name', ''))
                if not name.startswith(want):
                    continue
                origin = tuple(int(be[k]) + int(be[p]) for k, p in
                               (('x', 'posX'), ('y', 'posY'), ('z', 'posZ')))
                size = tuple(int(be['size' + k]) for k in 'XYZ')
                out[name[len(want):]] = (origin, size)
    return out


def block_entities(world, lo, hi):
    """The nbt on chests, spawners and the like inside the box, keyed by local position."""
    out = {}
    for path in sorted(glob.glob(os.path.join(scan.region_dir(world), '*.mca'))):
        for chunk in chunks(path):
            for be in chunk.get('block_entities', []) or []:
                x, y, z = (int(be.get(k, 0)) for k in 'xyz')
                if not (lo[0] <= x <= hi[0] and lo[1] <= y <= hi[1] and lo[2] <= z <= hi[2]):
                    continue
                if str(be.get('id', '')).endswith(('structure_block', 'jigsaw')):
                    continue
                entry = {k: v for k, v in be.items() if k not in ('x', 'y', 'z', 'keepPacked')}
                out[(x - lo[0], y - lo[1], z - lo[2])] = entry
    return out


def shipped(family, name):
    """The piece the mod has now: {(x, y, z): (block, block entity nbt)}."""
    path = os.path.join(DATA, family, name + '.nbt')
    if not os.path.isfile(path):
        return {}
    root = nbt.read(path)
    palette = [nbt.palette_name(e) for e in root['palette']]
    out = {}
    for b in root['blocks']:
        pos = tuple(int(v) for v in b['pos'])
        out[pos] = (palette[int(b['state'])], dict(b['nbt']) if 'nbt' in b else None)
    return out


def relist(name, at, entry, before):
    """Opening a chest in the workshop rolls its loot table there and then: the table is
    replaced by the items it made. Put the table back from the piece the mod is shipping and
    throw the items away - loot is data, and data is not something the workshop edits.

    A chest that cannot be given a table back does not come back at all. There is no way to
    set one from inside the game, so it would ship as a chest holding one roll of somebody's
    creative-mode afternoon. Ask for a chest in a place and the generator will put one there.
    """
    if not str(entry.get('id', '')).endswith('chest'):
        return entry, None                     # a barrel may be empty on purpose
    if 'LootTable' in entry or 'Items' not in entry:
        return entry, None
    was = before.get(at, (None, None))[1] or {}
    entry = {k: v for k, v in entry.items() if k != 'Items'}
    if 'LootTable' in was:
        entry['LootTable'] = was['LootTable']
        return entry, None
    return None, '%s: dropped the chest at %s - it was opened, so it came back with items instead of a loot table' % (name, at)


def grab(world, family, name, origin, size):
    lo = origin
    hi = tuple(origin[i] + size[i] - 1 for i in range(3))
    blocks = scan.read_box(world, lo, hi)
    extra = block_entities(world, lo, hi)
    before, notes, dropped = shipped(family, name), [], set()
    for at in list(extra):
        entry, note = relist(name, at, extra[at], before)
        if note:
            notes.append(note)
        if entry is None:
            dropped.add(at)
            del extra[at]
        else:
            extra[at] = entry
    piece = Piece(size[0], size[1], size[2], AIR)
    jigsaws = 0
    for (x, y, z), value in blocks.items():
        block, props = value if isinstance(value, tuple) else (value, None)
        if not block.startswith('minecraft:'):
            block = 'minecraft:' + block
        at = (x - lo[0], y - lo[1], z - lo[2])
        if block == 'minecraft:jigsaw':
            jigsaws += 1                       # left behind: the generator wires its own
            continue
        if at in dropped:                      # an opened chest, with nothing to put in it
            continue
        piece.set(at[0], at[1], at[2], block, dict(props) if props else None)
    for at, entry in extra.items():
        if at in piece.extra or piece.grid.get(at, (AIR,))[0] != AIR:
            piece.extra[at] = entry
    return piece, jigsaws, notes


def compare(family, name, piece):
    """What changed against the piece the mod is shipping now, in one line."""
    path = os.path.join(DATA, family, name + '.nbt')
    if not os.path.isfile(path):
        return 'new'
    root = nbt.read(path)
    palette = [nbt.palette_name(e) for e in root['palette']]
    old = {}
    for b in root['blocks']:
        x, y, z = (int(v) for v in b['pos'])
        old[(x, y, z)] = palette[int(b['state'])]
    new = {p: v[0] for p, v in piece.grid.items() if v[0] != AIR}
    old = {p: v for p, v in old.items() if v != AIR}
    changed = sum(1 for p in set(old) | set(new) if old.get(p) != new.get(p))
    return 'same' if not changed else '%d blocks differ' % changed


def main():
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    family = sys.argv[1]
    world = scan.world_folder(sys.argv[2] if len(sys.argv) > 2 else None)
    print('world: %s' % world)
    found = structure_blocks(world, family)
    if not found:
        raise SystemExit('no structure block in that world names a piece of %r - run '
                         'tools/workshop.py %s and /function workshop:%s first'
                         % (family, family, family))
    out_dir = os.path.join(HAND, family)
    if not os.path.isdir(out_dir):
        os.makedirs(out_dir)
    for name, (origin, size) in sorted(found.items()):
        piece, jigsaws, notes = grab(world, family, name, origin, size)
        note = compare(family, name, piece)
        piece.write(os.path.join(out_dir, name + '.nbt'))
        print('  %-16s %-12s %-18s %d jigsaws left behind'
              % (name, 'x'.join(str(v) for v in size), note, jigsaws))
        for line in notes:
            print('      !! ' + line)
    print('-> %s' % os.path.relpath(out_dir, ROOT))
    print('   now run the generator: it prefers these over anything it would build itself')


if __name__ == '__main__':
    main()
