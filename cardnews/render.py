"""카드뉴스 문안 CSV -> 인스타그램용 PNG 이미지(1080x1350) 자동 생성.

사용법:
    python3 cardnews/render.py cardnews/content/fruit_v1.csv --out cardnews/out

CSV 열: 세트, 장, 역할(표지/본문/CTA), 큰 제목, 본문
본문의 " / " 는 줄바꿈으로 처리한다.
"""
import argparse
import csv
import os
import sys
from collections import defaultdict

from PIL import Image, ImageDraw, ImageFont

WIDTH, HEIGHT = 1080, 1350  # 인스타그램 세로형 4:5
MARGIN = 96
def _pick_font(candidates):
    """존재하는 첫 글꼴 경로를 반환. 리눅스(나눔) -> Windows(맑은 고딕) 순."""
    for path in candidates:
        if path and os.path.exists(path):
            return path
    raise FileNotFoundError(f"한글 글꼴을 찾을 수 없음: {candidates}")


FONT_BOLD = _pick_font([
    os.environ.get("CARDNEWS_FONT_BOLD"),
    "/usr/share/fonts/truetype/nanum/NanumSquareB.ttf",
    r"C:\Windows\Fonts\malgunbd.ttf",
])
FONT_REG = _pick_font([
    os.environ.get("CARDNEWS_FONT_REG"),
    "/usr/share/fonts/truetype/nanum/NanumSquareR.ttf",
    r"C:\Windows\Fonts\malgun.ttf",
])

# 세트별 색 (배경, 강조). 세트 번호가 더 많으면 순환.
THEMES = [
    ("#F3F7EE", "#3E7B27"),  # 초록
    ("#FFF4E6", "#E8710A"),  # 주황(귤)
    ("#FDEEEE", "#C62828"),  # 빨강(사과)
    ("#F7EEF8", "#8E3A9D"),  # 보라
]
TEXT_DARK = "#222222"
TEXT_SUB = "#555555"

REQUIRED_COLUMNS = ["세트", "장", "역할", "큰 제목", "본문"]
ROLES = {"표지", "본문", "CTA"}


def load_slides(csv_path):
    """CSV를 읽어 {세트번호: [슬라이드...]} 로 반환. 형식 오류는 ValueError."""
    with open(csv_path, encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        missing = [c for c in REQUIRED_COLUMNS if c not in (reader.fieldnames or [])]
        if missing:
            raise ValueError(f"CSV에 필요한 열이 없음: {missing}")
        sets = defaultdict(list)
        for line_no, row in enumerate(reader, start=2):
            if not (row.get("세트") or "").strip():
                continue
            role = row["역할"].strip()
            if role not in ROLES:
                raise ValueError(f"{line_no}행: 역할 '{role}' 은 {sorted(ROLES)} 중 하나여야 함")
            title = row["큰 제목"].strip()
            if not title:
                raise ValueError(f"{line_no}행: 큰 제목이 비어 있음")
            sets[int(row["세트"])].append({
                "page": int(row["장"]),
                "role": role,
                "title": title,
                "body": row["본문"].strip(),
            })
    for set_no, slides in sets.items():
        slides.sort(key=lambda s: s["page"])
        pages = [s["page"] for s in slides]
        if pages != list(range(1, len(pages) + 1)):
            raise ValueError(f"세트 {set_no}: 장 번호가 1부터 연속이 아님 {pages}")
    return dict(sets)


def wrap_text(text, font, max_width, draw):
    """픽셀 폭 기준 줄바꿈. 공백 단위로 자르고, 한 단어가 너무 길면 글자 단위로 자른다."""
    lines = []
    for paragraph in text.split(" / "):
        words = paragraph.split(" ")
        line = ""
        for word in words:
            candidate = word if not line else f"{line} {word}"
            if draw.textlength(candidate, font=font) <= max_width:
                line = candidate
                continue
            if line:
                lines.append(line)
            # 단어 자체가 한 줄보다 긴 경우 글자 단위로 분할
            line = ""
            for ch in word:
                if draw.textlength(line + ch, font=font) <= max_width:
                    line += ch
                else:
                    lines.append(line)
                    line = ch
        if line:
            lines.append(line)
    return lines


def _draw_block(draw, lines, font, x, y, fill, line_gap):
    for line in lines:
        draw.text((x, y), line, font=font, fill=fill)
        y += font.size + line_gap
    return y


DISCLOSURE = "이 게시물은 쿠팡 파트너스 활동의 일환으로, 이에 따른 일정액의 수수료를 제공받습니다."


def render_slide(slide, total, theme, disclosure=None):
    bg, accent = theme
    img = Image.new("RGB", (WIDTH, HEIGHT), bg)
    draw = ImageDraw.Draw(img)
    if disclosure and slide["role"] == "표지":
        # 광고 표시: 표지 맨 위, 배경과 대비되는 띠 위에 표시
        d_font = ImageFont.truetype(FONT_BOLD, 28)
        d_lines = wrap_text(disclosure, d_font, WIDTH - MARGIN * 2, draw)
        band_h = 40 + len(d_lines) * 40
        draw.rectangle([0, 0, WIDTH, band_h], fill="#333333")
        _draw_block(draw, d_lines, d_font, MARGIN, 24, "#FFFFFF", 12)
    max_w = WIDTH - MARGIN * 2
    role = slide["role"]

    title_size = {"표지": 92, "본문": 76, "CTA": 76}[role]
    body_size = {"표지": 46, "본문": 44, "CTA": 42}[role]
    title_font = ImageFont.truetype(FONT_BOLD, title_size)
    body_font = ImageFont.truetype(FONT_REG, body_size)

    title_lines = wrap_text(slide["title"], title_font, max_w, draw)
    body_lines = wrap_text(slide["body"], body_font, max_w, draw) if slide["body"] else []

    title_h = len(title_lines) * (title_size + 24)
    body_h = len(body_lines) * (body_size + 20)
    gap = 56 if body_lines else 0
    block_h = title_h + gap + body_h

    if role == "표지":
        y = (HEIGHT - block_h) // 2 - 40
        draw.rectangle([MARGIN, y - 60, MARGIN + 120, y - 48], fill=accent)
    else:
        y = 300
        draw.rectangle([0, 0, WIDTH, 24], fill=accent)

    y = _draw_block(draw, title_lines, title_font, MARGIN, y, accent if role != "본문" else TEXT_DARK, 24)
    if role == "본문":
        draw.rectangle([MARGIN, y + 8, MARGIN + 80, y + 16], fill=accent)
    y += gap
    y = _draw_block(draw, body_lines, body_font, MARGIN, y, TEXT_SUB, 20)

    # 하단 페이지 표시
    page_font = ImageFont.truetype(FONT_REG, 32)
    page_text = f"{slide['page']} / {total}"
    pw = draw.textlength(page_text, font=page_font)
    draw.text((WIDTH - MARGIN - pw, HEIGHT - MARGIN - 32), page_text, font=page_font, fill=TEXT_SUB)

    if y > HEIGHT - MARGIN - 60:
        raise ValueError(f"글자가 너무 많아 이미지 밖으로 넘침: '{slide['title']}'")
    return img


def render_all(csv_path, out_dir, disclosure=None):
    sets = load_slides(csv_path)
    written = []
    for set_no in sorted(sets):
        slides = sets[set_no]
        theme = THEMES[(set_no - 1) % len(THEMES)]
        set_dir = os.path.join(out_dir, f"set{set_no:02d}")
        os.makedirs(set_dir, exist_ok=True)
        for slide in slides:
            img = render_slide(slide, len(slides), theme, disclosure)
            path = os.path.join(set_dir, f"{slide['page']:02d}.png")
            img.save(path, "PNG")
            written.append(path)
    return written


def main(argv=None):
    parser = argparse.ArgumentParser(description="카드뉴스 CSV -> PNG")
    parser.add_argument("csv_path")
    parser.add_argument("--out", default="cardnews/out")
    parser.add_argument("--affiliate", action="store_true",
                        help="쿠팡 파트너스 링크를 붙일 게시물: 표지에 광고 표시 문구를 넣는다")
    args = parser.parse_args(argv)
    written = render_all(args.csv_path, args.out, DISCLOSURE if args.affiliate else None)
    print(f"{len(written)}장 생성 -> {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
