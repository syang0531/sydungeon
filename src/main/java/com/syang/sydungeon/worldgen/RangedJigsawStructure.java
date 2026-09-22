package com.syang.sydungeon.worldgen;

import com.mojang.serialization.DataResult;
import com.mojang.serialization.MapCodec;
import com.mojang.serialization.codecs.RecordCodecBuilder;
import com.syang.sydungeon.registry.ModStructureTypes;
import java.util.List;
import java.util.Optional;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Holder;
import net.minecraft.resources.Identifier;
import net.minecraft.util.valueproviders.IntProvider;
import net.minecraft.util.valueproviders.IntProviders;
import net.minecraft.world.level.ChunkPos;
import net.minecraft.world.level.levelgen.Heightmap;
import net.minecraft.world.level.levelgen.WorldGenerationContext;
import net.minecraft.world.level.levelgen.heightproviders.HeightProvider;
import net.minecraft.world.level.levelgen.structure.Structure;
import net.minecraft.world.level.levelgen.structure.StructureType;
import net.minecraft.world.level.levelgen.structure.pools.DimensionPadding;
import net.minecraft.world.level.levelgen.structure.pools.JigsawPlacement;
import net.minecraft.world.level.levelgen.structure.pools.StructureTemplatePool;
import net.minecraft.world.level.levelgen.structure.pools.alias.PoolAliasBinding;
import net.minecraft.world.level.levelgen.structure.pools.alias.PoolAliasLookup;
import net.minecraft.world.level.levelgen.structure.structures.JigsawStructure;
import net.minecraft.world.level.levelgen.structure.templatesystem.LiquidSettings;

/**
 * Vanilla's jigsaw structure with one difference: {@code size} is an int provider, so the depth
 * of each dungeon is rolled when it is placed instead of being the same number for every one.
 *
 * <p>This is the first thing the data-only rule (CLAUDE.md §1) could not do. Vanilla's
 * {@code minecraft:jigsaw} takes a single integer, and a maze that is always the same depth
 * looks like the same maze. Everything else here is a copy of {@link JigsawStructure}: same
 * fields, same JSON, same call into {@link JigsawPlacement}. The depth limit is raised from
 * 20 to 32 because the surface shaft spends the first few levels of it before the maze starts.
 *
 * <p>And a second thing, added later: {@code level_ground}. A fortress forty-nine blocks
 * across landed on the lip of a cliff and stood there with its foundation over the drop
 * (2026-09-22). Terrain adaptation cannot save that - the beard reaches twelve blocks and the
 * cliff was deeper - and no arrangement of jigsaws can either, because a jigsaw structure
 * never looks at the ground. So this looks: it samples the heightmap round the middle and
 * gives the spot up if the ground is not level enough for what is about to stand on it. The
 * cost is rarity, which is why it is optional and why the number is generous.
 */
public final class RangedJigsawStructure extends Structure {

    public static final int MAX_DEPTH = 64;

    public static final MapCodec<RangedJigsawStructure> CODEC = RecordCodecBuilder.<RangedJigsawStructure>mapCodec(
            i -> i.group(
                    settingsCodec(i),
                    StructureTemplatePool.CODEC.fieldOf("start_pool").forGetter(s -> s.startPool),
                    Identifier.CODEC.optionalFieldOf("start_jigsaw_name").forGetter(s -> s.startJigsawName),
                    IntProviders.codec(0, MAX_DEPTH).fieldOf("size").forGetter(s -> s.size),
                    HeightProvider.CODEC.fieldOf("start_height").forGetter(s -> s.startHeight),
                    com.mojang.serialization.Codec.BOOL.fieldOf("use_expansion_hack").forGetter(s -> s.useExpansionHack),
                    Heightmap.Types.CODEC.optionalFieldOf("project_start_to_heightmap").forGetter(s -> s.projectStartToHeightmap),
                    JigsawStructure.MaxDistance.CODEC.fieldOf("max_distance_from_center").forGetter(s -> s.maxDistanceFromCenter),
                    com.mojang.serialization.Codec.list(PoolAliasBinding.CODEC).optionalFieldOf("pool_aliases", List.of()).forGetter(s -> s.poolAliases),
                    DimensionPadding.CODEC.optionalFieldOf("dimension_padding", JigsawStructure.DEFAULT_DIMENSION_PADDING).forGetter(s -> s.dimensionPadding),
                    LiquidSettings.CODEC.optionalFieldOf("liquid_settings", JigsawStructure.DEFAULT_LIQUID_SETTINGS).forGetter(s -> s.liquidSettings),
                    com.mojang.serialization.Codec.INT.optionalFieldOf("level_ground_drop").forGetter(s -> s.levelGroundDrop),
                    com.mojang.serialization.Codec.intRange(1, 64).optionalFieldOf("level_ground_radius", 16).forGetter(s -> s.levelGroundRadius)
                )
                .apply(i, RangedJigsawStructure::new)
        )
        .validate(RangedJigsawStructure::verifyRange);

    private final Holder<StructureTemplatePool> startPool;
    private final Optional<Identifier> startJigsawName;
    private final IntProvider size;
    private final HeightProvider startHeight;
    private final boolean useExpansionHack;
    private final Optional<Heightmap.Types> projectStartToHeightmap;
    private final JigsawStructure.MaxDistance maxDistanceFromCenter;
    private final List<PoolAliasBinding> poolAliases;
    private final DimensionPadding dimensionPadding;
    private final LiquidSettings liquidSettings;
    private final Optional<Integer> levelGroundDrop;
    private final int levelGroundRadius;

    public RangedJigsawStructure(
            Structure.StructureSettings settings,
            Holder<StructureTemplatePool> startPool,
            Optional<Identifier> startJigsawName,
            IntProvider size,
            HeightProvider startHeight,
            boolean useExpansionHack,
            Optional<Heightmap.Types> projectStartToHeightmap,
            JigsawStructure.MaxDistance maxDistanceFromCenter,
            List<PoolAliasBinding> poolAliases,
            DimensionPadding dimensionPadding,
            LiquidSettings liquidSettings,
            Optional<Integer> levelGroundDrop,
            int levelGroundRadius) {
        super(settings);
        this.startPool = startPool;
        this.startJigsawName = startJigsawName;
        this.size = size;
        this.startHeight = startHeight;
        this.useExpansionHack = useExpansionHack;
        this.projectStartToHeightmap = projectStartToHeightmap;
        this.maxDistanceFromCenter = maxDistanceFromCenter;
        this.poolAliases = poolAliases;
        this.dimensionPadding = dimensionPadding;
        this.liquidSettings = liquidSettings;
        this.levelGroundDrop = levelGroundDrop;
        this.levelGroundRadius = levelGroundRadius;
    }

    /**
     * How far the ground falls across the footprint: the highest sample minus the lowest, taken
     * at the middle, the four corners and the four sides of a square of {@code radius}.
     *
     * <p>Nine samples, not the whole footprint: this runs for every candidate position in the
     * world, and a cliff is not a thing you can miss by sampling coarsely.
     */
    private int groundDrop(Structure.GenerationContext context, BlockPos middle) {
        int low = Integer.MAX_VALUE;
        int high = Integer.MIN_VALUE;
        for (int dx = -1; dx <= 1; dx++) {
            for (int dz = -1; dz <= 1; dz++) {
                int y = context.chunkGenerator()
                        .getFirstFreeHeight(
                                middle.getX() + dx * this.levelGroundRadius,
                                middle.getZ() + dz * this.levelGroundRadius,
                                this.projectStartToHeightmap.orElse(Heightmap.Types.WORLD_SURFACE_WG),
                                context.heightAccessor(),
                                context.randomState());
                low = Math.min(low, y);
                high = Math.max(high, y);
            }
        }
        return high - low;
    }

    /** Same rule as vanilla: terrain adaptation needs 12 blocks of edge inside the 128 limit. */
    private static DataResult<RangedJigsawStructure> verifyRange(RangedJigsawStructure structure) {
        int edgeNeeded = switch (structure.terrainAdaptation()) {
            case NONE -> 0;
            case BURY, BEARD_THIN, BEARD_BOX, ENCAPSULATE -> 12;
        };
        return structure.maxDistanceFromCenter.horizontal() + edgeNeeded > JigsawStructure.MAX_TOTAL_STRUCTURE_RANGE
                ? DataResult.error(() -> "Horizontal structure size including terrain adaptation must not exceed 128")
                : DataResult.success(structure);
    }

    @Override
    public Optional<Structure.GenerationStub> findGenerationPoint(Structure.GenerationContext context) {
        ChunkPos chunkPos = context.chunkPos();
        int height = this.startHeight.sample(context.random(),
                new WorldGenerationContext(context.chunkGenerator(), context.heightAccessor()));
        BlockPos startPos = new BlockPos(chunkPos.getMinBlockX(), height, chunkPos.getMinBlockZ());
        if (this.levelGroundDrop.isPresent()
                && this.groundDrop(context, chunkPos.getMiddleBlockPosition(0)) > this.levelGroundDrop.get()) {
            return Optional.empty();       // a cliff edge, a ravine lip, the side of a peak
        }
        int depth = this.size.sample(context.random());
        return JigsawPlacement.addPieces(
                context,
                this.startPool,
                this.startJigsawName,
                depth,
                startPos,
                this.useExpansionHack,
                this.projectStartToHeightmap,
                this.maxDistanceFromCenter,
                PoolAliasLookup.create(this.poolAliases, startPos, context.seed()),
                this.dimensionPadding,
                this.liquidSettings);
    }

    @Override
    public StructureType<?> type() {
        return ModStructureTypes.RANGED_JIGSAW.get();
    }
}
