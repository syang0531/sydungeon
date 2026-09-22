# -*- coding: utf-8 -*-
"""The small dungeons' prose. One machine, so one text, filled in per skin.

Imported by level_notes.py. The table it reads is generate_small.SKINS, so a skin added
there gets its document without anything being written twice.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from generate_small import SKINS  # noqa: E402

HEAD = {
    'well': '돌 테를 두른 우물. 기둥 둘과 들보, 그리고 내려간 쇠사슬.',
    'mound': '낮은 둔덕. 북쪽이 두 칸 높이로 뚫려 있고 그 안이 구멍이다.',
    'hut': '판자 오두막. 서쪽에 문, 안에 작업대와 상자, 바닥 가운데에 구멍.',
    'cairn': '돌무덤. 쌓아 올린 돌 사이가 북쪽으로 뚫려 있다.',
    None: '**지상에 아무것도 없다.** 바위 속에 놓인 방 하나가 시작이고, 거기서 미로가 자란다.',
}

PRINCIPLE = """
### 하나의 기계, 바이옴마다 껍질

작은 던전은 십 분이다 — 입구, 사다리, 사다리가 닿는 방, 짧은 미로, 상자 한둘. 그건 지하감옥의
숫자를 줄인 것이고, 열 번 따로 쓰면 같은 버그를 고칠 자리가 열 개가 된다. 그래서 모양은
`tools/generate_small.py`에 한 번만 쓰여 있고, `SKINS` 표가 **무엇으로 지었는지 · 어디 서는지 ·
무엇이 사는지**만 말한다. 이 문서도 그 표에서 나온다.

### 보스도 시그니처도 없다

§2.8이다. 여기에 트라이얼 스포너를 달면 "마법 부여 장비는 보스당 한 조각"(§2.4)이 무너진다 —
300블록마다 하나씩 나오는 던전이니까. `generate_small.py`의 검사기가 **트라이얼 스포너를
거부한다.** 주는 것은 파밍 없는 세계의 첫날 밤에 실제로 필요한 것이다: 침대, 횃불, 음식,
그리고 움직일 만큼의 철.

### 큰 던전과 같은 바이옴에, 같은 자리에는 안 선다

각 껍질은 그 바이옴을 가진 대규모 던전과 자리를 나눠 쓰되, structure_set에 **exclusion_zone**을
걸어 두어 그 세트 근처 6청크 안에는 서지 않는다 (동굴 둘은 나눠 쓸 상대가 없어 그냥 선다). 큰 것은 찾아가는 하루고, 이건 가는 길에
빠지는 구멍이다.

### 상자 방은 반드시 나온다

허브의 북문은 **단일 원소 풀**(`store`)을 부른다. 미로가 어떻게 자라든 상자 하나는 확정이다 —
보스를 거는 방법과 같고(§7), 여기서 보장되는 것이 상자라는 점만 다르다.

### 나머지는 다른 던전과 같은 규칙

바닥 켜는 y=0에 있고 기초를 달지 않는다 (§30). 수직통로는 한 칸이고 둘레 여덟은 막혀 있다
(§33). 껍데기는 지형의 돌에 띠를 넣은 것이고 벽돌은 안쪽에만 쓴다 (§5.2). `terrain_adaptation`은
`none`이라 주변 땅을 깎지 않는다 (§31) — 대신 `level_ground_drop` 8로 급한 자리를 피한다 (§34).
"""


def install(INTRO, NOTES):
    for skin in SKINS:
        key = skin['key']
        biomes = ' · '.join(b.split(':')[-1] for b in skin['biomes'])
        INTRO[key] = {
            'title': '# 레벨 설계 — %s' % skin['title'],

            'summary': ("""
**중소규모 던전**이다 (§2.8). %s 그 아래 21칸을 내려가면 짧은 미로와 상자 방이 있다.

보스도 시그니처도 없고, 한 판 십 분이다. 열 껍질이 같은 기계에서 나오며 이것은 그중 하나다.

바이옴: %s
""" % (HEAD[skin['head']], biomes)) if not skin.get('deep') else ("""
**중소규모 던전**이고, **지표 입구가 없다** (§2.8). %s

`project_start_to_heightmap`을 쓰지 않고 높이를 직접 준다 — y %d에서 %d 사이 어딘가의 바위
속에 방 하나가 놓이고, 거기서 미로가 자란다. 보스도 시그니처도 없고 한 판 십 분이다.

바이옴: %s
""" % (HEAD[None], skin['deep'][0], skin['deep'][1], biomes)),

            'principle': PRINCIPLE,

            'skeleton': """
입구와 수직통로, 사다리가 닿는 허브, 그리고 허브가 반드시 부르는 상자 방. 미로는 판마다 다르다.
""",

            'floors': ([('허브', 1)] if skin.get('deep')
                       else [('지표', 1), ('수직통로', -10), ('허브', -25)]),

            'order': (['hub', 'store', 'passage', 'corner', 'cross', 'den', 'nook', 'cap']
                      if skin.get('deep') else
                      ['head', 'shaft', 'hub', 'store',
                       'passage', 'corner', 'cross', 'den', 'nook', 'cap']),

            'outro': """
## 다듬을 곳

- **조각이 열 개뿐이다.** 같은 문 배치의 방을 더 만들어 풀에 넣으면 그만큼 다양해지고,
  **배선은 안 건드려도 된다** (§16)
- **입구가 네 종류뿐이다.** `head`는 우물·둔덕·오두막·돌무덤 넷이고 여덟 껍질이 그걸 나눠
  쓴다. 구조물 블록 한계(48) 안이므로 손으로 지어 되가져올 수 있다
- **심층 어둠에는 아직 없다.** 러시·종유석은 들어왔지만 심층 어둠은 비어 있다 — 바닐라
  고대 도시가 이미 그 자리에 있어서, 넣는다면 그것과 어떻게 나눌지부터 정해야 한다
- **산·해변·벚꽃숲·버섯섬에 중소규모가 없다.** 표에 줄을 더하면 되는 일이다 (§35)
""",
        }

        if skin.get('deep'):
            NOTES['%s/hub' % key] = """
시작 조각. 바위 속에 놓이는 방 하나고, 서·남·동문이 미로로, **북문이 상자 방**으로 간다 —
단일 원소 풀이라 반드시 나온다. 사다리도 입구도 없다.
"""
        else:
            NOTES['%s/head' % key] = """
시작 조각. %s 기초는 없다 — 바닥 켜가 곧 지형의 맨 윗 블록이다 (§30).
""" % HEAD[skin['head']]
            NOTES['%s/shaft' % key] = '수직통로 21칸. 지형의 돌에 띠, 가운데 한 칸이 사다리 (§33).'
            NOTES['%s/hub' % key] = """
사다리가 닿는 방. 서·남문이 미로로 가고 **북문이 상자 방**을 부른다 — 단일 원소 풀이라
반드시 나온다. 이 던전에서 불이 켜져 있는 곳은 여기뿐이다 (§6).
"""
        NOTES['%s/store' % key] = '상자 방. 상자·통·랜턴. 허브가 반드시 부르므로 언제나 있다.'
        NOTES['%s/passage' % key] = '미로의 기본 단위.'
        NOTES['%s/corner' % key] = '꺾이는 통로. 랜턴 하나.'
        NOTES['%s/cross' % key] = '네거리. 네 구석에 기둥.'
        NOTES['%s/den' % key] = '스포너 칸. %s가 나온다.' % skin['mob'].split(':')[-1]
        NOTES['%s/nook' % key] = '막다른 방. 상자 하나.'
        NOTES['%s/cap' % key] = '두께 1의 마개. 미로 풀의 fallback (§4).'
