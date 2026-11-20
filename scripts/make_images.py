#!/usr/bin/env python3
"""파비콘·앱 아이콘·Notion 아이콘/커버·공유 이미지를 만듭니다. (Playwright 필요)

    python3 scripts/make_images.py
"""
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
ICONS = ROOT / "assets" / "icons"
NOTION = ROOT / "assets" / "notion"
SVG = (ICONS / "favicon.svg").read_text(encoding="utf-8")
# 사이트 바탕과 같은 갱지 질감
import urllib.parse
TEXTURE = "url(data:image/svg+xml," + urllib.parse.quote((ROOT / "assets" / "paper.svg").read_text(encoding="utf-8"), safe="") + ")"

PAPER, INK, MUTED, RULE, ACCENT = "#FAF8F3", "#1A1A1A", "#5A5650", "#C9C3B6", "#9E2A1E"
SERIF = '"Noto Serif CJK KR","Noto Serif KR",serif'
SANS = '"Noto Sans CJK KR","Noto Sans KR",sans-serif'


def icon_html(size: int, textured: bool = True) -> str:
    svg = SVG.replace('<svg ', f'<svg width="{size}" height="{size}" style="position:absolute;left:0;top:0" ', 1)
    if not textured:
        return f"<html><body style='margin:0;background:transparent'><div id='s' style='width:{size}px;height:{size}px'>{svg}</div></body></html>"
    # 종이 바탕(질감)을 깔고, 아이콘의 바탕 사각형은 투명하게 해서 질감이 보이게 함
    svg = svg.replace('fill="' + PAPER + '"', 'fill="none"', 1)
    r = size * 14 / 64
    inset = size * 1.5 / 64
    tile = max(200, size)  # 작은 아이콘에서도 결이 보이도록 타일을 줄임
    return (f"<html><body style='margin:0;background:transparent'><div id='s' style='position:relative;width:{size}px;height:{size}px'>"
            f"<div style=\"position:absolute;left:{inset}px;top:{inset}px;right:{inset}px;bottom:{inset}px;border-radius:{r}px;"
            f"background-color:{PAPER};background-image:{TEXTURE};background-size:{tile}px {tile}px\"></div>{svg}</div></body></html>")


def bars(n, x, y, w, gap=22, h=8, seed=0):
    """신문 본문처럼 보이는 회색 줄."""
    out = []
    for i in range(n):
        ww = w if (i + seed) % 5 != 4 else w * 0.62
        out.append(f"<div style='position:absolute;left:{x}px;top:{y + i * gap}px;width:{ww:.0f}px;height:{h}px;background:{INK};opacity:.13'></div>")
    return "".join(out)


def cover_html(w: int, h: int, notion: bool = False) -> str:
    """가운데 정렬 구도. Notion은 갤러리 카드에서 양옆, 페이지 커버에서 위아래를 자르므로
    제호·해·가로줄을 가운데 띠(세로 약 200~400px, 가로 약 300~1200px)에 모읍니다."""
    s = h / 600
    cx, cy = w / 2, h / 2
    title_px = 118 * s
    sun_r = 54 * s
    row_w = 760 * s
    base = cy + 40 * s          # 제호 아랫선 = 지평선
    left = cx - row_w / 2
    # 가장자리 장식용 신문 줄 (잘려도 무방)
    deco = ""
    for side_x in (60 * s, w - 60 * s - 170 * s):
        deco += bars(9, side_x, cy - 100 * s, 170 * s, gap=22 * s, h=7 * s, seed=int(side_x) % 5)
    return f"""<html><body style='margin:0'>
<div id='s' style='position:relative;width:{w}px;height:{h}px;overflow:hidden;background-color:{PAPER};background-image:{TEXTURE};background-size:800px 800px;font-family:{SANS};color:{INK}'>
  <div style='position:absolute;left:0;right:0;top:{40*s}px;border-top:{3*s}px solid {INK}'></div>
  <div style='position:absolute;left:0;right:0;top:{48*s}px;border-top:{1*s}px solid {INK}'></div>
  <div style='position:absolute;left:0;right:0;bottom:{48*s}px;border-top:{1*s}px solid {INK}'></div>
  <div style='position:absolute;left:0;right:0;bottom:{40*s}px;border-top:{3*s}px solid {INK}'></div>
  {deco}
  <div style='position:absolute;left:0;width:{w}px;top:{cy - 150*s}px;text-align:center;font-size:{18*s}px;letter-spacing:.32em;color:{MUTED}'>HR · AX · ECONOMY</div>
  <div style='position:absolute;left:{left}px;width:{row_w}px;top:{base - title_px*1.12}px;display:flex;align-items:flex-end;justify-content:center;gap:{30*s}px'>
    <div style='width:{sun_r*2}px;height:{sun_r}px;border-radius:{sun_r}px {sun_r}px 0 0;background:{ACCENT};flex:none;margin-bottom:{4*s}px'></div>
    <div style='font-family:{SERIF};font-weight:900;font-size:{title_px}px;line-height:1.1;letter-spacing:-.02em;white-space:nowrap'>아침 브리핑</div>
  </div>
  <div style='position:absolute;left:{left - 40*s}px;width:{row_w + 80*s}px;top:{base + 6*s}px;height:{6*s}px;background:{INK}'></div>
  <div style='position:absolute;left:{left - 40*s}px;width:{row_w + 80*s}px;top:{base + 18*s}px;height:{2*s}px;background:{INK}'></div>
  <div style='position:absolute;left:0;width:{w}px;top:{base + 44*s}px;text-align:center;font-family:{SERIF};font-size:{22*s}px;color:#3A3732'>일하는 사람을 위한 나만의 조간 · 매일 아침 9시 30분</div>
</div></body></html>"""


def shoot(page, html, out, w, h, transparent=False):
    page.set_viewport_size({"width": w, "height": h})
    page.set_content(html)
    page.wait_for_timeout(150)
    page.locator("#s").screenshot(path=str(out), omit_background=transparent)
    print("만듦:", out.relative_to(ROOT))


def main():
    NOTION.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as p:
        b = p.chromium.launch()
        pg = b.new_page()
        shoot(pg, icon_html(32, textured=False), ICONS / "favicon-32.png", 32, 32, transparent=True)  # 너무 작아 질감 생략
        for size, name in [(180, "apple-touch-icon.png"), (192, "icon-192.png"), (512, "icon-512.png")]:
            shoot(pg, icon_html(size), ICONS / name, size, size, transparent=True)
        shoot(pg, icon_html(512), NOTION / "notion-icon.png", 512, 512, transparent=True)
        shoot(pg, cover_html(1500, 600), NOTION / "notion-cover.png", 1500, 600)
        shoot(pg, cover_html(1200, 630), ICONS / "og-image.png", 1200, 630)
        b.close()


if __name__ == "__main__":
    main()
