# 📰 아침 브리핑 (Morning-News-Paper)

매일 아침 자동으로 쌓이는 세 가지 브리핑을 **한 장의 신문**으로 엮어 보는 정적 웹앱입니다.

| 섹션 | 원본 레포 | 원본 경로 |
|---|---|---|
| HR | [dhcoaud98/HR](https://github.com/dhcoaud98/HR) | `briefings/YYYY/MM/YYYY-MM-DD.md` |
| AX · AI · 기업교육 | [dhcoaud98/AI-AX](https://github.com/dhcoaud98/AI-AX) | `briefings/YYYY/MM/YYYY-MM-DD.md` |
| 경제 | [dhcoaud98/economy](https://github.com/dhcoaud98/economy) | `briefings/YYYY/MM/YYYY-MM-DD.md` |

어느 날짜에 특정 레포의 브리핑이 없으면, 그 섹션은 빼고 그날 신문을 발행합니다.

## 화면

- **메인** (`/`) — 최신호 요약, 달력, 지난 신문 전체 목록, 키워드 검색과 섹션 필터
- **신문 한 호** (`#issue-2026-11-20`) — 1면 톱기사 · 오늘의 한 줄 · 숫자 한눈에 · 볼 만한 것, 이어서 섹션별 전체 기사
- `#today` — 최신호로 바로 이동

## 구조

```
Morning-News-Paper/
├─ index.html                 # 웹앱 진입점
├─ assets/style.css           # 신문 디자인
├─ assets/app.js              # 데이터 로딩 · 화면 그리기
├─ scripts/build.py           # 마크다운 브리핑 → 신문 JSON 변환기 (표준 라이브러리만 사용)
├─ issues/
│  ├─ index.json              # 발행 목록 (메인 화면·검색용)
│  └─ YYYY/MM/YYYY-MM-DD.json # 각 호
└─ .github/workflows/daily.yml  # 매일 자동 발행
```

## 매일 자동 발행

`.github/workflows/daily.yml`이 매일 **한국 시간 10:20, 12:20**에 돌면서

1. 세 레포의 `briefings/`를 가져와
2. `scripts/build.py`로 날짜별 신문을 다시 만들고
3. 바뀐 것이 있으면 `issues/`를 커밋합니다.

Actions 탭에서 **Run workflow**로 언제든 수동 실행할 수 있습니다.
원본 레포에서 브리핑을 올린 직후 바로 발행하고 싶다면, 원본 레포의 작업 끝에 `repository_dispatch`(`briefing-updated`)를 보내면 됩니다.

## 웹으로 열기 (GitHub Pages)

Settings → Pages → **Deploy from a branch** → `main` / `(root)` 를 고르면
`https://dhcoaud98.github.io/Morning-News-Paper/` 에서 열립니다.

## 로컬에서 보기

```bash
# 원본 레포 세 개를 옆 폴더에 받아 두었다면
python3 scripts/build.py --hr ../HR --ax ../AI-AX --econ ../economy
python3 -m http.server 8000   # http://localhost:8000
```

JSON을 `fetch`로 읽으므로 파일을 더블클릭하지 말고 로컬 서버로 여세요.

## 브리핑 형식이 바뀌면

변환기는 원본 마크다운의 다음 규칙을 읽습니다.

- `**오늘의 한 줄:**` → 섹션 요약
- `## 분류` → 기사 묶음, `### 1. 제목 (날짜)` → 기사
- `- **→ 나에게 의미:**` / `- **연결고리 → …:**` → 강조 상자, 그 밖의 `- **라벨:**` → 참고 메모, `- 출처:` → 출처 링크
- 경제 브리핑의 `오늘의 용어` · `숫자 한눈에 보기`(표) · `오늘의 읽을거리` · `오늘 생각해볼 질문`

형식이 크게 바뀌어 기사를 하나도 읽지 못하면 변환기가 경고를 출력합니다.
