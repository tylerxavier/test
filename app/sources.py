from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Source:
    name: str
    category: str
    kind: str
    url: str
    geographic_hint: bool = False


SOURCES = [
    Source(
        name="WTOP Local DC",
        category="news",
        kind="rss",
        url="https://wtop.com/region/local/dc/feed/",
    ),
    Source(
        name="PoPville",
        category="news",
        kind="rss",
        url="https://www.popville.com/feed/",
    ),
    Source(
        name="Trinidad DC Resources",
        category="news",
        kind="html",
        url="https://trinidad-dc.com/",
        geographic_hint=True,
    ),
    Source(
        name="DC Public Library Events",
        category="events",
        kind="html",
        url="https://www.dclibrary.org/attend-event",
    ),
    Source(
        name="Eventbrite Trinidad Community",
        category="events",
        kind="html",
        url="https://www.eventbrite.com/b/dc--washington--trinidad/community/",
        geographic_hint=True,
    ),
    Source(
        name="Eventbrite Trinidad Things To Do",
        category="events",
        kind="html",
        url="https://www.eventbrite.com/ttd/dc--washington--trinidad/",
        geographic_hint=True,
    ),
    Source(
        name="Eventbrite DC Sports",
        category="sports",
        kind="html_context",
        url="https://www.eventbrite.com/d/dc--washington/sports-and-fitness--events/",
        geographic_hint=True,
    ),
    Source(
        name="Ticketmaster DC Sports",
        category="sports",
        kind="html_context",
        url="https://www.ticketmaster.com/discover/sports/washington",
        geographic_hint=True,
    ),
]
