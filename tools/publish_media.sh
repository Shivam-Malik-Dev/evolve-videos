#!/usr/bin/env bash
# Upload finished videos to the orphan "media" branch (no history kept, so the repo never grows).
# Keeps files from the last KEEP_DAYS days (by filename date prefix YYYY-MM-DD_), adds the new ones,
# force-pushes, and prints the public raw URL of each new file.
# Usage: tools/publish_media.sh /path/to/2026-11-27_name.mp4 [more files...]
set -euo pipefail
REPO_URL=https://github.com/Shivam-Malik-Dev/evolve-videos
KEEP_DAYS=${KEEP_DAYS:-5}
TMP=$(mktemp -d)
cd "$TMP"
git init -q -b media && git remote add origin "$REPO_URL"
git config user.name "Shivam-Malik-Dev"; git config user.email "shivammalik.work@gmail.com"
if git fetch -q --depth 1 origin media 2>/dev/null; then git checkout -q FETCH_HEAD -- . 2>/dev/null || true; fi
cutoff=$(date -d "-${KEEP_DAYS} days" +%Y-%m-%d)
shopt -s nullglob; for f in *.mp4 *.png; do
  [ -e "$f" ] || continue
  d=${f:0:10}; [[ "$d" < "$cutoff" ]] && rm -f "$f"
done
for src in "$@"; do cp "$src" .; done
git add -A && git commit -q -m "media $(date +%F_%H%M)"
git -c http.postBuffer=524288000 push -q -f origin media
for src in "$@"; do
  name=$(basename "$src")
  url="https://raw.githubusercontent.com/Shivam-Malik-Dev/evolve-videos/media/$name"
  for i in 1 2 3 4 5 6; do code=$(curl -s -o /dev/null -w "%{http_code}" -r 0-0 "$url"); [ "$code" = "206" -o "$code" = "200" ] && break; sleep 5; done
  echo "$url $code"
done
rm -rf "$TMP"
