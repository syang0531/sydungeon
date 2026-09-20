# -*- coding: utf-8 -*-
"""Bundle the mod's data/ folder as a vanilla datapack, for testing without a mod build.

    python tools/pack_datapack.py                       -> build/datapack/sydungeon.zip
    python tools/pack_datapack.py <path to a world>     -> <world>/datapacks/sydungeon.zip

Everything under src/main/resources/data/ is a datapack already - a mod jar is one with a
class in it. This zips it with a datapack pack.mcmeta so the same files can be dropped into a
vanilla 26.2 world and looked at with `/place`. The world is only written into its
datapacks/ folder; nothing else in it is touched.
"""
import json
import os
import sys
import zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, 'src', 'main', 'resources', 'data')

PACK_MCMETA = {
    'pack': {
        'description': 'SY Dungeon (datapack build for testing)',
        'min_format': 107,
        'max_format': 107,
    }
}


def main():
    if len(sys.argv) > 1:
        out_dir = os.path.join(sys.argv[1], 'datapacks')
        if not os.path.isfile(os.path.join(sys.argv[1], 'level.dat')):
            sys.exit('%s has no level.dat - is it a world folder?' % sys.argv[1])
    else:
        out_dir = os.path.join(ROOT, 'build', 'datapack')
    os.makedirs(out_dir, exist_ok=True)
    out = os.path.join(out_dir, 'sydungeon.zip')
    n = 0
    with zipfile.ZipFile(out, 'w', zipfile.ZIP_DEFLATED) as z:
        z.writestr('pack.mcmeta', json.dumps(PACK_MCMETA, indent=2))
        for dirpath, _, files in os.walk(DATA):
            for f in sorted(files):
                full = os.path.join(dirpath, f)
                arc = os.path.relpath(full, os.path.dirname(DATA)).replace(os.sep, '/')
                z.write(full, arc)
                n += 1
    print('%s  (%d files)' % (out, n))


if __name__ == '__main__':
    main()
