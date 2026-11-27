"""EVOLVEUNFILTERED - text-style Short generator (no stock footage needed).
Usage: python3 make_text_short.py script.json out.mp4
script.json: {"voice": "hi-IN-MadhurNeural", "lines": [{"say": "...", "show": "...", "hl": ["word"]}]}
"""
import asyncio, json, os, ssl, subprocess, sys, textwrap
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import edge_tts, edge_tts.communicate as c

CA = os.path.expanduser("~/.ccr/ca-bundle.crt")
if os.path.exists(CA):
    c._SSL_CTX = ssl.create_default_context(cafile=CA)

W, H, FPS = 1080, 1920, 30
FONT = "/usr/share/fonts/truetype/google-fonts/ofl/anton/Anton-Regular.ttf"
SMALL = "/usr/share/fonts/truetype/google-fonts/ofl/montserrat/Montserrat[wght].ttf"
ACCENT = (255, 140, 40)


def dur(p):
    return float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", p]).decode())


def background():
    img = Image.new("RGB", (W, H), (8, 8, 10))
    d = ImageDraw.Draw(img)
    for r in range(900, 0, -6):  # warm glow behind text
        a = int(38 * (1 - r / 900))
        d.ellipse([W // 2 - r, H // 2 - r, W // 2 + r, H // 2 + r], fill=(10 + a, 8 + a // 2, 8))
    return img.filter(ImageFilter.GaussianBlur(40))


def frame(text, hl, path, idx, total):
    img = background()
    d = ImageDraw.Draw(img)
    f = ImageFont.truetype(FONT, 96)
    lines = textwrap.wrap(text.upper(), 16)
    lh = 120
    y = H // 2 - len(lines) * lh // 2
    hlset = {h.upper() for h in hl}
    for ln in lines:
        words = ln.split(" ")
        widths = [d.textlength(w + " ", font=f) for w in words]
        x = (W - sum(widths)) // 2
        for w, wd in zip(words, widths):
            col = ACCENT if w.strip(".,?!") in hlset else (245, 245, 245)
            d.text((x + 4, y + 4), w, font=f, fill=(0, 0, 0))
            d.text((x, y), w, font=f, fill=col)
            x += wd
        y += lh
    s = ImageFont.truetype(SMALL, 38)
    brand = "EVOLVE UNFILTERED"
    d.text(((W - d.textlength(brand, font=s)) // 2, 170), brand, font=s, fill=(200, 200, 200))
    # progress bar
    d.rectangle([80, H - 220, W - 80, H - 212], fill=(50, 50, 50))
    d.rectangle([80, H - 220, 80 + int((W - 160) * (idx + 1) / total), H - 212], fill=ACCENT)
    img.save(path)


async def tts(text, voice, out):
    await edge_tts.Communicate(text, voice, rate="+8%", pitch="-4Hz").save(out)


def main(spec_path, out):
    spec = json.load(open(spec_path))
    voice = spec.get("voice", "hi-IN-MadhurNeural")
    work = os.path.join(os.path.dirname(os.path.abspath(out)), "work")
    os.makedirs(work, exist_ok=True)
    clips = []
    n = len(spec["lines"])
    for i, ln in enumerate(spec["lines"]):
        mp3, png, mp4 = (os.path.join(work, f"{i}.{e}") for e in ("mp3", "png", "mp4"))
        asyncio.run(tts(ln["say"], voice, mp3))
        frame(ln.get("show", ln["say"]), ln.get("hl", []), png, i, n)
        t = dur(mp3) + 0.25
        zoom = f"zoompan=z='1+0.0009*on':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={int(t*FPS)}:s={W}x{H}:fps={FPS}"
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-loop", "1", "-i", png, "-i", mp3,
                        "-filter_complex", f"[0:v]{zoom},fade=in:st=0:d=0.15,format=yuv420p[v];[1:a]apad=pad_dur=0.25[a]",
                        "-map", "[v]", "-map", "[a]", "-t", f"{t:.2f}", "-c:v", "libx264", "-preset", "veryfast",
                        "-c:a", "aac", "-ar", "44100", "-ac", "2", mp4], check=True)
        clips.append(mp4)
    lst = os.path.join(work, "list.txt")
    open(lst, "w").write("".join(f"file '{p}'\n" for p in clips))
    joined = os.path.join(work, "joined.mp4")
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", joined], check=True)
    total = dur(joined)
    # low suspense drone under the voice (generated, no copyright)
    drone = "aevalsrc='0.05*sin(2*PI*55*t)+0.03*sin(2*PI*82.4*t)+0.02*sin(2*PI*110*t)*sin(2*PI*0.2*t)':s=44100:d=%f" % total
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", joined, "-f", "lavfi", "-i", drone,
                    "-filter_complex", "[1:a]volume=0.6,aformat=channel_layouts=stereo[m];[0:a][m]amix=inputs=2:duration=first:normalize=0[a]",
                    "-map", "0:v", "-map", "[a]", "-c:v", "copy", "-c:a", "aac", "-b:a", "160k", "-movflags", "+faststart", out], check=True)
    print(out, round(total, 1), "sec")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
