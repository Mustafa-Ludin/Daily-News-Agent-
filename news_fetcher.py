from __future__ import annotations

import html
import re
import ssl
from datetime import datetime
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen

import feedparser

try:
    import certifi
except ImportError:
    certifi = None


RSS_FEEDS = [
    "https://feeds.bbci.co.uk/news/world/rss.xml",
    "https://www.aljazeera.com/xml/rss/all.xml",
    "https://www.reutersagency.com/feed/?best-topics=world",
    "https://feeds.bbci.co.uk/sport/football/rss.xml",
    "https://tolonews.com/rss",
]

MAX_ARTICLES_PER_FEED = 25
FEED_TIMEOUT_SECONDS = 20
REQUEST_HEADERS = {
    "User-Agent": "AI-News-System/1.0",
    "Accept": "application/rss+xml, application/xml;q=0.9, text/xml;q=0.8, */*;q=0.7",
}


def fetch_news() -> list[dict[str, str]]:
    articles: list[dict[str, str]] = []
    seen: set[str] = set()

    for feed_url in RSS_FEEDS:
        try:
            parsed_feed = _parse_feed(feed_url)
            source = _source_name(parsed_feed, feed_url)

            for entry in parsed_feed.entries[:MAX_ARTICLES_PER_FEED]:
                article = _entry_to_article(entry, source)
                if not article:
                    continue

                key = _dedupe_key(article)
                if key in seen:
                    continue

                seen.add(key)
                articles.append(article)

        except (HTTPError, URLError, TimeoutError, ValueError) as exc:
            _log(f"RSS feed failed, skipping {feed_url}: {exc}")
        except Exception as exc:
            _log(f"Unexpected RSS error, skipping {feed_url}: {exc}")

    _log(f"Fetched {len(articles)} articles.")
    return articles


def _parse_feed(feed_url: str) -> Any:
    request = Request(feed_url, headers=REQUEST_HEADERS)
    with urlopen(
        request,
        timeout=FEED_TIMEOUT_SECONDS,
        context=_ssl_context(),
    ) as response:
        payload = response.read()

    parsed_feed = feedparser.parse(payload)

    if parsed_feed.bozo and not parsed_feed.entries:
        raise ValueError(parsed_feed.bozo_exception)

    return parsed_feed


def _ssl_context() -> ssl.SSLContext:
    if certifi is not None:
        return ssl.create_default_context(cafile=certifi.where())
    return ssl.create_default_context()


def _entry_to_article(entry: Any, source: str) -> dict[str, str] | None:
    title = _clean_text(entry.get("title", ""))
    link = entry.get("link", "").strip()
    summary = _clean_text(
        entry.get("summary")
        or entry.get("description")
        or entry.get("subtitle")
        or ""
    )

    if not title or not link:
        return None

    return {
        "title": title,
        "summary": summary,
        "source": source,
        "link": link,
    }


def _source_name(parsed_feed: Any, feed_url: str) -> str:
    feed_title = parsed_feed.feed.get("title", "")
    cleaned_title = _clean_text(feed_title)
    if cleaned_title:
        return cleaned_title

    hostname = urlparse(feed_url).hostname or feed_url
    return hostname.replace("www.", "")


def _clean_text(value: str) -> str:
    value = html.unescape(str(value))
    value = re.sub(r"<[^>]+>", " ", value)
    value = re.sub(r"\s+", " ", value)
    return value.strip()


def _dedupe_key(article: dict[str, str]) -> str:
    return (article.get("link") or article["title"]).strip().rstrip("/").lower()


def _log(message: str) -> None:
    timestamp = datetime.now().isoformat(timespec="seconds")
    print(f"{timestamp} {message}", flush=True)


__all__ = ["fetch_news"]
