import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import caption  # noqa: E402
import render  # noqa: E402

CONTENT_DIR = os.path.join(os.path.dirname(__file__), "..", "content")
V2 = os.path.join(CONTENT_DIR, "all_fields_v2.csv")
FRUIT = os.path.join(CONTENT_DIR, "fruit_v1.csv")


class TestCaption(unittest.TestCase):
    def test_affiliate_caption_starts_with_disclosure(self):
        with tempfile.TemporaryDirectory() as out:
            paths = caption.write_captions(V2, out, affiliate=True)
            self.assertEqual(len(paths), 13)
            for p in paths:
                with open(p, encoding="utf-8") as f:
                    text = f.read()
                self.assertTrue(text.startswith("[광고] " + render.DISCLOSURE))
                self.assertIn(caption.LINK_LINE, text)

    def test_non_affiliate_caption_has_no_ad_or_link(self):
        with tempfile.TemporaryDirectory() as out:
            for p in caption.write_captions(V2, out, affiliate=False):
                with open(p, encoding="utf-8") as f:
                    text = f.read()
                self.assertNotIn("[광고]", text)
                self.assertNotIn(caption.LINK_LINE, text)

    def test_every_field_has_hashtags(self):
        fields = set(caption.load_fields(V2).values())
        fields |= set(caption.load_fields(os.path.join(CONTENT_DIR, "all_fields_v1.csv")).values())
        self.assertEqual(fields - set(caption.HASHTAGS), set())

    def test_csv_without_field_column_uses_default_tags(self):
        with tempfile.TemporaryDirectory() as out:
            p = caption.write_captions(FRUIT, out)[0]
            with open(p, encoding="utf-8") as f:
                self.assertIn(caption.DEFAULT_TAGS, f.read())


class TestRenderDisclosure(unittest.TestCase):
    def test_disclosure_changes_only_cover(self):
        sets = render.load_slides(V2)
        slides = sets[1]
        theme = render.THEMES[0]
        cover_plain = render.render_slide(slides[0], 6, theme)
        cover_ad = render.render_slide(slides[0], 6, theme, render.DISCLOSURE)
        self.assertNotEqual(cover_plain.tobytes(), cover_ad.tobytes())
        body_plain = render.render_slide(slides[1], 6, theme)
        body_ad = render.render_slide(slides[1], 6, theme, render.DISCLOSURE)
        self.assertEqual(body_plain.tobytes(), body_ad.tobytes())

    def test_default_render_unchanged_without_flag(self):
        # 기존 호출(옵션 없음)은 광고 띠가 없어야 함: 좌상단 픽셀이 배경색
        sets = render.load_slides(V2)
        img = render.render_slide(sets[1][0], 6, render.THEMES[0])
        self.assertEqual(img.getpixel((5, 5)), (0xF3, 0xF7, 0xEE))


if __name__ == "__main__":
    unittest.main()
