# -*- coding: utf-8 -*-
"""What every boss actually gives, and whether the chests still start with a bed.

    python tools/check_rewards.py

Three promises in docs/concepts.md are about loot, and loot is a pile of JSON that drifts
quietly:

  2.2  a signature is certain - "here, and always", never a roll
  2.4  one piece of enchanted gear per boss, so a full set is six wins
  8    the first pool of every chest is survival kit, so no chest is four loaves of bread

The pyramid lost its gear piece once and nobody noticed until the prison and the pyramid were
read side by side. So this reads the tables instead: a pool with one roll and one outcome is
a promise, anything else is a chance. It prints what each boss promises - which is the table
in concepts.md section 7, rebuilt from what the game will actually hand over.
"""
import io
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, 'src', 'main', 'resources', 'data', 'sydungeon')

GEAR = ('sword', 'axe', 'pickaxe', 'shovel', 'hoe', 'helmet', 'chestplate', 'leggings',
        'boots', 'bow', 'crossbow', 'trident', 'elytra', 'shield')
TIER = ('diamond_', 'netherite_')

# What a first roll must not be. Saying it this way round is the point of section 8: the
# first roll is the one thing every chest owes you, and treasure is what the rest is for.
TREASURE = ('diamond', 'netherite', 'elytra', 'shulker_shell', 'trident', 'enchanted_book',
            'smithing_template', 'ancient_debris', 'totem', 'heart_of_the_sea',
            'enchanted_golden_apple', 'gold_block', 'emerald_block')
# The two chests that deliberately break section 8, and why. Written down rather than
# quietly skipped: an exception nobody can see is how the rule rots.
KIT_EXEMPT = {
    'pyramid_crypt': 'its first roll IS the promise - the crypt over the pharaoh (4.2)',
    'tower_library': 'stationery: it stands beside the enchanting table (4.3)',
}

# What each boss is promised to hand over, by item id. The prose lives in concepts.md 7;
# this is the same promise written so a machine can hold us to it.
PROMISED = {
    'dungeon/boss': [],                       # gear only: "an enchanted diamond piece"
    'pyramid/pharaoh': ['obsidian', 'flint_and_steel'],
    'tower/archmage': ['ender_eye', 'totem_of_undying'],
    'swamp/mother': ['brewing_stand', 'nether_wart', 'blaze_powder'],
    'ice/frost_lord': ['enchanted_book'],
    'temple/priest': ['enchanted_book'],
    'camp/warlord': ['ominous_bottle', 'emerald'],
    'grave/captain': ['enchanted_book', 'saddle'],
    'dwarf/smith_king': ['anvil', 'diamond'],
    'light/deep_sentinel': ['trident', 'heart_of_the_sea', 'sponge'],
    'fort/boss': ['blaze_rod', 'wither_skeleton_skull'],
    'vault/boss': ['netherite_scrap', 'netherite_upgrade_smithing_template',
                   'ancient_debris'],
    'sanctum/boss': ['enchanted_book', 'enchanted_golden_apple'],
    'spire/boss': ['elytra', 'shulker_shell'],
    'chorus/boss': ['ender_pearl', 'obsidian'],
}


def read(path):
    with io.open(path, encoding='utf-8') as f:
        return json.load(f)


def certain(pool):
    """A pool that always gives the same thing: one roll, and one outcome whatever the
    weights. Entries that differ only in which piece of gear count as one promise."""
    if pool.get('rolls') != 1:
        return None
    names = [e.get('name', '') for e in pool['entries'] if e.get('type') == 'minecraft:item']
    if len(names) != len(pool['entries']) or not names:
        return None
    if len(set(names)) == 1:
        return names[0].split(':')[-1]
    if all(any(g in n for g in GEAR) for n in names):
        return 'gear: ' + ' or '.join(n.split(':')[-1] for n in names)
    return 'one of: ' + ' or '.join(n.split(':')[-1] for n in names)


def is_gear(name):
    return any(g in name for g in GEAR)


def main():
    problems = []

    # --- every boss's promise ---------------------------------------------------------
    print('what each boss hands over, from the tables themselves')
    for family in sorted(os.listdir(os.path.join(DATA, 'trial_spawner'))):
        for config in sorted(os.listdir(os.path.join(DATA, 'trial_spawner', family))):
            if 'guard' in config:
                continue
            key = '%s/%s' % (family, config[:-5])
            spawner = read(os.path.join(DATA, 'trial_spawner', family, config))
            tables = [e['data'] for e in spawner.get('loot_tables_to_eject', [])]
            if len(tables) != 1:
                problems.append('%s ejects %d tables; a boss gives one' % (key, len(tables)))
                continue
            path = os.path.join(DATA, 'loot_table', *tables[0].split(':')[-1].split('/'))
            table = read(path + '.json')
            promises = [c for c in (certain(p) for p in table['pools']) if c]
            wears = [p for p in promises if any(g in p for g in GEAR)]
            tiered = [p for p in wears if any(m in p for m in TIER)]
            print('  %-20s %s' % (key, ' + '.join(promises) or '(nothing certain)'))
            if not promises:
                problems.append('%s promises nothing: every pool is a roll (section 2.2)'
                                % key)
            if not wears:
                problems.append('%s hands over nothing to wear or wield; every boss gives '
                                'one (section 2.4) - the pyramid lost its piece once' % key)
            if len(tiered) > 1:
                problems.append('%s promises %d diamond-tier pieces; section 2.4 says one '
                                'per boss, so a full set is six wins' % (key, len(tiered)))
            for want in PROMISED.get(key, []):
                if not any(want in p for p in promises):
                    problems.append('%s does not promise %s, which concepts.md section 7 '
                                    'says it does' % (key, want))

    # --- every chest's first roll ------------------------------------------------------
    chests = os.path.join(DATA, 'loot_table', 'chests')
    for name in sorted(os.listdir(chests)):
        if name[:-5] in KIT_EXEMPT:
            continue
        table = read(os.path.join(chests, name))
        first = table['pools'][0]
        names = [e.get('name', '').split(':')[-1] for e in first['entries']]
        # A count is a promise however large; a range is a chance wearing a promise's hat.
        if not isinstance(first.get('rolls'), int):
            problems.append('%s rolls its first pool %s; section 8 wants a certain thing, '
                            'and a range is not certain'
                            % (name[:-5], json.dumps(first.get('rolls'))))
        loot = [n for n in names if any(t in n for t in TREASURE)]
        if loot:
            problems.append('%s starts with %s; the first roll is survival kit and the rest '
                            'is what treasure is for (section 8)' % (name[:-5], loot[0]))

    # --- two large dungeons must not want the same biome -------------------------------
    tags = os.path.join(DATA, 'tags', 'worldgen', 'biome', 'has_structure')
    LARGE = {'dungeon', 'pyramid', 'tower', 'swamp', 'ice', 'temple', 'camp', 'grave',
             'dwarf', 'light', 'fort', 'vault', 'sanctum', 'spire', 'chorus'}
    owner = {}
    for name in sorted(os.listdir(tags)):
        key = name[:-5]
        for biome in read(os.path.join(tags, name))['values']:
            owner.setdefault(biome, []).append(key)
    for biome, who in sorted(owner.items()):
        big = [k for k in who if k in LARGE]
        if len(big) > 1:
            problems.append('%s is claimed by %s; concepts.md section 4.0 gives a biome one '
                            'large dungeon' % (biome, ' and '.join(big)))

    # --- no two structure sets on the same salt ----------------------------------------
    sets = os.path.join(DATA, 'worldgen', 'structure_set')
    salts = {}
    for name in sorted(os.listdir(sets)):
        placement = read(os.path.join(sets, name))['placement']
        salts.setdefault(placement['salt'], []).append(name[:-5])
        if placement['separation'] >= placement['spacing']:
            problems.append('%s has separation %d and spacing %d: nothing would generate'
                            % (name[:-5], placement['separation'], placement['spacing']))
    for salt, who in sorted(salts.items()):
        if len(who) > 1:
            problems.append('%s share the salt %d, so they would land on the same spots'
                            % (' and '.join(who), salt))

    print()
    for line in problems:
        print('  PROBLEM  ' + line)
    if problems:
        return 1
    print('checked: every boss promises its signature and something to wear or wield, every '
          'chest starts with a certain thing that is not treasure, one large dungeon per '
          'biome, no shared salts')
    for name in sorted(KIT_EXEMPT):
        print('  section 8 exception: %-14s %s' % (name, KIT_EXEMPT[name]))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
