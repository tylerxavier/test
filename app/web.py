from __future__ import annotations

from html import escape
from urllib.parse import parse_qs

from .scanner import render_markdown, scan_sources, to_json


def page_template(body: str, title: str = "Trinidad News + Events Scanner") -> bytes:
    html = f"""<!doctype html>
<html lang='en'>
  <head>
    <meta charset='utf-8'>
    <meta name='viewport' content='width=device-width, initial-scale=1'>
    <title>{escape(title)}</title>
    <style>
      body {{ font-family: Arial, sans-serif; margin: 0; background: #f5f7fb; color: #1f2937; }}
      .wrap {{ max-width: 1100px; margin: 0 auto; padding: 2rem; }}
      .hero, .card {{ background: white; border-radius: 16px; padding: 1.25rem 1.5rem; box-shadow: 0 10px 30px rgba(15, 23, 42, 0.08); margin-bottom: 1rem; }}
      .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 1rem; }}
      button {{ background: #0f766e; color: white; border: 0; border-radius: 999px; padding: 0.8rem 1.2rem; font-weight: bold; cursor: pointer; }}
      a {{ color: #0f766e; }}
      .meta {{ color: #475569; font-size: 0.92rem; }}
      .pill {{ display: inline-block; margin: 0.1rem 0.35rem 0.1rem 0; padding: 0.2rem 0.5rem; border-radius: 999px; background: #dcfce7; color: #166534; font-size: 0.82rem; }}
      pre {{ white-space: pre-wrap; background: #0b1020; color: #e2e8f0; padding: 1rem; border-radius: 12px; overflow: auto; }}
    </style>
  </head>
  <body><div class='wrap'>{body}</div></body>
</html>"""
    return html.encode("utf-8")


def render_index(result=None, markdown_output: str | None = None) -> bytes:
    body = [
        "<section class='hero'>",
        "<h1>Trinidad Neighborhood News + Events</h1>",
        "<p>Scan key official, local news, and community event sites for Trinidad in Northeast DC and immediately adjacent neighborhoods.</p>",
        "<form method='post' action='/scan'><button type='submit'>Scan key sites now</button></form>",
        "<p class='meta'>News window: last 7 days. Event window: next 14 days. Coverage includes Trinidad, Carver/Langston, Ivy City, Near Northeast, H Street, Union Market, NoMa, and Eckington.</p>",
        "</section>",
    ]
    if result:
        body.append("<div class='grid'>")
        body.append(render_items_card("News", result.news, "No recent news items matched the current Trinidad-area filters."))
        body.append(render_items_card("Events", result.events, "No upcoming events matched the current Trinidad-area filters."))
        body.append("</div>")
        body.append(f"<section class='card'><h2>Markdown output</h2><pre>{escape(markdown_output or '')}</pre></section>")
        if result.errors:
            error_html = "".join(f"<li>{escape(error)}</li>" for error in result.errors)
            body.append(f"<section class='card'><h2>Source errors</h2><ul>{error_html}</ul></section>")
    return page_template("".join(body))


def render_items_card(title: str, items: list, empty_message: str) -> str:
    html = [f"<section class='card'><h2>{escape(title)}</h2>"]
    if not items:
        html.append(f"<p>{escape(empty_message)}</p></section>")
        return "".join(html)
    for item in items:
        pills = "".join(f"<span class='pill'>{escape(term)}</span>" for term in (item.matched_terms or [])[:5])
        meta = " · ".join(part for part in [item.source, item.published_at, item.location] if part)
        html.append(
            f"<article><h3><a href='{escape(item.url)}' target='_blank' rel='noreferrer'>{escape(item.title)}</a></h3>"
            f"<p class='meta'>{escape(meta)}</p><p>{escape(item.summary)}</p><p>{pills}</p></article><hr>"
        )
    html.append("</section>")
    return "".join(html)


def create_app():
    def app(environ, start_response):
        path = environ.get("PATH_INFO", "/")
        method = environ.get("REQUEST_METHOD", "GET").upper()
        query = parse_qs(environ.get("QUERY_STRING", ""))

        if path == "/":
            start_response("200 OK", [("Content-Type", "text/html; charset=utf-8")])
            return [render_index()]

        if path == "/scan" and method == "POST":
            result = scan_sources()
            start_response("200 OK", [("Content-Type", "text/html; charset=utf-8")])
            return [render_index(result=result, markdown_output=render_markdown(result))]

        if path == "/api/scan":
            result = scan_sources()
            payload = to_json(result)
            if query.get("format") == ["markdown"]:
                payload = render_markdown(result)
                content_type = "text/markdown; charset=utf-8"
            else:
                content_type = "application/json; charset=utf-8"
            start_response("200 OK", [("Content-Type", content_type)])
            return [payload.encode("utf-8")]

        start_response("404 Not Found", [("Content-Type", "text/plain; charset=utf-8")])
        return [b"Not found"]

    return app
