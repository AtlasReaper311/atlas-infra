#!/usr/bin/env bash
set -euo pipefail

TARGET="${1:-https://atlas-systems.uk}"

echo "Checking $TARGET..."

STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$TARGET")

if [ "$STATUS" -eq 200 ]; then
    echo "OK — $TARGET returned $STATUS"
    exit 0
else
    echo "FAIL — $TARGET returned $STATUS"
    exit 1
fi