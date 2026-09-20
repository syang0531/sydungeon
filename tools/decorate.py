# -*- coding: utf-8 -*-
"""Put the things worth finding into the pieces: loot chests and spawners.

    python tools/decorate.py        (or through make_pieces.py)

Edits pieces already in data/sydungeon/structure/dungeon/ in place:

  cell        a chest against the back wall, loot table sydungeon:chests/dungeon_cell
  dead_end    a spawner in the middle and a chest in the corner, loot sydungeon:chests/dungeon_guard
  cross_guard a copy of the cross with a spawner in the middle of the crossing

and takes the lanterns out of every piece except the entrance and the boss room. A lit
corridor spawns nothing on its own; a dark one is a vanilla dungeon, and that is most of
what makes it one.

Both are block entities with NBT, which is the one thing a structure block cannot save
convincingly from a hand-built world: a chest saves its *items*, not a loot table, and a
spawner saves whatever /setblock was typed. Writing them here keeps the NBT in one readable
place. A block already at the spot is overwritten; running twice gives the same result.

The spawner carries custom_spawn_rules allowing any block light, because every piece has a
lantern and a monster spawner in a lit corridor otherwise spawns nothing.
"""
import glob
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
import nbt  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DST = os.path.join(ROOT, 'src', 'main', 'resources', 'data', 'sydungeon', 'structure', 'dungeon')

ANY_LIGHT = {'block_light_limit': {'min_inclusive': nbt.Int(0), 'max_inclusive': nbt.Int(15)}}

# (weight, entity id)
GUARDS = [(4, 'minecraft:zombie'), (4, 'minecraft:skeleton'), (2, 'minecraft:spider'), (1, 'minecraft:cave_spider')]


def spawn_data(entity):
    return {'entity': {'id': entity}, 'custom_spawn_rules': ANY_LIGHT}


def spawner_nbt():
    return {
        'id': 'minecraft:mob_spawner',
        'SpawnData': spawn_data(GUARDS[0][1]),
        'SpawnPotentials': nbt.List(nbt.COMPOUND, [
            {'weight': nbt.Int(w), 'data': spawn_data(e)} for w, e in GUARDS]),
        'Delay': nbt.Short(20),
        'MinSpawnDelay': nbt.Short(200),
        'MaxSpawnDelay': nbt.Short(800),
        'SpawnCount': nbt.Short(4),
        'MaxNearbyEntities': nbt.Short(6),
        'RequiredPlayerRange': nbt.Short(16),
        'SpawnRange': nbt.Short(4),
    }


def chest_nbt(loot_table):
    return {'id': 'minecraft:chest', 'LootTable': loot_table}


def put(root, pos, name, props, block_nbt):
    """Set the block at pos, adding a palette entry if needed."""
    palette = root['palette']
    entry = {'Name': name}
    if props:
        entry['Properties'] = props
    index = None
    for i, e in enumerate(palette):
        if e == entry:
            index = i
    if index is None:
        palette.append(entry)
        index = len(palette) - 1
    for block in root['blocks']:
        if tuple(block['pos']) == pos:
            block['state'] = nbt.Int(index)
            if block_nbt is None:
                block.pop('nbt', None)
            else:
                block['nbt'] = block_nbt
            return
    raise KeyError('no block at %s' % (pos,))


def decorate_cell(root):
    # The cell is open to the north (the bars); the chest sits against the south wall,
    # facing the bars so its lid opens toward whoever broke in.
    put(root, (3, 1, 5), 'minecraft:chest',
        {'facing': 'north', 'type': 'single', 'waterlogged': 'false'},
        chest_nbt('sydungeon:chests/dungeon_cell'))


def decorate_dead_end(root):
    # The dead end opens west. Spawner in the middle of the room, chest in the far corner.
    put(root, (3, 1, 3), 'minecraft:spawner', None, spawner_nbt())
    put(root, (5, 1, 1), 'minecraft:chest',
        {'facing': 'west', 'type': 'single', 'waterlogged': 'false'},
        chest_nbt('sydungeon:chests/dungeon_guard'))


def decorate_cross_guard(root):
    put(root, (3, 1, 3), 'minecraft:spawner', None, spawner_nbt())


def strip_lanterns(root):
    """Lanterns become air. Returns how many."""
    palette = root['palette']
    air = None
    for i, e in enumerate(palette):
        if nbt.palette_name(e) == 'minecraft:air':
            air = i
    if air is None:
        palette.append({'Name': 'minecraft:air'})
        air = len(palette) - 1
    n = 0
    for block in root['blocks']:
        if nbt.palette_name(palette[block['state']]) == 'minecraft:lantern':
            block['state'] = nbt.Int(air)
            block.pop('nbt', None)
            n += 1
    return n


DECORATE = {
    'cell': decorate_cell,
    'dead_end': decorate_dead_end,
}

DERIVED = {
    'cross_guard': ('cross', decorate_cross_guard),
}

KEEP_LIT = ('entrance', 'boss_room')


def main():
    for name, fn in DECORATE.items():
        path = os.path.join(DST, name + '.nbt')
        root = nbt.read(path)
        fn(root)
        nbt.write(path, root)
        print('%-14s decorated' % name)
    for name, (source, fn) in DERIVED.items():
        root = nbt.read(os.path.join(DST, source + '.nbt'))
        fn(root)
        nbt.write(os.path.join(DST, name + '.nbt'), root)
        print('%-14s derived from %s' % (name, source))
    for path in sorted(glob.glob(os.path.join(DST, '*.nbt'))):
        name = os.path.basename(path)[:-4]
        if name in KEEP_LIT:
            continue
        root = nbt.read(path)
        n = strip_lanterns(root)
        if n:
            nbt.write(path, root)
            print('%-14s %d lantern(s) removed' % (name, n))


if __name__ == '__main__':
    main()
