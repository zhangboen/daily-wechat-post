import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import main


class SourceTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.source = Path(temporary.name)
        environment = patch.dict(os.environ, {
            "WECHAT_SOURCE_DIR": str(self.source),
            "WECHAT_HTML_SOURCE_BASE_URL": "",
        })
        environment.start()
        self.addCleanup(environment.stop)
        self.date = "2026-10-01"
        (self.source / f"wechat-post-{self.date}.html").write_text("<p>正文</p>", encoding="utf-8")
        (self.source / f"wechat-post-{self.date}.json").write_text(
            json.dumps({"title": "今日论文", "digest": "摘要"}), encoding="utf-8"
        )

    @patch("main.fetch_text")
    def test_local_pair_avoids_network(self, fetch):
        self.assertEqual(main.load_source_article(self.date), ("今日论文", "摘要", "<p>正文</p>"))
        fetch.assert_not_called()

    @patch("main.fetch_text")
    def test_missing_date_never_uses_old_article_or_network(self, fetch):
        with self.assertRaises(FileNotFoundError):
            main.load_source_article("2026-10-02")
        fetch.assert_not_called()

    @patch("main.fetch_text")
    def test_custom_url_keeps_priority(self, fetch):
        fetch.side_effect = ["remote article", '{"title":"remote","digest":"summary"}']
        with patch.dict(os.environ, {"WECHAT_HTML_SOURCE_BASE_URL": "https://example.com/articles/"}):
            self.assertEqual(main.load_source_article(self.date), ("remote", "summary", "remote article"))
        self.assertEqual(fetch.call_args_list[0].args[0], "https://example.com/articles/wechat-post-2026-10-01.html")

    @patch("main.create_draft")
    @patch("main.write_outputs")
    def test_dry_run_does_not_create_draft(self, write, create):
        self.assertEqual(main.run(self.date, dry_run=True), 0)
        create.assert_not_called()
        write.assert_called_once_with(self.date, "今日论文", "摘要", "<p>正文</p>", True)

    @patch("main.create_draft")
    @patch("main.write_outputs")
    def test_bad_metadata_does_not_create_draft(self, write, create):
        (self.source / f"wechat-post-{self.date}.json").write_text("invalid", encoding="utf-8")
        with self.assertRaises(json.JSONDecodeError):
            main.run(self.date)
        create.assert_not_called()
        write.assert_not_called()
