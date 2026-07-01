import json
import os
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from config import DEFAULT_THUMB_MEDIA_ID


TOKEN_URL = "https://api.weixin.qq.com/cgi-bin/token"
DRAFT_ADD_URL = "https://api.weixin.qq.com/cgi-bin/draft/add"


class WeChatDraftResult:
    def __init__(self, media_id, raw):
        self.media_id = media_id
        self.raw = raw


def _request_json(method, url, params=None, payload=None):
    if params:
        url = "%s?%s" % (url, urlencode(params))
    data = None
    headers = {}
    if payload is not None:
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        headers["Content-Type"] = "application/json; charset=utf-8"
    request = Request(url, data=data, headers=headers, method=method)
    with urlopen(request, timeout=60) as response:
        return json.loads(response.read().decode("utf-8"))


def get_access_token():
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
        raise RuntimeError("Failed to get WeChat access_token: %s" % json.dumps(result, ensure_ascii=False))
    return token


def create_draft(title, html, digest):
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
        payload={"articles": [article]},
    )
    if result.get("errcode"):
        raise RuntimeError("Failed to create WeChat draft: %s" % json.dumps(result, ensure_ascii=False))
    return WeChatDraftResult(media_id=result.get("media_id"), raw=result)
