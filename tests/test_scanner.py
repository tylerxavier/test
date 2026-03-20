import unittest

from app.scanner import Item, ScanResult, dedupe_and_sort, filter_items, render_markdown
from app.sources import Source


class ScannerTests(unittest.TestCase):
    def test_filter_items_matches_keywords_and_date_windows(self):
        source = Source(name="Test Source", category="news", kind="rss", url="https://example.com")
        items = [
            Item(
                title="Trinidad meeting tonight",
                url="https://example.com/1",
                source=source.name,
                category="news",
                summary="Community update for Trinidad and Ivy City",
                published_at="2099-03-20T12:00:00+00:00",
            ),
            Item(
                title="Completely unrelated story",
                url="https://example.com/2",
                source=source.name,
                category="news",
                summary="No neighborhood match here",
                published_at="2099-03-20T12:00:00+00:00",
            ),
        ]

        filtered = filter_items(items, source)

        self.assertEqual(len(filtered), 1)
        self.assertEqual(filtered[0].matched_terms, ["ivy city", "trinidad"])

    def test_dedupe_and_markdown_rendering(self):
        result = ScanResult(
            generated_at="2099-03-20T12:00:00+00:00",
            news=[
                Item(title="Story", url="https://example.com/1", source="A", category="news", summary="Summary"),
                Item(title="Story", url="https://example.com/1/", source="A", category="news", summary="Duplicate"),
            ],
            events=[],
            errors=["Example error"],
        )

        deduped = dedupe_and_sort(result.news)
        self.assertEqual(len(deduped), 1)

        markdown = render_markdown(result)
        self.assertIn("# Trinidad Area News and Events", markdown)
        self.assertIn("Example error", markdown)


if __name__ == "__main__":
    unittest.main()
