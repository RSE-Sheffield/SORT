#!/usr/bin/env python3
"""
Script to inject Django session cookie into Pa11y CI configuration.
This allows Pa11y to test authenticated pages during accessibility testing.
"""
import json
import sys
from pathlib import Path


def inject_cookie(config_path: str, session_key: str, cookie_name: str = "sessionid"):
    """
    Inject session cookie into Pa11y CI configuration file.

    Args:
        config_path: Path to .pa11yci.json configuration file
        session_key: Django session key value
        cookie_name: Name of the session cookie (default: "sessionid")
    """
    config_file = Path(config_path)

    if not config_file.exists():
        print(f"Error: Configuration file not found: {config_path}", file=sys.stderr)
        sys.exit(1)

    # Load existing configuration
    with open(config_file, 'r') as f:
        config = json.load(f)

    # Prepare cookie configuration
    cookie_config = {
        "name": cookie_name,
        "value": session_key,
        "domain": "localhost"
    }

    # Inject cookies into each URL configuration
    if "urls" in config and isinstance(config["urls"], list):
        for url_config in config["urls"]:
            if isinstance(url_config, dict):
                # Add cookie to each URL that needs authentication
                # (URLs with "actions" key are typically authenticated pages)
                if "actions" in url_config or "myorganisation" in url_config.get("url", ""):
                    if "page" not in url_config:
                        url_config["page"] = {}
                    if "setCookie" not in url_config["page"]:
                        url_config["page"]["setCookie"] = []
                    url_config["page"]["setCookie"].append(cookie_config)

    # Write updated configuration
    with open(config_file, 'w') as f:
        json.dump(config, f, indent=2)

    print(f"✓ Injected session cookie into {config_path}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: inject_session_cookie.py <session_key> [config_path] [cookie_name]")
        print("Example: inject_session_cookie.py abc123xyz .pa11yci.json sessionid")
        sys.exit(1)

    session_key = sys.argv[1]
    config_path = sys.argv[2] if len(sys.argv) > 2 else ".pa11yci.json"
    cookie_name = sys.argv[3] if len(sys.argv) > 3 else "sessionid"

    inject_cookie(config_path, session_key, cookie_name)
