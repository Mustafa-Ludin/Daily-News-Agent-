from __future__ import annotations

import html
import os
import smtplib
import ssl
from datetime import date
from email.message import EmailMessage

try:
    import certifi
except ImportError:
    certifi = None


SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 587


def send_email(newsletter: str) -> None:
    if not newsletter or not newsletter.strip():
        raise ValueError("send_email requires newsletter content.")

    sender = os.getenv("EMAIL_ADDRESS", "").strip()
    password = os.getenv("EMAIL_PASSWORD", "").strip()
    recipient = sender

    if not sender or sender.startswith("your_"):
        raise RuntimeError("EMAIL_ADDRESS is missing.")
    if not password or password.startswith("your_"):
        raise RuntimeError("EMAIL_PASSWORD is missing.")

    message = _build_message(sender, recipient, newsletter.strip())
    context = _ssl_context()

    with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=30) as smtp:
        smtp.ehlo()
        smtp.starttls(context=context)
        smtp.ehlo()
        try:
            smtp.login(sender, password)
        except smtplib.SMTPAuthenticationError as exc:
            raise RuntimeError(
                "Gmail rejected the login. Use a Google App Password for EMAIL_PASSWORD."
            ) from exc
        smtp.send_message(message)


def _build_message(sender: str, recipient: str, newsletter: str) -> EmailMessage:
    today = date.today().strftime("%B %d, %Y")
    message = EmailMessage()
    message["Subject"] = f"Daily AI News Briefing - {today}"
    message["From"] = sender
    message["To"] = recipient
    message.set_content(newsletter)
    message.add_alternative(_html_body(newsletter), subtype="html")
    return message


def _ssl_context() -> ssl.SSLContext:
    if certifi is not None:
        return ssl.create_default_context(cafile=certifi.where())
    return ssl.create_default_context()


def _html_body(newsletter: str) -> str:
    escaped_newsletter = html.escape(newsletter)
    return f"""<!doctype html>
<html>
  <body style="margin:0;padding:0;background:#f5f7fa;">
    <main style="max-width:760px;margin:0 auto;padding:32px 24px;background:#ffffff;color:#111827;font-family:Arial,Helvetica,sans-serif;line-height:1.55;">
      <div style="white-space:pre-wrap;font-size:15px;">{escaped_newsletter}</div>
    </main>
  </body>
</html>"""


__all__ = ["send_email"]
