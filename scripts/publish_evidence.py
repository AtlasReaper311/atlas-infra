#!/usr/bin/env python3
"""Publish one validated evidence document to atlas-api-public."""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--kind", choices=("conformance", "chaos"), required=True)
    parser.add_argument("--file", required=True)
    parser.add_argument(
        "--url",
        default=os.getenv("ATLAS_EVIDENCE_URL", "https://api.atlas-systems.uk/v1/evidence"),
    )
    args = parser.parse_args()

    token = os.getenv("EVIDENCE_REPORT_KEY")
    if not token:
        print("EVIDENCE_REPORT_KEY is not set; skipping public evidence publish.")
        return 0

    path = Path(args.file)
    payload = json.loads(path.read_text(encoding="utf-8"))
    body = json.dumps(payload, separators=(",", ":")).encode("utf-8")
    request = urllib.request.Request(
        f"{args.url.rstrip('/')}/{args.kind}/report",
        data=body,
        method="POST",
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "User-Agent": "atlas-infra-evidence/1.0",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            result = json.load(response)
    except urllib.error.HTTPError as error:
        detail = error.read().decode("utf-8", errors="replace")
        print(f"Evidence publish failed: HTTP {error.code}: {detail}", file=sys.stderr)
        return 1
    except urllib.error.URLError as error:
        print(f"Evidence publish failed: {error}", file=sys.stderr)
        return 1

    print(
        f"Published {args.kind} evidence: "
        f"changed={result.get('changed')} fingerprint={result.get('fingerprint')}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
