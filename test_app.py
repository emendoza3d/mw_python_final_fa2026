import unittest

from app import _ring_preview_svg


class RingPreviewTests(unittest.TestCase):
    def test_preview_reflects_shape_metal_diamond_and_style(self):
        preview = _ring_preview_svg("oval", "halo", "rose gold", "lab")

        self.assertIn('<ellipse cx="220" cy="93"', preview)
        self.assertIn('stroke="#e8d8ae"', preview)
        self.assertIn('stop-color="#c98276"', preview)
        self.assertIn("Oval · Halo · Rose Gold · Lab", preview)

    def test_preview_escapes_choice_labels(self):
        preview = _ring_preview_svg(
            '<script>alert(1)</script>', "solitaire", "gold", "natural"
        )

        self.assertNotIn("<script>", preview)
        self.assertIn("&lt;script&gt;", preview)
        self.assertIn('<circle cx="220" cy="93" r="25" />', preview)


if __name__ == "__main__":
    unittest.main()
