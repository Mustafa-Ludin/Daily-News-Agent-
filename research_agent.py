from __future__ import annotations

import json
import os
import time
from datetime import datetime
from typing import Any

from openai import OpenAI, OpenAIError


DEFAULT_MODEL = "gpt-4.1-mini"
MAX_ARTICLES_FOR_PROMPT = 80
MAX_OPENAI_ATTEMPTS = 2


def research_news(articles: list[dict[str, str]]) -> str:
    if not articles:
        raise ValueError("research_news requires at least one article.")

    _validate_openai_api_key()

    prompt = """You are AGENT 2: Research Agent for a daily executive news briefing.

Use only the RSS article data provided by AGENT 1. Do not invent facts. If a detail is missing, say so briefly.

Return a concise research report with exactly these sections:

# Top 10 Most Important Stories
Rank the 10 most important stories. For each story include title, source, link, and one sentence explaining importance.

# Global Trends
Identify cross-source patterns and themes.

# Football News Summary
Summarize football-specific developments from the available articles.

# Geopolitical Developments
Summarize major geopolitical developments and tensions.
"""

    payload = {
        "article_count": len(articles),
        "articles": _prepare_articles(articles),
    }

    return _call_openai(prompt, json.dumps(payload, ensure_ascii=False, indent=2), 2600)


def _validate_openai_api_key() -> None:
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if not api_key or api_key.startswith("your_"):
        raise RuntimeError("OPENAI_API_KEY is missing.")


def _model() -> str:
    return os.getenv("OPENAI_MODEL", DEFAULT_MODEL).strip() or DEFAULT_MODEL


def _prepare_articles(articles: list[dict[str, str]]) -> list[dict[str, str]]:
    prepared: list[dict[str, str]] = []
    for article in articles[:MAX_ARTICLES_FOR_PROMPT]:
        prepared.append(
            {
                "title": _truncate(article.get("title", ""), 220),
                "summary": _truncate(article.get("summary", ""), 700),
                "source": _truncate(article.get("source", ""), 120),
                "link": article.get("link", ""),
            }
        )
    return prepared


def _call_openai(developer_prompt: str, user_payload: str, max_output_tokens: int) -> str:
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    last_error: Exception | None = None

    for attempt in range(1, MAX_OPENAI_ATTEMPTS + 1):
        try:
            response = client.responses.create(
                model=_model(),
                input=[
                    {"role": "developer", "content": developer_prompt},
                    {"role": "user", "content": user_payload},
                ],
                temperature=0.2,
                max_output_tokens=max_output_tokens,
            )

            text = _extract_response_text(response)
            if not text:
                raise RuntimeError("OpenAI returned an empty research report.")
            return text

        except (OpenAIError, RuntimeError) as exc:
            last_error = exc
            _log(f"Research Agent OpenAI attempt {attempt} failed: {exc}")
            if attempt < MAX_OPENAI_ATTEMPTS:
                time.sleep(3)

    raise RuntimeError(f"Research Agent failed after retry: {last_error}") from last_error


def _extract_response_text(response: Any) -> str:
    output_text = getattr(response, "output_text", None)
    if output_text:
        return output_text.strip()

    chunks: list[str] = []
    for item in getattr(response, "output", []) or []:
        for content in getattr(item, "content", []) or []:
            text = getattr(content, "text", None)
            if text:
                chunks.append(text)

    return "\n".join(chunks).strip()


def _truncate(value: str, limit: int) -> str:
    value = " ".join(str(value).split())
    if len(value) <= limit:
        return value
    return value[: limit - 3].rstrip() + "..."


def _log(message: str) -> None:
    timestamp = datetime.now().isoformat(timespec="seconds")
    print(f"{timestamp} {message}", flush=True)


__all__ = ["research_news"]
