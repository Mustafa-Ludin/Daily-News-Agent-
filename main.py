from __future__ import annotations

from datetime import datetime

from dotenv import load_dotenv

from analysis_agent import analyze_news
from editor_agent import create_newsletter
from email_agent import send_email
from news_fetcher import fetch_news
from research_agent import research_news


def run_workflow() -> str:
    load_dotenv()

    _log("FETCHING NEWS...")
    articles = fetch_news()
    if not articles:
        raise RuntimeError("No articles were fetched from the RSS feeds.")

    _log("RESEARCHING...")
    research_report = research_news(articles)

    _log("ANALYZING...")
    analysis_report = analyze_news(research_report)

    _log("GENERATING NEWSLETTER...")
    newsletter = create_newsletter(research_report, analysis_report)

    _log("SENDING EMAIL...")
    send_email(newsletter)

    _log("DONE.")
    return newsletter


def main() -> None:
    try:
        run_workflow()
    except Exception as exc:
        _log(f"Workflow failed: {exc}")
        raise


def _log(message: str) -> None:
    timestamp = datetime.now().isoformat(timespec="seconds")
    print(f"{timestamp} {message}", flush=True)


if __name__ == "__main__":
    main()
