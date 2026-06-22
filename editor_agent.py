from __future__ import annotations

import os
import time
from datetime import date, datetime
from typing import Any

from openai import OpenAI, OpenAIError


DEFAULT_MODEL = "gpt-4.1-mini"
MAX_OPENAI_ATTEMPTS = 2


def create_newsletter(research_report: str, analysis_report: str) -> str:
    if not research_report or not research_report.strip():
        raise ValueError("create_newsletter requires a research report.")
    if not analysis_report or not analysis_report.strip():
        raise ValueError("create_newsletter requires an analysis report.")

    _validate_openai_api_key()

    today = date.today().strftime("%B %d, %Y")
    prompt = f"""You are AGENT 4: Editor Agent for a professional daily AI news system.

Create a polished, executive-grade newsletter for {today}. Use only the research and analysis provided. Do not invent facts or add unsupported claims.

The newsletter must be publication-ready and include exactly these sections:

# Executive Summary
# Top Stories
# Global Affairs
# Football
# Strategic Insights
# What to Watch

Style requirements:
- Professional and concise.
- Include source links when they are available in the research.
- Use clear bullets for scannability.
- Keep the newsletter focused on decisions, signals, and implications.
"""

    payload = f"""RESEARCH REPORT
{research_report.strip()}

ANALYSIS REPORT
{analysis_report.strip()}
"""

    return _call_openai(prompt, payload, 3200)


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
                temperature=0.35,
                max_output_tokens=max_output_tokens,
            )

            text = _extract_response_text(response)
            if not text:
                raise RuntimeError("OpenAI returned an empty newsletter.")
            return text

        except (OpenAIError, RuntimeError) as exc:
            last_error = exc
            _log(f"Editor Agent OpenAI attempt {attempt} failed: {exc}")
            if attempt < MAX_OPENAI_ATTEMPTS:
                time.sleep(3)

    raise RuntimeError(f"Editor Agent failed after retry: {last_error}") from last_error


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


__all__ = ["create_newsletter"]
