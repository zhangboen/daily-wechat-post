from __future__ import annotations

import json
from pathlib import Path

from google_auth_oauthlib.flow import InstalledAppFlow


SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]


def main() -> int:
    credentials_path = Path("credentials.json")
    token_path = Path("token.json")

    if not credentials_path.exists():
        raise SystemExit(
            "Missing credentials.json. Download an OAuth Desktop client JSON "
            "from Google Cloud Console and save it as credentials.json."
        )

    flow = InstalledAppFlow.from_client_secrets_file(str(credentials_path), SCOPES)
    credentials = flow.run_local_server(port=0)
    token_path.write_text(credentials.to_json(), encoding="utf-8")

    token = json.loads(credentials.to_json())
    if not token.get("refresh_token"):
        raise SystemExit(
            "token.json was created, but it does not contain refresh_token. "
            "Delete token.json and try again, making sure to approve offline access."
        )

    print("Created token.json.")
    print("Now run:")
    print("  gh secret set GMAIL_TOKEN_JSON --repo zhangboen/daily-wechat-post --body-file token.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
