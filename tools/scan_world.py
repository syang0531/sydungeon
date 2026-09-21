# -*- coding: utf-8 -*-
"""Read blocks straight out of a world, to see what was built there by hand.

    python tools/scan_world.py                         # newest world, around the player
    python tools/scan_world.py "<world>" x y z r       # a box of radius r around a point

Prints where the player is, then every block that is not plain terrain inside the box, as
layer maps and a tally. This is how a piece built in the dev client gets read back without
anyone having to remember to press SAVE on a structure block first.

Reads the Anvil region format directly (zlib chunks, NBT inside, palette per section).
"""
import glob
import gzip
import os
import struct
import sys
import zlib
from collections import Counter, OrderedDict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import nbt  # noqa: E402
from inspect_world import chunks  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SAVES = os.path.join(ROOT, 'run', 'saves')

# what the world makes on its own; anything else in the box was put there by a person
NATURAL = {
    'air', 'cave_air', 'void_air', 'stone', 'deepslate', 'dirt', 'grass_block', 'sand',
    'gravel', 'water', 'lava', 'bedrock', 'granite', 'diorite', 'andesite', 'tuff',
    'coarse_dirt', 'podzol', 'clay', 'sandstone', 'snow', 'snow_block', 'ice', 'packed_ice',
    'oak_log', 'oak_leaves', 'birch_log', 'birch_leaves', 'spruce_leaves',
    'dark_oak_log', 'dark_oak_leaves', 'jungle_log', 'jungle_leaves', 'acacia_log',
    'acacia_leaves', 'cherry_log', 'cherry_leaves', 'mangrove_log', 'mangrove_leaves',
    'pale_oak_log', 'pale_oak_leaves', 'grass', 'short_grass', 'tall_grass', 'fern',
    'large_fern', 'dead_bush', 'seagrass', 'tall_seagrass', 'kelp', 'kelp_plant',
    'sugar_cane', 'cactus', 'vine', 'lily_pad', 'moss_block', 'moss_carpet',
    'copper_ore', 'iron_ore', 'coal_ore', 'gold_ore', 'redstone_ore', 'lapis_ore',
    'diamond_ore', 'emerald_ore', 'deepslate_iron_ore', 'deepslate_coal_ore',
    'deepslate_copper_ore', 'deepslate_gold_ore', 'deepslate_redstone_ore',
    'deepslate_lapis_ore', 'deepslate_diamond_ore', 'deepslate_emerald_ore',
    'dripstone_block', 'pointed_dripstone', 'amethyst_block', 'budding_amethyst',
    'calcite', 'smooth_basalt', 'raw_iron_block', 'raw_copper_block',
    'dandelion', 'poppy', 'blue_orchid', 'allium', 'azure_bluet', 'oxeye_daisy',
    'cornflower', 'lily_of_the_valley', 'sunflower', 'lilac', 'rose_bush', 'peony',
    'brown_mushroom', 'red_mushroom', 'sweet_berry_bush', 'pumpkin', 'melon',
    'powder_snow', 'mud', 'rooted_dirt', 'hanging_roots', 'azalea', 'flowering_azalea',
}


def world_folder(name=None):
    if name:
        return name if os.path.isdir(name) else os.path.join(SAVES, name)
    worlds = [d for d in glob.glob(os.path.join(SAVES, '*')) if os.path.isdir(d)]
    if not worlds:
        sys.exit('no world under %s' % SAVES)
    return max(worlds, key=os.path.getmtime)


def region_dir(world):
    for parts in (('dimensions', 'minecraft', 'overworld', 'region'), ('region',)):
        path = os.path.join(world, *parts)
        if os.path.isdir(path):
            return path
    sys.exit('no overworld region folder in %s' % world)


def player(world):
    """Where the player last stood: in a single-player world that is the player file under
    players/data/, and only level.dat's spawn if there is none."""
    for path in sorted(glob.glob(os.path.join(world, 'players', 'data', '*.dat'))):
        pos = nbt.read(path).get('Pos')
        if pos:
            return tuple(int(v) for v in pos)
    spawn = nbt.read(os.path.join(world, 'level.dat'))['Data'].get('spawn', {}).get('pos')
    return tuple(int(v) for v in spawn) if spawn else None


def section_blocks(section):
    """Unpack one 16x16x16 section into {(x, y, z) inside it: (name, properties)}.

    The properties matter: a staircase read back without its `facing` is a pile of steps all
    pointing north, which is what a spiral built by hand turns into if they are thrown away.
    """
    states = section.get('block_states')
    if not states:
        return {}
    palette = [(nbt.palette_name(e).replace('minecraft:', ''),
                dict(nbt.palette_props(e) or {}) or None) for e in states['palette']]
    if len(palette) == 1:
        return {} if palette[0] in ('air', 'cave_air', 'void_air') else \
            {(x, y, z): palette[0] for x in range(16) for y in range(16) for z in range(16)}
    data = states.get('data')
    if data is None:
        return {}
    bits = max(4, (len(palette) - 1).bit_length())
    per_long = 64 // bits
    mask = (1 << bits) - 1
    out = {}
    for i in range(4096):
        word, offset = divmod(i, per_long)
        if word >= len(data):
            break
        index = (int(data[word]) >> (offset * bits)) & mask
        if index >= len(palette):
            continue
        name = palette[index]
        if name[0] in ('air', 'cave_air', 'void_air'):
            continue
        y, rest = divmod(i, 256)
        z, x = divmod(rest, 16)
        out[(x, y, z)] = name
    return out


def read_box(world, lo, hi):
    """{(x, y, z): (block name, properties)} for everything solid in the box."""
    found = {}
    cx0, cx1 = lo[0] >> 4, hi[0] >> 4
    cz0, cz1 = lo[2] >> 4, hi[2] >> 4
    wanted = {(cx, cz) for cx in range(cx0, cx1 + 1) for cz in range(cz0, cz1 + 1)}
    for path in sorted(glob.glob(os.path.join(region_dir(world), '*.mca'))):
        rx, rz = (int(v) for v in os.path.basename(path).split('.')[1:3])
        if not any(cx >> 5 == rx and cz >> 5 == rz for cx, cz in wanted):
            continue
        for chunk in chunks(path):
            cx, cz = int(chunk.get('xPos', 0)), int(chunk.get('zPos', 0))
            if (cx, cz) not in wanted:
                continue
            for section in chunk.get('sections', []):
                sy = int(section['Y'])
                if sy * 16 > hi[1] or sy * 16 + 15 < lo[1]:
                    continue
                for (x, y, z), name in section_blocks(section).items():
                    wx, wy, wz = cx * 16 + x, sy * 16 + y, cz * 16 + z
                    if lo[0] <= wx <= hi[0] and lo[1] <= wy <= hi[1] and lo[2] <= wz <= hi[2]:
                        found[(wx, wy, wz)] = name
    return found


def built(blocks):
    return {p: v for p, v in blocks.items() if v[0] not in NATURAL}


def names(blocks):
    return {p: v[0] for p, v in blocks.items()}


def layers(blocks, glyphs=None):
    """Print each Y layer of a set of blocks, north up."""
    if not blocks:
        print('  nothing')
        return
    xs = [p[0] for p in blocks]
    ys = [p[1] for p in blocks]
    zs = [p[2] for p in blocks]
    flat = names(blocks) if blocks and isinstance(next(iter(blocks.values())), tuple) else blocks
    blocks = flat
    glyphs = glyphs or OrderedDict(
        (n, '#=+*o%&@$xXvVnN^~-:;abcdefghijklmpqrstuwyz'[i % 43])
        for i, n in enumerate(sorted(set(blocks.values()))))
    for y in range(min(ys), max(ys) + 1):
        rows = []
        for z in range(min(zs), max(zs) + 1):
            row = ''.join(glyphs.get(blocks.get((x, y, z)), '.') if (x, y, z) in blocks else '.'
                          for x in range(min(xs), max(xs) + 1))
            rows.append(row)
        if not any(r.strip('.') for r in rows):
            continue
        print('--- y = %d' % y)
        for z, row in zip(range(min(zs), max(zs) + 1), rows):
            print('  z=%4d  %s' % (z, row))
    print('legend: ' + '  '.join('%s %s' % (g, n) for n, g in sorted(glyphs.items(),
                                                                     key=lambda kv: kv[1])))


def main():
    args = sys.argv[1:]
    world = world_folder(args[0] if args else None)
    print('world: %s' % os.path.relpath(world, ROOT))
    here = player(world)
    print('player at %s' % (here,))
    if len(args) >= 5:
        cx, cy, cz, r = (int(v) for v in args[1:5])
    else:
        if here is None:
            sys.exit('no player position; pass x y z r')
        cx, cy, cz, r = here[0], here[1], here[2], 80
    lo = (cx - r, max(-64, cy - 40), cz - r)
    hi = (cx + r, cy + 40, cz + r)
    print('scanning %s .. %s' % (lo, hi))
    blocks = read_box(world, lo, hi)
    mine = built(blocks)
    print('%d solid blocks, %d of them placed by hand' % (len(blocks), len(mine)))
    tally = Counter(v[0] for v in mine.values())
    for name, n in tally.most_common(30):
        print('   %-28s %d' % (name, n))
    if mine:
        xs = [p[0] for p in mine]
        ys = [p[1] for p in mine]
        zs = [p[2] for p in mine]
        print('built box: x %d..%d  y %d..%d  z %d..%d  (%dx%dx%d)'
              % (min(xs), max(xs), min(ys), max(ys), min(zs), max(zs),
                 max(xs) - min(xs) + 1, max(ys) - min(ys) + 1, max(zs) - min(zs) + 1))


if __name__ == '__main__':
    main()
