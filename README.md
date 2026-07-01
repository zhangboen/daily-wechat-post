# daily-wechat-post

GitHub Actions automation for publishing an already generated WeChat HTML article as a WeChat Official Account draft.

This repo no longer reads Gmail/Outlook, parses papers, or calls OpenAI. Those steps belong to `zhangboen/hydrology-paper-brief`, which generates:

```text
outputs/wechat-post-YYYY-MM-DD.html
outputs/wechat-post-YYYY-MM-DD.json
```

`daily-wechat-post` only fetches those files and calls the WeChat draft API.

It runs every day at **07:50 Asia/Shanghai** (`50 23 * * *` UTC), after the paper brief workflow has had time to generate the HTML.

## Required GitHub Secrets

Add these in GitHub repository settings: `Settings -> Secrets and variables -> Actions -> New repository secret`.

| Secret | Required | Notes |
| --- | --- | --- |
| `WECHAT_APPID` | yes | WeChat Official Account AppID. |
| `WECHAT_SECRET` | yes | WeChat Official Account AppSecret. |
| `WECHAT_THUMB_MEDIA_ID` | no | Cover image media id. Defaults to the existing cover media id if omitted. |
| `WECHAT_HTML_SOURCE_BASE_URL` | no | Defaults to `https://raw.githubusercontent.com/zhangboen/hydrology-paper-brief/main/outputs`. |
| `CONFIRMATION_SMTP_USERNAME` | yes | Email account used to send the success confirmation email. |
| `CONFIRMATION_SMTP_PASSWORD` | yes | SMTP password or app password. |
| `CONFIRMATION_EMAIL_TO` | no | Recipient address. Defaults to `CONFIRMATION_SMTP_USERNAME`. |
| `CONFIRMATION_EMAIL_FROM` | no | Sender address. Defaults to `CONFIRMATION_SMTP_USERNAME`. |

Do not commit AppSecret, SMTP passwords, or API keys.

## Source Files

By default, for date `2026-07-01`, this repo fetches:

```text
https://raw.githubusercontent.com/zhangboen/hydrology-paper-brief/main/outputs/wechat-post-2026-07-01.html
https://raw.githubusercontent.com/zhangboen/hydrology-paper-brief/main/outputs/wechat-post-2026-07-01.json
```

The JSON provides the WeChat draft title and digest. The HTML provides the article body.

## Manual Run

In GitHub, open `Actions -> daily-wechat-post -> Run workflow`.

For local dry run:

```powershell
python -m pip install -r requirements.txt
python main.py --date 2026-07-01 --dry-run
```

For local draft creation, set `WECHAT_APPID`, `WECHAT_SECRET`, and optionally `WECHAT_THUMB_MEDIA_ID`, then run:

```powershell
python main.py --date 2026-07-01
```

## WeChat IP Whitelist

WeChat may reject API calls with `errcode 40164` if the runner IP is not in the Official Account IP whitelist. Use a self-hosted GitHub Actions runner on a stable VPS IP, and add that IP to the WeChat Official Account backend.
