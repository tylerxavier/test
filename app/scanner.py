from __future__ import annotations

import json
import re
import xml.etree.ElementTree as ET
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from html import unescape
from html.parser import HTMLParser
from typing import Iterable
from urllib.parse import urljoin
from urllib.request import Request, urlopen

from .config import EVENT_DAYS, KEYWORDS, NEWS_DAYS, SPORTS_DAYS, SPORTS_KEYWORDS
from .sources import SOURCES, Source

USER_AGENT = "trinidad-neighborhood-scanner/0.2 (+https://localhost)"
MAX_HTML_ITEMS = 12
TIMEOUT_SECONDS = 15


@dataclass
class Item:
    title: str
    url: str
    source: str
    category: str
    summary: str = ""
    published_at: str | None = None
    location: str | None = None
    matched_terms: list[str] | None = None
    price_text: str | None = None


@dataclass
class ScanResult:
    generated_at: str
    news: list[Item]
    events: list[Item]
    sports: list[Item]
    errors: list[str]


class AnchorExtractor(HTMLParser):
    def __init__(self, base_url: str) -> None:
        super().__init__()
        self.base_url = base_url
        self.items: list[tuple[str, str]] = []
        self._href: str | None = None
        self._text_parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag == "a":
            attr_map = dict(attrs)
            href = attr_map.get("href")
            if href:
                self._href = urljoin(self.base_url, href)
                self._text_parts = []

    def handle_data(self, data: str) -> None:
        if self._href is not None:
            self._text_parts.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag == "a" and self._href is not None:
            title = clean_space(" ".join(self._text_parts))
            if title:
                self.items.append((title, self._href))
            self._href = None
            self._text_parts = []


def fetch_text(url: str) -> str:
    request = Request(url, headers={"User-Agent": USER_AGENT, "Accept": "text/html,application/rss+xml,application/xml"})
    with urlopen(request, timeout=TIMEOUT_SECONDS) as response:
        charset = response.headers.get_content_charset() or "utf-8"
        return response.read().decode(charset, errors="replace")


def scan_sources() -> ScanResult:
    grouped = {"news": [], "events": [], "sports": []}
    errors: list[str] = []

    for source in SOURCES:
        try:
            body = fetch_text(source.url)
            if source.kind == "rss":
                items = parse_rss(source, body)
            elif source.kind == "html_context":
                items = parse_html_context(source, body)
            else:
                items = parse_html(source, body)
            filtered = filter_items(items, source)
            grouped[source.category].extend(filtered)
        except Exception as exc:
            errors.append(f"{source.name}: {exc}")

    return ScanResult(
        generated_at=datetime.now(timezone.utc).isoformat(),
        news=dedupe_and_sort(grouped["news"]),
        events=dedupe_and_sort(grouped["events"]),
        sports=dedupe_and_sort(grouped["sports"]),
        errors=errors,
    )


def parse_rss(source: Source, body: str) -> list[Item]:
    root = ET.fromstring(body)
    items: list[Item] = []
    for node in root.findall(".//item")[:25]:
        items.append(
            Item(
                title=text_of(node.find("title")),
                url=text_of(node.find("link")),
                source=source.name,
                category=source.category,
                summary=strip_tags(text_of(node.find("description"))),
                published_at=normalize_date(text_of(node.find("pubDate"))),
            )
        )
    return items


def parse_html(source: Source, body: str) -> list[Item]:
    parser = AnchorExtractor(source.url)
    parser.feed(body)
    items: list[Item] = []
    seen: set[str] = set()
    text_blob = clean_space(strip_tags(body))
    page_date = extract_date(text_blob)
    page_location = extract_location(text_blob)

    for title, href in parser.items:
        if len(title) < 8 or href in seen or href.startswith(("javascript:", "mailto:")):
            continue
        items.append(
            Item(
                title=title,
                url=href,
                source=source.name,
                category=source.category,
                summary=text_blob[:400],
                published_at=page_date,
                location=page_location,
            )
        )
        seen.add(href)
        if len(items) >= MAX_HTML_ITEMS:
            break
    return items


def parse_html_context(source: Source, body: str) -> list[Item]:
    parser = AnchorExtractor(source.url)
    parser.feed(body)
    items: list[Item] = []
    seen: set[str] = set()

    for title, href in parser.items:
        if len(title) < 8 or href in seen or href.startswith(("javascript:", "mailto:")):
            continue
        context = extract_context(body, title, href)
        items.append(
            Item(
                title=title,
                url=href,
                source=source.name,
                category=source.category,
                summary=clean_space(strip_tags(context))[:400],
                published_at=extract_date(context),
                location=extract_location(context),
                price_text=extract_price(context),
            )
        )
        seen.add(href)
        if len(items) >= MAX_HTML_ITEMS:
            break
    return items


def filter_items(items: Iterable[Item], source: Source) -> list[Item]:
    now = datetime.now(timezone.utc)
    news_cutoff = now - timedelta(days=NEWS_DAYS)
    event_cutoff = now + timedelta(days=EVENT_DAYS)
    sports_cutoff = now + timedelta(days=SPORTS_DAYS)
    filtered: list[Item] = []

    for item in items:
        haystack = f"{item.title} {item.summary} {item.location or ''} {item.url}".lower()
        keywords = SPORTS_KEYWORDS if item.category == "sports" else KEYWORDS
        matched_terms = [term for term in keywords if term in haystack]
        if not matched_terms and not source.geographic_hint:
            continue
        item.matched_terms = matched_terms

        dt = parse_iso_datetime(item.published_at)
        if item.category == "news" and dt and dt < news_cutoff:
            continue
        if item.category == "events" and dt and (dt < now - timedelta(days=1) or dt > event_cutoff):
            continue
        if item.category == "sports":
            if dt and (dt < now - timedelta(days=1) or dt > sports_cutoff):
                continue
            if not item.price_text:
                item.price_text = "Price not listed"
        filtered.append(item)

    return filtered[:10]


def dedupe_and_sort(items: list[Item]) -> list[Item]:
    unique: dict[str, Item] = {}
    for item in items:
        unique.setdefault(item.url.rstrip("/"), item)
    return sorted(unique.values(), key=lambda item: item.published_at or "", reverse=True)


def render_markdown(result: ScanResult) -> str:
    lines = ["# Trinidad Area News and Events", "", f"Generated at: {result.generated_at}", "", "## News"]
    lines.extend(render_section(result.news, "No news items matched the current filters."))
    lines.extend(["", "## Events"])
    lines.extend(render_section(result.events, "No events matched the current filters."))
    lines.extend(["", "## Sports events (next 30 days, DC + ~20 mile radius)"])
    lines.extend(render_section(result.sports, "No sports events matched the current filters."))
    if result.errors:
        lines.extend(["", "## Source errors", *[f"- {error}" for error in result.errors]])
    return "\n".join(lines)


def render_section(items: list[Item], empty_message: str) -> list[str]:
    if not items:
        return [f"- {empty_message}"]
    lines: list[str] = []
    for item in items:
        lines.append(f"- [{item.title}]({item.url})")
        meta = [item.source]
        if item.published_at:
            meta.append(item.published_at)
        if item.location:
            meta.append(item.location)
        if item.price_text:
            meta.append(item.price_text)
        if item.matched_terms:
            meta.append("matches: " + ", ".join(item.matched_terms[:5]))
        lines.append(f"  - {' | '.join(meta)}")
        if item.summary:
            lines.append(f"  - {item.summary[:240]}")
    return lines


def to_json(result: ScanResult) -> str:
    return json.dumps(
        {
            "generated_at": result.generated_at,
            "news": [asdict(item) for item in result.news],
            "events": [asdict(item) for item in result.events],
            "sports": [asdict(item) for item in result.sports],
            "errors": result.errors,
        },
        indent=2,
    )


def extract_context(body: str, title: str, href: str) -> str:
    patterns = [re.escape(title), re.escape(href)]
    for pattern in patterns:
        match = re.search(pattern, body, flags=re.IGNORECASE)
        if match:
            start = max(0, match.start() - 500)
            end = min(len(body), match.end() + 500)
            return body[start:end]
    return body[:1200]


def text_of(node: ET.Element | None) -> str:
    return clean_space(node.text if node is not None and node.text else "")


def clean_space(value: str) -> str:
    return re.sub(r"\s+", " ", unescape(value or "")).strip()


def strip_tags(value: str) -> str:
    return clean_space(re.sub(r"<[^>]+>", " ", value or ""))


def normalize_date(value: str | None) -> str | None:
    if not value:
        return None
    try:
        return parsedate_to_datetime(value).astimezone(timezone.utc).isoformat()
    except (TypeError, ValueError, IndexError):
        match = re.search(r"(\d{4}-\d{2}-\d{2})", value)
        if match:
            return f"{match.group(1)}T00:00:00+00:00"
        return None


def extract_date(text: str) -> str | None:
    for pattern in [
        r"\b\d{4}-\d{2}-\d{2}\b",
        r"\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{1,2},\s+\d{4}\b",
    ]:
        match = re.search(pattern, text)
        if match:
            return normalize_date(match.group(0))
    return None


def extract_location(text: str) -> str | None:
    patterns = [
        r"([0-9]{1,5}[^|]{0,80}(?:NE|NW|SE|SW|Washington, DC))",
        r"\b(Washington, DC|Washington DC|Arlington, VA|Alexandria, VA|Bethesda, MD|Silver Spring, MD|College Park, MD)\b",
    ]
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            return clean_space(match.group(1))
    return None


def extract_price(text: str) -> str | None:
    patterns = [
        r"(Starts? at\s*\$\d+(?:\.\d{2})?)",
        r"(Tickets?\s+from\s*\$\d+(?:\.\d{2})?)",
        r"(From\s*\$\d+(?:\.\d{2})?)",
        r"(\$\d+(?:\.\d{2})?\s*(?:and up|starting price))",
    ]
    for pattern in patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match:
            return clean_space(match.group(1))
    return None


def parse_iso_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        return None
