import argparse
import json
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.request import urlopen

from wechat import create_draft


SHANGHAI = timezone(timedelta(hours=8))
DEFAULT_SOURCE_BASE_URL = (
    "https://raw.githubusercontent.com/zhangboen/hydrology-paper-brief/main/outputs"
)


def source_base_url():
    return os.environ.get("WECHAT_HTML_SOURCE_BASE_URL", DEFAULT_SOURCE_BASE_URL).rstrip("/")


def fetch_text(url):
    with urlopen(url, timeout=60) as response:
        return response.read().decode("utf-8")


def load_source_article(run_date):
    base_url = source_base_url()
    html_url = "%s/wechat-post-%s.html" % (base_url, run_date)
    json_url = "%s/wechat-post-%s.json" % (base_url, run_date)

    html = fetch_text(html_url)
    metadata = json.loads(fetch_text(json_url))
    title = metadata.get("title") or "今日水文气候文献简报（%s）" % run_date
    digest = metadata.get("digest") or "今日水文气候文献简报。"
    return title, digest, html


def write_outputs(run_date, title, digest, html, dry_run):
    outputs = Path("outputs")
    outputs.mkdir(exist_ok=True)
    html_path = outputs / ("wechat-post-%s.html" % run_date)
    metadata_path = outputs / ("wechat-post-%s.json" % run_date)
    html_path.write_text(html, encoding="utf-8")
    metadata_path.write_text(
        json.dumps(
            {
                "title": title,
                "digest": digest,
                "source_base_url": source_base_url(),
                "dry_run": dry_run,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )


def run(run_date=None, dry_run=False):
    date_stamp = run_date or datetime.now(SHANGHAI).date().isoformat()
    title, digest, html = load_source_article(date_stamp)
    write_outputs(date_stamp, title, digest, html, dry_run)

    if dry_run:
        print("Dry run complete. Loaded WeChat HTML for %s." % date_stamp)
        return 0

    result = create_draft(title=title, html=html, digest=digest)
    print(json.dumps({"wechat_draft_media_id": result.media_id, "date": date_stamp}, ensure_ascii=False))
    return 0


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--date", help="Article date in YYYY-MM-DD format. Defaults to today in Asia/Shanghai.")
    parser.add_argument("--dry-run", action="store_true", help="Fetch source HTML without creating a WeChat draft.")
    args = parser.parse_args()
    return run(run_date=args.date, dry_run=args.dry_run)


if __name__ == "__main__":
    raise SystemExit(main())
