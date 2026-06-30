from __future__ import annotations

import json
import os
from dataclasses import dataclass

import requests

from config import DEFAULT_THUMB_MEDIA_ID


TOKEN_URL = "https://api.weixin.qq.com/cgi-bin/token"
DRAFT_ADD_URL = "https://api.weixin.qq.com/cgi-bin/draft/add"


@dataclass
class WeChatDraftResult:
    media_id: str | None
    raw: dict


def _request_json(method: str, url: str, **kwargs) -> dict:
    response = requests.request(method, url, timeout=60, **kwargs)
    response.raise_for_status()
    return response.json()


def get_access_token() -> str:
    appid = os.environ.get("WECHAT_APPID")
    secret = os.environ.get("WECHAT_SECRET")
    if not appid or not secret:
        raise RuntimeError("Missing WECHAT_APPID or WECHAT_SECRET.")

    result = _request_json(
        "GET",
        TOKEN_URL,
        params={
            "grant_type": "client_credential",
            "appid": appid,
            "secret": secret,
        },
    )
    token = result.get("access_token")
    if not token:
        raise RuntimeError(f"Failed to get WeChat access_token: {json.dumps(result, ensure_ascii=False)}")
    return token


def create_draft(title: str, html: str, digest: str) -> WeChatDraftResult:
    token = get_access_token()
    thumb_media_id = os.environ.get("WECHAT_THUMB_MEDIA_ID") or DEFAULT_THUMB_MEDIA_ID
    article = {
        "title": title,
        "thumb_media_id": thumb_media_id,
        "author": os.environ.get("WECHAT_AUTHOR", "Hiboorn"),
        "digest": digest[:120],
        "content": html,
        "need_open_comment": 0,
        "only_fans_can_comment": 0,
    }
    result = _request_json(
        "POST",
        DRAFT_ADD_URL,
        params={"access_token": token},
        json={"articles": [article]},
    )
    if result.get("errcode"):
        raise RuntimeError(f"Failed to create WeChat draft: {json.dumps(result, ensure_ascii=False)}")
    return WeChatDraftResult(media_id=result.get("media_id"), raw=result)
