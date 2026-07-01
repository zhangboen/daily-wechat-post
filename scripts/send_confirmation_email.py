from __future__ import annotations

import json
import os
import smtplib
from datetime import datetime
from email.message import EmailMessage
from pathlib import Path


def _latest_metadata() -> dict:
    output_dir = Path("outputs")
    metadata_files = sorted(output_dir.glob("daily-wechat-post-*.json"), key=lambda path: path.stat().st_mtime)
    if not metadata_files:
        return {}
    try:
        return json.loads(metadata_files[-1].read_text(encoding="utf-8"))
    except Exception:
        return {}


def _required_env(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value:
        raise RuntimeError(f"Missing {name} secret.")
    return value


def main() -> int:
    username = _required_env("CONFIRMATION_SMTP_USERNAME")
    password = _required_env("CONFIRMATION_SMTP_PASSWORD")
    recipient = os.environ.get("CONFIRMATION_EMAIL_TO", "").strip() or username
    sender = os.environ.get("CONFIRMATION_EMAIL_FROM", "").strip() or username
    host = os.environ.get("CONFIRMATION_SMTP_HOST", "smtp.gmail.com")
    port = int(os.environ.get("CONFIRMATION_SMTP_PORT", "587"))

    metadata = _latest_metadata()
    run_id = os.environ.get("GITHUB_RUN_ID", "")
    repo = os.environ.get("GITHUB_REPOSITORY", "")
    run_url = f"https://github.com/{repo}/actions/runs/{run_id}" if repo and run_id else ""
    completed_at = datetime.now().astimezone().isoformat(timespec="seconds")
    article_title = metadata.get("title") or "daily-wechat-post"
    paper_count = metadata.get("paper_count", "unknown")

    message = EmailMessage()
    message["From"] = sender
    message["To"] = recipient
    message["Subject"] = f"daily-wechat-post completed successfully: {article_title}"
    message.set_content(
        "\n".join(
            [
                "The daily WeChat post workflow completed successfully.",
                "",
                f"Completed at: {completed_at}",
                f"Repository: {repo or 'unknown'}",
                f"Run URL: {run_url or 'unavailable'}",
                f"Article title: {article_title}",
                f"Paper count: {paper_count}",
                f"Source email: {metadata.get('email_subject', 'unknown')}",
            ]
        )
    )

    with smtplib.SMTP(host, port, timeout=30) as server:
        server.starttls()
        server.login(username, password)
        server.send_message(message)

    print(f"Sent confirmation email to {recipient}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
