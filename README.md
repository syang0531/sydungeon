# SY Dungeon

마인크래프트 자바 에디션 모드. **손으로 지은 조각을 직소가 이어 붙여, 매번 다른 던전을 만든다.**

Stan Yang의 모드 가족(`sy…`) 세 번째. [SY Alchemy](https://www.curseforge.com/minecraft/mc-mods/syalchemy)·[SY Village](https://www.curseforge.com/minecraft/mc-mods/syvillage)와 함께 플레이하는 것이 전제다.

## 무엇이 나오나

**지하감옥** (0.1.0) — 지표의 돌벽돌 정자에서 사다리로 내려가면 미로가 시작된다. 직선 통로·십자 교차로·계단이 7×7 격자로 이어지고, 통로 옆 철창 뒤 감방에는 상자가, 막다른 경비실에는 스포너가 있다. 던전마다 깊이가 다르고 벽은 금 가고 이끼 끼어 있다. 허브에서 뻗은 복도 하나는 두 배 큰 보스방으로 이어지고, 거기서 좀비말을 탄 간수장과 무장 경비를 잡으면 트라이얼 스포너가 마법 부여 다이아 장비를 뱉는다. `/locate structure sydungeon:dungeon`으로 찾는다.

계획: **대피라미드**(사막), **마법사의 성**(지표).

## 어떻게 만들어지나

조각은 크리에이티브에서 구조물 블록으로 저장한 `.nbt`, 이어 붙이는 규칙은 바닐라 worldgen JSON이다. Java는 바닐라 직소가 못 하는 일이 생길 때만 쓴다. 조각을 바꾸고 싶으면 코드가 아니라 월드에서 바꾼다 — [CLAUDE.md](CLAUDE.md)와 [docs/design.md](docs/design.md).

| 항목 | 값 |
|---|---|
| Minecraft | 26.2 (Java Edition) |
| 모드로더 | NeoForge 26.2.0.88 |
| Java | 25 |
| modid | `sydungeon` |
| 배포 | CurseForge — [PUBLISHING.md](PUBLISHING.md), 등록 정보는 [docs/curseforge/등록정보.md](docs/curseforge/등록정보.md) |

```bash
./gradlew build        # 빌드
./gradlew runClient    # 클라이언트 실행
```

모드 빌드 없이 보려면 데이터팩으로 묶어 26.2 월드에 넣는다:

```bash
python tools/pack_datapack.py "<월드 경로>"
```

그리고 게임에서 `/reload` 후 `/place jigsaw sydungeon:dungeon/start sydungeon:door 10 ~ ~ ~`.
