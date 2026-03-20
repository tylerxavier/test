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

WASHINGTON_RADIUS_TERMS = [
    "Washington, DC",
    "Washington DC",
    "Washington",
    "District of Columbia",
    "Capitol One Arena",
    "Nationals Park",
    "Audi Field",
    "North Bethesda",
    "College Park",
    "Fairfax",
    "Tysons",
    "Bethesda",
    "Arlington",
    "Alexandria",
    "Silver Spring",
]

KEYWORDS = sorted({term.lower() for term in ADJACENT_NEIGHBORHOODS + KEY_LOCATIONS})
SPORTS_KEYWORDS = sorted({term.lower() for term in WASHINGTON_RADIUS_TERMS})

NEWS_DAYS = 7
EVENT_DAYS = 14
SPORTS_DAYS = 30
