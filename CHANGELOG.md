# Changelog

## 0.1.1 (2026-09-20)

지하감옥 마무리. 모드의 목적이 "파밍과 채굴 없이 탐험만으로 엔드 콘텐츠"라는 것을 `docs/concepts.md`에 세우고, 첫 던전이 그 약속의 첫 단추를 채우도록 고쳤다.

- **생성 바이옴을 육지 전체에서 온대·냉대 숲과 평원 13종으로 축소.** 바이옴 하나에 던전 하나가 원칙이다 (`docs/concepts.md` §2.7). 어두운숲·창백한 정원은 저주받은 묘지, 눈 타이가·그로브는 얼음 성채 몫으로 넘겼다
- **상자에 침대·횃불·식량 추가.** 두 테이블 모두 풀이 둘이 되어 첫 풀이 생존 물자 하나를 확정으로 준다. 감방 = 횃불·빵·구운 돼지고기·석탄·침대·양초, 경비실 = 횃불·구운 소고기·구운 양고기·침대·랜턴. 경비실 둘째 풀에 석탄·황금 당근도 넣었다
- **`tools/validate_data.py`**: 데이터팩의 모든 id를 게임 jar와 대조하고 조각·풀·전리품·스포너의 상호 참조를 검사한다. 0.1.0에서 `minecraft:chain`(26.2에서는 `iron_chain`)이 감방 전리품 테이블 전체를 로드 실패시켜 상자가 비어 있었고, `minecraft:dappled_forest`(26.3 전용)가 월드 로딩을 막았다. 둘 다 빌드는 통과했었다
- 바이옴별 던전 16종과 T0~T5 보상 설계를 `docs/concepts.md`에 문서화

## 0.1.0 (2026-09-20)

- 지하감옥 조각 12개 (`structure/dungeon/`): entrance, shaft, hub, shaft_cap, passage, passage_cell, passage_cells, cross, stair, dead_end, cell, cap
- 풀 6개 (start / shafts / shaft_caps / passages / cells / caps), 모든 풀의 fallback은 1칸 마개
- `sydungeon:dungeon` 구조물: 지표 입구에서 사다리로 내려가는 미로. 깊이 13~23 랜덤(`sydungeon:ranged_jigsaw`), beard_thin, 육지 바이옴
- 전리품 상자 2종(`chests/dungeon_cell`, `chests/dungeon_guard`), dead_end 스포너(빛 무시)
- 풍화 processor `dungeon_weathering`: 금간·이끼 벽돌, 조약돌, 빠진 창살
- 보스방: hub 남문에서 보스 통로 최소 5개 뒤에 21×21×21 방. 트라이얼 스포너 다섯(좀비말 탄 간수장 + 사분면 경비 웨이브), 클리어 시 플레이어마다 마법 부여 다이아 장비 지급(`trial/boss_reward`)
- 입구와 보스방 외의 랜턴 제거. 교차로 스포너 조각 `cross_guard`, 경비실 가중치 5
- CurseForge 등록 정보(`docs/curseforge/`), 로고, `PUBLISHING.md`
- Minecraft 26.2 / NeoForge 26.2.0.88 — 가족(syalchemy, syvillage)과 같은 스택. 26.3 월드에서 저장한 연습 조각은 변환기가 26.2 형식으로 내림
- 도구: `tools/nbt.py`, `convert_yame.py`, `dump_structure.py`, `pack_datapack.py`
