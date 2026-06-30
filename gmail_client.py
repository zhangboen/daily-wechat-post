from __future__ import annotations

import base64
import json
import os
from dataclasses import dataclass
from email.utils import parsedate_to_datetime

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

from config import GMAIL_QUERIES


SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]


@dataclass
class GmailMessage:
    message_id: str
    subject: str
    body: str
    timestamp: str


def _load_credentials() -> Credentials:
    token_json = os.environ.get("GMAIL_TOKEN_JSON")
    if not token_json:
        raise RuntimeError("Missing GMAIL_TOKEN_JSON secret.")
    token_info = json.loads(token_json)
    return Credentials.from_authorized_user_info(token_info, SCOPES)


def _decode_body_part(data: str | None) -> str:
    if not data:
        return ""
    padded = data + "=" * (-len(data) % 4)
    return base64.urlsafe_b64decode(padded.encode("utf-8")).decode("utf-8", errors="replace")


def _extract_body(payload: dict) -> str:
    if payload.get("body", {}).get("data"):
        return _decode_body_part(payload["body"]["data"])

    parts = payload.get("parts") or []
    plain_text = []
    html_text = []
    stack = list(parts)
    while stack:
        part = stack.pop(0)
        stack.extend(part.get("parts") or [])
        mime_type = part.get("mimeType", "")
        data = part.get("body", {}).get("data")
        if mime_type == "text/plain":
            plain_text.append(_decode_body_part(data))
        elif mime_type == "text/html":
            html_text.append(_decode_body_part(data))
    if plain_text:
        return "\n".join(plain_text)
    return "\n".join(html_text)


def _header(headers: list[dict], name: str) -> str:
    for header in headers:
        if header.get("name", "").lower() == name.lower():
            return header.get("value", "")
    return ""


def get_latest_brief_email() -> GmailMessage | None:
    service = build("gmail", "v1", credentials=_load_credentials(), cache_discovery=False)
    best: tuple[int, str] | None = None
    for query in GMAIL_QUERIES:
        result = service.users().messages().list(userId="me", q=query, maxResults=5).execute()
        for item in result.get("messages", []):
            message = service.users().messages().get(userId="me", id=item["id"], format="metadata").execute()
            internal_date = int(message.get("internalDate", "0"))
            if best is None or internal_date > best[0]:
                best = (internal_date, item["id"])

    if best is None:
        return None

    message = service.users().messages().get(userId="me", id=best[1], format="full").execute()
    payload = message.get("payload", {})
    headers = payload.get("headers", [])
    date_header = _header(headers, "Date")
    try:
        timestamp = parsedate_to_datetime(date_header).isoformat()
    except Exception:
        timestamp = str(message.get("internalDate", ""))
    return GmailMessage(
        message_id=message["id"],
        subject=_header(headers, "Subject"),
        body=_extract_body(payload),
        timestamp=timestamp,
    )
