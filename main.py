import argparse
import json
import os
import time
from datetime import datetime, timedelta, timezone
from http.client import HTTPException
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import urlopen

from wechat import create_draft


SHANGHAI = timezone(timedelta(hours=8))
DEFAULT_SOURCE_BASE_URL = (
    "https://raw.githubusercontent.com/zhangboen/hydrology-paper-brief/main/outputs"
)
DOWNLOAD_TIMEOUT_SECONDS = 180
DOWNLOAD_MAX_ATTEMPTS = 3
DOWNLOAD_RETRY_DELAY_SECONDS = 5


def source_base_url():
    configured_url = os.environ.get("WECHAT_HTML_SOURCE_BASE_URL")
    return (configured_url or DEFAULT_SOURCE_BASE_URL).rstrip("/")


def fetch_text(url):
    for attempt in range(1, DOWNLOAD_MAX_ATTEMPTS + 1):
        print("Downloading source file (attempt %s/%s, timeout %ss)." % (
            attempt, DOWNLOAD_MAX_ATTEMPTS, DOWNLOAD_TIMEOUT_SECONDS
        ), flush=True)
        try:
            with urlopen(url, timeout=DOWNLOAD_TIMEOUT_SECONDS) as response:
                return response.read().decode("utf-8")
        except (OSError, HTTPException) as error:
            # Retry transient failures, not permanent errors such as a missing file.
            if isinstance(error, HTTPError) and error.code not in (408, 429) and not 500 <= error.code < 600:
                raise
            if attempt == DOWNLOAD_MAX_ATTEMPTS:
                raise
            print("Download failed (%s); retrying in %s seconds." % (
                type(error).__name__, DOWNLOAD_RETRY_DELAY_SECONDS
            ), flush=True)
            time.sleep(DOWNLOAD_RETRY_DELAY_SECONDS)


def load_source_article(run_date):
    source_dir = os.environ.get("WECHAT_SOURCE_DIR")
    if source_dir and not os.environ.get("WECHAT_HTML_SOURCE_BASE_URL"):
        # Read both files from the same checked-out commit; never use an older date.
        source = Path(source_dir)
        print("Reading checked-out article for %s." % run_date, flush=True)
        html = (source / ("wechat-post-%s.html" % run_date)).read_text(encoding="utf-8")
        metadata = json.loads(
            (source / ("wechat-post-%s.json" % run_date)).read_text(encoding="utf-8")
        )
    else:
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
