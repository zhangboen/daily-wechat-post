# daily-wechat-post

GitHub Actions automation for turning the latest Gmail `daily hydrology paper brief` email into a WeChat Official Account draft.

It runs every day at **08:30 Asia/Shanghai** (`30 0 * * *` UTC).

## What It Does

1. Reads the latest Gmail email matching `daily hydrology paper brief`.
2. Parses papers in email order.
3. Fills missing abstracts from DOI/Crossref/Semantic Scholar when possible.
4. Uses OpenAI to translate titles and write 2-3 sentence Chinese hydrology/hydroclimate summaries.
5. Builds a WeChat-compatible HTML article.
6. Creates a WeChat Official Account draft. It does **not** publish.

## Required GitHub Secrets

Add these in GitHub repository settings: `Settings -> Secrets and variables -> Actions -> New repository secret`.

| Secret | Required | Notes |
| --- | --- | --- |
| `GMAIL_TOKEN_JSON` | yes | OAuth token JSON for Gmail API with `gmail.readonly` scope. |
| `OPENAI_API_KEY` | yes | Used for Chinese title translation and summaries. |
| `WECHAT_APPID` | yes | WeChat Official Account AppID. |
| `WECHAT_SECRET` | yes | WeChat Official Account AppSecret. |
| `WECHAT_THUMB_MEDIA_ID` | no | Cover image media id. Defaults to the existing cover media id if omitted. |
| `OPENAI_MODEL` | no | Defaults to `gpt-4o-mini`. |

Do not commit `credentials.json`, `token.json`, AppSecret, or API keys.

## Gmail OAuth Token

The action needs a Gmail OAuth token that can refresh itself. The token JSON should include a `refresh_token`.

Expected secret shape:

```json
{
  "token": "...",
  "refresh_token": "...",
  "token_uri": "https://oauth2.googleapis.com/token",
  "client_id": "...",
  "client_secret": "...",
  "scopes": ["https://www.googleapis.com/auth/gmail.readonly"]
}
```

## WeChat IP Whitelist

WeChat may reject GitHub Actions with `errcode 40164` if the runner IP is not in the Official Account IP whitelist. GitHub-hosted runner IPs can change, so for reliable WeChat API calls you may need either:

- a self-hosted GitHub Actions runner on a stable whitelisted IP, or
- a stable proxy/server whose IP is whitelisted.

## Manual Run

In GitHub, open `Actions -> daily-wechat-post -> Run workflow`.

## Local Smoke Test

After setting environment variables locally:

```powershell
python -m pip install -r requirements.txt
python main.py --dry-run
```
