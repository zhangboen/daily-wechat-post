# daily-wechat-post

GitHub Actions automation for turning the latest Outlook `daily hydrology paper brief` email into a WeChat Official Account draft.

It runs every day at **08:00 Asia/Shanghai** (`0 0 * * *` UTC).

## What It Does

1. Reads the latest Outlook email matching `daily hydrology paper brief`.
2. Parses papers in email order.
3. Fills missing abstracts from DOI/Crossref/Semantic Scholar when possible.
4. Uses OpenAI to translate titles and write 2-3 sentence Chinese hydrology/hydroclimate summaries.
5. Builds a WeChat-compatible HTML article.
6. Creates a WeChat Official Account draft. It does **not** publish.

## Required GitHub Secrets

Add these in GitHub repository settings: `Settings -> Secrets and variables -> Actions -> New repository secret`.

| Secret | Required | Notes |
| --- | --- | --- |
| `OUTLOOK_EMAIL` | yes | Outlook mailbox that receives the daily brief. |
| `OUTLOOK_PASSWORD` | yes | Outlook password or app password for IMAP access. |
| `OUTLOOK_IMAP_HOST` | no | Defaults to `outlook.office365.com`. |
| `OUTLOOK_IMAP_PORT` | no | Defaults to `993`. |
| `OUTLOOK_IMAP_FOLDER` | no | Defaults to `INBOX`. |
| `MAIL_SEARCH_SUBJECT` | no | Defaults to `Daily Hydrology Paper Brief`. |
| `OPENAI_API_KEY` | yes | Used for Chinese title translation and summaries. |
| `WECHAT_APPID` | yes | WeChat Official Account AppID. |
| `WECHAT_SECRET` | yes | WeChat Official Account AppSecret. |
| `WECHAT_THUMB_MEDIA_ID` | no | Cover image media id. Defaults to the existing cover media id if omitted. |
| `OPENAI_MODEL` | no | Defaults to `gpt-4o-mini`. |
| `CONFIRMATION_SMTP_USERNAME` | yes | Gmail address used to send the success confirmation email. |
| `CONFIRMATION_SMTP_PASSWORD` | yes | Gmail app password for `CONFIRMATION_SMTP_USERNAME`. |
| `CONFIRMATION_EMAIL_TO` | no | Recipient address. Defaults to `CONFIRMATION_SMTP_USERNAME`. |
| `CONFIRMATION_EMAIL_FROM` | no | Sender address. Defaults to `CONFIRMATION_SMTP_USERNAME`. |

Do not commit `credentials.json`, `token.json`, AppSecret, or API keys.

## Success Confirmation Email

After a successful WeChat draft creation, the workflow sends a confirmation email through Gmail SMTP. For a Gmail account, create an app password in Google Account security settings and save it as `CONFIRMATION_SMTP_PASSWORD`; use the Gmail address as `CONFIRMATION_SMTP_USERNAME`. If `CONFIRMATION_EMAIL_TO` is omitted, the confirmation email is sent to the same Gmail account.

## Outlook IMAP Setup

The action reads the source brief from Outlook over IMAP. Save the mailbox and password as GitHub Actions secrets:

```powershell
gh secret set OUTLOOK_EMAIL --repo zhangboen/daily-wechat-post --body "boenzhang.gis@outlook.com"
gh secret set OUTLOOK_PASSWORD --repo zhangboen/daily-wechat-post --body "your-outlook-password-or-app-password"
```

If the mailbox uses a custom IMAP host, folder, or subject line, also set `OUTLOOK_IMAP_HOST`, `OUTLOOK_IMAP_PORT`, `OUTLOOK_IMAP_FOLDER`, or `MAIL_SEARCH_SUBJECT`.

## WeChat IP Whitelist

WeChat may reject GitHub Actions with `errcode 40164` if the runner IP is not in the Official Account IP whitelist. GitHub-hosted runner IPs can change, so for reliable WeChat API calls you may need either:

- a self-hosted GitHub Actions runner on a stable whitelisted IP, or
- a stable proxy/server whose IP is whitelisted.

The workflow prints the current GitHub runner public IP before calling the WeChat API. If you see `errcode 40164`, add that printed IP to the WeChat Official Account IP whitelist and re-run the workflow. This is a temporary fix because GitHub-hosted runner IPs may change on future runs.

## Manual Run

In GitHub, open `Actions -> daily-wechat-post -> Run workflow`.

## Local Smoke Test

After setting environment variables locally:

```powershell
python -m pip install -r requirements.txt
python main.py --dry-run
```
