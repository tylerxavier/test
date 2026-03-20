# Trinidad Neighborhood News + Events Scanner

A small Python web app that scans a curated set of official, local news, and community event pages to surface items relevant to the Trinidad neighborhood in Northeast DC and immediately adjacent neighborhoods.

## What it does

- Scans key sites on demand from a simple web UI.
- Filters results to Trinidad and adjacent neighborhood/location keywords.
- Splits results into:
  - local news from the last 7 days
  - local events in the next 14 days
- Exposes both:
  - an HTML dashboard at `/`
  - JSON output at `/api/scan`
  - Markdown output at `/api/scan?format=markdown`

## Included source types

- Local news feeds
  - WTOP Local DC RSS
  - PoPville RSS
  - Trinidad DC Resources
- Event/community sources
  - DC Public Library events page
  - Eventbrite Trinidad community page
  - Eventbrite Trinidad things-to-do page

The source list is intentionally easy to edit in `app/sources.py`.

## Geography rules

The first version uses keyword matching for Trinidad plus adjacent neighborhoods and nearby landmarks/streets. You can tune the list in `app/config.py`.

## Run locally

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python run.py
```

Then open <http://127.0.0.1:8000>.

## API

- `GET /` – dashboard
- `POST /scan` – trigger a scan from the form
- `GET /api/scan` – returns JSON with `news`, `events`, and `errors`
- `GET /api/scan?format=markdown` – returns a Markdown summary

## Testing

```bash
python3 -m unittest discover -s tests -v
```
