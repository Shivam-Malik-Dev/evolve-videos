"""Indic Parler-TTS (AI4Bharat, Apache-2.0) voice engine with mood-controlled delivery.

Needs: torch, parler-tts (git+https://github.com/huggingface/parler-tts.git), protobuf>=5.26, env HF_TOKEN
(the model is gated: the HF account must have accepted ai4bharat/indic-parler-tts terms).
Speed on 2 CPU cores: ~10 s of compute per 1 s of audio.
"""
import os, re, subprocess
import numpy as np

MODEL = "ai4bharat/indic-parler-tts"
CLEAR = "with very clear audio and no background noise."
MOOD_DESC = {
    "hook":    "speaks in an intriguing, expressive storytelling tone with strong emphasis, at a moderate pace,",
    "neutral": "speaks in a warm, expressive storytelling tone at a moderate pace,",
    "warm":    "speaks in a warm, gentle and expressive storytelling tone at a moderate pace,",
    "tense":   "speaks in a serious, low and suspenseful storytelling tone, slightly slowly,",
    "shock":   "speaks in an excited, dramatic and emphatic tone with high expressivity, slightly fast,",
    "sad":     "speaks in a soft, emotional and sad tone, slowly,",
    "cta":     "speaks in a warm, friendly and energetic tone at a moderate pace,",
    "verse":   "speaks in a calm, devotional and melodic tone, slowly, like reciting a prayer,",
}
_m = {}


def _load():
    if _m:
        return _m
    import torch
    from parler_tts import ParlerTTSForConditionalGeneration
    from transformers import AutoTokenizer
    torch.set_num_threads(os.cpu_count() or 2)
    tok = os.environ.get("HF_TOKEN")
    model = ParlerTTSForConditionalGeneration.from_pretrained(MODEL, token=tok).eval()
    _m.update(torch=torch, model=model,
              ptok=AutoTokenizer.from_pretrained(MODEL, token=tok),
              dtok=AutoTokenizer.from_pretrained(model.config.text_encoder._name_or_path, token=tok),
              sr=model.config.sampling_rate)
    return _m


def say(text, mood, speaker, out_wav, seed=42):
    """Synthesize one sentence → 24 kHz mono wav (silence-trimmed). Returns word timings [(start, end, word)]."""
    m = _load(); torch = m["torch"]
    desc = f"{speaker} {MOOD_DESC.get(mood, MOOD_DESC['neutral'])} {CLEAR}"
    d = m["dtok"](desc, return_tensors="pt"); p = m["ptok"](text, return_tensors="pt")
    torch.manual_seed(seed)
    with torch.no_grad():
        g = m["model"].generate(input_ids=d.input_ids, attention_mask=d.attention_mask,
                                prompt_input_ids=p.input_ids, prompt_attention_mask=p.attention_mask)
    a = g.cpu().numpy().squeeze().astype(np.float32)
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "f32le", "-ar", str(m["sr"]), "-ac", "1", "-i", "-", "-af",
                    "silenceremove=start_periods=1:start_threshold=-42dB:start_silence=0.03,"
                    "areverse,silenceremove=start_periods=1:start_threshold=-42dB:start_silence=0.06,areverse",
                    "-ar", "24000", "-ac", "1", out_wav], input=a.tobytes(), check=True)
    dur = float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", out_wav]).decode())
    # Parler gives no word timestamps: spread words over the sentence by spoken length (chars), small pause after commas
    words = [w for w in re.split(r"\s+", text.strip()) if w]
    weights = [len(re.sub(r"[^\wऀ-ॿ]", "", w)) + 1.5 + (2.5 if re.search(r"[,،…]$", w) else 0) for w in words]
    tot = sum(weights) or 1
    t, res = 0.0, []
    for w, wt in zip(words, weights):
        span = dur * wt / tot
        clean = re.sub(r"[।॥,!?\"“”‘’…]+$", "", w)
        res.append((t, t + span * 0.92, clean))
        t += span
    return res
