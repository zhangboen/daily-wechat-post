from __future__ import annotations

import imaplib
import os
from dataclasses import dataclass
from datetime import datetime, timedelta
from email import message_from_bytes
from email.header import decode_header, make_header
from email.message import Message
from email.utils import parsedate_to_datetime

from bs4 import BeautifulSoup


@dataclass
class MailMessage:
    message_id: str
    subject: str
    body: str
    timestamp: str


def _required_env(*names: str) -> str:
    for name in names:
        value = os.environ.get(name)
        if value:
            return value
    raise RuntimeError(f"Missing one of required secrets: {', '.join(names)}.")


def _decode_mime_header(value: str) -> str:
    if not value:
        return ""
    try:
        return str(make_header(decode_header(value)))
    except Exception:
        return value


def _decode_payload(part: Message) -> str:
    payload = part.get_payload(decode=True)
    if payload is None:
        return ""
    charset = part.get_content_charset() or "utf-8"
    return payload.decode(charset, errors="replace")


def _html_to_text(raw_html: str) -> str:
    soup = BeautifulSoup(raw_html, "html.parser")
    return soup.get_text("\n", strip=True)


def _extract_body(message: Message) -> str:
    plain_parts: list[str] = []
    html_parts: list[str] = []

    if message.is_multipart():
        for part in message.walk():
            if part.get_content_disposition() == "attachment":
                continue
            content_type = part.get_content_type()
            if content_type == "text/plain":
                plain_parts.append(_decode_payload(part))
            elif content_type == "text/html":
                html_parts.append(_html_to_text(_decode_payload(part)))
    else:
        content_type = message.get_content_type()
        if content_type == "text/html":
            html_parts.append(_html_to_text(_decode_payload(message)))
        else:
            plain_parts.append(_decode_payload(message))

    if plain_parts:
        return "\n".join(part for part in plain_parts if part.strip())
    return "\n".join(part for part in html_parts if part.strip())


def _parse_timestamp(message: Message) -> str:
    date_header = message.get("Date", "")
    try:
        return parsedate_to_datetime(date_header).isoformat()
    except Exception:
        return date_header


def _message_sort_time(message: Message) -> float:
    date_header = message.get("Date", "")
    try:
        parsed = parsedate_to_datetime(date_header)
        return parsed.timestamp()
    except Exception:
        return 0.0


def get_latest_brief_email() -> MailMessage | None:
    host = os.environ.get("OUTLOOK_IMAP_HOST") or os.environ.get("MAIL_IMAP_HOST") or "outlook.office365.com"
    port = int(os.environ.get("OUTLOOK_IMAP_PORT") or os.environ.get("MAIL_IMAP_PORT") or "993")
    username = _required_env("OUTLOOK_EMAIL", "MAIL_USERNAME")
    password = _required_env("OUTLOOK_PASSWORD", "MAIL_PASSWORD")
    folder = os.environ.get("OUTLOOK_IMAP_FOLDER") or os.environ.get("MAIL_IMAP_FOLDER") or "INBOX"
    subject = os.environ.get("MAIL_SEARCH_SUBJECT") or "Daily Hydrology Paper Brief"
    lookback_days = int(os.environ.get("MAIL_LOOKBACK_DAYS") or "14")

    since = (datetime.now() - timedelta(days=lookback_days)).strftime("%d-%b-%Y")
    messages: list[tuple[float, bytes, Message]] = []

    with imaplib.IMAP4_SSL(host, port) as client:
        client.login(username, password)
        client.select(folder)
        status, data = client.search(None, "SINCE", since)
        if status != "OK" or not data or not data[0]:
            return None

        for message_id in data[0].split():
            status, raw_data = client.fetch(message_id, "(RFC822)")
            if status != "OK" or not raw_data:
                continue
            raw_message = next(
                (item[1] for item in raw_data if isinstance(item, tuple) and item[1]),
                None,
            )
            if not raw_message:
                continue
            parsed = message_from_bytes(raw_message)
            decoded_subject = _decode_mime_header(parsed.get("Subject", ""))
            if subject.lower() not in decoded_subject.lower():
                continue
            messages.append((_message_sort_time(parsed), message_id, parsed))

    if not messages:
        return None

    _, message_id, latest = max(messages, key=lambda item: item[0])
    return MailMessage(
        message_id=message_id.decode("ascii", errors="replace"),
        subject=_decode_mime_header(latest.get("Subject", "")),
        body=_extract_body(latest),
        timestamp=_parse_timestamp(latest),
    )
