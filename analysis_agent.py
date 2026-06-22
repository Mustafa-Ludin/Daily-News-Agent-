from __future__ import annotations

import os
import time
from datetime import datetime
from typing import Any

from openai import OpenAI, OpenAIError


DEFAULT_MODEL = "gpt-4.1-mini"
MAX_OPENAI_ATTEMPTS = 2


def analyze_news(research_report: str) -> str:
    if not research_report or not research_report.strip():
        raise ValueError("analyze_news requires a research report.")

    _validate_openai_api_key()

    prompt = """You are AGENT 3: Analysis Agent for a daily executive news briefing.

Analyze AGENT 2's research report. Use only the information in that report. Be practical, strategic, and concise.

Return an analysis report with exactly these sections:

# Why Stories Matter
Explain the strategic significance of the top stories.

# Economic Impact
Assess likely economic, market, trade, labor, and investment implications.

# AI/Tech Implications
Identify implications for AI, technology, cybersecurity, media, and digital infrastructure.

# Football Industry Insights
Analyze football as an industry, including clubs, leagues, governance, transfers, broadcasting, and fan interest where relevant.

# Future Outlook
Give likely near-term developments to monitor.
"""

    return _call_openai(prompt, research_report.strip(), 2600)


def _validate_openai_api_key() -> None:
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if not api_key or api_key.startswith("your_"):
        raise RuntimeError("OPENAI_API_KEY is missing.")


def _model() -> str:
    return os.getenv("OPENAI_MODEL", DEFAULT_MODEL).strip() or DEFAULT_MODEL


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
                temperature=0.25,
                max_output_tokens=max_output_tokens,
            )

            text = _extract_response_text(response)
            if not text:
                raise RuntimeError("OpenAI returned an empty analysis report.")
            return text

        except (OpenAIError, RuntimeError) as exc:
            last_error = exc
            _log(f"Analysis Agent OpenAI attempt {attempt} failed: {exc}")
            if attempt < MAX_OPENAI_ATTEMPTS:
                time.sleep(3)

    raise RuntimeError(f"Analysis Agent failed after retry: {last_error}") from last_error


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


def _log(message: str) -> None:
    timestamp = datetime.now().isoformat(timespec="seconds")
    print(f"{timestamp} {message}", flush=True)


__all__ = ["analyze_news"]
