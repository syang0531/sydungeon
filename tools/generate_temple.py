# -*- coding: utf-8 -*-
"""The Temple Swallowed by Vines: a stepped ziggurat in the jungle, wet underneath.

    python tools/generate_temple.py        (or through make_pieces.py)

Writes data/sydungeon/structure/temple/*.nbt and the pools that join them.

THE SAME FENCE AS THE PYRAMID, ONE STOREY LOWER
The silhouette is kept the way the pyramid's is (CLAUDE.md section 10): a jigsaw that points
inside its own piece's box hands that box to everything it places, so a maze grown from `core`
can never leave `core`. What is different is that this temple is half underground, and a box
cannot be escaped once you are inside it (section 19) - so the foundation is part of the same
skin piece. `skin_base` is fourteen courses tall, seven of them below the jungle floor, and
both mazes hang inside it: the dry one at ground level and the wet one under it.

    skin_base 63x14x63  ─inside→ core      49x7x49   the dry maze, and the spine to the well
                        ─inside→ core_deep 49x7x49   the water channels
    skin_mid  49x21x49  ─inside→ vault     21x14x21  the hall of the Illusionist Priest
    shrine     7x 7x 7                                the summit, reached from outside

ONE COLUMN, THREE FLOORS
The well at the middle of the dry maze drops to the cistern below it and rises into the
vault above it, and all three cut the same SHAFT out of their own coordinates - deterministic
geometry, no jigsaws (section 11). The ladder stands against the south wall one block off the
doorway lane, so it has something solid to hang on at every course; verify() climbs it.

NO TRIGGERS
The concept called for tripwire arrow traps. Mobs do not care whose foot it is (section 12),
so what is here instead can only be set off by a player: infested stone that has to be mined,
suspicious gravel that has to be brushed, and a treasury behind an iron door with a lever - a
mob can walk over a pressure plate but it cannot throw a switch. The water channels need no
trigger at all; they are simply moving.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import nbt  # noqa: E402
from generate_pieces import Piece  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DST = os.path.join(ROOT, 'src', 'main', 'resources', 'data', 'sydungeon', 'structure', 'temple')
POOL_JSON = os.path.join(ROOT, 'src', 'main', 'resources', 'data', 'sydungeon', 'worldgen',
                         'template_pool', 'temple')
HAND = os.path.join(ROOT, 'tools', 'handmade', 'temple')

NS = 'sydungeon'
DOOR = NS + ':tpl_door'          # the dry maze's connector
FLOW = NS + ':tpl_flow'          # the wet one's, so the two mazes cannot grow into each other
SPINE = NS + ':tpl_spine'        # the spine chain's, entered only its own way
ANCHOR = NS + ':tpl_anchor'      # skin -> core / vault / shrine
EMPTY = 'minecraft:empty'
PRIORITY = 20                    # skins, cores, spine and vault all go down before the mazes

CELL = 7
BASE = 63                        # the ground terrace is nine cells across
STEP = 7                         # each terrace is this tall and insets by this much
FOOT = 7                         # courses of foundation below the jungle floor
CX = CZ = (BASE - 1) // 2        # 31
GRID = 7                         # cells across inside a core

MOSS = 'minecraft:mossy_cobblestone'
COBBLE = 'minecraft:cobblestone'
BRICK = 'minecraft:mossy_stone_bricks'
CHISEL = 'minecraft:chiseled_stone_bricks'
STAIR = 'minecraft:mossy_cobblestone_stairs'
SLAB = 'minecraft:mossy_cobblestone_slab'
PLANK = 'minecraft:jungle_planks'
LOG = 'minecraft:jungle_log'
FENCE = 'minecraft:jungle_fence'
VINE = 'minecraft:vine'
LEAF = 'minecraft:jungle_leaves'
INFESTED = 'minecraft:infested_stone_bricks'
GRAVEL = 'minecraft:gravel'
SUSPICIOUS = 'minecraft:suspicious_gravel'
WATER = 'minecraft:water'
LANTERN = 'minecraft:lantern'
VOID = 'minecraft:structure_void'
AIR = 'minecraft:air'

HANGING = {'hanging': 'true', 'waterlogged': 'false'}
FLOWING = {'level': '0'}
LEAVES = {'distance': '7', 'persistent': 'true', 'waterlogged': 'false'}

# Where each piece sits in temple coordinates, and how big it is. Every alignment in this file
# is derived from here, so a number changed in one place cannot pull a ladder into a wall
# without verify() saying so.
AT = {
    'skin_base': (0, -FOOT, 0),
    'core': (CELL, 0, CELL),
    'core_deep': (CELL, -FOOT, CELL),
    'skin_mid': (CELL, STEP, CELL),
    'vault': (3 * CELL, STEP, 3 * CELL),
    'shrine': (4 * CELL, 4 * STEP, 4 * CELL),
}
SIZE = {
    'skin_base': (BASE, FOOT + STEP, BASE),
    'core': (GRID * CELL, CELL, GRID * CELL),
    'core_deep': (GRID * CELL, CELL, GRID * CELL),
    'skin_mid': (49, 3 * STEP, 49),
    'vault': (21, 14, 21),
    'shrine': (CELL, CELL, CELL),
}

GATE_CELL = (3, 0)               # the middle of the core's north edge
WELL_CELL = (3, 3)               # its middle, where the three floors meet
SPINE_STEPS = 3                  # spine_1 .. spine_3, and the well is the cell after them

# The one column the three floors share: a three by three hole and a ladder against its south
# wall, one block clear of the doorway lane so every course has something to hang on.
SHAFT = (29, 31, 31, 33)         # x0 x1 z0 z1
CLIMB_X, CLIMB_Z = 29, 33

POOL = {k: NS + ':temple/' + k for k in (
    'start', 'core', 'core_deep', 'skin_mid', 'shrine', 'vault', 'cistern',
    'passages', 'channels', 'caps', 'channel_caps', 'well') +
    tuple('spine_%d' % i for i in range(1, SPINE_STEPS + 1))}

TRIAL_STATE = {'trial_spawner_state': 'inactive', 'ominous': 'false'}
ANY_LIGHT = {'block_light_limit': {'min_inclusive': nbt.Int(0), 'max_inclusive': nbt.Int(15)}}


def trial_spawner(config):
    return {'id': 'minecraft:trial_spawner',
            'normal_config': NS + ':temple/' + config,
            'ominous_config': NS + ':temple/' + config,
            'target_cooldown_length': nbt.Int(2_000_000_000),
            'required_player_range': nbt.Int(14)}


def mob_spawner(entity, count=2):
    return {'id': 'minecraft:mob_spawner',
            'SpawnData': {'entity': {'id': entity}, 'custom_spawn_rules': ANY_LIGHT},
            'Delay': nbt.Short(20), 'MinSpawnDelay': nbt.Short(240),
            'MaxSpawnDelay': nbt.Short(900), 'SpawnCount': nbt.Short(count),
            'MaxNearbyEntities': nbt.Short(5), 'RequiredPlayerRange': nbt.Short(14),
            'SpawnRange': nbt.Short(4)}


def chest(table, facing='north'):
    return ('minecraft:chest', {'facing': facing, 'type': 'single', 'waterlogged': 'false'},
            {'id': 'minecraft:chest', 'LootTable': NS + ':chests/' + table})


def ladder(facing='north'):
    return ('minecraft:ladder', {'facing': facing, 'waterlogged': 'false'})


def half(y):
    """Half the width of the terrace this course belongs to. Below the jungle floor the
    foundation is full width, which is what lets both mazes hang inside one skin piece."""
    if y < 0:
        return (BASE - 1) // 2
    return (BASE - 1) // 2 - STEP * (y // STEP)


def solid(x, y, z):
    return max(abs(x - CX), abs(z - CZ)) <= half(y)


# ------------------------------------------------------------------------------- joins
def anchor_into(p, parent, child, pool=None):
    """The jigsaw on `parent` that hangs `child` inside its own box. Horizontal, so the
    rotation is pinned: the child's anchor faces west and only the identity rotation leaves
    it looking back."""
    ox, oy, oz = AT[parent]
    cx, cy, cz = AT[child]
    p.jigsaw(cx - 1 - ox, cy - oy, cz + SIZE[child][2] // 2 - oz, 'east_up',
             pool or POOL[child], MOSS, priority=PRIORITY, name=DOOR, target=ANCHOR)


def stack_onto(p, parent, child):
    ox, oy, oz = AT[parent]
    cx, cy, cz = AT[child]
    p.jigsaw(cx - ox, cy - 1 - oy, cz - oz, 'up_east', POOL[child], MOSS,
             joint='aligned', priority=PRIORITY, name=DOOR, target=ANCHOR)


def side_anchor(p, child, fill=MOSS):
    """The matching anchor a horizontally placed child carries, on its west face."""
    depth = SIZE[child][2] if child in SIZE else p.size[2]
    p.jigsaw(0, 0, depth // 2, 'west_up', EMPTY, fill, name=ANCHOR, target=ANCHOR)


def under_anchor(p):
    p.jigsaw(0, 0, 0, 'down_east', EMPTY, MOSS, joint='aligned', name=ANCHOR, target=ANCHOR)


# ------------------------------------------------------------------------------- the shell
def entrance_cut(x, y, z):
    """The way in: a recess in the bottom terrace's north face and a three-wide passage
    through it to the core."""
    if CX - 1 <= x <= CX + 1 and 1 <= y <= 4 and z < AT['core'][2]:
        return True
    return CX - 3 <= x <= CX + 3 and 1 <= y <= 6 and z <= 2


def stair_cut(x, y, z):
    """The grand stair up the south face, one terrace at a time: each flight is cut into the
    slope so the summit can be walked to from outside. This is what a ziggurat is for."""
    if not (CX - 2 <= x <= CX + 2) or y < 1:
        return False       # nothing at or below the jungle floor: the first tread IS the
                           # ground course, and the foundation under it is not a stair.
    # One flight per terrace, cut into its SOUTH face - the way in is on the north, and the
    # two would carve each other. The tread climbs a block for every block it moves inward,
    # so each terrace's flight carries straight on from the one below and the last of them
    # lands at the shrine's door on the summit.
    #
    # Four deep, not three. Three leaves exactly two blocks of air over each tread, which is
    # enough to walk under and not enough to jump under - you crack your head on the ceiling
    # the whole way up.
    tread = (CZ + half(y)) - (y % STEP)
    return tread <= z <= tread + 3


def skin(name, keep=None):
    """A slice of the ziggurat: mossy stone inside the silhouette, nothing written outside it,
    so the jungle keeps its own ground against the terraces instead of being cut back to a
    box. `keep` marks what to leave open."""
    ox, oy, oz = AT[name]
    sx, sy, sz = SIZE[name]
    p = Piece(sx, sy, sz, VOID)
    for lx in range(sx):
        for ly in range(sy):
            for lz in range(sz):
                x, y, z = ox + lx, oy + ly, oz + lz
                if not solid(x, y, z):
                    continue
                if keep and keep(x, y, z):
                    p.set(lx, ly, lz, AIR)
                    continue
                block = MOSS
                if y >= 0 and y % STEP == STEP - 1:
                    block = BRICK                      # a course of brick along every terrace
                elif y < 0:
                    block = COBBLE                     # the foundation, never seen
                elif (x + z) % 11 == 0 and y % STEP in (2, 3):
                    block = COBBLE                     # patchy masonry
                p.set(lx, ly, lz, block)
    return p


def dress_terraces(p, name):
    """Vines down the faces and a leaf or two on the terraces: the jungle taking it back."""
    ox, oy, oz = AT[name]
    sx, sy, sz = SIZE[name]
    for lx in range(sx):
        for ly in range(sy):
            for lz in range(sz):
                x, y, z = ox + lx, oy + ly, oz + lz
                if y < 0 or p.grid[(lx, ly, lz)][0] != VOID:
                    continue
                for side, dx, dz in (('south', 0, -1), ('north', 0, 1),
                                     ('east', -1, 0), ('west', 1, 0)):
                    nx, nz = x + dx, z + dz
                    if not solid(nx, y, nz) or not (0 <= lx + dx < sx and 0 <= lz + dz < sz):
                        continue
                    if p.grid[(lx + dx, ly, lz + dz)][0] == AIR:
                        continue
                    if (x * 5 + y * 3 + z) % 4:
                        continue
                    p.set(lx, ly, lz, VINE, {side: 'true', 'up': 'false',
                                             'north': 'false', 'south': 'false',
                                             'east': 'false', 'west': 'false'} | {side: 'true'})
                    break


def skin_base():
    p = skin('skin_base', keep=lambda x, y, z: entrance_cut(x, y, z) or stair_cut(x, y, z))
    dress_terraces(p, 'skin_base')
    anchor_into(p, 'skin_base', 'core')
    anchor_into(p, 'skin_base', 'core_deep')
    stack_onto(p, 'skin_base', 'skin_mid')
    return p


def skin_mid():
    p = skin('skin_mid', keep=stair_cut)
    dress_terraces(p, 'skin_mid')
    under_anchor(p)
    anchor_into(p, 'skin_mid', 'vault')
    stack_onto(p, 'skin_mid', 'shrine')
    return p


def shrine():
    """The summit. No boss and no maze - it is the one room the temple gives away to anyone
    who climbs the outside, and it holds the temple's second chest."""
    p = Piece(CELL, CELL, CELL, MOSS)
    p.box(1, 1, 1, CELL - 2, CELL - 2, CELL - 2, AIR)
    # The doorway is cut from the floor course, not from the course above it: the shrine
    # stands a block higher than the terrace the stair lands on, so the sill is that block.
    # Cut one higher, the last step of the climb is two blocks and cannot be walked.
    p.box(CELL // 2 - 1, 0, CELL - 1, CELL // 2 + 1, 4, CELL - 1, AIR)
    under_anchor(p)
    mid = CELL // 2
    p.box(1, 0, 1, CELL - 2, 0, CELL - 2, BRICK)
    p.set(mid, 1, 1, CHISEL)
    p.set(mid, 2, 1, *chest('temple_shrine', 'south'))
    for x, z in ((1, 1), (CELL - 2, 1)):
        p.set(x, 1, z, LOG, {'axis': 'y'})
        p.set(x, 2, z, LOG, {'axis': 'y'})
    p.set(mid, 4, mid, LANTERN, HANGING)
    return p


# --------------------------------------------------------------------------------- the maze
DOOR_AT = {'west': (0, 0, 3, 'west_up'), 'east': (CELL - 1, 0, 3, 'east_up'),
           'north': (3, 0, 0, 'north_up'), 'south': (3, 0, CELL - 1, 'south_up')}


def cell(doors, fill=MOSS, floor=None):
    p = Piece(CELL, CELL, CELL, fill)
    p.box(1, 1, 1, CELL - 2, CELL - 2, CELL - 2, AIR)
    if floor:
        p.box(1, 0, 1, CELL - 2, 0, CELL - 2, floor)
    mid = CELL // 2
    for side in doors:
        if side == 'west':
            p.box(0, 1, mid - 1, 0, 4, mid + 1, AIR)
        elif side == 'east':
            p.box(CELL - 1, 1, mid - 1, CELL - 1, 4, mid + 1, AIR)
        elif side == 'north':
            p.box(mid - 1, 1, 0, mid + 1, 4, 0, AIR)
        else:
            p.box(mid - 1, 1, CELL - 1, mid + 1, 4, CELL - 1, AIR)
    return p


def door(p, side, pool, name=DOOR, target=DOOR, priority=0):
    x, y, z, orientation = DOOR_AT[side]
    p.jigsaw(x, y, z, orientation, pool, MOSS, priority=priority, name=name, target=target)


def core(name, pool, anchor_pool=None):
    """Solid rock with one way in. The maze carves it and, because that way in points inside
    this box, nothing the maze places can leave it (section 10)."""
    sx, sy, sz = SIZE[name]
    p = Piece(sx, sy, sz, MOSS if name == 'core' else COBBLE)
    side_anchor(p, name, MOSS if name == 'core' else COBBLE)
    return p


def core_dry():
    p = core('core', POOL['spine_1'])
    # The anchor sits one block west of the gate cell and faces east, so the cell lands
    # exactly on the grid - the same trick `anchor_into` uses. Pointing north out of the
    # gate cell would put the spine a block off the grid and outside this box, where the
    # fence throws it away (section 10).
    p.jigsaw(GATE_CELL[0] * CELL - 1, 0, GATE_CELL[1] * CELL + 3, 'east_up',
             POOL['spine_1'], MOSS, priority=PRIORITY, name=DOOR, target=ANCHOR)
    return p


def core_wet():
    p = core('core_deep', POOL['cistern'])
    # the cistern sits under the well, and the channels grow from its four doors
    cx = WELL_CELL[0] * CELL
    cz = WELL_CELL[1] * CELL
    p.jigsaw(cx - 1, 0, cz + 3, 'east_up', POOL['cistern'], COBBLE,
             priority=PRIORITY, name=FLOW, target=ANCHOR)
    return p


def spine(step):
    """One link of the way in. The first is anchored off the core and its north wall is open
    to the entrance tunnel; the rest are chained south, entered by a jigsaw named for the
    chain so the maze cannot join it halfway and turn it round (section 13)."""
    first = step == 1
    p = cell(['north', 'south', 'east'] if first else ['north', 'south', 'west', 'east'],
             floor=BRICK)
    if first:
        side_anchor(p, 'spine_1')          # the west face is the anchor, not a door
    else:
        p.jigsaw(3, 0, 0, 'north_up', EMPTY, MOSS, name=SPINE, target=SPINE)
        door(p, 'west', POOL['passages'])
    nxt = POOL['spine_%d' % (step + 1)] if step < SPINE_STEPS else POOL['well']
    door(p, 'south', nxt, name=DOOR, target=SPINE, priority=PRIORITY)
    door(p, 'east', POOL['passages'])
    for x in (1, CELL - 2):
        p.set(x, 1, 1, LOG, {'axis': 'y'})
        p.set(x, 2, 1, LOG, {'axis': 'y'})
    return p


def shaft_hole(p, origin, y0, y1, rim=None):
    """The column the three floors share, cut into a piece that knows where it stands.
    `origin` is that piece's position in temple coordinates."""
    x0, x1, z0, z1 = SHAFT
    ox, oy, oz = origin
    if rim:
        for x in range(x0 - 1, x1 + 2):
            for z in range(z0 - 1, z1 + 2):
                for y in range(y0, y1 + 1):
                    at = (x - ox, y - oy, z - oz)
                    if at in p.grid and p.grid[at][0] in (AIR, VOID):
                        p.set(at[0], at[1], at[2], rim)
    for x in range(x0, x1 + 1):
        for y in range(y0, y1 + 1):
            for z in range(z0, z1 + 1):
                # The ladder's own row stays in at the first course: a landing to walk out
                # along and step onto the climb. One block beside the ladder is not enough -
                # it would be an island in the middle of the hole, reachable only from the
                # ladder it is there to reach.
                if z == CLIMB_Z and x != CLIMB_X and y == y0:
                    continue
                p.set(x - ox, y - oy, z - oz, AIR)
    for y in range(y0, y1 + 1):
        p.set(CLIMB_X - ox, y - oy, CLIMB_Z - oz, *ladder())


def well():
    """Where the three floors meet: the spine arrives, the cistern is below and the vault is
    above, and all three cut the same column out of their own coordinates (section 11)."""
    p = cell(['north', 'west', 'east'], floor=BRICK)
    p.jigsaw(3, 0, 0, 'north_up', EMPTY, MOSS, name=SPINE, target=SPINE)
    door(p, 'west', POOL['passages'])
    door(p, 'east', POOL['passages'])
    origin = (AT['core'][0] + WELL_CELL[0] * CELL, 0, AT['core'][2] + WELL_CELL[1] * CELL)
    shaft_hole(p, origin, 0, CELL - 1)
    for x, z in ((1, 1), (CELL - 2, 1)):
        p.set(x, 1, z, LOG, {'axis': 'y'})
    p.set(1, 4, 1, LANTERN, HANGING)
    return p


def cistern():
    """Under the well: the water the temple was built for. Four ways out into the channels."""
    # Three ways out, not four: the anchor that places this piece sits in the middle of the
    # west face, which is where a fourth door's jigsaw would go - and the second one written
    # would rub out the first. The anchor wins; a wall is a fine thing to arrive through.
    p = cell(['east', 'north', 'south'], fill=COBBLE, floor=BRICK)
    side_anchor(p, 'cistern', COBBLE)
    for side in ('east', 'north', 'south'):
        door(p, side, POOL['channels'], name=FLOW, target=FLOW)
    origin = (AT['core_deep'][0] + WELL_CELL[0] * CELL, -FOOT,
              AT['core_deep'][2] + WELL_CELL[1] * CELL)
    p.box(1, 1, 1, CELL - 2, 1, CELL - 2, WATER, FLOWING)
    # the hole last: it carves the water back out of the column, so the ladder's foot lands
    # on dry brick with the pool round it rather than in it
    shaft_hole(p, origin, -FOOT + 1, -1, rim=COBBLE)
    return p


def vault():
    """The hall of the Illusionist Priest. The ladder comes up through its floor, so you
    arrive in the middle of it with the spawners already around you - the pyramid's trick,
    and it is the best thing in that dungeon."""
    sx, sy, sz = SIZE['vault']
    p = Piece(sx, sy, sz, MOSS)
    p.box(1, 1, 1, sx - 2, sy - 2, sz - 2, AIR)
    p.box(0, 0, 0, sx - 1, 0, sz - 1, BRICK)
    side_anchor(p, 'vault')
    c = sx // 2
    for x0, z0 in ((3, 3), (3, sz - 5), (sx - 5, 3), (sx - 5, sz - 5)):
        for y in range(1, sy - 1):
            p.box(x0, y, z0, x0 + 1, y, z0 + 1, LOG, {'axis': 'y'})
    # The dais stands to the north of the middle, not on it: the ladder comes up through the
    # middle of the floor, and the first pass put the priest's platform on top of the hole.
    p.box(c - 3, 1, 3, c + 3, 1, 7, BRICK)
    p.box(c - 1, 2, 4, c + 1, 2, 6, CHISEL)
    p.set(c, 3, 5, 'minecraft:trial_spawner', TRIAL_STATE, trial_spawner('priest'))
    for x, z in ((5, 5), (5, sz - 6), (sx - 6, 5), (sx - 6, sz - 6)):
        p.set(x, 1, z, 'minecraft:trial_spawner', TRIAL_STATE, trial_spawner('temple_guards'))
    for x, z in ((c, 4), (4, c), (sx - 5, c), (c, sz - 5)):
        p.set(x, sy - 3, z, LANTERN, HANGING)
    shaft_hole(p, AT['vault'], STEP, STEP, rim=BRICK)
    return p


# ------------------------------------------------------------------------- the maze's cells
def dry(kind):
    doors = {'passage': ['west', 'east'], 'corner': ['west', 'south'],
             'cross': ['west', 'east', 'north', 'south'],
             'guard_post': ['west', 'east', 'north', 'south'],
             'niche': ['west'], 'infested': ['west', 'east'],
             'dig_site': ['west'], 'shrine_room': ['west']}[kind]
    p = cell(doors, floor=BRICK if kind in ('niche', 'shrine_room') else None)
    for side in doors:
        door(p, side, POOL['passages'])
    mid = CELL // 2
    if kind == 'niche':
        p.set(CELL - 2, 1, mid, *chest('temple', 'west'))
        p.set(1, 1, 1, CHISEL)
        p.set(1, 2, 1, LANTERN, {'hanging': 'false', 'waterlogged': 'false'})
    elif kind == 'shrine_room':
        p.box(1, 1, CELL - 2, CELL - 2, 2, CELL - 2, BRICK)
        p.set(mid, 3, CELL - 2, CHISEL)
        p.set(mid, 1, mid, *chest('temple', 'north'))
        p.set(1, 1, 1, 'minecraft:jungle_sapling', {'stage': '0'})
    elif kind == 'infested':
        # mining is the only way to set this off, and a player is the only thing that mines
        for x in range(1, CELL - 1):
            for z in range(1, CELL - 1):
                if (x * 3 + z) % 4 == 0:
                    p.set(x, 0, z, INFESTED)
        p.set(mid, 1, mid, INFESTED)
        p.set(1, 1, CELL - 2, INFESTED)
    elif kind == 'dig_site':
        p.box(1, 1, 1, CELL - 2, 1, CELL - 2, GRAVEL)
        p.box(2, 2, 2, 4, 2, 4, GRAVEL)
        for x, z in ((2, 2), (4, 3), (3, 4)):
            p.set(x, 1, z, SUSPICIOUS)
        p.set(3, 2, 3, SUSPICIOUS)
    elif kind == 'guard_post':
        p.set(mid, 1, mid, 'minecraft:spawner', None, mob_spawner('minecraft:cave_spider', 1))
        p.box(1, 1, 1, 1, 1, 1, 'minecraft:cobweb')
        p.box(CELL - 2, 1, CELL - 2, CELL - 2, 1, CELL - 2, 'minecraft:cobweb')
    return p


def wet(kind):
    doors = {'flow': ['west', 'east'], 'flow_corner': ['west', 'south'],
             'flow_cross': ['west', 'east', 'north', 'south'],
             'pool': ['west', 'east'], 'treasury': ['west'], 'drain': ['west']}[kind]
    p = cell(doors, fill=COBBLE, floor=BRICK)
    for side in doors:
        door(p, side, POOL['channels'], name=FLOW, target=FLOW)
    mid = CELL // 2
    if kind in ('flow', 'flow_corner', 'flow_cross'):
        # a channel with the water moving in it: no trigger, and it takes mobs along too
        p.box(1, 1, 1, CELL - 2, 1, CELL - 2, WATER, FLOWING)
        p.box(1, 0, 1, CELL - 2, 0, CELL - 2, COBBLE)
        for x, z in ((1, 1), (CELL - 2, CELL - 2)):
            p.set(x, 1, z, BRICK)
    elif kind == 'pool':
        p.box(1, 0, 1, CELL - 2, 1, CELL - 2, WATER, FLOWING)
        p.set(mid, 2, mid, 'minecraft:spawner', None, mob_spawner('minecraft:cave_spider', 1))
        p.box(mid - 1, 2, mid - 1, mid + 1, 2, mid + 1, BRICK)
    elif kind == 'drain':
        p.box(1, 1, 1, CELL - 2, 1, CELL - 2, WATER, FLOWING)
        p.set(CELL - 2, 2, mid, *chest('temple', 'west'))
        p.box(CELL - 2, 1, mid, CELL - 2, 1, mid, BRICK)
    elif kind == 'treasury':
        # an iron door and a lever. A mob can tread on a plate; it cannot throw a switch.
        p.box(1, 1, 1, CELL - 2, 4, CELL - 2, COBBLE)
        p.box(2, 1, 2, 4, 3, 4, AIR)
        for y in (1, 2):
            p.set(1, y, mid, 'minecraft:iron_door',
                  {'facing': 'east', 'half': 'lower' if y == 1 else 'upper',
                   'hinge': 'left', 'open': 'false', 'powered': 'false'})
        p.set(1, 3, mid, COBBLE)
        p.set(0, 2, mid - 1, 'minecraft:lever',
              {'face': 'wall', 'facing': 'east', 'powered': 'false'})
        p.set(3, 1, 3, *chest('temple_vault', 'west'))
        p.set(3, 3, 3, LANTERN, HANGING)
    return p


def cap(name, connector, fill=MOSS):
    p = Piece(1, CELL, CELL, fill)
    p.jigsaw(0, 0, 3, 'west_up', POOL[name], fill, name=connector, target=connector)
    return p


# ---------------------------------------------------------------------------------- pools
def element(location, weight):
    return ('    { "weight": %d, "element": { "element_type": "minecraft:single_pool_element",'
            '\n        "location": "%s:temple/%s", "projection": "rigid", '
            '"processors": "%s:temple_weathering" } }' % (weight, NS, location, NS))


def write_pool(name, elements, fallback):
    if not os.path.isdir(POOL_JSON):
        os.makedirs(POOL_JSON)
    text = ('{\n  "fallback": "%s",\n  "elements": [\n%s\n  ]\n}\n'
            % (fallback, ',\n'.join(elements)))
    with open(os.path.join(POOL_JSON, name + '.json'), 'w', encoding='utf-8', newline='\n') as f:
        f.write(text)


# ---------------------------------------------------------------------------------- checks
def verify(pieces):
    problems = []
    for child, parent in (('core', 'skin_base'), ('core_deep', 'skin_base'),
                          ('vault', 'skin_mid')):
        for axis in range(3):
            lo = AT[child][axis] - AT[parent][axis]
            if lo < 0 or lo + SIZE[child][axis] > SIZE[parent][axis]:
                problems.append('%s is not inside %s on axis %d - the maze would be judged '
                                'against the world instead of the box' % (child, parent, axis))

    for name in ('core', 'vault', 'shrine'):
        ox, oy, oz = AT[name]
        sx, sy, sz = SIZE[name]
        margin = min((half(y) - max(abs(x - CX), abs(z - CZ)))
                     for y in range(oy, oy + sy)
                     for x in (ox, ox + sx - 1) for z in (oz, oz + sz - 1))
        want = CELL if name == 'core' else 0
        if margin < want:
            problems.append('%s comes within %d of the terrace face; want %d'
                            % (name, margin, want))

    if WELL_CELL != (GATE_CELL[0], GATE_CELL[1] + SPINE_STEPS):
        problems.append('the spine is %d cells long but the well is at %s: the chain would '
                        'not land on it' % (SPINE_STEPS, (WELL_CELL,)))
    x0, x1, z0, z1 = SHAFT
    if not (x0 <= CLIMB_X <= x1 and z0 <= CLIMB_Z <= z1):
        problems.append('the ladder is not in the shaft')
    well_o = (AT['core'][0] + WELL_CELL[0] * CELL, AT['core'][2] + WELL_CELL[1] * CELL)
    for axis, lo, hi, o in ((0, x0, x1, well_o[0]), (2, z0, z1, well_o[1])):
        if not (o < lo and hi < o + CELL - 1):
            problems.append('the shaft is not inside the well cell, clear of its walls, on '
                            'axis %d' % axis)
        if not (AT['vault'][axis] <= lo and hi < AT['vault'][axis] + SIZE['vault'][axis]):
            problems.append('the shaft misses the vault on axis %d' % axis)
    if CLIMB_Z != z1 or not (well_o[1] + CELL - 1 == z1 + 1):
        problems.append('the ladder does not hang on the well cell\'s south wall')
    lane = (well_o[0] + 2, well_o[0] + 4)
    if lane[0] <= CLIMB_X <= lane[1]:
        problems.append('the ladder hangs on the doorway, which is a hole: move it aside')

    # the climb, floor by floor, as the game stacks the three pieces
    at = {'vault': AT['vault'], 'well': (well_o[0], 0, well_o[1]),
          'cistern': (AT['core_deep'][0] + WELL_CELL[0] * CELL, -FOOT,
                      AT['core_deep'][2] + WELL_CELL[1] * CELL)}
    for y in range(-FOOT + 1, STEP + 1):
        for x in range(x0, x1 + 1):
            for z in range(z0, z1 + 1):
                if z == CLIMB_Z and x != CLIMB_X:
                    continue          # the landing: solid on purpose, at every floor course
                for name, (ox, oy, oz) in at.items():
                    piece = pieces[name]
                    if 0 <= y - oy < piece.size[1]:
                        block = piece.grid[(x - ox, y - oy, z - oz)][0]
                        break
                else:
                    problems.append('nothing covers %s in the shaft' % ((x, y, z),))
                    continue
                want = 'minecraft:ladder' if (x, z) == (CLIMB_X, CLIMB_Z) else AIR
                if block != want:
                    problems.append('%s has %s at %s in the shaft, where the climb needs %s'
                                    % (name, block.split(':')[-1], (x, y, z),
                                       want.split(':')[-1]))
    for name, piece in pieces.items():
        if max(piece.size) > 48 and not name.startswith(('skin', 'core')):
            problems.append('%s is %s: too big to rebuild by hand' % (name, piece.size))
    for line in problems:
        print('  PROBLEM  ' + line)
    if problems:
        raise SystemExit('the temple does not hold together')
    print('  checked: both cores inside the one skin, the maze a cell clear of the terraces, '
          'the shaft aligned through all three floors and the ladder on a wall')


PASSABLE = {'air', 'ladder', 'lantern', 'vine', 'water', 'cobweb', 'jungle_sapling',
            'suspicious_gravel', 'torch'}


def walk_problems():
    """Assemble the temple as the game does and walk it.

    Reads the files that were just written, so it checks the result rather than the intent.
    The route it has to find is the whole dungeon in one line: in at the north door, along
    the spine, down the well into the water, back up into the priest's hall - and, from
    outside, up the grand stair to the shrine."""
    import gen_level_doc as doc

    pieces, pools = doc.load_family('temple'), doc.load_pools('temple')
    start = pools['start']['elements'][0][1].split('/')[-1]
    placed, queue = [(start, (0, 0, 0), pieces[start])], [0]
    while queue:
        name, at, piece = placed[queue.pop(0)]
        for j in piece['jigsaws']:
            pool = pools.get(j['pool'].split('/')[-1])
            if not pool or len(pool['elements']) != 1:
                continue
            child_name = pool['elements'][0][1].split('/')[-1]
            child = pieces.get(child_name)
            if child is None or child_name == name:
                continue
            front, able = doc.facing(j['orientation']), []
            for turn in range(4):
                spun = doc.rotated(child, turn)
                able = [c for c in spun['jigsaws'] if c['name'] == j['target']
                        and doc.facing(c['orientation']) == doc.OPPOSITE[front]]
                if able:
                    child = spun
                    break
            if len(able) != 1:
                continue
            pos = tuple(at[k] + j['pos'][k] + doc.STEP[front][k] - able[0]['pos'][k]
                        for k in range(3))
            if any(p[0] == child_name and p[1] == pos for p in placed):
                continue
            placed.append((child_name, pos, child))
            queue.append(len(placed) - 1)

    off = AT['skin_base']                       # the assembly is drawn from the start piece
    world = {}
    for name, at, piece in placed:
        for (x, y, z), i in piece['grid'].items():
            world[(x + at[0] + off[0], y + at[1] + off[1], z + at[2] + off[2])] =                 piece['palette'][i][0]

    def open_at(p):
        block = world.get(p)
        return block is None or block in PASSABLE

    def stand(p):
        x, y, z = p
        return open_at(p) and open_at((x, y + 1, z)) and not open_at((x, y - 1, z))

    def reach(start_at):
        seen, stack = {start_at}, [start_at]
        while stack:
            x, y, z = stack.pop()
            flat = [(x + 1, y, z), (x - 1, y, z), (x, y, z + 1), (x, y, z - 1)]
            moves = flat + [(a, y + 1, c) for a, _, c in flat]                 + [(a, y - 1, c) for a, _, c in flat]
            if world.get((x, y, z)) == 'ladder' or world.get((x, y + 1, z)) == 'ladder':
                moves.append((x, y + 1, z))
            if world.get((x, y - 1, z)) == 'ladder':
                moves.append((x, y - 1, z))
            for move in moves:
                if move not in seen and (world.get(move) == 'ladder' or stand(move)):
                    seen.add(move)
                    stack.append(move)
        return seen

    inside = reach((CX, 1, 3))                  # a step inside the north door
    problems = []
    for label, spot in (('the spine', (CX, 1, AT['core'][2] + 3)),
                        ('the well', (CX - 1, 1, CZ - 1)),
                        ('the water below it', (CLIMB_X, -FOOT + 1, CLIMB_Z - 1)),
                        ("the priest's hall", (CX, STEP + 1, CZ + 4))):
        if not any((spot[0], spot[1] + dy, spot[2]) in inside for dy in (-1, 0, 1)):
            problems.append('%s cannot be walked to from the door' % label)

    outside = reach((CX, 0, BASE - 1))         # on the first tread of the grand stair
    summit = (CX, 4 * STEP + 1, CZ)
    if not any((summit[0], summit[1] + dy, summit[2]) in outside for dy in (-1, 0, 1)):
        problems.append('the shrine cannot be walked to up the grand stair')
    return problems


def main():
    if not os.path.isdir(DST):
        os.makedirs(DST)
    pieces = {
        'skin_base': skin_base(), 'skin_mid': skin_mid(), 'shrine': shrine(),
        'core': core_dry(), 'core_deep': core_wet(),
        'well': well(), 'cistern': cistern(), 'vault': vault(),
        'passage': dry('passage'), 'corner': dry('corner'), 'cross': dry('cross'),
        'niche': dry('niche'), 'infested': dry('infested'), 'dig_site': dry('dig_site'),
        'guard_post': dry('guard_post'), 'shrine_room': dry('shrine_room'),
        'flow': wet('flow'), 'flow_corner': wet('flow_corner'),
        'flow_cross': wet('flow_cross'), 'pool': wet('pool'),
        'treasury': wet('treasury'), 'drain': wet('drain'),
        'cap': cap('caps', DOOR), 'channel_cap': cap('channel_caps', FLOW, COBBLE),
    }
    for step in range(1, SPINE_STEPS + 1):
        pieces['spine_%d' % step] = spine(step)
    verify(pieces)
    for name, piece in sorted(pieces.items()):
        piece.write(os.path.join(DST, name + '.nbt'))
        print('  %-16s %s' % (name, list(piece.size)))

    write_pool('start', [element('skin_base', 1)], EMPTY)
    write_pool('core', [element('core', 1)], EMPTY)
    write_pool('core_deep', [element('core_deep', 1)], EMPTY)
    write_pool('skin_mid', [element('skin_mid', 1)], EMPTY)
    write_pool('shrine', [element('shrine', 1)], EMPTY)
    write_pool('vault', [element('vault', 1)], EMPTY)
    write_pool('cistern', [element('cistern', 1)], EMPTY)
    write_pool('well', [element('well', 1)], EMPTY)
    for step in range(1, SPINE_STEPS + 1):
        write_pool('spine_%d' % step, [element('spine_%d' % step, 1)], EMPTY)
    write_pool('passages', [element('passage', 10), element('corner', 9),
                            element('cross', 5), element('guard_post', 4),
                            element('niche', 7), element('shrine_room', 5),
                            element('infested', 5), element('dig_site', 5)],
               POOL['caps'])
    write_pool('caps', [element('cap', 1)], EMPTY)
    write_pool('channels', [element('flow', 9), element('flow_corner', 9),
                            element('flow_cross', 4), element('pool', 6),
                            element('drain', 6), element('treasury', 4)],
               POOL['channel_caps'])
    write_pool('channel_caps', [element('channel_cap', 1)], EMPTY)
    print('  pools -> %s' % os.path.relpath(POOL_JSON, ROOT))
    problems = walk_problems()
    for line in problems:
        print('  PROBLEM  ' + line)
    if problems:
        raise SystemExit('the temple is built but you cannot walk it')
    print('  walked: door to spine to well, down to the water, up into the hall, and the '
          'grand stair from the jungle floor to the shrine')


if __name__ == '__main__':
    main()
