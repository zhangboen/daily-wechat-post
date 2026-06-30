from __future__ import annotations

import argparse
import json
from datetime import UTC, date, datetime, timedelta, timezone
from pathlib import Path

from abstract_lookup import lookup_abstract
from article_builder import build_html, generate_chinese_entries
from gmail_client import get_latest_brief_email
from paper_parser import parse_papers
from wechat import create_draft


SHANGHAI = timezone(timedelta(hours=8))


def run(dry_run: bool = False) -> int:
    run_date = datetime.now(SHANGHAI).date()
    outputs = Path("outputs")
    outputs.mkdir(exist_ok=True)

    message = get_latest_brief_email()
    if message is None:
        print("No daily hydrology paper brief email found. Stopping.")
        return 0

    papers = parse_papers(message.body)
    if not papers:
        print(f"Latest brief email {message.subject!r} contains no parsed papers. Stopping.")
        return 0

    for paper in papers:
        if not paper.abstract:
            paper.abstract = lookup_abstract(paper.title, paper.identifier, paper.url)

    entries = generate_chinese_entries(papers)
    title, digest, html = build_html(papers, entries, run_date)

    html_path = outputs / f"daily-wechat-post-{run_date.isoformat()}.html"
    html_path.write_text(html, encoding="utf-8")
    metadata_path = outputs / f"daily-wechat-post-{run_date.isoformat()}.json"
    metadata_path.write_text(
        json.dumps(
            {
                "email_message_id": message.message_id,
                "email_subject": message.subject,
                "email_timestamp": message.timestamp,
                "paper_count": len(papers),
                "title": title,
                "dry_run": dry_run,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    if dry_run:
        print(f"Dry run complete. Wrote {html_path}.")
        return 0

    result = create_draft(title=title, html=html, digest=digest)
    print(json.dumps({"wechat_draft_media_id": result.media_id, "paper_count": len(papers)}, ensure_ascii=False))
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true", help="Build HTML and metadata without creating WeChat draft.")
    args = parser.parse_args()
    return run(dry_run=args.dry_run)


if __name__ == "__main__":
    raise SystemExit(main())
