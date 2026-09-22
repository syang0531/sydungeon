# -*- coding: utf-8 -*-
"""Build every piece under data/sydungeon/structure/dungeon/ from what is in the repo.

    python tools/make_pieces.py

Ten steps, each its own script:
  1. convert_yame.py     the hand-built practice pieces, renamed and rewired, brought to 26.2
  2. generate_pieces.py  the prison's plugs and entrance shaft, described in code
  3. decorate.py         loot chests and spawners placed into the pieces above
  4. generate_pyramid.py the pyramid: shell, spine, burial chamber, maze and its pools
  5. generate_tower.py   the wizard's tower: shell, stairwell, library, sanctum and its pools
  6. generate_swamp.py   the witch's swamp: the village on stilts and the brewery under it
  7. generate_ice.py     the ice fortress: keep, curtain wall, towers and the ice cellars
  8. generate_temple.py  the jungle temple: terraces, the dry maze, the water under it
  9. generate_camp.py    the warlord's camp: palisade, longhouse, watchtowers, the mine
 10. generate_grave.py   the cursed graveyard: the chapel, the plots, the ossuary

Pieces saved from the dev client and brought in with import_piece.py are not touched by
this - they are already ours. Note that step 1 overwrites the eight converted pieces, so a
piece that was later reshaped in the dev client must be re-imported after running this, or
removed from convert_yame.RENAME once the practice version is no longer wanted.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

import convert_yame  # noqa: E402
import decorate  # noqa: E402
import generate_pieces  # noqa: E402
import generate_tower  # noqa: E402
import generate_pyramid  # noqa: E402
import generate_swamp  # noqa: E402
import generate_ice  # noqa: E402
import generate_temple  # noqa: E402
import generate_camp  # noqa: E402
import generate_grave  # noqa: E402

if __name__ == '__main__':
    print('-- convert')
    convert_yame.main()
    print('-- generate')
    generate_pieces.main()
    print('-- decorate')
    decorate.main()
    print('-- pyramid')
    generate_pyramid.main()
    print('-- tower')
    generate_tower.main()
    print('-- swamp')
    generate_swamp.main()
    print('-- ice')
    generate_ice.main()
    print('-- temple')
    generate_temple.main()
    print('-- camp')
    generate_camp.main()
    print('-- grave')
    generate_grave.main()
