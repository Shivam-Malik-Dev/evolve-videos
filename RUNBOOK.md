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

## 1b. Voice
Follow VOICE.md (Parler, speaker Aman). Evening story reels use music devotional_bg.mp3, bells false.

## 2. Pick topic
Read STYLE.md, CONTENT_PLAN.md, topics_done.md and LEARNINGS.md (weekly data-driven rules; they override defaults). Choose the next phase-1 topic not already done
(alternate Ramayan / Mahabharat vs. the last entry). Research it with web search before writing.

## 3. Write spec
`specs/YYYY-MM-DD_<slug>.json` in the same format as `specs/barbarik.json`, plus "engine": "parler", "speaker": "Aman", "music": "devotional_bg.mp3".

## 3b. Cover (owner request) — every evening reel gets its own cover
Add "cover": {"kind": "story", "bg": "id:<pixabay id>", "line1": "<big hook ≤ 14 chars>", "line2": "<line 2>", "tag": "<series tag, e.g. महाभारत की अनसुनी कहानी / रामायण की अनसुनी कहानी>"}.
Pick a dramatic, on-topic image (look at it first). Good epic art ids: 9252303, 9252305, 9252309 (warrior archer),
9252299 (Krishna & Arjun at war), 9252314 (Ram on horse in battle), 8674031 (Krishna), 8598225 / 8797246 (Hanuman), 8537288 (warrior king).
Use the printed cover_offset_ms as Buffer thumbnailOffset.

## 4. Render & check
```bash
nohup python3 tools/make_reel.py specs/<file>.json /tmp/out.mp4 > /tmp/render.log 2>&1 &   # ~12 min with Parler; poll
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
dueAt = today 19:00 IST (+05:30) (if already past, shareNow), assets [{video:{url (the media-branch raw URL), metadata:{thumbnailOffset: cover_offset_ms}}}],
metadata.instagram = {type: reel, shouldShareToFeed: true, isAiGenerated: true}, caption per STYLE.md.

## 6. Report
Tell the owner (in Hindi/Hinglish): topic, scheduled time, video file (SendUserFile), and any problem.
