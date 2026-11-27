# YouTube channel EVOLVEUNFILTERED — daily run

Buffer YouTube channel: 6b092e9d8541f09ecbbdee6c · Buffer org: 6b09117649746287af4d2ab5 · vidIQ channelId: UCiGqUtRH0SXG-AVlFZC5X1Q
Approved references: specs/youtube/harshad_mehta.json (long) → https://www.youtube.com/watch?v=SOgLEvSo2DA, specs/youtube/harshad_short.json (Short)

## Schedule (owner decided 2026-11-27, IST) — kept light to save plan usage
- **Wednesday & Saturday**: ONE long video (8:10–10 min) published 18:00 + ONE teaser Short for it published 09:00
  ("आज शाम 6 बजे पूरी कहानी" style cliffhanger). The custom thumbnail is set by a separate 18:23 task.
- **All other days**: ONE standalone Short (35–50 s) published 18:30.

## Niche & topics
India AND world: untold / lesser-known true stories, mysteries, history, scams & business stories, science & "how it works",
and explainers on what is trending right now (news everyone is searching). Educational, gripping, documentary style like the
Harshad Mehta video. Pick what people are SEARCHING now: web/news search for India's trending topics today; optionally 1 vidIQ
keyword/trending call (credits are limited — keep ≥ 25 for thumbnails). Never repeat yt_topics_done.md. Mix categories across the week.

## Voice & music
Follow VOICE.md: Parler, speaker Aman, music "doc_bg.mp3" (music_volume 0.8). Long-video rate setting is ignored by Parler;
pace comes from moods — use shock/tense/sad/warm generously so the delivery changes with the script.
A 9-minute long video takes ~2 hours to render: start it early (background + poll). Make the teaser Short FIRST (it publishes 09:00).

## Learnings
Read LEARNINGS.md (weekly data-driven rules) before choosing topics; it overrides defaults here.

## Safety rules (copyright + legal)
- Only Pixabay footage/images, our own graphics (tools/viz.py), our generated music. NEVER film/TV/news clips, songs, logos as main
  visuals, or photos of real people.
- Real people/companies: only documented facts (court records, regulators, major newspapers). "आरोप"/"रिपोर्टों के मुताबिक़" for
  anything unproven. Sources + disclaimer in description. isAiGenerated true, madeForKids false.

## Long video recipe
1. Research (≥3 sources), note exact numbers/dates.
2. Spec specs/youtube/YYYY-MM-DD_<slug>.json like harshad_mehta.json + "engine":"parler","speaker":"Aman","music":"doc_bg.mp3":
   hook (question/shocking fact), 5–6 chapters, ~1,350–1,600 words, simple analogies, twist, lesson. 30–40% of blocks with "viz"
   (chart/flow/headline/text). India-specific broll queries where the story is Indian. "avoid_tags" for off-topic imagery.
   End CTA (mood cta): ask a comment question + "वीडियो पसंद आई तो लाइक करो, चैनल को सब्सक्राइब करो और बेल आइकन दबाओ".
3. `nohup python3 tools/make_doc.py <spec> /tmp/long.mp4 > /tmp/long.log 2>&1 &` and poll. Must be ≥ 8:10. Check a 16-frame grid; fix bad shots.
4. Thumbnail: clean frame from a source clip in the _work dir → `python3 tools/thumbnail.py bg.png thumb.png "<BIG ≤12 chars>" "<line 2>" "<red tag>" down|up|none`.
   Prepend as 1-second first frame (1 s clip + silent stereo 44.1k, concat, re-encode crf 25 maxrate 1400k). Also publish thumb_1280 as
   YYYY-MM-DD_<slug>-thumb.png via publish_media.sh (the 18:23 task uses it).
5. `tools/publish_media.sh` the long mp4 (+ thumb png). Buffer create_post: type regularVideo, title ≤100 (English keyword + Hindi hook),
   categoryId "27", privacy public, madeForKids false, isAiGenerated true, thumbnailOffset 500, **customScheduled 18:00 IST**.
   Description: summary, what you'll learn, ⏱️ chapters (+1 s shift), comment question, subscribe line, 📚 sources, ⚠️ disclaimer, hashtags.

## Shorts recipe (teaser or standalone)
Spec like harshad_short.json + engine parler/Aman + music doc_bg.mp3; 35–50 s; hook in first 2 s; one surprising fact/twist.
Teaser CTA: "पूरी कहानी आज शाम 6 बजे, हमारे चैनल पर — सब्सक्राइब कर लो ताकि छूटे नहीं".
Standalone CTA: comment question + "ऐसी ही कहानियों के लिए सब्सक्राइब करो". Render with make_reel.py.
Buffer: type short, title ends with #shorts, categoryId "27", madeForKids false, isAiGenerated true, customScheduled (09:00 teaser / 18:30 standalone).

## After posting
Append to yt_topics_done.md, commit specs/log to main (never videos). Report to owner (SendUserMessage) incl. what's scheduled when.
