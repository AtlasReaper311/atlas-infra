#!/usr/bin/env python3
"""Send one compact assurance report through atlas-notify."""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.request
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--title", required=True)
    parser.add_argument("--message", required=True)
    parser.add_argument("--level", choices=("info", "warning", "failure"), required=True)
    parser.add_argument("--url", default="")
    args = parser.parse_args()

    token = os.getenv("NOTIFY_TOKEN", "")
    if not token:
        print("NOTIFY_TOKEN is not set. Skipping atlas-notify delivery.")
        return 0
    payload = json.dumps(
        {
            "source": "alert",
            "level": args.level,
            "title": args.title,
            "message": args.message[:900],
            "url": args.url,
            "persist_only": True,
        }
    ).encode("utf-8")
    request = urllib.request.Request(
        "https://api.atlas-systems.uk/notify",
        data=payload,
        method="POST",
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "User-Agent": "atlas-estate-assurance/1.0",
        },
    )
    with urllib.request.urlopen(request, timeout=20) as response:
        if response.status >= 300:
            raise RuntimeError(f"atlas-notify returned {response.status}")
    print("Posted assurance report to atlas-notify.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
