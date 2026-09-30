import io
import unittest
from contextlib import redirect_stdout
from http.client import IncompleteRead
from unittest.mock import MagicMock, call, patch
from urllib.error import HTTPError, URLError

from main import fetch_text


URL = "https://example.com/article.html"


def response(body=b"article"):
    context = MagicMock()
    context.__enter__.return_value.read.return_value = body
    return context


class DownloadTests(unittest.TestCase):
    def setUp(self):
        self.output = redirect_stdout(io.StringIO())
        self.output.__enter__()
        self.addCleanup(self.output.__exit__, None, None, None)

    @patch("main.time.sleep")
    @patch("main.urlopen")
    def test_success_has_no_retry(self, open_url, sleep):
        open_url.return_value = response("正文".encode("utf-8"))
        self.assertEqual(fetch_text(URL), "正文")
        open_url.assert_called_once_with(URL, timeout=180)
        sleep.assert_not_called()

    @patch("main.time.sleep")
    @patch("main.urlopen")
    def test_connection_failures_recover_on_third_attempt(self, open_url, sleep):
        open_url.side_effect = [TimeoutError(), URLError("connection failed"), response()]
        self.assertEqual(fetch_text(URL), "article")
        self.assertEqual(open_url.call_args_list, [call(URL, timeout=180)] * 3)
        self.assertEqual(sleep.call_args_list, [call(5)] * 2)

    @patch("main.time.sleep")
    @patch("main.urlopen")
    def test_read_failures_restart_download_and_close_response(self, open_url, sleep):
        for failure in (TimeoutError(), IncompleteRead(b"partial", 100)):
            with self.subTest(failure=type(failure).__name__):
                broken = response()
                broken.__enter__.return_value.read.side_effect = failure
                open_url.side_effect = [broken, response(b"complete")]
                self.assertEqual(fetch_text(URL), "complete")
                broken.__exit__.assert_called_once()

    @patch("main.time.sleep")
    @patch("main.urlopen")
    def test_exhaustion_raises_without_fourth_attempt(self, open_url, sleep):
        error = TimeoutError("read timed out")
        open_url.side_effect = error
        with self.assertRaises(TimeoutError) as raised:
            fetch_text(URL)
        self.assertIs(raised.exception, error)
        self.assertEqual(open_url.call_count, 3)
        self.assertEqual(sleep.call_args_list, [call(5)] * 2)

    @patch("main.time.sleep")
    @patch("main.urlopen")
    def test_http_retry_policy(self, open_url, sleep):
        for status in (408, 429, 500, 503):
            with self.subTest(status=status):
                open_url.reset_mock()
                open_url.side_effect = [HTTPError(URL, status, "temporary", {}, None), response()]
                self.assertEqual(fetch_text(URL), "article")
                self.assertEqual(open_url.call_count, 2)
        open_url.reset_mock()
        sleep.reset_mock()
        open_url.side_effect = HTTPError(URL, 404, "not found", {}, None)
        with self.assertRaises(HTTPError):
            fetch_text(URL)
        self.assertEqual(open_url.call_count, 1)
        sleep.assert_not_called()


if __name__ == "__main__":
    unittest.main()
