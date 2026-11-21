import csv
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import render  # noqa: E402

CONTENT = os.path.join(os.path.dirname(__file__), "..", "content", "fruit_v1.csv")


def write_csv(rows):
    fd, path = tempfile.mkstemp(suffix=".csv")
    with os.fdopen(fd, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(render.REQUIRED_COLUMNS)
        w.writerows(rows)
    return path


class TestLoad(unittest.TestCase):
    def test_real_content_has_3_sets_of_6(self):
        sets = render.load_slides(CONTENT)
        self.assertEqual(sorted(sets), [1, 2, 3])
        for slides in sets.values():
            self.assertEqual(len(slides), 6)
            self.assertEqual(slides[0]["role"], "표지")
            self.assertEqual(slides[-1]["role"], "CTA")

    def test_no_sales_wording_in_content(self):
        # 과일 판매 전이므로 판매/직송 문구가 들어가면 안 됨
        with open(CONTENT, encoding="utf-8") as f:
            text = f.read()
        for word in ["직송", "판매", "구매", "주문", "가격"]:
            self.assertNotIn(word, text)

    def test_bad_role_rejected(self):
        path = write_csv([[1, 1, "엉뚱", "제목", "본문"]])
        with self.assertRaises(ValueError):
            render.load_slides(path)

    def test_page_gap_rejected(self):
        path = write_csv([[1, 1, "표지", "a", ""], [1, 3, "본문", "b", ""]])
        with self.assertRaises(ValueError):
            render.load_slides(path)


class TestRender(unittest.TestCase):
    def test_render_all_outputs_18_images_at_1080x1350(self):
        from PIL import Image
        with tempfile.TemporaryDirectory() as out:
            written = render.render_all(CONTENT, out)
            self.assertEqual(len(written), 18)
            for p in written:
                with Image.open(p) as im:
                    self.assertEqual(im.size, (1080, 1350))

    def test_overflow_raises(self):
        path = write_csv([[1, 1, "본문", "가" * 400, "나" * 400]])
        with tempfile.TemporaryDirectory() as out:
            with self.assertRaises(ValueError):
                render.render_all(path, out)

    def test_wrap_fits_width(self):
        from PIL import Image, ImageDraw, ImageFont
        draw = ImageDraw.Draw(Image.new("RGB", (10, 10)))
        font = ImageFont.truetype(render.FONT_BOLD, 76)
        max_w = render.WIDTH - render.MARGIN * 2
        for line in render.wrap_text("④ 보관은 서늘하게 / 겹치지 않게 아주아주아주아주아주아주긴단어입니다", font, max_w, draw):
            self.assertLessEqual(draw.textlength(line, font=font), max_w)


if __name__ == "__main__":
    unittest.main()
