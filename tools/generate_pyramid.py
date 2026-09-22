# -*- coding: utf-8 -*-
"""The Great Pyramid: shell, spine, burial chamber and the maze under them.

    python tools/generate_pyramid.py        (or through make_pieces.py)

Writes data/sydungeon/structure/pyramid/*.nbt and the template pools that join them.

WHY THIS IS GENERATED AND NOT BUILT BY HAND
A structure block saves at most 48 blocks a side. The shell slices are 91 and 77 wide, so
they cannot be saved in game at all. They also have to be exact: the whole point of the
design is that the silhouette is guaranteed, and a hand-built 91-wide slope would drift.

HOW THE SHAPE IS GUARANTEED
Vanilla jigsaw generation grows a tree and knows nothing about a silhouette, so left alone it
would carve rooms out through the slope. The guarantee comes from one rule in
JigsawPlacement: when a piece's jigsaw points at a position inside that same piece's own
bounding box, its children are tested against *that box* as their free space instead of the
global one. Bastions use this to fill a hall with rooms. We use it to fence the maze in:

    skin_base (91x7x91)  --inside--> core (63x7x63)  --inside--> spine, then the maze
    skin_mid  (77x21x77) --inside--> tomb (21x21x21)
    skin_top  (35x18x35) --inside--> crypt (7x7x7)

Every maze piece is a descendant of `core`, so every one of them is tested against core's box
and none can leave it. Core is inset two cells from the pyramid's edge, so the slope is never
touched. No blocker pieces and no voids to maintain: the box is the fence.

The three skins stack with aligned vertical jigsaws in one deterministic chain, so the
pyramid is always whole. Everything else - the entrance tunnel, the ladder shaft from the
well up into the tomb, the hatch from the tomb up into the crypt - is carved into both pieces
at matching coordinates, because two pieces joined by a single anchor jigsaw always land in
the same relative position. Deterministic geometry does not need a jigsaw.

WHAT IS LEFT SOLID
Layer one is a 9x9 grid of maze cells. Above it the middle of the pyramid is the burial
chamber and everything else is solid sandstone, which is what a pyramid is. Whatever the maze
does not reach is simply not excavated yet.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
import nbt  # noqa: E402
from generate_pieces import Piece  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DST = os.path.join(ROOT, 'src', 'main', 'resources', 'data', 'sydungeon', 'structure', 'pyramid')
POOL_JSON = os.path.join(ROOT, 'src', 'main', 'resources', 'data', 'sydungeon', 'worldgen',
                         'template_pool', 'pyramid')

NS = 'sydungeon'
DOOR = NS + ':pyr_door'          # the maze's connector
SPINE_DOOR = NS + ':pyr_spine'   # the spine's, so a spine piece is only entered its own way
ANCHOR = NS + ':pyr_anchor'      # skin -> core / tomb / crypt, and skin -> skin
EMPTY = 'minecraft:empty'

CELL = 7
BASE = 91                        # width at the ground course
APEX = (BASE - 1) // 2           # 45: solid where max(|dx|, |dz|) <= APEX - y
CX = CZ = APEX
PRIORITY = 20                    # skins, core, spine and tomb all go down before the maze

SANDSTONE = 'minecraft:sandstone'
CUT = 'minecraft:cut_sandstone'
CHISELED = 'minecraft:chiseled_sandstone'
SMOOTH = 'minecraft:smooth_sandstone'
SAND = 'minecraft:sand'
VOID = 'minecraft:structure_void'
AIR = 'minecraft:air'

# Where each piece sits in pyramid coordinates, and how big it is. Everything else is derived
# from this table, so the alignments that matter - the ladder shaft, the hatch, the entrance
# tunnel - stay true when a number here changes.
AT = {
    'skin_base': (0, 0, 0),
    'core': (14, 0, 14),
    'skin_mid': (7, 7, 7),
    'tomb': (35, 7, 35),
    'skin_top': (28, 28, 28),
    'crypt': (47, 28, 49),
}
SIZE = {
    'skin_base': (BASE, 7, BASE),
    'core': (63, 7, 63),
    'skin_mid': (77, 21, 77),
    'tomb': (21, 21, 21),
    'skin_top': (35, 18, 35),
    'crypt': (CELL, CELL, CELL),
}

# The maze grid inside `core`: 9x9 cells. The way in is the middle of the north edge and the
# spine runs straight to the well at the centre.
GATE_CELL = (4, 0)
WELL_CELL = (4, 4)
SPINE_STEPS = 3

# The shaft from the well up into the tomb, in pyramid coordinates: ONE column, in the middle
# of the well cell, with the ladder in it and the block behind it solid. Three wide was worse
# than it looked - you stepped into it and fell past the ladder (section 33).
SHAFT = (45, 45, 45, 45)
LADDER_X, LADDER_Z = 45, 45

# The hatch from the tomb up into the crypt, and the ladder up to it: the same, in the middle
# of the crypt.
HATCH = (50, 50, 52, 52)
CLIMB_X, CLIMB_Z = 50, 52

POOL = {k: NS + ':pyramid/' + k for k in (
    'passages', 'caps', 'well', 'core', 'tomb', 'crypt', 'skin_mid', 'skin_top',
    'spine_1', 'spine_2', 'spine_3')}


def solid(x, y, z):
    """Is this pyramid coordinate inside the silhouette?"""
    return max(abs(x - CX), abs(z - CZ)) <= APEX - y


# --------------------------------------------------------------------------- joins

def anchor_into(p, parent, child):
    """The jigsaw on `parent` that places `child` beside it, horizontally. Horizontal pins the
    rotation: the child's own anchor faces west, so only the identity rotation leaves it
    facing back at the parent."""
    ox, oy, oz = AT[parent]
    cx, cy, cz = AT[child]
    az = SIZE[child][2] // 2
    p.jigsaw(cx - 1 - ox, cy - oy, cz + az - oz, 'east_up', POOL[child], SANDSTONE,
             priority=PRIORITY, name=DOOR, target=ANCHOR)


def stack_onto(p, parent, child):
    """The jigsaw that sets the next skin slice on top of this one. Aligned, so the stack
    keeps whatever rotation the start piece was given."""
    ox, oy, oz = AT[parent]
    cx, cy, cz = AT[child]
    p.jigsaw(cx - ox, cy - 1 - oy, cz - oz, 'up_east', POOL[child], SANDSTONE,
             joint='aligned', priority=PRIORITY, name=DOOR, target=ANCHOR)


def side_anchor(p, child):
    """The matching anchor a horizontally placed child carries, on its west face."""
    p.jigsaw(0, 0, SIZE[child][2] // 2, 'west_up', EMPTY, SANDSTONE,
             name=ANCHOR, target=ANCHOR)


def under_anchor(p):
    """The matching anchor a stacked child carries, at its bottom corner."""
    p.jigsaw(0, 0, 0, 'down_east', EMPTY, SANDSTONE, joint='aligned',
             name=ANCHOR, target=ANCHOR)


# --------------------------------------------------------------------------- the shell

def entrance_cut(x, y, z):
    """The way in: a recess in the slope and a 3-wide passage through to the core."""
    if 44 <= x <= 46 and 1 <= y <= 4 and z < AT['core'][2]:
        return True
    return 42 <= x <= 48 and 1 <= y <= 6 and z <= 6


def skin(name, keep=None):
    """A horizontal slice of the pyramid: sandstone inside the silhouette, structure_void
    outside it so the desert keeps its dunes against the slope instead of being cut back to a
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
                # a course of cut sandstone every seventh layer: masonry you can read from
                # far off, for nothing
                p.set(lx, ly, lz, CUT if y % 7 == 6 else SANDSTONE)
    return p


def skin_base():
    p = skin('skin_base', keep=entrance_cut)
    anchor_into(p, 'skin_base', 'core')
    stack_onto(p, 'skin_base', 'skin_mid')
    return p


def skin_mid():
    p = skin('skin_mid')
    under_anchor(p)
    anchor_into(p, 'skin_mid', 'tomb')
    stack_onto(p, 'skin_mid', 'skin_top')
    return p


def skin_top():
    p = skin('skin_top')
    under_anchor(p)
    anchor_into(p, 'skin_top', 'crypt')
    return p


# --------------------------------------------------------------------------- the maze

DOOR_AT = {'west': (0, 0, 3, 'west_up'), 'east': (6, 0, 3, 'east_up'),
           'north': (3, 0, 0, 'north_up'), 'south': (3, 0, 6, 'south_up')}


def cell(doors, floor=SANDSTONE):
    """A 7x7x7 maze cell: solid sandstone with a 5x5 room cut out and a 3-wide, 4-high
    doorway on each named face. The same grid and doorway as the prison (CLAUDE.md section
    2), so one set of tools and checks covers both dungeons."""
    p = Piece(CELL, CELL, CELL, SANDSTONE)
    p.box(1, 1, 1, 5, 5, 5, AIR)
    p.box(0, 0, 0, 6, 0, 6, floor)
    for d in doors:
        x, _, z, _ = DOOR_AT[d]
        if d in ('west', 'east'):
            p.box(x, 1, 2, x, 4, 4, AIR)
        else:
            p.box(2, 1, z, 4, 4, z, AIR)
    return p


def door(p, side, pool, name=DOOR, target=DOOR, priority=0):
    x, y, z, orientation = DOOR_AT[side]
    p.jigsaw(x, y, z, orientation, pool, SANDSTONE, priority=priority, name=name, target=target)


def passage():
    p = cell(['west', 'east'])
    door(p, 'west', POOL['passages'])
    door(p, 'east', POOL['passages'])
    return p


def corner():
    p = cell(['west', 'south'])
    door(p, 'west', POOL['passages'])
    door(p, 'south', POOL['passages'])
    return p


def cross():
    p = cell(['west', 'east', 'north', 'south'])
    for side in ('west', 'east', 'north', 'south'):
        door(p, side, POOL['passages'])
    return p


def niche():
    """A burial niche: a chest on a plinth at the back of a dead end."""
    p = cell(['west'])
    door(p, 'west', POOL['passages'])
    p.box(4, 1, 2, 5, 1, 4, CUT)
    p.set(5, 2, 3, CHISELED)
    p.set(4, 2, 3, 'minecraft:chest', {'facing': 'west', 'type': 'single', 'waterlogged': 'false'},
          {'id': 'minecraft:chest', 'LootTable': NS + ':chests/pyramid_niche'})
    return p


def sand_den():
    """A cell the desert took back. The corridor is still open but the rest is packed sand,
    and a husk is waiting in the alcove behind it."""
    p = cell(['west', 'east'])
    door(p, 'west', POOL['passages'])
    door(p, 'east', POOL['passages'])
    p.box(1, 1, 1, 5, 5, 1, SAND)          # the north half, buried
    p.box(1, 3, 2, 5, 5, 4, SAND)          # sand drifted down from the ceiling
    p.box(1, 1, 5, 5, 3, 5, AIR)           # the alcove
    p.set(3, 1, 5, 'minecraft:spawner', None, husk_spawner())
    return p


def dig_site():
    """A drift of sand with things buried in it. Brushing suspicious sand is something only a
    player can do, which is the point: the two trigger traps that stood here before - a plate
    on TNT and sand hung over a tripwire - were set off by the wandering mobs long before
    anyone walked in, and the TNT one took a piece of the pyramid with it."""
    p = cell(['west', 'east'])
    door(p, 'west', POOL['passages'])
    door(p, 'east', POOL['passages'])
    p.box(1, 1, 1, 5, 2, 1, SAND)        # the drift against the north wall
    p.box(1, 1, 5, 5, 1, 5, SAND)        # and a lower one on the south side
    for x, y, z in ((2, 1, 1), (4, 2, 1), (2, 1, 5), (5, 1, 5)):
        p.set(x, y, z, 'minecraft:suspicious_sand', {'dusted': '0'},
              {'id': 'minecraft:brushable_block', 'LootTable': NS + ':archaeology/pyramid'})
    return p


def guard_post():
    """A crossroads with a husk on a plinth in the middle of it. The maze needs somewhere the
    mobs come from besides the dark."""
    p = cell(['west', 'east', 'north', 'south'])
    for side in ('west', 'east', 'north', 'south'):
        door(p, side, POOL['passages'])
    p.set(3, 1, 3, 'minecraft:spawner', None, husk_spawner())
    for x, z in ((2, 2), (2, 4), (4, 2), (4, 4)):
        p.set(x, 1, z, CHISELED)
    return p


def cap():
    """The plug every pool falls back to, one block thin so it fits wherever it is wanted."""
    p = Piece(1, CELL, CELL, SANDSTONE)
    p.jigsaw(0, 0, 3, 'west_up', POOL['caps'], SANDSTONE, name=DOOR, target=DOOR)
    return p


# --------------------------------------------------------------------------- spine and well

def spine(step):
    """A straight run of the way in, from the gate to the well. Its entry carries its own
    connector name so it can only be entered from the gate side: with one name the generator
    would come in through the continuation door half the time and the spine would wander off
    instead of reaching the centre."""
    p = cell(['north', 'south', 'west', 'east'])
    door(p, 'north', EMPTY, name=SPINE_DOOR, target=SPINE_DOOR)
    nxt = POOL['well'] if step == SPINE_STEPS else POOL['spine_%d' % (step + 1)]
    door(p, 'south', nxt, name=DOOR, target=SPINE_DOOR, priority=PRIORITY)
    door(p, 'west', POOL['passages'])
    door(p, 'east', POOL['passages'])
    return p


def well():
    """Where the spine ends: a shaft in the ceiling with a ladder, up into the tomb."""
    p = cell(['north', 'east', 'west', 'south'])
    door(p, 'north', EMPTY, name=SPINE_DOOR, target=SPINE_DOOR)
    for side in ('east', 'west', 'south'):
        door(p, side, POOL['passages'])
    ox = AT['core'][0] + WELL_CELL[0] * CELL
    oz = AT['core'][2] + WELL_CELL[1] * CELL
    x0, x1, z0, z1 = SHAFT
    p.box(LADDER_X - ox, 1, LADDER_Z - oz - 1,                # what the ladder hangs on
          LADDER_X - ox, 5, LADDER_Z - oz - 1, CUT)
    p.box(x0 - ox, 6, z0 - oz, x1 - ox, 6, z1 - oz, AIR)      # the hole in the ceiling
    for y in range(1, CELL):
        p.set(LADDER_X - ox, y, LADDER_Z - oz, 'minecraft:ladder',
              {'facing': 'south', 'waterlogged': 'false'})
    p.set(3, 5, 5, 'minecraft:lantern', {'hanging': 'true', 'waterlogged': 'false'})
    return p


def core():
    """The maze's block of stone: nine cells a side, solid, with the gate corridor cut into
    it and one jigsaw at the corridor's inner end to start the spine."""
    sx, sy, sz = SIZE['core']
    p = Piece(sx, sy, sz, SANDSTONE)
    side_anchor(p, 'core')
    gx, gz = GATE_CELL
    p.box(gx * CELL + 2, 1, gz * CELL, gx * CELL + 4, 4, gz * CELL + 6, AIR)
    p.jigsaw(gx * CELL + 3, 0, gz * CELL + 6, 'south_up', POOL['spine_1'], SANDSTONE,
             priority=PRIORITY, name=DOOR, target=SPINE_DOOR)
    return p


# --------------------------------------------------------------------------- tomb and crypt

TRIAL_COOLDOWN = 2_000_000_000
TRIAL_STATE = {'trial_spawner_state': 'inactive', 'ominous': 'false'}
ANY_LIGHT = {'block_light_limit': {'min_inclusive': nbt.Int(0), 'max_inclusive': nbt.Int(15)}}


def trial_spawner(config):
    return {
        'id': 'minecraft:trial_spawner',
        'normal_config': NS + ':pyramid/' + config,
        'ominous_config': NS + ':pyramid/' + config,
        'target_cooldown_length': nbt.Int(TRIAL_COOLDOWN),
        'required_player_range': nbt.Int(14),
    }


def husk_spawner():
    return {
        'id': 'minecraft:mob_spawner',
        'SpawnData': {'entity': {'id': 'minecraft:husk'}, 'custom_spawn_rules': ANY_LIGHT},
        'Delay': nbt.Short(20),
        'MinSpawnDelay': nbt.Short(200),
        'MaxSpawnDelay': nbt.Short(800),
        'SpawnCount': nbt.Short(3),
        'MaxNearbyEntities': nbt.Short(5),
        'RequiredPlayerRange': nbt.Short(14),
        'SpawnRange': nbt.Short(4),
    }


def tomb():
    """The burial hall: 21x21x21, the same as the prison's. You come up a ladder into the
    middle of the floor with the spawners already around you."""
    ox, oy, oz = AT['tomb']
    n = SIZE['tomb'][0]
    c = n // 2
    p = Piece(n, n, n, SANDSTONE)
    side_anchor(p, 'tomb')
    p.box(1, 1, 1, n - 2, n - 2, n - 2, AIR)
    for y in (7, 14):                                   # courses round the walls
        for i in range(n):
            for x, z in ((0, i), (n - 1, i), (i, 0), (i, n - 1)):
                p.set(x, y, z, CUT)
    for x0, z0 in ((2, 2), (2, n - 4), (n - 4, 2), (n - 4, n - 4)):
        p.box(x0, 1, z0, x0 + 1, n - 2, z0 + 1, CHISELED)
    for x in range(1, n - 1):
        for z in range(1, n - 1):
            if x % 3 == 1 and z % 3 == 1:
                p.set(x, 0, z, CUT)

    # the dais at the north end, the pharaoh on it, guards in the four quarters
    p.box(c - 3, 1, 3, c + 3, 1, 7, SMOOTH)
    p.box(c - 1, 2, 4, c + 1, 2, 6, CHISELED)
    p.set(c, 3, 5, 'minecraft:trial_spawner', TRIAL_STATE, trial_spawner('pharaoh'))
    for x, z in ((5, 5), (n - 6, 5), (5, n - 6), (n - 6, n - 6)):
        p.set(x, 1, z, 'minecraft:trial_spawner', TRIAL_STATE, trial_spawner('tomb_guards'))

    # the shaft you arrive by
    x0, x1, z0, z1 = SHAFT
    p.box(x0 - ox, 0, z0 - oz, x1 - ox, 0, z1 - oz, AIR)
    p.set(LADDER_X - ox, 0, LADDER_Z - oz, 'minecraft:ladder',
          {'facing': 'south', 'waterlogged': 'false'})

    # the climb to the crypt: the hatch first, then the ladder up to it, or the hatch would
    # cut the top rung off the ladder it is there to let you reach
    hx0, hx1, hz0, hz1 = HATCH
    p.box(hx0 - ox, n - 1, hz0 - oz, hx1 - ox, n - 1, hz1 - oz, AIR)
    for y in range(1, n):
        p.set(CLIMB_X - ox, y, CLIMB_Z - oz + 1, CHISELED)     # the post it hangs on: one
        p.set(CLIMB_X - ox, y, CLIMB_Z - oz, 'minecraft:ladder',   # column, so the wall it
              {'facing': 'north', 'waterlogged': 'false'})         # used to need is gone

    for x, z in ((c, 4), (4, c), (n - 5, c), (c, n - 5)):
        p.set(x, n - 5, z, 'minecraft:lantern', {'hanging': 'true', 'waterlogged': 'false'})
    return p


def crypt():
    """Above the burial hall's ceiling: the room the pyramid was built for."""
    ox, oy, oz = AT['crypt']
    p = Piece(CELL, CELL, CELL, SANDSTONE)
    side_anchor(p, 'crypt')
    p.box(1, 1, 1, 5, 5, 5, AIR)
    hx0, hx1, hz0, hz1 = HATCH
    p.box(hx0 - ox, 0, hz0 - oz, hx1 - ox, 0, hz1 - oz, AIR)
    for y in (0, 1):     # one rung through the floor and one to step off onto it
        p.set(CLIMB_X - ox, y, CLIMB_Z - oz + 1, SANDSTONE)    # the post, carried up from
        p.set(CLIMB_X - ox, y, CLIMB_Z - oz, 'minecraft:ladder',   # the tomb below
              {'facing': 'north', 'waterlogged': 'false'})
    p.box(1, 1, 1, 5, 1, 1, CHISELED)
    p.set(3, 2, 1, 'minecraft:chest', {'facing': 'south', 'type': 'single', 'waterlogged': 'false'},
          {'id': 'minecraft:chest', 'LootTable': NS + ':chests/pyramid_crypt'})
    p.set(3, 5, 3, 'minecraft:lantern', {'hanging': 'true', 'waterlogged': 'false'})
    return p


# --------------------------------------------------------------------------- pools

def element(location, weight):
    return ('    { "weight": %d, "element": { "element_type": "minecraft:single_pool_element",\n'
            '        "location": "%s:pyramid/%s", "projection": "rigid", '
            '"processors": "%s:pyramid_weathering" } }' % (weight, NS, location, NS))


def write_pool(name, elements, fallback=NS + ':pyramid/caps'):
    os.makedirs(POOL_JSON, exist_ok=True)
    text = '{\n  "fallback": "%s",\n  "elements": [\n%s\n  ]\n}\n' % (fallback, ',\n'.join(elements))
    with open(os.path.join(POOL_JSON, name + '.json'), 'w', encoding='utf-8', newline='\n') as f:
        f.write(text)


def verify(pieces):
    """Assemble the pyramid on paper and check the things that are invisible until you are
    standing in one: that the maze cannot reach the slope, that the two halves of each shaft
    line up, and that the skin actually closes.

    Every alignment in this file is derived from AT and SIZE, so a change to one number can
    silently move a ladder into a wall. These checks are cheap and they run on every build of
    the pieces."""
    problems = []

    # 1. Boxes nest the way the confinement argument needs them to.
    for child, parent in (('core', 'skin_base'), ('tomb', 'skin_mid'), ('crypt', 'skin_top')):
        for axis in range(3):
            lo = AT[child][axis] - AT[parent][axis]
            if lo < 0 or lo + SIZE[child][axis] > SIZE[parent][axis]:
                problems.append('%s is not inside %s on axis %d' % (child, parent, axis))

    # 2. The maze's fence. Core's whole box has to sit inside the silhouette with room to
    #    spare, or a maze piece at the edge would cut through the slope.
    margin = min((APEX - y) - max(abs(x - CX), abs(z - CZ))
                 for y in range(AT['core'][1], AT['core'][1] + SIZE['core'][1])
                 for x in (AT['core'][0], AT['core'][0] + SIZE['core'][0] - 1)
                 for z in (AT['core'][2], AT['core'][2] + SIZE['core'][2] - 1))
    if margin < CELL:
        problems.append('core comes within %d blocks of the slope; want at least one cell' % margin)

    # 3. The tomb and the crypt are inside the silhouette too, at their highest course.
    for name in ('tomb', 'crypt'):
        ox, oy, oz = AT[name]
        sx, sy, sz = SIZE[name]
        for x in (ox, ox + sx - 1):
            for z in (oz, oz + sz - 1):
                if not solid(x, oy + sy - 1, z):
                    problems.append('%s pokes out of the pyramid at its top corner' % name)

    # 4. The two halves of each shaft meet. The well's ceiling hole and the tomb's floor hole
    #    are cut from the same SHAFT constant, so what is checked here is that the ladders
    #    are in the hole and that each has something to hang on.
    well_o = (AT['core'][0] + WELL_CELL[0] * CELL, 0, AT['core'][2] + WELL_CELL[1] * CELL)
    x0, x1, z0, z1 = SHAFT
    if not (x0 <= LADDER_X <= x1 and z0 <= LADDER_Z <= z1):
        problems.append('the well ladder is not in the shaft')
    for axis, lo, hi in ((0, x0, x1), (2, z0, z1)):
        if not (well_o[axis] <= lo and hi < well_o[axis] + CELL):
            problems.append('the shaft is not inside the well cell on axis %d' % axis)
        if not (AT['tomb'][axis] <= lo and hi < AT['tomb'][axis] + SIZE['tomb'][axis]):
            problems.append('the shaft is not inside the tomb on axis %d' % axis)

    hx0, hx1, hz0, hz1 = HATCH
    if not (hx0 <= CLIMB_X <= hx1 and hz0 <= CLIMB_Z <= hz1):
        problems.append('the crypt ladder does not come up through the hatch')
    for axis, lo, hi in ((0, hx0, hx1), (2, hz0, hz1)):
        if not (AT['crypt'][axis] <= lo and hi < AT['crypt'][axis] + SIZE['crypt'][axis]):
            problems.append('the hatch is not under the crypt on axis %d' % axis)
        if not (AT['tomb'][axis] <= lo and hi < AT['tomb'][axis] + SIZE['tomb'][axis]):
            problems.append('the hatch is not inside the tomb on axis %d' % axis)

    # 5. The way in is continuous: the tunnel through the skin has to meet the gate corridor
    #    cut into the core, at the same height and the same columns.
    gx, gz = GATE_CELL
    gate_x = set(range(AT['core'][0] + gx * CELL + 2, AT['core'][0] + gx * CELL + 5))
    tunnel_x = {x for x in range(BASE) if entrance_cut(x, 2, AT['core'][2] - 1)}
    if not gate_x <= tunnel_x:
        problems.append('the entrance tunnel does not line up with the gate corridor')
    if AT['core'][2] + gz * CELL != AT['core'][2]:
        problems.append('the gate cell is not on the core edge the tunnel arrives at')

    # 6. Nothing writes outside its own piece.
    for name, piece in pieces.items():
        sx, sy, sz = piece.size
        for (x, y, z) in piece.grid:
            if not (0 <= x < sx and 0 <= y < sy and 0 <= z < sz):
                problems.append('%s writes a block outside itself at %s' % (name, (x, y, z)))
                break

    for line in problems:
        print('  PROBLEM  ' + line)
    if problems:
        raise SystemExit('the pyramid does not hold together')
    print('  checked: maze fenced %d blocks clear of the slope, shafts aligned, way in joined'
          % margin)


def main():
    os.makedirs(DST, exist_ok=True)
    pieces = {
        'skin_base': skin_base(), 'skin_mid': skin_mid(), 'skin_top': skin_top(),
        'core': core(), 'tomb': tomb(), 'crypt': crypt(), 'well': well(),
        'passage': passage(), 'corner': corner(), 'cross': cross(), 'niche': niche(),
        'sand_den': sand_den(), 'dig_site': dig_site(), 'guard_post': guard_post(),
        'cap': cap(),
    }
    for i in range(1, SPINE_STEPS + 1):
        pieces['spine_%d' % i] = spine(i)
    verify(pieces)
    for name, piece in sorted(pieces.items()):
        piece.write(os.path.join(DST, name + '.nbt'))
        print('  %-12s %s' % (name, list(piece.size)))

    write_pool('start', [element('skin_base', 1)], fallback=EMPTY)
    for one in ('skin_mid', 'skin_top', 'core', 'tomb', 'crypt', 'well'):
        write_pool(one, [element(one, 1)], fallback=EMPTY)
    for i in range(1, SPINE_STEPS + 1):
        write_pool('spine_%d' % i, [element('spine_%d' % i, 1)], fallback=EMPTY)
    # Weights, and what they buy. Expected new doors per piece is
    # (10 + 8 + 7*3 + 0 + 6 + 6*3 + 5) / 51 = 1.33, comfortably over one, so the maze still
    # fills the floor. A chest in 18% of cells and a spawner in 24% of them.
    write_pool('passages', [element('passage', 10), element('corner', 8), element('cross', 7),
                            element('niche', 9), element('sand_den', 6),
                            element('guard_post', 6), element('dig_site', 5)])
    write_pool('caps', [element('cap', 1)], fallback=EMPTY)
    print('  pools -> %s' % os.path.relpath(POOL_JSON, ROOT))


if __name__ == '__main__':
    main()
