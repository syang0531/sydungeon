package com.syang.sydungeon;

import com.syang.sydungeon.registry.ModStructureTypes;
import net.neoforged.bus.api.IEventBus;
import net.neoforged.fml.ModContainer;
import net.neoforged.fml.common.Mod;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

/**
 * Entry point.
 *
 * <p>SyDungeon adds randomly assembled dungeons - a maze-like prison first, a pyramid and a
 * wizard's castle later - built from hand-made pieces that vanilla's jigsaw generation joins
 * together. The pieces are structure-block saves under {@code data/sydungeon/structure/}, and
 * the rules that join them are worldgen JSON beside them. Java is for what that JSON cannot
 * say: so far, a jigsaw structure whose depth is rolled per dungeon
 * ({@link com.syang.sydungeon.worldgen.RangedJigsawStructure}). The design lives in
 * {@code CLAUDE.md} and {@code docs/design.md}.
 */
@Mod(SyDungeon.MODID)
public class SyDungeon {

    public static final String MODID = "sydungeon";
    public static final Logger LOGGER = LoggerFactory.getLogger(MODID);

    public SyDungeon(IEventBus modBus, ModContainer container) {
        ModStructureTypes.register(modBus);
    }
}
