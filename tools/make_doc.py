"""EVOLVEUNFILTERED YouTube documentary builder (16:9, 8-12 min, Hindi narration over stock footage).

Usage: python3 make_doc.py spec.json out.mp4     (env PIXABAY_KEY)
spec: {title, voice, rate, seed,
       chapters: [{title, blocks: [{mood, say, broll: [...], card?: "big on-screen fact"}]}]}
"""
import asyncio, json, os, random, subprocess, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import make_reel as R
import viz

W, H, FPS = 1920, 1080, 30
CHAPTER_CARD = 2.6


def seg(src, seconds, out):
    if src.lower().endswith((".jpg", ".jpeg", ".png")):
        n = int(seconds * FPS) + 1
        vf = (f"scale={W*2}:{H*2}:force_original_aspect_ratio=increase,crop={W*2}:{H*2},"
              f"zoompan=z='1.0+0.08*on/{n}':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={n}:s={W}x{H}:fps={FPS},"
              f"eq=brightness=-0.05:saturation=0.9,vignette=PI/5,format=yuv420p")
        R.sh("ffmpeg", "-y", "-v", "error", "-loop", "1", "-i", src, "-t", f"{seconds:.3f}", "-vf", vf, "-r", str(FPS),
             "-c:v", "libx264", "-preset", "veryfast", "-crf", "23", out)
        return
    vf = (f"scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},"
          f"eq=brightness=-0.06:saturation=0.85:contrast=1.05,vignette=PI/5,format=yuv420p")
    R.sh("ffmpeg", "-y", "-v", "error", "-stream_loop", "-1", "-i", src, "-t", f"{seconds:.3f}", "-vf", vf, "-an", "-r", str(FPS),
         "-c:v", "libx264", "-preset", "veryfast", "-crf", "23", out)


def looks_ok(src):
    """reject near-blank (white/black/flat) clips"""
    from PIL import Image, ImageStat
    png = src + ".chk.png"
    try:
        if src.lower().endswith((".jpg", ".jpeg", ".png")):
            im = Image.open(src)
        else:
            subprocess.run(["ffmpeg", "-y", "-v", "error", "-ss", "1", "-i", src, "-frames:v", "1", "-vf", "scale=320:-1", png], check=True)
            im = Image.open(png)
        st = ImageStat.Stat(im.convert("L"))
        import numpy as np
        a = np.asarray(im.convert("RGB")).astype(int)
        green = ((a[..., 1] > 140) & (a[..., 0] < 110) & (a[..., 2] < 110)).mean()
        return 25 < st.mean[0] < 235 and st.stddev[0] > 22 and green < 0.2
    except Exception:
        return False


def card_clip(seconds, out):
    R.sh("ffmpeg", "-y", "-v", "error", "-f", "lavfi", "-i", f"color=c=0x0b0b0e:s={W}x{H}:r={FPS}:d={seconds:.3f}",
         "-vf", "vignette=PI/4,format=yuv420p", "-c:v", "libx264", "-preset", "veryfast", "-crf", "23", out)


def main(spec_path, out):
    spec = json.load(open(spec_path, encoding="utf-8"))
    voice, rate = spec.get("voice", "hi-IN-MadhurNeural"), spec.get("rate", "+10%")
    work = os.path.splitext(os.path.abspath(out))[0] + "_work"
    os.makedirs(work, exist_ok=True)
    random.seed(spec.get("seed", 3))
    sil = lambda sec, name: (R.sh("ffmpeg", "-y", "-v", "error", "-f", "lavfi", "-i", "anullsrc=r=24000:cl=mono", "-t", f"{sec:.2f}",
                                  os.path.join(work, name)), os.path.join(work, name))[1]

    # 1. voice + timeline
    t, wavs, words, spans, cards, chapters, hits = 0.0, [], [], [], [], [], []
    bi = 0
    for ci, ch in enumerate(spec["chapters"]):
        if ch.get("title"):
            chapters.append((t, ch["title"]))
            wavs.append(sil(CHAPTER_CARD, f"cg{ci}.wav")); spans.append(("CARD", t, t + CHAPTER_CARD)); t += CHAPTER_CARD
        for b in ch["blocks"]:
            mood = R.MOODS.get(b.get("mood", "neutral"), R.MOODS["neutral"])
            if bi and mood["pause"]:
                wavs.append(sil(mood["pause"], f"p{bi}.wav")); t += mood["pause"]
            if b.get("mood") in ("shock", "hook"):
                hits.append(max(t - 0.12, 0))
            mp3 = os.path.join(work, f"v{bi}.mp3")
            ws = asyncio.run(R.tts_line(b["say"], voice, R.shift(rate, mood["rate"]), mp3, mood["pitch"], mood["vol"]))
            wav = os.path.join(work, f"v{bi}.wav")
            R.sh("ffmpeg", "-y", "-v", "error", "-i", mp3, "-af",
                 "areverse,silenceremove=start_periods=1:start_threshold=-45dB:start_silence=0.08,areverse", "-ar", "24000", "-ac", "1", wav)
            ws = R.compress_pauses(wav, ws, normal=0.32, dramatic=0.55)
            d = R.dur(wav)
            words += [(a + t, b_ + t, x) for a, b_, x in ws]
            if b.get("card") and not b.get("viz"):
                cards.append((t + 0.3, min(t + d, t + 5.5), b["card"]))
            spans.append((b, t, t + d)); wavs.append(wav); t += d; bi += 1
    total = t + 2.0
    wavs.append(sil(2.0, "tail.wav"))
    lst = os.path.join(work, "v.txt"); open(lst, "w").write("".join(f"file '{w}'\n" for w in wavs))
    voice_wav = os.path.join(work, "voice.wav")
    R.sh("ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", lst,
         "-af", "highpass=f=70,acompressor=threshold=-18dB:ratio=3:attack=5:release=80,loudnorm=I=-15:TP=-1.5:LRA=9",
         "-ar", "44100", "-ac", "2", voice_wav)

    # 2. footage
    used, segs = set(), []
    for si, (b, a, e) in enumerate(spans):
        nxt = spans[si + 1][1] if si + 1 < len(spans) else total
        length = nxt - a
        if b == "CARD":
            p = os.path.join(work, f"card{si}.mp4"); card_clip(length, p); segs.append(p); continue
        if b.get("viz"):
            p = os.path.join(work, f"viz{si}.mp4"); viz.render(b["viz"], length, p); segs.append(p); continue
        n = max(1, round(length / 4.5))
        qs = b.get("broll", ["city night"])
        for k in range(n):
            q = qs[k % len(qs)]
            ext = ".jpg" if q.startswith("img:") else ".mp4"
            for attempt in range(4):
                url = R.pixabay(q, used) or R.pixabay("india city", used)
                src = R.fetch(url, os.path.join(work, f"src_{si}_{k}_{attempt}{ext}"))
                if looks_ok(src):
                    break
            p = os.path.join(work, f"seg_{si}_{k}.mp4"); seg(src, length / n, p); segs.append(p)
    vl = os.path.join(work, "segs.txt"); open(vl, "w").write("".join(f"file '{s}'\n" for s in segs))
    base = os.path.join(work, "base.mp4")
    R.sh("ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", vl, "-c", "copy", base)

    # 3. subtitles + cards + chapter titles
    head = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {W}
PlayResY: {H}
WrapStyle: 2

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Cap,Mukta ExtraBold,60,&H00FFFFFF,&H00FFFFFF,&H00000000,&H96000000,0,0,0,0,100,100,0,0,1,5,2,2,160,160,70,1
Style: Card,Mukta ExtraBold,120,&H00FFFFFF,&H00FFFFFF,&H00000000,&H64000000,0,0,0,0,100,100,0,0,1,8,4,5,120,120,0,1
Style: Chap,Mukta ExtraBold,96,&H00FFFFFF,&H00FFFFFF,&H00000000,&H00000000,0,0,0,0,100,100,1,0,1,0,0,5,120,120,0,1
Style: Brand,Mukta Bold,30,&H90FFFFFF,&H00FFFFFF,&H00000000,&H00000000,0,0,0,0,100,100,2,0,1,2,0,9,40,40,30,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    ACC = "&H0028B4FF&"
    ev = [f"Dialogue: 1,{R.ass_time(0)},{R.ass_time(total)},Brand,,0,0,0,,EVOLVE UNFILTERED"]
    for (st, title) in chapters:
        title = title.replace("\n", "\\N")
        ev.append(f"Dialogue: 2,{R.ass_time(st + 0.15)},{R.ass_time(st + CHAPTER_CARD - 0.1)},Chap,,0,0,0,,{{\\fad(250,250)}}{{\\c{ACC}\\fs60}}EVOLVE UNFILTERED\\N{{\\c&H00FFFFFF&\\fs96}}{title}")
    for st, en, txt in cards:
        txt = txt.replace("\n", "\\N")
        ev.append(f"Dialogue: 3,{R.ass_time(st)},{R.ass_time(en)},Card,,0,0,0,,{{\\fad(200,300)\\c{ACC}\\pos({W//2},{int(H*0.42)})}}{txt}")
    chunks, cur = [], []
    for i, w in enumerate(words):
        cur.append(w)
        nx = words[i + 1] if i + 1 < len(words) else None
        if len(cur) == 6 or nx is None or nx[0] - w[1] > 0.3:
            chunks.append(cur); cur = []
    for ci, chk in enumerate(chunks):
        end = min(chunks[ci + 1][0][0] if ci + 1 < len(chunks) else total, chk[-1][1] + 0.5)
        for wi, w in enumerate(chk):
            en = chk[wi + 1][0] if wi + 1 < len(chk) else end
            txt = " ".join(f"{{\\c{ACC}}}{x[2]}{{\\c&H00FFFFFF&}}" if k == wi else x[2] for k, x in enumerate(chk))
            ev.append(f"Dialogue: 0,{R.ass_time(w[0])},{R.ass_time(en)},Cap,,0,0,0,,{txt}")
    ass = os.path.join(work, "caps.ass"); open(ass, "w", encoding="utf-8").write(head + "\n".join(ev) + "\n")

    # 4. music bed + mix
    bed0 = os.path.join(work, "bed0.wav"); R.ambient(total, bed0)
    bed = bed0
    if hits:
        boom = os.path.join(work, "boom.wav")
        R.sh("ffmpeg", "-y", "-v", "error", "-f", "lavfi", "-i", "aevalsrc='0.9*sin(2*PI*(90-60*t)*t)*exp(-4*t)':s=44100:d=1.2",
             "-af", "lowpass=f=300,aformat=channel_layouts=stereo", boom)
        bed = os.path.join(work, "bed.wav")
        ins = ["-i", bed0] + sum([["-i", boom] for _ in hits], [])
        pre = ";".join(f"[{k+1}:a]adelay={int(h*1000)}|{int(h*1000)}[b{k}]" for k, h in enumerate(hits))
        R.sh("ffmpeg", "-y", "-v", "error", *ins, "-filter_complex",
             f"{pre};[0:a]{''.join(f'[b{k}]' for k in range(len(hits)))}amix=inputs={len(hits)+1}:normalize=0:duration=first", bed)
    R.sh("ffmpeg", "-y", "-v", "error", "-i", base, "-i", voice_wav, "-i", bed, "-filter_complex",
         f"[0:v]ass={ass}:fontsdir={R.FONT_DIR}[v];[1:a]asplit=2[va][vb];[2:a]volume=0.5[m];"
         f"[m][va]sidechaincompress=threshold=0.05:ratio=6:attack=20:release=300[md];[vb][md]amix=inputs=2:duration=longest:normalize=0[a]",
         "-map", "[v]", "-map", "[a]", "-t", f"{total:.2f}", "-c:v", "libx264", "-preset", "veryfast", "-crf", "25",
         "-maxrate", "1400k", "-bufsize", "2800k", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "128k", "-movflags", "+faststart", out)
    # chapters list for YouTube description
    chap_txt = "\n".join(f"{int(s//60)}:{int(s%60):02d} {ti.replace(chr(10),' ')}" for s, ti in chapters)
    if chapters and chapters[0][0] > 0:
        chap_txt = "0:00 शुरुआत\n" + chap_txt
    open(os.path.splitext(out)[0] + "_chapters.txt", "w", encoding="utf-8").write(chap_txt)
    print(json.dumps({"out": out, "minutes": round(total / 60, 2), "MB": round(os.path.getsize(out) / 1e6, 1), "cuts": len(segs)}))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
