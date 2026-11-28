# Voice (owner-approved 2026-11-27): Indic Parler-TTS, speaker **Aman** — used for ALL videos (Instagram + YouTube)

Setup (after RUNBOOK §1):
```bash
pip install --break-system-packages -q git+https://github.com/huggingface/parler-tts.git   # pulls torch (pytorch.org index is blocked by proxy)
pip install --break-system-packages -q "protobuf>=5.26"   # separately, after parler (one command = resolver conflict)
export HF_TOKEN=...   # from the task prompt; never commit
```
First use downloads ~3.7 GB. Speed ≈ 10 s of compute per 1 s of audio → 60 s reel ≈ 12 min, 9 min long video ≈ 90–110 min.
Always run renders with `nohup ... &` and poll the log.

In every spec: `"engine": "parler", "speaker": "Aman"`. Delivery follows each block's `mood`
(hook / neutral / warm / tense / shock / sad / cta / verse — see tools/parler_engine.py) and is generated sentence by sentence,
so WRITE FOR THE VOICE: short sentences, `?` for questions, `!` for excitement, `...` for suspense, and pick the mood that matches
the emotion of each block (slow+soft for sad, fast+dramatic for shock, low for suspense).

Fallback: if install/token/model fails or a render would miss its publish time, remove "engine"/"speaker" from the spec
(Edge voice hi-IN-MadhurNeural) and tell the owner.

Music (royalty-free, generated for us): `"music": "devotional_bg.mp3"` for Chalisa / Ramayan / Mahabharat,
`"music": "doc_bg.mp3"` for YouTube documentaries and Shorts. `"bells": true` only for Chalisa / devotional reels.
