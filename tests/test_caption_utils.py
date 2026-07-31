import unittest

from adapters.telegram.caption_utils import html_text_length, trim_media_caption


class MediaCaptionTests(unittest.TestCase):
    def test_short_caption_is_unchanged(self) -> None:
        caption = "<b>Title</b>\nStory"

        self.assertEqual(caption, trim_media_caption(caption))

    def test_long_caption_is_trimmed_and_html_is_balanced(self) -> None:
        caption = f"<b>{'😀' * 600}</b>"

        result = trim_media_caption(caption)

        self.assertLessEqual(html_text_length(result), 1024)
        self.assertTrue(result.endswith("…</b>"))

    def test_trailing_link_is_preserved_when_story_is_trimmed(self) -> None:
        link = "<a href='https://mydramalist.com/example'>See more...</a>"
        caption = f"<b>Storyline:</b> {'A' * 1200}\n{link}"

        result = trim_media_caption(caption)

        self.assertLessEqual(html_text_length(result), 1024)
        self.assertIn("…\n", result)
        self.assertTrue(result.endswith(link))

    def test_html_entities_count_as_rendered_characters(self) -> None:
        caption = "&amp;" * 1024

        self.assertEqual(caption, trim_media_caption(caption))
        self.assertEqual(1024, html_text_length(caption))


if __name__ == "__main__":
    unittest.main()
