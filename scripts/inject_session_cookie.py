#!/usr/bin/env python3
"""
Add a Django session cookie to the authenticated URLs in a Pa11y CI config.

URLs are treated as authenticated if they have `"authenticated": true`.

Usage: inject_session_cookie.py <session_key> [config_path] [cookie_name]
"""

import json
import sys
from pathlib import Path


def inject_cookie(config_path: Path, session_key: str, cookie_name: str) -> None:
    config = json.loads(config_path.read_text())
    cookie = {"name": cookie_name, "value": session_key, "domain": "localhost"}

    for url_config in config.get("urls", []):
        if isinstance(url_config, dict) and url_config.pop("authenticated", False):
            url_config.setdefault("page", {}).setdefault("setCookie", []).append(cookie)

    config_path.write_text(json.dumps(config, indent=2))


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    path = Path(sys.argv[2] if len(sys.argv) > 2 else ".pa11yci.json")
    if not path.exists():
        sys.exit(f"Configuration file not found: {path}")
    inject_cookie(path, sys.argv[1], sys.argv[3] if len(sys.argv) > 3 else "sessionid")
