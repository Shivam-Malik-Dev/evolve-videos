"""EVOLVEUNFILTERED kids story video builder (YouTube, 16:9, 5-10 min).

Usage: python3 make_story.py spec.json out.mp4      (env PIXABAY_KEY)
Spec: title, voices{who:{voice,rate,pitch}}, cast{id:{pixabay_id,height,name?,hue?,flip?}},
      backgrounds{name:pixabay_id}, scenes[{bg, chars[{id,x,y,enter?}], lines[{who,say}]}]
Characters are transparent PNGs reused in every scene (consistent look); the speaking one bounces.
"""
import asyncio, json, math, os, subprocess, sys, urllib.parse, urllib.request
import numpy as np
from PIL import Image, ImageDraw, ImageFont
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from make_reel import tts_line, compress_pauses, fetch, dur, sh, ass_time, SSL, FONT_DIR

W, H, FPS, SR = 1920, 1080, 24, 24000
LINE_GAP, SCENE_GAP, TITLE_SEC = 0.35, 0.7, 3.8
FONT = os.path.join(FONT_DIR, "Mukta-ExtraBold.ttf")


def pix_by_id(pid):
    url = "https://pixabay.com/api/?" + urllib.parse.urlencode({"key": os.environ["PIXABAY_KEY"], "id": pid})
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (EvolveUnfiltered bot)"})
    h = json.load(urllib.request.urlopen(req, context=SSL, timeout=30))["hits"][0]
    return h.get("largeImageURL") or h["webformatURL"]


def load_assets(spec, work):
    bgs, chars = {}, {}
    for name, pid in spec["backgrounds"].items():
        p = fetch(pix_by_id(pid), os.path.join(work, f"bg_{pid}.img"))
        im = Image.open(p).convert("RGB")
        sc = max(W * 1.1 / im.width, H * 1.1 / im.height)
        im = im.resize((int(im.width * sc) + 1, int(im.height * sc) + 1), Image.LANCZOS)
        bgs[name] = im
    for cid, c in spec["cast"].items():
        p = fetch(pix_by_id(c["pixabay_id"]), os.path.join(work, f"ch_{c['pixabay_id']}.png"))
        im = Image.open(p).convert("RGBA")
        im = im.crop(im.getbbox())
        if c.get("hue"):
            a = im.getchannel("A")
            hsv = np.array(im.convert("RGB").convert("HSV")).astype(np.int16)
            hsv[..., 0] = (hsv[..., 0] + int(255 * c["hue"])) % 256
            im = Image.fromarray(hsv.astype(np.uint8), "HSV").convert("RGBA")
            im.putalpha(a)
        h = c.get("height", 420)
        im = im.resize((int(im.width * h / im.height), h), Image.LANCZOS)
        if c.get("flip"):
            im = im.transpose(Image.FLIP_LEFT_RIGHT)
        chars[cid] = {"img": im, "flipped": im.transpose(Image.FLIP_LEFT_RIGHT)}
    return bgs, chars


def music(total, out):
    """cheerful Karplus-Strong pluck loop in C major pentatonic + soft bass (copyright-free, generated)."""
    sr, bpm = 44100, 96
    beat = 60 / bpm
    rng = np.random.default_rng(4)
    y = np.zeros(int((total + 2) * sr))
    def pluck(freq, t0, amp, length=1.2):
        n = int(sr / freq); buf = rng.uniform(-1, 1, n); out_ = np.zeros(int(length * sr))
        for i in range(len(out_)):
            out_[i] = buf[i % n]; buf[i % n] = 0.996 * 0.5 * (buf[i % n] + buf[(i + 1) % n])
        s = int(t0 * sr); e = min(len(y), s + len(out_)); y[s:e] += amp * out_[: e - s]
    notes = [523.25, 587.33, 659.25, 783.99, 880.0]
    melody = [0, 2, 3, 2, 4, 3, 2, 1, 0, 2, 3, 4, 3, 2, 0, -1]  # 16 eighths = 2 bars
    bass = [130.81, 98.0, 110.0, 87.31]
    cache = {}
    t, bar = 0.0, 0
    while t < total:
        for k, m in enumerate(melody):
            if m >= 0:
                key = ("m", m)
                tt = t + k * beat / 2
                if tt < total: pluck(notes[m], tt, 0.18)
        for k in range(2):
            tt = t + k * beat * 2
            if tt < total: pluck(bass[(bar * 2 + k) % 4], tt, 0.30, 2.0)
        t += beat * 8; bar += 1
    y = np.tanh(y * 1.2) * 0.5
    fade = int(2 * sr); y[: fade] *= np.linspace(0, 1, fade); end = int(total * sr); y[end - fade: end] *= np.linspace(1, 0, fade)
    y = y[:end]
    pcm = (np.clip(y, -1, 1) * 32767).astype(np.int16)
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "s16le", "-ar", str(sr), "-ac", "1", "-i", "-",
                    "-af", "aecho=0.8:0.6:180:0.25,aformat=channel_layouts=stereo", out], input=pcm.tobytes(), check=True)


def main(spec_path, out):
    spec = json.load(open(spec_path, encoding="utf-8"))
    work = os.path.splitext(os.path.abspath(out))[0] + "_work"
    os.makedirs(work, exist_ok=True)
    bgs, chars = load_assets(spec, work)

    # ---- voice timeline ----
    audio = [np.zeros(int(TITLE_SEC * SR), np.int16)]
    t = TITLE_SEC
    words, timeline = [], []  # timeline: per scene {start,end, speaking:[(who,a,b)]}
    for si, sc in enumerate(spec["scenes"]):
        s_start, speaking = t, []
        for li, ln in enumerate(sc["lines"]):
            v = spec["voices"][ln["who"]]
            mp3 = os.path.join(work, f"s{si}_l{li}.mp3")
            ws = asyncio.run(tts_line(ln["say"], v["voice"], v.get("rate", "+0%"), mp3, v.get("pitch", "+0Hz"), v.get("volume", "+0%")))
            wav = os.path.join(work, f"s{si}_l{li}.wav")
            sh("ffmpeg", "-y", "-v", "error", "-i", mp3, "-af",
               "areverse,silenceremove=start_periods=1:start_threshold=-45dB:start_silence=0.05,areverse", "-ar", str(SR), "-ac", "1", wav)
            ws = compress_pauses(wav, ws, normal=0.34, dramatic=0.55)
            raw = subprocess.check_output(["ffmpeg", "-v", "error", "-i", wav, "-f", "s16le", "-ar", str(SR), "-ac", "1", "-"])
            pcm = np.frombuffer(raw, np.int16)
            d = len(pcm) / SR
            words += [(a + t, b + t, txt) for a, b, txt in ws]
            speaking.append((ln["who"], t, t + d))
            audio += [pcm, np.zeros(int(LINE_GAP * SR), np.int16)]
            t += d + LINE_GAP
        audio.append(np.zeros(int(SCENE_GAP * SR), np.int16))
        t += SCENE_GAP
        timeline.append({"start": s_start, "end": t, "speaking": speaking, "scene": sc})
    timeline[0]["start"] = 0.0
    total = t + 1.0
    voice = np.concatenate(audio + [np.zeros(int(1.0 * SR), np.int16)])
    voice_wav = os.path.join(work, "voice.wav")
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "s16le", "-ar", str(SR), "-ac", "1", "-i", "-",
                    "-af", "highpass=f=70,acompressor=threshold=-18dB:ratio=3,loudnorm=I=-15:TP=-1.5:LRA=9",
                    "-ar", "44100", "-ac", "2", voice_wav], input=voice.tobytes(), check=True)
    bed = os.path.join(work, "music.wav")
    music(total, bed)

    # ---- captions (bottom, kid friendly) ----
    ass = os.path.join(work, "caps.ass")
    title = spec["title"].replace("\n", "\\N")
    head = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {W}
PlayResY: {H}
WrapStyle: 2

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Cap,Mukta ExtraBold,74,&H00FFFFFF,&H00FFFFFF,&H00301A00,&H80000000,0,0,0,0,100,100,0,0,1,6,2,2,120,120,60,1
Style: Title,Mukta ExtraBold,130,&H00FFFFFF,&H00FFFFFF,&H00301A00,&H80000000,0,0,0,0,100,100,0,0,1,10,5,5,100,100,0,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    ev = [f"Dialogue: 1,{ass_time(0.2)},{ass_time(TITLE_SEC - 0.2)},Title,,0,0,0,,{{\\fad(300,300)\\t(0,600,\\fscx105\\fscy105)}}{title}"]
    chunks, cur = [], []
    for i, w in enumerate(words):
        cur.append(w)
        nxt = words[i + 1] if i + 1 < len(words) else None
        if len(cur) == 6 or nxt is None or nxt[0] - w[1] > 0.3:
            chunks.append(cur); cur = []
    for ci, ch in enumerate(chunks):
        end = min(chunks[ci + 1][0][0] if ci + 1 < len(chunks) else total, ch[-1][1] + 0.5)
        for wi, w in enumerate(ch):
            en = ch[wi + 1][0] if wi + 1 < len(ch) else end
            txt = " ".join(f"{{\\c&H0035D7FF&}}{x[2]}{{\\c&H00FFFFFF&}}" if k == wi else x[2] for k, x in enumerate(ch))
            ev.append(f"Dialogue: 0,{ass_time(w[0])},{ass_time(en)},Cap,,0,0,0,,{txt}")
    open(ass, "w", encoding="utf-8").write(head + "\n".join(ev) + "\n")

    # ---- frames ----
    nfr = int(total * FPS)
    name_font = ImageFont.truetype(FONT, 46, layout_engine=ImageFont.Layout.RAQM)
    enc = subprocess.Popen(["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                            "-i", voice_wav, "-i", bed, "-filter_complex",
                            f"[0:v]ass={ass}:fontsdir={FONT_DIR}[v];[1:a]asplit=2[va][vb];[2:a]volume=0.35[m];"
                            f"[m][va]sidechaincompress=threshold=0.04:ratio=5:attack=30:release=400[md];[vb][md]amix=inputs=2:duration=first:normalize=0[a]",
                            "-map", "[v]", "-map", "[a]", "-c:v", "libx264", "-preset", "veryfast", "-tune", "animation", "-crf", "24",
                            "-maxrate", "1800k", "-bufsize", "3600k", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "128k",
                            "-movflags", "+faststart", out], stdin=subprocess.PIPE)
    si = 0
    for f in range(nfr):
        tt = f / FPS
        while si + 1 < len(timeline) and tt >= timeline[si]["end"]:
            si += 1
        T = timeline[si]; sc = T["scene"]
        bg = bgs[sc["bg"]]
        p = (tt - T["start"]) / max(T["end"] - T["start"], 0.1)
        ox = int((bg.width - W) * (0.15 + 0.7 * p)); oy = int((bg.height - H) * 0.5)
        frame = bg.crop((ox, oy, ox + W, oy + H)).convert("RGBA")
        who_now = next((w for w, a, b in T["speaking"] if a <= tt < b), None)
        for k, c in enumerate(sc.get("chars", [])):
            cimg = chars[c["id"]]
            img = cimg["flipped"] if c.get("face") == "left" else cimg["img"]
            x = c["x"] * W; y = c["y"] * H
            if c.get("enter") and tt - T["start"] < 1.2:
                e = (tt - T["start"]) / 1.2; e = 1 - (1 - e) ** 3
                x = (1.25 * W if c["enter"] == "right" else -0.25 * W) * (1 - e) + x * e
            y += 8 * math.sin(2 * math.pi * 0.7 * tt + k * 1.7)
            if who_now == c["id"]:
                y -= abs(math.sin(2 * math.pi * 2.6 * tt)) * 22
            frame.alpha_composite(img, (int(x - img.width / 2), int(y - img.height / 2)))
            if who_now == c["id"]:
                nm = spec["cast"][c["id"]].get("name")
                if nm:
                    d = ImageDraw.Draw(frame); tw = d.textlength(nm, font=name_font)
                    bx, by = int(x - tw / 2 - 22), int(y - img.height / 2 - 78)
                    d.rounded_rectangle([bx, by, bx + tw + 44, by + 66], radius=30, fill=(255, 205, 40, 235))
                    d.text((bx + 22, by + 4), nm, font=name_font, fill=(60, 30, 0))
        # dip to dark between scenes
        fadek = min(1.0, (tt - T["start"]) / 0.35, (T["end"] - tt) / 0.35) if si > 0 or tt > 0.35 else tt / 0.35
        fr = frame.convert("RGB")
        if fadek < 1:
            fr = Image.eval(fr, lambda v, k=max(fadek, 0): int(v * k))
        if tt < TITLE_SEC:  # title card: darker background
            fr = Image.eval(fr, lambda v: int(v * 0.55))
        enc.stdin.write(fr.tobytes())
    enc.stdin.close(); enc.wait()
    print(json.dumps({"out": out, "minutes": round(total / 60, 2), "scenes": len(timeline), "MB": round(os.path.getsize(out) / 1e6, 1)}))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
