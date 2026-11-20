#!/usr/bin/env python3
"""HR · AI-AX · economy 레포의 일일 브리핑(마크다운)을 날짜별 신문 JSON으로 변환합니다.

사용법:
    python3 scripts/build.py --hr ../HR --ax ../AI-AX --econ ../economy

각 레포의 briefings/YYYY/MM/YYYY-MM-DD.md 를 읽어
issues/YYYY/MM/YYYY-MM-DD.json 과 issues/index.json 을 만듭니다.
어느 날짜에 특정 레포의 브리핑이 없으면 그 섹션은 빼고 발행합니다.
표준 라이브러리만 씁니다.
"""
import argparse
import datetime as dt
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

SECTIONS = [
    # key, 인자 이름, 표시 이름, GitHub 레포
    ("hr", "hr", "HR", "dhcoaud98/HR"),
    ("ax", "ax", "AX · AI · 기업교육", "dhcoaud98/AI-AX"),
    ("econ", "econ", "경제", "dhcoaud98/economy"),
]
WEEK = "월화수목금토일"
DATE_RE = re.compile(r"(\d{4}-\d{2}-\d{2})\.md$")
LINK_RE = re.compile(r"\[((?:[^\[\]]|\[[^\]]*\])+)\]\((https?://[^\s)]+(?:\([^\s)]*\)[^\s)]*)*)\)")
# 줄 맨 앞의 이모지·기호 제거 (📈 HR 트렌드 → HR 트렌드)
LEAD_SYMBOLS_RE = re.compile(r"^[^\w\[\(\"'‘“가-힣]+", re.UNICODE)
NUM_PREFIX_RE = re.compile(r"^(?:\d+[.)]\s*|[①②③④⑤⑥⑦⑧⑨⑩]\s*)")
TRAIL_PAREN_RE = re.compile(r"\s*\(([^()]*(?:\([^()]*\)[^()]*)*)\)\s*$")


def strip_symbols(s: str) -> str:
    s = s.replace("\u2139", "").replace("\ufe0f", "")
    return LEAD_SYMBOLS_RE.sub("", s).strip()


def strip_bold(s: str) -> str:
    return s.replace("**", "").strip()


def links(s: str):
    return [{"title": t.strip(), "url": u.strip()} for t, u in LINK_RE.findall(s) if u.startswith("http")]


def parse_bullet(text: str):
    """'- **라벨:** 내용' → (라벨, 내용). 라벨이 없으면 ('', 내용)."""
    m = re.match(r"^\*\*([^*]+?)\*\*\s*(.*)$", text)
    if m and m.group(1).rstrip().endswith(":"):
        return strip_symbols(m.group(1).rstrip()[:-1]), m.group(2).strip()
    m = re.match(r"^\*\*([^*]+?):\*\*\s*(.*)$", text)
    if m:
        return strip_symbols(m.group(1)), m.group(2).strip()
    return "", text.strip()


def new_article(heading: str):
    h = strip_symbols(heading)
    h = NUM_PREFIX_RE.sub("", h).strip()
    when = ""
    m = TRAIL_PAREN_RE.search(h)
    # 끝 괄호가 날짜·보도 시점일 때만 떼어 냄
    if m and re.search(r"\d|월|일|주간|보도|발표|시간", m.group(1)):
        when = m.group(1).strip()
        h = h[: m.start()].strip()
    return {"title": h, "when": when, "body": [], "meaning": None, "notes": [], "sources": []}


def classify(heading: str) -> str:
    if "용어" in heading:
        return "terms"
    if "숫자" in heading:
        return "numbers"
    if "볼 만한" in heading or "읽을거리" in heading:
        return "picks"
    if "질문" in heading:
        return "question"
    return "news"


def parse_briefing(text: str) -> dict:
    lines = text.splitlines()
    out = {"title": "", "oneLine": "", "categories": [], "terms": [], "numbers": [],
           "nextCheck": "", "picks": [], "question": None}
    block = None          # 현재 '## ' 블록 종류
    cat = None            # 현재 뉴스 카테고리
    art = None            # 현재 기사
    term = None
    in_details = False
    q_lines, a_lines = [], []

    for raw in lines:
        line = raw.rstrip()
        s = line.strip()
        if not s or s == "---":
            continue
        if s.startswith("# ") and not out["title"]:
            out["title"] = strip_symbols(s[2:])
            continue
        if s.startswith("**오늘의 한 줄:**"):
            out["oneLine"] = s.split("**", 2)[2].strip()
            continue
        if s.startswith("## "):
            heading = re.sub(r"^\d+\)\s*", "", strip_symbols(s[3:]))
            block = classify(heading)
            art = term = None
            if block == "news":
                name = heading.replace("오늘의 ", "")
                cat = {"name": name, "articles": []}
                out["categories"].append(cat)
            continue
        if block is None:
            continue  # 머리말의 용어 링크 등

        if block == "news":
            if s.startswith("### "):
                art = new_article(s[4:])
                cat["articles"].append(art)
                continue
            if art is None:
                continue
            if s.startswith("- "):
                body = s[2:].strip()
                if body.startswith("출처:") or body.startswith("**출처:**"):
                    art["sources"].extend(links(body))
                    continue
                label, val = parse_bullet(body)
                if "나에게 의미" in label or label.startswith("연결고리"):
                    art["meaning"] = {"label": label.replace("→", "").strip() if "나에게" in label else label, "text": val}
                else:
                    art["notes"].append({"label": label, "text": val})
                continue
            if s.startswith(">"):
                continue
            art["body"].append(s)

        elif block == "terms":
            if s.startswith("### "):
                term = {"name": NUM_PREFIX_RE.sub("", strip_symbols(s[4:])), "items": []}
                out["terms"].append(term)
            elif term and s.startswith("- "):
                label, val = parse_bullet(s[2:])
                term["items"].append({"label": label, "text": val})

        elif block == "numbers":
            if s.startswith("|"):
                cells = [c.strip() for c in s.strip("|").split("|")]
                if len(cells) >= 2 and not set("".join(cells)) <= set("-: ") and cells[0] != "지표":
                    out["numbers"].append({"name": strip_bold(cells[0]), "value": strip_bold(cells[1]),
                                           "basis": cells[2] if len(cells) > 2 else ""})
            elif "다음 주 체크" in s:
                out["nextCheck"] = re.sub(r"^.*?다음 주 체크:\*\*\s*", "", s)

        elif block == "picks":
            if s.startswith("- "):
                body = s[2:].strip()
                ls = links(body)
                m = re.match(r"^\*\*(.+?)\*\*", body)
                if m:
                    title = strip_bold(m.group(1)).rstrip(":").strip()
                    if len(title) <= 6:  # '책', '무료 자료' 같은 짧은 분류명이면 내용을 붙임
                        rest = LINK_RE.sub(lambda x: x.group(1), body[m.end():]).strip(" :")
                        title = f"{title} · {ls[0]['title'] if ls else rest.split('.')[0][:50]}"
                else:
                    title = ls[0]["title"] if ls else body[:60]
                out["picks"].append({"title": title, "url": ls[0]["url"] if ls else "", "text": body})

        elif block == "question":
            if s.startswith("<details"):
                in_details = True
                continue
            if s.startswith("</details"):
                in_details = False
                continue
            if in_details:
                if not s.startswith("<summary"):
                    a_lines.append(s)
            elif s.startswith(">") and "이 브리핑은" not in s:
                q_lines.append(s.lstrip("> ").strip())

    if q_lines:
        out["question"] = {"q": " ".join(q_lines), "a": a_lines}
    # 기사가 하나도 없는 카테고리 제거
    out["categories"] = [c for c in out["categories"] if c["articles"]]
    return out


def collect(repo: Path):
    found = {}
    if not repo or not (repo / "briefings").is_dir():
        return found
    for p in (repo / "briefings").rglob("*.md"):
        m = DATE_RE.search(p.name)
        if m:
            found[m.group(1)] = p
    return found


def main():
    ap = argparse.ArgumentParser()
    for _, arg, name, _ in SECTIONS:
        ap.add_argument(f"--{arg}", type=Path, help=f"{name} 레포 경로")
    ap.add_argument("--out", type=Path, default=ROOT / "issues")
    a = ap.parse_args()

    sources = {key: collect(getattr(a, arg)) for key, arg, _, _ in SECTIONS}
    dates = sorted(set().union(*[set(v) for v in sources.values()]))
    if not dates:
        print("브리핑을 찾지 못했습니다.", file=sys.stderr)
        sys.exit(1)

    index = []
    warnings = 0
    for no, date in enumerate(dates, start=1):
        d = dt.date.fromisoformat(date)
        issue = {"date": date, "weekday": WEEK[d.weekday()], "issueNo": no, "sections": {}}
        for key, _, name, gh in SECTIONS:
            p = sources[key].get(date)
            if not p:
                continue
            parsed = parse_briefing(p.read_text(encoding="utf-8"))
            rel = p.relative_to(getattr(a, [s[1] for s in SECTIONS if s[0] == key][0]))
            parsed["sourceUrl"] = f"https://github.com/{gh}/blob/HEAD/{rel.as_posix()}"
            n = sum(len(c["articles"]) for c in parsed["categories"])
            if n == 0 and not parsed["terms"]:
                print(f"  경고: {date} {name} — 기사를 읽지 못했습니다", file=sys.stderr)
                warnings += 1
            issue["sections"][key] = parsed

        out_path = a.out / date[:4] / date[5:7] / f"{date}.json"
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(issue, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")

        secs = issue["sections"]
        lead = next((secs[k]["categories"][0]["articles"][0]["title"]
                     for k, *_ in SECTIONS if k in secs and secs[k]["categories"]), "")
        index.append({
            "date": date, "weekday": issue["weekday"], "issueNo": no, "lead": lead,
            "sections": [k for k, *_ in SECTIONS if k in secs],
            "oneLines": {k: secs[k]["oneLine"] for k in secs},
            "titles": {k: [ar["title"] for c in secs[k]["categories"] for ar in c["articles"]] for k in secs},
        })

    index.sort(key=lambda e: e["date"], reverse=True)
    idx_path = a.out / "index.json"
    updated = dt.datetime.now(dt.timezone(dt.timedelta(hours=9))).strftime("%Y-%m-%d %H:%M")
    if idx_path.exists():  # 내용이 그대로면 갱신 시각도 그대로 둠 (빈 커밋 방지)
        try:
            old = json.loads(idx_path.read_text(encoding="utf-8"))
            if old.get("issues") == index:
                updated = old.get("updated", updated)
        except ValueError:
            pass
    meta = {"title": "아침 브리핑", "tagline": "일하는 사람을 위한 나만의 조간 — 인사 · AI 전환과 기업교육 · 경제",
            "updated": updated, "issues": index}
    idx_path.write_text(json.dumps(meta, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"{len(dates)}개 호 발행 ({dates[0]} ~ {dates[-1]}), 경고 {warnings}건")


if __name__ == "__main__":
    main()
