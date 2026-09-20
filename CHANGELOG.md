# Changelog

## 0.1.0 (unreleased)

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
