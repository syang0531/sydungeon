# -*- coding: utf-8 -*-
"""Check every id in our data pack against the game's own jar.

    python tools/validate_data.py

Reads the Minecraft sources jar that the Gradle build unpacked under
build/moddev/artifacts/ and confirms that every item, block, biome, entity,
enchantment and loot table our JSON names actually exists in this version.

This exists because the same bug landed twice, and each time the failure was
silent until the game was already running:

  - `minecraft:chain` became `iron_chain` in 26.2, so the whole cell loot table
    failed to load and every cell chest was empty
  - `minecraft:dappled_forest` is 26.3-only, so the world would not load at all

Both are one line in a JSON file and neither shows up in a build. Run this
before every build; it is a second and it reads the jar, not a list someone
typed. Cross-file references are checked too: a pool that names a structure
piece we do not ship, a spawner config nothing points at, a loot table only a
typo refers to.
"""
import glob
import json
import os
import sys
import zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, 'src', 'main', 'resources', 'data', 'sydungeon')
NS = 'sydungeon'


# Pieces that are deliberately in no pool: a generator reads them and builds something else
# out of them, so they exist to be edited by hand rather than to be placed. `shaft_floor` is
# one floor of the tower's wall, which `generate_tower.py` stacks seven times because a
# structure block cannot save the forty-nine-block whole.
SOURCE_PIECES = set()   # none at the moment; the tower's ring lives in tools/handmade/


def game_jar():
    """The game's own jar for the version in gradle.properties.

    Any of the artifacts moddev unpacks carries the assets and data we read, but only the
    plain one is produced by every build - CI once failed here because it looked for the
    sources jar, which is only unpacked when something asks for it."""
    version = None
    with open(os.path.join(ROOT, 'gradle.properties'), encoding='utf-8') as f:
        for line in f:
            if line.startswith('minecraft_version='):
                version = line.split('=', 1)[1].strip()
    jars = glob.glob(os.path.join(ROOT, 'build', 'moddev', 'artifacts', '*%s*.jar' % version))
    plain = [j for j in jars if not j.endswith(('-sources.jar', '-merged.jar'))]
    for candidate in plain + jars:
        z = zipfile.ZipFile(candidate)
        if 'assets/minecraft/lang/en_us.json' in z.namelist():
            return version, z
        z.close()
    sys.exit('no %s jar with game data under build/moddev/artifacts - run ./gradlew build first'
             % version)


def registry(z, prefix, suffix='.json'):
    return {n[len(prefix):-len(suffix)] for n in z.namelist()
            if n.startswith(prefix) and n.endswith(suffix)}


def ours(kind):
    """Our own ids of one kind, e.g. 'structure' or 'loot_table'."""
    base = os.path.join(DATA, kind)
    out = set()
    for ext in ('.json', '.nbt'):
        for path in glob.glob(os.path.join(base, '**', '*' + ext), recursive=True):
            out.add(os.path.relpath(path, base)[:-len(ext)].replace(os.sep, '/'))
    return out


def walk(node, want, found):
    """Collect every string value under the keys in `want`."""
    if isinstance(node, dict):
        for key, value in node.items():
            if key in want and isinstance(value, str):
                found.setdefault(key, set()).add(value)
            walk(value, want, found)
    elif isinstance(node, list):
        for item in node:
            walk(item, want, found)


KEYS = {'name', 'id', 'block', 'location', 'pool', 'fallback', 'target',
        'enchantment', 'normal_config', 'ominous_config', 'loot_table', 'data',
        'structure', 'processors'}


def main():
    version, z = game_jar()
    print('checking data/%s against Minecraft %s' % (NS, version))

    game = {
        'item': registry(z, 'assets/minecraft/items/'),
        'block': registry(z, 'assets/minecraft/blockstates/'),
        'biome': registry(z, 'data/minecraft/worldgen/biome/'),
        'enchantment': registry(z, 'data/minecraft/enchantment/'),
        'processor_list': registry(z, 'data/minecraft/worldgen/processor_list/'),
        'template_pool': registry(z, 'data/minecraft/worldgen/template_pool/'),
        'loot_table': registry(z, 'data/minecraft/loot_table/'),
        'structure': registry(z, 'data/minecraft/structure/', '.nbt'),
        'biome_tag': registry(z, 'data/minecraft/tags/worldgen/biome/'),
    }
    # Entities and attributes have no data files. The language file is the honest
    # source: every registered one has a translation key, and it is data, not
    # decompiled source that may be reshaped by the next mapping change.
    lang = json.loads(z.read('assets/minecraft/lang/en_us.json'))
    game['entity'] = {key.split('.')[2] for key in lang
                      if key.startswith('entity.minecraft.') and key.count('.') == 2}
    game['attribute'] = {key.rsplit('.', 1)[1] for key in lang
                         if key.startswith('attribute.name.')}

    mine = {kind: ours(kind) for kind in
            ('structure', 'loot_table', 'trial_spawner', 'worldgen/template_pool',
             'worldgen/processor_list')}

    problems = []
    used_pools = set()
    used_pieces = set()
    used_tables = set()
    used_spawners = set()

    for path in sorted(glob.glob(os.path.join(DATA, '**', '*.json'), recursive=True)):
        rel = os.path.relpath(path, os.path.dirname(DATA)).replace(os.sep, '/')
        with open(path, encoding='utf-8') as f:
            try:
                doc = json.load(f)
            except ValueError as e:
                problems.append('%s: not valid JSON: %s' % (rel, e))
                continue
        found = {}
        walk(doc, KEYS, found)
        # a biome tag's values are bare ids
        if '/tags/worldgen/biome/' in rel:
            for value in doc.get('values', []):
                if value.startswith('#'):
                    if value[1:].removeprefix('minecraft:') not in game['biome_tag']:
                        problems.append('%s: no biome tag %s' % (rel, value))
                elif value.removeprefix('minecraft:') not in game['biome']:
                    problems.append('%s: no biome %s' % (rel, value))
        for key, values in found.items():
            for value in values:
                if not isinstance(value, str) or ':' not in value:
                    continue
                namespace, name = value.split(':', 1)
                if key == 'name' and namespace == 'minecraft':
                    # `name` in our JSON is only ever a loot table entry: an item.
                    # This is the check that would have caught `minecraft:chain`.
                    if name not in game['item']:
                        problems.append('%s: no item minecraft:%s' % (rel, name))
                elif key == 'id' and namespace == 'minecraft':
                    # an item in a component, an entity to spawn, or an attribute
                    if not (name in game['item'] or name in game['entity']
                            or name in game['block'] or name in game['attribute']):
                        problems.append('%s: minecraft:%s is not an item, entity, block or attribute'
                                        % (rel, name))
                elif key == 'block' and namespace == 'minecraft' and name not in game['block']:
                    problems.append('%s: no block minecraft:%s' % (rel, name))
                elif key == 'enchantment' and namespace == 'minecraft' and name not in game['enchantment']:
                    problems.append('%s: no enchantment minecraft:%s' % (rel, name))
                elif key == 'location':
                    (used_pieces if namespace == NS else set()).add(name)
                    if namespace == NS and name not in mine['structure']:
                        problems.append('%s: no structure piece %s' % (rel, value))
                    elif namespace == 'minecraft' and name not in game['structure']:
                        problems.append('%s: no vanilla structure %s' % (rel, value))
                elif key in ('pool', 'fallback'):
                    if namespace == NS:
                        used_pools.add(name)
                        if name not in mine['worldgen/template_pool']:
                            problems.append('%s: no template pool %s' % (rel, value))
                    elif name != 'empty' and name not in game['template_pool']:
                        problems.append('%s: no vanilla template pool %s' % (rel, value))
                elif key == 'processors' and namespace == NS:
                    if name not in mine['worldgen/processor_list']:
                        problems.append('%s: no processor list %s' % (rel, value))
                elif key == 'processors' and namespace == 'minecraft':
                    if name != 'empty' and name not in game['processor_list']:
                        problems.append('%s: no vanilla processor list %s' % (rel, value))
                elif key in ('data', 'loot_table') and namespace == NS:
                    used_tables.add(name)
                    if name not in mine['loot_table']:
                        problems.append('%s: no loot table %s' % (rel, value))
                elif key in ('normal_config', 'ominous_config') and namespace == NS:
                    used_spawners.add(name)
                    if name not in mine['trial_spawner']:
                        problems.append('%s: no trial spawner config %s' % (rel, value))

    # the jigsaws inside our .nbt pieces name pools and trial spawner configs too
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import nbt  # noqa: E402
    for path in sorted(glob.glob(os.path.join(DATA, 'structure', '**', '*.nbt'), recursive=True)):
        rel = os.path.relpath(path, os.path.dirname(DATA)).replace(os.sep, '/')
        root = nbt.read(path)
        palette = root['palette']
        # every block a piece places has to exist in this version too: a typo here is a
        # piece that logs an error and leaves a hole where the block should be
        for entry in palette:
            block = nbt.palette_name(entry)
            if block.startswith('minecraft:') and block.split(':', 1)[1] not in game['block']:
                problems.append('%s: no block %s in its palette' % (rel, block))
        for block in root['blocks']:
            meta = block.get('nbt')
            if not meta:
                continue
            name = nbt.palette_name(palette[block['state']])
            if name == 'minecraft:jigsaw':
                pool = meta.get('pool', '')
                if pool.startswith(NS + ':'):
                    used_pools.add(pool.split(':', 1)[1])
                    if pool.split(':', 1)[1] not in mine['worldgen/template_pool']:
                        problems.append('%s: jigsaw names missing pool %s' % (rel, pool))
            elif name == 'minecraft:trial_spawner':
                for key in ('normal_config', 'ominous_config'):
                    config = meta.get(key, '')
                    if config.startswith(NS + ':'):
                        used_spawners.add(config.split(':', 1)[1])
                        if config.split(':', 1)[1] not in mine['trial_spawner']:
                            problems.append('%s: no trial spawner config %s' % (rel, config))
            # any block entity may carry one: chests and barrels, and the brushable blocks
            # that suspicious sand and gravel are
            table = meta.get('LootTable', '')
            if table.startswith(NS + ':'):
                used_tables.add(table.split(':', 1)[1])
                if table.split(':', 1)[1] not in mine['loot_table']:
                    problems.append('%s: no loot table %s' % (rel, table))

    # things we ship that nothing refers to: usually a rename that missed a spot
    start_pools = set()
    for path in glob.glob(os.path.join(DATA, 'worldgen', 'structure', '*.json')):
        with open(path, encoding='utf-8') as f:
            pool = json.load(f).get('start_pool', '')
        if pool.startswith(NS + ':'):
            start_pools.add(pool.split(':', 1)[1])
    orphans = []
    for name in sorted(mine['worldgen/template_pool'] - used_pools - start_pools):
        orphans.append('template pool %s is never used' % name)
    for name in sorted(mine['structure'] - used_pieces - SOURCE_PIECES):
        orphans.append('structure piece %s is in no pool' % name)
    for name in sorted(mine['loot_table'] - used_tables):
        orphans.append('loot table %s is never used' % name)
    for name in sorted(mine['trial_spawner'] - used_spawners):
        orphans.append('trial spawner config %s is never used' % name)

    for line in problems:
        print('  ERROR  ' + line)
    for line in orphans:
        print('  unused ' + line)
    if problems:
        sys.exit('\n%d problem(s). These break the game, not the build.' % len(problems))
    # geometry the ids cannot catch: a start piece standing on a plinth of its own
    # footing, which puts its doorway that many blocks above the grass (section 30)
    import check_starts
    if check_starts.main():
        sys.exit('the start pieces do not sit on the ground.')
    print('ok: %d pieces, %d pools, %d loot tables, %d spawner configs%s' % (
        len(mine['structure']), len(mine['worldgen/template_pool']), len(mine['loot_table']),
        len(mine['trial_spawner']),
        '' if not orphans else ', %d unused' % len(orphans)))


if __name__ == '__main__':
    main()
