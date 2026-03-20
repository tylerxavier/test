import unittest
from datetime import datetime, timedelta, timezone

from app.scanner import Item, ScanResult, dedupe_and_sort, extract_price, filter_items, render_markdown
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

    def test_sports_items_capture_price_and_radius_keywords(self):
        source = Source(name="Sports Source", category="sports", kind="html_context", url="https://example.com", geographic_hint=True)
        soon = (datetime.now(timezone.utc) + timedelta(days=7)).isoformat()
        items = [
            Item(
                title="Washington Capitals vs Rangers",
                url="https://example.com/sports",
                source=source.name,
                category="sports",
                summary="Capital One Arena in Washington, DC. Tickets from $55.",
                published_at=soon,
                price_text="Tickets from $55",
            )
        ]

        filtered = filter_items(items, source)

        self.assertEqual(len(filtered), 1)
        self.assertIn("washington, dc", filtered[0].matched_terms)
        self.assertEqual(filtered[0].price_text, "Tickets from $55")

    def test_extract_price_supports_multiple_patterns(self):
        self.assertEqual(extract_price("Starts at $19.99"), "Starts at $19.99")
        self.assertEqual(extract_price("Tickets from $42"), "Tickets from $42")

    def test_dedupe_and_markdown_rendering(self):
        result = ScanResult(
            generated_at="2099-03-20T12:00:00+00:00",
            news=[
                Item(title="Story", url="https://example.com/1", source="A", category="news", summary="Summary"),
                Item(title="Story", url="https://example.com/1/", source="A", category="news", summary="Duplicate"),
            ],
            events=[],
            sports=[
                Item(title="Game", url="https://example.com/game", source="A", category="sports", price_text="From $20")
            ],
            errors=["Example error"],
        )

        deduped = dedupe_and_sort(result.news)
        self.assertEqual(len(deduped), 1)

        markdown = render_markdown(result)
        self.assertIn("# Trinidad Area News and Events", markdown)
        self.assertIn("## Sports events", markdown)
        self.assertIn("From $20", markdown)
        self.assertIn("Example error", markdown)


if __name__ == "__main__":
    unittest.main()
