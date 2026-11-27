# YouTube channel EVOLVEUNFILTERED — daily run

Buffer YouTube channel: 6b092e9d8541f09ecbbdee6c · Buffer org: 6b09117649746287af4d2ab5
Approved reference: specs/youtube/harshad_mehta.json → https://www.youtube.com/watch?v=SOgLEvSo2DA
Teaser-short reference: specs/youtube/harshad_short.json

## What to make (by weekday, IST)
- **Tuesday, Thursday, Saturday** → ONE long video (8.5–10 min) + ONE teaser Short for it.
  Long video publishes 18:00 IST, teaser Short 19:30 IST.
- **Sunday, Monday, Wednesday, Friday** → ONE standalone Short (30–50 s), publishes 18:30 IST.

## Niche & topics (owner chose: "paise aur business ki kahaniyan")
India-related money / business / scam / company rise-and-fall stories, told as a gripping documentary in simple Hindi.
Prefer topics people are SEARCHING or that are TRENDING right now: check web/news for current business news in India
(IPO, scam, company collapse, big acquisition, budget, famous founder in news) and vidIQ keyword research / trending
(vidIQ free credits are limited — use at most 1–2 cheap calls per run). Evergreen examples: Satyam scam, Amul's story,
Nirma vs HUL, Kingfisher/Vijay Mallya, Jet Airways, Byju's rise & fall, Sahara, Ketan Parekh, Dhirubhai's start,
Tata Nano, Paytm, Zomato IPO, Nokia in India, Maggi ban 2015, Hindenburg vs Adani (stick strictly to documented facts).
Never repeat a topic in yt_topics_done.md. Standalone Shorts: one surprising money/business fact or mini-story with a twist.

## Safety rules (copyright + legal)
- Only Pixabay footage/images (royalty-free), our own generated graphics (tools/viz.py) and generated music. NEVER use film/TV/news
  clips, songs, logos as main visuals, or photos of real people.
- Real people/companies: only facts from reliable reports (court records, RBI/SEBI, major newspapers). Use "आरोप", "रिपोर्टों के मुताबिक़"
  for anything not proven in court. No insults, no speculation. Add sources + "निवेश सलाह नहीं" disclaimer in description.
- Set isAiGenerated true, madeForKids false.

## Long video recipe
1. Setup as RUNBOOK.md §1. Research the topic (web search; at least 3 sources). Note exact numbers/dates.
2. Write specs/youtube/YYYY-MM-DD_<slug>.json like harshad_mehta.json: hook intro (question / shocking fact), 5–6 chapters,
   ~1,450–1,700 words total, rate "+0%", simple analogies, twist, lesson, comment question CTA. 30–40% of blocks use "viz"
   (chart / flow / headline / text) for numbers, mechanisms, dates. Broll queries India-specific ("india city", "mumbai",
   "indian rupee", "india people", "stock market", "india night"...). Add "avoid_tags": ["aarti","temple","religion","wedding","hindu"] for business topics.
3. `python3 tools/make_doc.py <spec> /tmp/long.mp4` (takes ~20 min; run it with nohup in background and poll). Must be ≥ 8:10.
   Check a 16-frame grid; fix off-topic/foreign/blank shots (change queries/seed) and re-render if needed.
4. Thumbnail: pick a clean frame from a source clip in the _work dir (no captions), then
   `python3 tools/thumbnail.py bg.png thumb.png "<BIG LINE ≤12 chars>" "<line 2>" "<red tag>" down|up|none`.
   Prepend it as a 1-second first frame (see below) so thumbnailOffset 500 shows it.
   ffmpeg: make 1 s clip from thumb.png (+silent stereo 44.1k), concat with the video (re-encode crf 25, maxrate 1400k).
5. Teaser Short: spec like harshad_short.json (35–45 s, cliffhanger, CTA "पूरी कहानी हमारे चैनल पर"), render with tools/make_reel.py.
6. Upload: `tools/publish_media.sh /tmp/YYYY-MM-DD_<slug>.mp4 /tmp/YYYY-MM-DD_<slug>-short.mp4` → raw URLs (must print 200/206).
7. Buffer create_post (YouTube): long = type regularVideo, title (≤100 chars, English keyword + Hindi hook), categoryId "27",
   privacy public, madeForKids false, isAiGenerated true, assets video thumbnailOffset 500, customScheduled 18:00 IST.
   Description: 2-line summary, what you'll learn, ⏱️ chapters from the *_chapters.txt file (+1 s shift because of the thumbnail
   frame), comment question, subscribe line, 📚 sources, ⚠️ disclaimer, 5–8 hashtags.
   Teaser short = type short, customScheduled 19:30 IST, title ends with #shorts.
8. Append to yt_topics_done.md, commit specs + log to main (not the videos). Report to owner with SendUserMessage + SendUserFile (thumbnail).
