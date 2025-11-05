#!/usr/bin/env bash
set -euo pipefail

# === CONFIG ===
API_KEY="api_key"
IMMICH_URL="http://ip_addr:port"
ALBUM_ID="album_id"
DEST_DIR="path"
PAGE_SIZE=1000
# ======================

mkdir -p "$DEST_DIR"
echo "Fetching list of assets from album ID: $ALBUM_ID"

# Loop through pages
PAGE=1
while true; do
  echo "Page $PAGE ..."
  RESPONSE=$(curl -s -H "x-api-key: $API_KEY" \
    -H "Content-Type: application/json" \
    -X POST "$IMMICH_URL/api/search/metadata" \
    -d "{\"albumIds\":[\"$ALBUM_ID\"],\"page\":$PAGE,\"size\":$PAGE_SIZE}")

  ASSET_COUNT=$(echo "$RESPONSE" | jq -r '.assets.items | length')
  if [[ "$ASSET_COUNT" -lt 1 ]]; then
    echo "No more assets found. Exiting."
    break
  fi

  echo "Found $ASSET_COUNT assets on this page."

  echo "$RESPONSE" | jq -r '.assets.items[] | "\(.id) \t \(.originalFileName)"' | \
  while IFS=$'\t' read -r ASSET_ID FILENAME; do
    FILENAME=$(echo "$FILENAME" | xargs)
    OUTPUT_PATH="$DEST_DIR/$FILENAME"
    if [[ -f "$OUTPUT_PATH" ]]; then
      echo "Skipping existing: $FILENAME"
      continue
    fi
    echo "Downloading: $FILENAME"
    curl -s -H "x-api-key: $API_KEY" \
      -L "$IMMICH_URL/api/assets/$ASSET_ID/download" \
      -o "$OUTPUT_PATH"
    if [[ $? -ne 0 ]]; then
      echo "ERROR downloading $FILENAME"
    else
      echo "Saved: $FILENAME"
    fi
  done

  PAGE=$((PAGE + 1))
done

echo "All done. Files saved in: $DEST_DIR"
