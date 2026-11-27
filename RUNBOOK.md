# Daily run — make & schedule one Instagram reel

Repo: Shivam-Malik-Dev/evolve-videos (public; videos are served from raw.githubusercontent.com)
Buffer org: 6b09117649746287af4d2ab5 · Instagram channel: 6b092d878541f09ecbbde431 · YouTube channel: 6b092e9d8541f09ecbbdee6c (not used yet)

## 1. Setup (fresh machine)
```bash
pip install --break-system-packages -q edge-tts numpy pillow
mkdir -p ~/.fonts && cd ~/.fonts
for f in ofl/mukta/Mukta-ExtraBold.ttf ofl/mukta/Mukta-Bold.ttf; do
  curl -sfL -o "$(basename $f)" "https://raw.githubusercontent.com/google/fonts/main/$f"; done
fc-cache -f ~/.fonts
export PIXABAY_KEY=...   # given in the task prompt, never commit it
```
If edge-tts or Pixabay give SSL errors, the proxy CA is at ~/.ccr/ca-bundle.crt (make_reel.py already uses it if present).

## 2. Pick topic
Read STYLE.md, CONTENT_PLAN.md, topics_done.md and LEARNINGS.md (weekly data-driven rules; they override defaults). Choose the next phase-1 topic not already done
(alternate Ramayan / Mahabharat vs. the last entry). Research it with web search before writing.

## 3. Write spec
`specs/YYYY-MM-DD_<slug>.json` in the same format as `specs/barbarik.json` (voice hi-IN-MadhurNeural, rate +18%).

## 4. Render & check
```bash
python3 tools/make_reel.py specs/<file>.json /tmp/out.mp4
```
Extract ~10 frames (ffmpeg -ss ... -frames:v 1), hstack them, and LOOK at the grid with the Read tool.
Fix bad visuals (change queries/seed) and re-render. Check duration is 50–75 s.

## 5. Publish
```bash
cp /tmp/out.mp4 /tmp/YYYY-MM-DD_<slug>.mp4
tools/publish_media.sh /tmp/YYYY-MM-DD_<slug>.mp4      # uploads to the history-free "media" branch, prints raw URL + 200/206
# append a line to topics_done.md, commit the spec + log to main (NOT the video)
git add -A && git commit -m "Reel YYYY-MM-DD: <topic>" && git -c push.negotiate=true push
```
Buffer `create_post`: channelId 6b092d878541f09ecbbde431, schedulingType automatic, mode customScheduled,
dueAt = today 19:00 IST (+05:30) (if already past, shareNow), assets [{video:{url (the media-branch raw URL), metadata:{thumbnailOffset:1500}}}],
metadata.instagram = {type: reel, shouldShareToFeed: true, isAiGenerated: true}, caption per STYLE.md.

## 6. Report
Tell the owner (in Hindi/Hinglish): topic, scheduled time, video file (SendUserFile), and any problem.
