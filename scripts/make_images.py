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

PAPER, INK, MUTED, RULE, ACCENT = "#FAF8F3", "#1A1A1A", "#5A5650", "#C9C3B6", "#9E2A1E"
SERIF = '"Noto Serif CJK KR","Noto Serif KR",serif'
SANS = '"Noto Sans CJK KR","Noto Sans KR",sans-serif'


def icon_html(size: int) -> str:
    return f"<html><body style='margin:0;background:transparent'><div id='s' style='width:{size}px;height:{size}px'>{SVG.replace('<svg ', f'<svg width=\"{size}\" height=\"{size}\" ', 1)}</div></body></html>"


def bars(n, x, y, w, gap=22, h=8, seed=0):
    """신문 본문처럼 보이는 회색 줄."""
    out = []
    for i in range(n):
        ww = w if (i + seed) % 5 != 4 else w * 0.62
        out.append(f"<div style='position:absolute;left:{x}px;top:{y + i * gap}px;width:{ww:.0f}px;height:{h}px;background:{INK};opacity:.13'></div>")
    return "".join(out)


def cover_html(w: int, h: int) -> str:
    s = h / 600  # 600px 높이 기준 비율
    sun_r = 165 * s
    horizon = h * 0.62
    sun_cx = w - 300 * s
    cols = ""
    col_w, col_gap = 120 * s, 26 * s
    left0 = sun_cx - (col_w * 3 + col_gap * 2) / 2
    for c in range(3):
        cols += bars(6, left0 + c * (col_w + col_gap), horizon + 34 * s, col_w, gap=22 * s, h=7 * s, seed=c)
    return f"""<html><body style='margin:0'>
<div id='s' style='position:relative;width:{w}px;height:{h}px;overflow:hidden;background:{PAPER};font-family:{SANS};color:{INK}'>
  <div style='position:absolute;left:0;right:0;top:{40*s}px;border-top:{3*s}px solid {INK}'></div>
  <div style='position:absolute;left:0;right:0;top:{48*s}px;border-top:{1*s}px solid {INK}'></div>
  <div style='position:absolute;left:0;right:0;bottom:{48*s}px;border-top:{1*s}px solid {INK}'></div>
  <div style='position:absolute;left:0;right:0;bottom:{40*s}px;border-top:{3*s}px solid {INK}'></div>

  <div style='position:absolute;left:{sun_cx - sun_r}px;top:{horizon - sun_r}px;width:{sun_r*2}px;height:{sun_r}px;border-radius:{sun_r}px {sun_r}px 0 0;background:{ACCENT}'></div>
  <div style='position:absolute;left:{sun_cx - 330*s}px;width:{660*s}px;top:{horizon}px;height:{9*s}px;background:{INK}'></div>
  <div style='position:absolute;left:{sun_cx - 330*s}px;width:{660*s}px;top:{horizon + 16*s}px;height:{2.5*s}px;background:{INK}'></div>
  {cols}

  <div style='position:absolute;left:{110*s}px;top:{150*s}px'>
    <div style='font-size:{20*s}px;letter-spacing:.32em;color:{MUTED}'>HR · AX · ECONOMY</div>
    <div style='font-family:{SERIF};font-weight:900;font-size:{148*s}px;line-height:1.05;letter-spacing:-.02em;margin-top:{14*s}px'>아침 브리핑</div>
    <div style='margin-top:{22*s}px;padding-top:{18*s}px;border-top:{1.5*s}px solid {INK};font-family:{SERIF};font-size:{26*s}px;color:#3A3732;width:{620*s}px'>일하는 사람을 위한 나만의 조간</div>
    <div style='margin-top:{10*s}px;font-size:{18*s}px;color:{MUTED}'>인사 · AI 전환과 기업교육 · 경제 &nbsp;|&nbsp; 매일 아침 9시 30분 발행</div>
  </div>
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
        for size, name in [(32, "favicon-32.png"), (180, "apple-touch-icon.png"), (192, "icon-192.png"), (512, "icon-512.png")]:
            shoot(pg, icon_html(size), ICONS / name, size, size, transparent=True)
        shoot(pg, icon_html(512), NOTION / "notion-icon.png", 512, 512, transparent=True)
        shoot(pg, cover_html(1500, 600), NOTION / "notion-cover.png", 1500, 600)
        shoot(pg, cover_html(1200, 630), ICONS / "og-image.png", 1200, 630)
        b.close()


if __name__ == "__main__":
    main()
