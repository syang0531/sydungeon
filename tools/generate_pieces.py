# -*- coding: utf-8 -*-
"""Pieces that are simpler to describe than to build: plugs and the entrance shaft.

    python tools/generate_pieces.py        (or through make_pieces.py)

Writes into data/sydungeon/structure/dungeon/:

  cap         1x7x7   a stone-brick wall across a doorway; fallback for every horizontal pool
  shaft_cap   7x1x7   a stone-brick floor across the shaft; fallback for the shafts pool
  entrance    7x7x7   the surface piece: a roofed pavilion with a ladder hole in its floor;
                      its down jigsaw uses the shaft_first pool (shaft only), so at least one
                      shaft sits between the surface and the hub
  shaft      7x21x7   three cells of ladder, joins entrance/shaft above to shaft/hub below
  hub         7x7x7   where the shaft lands: ladder down the north wall, doors W/E to the
                      maze, S to the boss branch
  boss_room 21x21x21  the end of the boss branch: dais, five trial spawners, pillars
  boss_passage 7x7x7  the cross with its east door continuing the boss branch; N numbered
                      copies force a minimum corridor length (their pools are written too)

The shaft column is x 2..4, z 1..3 - off centre on purpose, so the ladder at z=1 hangs on the
north wall (z=0), which is solid in every piece of the chain; the hub therefore has no north
door. Vertical jigsaws use joint=aligned so the column stays on the same side all the way down.

Anything here is a starting point: open it in the dev client, make it look like something,
save it under the same name and import it (tools/import_piece.py). The wiring - jigsaw
positions, names, pools - is what must survive that; dump_structure.py shows it.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
import nbt  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DST = os.path.join(ROOT, 'src', 'main', 'resources', 'data', 'sydungeon', 'structure', 'dungeon')

DATA_VERSION = nbt.Int(4903)   # Minecraft 26.2
NS = 'sydungeon'
DOOR = NS + ':door'
# The boss branch has its own connector name, so a boss piece can only be entered through the
# door meant for it: a cross-shaped boss_passage would otherwise be entered through its
# continuation door as often as not, and the branch would lose the room.
BOSS_DOOR = NS + ':boss_door'
POOL = {k: NS + ':dungeon/' + k for k in (
    'passages', 'cells', 'caps', 'shaft_first', 'shafts', 'shaft_caps', 'boss_approach')}

# The boss corridor is at least this many pieces long before the room may appear. Each step
# is its own pool (boss_approach_1 .. _N) holding one boss_passage variant whose continuation
# points at the next pool; the last pool, boss_approach, mixes passage and room. A jigsaw's
# pool is baked into the piece, which is why the chain needs N copies of the same passage.
MIN_BOSS_STEPS = 5
POOL_JSON = os.path.join(ROOT, 'src', 'main', 'resources', 'data', 'sydungeon', 'worldgen',
                         'template_pool', 'dungeon')

STONE = 'minecraft:stone_bricks'
CHISELED = 'minecraft:chiseled_stone_bricks'
AIR = 'minecraft:air'

# The boss branch is placed before the maze grows, so its 2x2x2-cell room finds room.
BOSS_PRIORITY = 10

# Trial spawner block entities: the fight itself is configured in data/sydungeon/trial_spawner/.
# The cooldown is as good as forever, so each dungeon's boss is fought once.
TRIAL_COOLDOWN = 2_000_000_000


def trial_spawner_nbt(config):
    return {
        'id': 'minecraft:trial_spawner',
        'normal_config': NS + ':dungeon/' + config,
        'ominous_config': NS + ':dungeon/' + config,
        'target_cooldown_length': nbt.Int(TRIAL_COOLDOWN),
        'required_player_range': nbt.Int(14),
    }


TRIAL_SPAWNER_STATE = {'trial_spawner_state': 'inactive', 'ominous': 'false'}


def jigsaw_nbt(pool, final_state, joint='rollable', priority=0, name=DOOR, target=DOOR):
    return {
        'name': name,
        'target': target,
        'pool': pool,
        'final_state': final_state,
        'joint': joint,
        'placement_priority': nbt.Int(priority),
        'selection_priority': nbt.Int(priority),
        'id': 'minecraft:jigsaw',
    }


class Piece:
    """A block grid plus a palette, written out as a structure file."""

    def __init__(self, sx, sy, sz, fill=AIR):
        self.size = (sx, sy, sz)
        self.grid = {}
        self.extra = {}   # pos -> block entity nbt
        for x in range(sx):
            for y in range(sy):
                for z in range(sz):
                    self.grid[(x, y, z)] = (fill, None)

    def set(self, x, y, z, name, props=None, block_nbt=None):
        self.grid[(x, y, z)] = (name, tuple(sorted(props.items())) if props else None)
        if block_nbt is not None:
            self.extra[(x, y, z)] = block_nbt
        else:
            self.extra.pop((x, y, z), None)

    def box(self, x0, y0, z0, x1, y1, z1, name, props=None):
        for x in range(x0, x1 + 1):
            for y in range(y0, y1 + 1):
                for z in range(z0, z1 + 1):
                    self.set(x, y, z, name, props)

    def jigsaw(self, x, y, z, orientation, pool, final_state, joint='rollable', priority=0, name=DOOR, target=DOOR):
        self.set(x, y, z, 'minecraft:jigsaw', {'orientation': orientation},
                 jigsaw_nbt(pool, final_state, joint, priority, name, target))

    def ladder(self, x, y0, y1, z, facing):
        for y in range(y0, y1 + 1):
            self.set(x, y, z, 'minecraft:ladder', {'facing': facing, 'waterlogged': 'false'})

    def write(self, path):
        """Write the piece out. `structure_void` is left out of the list entirely rather than
        written as a block: a template places what it lists and touches nothing else, so an
        omitted position is the only way to mean "leave the world alone". Written out it is
        placed - an invisible, walk-through block that replaced the turf round the tower's
        foot with something you can see straight through to the dirt below."""
        palette_index = {}
        palette = nbt.List(nbt.COMPOUND)
        blocks = nbt.List(nbt.COMPOUND)
        sx, sy, sz = self.size
        for x in range(sx):
            for y in range(sy):
                for z in range(sz):
                    key = self.grid[(x, y, z)]
                    if key[0] == 'minecraft:structure_void':
                        continue
                    if key not in palette_index:
                        palette_index[key] = len(palette)
                        entry = {'Name': key[0]}
                        if key[1]:
                            entry['Properties'] = dict(key[1])
                        palette.append(entry)
                    block = {'pos': nbt.List(nbt.INT, [nbt.Int(x), nbt.Int(y), nbt.Int(z)]),
                             'state': nbt.Int(palette_index[key])}
                    if (x, y, z) in self.extra:
                        block['nbt'] = self.extra[(x, y, z)]
                    blocks.append(block)
        nbt.write(path, {
            'size': nbt.List(nbt.INT, [nbt.Int(v) for v in self.size]),
            'entities': nbt.List(nbt.COMPOUND),
            'blocks': blocks,
            'palette': palette,
            'DataVersion': DATA_VERSION,
        })


def cap():
    p = Piece(1, 7, 7, STONE)
    p.jigsaw(0, 0, 3, 'west_up', POOL['caps'], STONE)
    return p


def shaft_cap():
    p = Piece(7, 1, 7, STONE)
    p.jigsaw(3, 0, 2, 'up_east', POOL['shaft_caps'], STONE, joint='aligned')
    return p


def entrance():
    p = Piece(7, 7, 7)
    p.box(0, 0, 0, 6, 0, 6, STONE)                 # floor
    p.box(0, 5, 0, 6, 5, 6, STONE)                 # roof
    p.box(0, 1, 0, 6, 4, 0, STONE)                 # north wall, the ladder hangs on it
    for x, z in ((0, 6), (6, 6)):                  # south corner pillars
        p.box(x, 1, z, x, 4, z, STONE)
    p.box(2, 0, 1, 4, 0, 3, AIR)                   # the hole
    p.ladder(3, 1, 4, 1, 'south')
    p.set(3, 4, 4, 'minecraft:lantern', {'hanging': 'true', 'waterlogged': 'false'})
    # shaft_first holds only the shaft, so the maze is never right under the surface
    p.jigsaw(3, 0, 2, 'down_east', POOL['shaft_first'], AIR, joint='aligned')
    return p


def shaft():
    p = Piece(7, 21, 7, STONE)
    p.box(2, 0, 1, 4, 20, 3, AIR)
    p.ladder(3, 0, 20, 1, 'south')
    p.jigsaw(3, 20, 2, 'up_east', POOL['shafts'], AIR, joint='aligned')
    p.jigsaw(3, 0, 2, 'down_east', POOL['shafts'], AIR, joint='aligned')
    return p


def hub():
    p = Piece(7, 7, 7, STONE)
    p.box(1, 1, 1, 5, 5, 5, AIR)                   # room
    p.box(2, 6, 1, 4, 6, 3, AIR)                   # hole in the ceiling, under the shaft
    p.ladder(3, 1, 6, 1, 'south')
    for x0, x1, z0, z1 in ((0, 0, 2, 4), (6, 6, 2, 4), (2, 4, 6, 6)):
        p.box(x0, 1, z0, x1, 4, z1, AIR)           # doors W, E, S
    p.jigsaw(3, 6, 2, 'up_east', POOL['shafts'], AIR, joint='aligned')
    p.jigsaw(0, 0, 3, 'west_up', POOL['passages'], STONE)
    p.jigsaw(6, 0, 3, 'east_up', POOL['passages'], STONE)
    # the south door starts the boss branch, and is expanded before anything else
    p.jigsaw(3, 0, 6, 'south_up', POOL['boss_approach'] + '_1', STONE, priority=BOSS_PRIORITY, target=BOSS_DOOR)
    return p


def boss_room():
    """21x21x21: three cells each way. One door, west face, dead centre (z=10, the middle
    cell's centre), so the room is centred on the corridor that reaches it.

    Inside: a 7x7 dais in the middle with the boss spawner on its top step, a guard spawner in
    each quadrant, 2x2 chiseled pillars in the corners, chiseled bands round the walls at two
    heights, lanterns on chains from the ceiling, soul lanterns in the corners.
    """
    n = 21
    p = Piece(n, n, n, STONE)
    p.box(1, 1, 1, n - 2, n - 2, n - 2, AIR)       # the hall
    for x in range(1, n - 1):                      # floor pattern
        for z in range(1, n - 1):
            if x % 3 == 1 and z % 3 == 1:
                p.set(x, 0, z, CHISELED)
    for y in (7, 14):                              # bands on the walls
        for i in range(n):
            for x, z in ((0, i), (n - 1, i), (i, 0), (i, n - 1)):
                p.set(x, y, z, CHISELED)
    for x0, z0 in ((2, 2), (2, n - 4), (n - 4, 2), (n - 4, n - 4)):
        p.box(x0, 1, z0, x0 + 1, n - 2, z0 + 1, CHISELED)   # corner pillars
    c = n // 2                                     # 10
    p.box(c - 3, 1, c - 3, c + 3, 1, c + 3, STONE) # dais
    p.box(c - 1, 2, c - 1, c + 1, 2, c + 1, CHISELED)       # its top step
    p.box(0, 1, c - 1, 0, 4, c + 1, AIR)           # the west door, centred
    for x, z in ((c, 4), (c, n - 5), (4, c), (n - 5, c), (6, 6), (6, n - 7), (n - 7, 6), (n - 7, n - 7)):
        p.box(x, n - 4, z, x, n - 2, z, 'minecraft:iron_chain', {'axis': 'y', 'waterlogged': 'false'})
        p.set(x, n - 5, z, 'minecraft:lantern', {'hanging': 'true', 'waterlogged': 'false'})
    for x, z in ((1, 1), (1, n - 2), (n - 2, 1), (n - 2, n - 2)):
        p.set(x, 1, z, 'minecraft:soul_lantern', {'hanging': 'false', 'waterlogged': 'false'})
    p.set(c, 3, c, 'minecraft:trial_spawner', TRIAL_SPAWNER_STATE, trial_spawner_nbt('boss'))
    for x, z in ((5, 5), (n - 6, 5), (5, n - 6), (n - 6, n - 6)):
        p.set(x, 1, z, 'minecraft:trial_spawner', TRIAL_SPAWNER_STATE, trial_spawner_nbt('guards'))
    p.jigsaw(0, 0, c, 'west_up', POOL['passages'], STONE, name=BOSS_DOOR)
    return p


def boss_passage(next_pool):
    """The cross, rewired: the west door is the boss-branch entry (named boss_door), the east
    door continues the branch into `next_pool` (targets boss_door, with priority), and north
    and south still open onto the maze, so the branch costs the maze nothing."""
    src = os.path.join(DST, 'cross.nbt')
    root = nbt.read(src)
    palette = root['palette']
    for block in root['blocks']:
        if nbt.palette_name(palette[block['state']]) != 'minecraft:jigsaw':
            continue
        orientation = nbt.palette_props(palette[block['state']]).get('orientation')
        if orientation == 'east_up':
            block['nbt'] = jigsaw_nbt(next_pool, STONE, priority=BOSS_PRIORITY, target=BOSS_DOOR)
        elif orientation == 'west_up':
            block['nbt'] = jigsaw_nbt(POOL['passages'], STONE, name=BOSS_DOOR)
    return root


def element(location, weight):
    return ('    { "weight": %d, "element": { "element_type": "minecraft:single_pool_element",\n'
            '        "location": "sydungeon:dungeon/%s", "projection": "rigid", '
            '"processors": "sydungeon:dungeon_weathering" } }' % (weight, location))


def write_pool(name, elements, fallback='sydungeon:dungeon/caps'):
    text = '{\n  "fallback": "%s",\n  "elements": [\n%s\n  ]\n}\n' % (fallback, ',\n'.join(elements))
    with open(os.path.join(POOL_JSON, name + '.json'), 'w', encoding='utf-8', newline='\n') as f:
        f.write(text)


def boss_chain():
    """boss_passage_1 .. _N and their pools, then boss_passage (the repeating one) and boss_approach."""
    for k in range(1, MIN_BOSS_STEPS + 1):
        next_pool = POOL['boss_approach'] + ('_%d' % (k + 1) if k < MIN_BOSS_STEPS else '')
        nbt.write(os.path.join(DST, 'boss_passage_%d.nbt' % k), boss_passage(next_pool))
        write_pool('boss_approach_%d' % k, [element('boss_passage_%d' % k, 1)])
    nbt.write(os.path.join(DST, 'boss_passage.nbt'), boss_passage(POOL['boss_approach']))
    write_pool('boss_approach', [element('boss_passage', 2), element('boss_room', 1)])
    print('%-14s x%d + boss_passage, pools boss_approach_1..%d and boss_approach' % (
        'boss_passage_k', MIN_BOSS_STEPS, MIN_BOSS_STEPS))


PIECES = {
    'cap': cap,
    'shaft_cap': shaft_cap,
    'entrance': entrance,
    'shaft': shaft,
    'hub': hub,
    'boss_room': boss_room,
}


def main():
    os.makedirs(DST, exist_ok=True)
    for name, make in PIECES.items():
        piece = make()
        piece.write(os.path.join(DST, name + '.nbt'))
        print('%-14s generated, size %s' % (name, list(piece.size)))
    boss_chain()


if __name__ == '__main__':
    main()
