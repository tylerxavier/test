from __future__ import annotations

ADJACENT_NEIGHBORHOODS = [
    "Trinidad",
    "Carver",
    "Langston",
    "Ivy City",
    "Near Northeast",
    "H Street",
    "Union Market",
    "NoMa",
    "Eckington",
]

KEY_LOCATIONS = [
    "Florida Ave NE",
    "Benning Road",
    "Bladensburg Road",
    "West Virginia Avenue",
    "Gallaudet",
    "National Arboretum",
    "Cole Recreation Center",
    "Trinidad Farmers Market",
]

KEYWORDS = sorted({term.lower() for term in ADJACENT_NEIGHBORHOODS + KEY_LOCATIONS})

NEWS_DAYS = 7
EVENT_DAYS = 14
