# EVOLVEUNFILTERED — Reel style guide (approved by owner)

Reference reel that the owner approved: `specs/barbarik.json` → https://www.instagram.com/reel/DgPVsM6RPIe/
Copy its structure, pacing and tone. Voice setup is final: `hi-IN-MadhurNeural`, rate `+18%`.

## Audience & topics
- Audience is Indian. EVERY topic must be India-related (Ramayan, Mahabharat, Puran, Indian history, Indian mysteries, Indian saints/warriors/temples, Indian psychology-style life lessons).
- Story must be enjoyable for kids and adults: clear, gripping, no gore, respectful to deities and faiths.
- Facts: research first. Legends/folk versions are said with "कहते हैं" / "कथा के अनुसार". Never invent numbers or dates.

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
