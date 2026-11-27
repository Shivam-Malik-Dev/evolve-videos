# EVOLVEUNFILTERED — Reel style guide (approved by owner)

Reference reel that the owner approved: `specs/barbarik.json` → https://www.instagram.com/reel/DgPVsM6RPIe/
Copy its structure, pacing and tone. Voice setup is final: `hi-IN-MadhurNeural`, rate `+18%`.

## Audience & topics
- Audience is Indian. EVERY topic must be India-related (Ramayan, Mahabharat, Puran, Indian history, Indian mysteries, Indian saints/warriors/temples, Indian psychology-style life lessons).
- Story must be enjoyable for kids and adults: clear, gripping, no gore, respectful to deities and faiths.
- Facts: research first. Legends/folk versions are said with "कहते हैं" / "कथा के अनुसार". Never invent numbers or dates.

## Topic must be INTERESTING (owner's #1 rule)
Before writing, list 5 candidate stories and score each 1–10 on: (a) surprise/twist most people don't know,
(b) can the hook be a shocking question, (c) emotion (fear, awe, sadness, injustice), (d) would people send it to someone.
Pick the highest total (must be ≥ 32/40). Avoid plain well-known moral tales told flatly; if a story is famous,
tell its least-known angle (e.g. "Ravan ki wo baat jo Ram ne Lakshman ko seekhne bheja").
The account is a STORY channel, not a devotional channel: tone = cinematic storyteller / mystery narrator, not bhajan.
Devotional comment CTAs ("जय श्री राम") only when it fits naturally — otherwise ask an opinion question
("तुम्हारे हिसाब से गलती किसकी थी? कमेंट में बताओ").

## Script rules (Devanagari only — Roman Hindi makes the voice mispronounce)
1. Open with a curiosity QUESTION (hook block, 1 sentence).
2. Always name who is speaking/acting ("श्रीकृष्ण ने कहा", "भीम का पोता") — never vague words like "भाई कहता है" without saying whose.
3. Short natural sentences. Put commas where a speaker breathes. Use "..." only 1–2 times for drama.
4. Write numbers as words ("चौरासी साल", "उन्नीस सौ सत्तावन").
5. Simple everyday Hindi; avoid heavy Sanskrit unless explained.
6. A twist / "असली बात" moment in the middle-late part (mood `shock`).
7. A lesson that people relate to in their own life.
8. End (mood `cta`): ask to SEND the reel to a specific kind of person + ask for a one-line comment
   e.g. "ये कहानी उस इंसान को भेजो जो... और कमेंट में लिखो, जय श्री राम।"
9. Total length 55–70 seconds (≈170–200 words).

## Blocks & moods (make_reel.py)
hook → neutral → warm/tense → shock → sad/warm → cta. Each block = 1–4 sentences (one TTS call, so speech flows).

## Visuals (broll)
- Deities: `img:krishna`, `img:shiva`, `img:hanuman`, `img:ram`, `img:ganesha` etc. (Pixabay images, single-word queries work best).
- Atmosphere videos: "storm clouds dark", "fire flames", "smoke dark", "candle dark", "diya", "sunset hill", "river ganga", "temple india".
- `img:ancient india`, `img:hindu temple`, `img:diya` for places.
- AFTER rendering, extract ~10 frames into a grid and LOOK at it. Replace any cartoon/off-topic/foreign-looking/black frame by changing that block's queries or `seed`, then re-render.

## Caption template (Instagram)
Line 1: hook in Hindi with an emoji. Line 2–3: 1-sentence summary. Then share + comment ask. Then 8–10 hashtags
(topic tags + #sanatandharma #hindumythology #indianhistory #evolveunfiltered). Always set isAiGenerated: true.
