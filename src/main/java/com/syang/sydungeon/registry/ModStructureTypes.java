package com.syang.sydungeon.registry;

import com.syang.sydungeon.SyDungeon;
import com.syang.sydungeon.worldgen.RangedJigsawStructure;
import net.minecraft.core.registries.Registries;
import net.minecraft.world.level.levelgen.structure.StructureType;
import net.neoforged.bus.api.IEventBus;
import net.neoforged.neoforge.registries.DeferredHolder;
import net.neoforged.neoforge.registries.DeferredRegister;

/** Structure types. One so far: a jigsaw whose depth is rolled per dungeon. */
public final class ModStructureTypes {

    public static final DeferredRegister<StructureType<?>> STRUCTURE_TYPES =
            DeferredRegister.create(Registries.STRUCTURE_TYPE, SyDungeon.MODID);

    /** {@code "type": "sydungeon:ranged_jigsaw"} in a worldgen/structure JSON. */
    public static final DeferredHolder<StructureType<?>, StructureType<RangedJigsawStructure>> RANGED_JIGSAW =
            STRUCTURE_TYPES.register("ranged_jigsaw", () -> () -> RangedJigsawStructure.CODEC);

    private ModStructureTypes() {}

    public static void register(IEventBus modBus) {
        STRUCTURE_TYPES.register(modBus);
    }
}
