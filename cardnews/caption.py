"""카드뉴스 세트별 인스타그램 캡션 자동 생성.

사용법:
    python3 cardnews/caption.py cardnews/content/all_fields_v2.csv --out cardnews/out/captions --affiliate

--affiliate 를 켜면 캡션 첫 줄에 쿠팡 파트너스 광고 표시 문구를 넣는다.
(링크가 들어가는 게시물은 반드시 켜야 한다. 문구가 빠지면 정산 제외될 수 있음)
"""
import argparse
import csv
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from render import DISCLOSURE, load_slides  # noqa: E402

HASHTAGS = {
    "육아": "#육아 #육아꿀팁 #아이랑놀기",
    "살림": "#살림 #살림꿀팁 #정리정돈",
    "패션": "#패션 #코디 #데일리룩",
    "뷰티": "#뷰티 #피부관리 #겨울피부",
    "요리": "#요리 #자취요리 #집밥",
    "인테리어": "#인테리어 #원룸인테리어 #방꾸미기",
    "여행": "#여행 #여행준비 #짐싸기",
    "반려동물": "#반려견 #강아지산책 #댕댕이",
    "자기계발": "#자기계발 #습관 #갓생",
    "직장생활": "#직장인 #업무꿀팁 #일잘러",
    "IT·앱": "#스마트폰꿀팁 #폰정리 #앱추천",
    "캠핑·아웃도어": "#캠핑 #겨울캠핑 #캠핑준비물",
    "취미": "#홈가드닝 #반려식물 #취미",
    "자동차": "#자동차 #차량관리 #겨울운전",
    "절약·생활비": "#절약 #생활비 #재테크기초",
    "문구·디지털 굿즈": "#다이어리 #다꾸 #문구",
    "계절·명절": "#연말정리 #새해목표 #연말",
}
DEFAULT_TAGS = "#꿀팁 #정보 #저장필수"
LINK_LINE = "👉 소개한 제품은 프로필 링크에서 볼 수 있어요"


def load_fields(csv_path):
    """세트 번호 -> 분야 (분야 열이 없으면 빈 문자열)."""
    fields = {}
    with open(csv_path, encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            if (row.get("세트") or "").strip():
                fields.setdefault(int(row["세트"]), (row.get("분야") or "").strip())
    return fields


def build_caption(slides, field, affiliate):
    lines = []
    if affiliate:
        lines += [f"[광고] {DISCLOSURE}", ""]
    cover = slides[0]
    lines.append(cover["title"])
    lines.append("")
    for s in slides[1:-1]:
        lines.append(s["title"])
    lines.append("")
    cta = slides[-1]
    lines.append(cta["title"])
    if cta["body"]:
        lines.append(cta["body"].replace(" / ", "\n"))
    if affiliate:
        lines += ["", LINK_LINE]
    lines += ["", HASHTAGS.get(field, DEFAULT_TAGS)]
    return "\n".join(lines)


def write_captions(csv_path, out_dir, affiliate=False):
    sets = load_slides(csv_path)
    fields = load_fields(csv_path)
    os.makedirs(out_dir, exist_ok=True)
    written = []
    for set_no in sorted(sets):
        text = build_caption(sets[set_no], fields.get(set_no, ""), affiliate)
        if affiliate and not text.startswith("[광고]"):
            raise AssertionError("광고 표시 문구가 첫 줄에 없음")
        path = os.path.join(out_dir, f"set{set_no:02d}.txt")
        with open(path, "w", encoding="utf-8") as f:
            f.write(text + "\n")
        written.append(path)
    return written


def main(argv=None):
    parser = argparse.ArgumentParser(description="카드뉴스 CSV -> 인스타 캡션")
    parser.add_argument("csv_path")
    parser.add_argument("--out", default="cardnews/out/captions")
    parser.add_argument("--affiliate", action="store_true")
    args = parser.parse_args(argv)
    written = write_captions(args.csv_path, args.out, args.affiliate)
    print(f"캡션 {len(written)}개 생성 -> {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
