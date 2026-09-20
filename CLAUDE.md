# SY Dungeon

마인크래프트 자바 에디션 모드. **손으로 지은 조각을 직소가 이어 붙여, 매번 다른 던전을 만든다.**

Stan Yang의 모드 가족(`sy…`) 세 번째. 형제는 `C:\Projects\syalchemy`(금속·합금·마법 장비)와 `C:\Projects\syvillage`(스스로 자라는 마을)이고, 셋을 같이 플레이하는 것이 전제다.

**목적: 파밍과 채굴 없이, 탐험만으로 엔드 콘텐츠(엔더 드래곤·풀 마법 부여·네더라이트)에 닿는다.** 바이옴마다 던전 하나, 던전마다 확정 시그니처 보상 하나. 바닐라가 파밍·채굴로 주던 것을 던전 보상으로 옮긴다. 전체 설계는 `docs/concepts.md`. 지하감옥(0.1.0 배포)부터 만들었고, 대피라미드(설계 확정)와 마법사의 성이 뒤따른다. 보상 테이블에 다른 모드의 아이템은 넣지 않는다.

## 환경

| 항목 | 값 |
|---|---|
| Minecraft | 26.2 (Java Edition) |
| 모드로더 | NeoForge 26.2.0.88 |
| Java | 25 |
| modid | `sydungeon` |
| 패키지 루트 | `com.syang.sydungeon` |
| 빌드 | `./gradlew build` / 실행 `./gradlew runClient` |

> **가족 전체가 26.2다.** 연습 조각은 26.3 월드에서 저장됐고, 26.2와 26.3 사이에 구조물 NBT 팔레트 키가 바뀌었다 (`Name`/`Properties` → `id`/`properties`, DataVersion 4903 → 5023). `tools/convert_yame.py`가 키를 되돌려 26.2 파일로 쓴다. 블록 자체는 둘 다 같은 것들이라 그것으로 끝이다. **새 조각은 26.2 월드에서 저장하는 것이 맞다** — 그러면 변환이 필요 없다. NeoForge 26.3은 2026-09-20 기준 베타뿐이다.

## 불변 원칙

### 1. 모양은 월드에서, 규칙은 JSON에서, 코드는 그 둘이 못 하는 것만

던전의 모양을 정하는 것은 `data/sydungeon/structure/**/*.nbt`(크리에이티브에서 구조물 블록으로 저장)이고, 어떻게 이어지는지는 `data/sydungeon/worldgen/`의 template_pool · structure · structure_set · processor_list다. **Java는 바닐라 직소가 못 하는 일이 생길 때만 쓴다.** 지금까지 그런 일은 하나다: 바닐라 `minecraft:jigsaw`의 `size`는 정수 하나라 던전 깊이가 늘 같다. `sydungeon:ranged_jigsaw`(`worldgen/RangedJigsawStructure`)는 그 복사본에 `size`를 IntProvider로 바꾼 것이다. 그 외 Java는 없다. 조각을 바꾸고 싶으면 코드가 아니라 월드에서 바꾸고, `tools/dump_structure.py`로 확인한다.

**예외 하나:** 전리품 상자와 스포너는 `tools/decorate.py`가 NBT로 넣는다. 구조물 블록은 상자의 *아이템*을 저장하고 loot table을 저장하지 못하며, 스포너는 `/setblock`에 친 것이 그대로 들어가서 읽을 수 없다. 두 블록엔티티의 NBT는 한 파일에서 읽히는 편이 낫다.

이 원칙은 syvillage가 성문·초소를 규칙으로 짓다가 템플릿으로 갈아탄 데서 배운 것이다 (syvillage `CLAUDE.md` §13).

### 2. 조각은 7×7×7 격자 셀이다

- 조각의 크기는 7의 배수. 계단은 7×14×7로 두 층을 차지한다
- 출입구는 면 중앙에 **3폭 × 4높이** (x 또는 z = 2..4, y = 1..4)
- 직소는 **바닥층(y=0), 그 면의 가운데**. `final_state`는 `minecraft:stone_bricks`
- 공기를 **전부 저장**한다(7×7×7 = 343블록). `rigid`로 놓이면 지형을 파낸다. `structure_void`를 쓰면 안 속이 흙으로 남는다

격자가 정확해야 두 가지가 같은 셀로 수렴해도 충돌 판정이 깔끔하고, 뚫린 문이 이웃 조각의 돌벽에 막혀 "막아둔 문"처럼 보인다.

### 3. 커넥터 이름은 둘, 무엇이 붙을지는 풀이 정한다

미로의 직소는 전부 name = target = `sydungeon:door`. 어떤 조각이 붙을 수 있는지는 직소가 가리키는 **풀**(`passages` / `cells`)이 정한다. 이름을 나누면 얻는 것은 없고 caps 풀에 마개가 하나 더 필요해진다.

예외가 보스 가지다. 바닐라는 자식 조각의 **아무 직소나** 이름이 맞으면 입구로 쓴다. 십자형 `boss_passage`를 `door` 하나로 배선하면 절반은 "다음 보스 통로" 문으로 들어와 버려서 가지가 방을 잃는다. 그래서 보스 조각의 입구만 `sydungeon:boss_door`이고, 보스 가지를 잇는 직소는 target이 `boss_door`다. 그 문으로만 들어올 수 있다.

### 4. 모든 풀의 fallback은 `caps`다

직소 생성은 최대 깊이에 닿거나 옆 조각과 충돌하면 fallback 풀에서 고른다. fallback이 `minecraft:empty`면 출입구가 흙·돌·동굴로 뚫린 채 남는다. 바닐라 마을이 `terminators`를 fallback으로 두는 이유가 이것이다.

마개(`cap`)는 **1×7×7 벽 한 장**이다. 두께가 1이라 최대 깊이에서도 거의 항상 들어간다. 7칸 깊이의 막다른 방(`dead_end`)은 본 풀에 낮은 가중치로만 둔다 — fallback으로 쓰면 그것도 충돌해서 구멍이 남는다.

### 5. 시작은 지표, 미로는 그 아래

시작 조각 `entrance`는 `project_start_to_heightmap`으로 지표에 선다. 바닥 구멍의 아래 직소가 `shaft_first` 풀(shaft만)을 부르고, 그 아래로는 `shafts` 풀(shaft 3 : hub 2)이 이어지다가 `hub`(사다리가 닿는 방, 문 셋)에서 미로(`passages`)가 시작된다. `shaft_first`가 따로 있는 이유: shafts 풀만 쓰면 40%는 입구 바로 밑이 hub여서 미로가 지표와 같은 높이에 생겼다(월드 데이터로 확인, 2026-09-20). 사다리 기둥은 x 2..4, z 1..3으로 **가운데가 아니다** — 사다리가 z=1에서 북벽(z=0)에 걸려야 하고, 북벽은 사슬의 모든 조각에서 막혀 있어야 한다. 그래서 hub에는 북문이 없다. 수직 직소는 전부 `joint=aligned`라 기둥이 내려가는 내내 같은 쪽에 있다.

직소 깊이는 경로마다 센다. 수직통로 사슬이 2~3을 쓰고, 미로 가지는 각자 나머지를 쓴다. `size`가 13~23인 이유가 그것이다: 미로 깊이 10~20에 수직통로 값을 더한 것.

### 6. 던전은 어둡다. 스포너는 빛을 무시한다

랜턴은 `entrance`와 `boss_room`에만 있다. `decorate.py`가 나머지 조각의 랜턴을 전부 뺀다. 어두운 통로에서는 바닐라 자연 스폰이 일어나고, 그게 긴장감의 대부분이다(2026-09-20, 밝아서 긴장감이 없다는 피드백). 원래 조각마다 랜턴이 있었고, 몬스터 스포너는 스폰되는 몹의 규칙을 따르므로 밝은 통로에서는 아무것도 내지 않는다. `decorate.py`의 SpawnData에 `custom_spawn_rules.block_light_limit 0..15`가 들어 있는 이유다. 빼면 스포너는 장식이 된다. 트라이얼 스포너는 빛을 보지 않는다.

### 7. 보스는 던전마다 하나, 미로보다 먼저 놓인다

hub의 남문이 `boss_approach_1`을 부르고, 그 풀의 유일한 원소 `boss_passage_1`의 동문이 `boss_approach_2`를 부르는 식으로 `boss_approach_5`까지 이어진 뒤에야 `boss_approach`(boss_passage 2 : boss_room 1)가 온다. 직소의 풀은 조각에 박히므로 "최소 5개"를 강제하려면 같은 통로의 복사본이 5개 필요하다(`generate_pieces.boss_chain`이 조각과 풀 JSON을 함께 쓴다). 방은 hub에서 통로 5~8개 뒤, 직선으로 35칸 이상이다. `boss_room`은 21×21×21, 즉 3×3×3 셀이라 미로가 먼저 자라면 충돌해서 못 놓인다. 그래서 보스 가지의 직소는 `placement_priority`·`selection_priority` 10이고(나머지는 0), 바닐라는 우선순위가 높은 조각부터 놓는다. boss_passage의 북·남문은 `passages`를 가리키므로 보스 가지는 미로를 줄이지 않는다.

**클리어 판정과 보상은 트라이얼 스포너가 한다.** 상자는 싸우지 않고 열 수 있고, "다 죽였는지"를 판정하려면 Java가 필요하다. 트라이얼 스포너는 인원에 맞춰 웨이브를 내고 다 잡으면 `loot_tables_to_eject`를 싸운 플레이어마다 뱉는다. 스포너 설정은 `data/sydungeon/trial_spawner/dungeon/`(boss, guards), 블록엔티티 NBT는 그 id만 가리킨다. `target_cooldown_length`가 사실상 무한이라 던전당 한 번이다.

## 조각 목록 (0.1.0, `structure/dungeon/`)

| 조각 | 크기 | 직소 | 풀 | 비고 |
|---|---|---|---|---|
| `entrance` | 7×7×7 | 아래(shaft_first) | start | 지표. 지붕 있는 정자, 바닥에 사다리 구멍. 생성 |
| `shaft` | 7×21×7 | 위·아래(shafts) | shafts(3) | 사다리 세 칸. 생성 |
| `hub` | 7×7×7 | 위(shafts) + 서·동(passages) + 남(boss_approach_1, 우선순위 10) | shafts(2) | 사다리가 닿는 방. 북벽에 사다리, 북문 없음. 생성 |
| `boss_passage_1..5` | 7×7×7 | 서(`boss_door` 입구)·동(→boss_approach_k+1, 우선순위 10)·북·남(passages) | boss_approach_k(1) | cross에서 파생. 최소 길이 강제용 |
| `boss_passage` | 7×7×7 | 위와 같되 동문이 boss_approach | boss_approach(2) | cross에서 파생 |
| `boss_room` | 21×21×21 | 서(`boss_door` 입구, 면 정중앙) | boss_approach(1) | 단상 위 보스 트라이얼 스포너 1, 사분면마다 경비 스포너 4, 모서리 기둥, 벽 띠, 쇠사슬 랜턴 8. 생성 |
| `cross_guard` | 7×7×7 | 서·동·북·남 | passages(4) | cross 가운데에 몬스터 스포너 |
| `shaft_cap` | 7×1×7 | 위 | shaft_caps | 수직통로 바닥 마개. 생성 |
| `passage` | 7×7×7 | 서·동 | passages | 직선 통로 |
| `passage_cell` | 7×7×7 | 서·동 + 남(cells) | passages | 남쪽 벽이 철창, 그 뒤에 감방 |
| `passage_cells` | 7×7×7 | 서·동 + 북·남(cells) | passages | 양쪽 철창 |
| `cross` | 7×7×7 | 서·동·북·남 | passages | 십자 교차로 |
| `stair` | 7×14×7 | 서(y=0)·서(y=7) | passages(가중치 5) | 한 층 위로. 층 간격 7 유지. 어느 문으로 붙느냐가 무작위라 절반은 아래층으로 이어진다 |
| `dead_end` | 7×7×7 | 서 | passages(가중치 5) | 경비실. 가운데 스포너(좀비·스켈레톤·거미·동굴거미), 구석에 상자 `chests/dungeon_guard` |
| `cell` | 7×7×7 | 북 | cells | 북쪽 면 전체 개방 → 부모의 철창에 붙음. **문이 없다**: 철창을 깨야 들어간다. 안쪽 벽에 상자 `chests/dungeon_cell` |
| `cap` | 1×7×7 | 서 | caps | 벽 마개. 생성 |

"생성"은 `tools/generate_pieces.py`가 코드로 만든 조각이다. 출발점일 뿐이니 개발 클라이언트에서 열어 예쁘게 고치고 같은 이름으로 저장해 가져오면 된다. 살아남아야 하는 것은 직소의 위치·이름·풀이고, `import_piece.py`가 그걸 검사한다. 연습 조각 `st_gate`는 쓰지 않는다(입구가 그 자리를 대신한다).

풍화는 `processor_list/dungeon_weathering.json`이 모든 풀 원소에 걸려 있다: 돌벽돌의 18%가 금간 벽돌, 14%가 이끼 벽돌, 4%가 조약돌, 철창의 8%가 사라진다. 조각은 그대로고 매번 다르게 보인다.

## 원본과 도구

원본 연습 조각은 월드 `C:\Users\syang\AppData\Roaming\.minecraft\saves\던전`의 `generated/yame/structure/`에 있고, **그 월드는 건드리지 않는다.** 읽기 전용 스냅샷이 `tools/orig_yame/`에 있다.

| 도구 | 하는 일 |
|---|---|
| `tools/nbt.py` | 의존성 없는 NBT 읽기/쓰기. 원본을 바이트 단위로 되살린다 |
| `tools/make_pieces.py` | 아래 셋을 순서대로. **조각을 다시 만들 때는 이것 하나만 돈다** |
| `tools/convert_yame.py` | 스냅샷 → `structure/dungeon/*.nbt` (이름 변경, 직소 name/target/pool 치환, 26.3→26.2 팔레트 내림) |
| `tools/generate_pieces.py` | cap · shaft_cap · entrance · shaft · hub · boss_room을 코드로 생성, boss_passage는 cross에서 파생 |
| `tools/simulate.py` | 풀 가중치로 던전 크기·계단 수·층 수 분포를 종이 위에서 굴려 본다 |
| `tools/inspect_world.py` | 개발 월드 region 파일에서 실제 생성된 던전의 조각·층 분포를 읽는다 |
| `tools/gen_logo.py` | CurseForge 로고 (`docs/curseforge/logo.png`, `src/main/resources/logo.png`) |
| `tools/decorate.py` | cell과 dead_end에 상자·스포너 NBT 삽입 |
| `tools/dump_structure.py` | 조각을 층별 텍스트로 출력 + 직소 목록. 26.2/26.3 팔레트 둘 다 읽음 |
| `tools/pack_datapack.py` | `data/`를 바닐라 데이터팩 zip으로 묶음. 모드 빌드 없이 26.2 월드에서 `/place`로 확인 |
| `tools/import_piece.py` | 개발 클라이언트(`run/saves/*/generated/sydungeon/structure/`)에서 저장한 조각을 모드로 복사하고 직소·격자 규약을 검사 |

## 조각 만들기 (개발 클라이언트)

`./gradlew runClient`로 뜨는 게임이 곧 26.2 + 이 모드다. 조각은 거기서 만든다.

1. 크리에이티브 월드에서 7×7×7 셀 규약대로 짓는다 (§2)
2. 구조물 블록 SAVE, 이름 `sydungeon:dungeon/<이름>` → `run/saves/<월드>/generated/sydungeon/structure/dungeon/<이름>.nbt`
3. `python tools/import_piece.py` 로 목록 확인, `python tools/import_piece.py dungeon/<이름>` 으로 가져온다. 직소 이름·풀·격자 위치를 검사해 어긋난 것을 말해 준다
4. 풀 JSON에 원소를 추가한다 — 도구가 해 주지 않는다
5. 게임에서 `/reload` 하면 데이터팩 부분(풀·구조물 JSON)은 다시 읽지만 **jar 안의 조각은 재시작**해야 바뀐다. 개발 중에는 저장한 조각이 `generated/`에 있는 한 월드가 그것을 먼저 읽으므로, 그 월드 안에서는 `/place jigsaw`로 바로 볼 수 있다

## 생성 결과 읽기

"단층만 생겼다"처럼 눈으로 본 것과 통계가 다를 수 있다. `tools/inspect_world.py <월드>`가 개발 월드의 region 파일에서 던전 시작점을 찾아 조각 수·조각별 개수·층별 분포를 출력한다. 던전 하나에 조각 300~1000개, 계단 15~50개, 층 5~8개가 정상이다. 조각 대부분은 hub 층에 몰린다.

## 테스트

```
python tools/pack_datapack.py <월드 경로>     # 바닐라 월드용. 개발 클라이언트에는 필요 없다
/reload
/place jigsaw sydungeon:dungeon/start sydungeon:door 10 ~ ~ ~     # 시작 풀에서 깊이 10
/place structure sydungeon:dungeon                                # structure JSON 그대로
/locate structure sydungeon:dungeon
```

## 코드 규약

- 식별자·주석·커밋 메시지는 영어. 설계 문서는 한국어
- 밸런스 숫자는 JSON(풀 가중치, structure_set 간격)에 있다. Java로 옮기지 않는다
- 로깅은 `SyDungeon.LOGGER`

## 다음

`docs/concepts.md` §9의 순서. 0.1.0은 CurseForge에 배포됐다(프로젝트 1703811). 다음은 **감옥 마무리(바이옴 축소, 상자에 침대·횃불·고기) → 대피라미드 → 마법사의 성 → 마녀의 늪**.
