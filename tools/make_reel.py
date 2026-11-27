"""EVOLVEUNFILTERED Reel builder v2.

Usage: python3 make_reel.py spec.json out.mp4
Env:   PIXABAY_KEY (required for footage)

spec.json:
{
  "voice": "hi-IN-MadhurNeural", "rate": "+12%",
  "hook_text": "On-screen hook (first ~3s)",
  "lines": [ {"say": "Devanagari line", "broll": ["pixabay query", "second query"]}, ... ]
}
"""
import asyncio, json, os, random, re, ssl, subprocess, sys, urllib.parse, urllib.request
import edge_tts, edge_tts.communicate as ecomm

W, H, FPS = 1080, 1920, 30
GAP = 0.18  # pause between lines (s)
CA = os.path.expanduser("~/.ccr/ca-bundle.crt")
SSL = ssl.create_default_context(cafile=CA) if os.path.exists(CA) else ssl.create_default_context()
ecomm._SSL_CTX = SSL
FONT_DIR = os.path.expanduser("~/.fonts")


def sh(*a):
    subprocess.run(list(a), check=True)


def dur(p):
    return float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", p]).decode())


# ---------------- voice ----------------
async def tts_line(text, voice, rate, out):
    for attempt in range(6):
        try:
            comm = edge_tts.Communicate(text, voice, rate=rate, boundary="WordBoundary")
            audio, words = b"", []
            async for ch in comm.stream():
                if ch["type"] == "audio":
                    audio += ch["data"]
                elif ch["type"] == "WordBoundary":
                    words.append((ch["offset"] / 1e7, (ch["offset"] + ch["duration"]) / 1e7, ch["text"]))
            if audio and words:
                open(out, "wb").write(audio)
                return words
        except Exception:
            pass
        await asyncio.sleep(2 + attempt)
    raise RuntimeError("TTS failed: " + text[:40])


# ---------------- footage ----------------
def pixabay(query, used):
    key = os.environ["PIXABAY_KEY"]
    url = "https://pixabay.com/api/videos/?" + urllib.parse.urlencode({"key": key, "q": query, "per_page": 20, "safesearch": "true"})
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (EvolveUnfiltered bot)"})
    hits = json.load(urllib.request.urlopen(req, context=SSL, timeout=30)).get("hits", [])
    hits = [h for h in hits if h["id"] not in used and h["duration"] >= 4]
    qw = set(query.lower().split())
    good = [h for h in hits if qw & set(re.split(r"[,\s]+", h.get("tags", "").lower()))]
    hits = good or hits
    if not hits:
        return None
    h = random.choice(hits[:3])
    used.add(h["id"])
    v = h["videos"].get("medium") or h["videos"].get("small")
    return v["url"]


def fetch(url, out):
    if not os.path.exists(out):
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        open(out, "wb").write(urllib.request.urlopen(req, context=SSL, timeout=120).read())
    return out


def make_segment(src, seconds, out):
    """crop to 9:16, darken, slow push-in, exact length"""
    vf = (f"scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},"
          f"zoompan=z='min(1.0+0.0012*on,1.12)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=1:s={W}x{H}:fps={FPS},"
          f"eq=brightness=-0.04:saturation=0.85:contrast=1.06,vignette=PI/5,format=yuv420p")
    sh("ffmpeg", "-y", "-v", "error", "-stream_loop", "-1", "-i", src, "-t", f"{seconds:.3f}", "-vf", vf,
       "-an", "-r", str(FPS), "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", out)


# ---------------- captions (ASS) ----------------
def ass_time(t):
    t = max(t, 0)
    return f"{int(t // 3600)}:{int(t % 3600 // 60):02d}:{t % 60:05.2f}"


def build_ass(words, hook, total, out):
    head = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {W}
PlayResY: {H}
WrapStyle: 2

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Cap,Mukta ExtraBold,104,&H00FFFFFF,&H00FFFFFF,&H00000000,&H96000000,0,0,0,0,100,100,0,0,1,7,3,5,60,60,0,1
Style: Hook,Mukta ExtraBold,104,&H00FFFFFF,&H00FFFFFF,&H00000000,&H64000000,0,0,0,0,100,100,0,0,1,8,4,8,60,60,330,1
Style: Brand,Mukta Bold,36,&H90FFFFFF,&H00FFFFFF,&H00000000,&H00000000,0,0,0,0,100,100,2,0,1,2,0,2,40,40,150,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    ev = []
    hook = hook.replace("\n", "\\N")
    hook = re.sub(r"\*(.+?)\*", r"{\\c&H0028B4FF&}\1{\\c&H00FFFFFF&}", hook)
    # hook card (top) for first 3.2s
    ev.append(f"Dialogue: 2,{ass_time(0)},{ass_time(min(3.2, total))},Hook,,0,0,0,,{{\\fad(120,250)}}{hook}")
    ev.append(f"Dialogue: 1,{ass_time(0)},{ass_time(total)},Brand,,0,0,0,,@evolveunfiltered")
    # chunk words: max 3 words per chunk, break on big gaps
    chunks, cur = [], []
    for i, w in enumerate(words):
        cur.append(w)
        nxt = words[i + 1] if i + 1 < len(words) else None
        if len(cur) == 3 or nxt is None or nxt[0] - w[1] > 0.35:
            chunks.append(cur)
            cur = []
    ACC = "&H0028B4FF&"  # orange-yellow (BGR)
    for ci, ch in enumerate(chunks):
        chunk_end = chunks[ci + 1][0][0] if ci + 1 < len(chunks) else total
        chunk_end = min(chunk_end, ch[-1][1] + 0.6)
        for wi, w in enumerate(ch):
            st = w[0]
            en = ch[wi + 1][0] if wi + 1 < len(ch) else chunk_end
            parts = []
            for k, x in enumerate(ch):
                txt = x[2]
                parts.append(f"{{\\c{ACC}\\fscx108\\fscy108}}{txt}{{\\c&H00FFFFFF&\\fscx100\\fscy100}}" if k == wi else txt)
            pop = "{\\fscx92\\fscy92\\t(0,90,\\fscx100\\fscy100)}" if wi == 0 else ""
            ev.append(f"Dialogue: 0,{ass_time(st)},{ass_time(en)},Cap,,0,0,0,,{{\\pos({W//2},{int(H*0.60)})}}{pop}{' '.join(parts)}")
    open(out, "w", encoding="utf-8").write(head + "\n".join(ev) + "\n")


# ---------------- music bed (generated, copyright-free) ----------------
def ambient(total, out):
    expr = ("0.06*sin(2*PI*55*t)*(0.6+0.4*sin(2*PI*0.08*t))"
            "+0.035*sin(2*PI*82.41*t)*(0.6+0.4*sin(2*PI*0.11*t+1))"
            "+0.025*sin(2*PI*130.81*t)*(0.5+0.5*sin(2*PI*0.05*t+2))"
            "+0.018*sin(2*PI*164.81*t)*(0.5+0.5*sin(2*PI*0.07*t))")
    sh("ffmpeg", "-y", "-v", "error",
       "-f", "lavfi", "-i", f"aevalsrc='{expr}':s=44100:d={total:.2f}",
       "-f", "lavfi", "-i", f"anoisesrc=c=brown:a=0.02:d={total:.2f}:r=44100",
       "-filter_complex", "[1:a]lowpass=f=400[n];[0:a][n]amix=inputs=2:normalize=0,aecho=0.8:0.7:120|240:0.3|0.2,"
       f"afade=t=in:d=1.2,afade=t=out:st={max(total-1.5,0):.2f}:d=1.5,aformat=channel_layouts=stereo",
       out)


def main(spec_path, out):
    spec = json.load(open(spec_path, encoding="utf-8"))
    voice, rate = spec.get("voice", "hi-IN-MadhurNeural"), spec.get("rate", "+12%")
    work = os.path.splitext(os.path.abspath(out))[0] + "_work"
    os.makedirs(work, exist_ok=True)
    random.seed(spec.get("seed", 7))

    # 1. voice per line + global word timeline
    words, t0, line_spans, wavs = [], 0.0, [], []
    for i, ln in enumerate(spec["lines"]):
        mp3 = os.path.join(work, f"v{i}.mp3")
        ws = asyncio.run(tts_line(ln["say"], voice, rate, mp3))
        d = dur(mp3)
        words += [(a + t0, b + t0, txt) for a, b, txt in ws]
        line_spans.append((t0, t0 + d + GAP))
        wav = os.path.join(work, f"v{i}.wav")
        sh("ffmpeg", "-y", "-v", "error", "-i", mp3, "-ar", "24000", "-ac", "1", wav)
        wavs.append(wav)
        t0 += d + GAP
    total = t0 + 0.4

    # 2. voice track
    lst = os.path.join(work, "v.txt")
    sil = os.path.join(work, "gap.wav")
    sh("ffmpeg", "-y", "-v", "error", "-f", "lavfi", "-i", f"anullsrc=r=24000:cl=mono", "-t", str(GAP), sil)
    with open(lst, "w") as f:
        for w_ in wavs:
            f.write(f"file '{w_}'\nfile '{sil}'\n")
    voice_wav = os.path.join(work, "voice.wav")
    sh("ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", lst,
       "-af", "highpass=f=70,acompressor=threshold=-18dB:ratio=3:attack=5:release=80,loudnorm=I=-14:TP=-1.5:LRA=7",
       "-ar", "44100", "-ac", "2", voice_wav)

    # 3. footage: a cut every ~2.5-3.5s, query rotates within line
    used, segs = set(), []
    for i, (ln, (a, b)) in enumerate(zip(spec["lines"], line_spans)):
        if i == len(spec["lines"]) - 1:
            b = total
        length = b - a
        n = max(1, round(length / 3.0))
        queries = ln.get("broll", ["dark night"])
        for k in range(n):
            q = queries[k % len(queries)]
            url = pixabay(q, used) or pixabay("dark moody", used)
            src = fetch(url, os.path.join(work, f"src_{i}_{k}.mp4"))
            seg = os.path.join(work, f"seg_{i}_{k}.mp4")
            make_segment(src, length / n, seg)
            segs.append(seg)
    vl = os.path.join(work, "segs.txt")
    open(vl, "w").write("".join(f"file '{s}'\n" for s in segs))
    base = os.path.join(work, "base.mp4")
    sh("ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", vl, "-c", "copy", base)

    # 4. captions + music + final mix
    ass = os.path.join(work, "caps.ass")
    build_ass(words, spec["hook_text"], total, ass)
    bed = os.path.join(work, "bed.wav")
    ambient(total, bed)
    sh("ffmpeg", "-y", "-v", "error", "-i", base, "-i", voice_wav, "-i", bed,
       "-filter_complex",
       f"[0:v]ass={ass}:fontsdir={FONT_DIR},fade=in:st=0:d=0.25[v];"
       f"[1:a]asplit=2[va][vb];[2:a]volume=0.55[m];[m][va]sidechaincompress=threshold=0.05:ratio=6:attack=20:release=300[md];"
       f"[vb][md]amix=inputs=2:duration=longest:normalize=0[a]",
       "-map", "[v]", "-map", "[a]", "-t", f"{total:.2f}",
       "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p",
       "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", out)
    print(json.dumps({"out": out, "seconds": round(total, 1), "words": len(words), "cuts": len(segs)}))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
