"""Animated explainer graphics for EVOLVEUNFILTERED documentaries (PIL frames -> mp4).

types:
  chart    {"type":"chart","title":"सेंसेक्स","points":[["जन 1992",2000],["अप्रैल",4467],["अगस्त",2529]],"unit":""}
  flow     {"type":"flow","nodes":["बैंक A","ब्रोकर","बैंक B"],"labels":["₹ पैसा","BR रसीद"],"note":"..."}
  headline {"type":"headline","paper":"THE TIMES OF INDIA","date":"23 अप्रैल 1992","text":"..."}
  text     {"type":"text","text":"big statement","sub":"small line"}
"""
import math, os, subprocess
from PIL import Image, ImageDraw, ImageFont, ImageFilter

W, H, FPS = 1920, 1080, 30
FD = os.path.expanduser("~/.fonts")
BOLD = os.path.join(FD, "Mukta-ExtraBold.ttf")
SEMI = os.path.join(FD, "Mukta-Bold.ttf")
SERIF = "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf"
ACC = (255, 160, 40)
BG = (12, 12, 16)
RAQM = ImageFont.Layout.RAQM


def F(path, size):
    return ImageFont.truetype(path, size, layout_engine=RAQM)


def ease(x):
    x = max(0.0, min(1.0, x))
    return 1 - (1 - x) ** 3


def background():
    im = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(im)
    for x in range(0, W, 80):
        d.line([(x, 0), (x, H)], fill=(22, 22, 28))
    for y in range(0, H, 80):
        d.line([(0, y), (W, y)], fill=(22, 22, 28))
    glow = Image.new("RGB", (W, H), (0, 0, 0))
    ImageDraw.Draw(glow).ellipse([W * 0.2, H * 0.1, W * 0.8, H * 0.9], fill=(40, 26, 10))
    return Image.blend(im, glow.filter(ImageFilter.GaussianBlur(200)), 0.5)


def ctext(d, xy, text, font, fill, anchor="mm"):
    d.text(xy, text, font=font, fill=fill, anchor=anchor)


def draw_chart(spec, p, base):
    im = base.copy(); d = ImageDraw.Draw(im)
    ctext(d, (W // 2, 110), spec.get("title", ""), F(BOLD, 72), (255, 255, 255))
    pts = spec["points"]; vals = [v for _, v in pts]
    lo, hi = 0, max(vals) * 1.15
    x0, x1, y0, y1 = 220, W - 220, H - 200, 230
    d.line([(x0, y0), (x1, y0)], fill=(90, 90, 100), width=4)
    n = len(pts)
    P = [(x0 + (x1 - x0) * i / (n - 1), y0 - (y0 - y1) * (v - lo) / (hi - lo)) for i, (_, v) in enumerate(pts)]
    prog = ease(p / 0.8) * (n - 1)
    seg = int(prog); fr = prog - seg
    drawn = P[: seg + 1]
    if seg < n - 1:
        a, b = P[seg], P[seg + 1]
        drawn = drawn + [(a[0] + (b[0] - a[0]) * fr, a[1] + (b[1] - a[1]) * fr)]
    for i in range(len(drawn) - 1):
        up = drawn[i + 1][1] <= drawn[i][1]
        d.line([drawn[i], drawn[i + 1]], fill=(70, 210, 110) if up else (240, 70, 70), width=12)
    lf, vf = F(SEMI, 44), F(BOLD, 58)
    for i, (lab, v) in enumerate(pts):
        if i <= prog + 0.01:
            x, y = P[i]
            d.ellipse([x - 16, y - 16, x + 16, y + 16], fill=ACC)
            ctext(d, (x, y0 + 60), lab, lf, (200, 200, 200))
            ctext(d, (x, y - 60), f"{spec.get('prefix','')}{v:,}{spec.get('unit','')}", vf, (255, 255, 255))
    return im


def box(d, cx, cy, text, font, fill=(30, 30, 38), outline=ACC, w=360, h=170):
    d.rounded_rectangle([cx - w // 2, cy - h // 2, cx + w // 2, cy + h // 2], radius=30, fill=fill, outline=outline, width=6)
    ctext(d, (cx, cy), text, font, (255, 255, 255))


def draw_flow(spec, p, base):
    im = base.copy(); d = ImageDraw.Draw(im)
    if spec.get("title"):
        ctext(d, (W // 2, 120), spec["title"], F(BOLD, 66), (255, 255, 255))
    nodes, labels = spec["nodes"], spec.get("labels", [])
    n = len(nodes); xs = [W * (0.17 + 0.66 * i / max(n - 1, 1)) for i in range(n)]; cy = H // 2
    steps = n + len(labels)
    k = ease(p / 0.85) * steps
    nf = F(BOLD, 56); lf = F(SEMI, 46)
    for i, name in enumerate(nodes):
        if k >= i * 2 * 0 + i + 0.01 or i == 0:
            box(d, int(xs[i]), cy, name, nf)
    for i, lab in enumerate(labels):
        if i + 1 < n and k > i + 1:
            a = xs[i] + 195; b = xs[i + 1] - 195
            t = min(1, k - (i + 1))
            e = a + (b - a) * t
            d.line([(a, cy), (e, cy)], fill=ACC, width=10)
            if t > 0.95:
                d.polygon([(b, cy), (b - 34, cy - 22), (b - 34, cy + 22)], fill=ACC)
            ctext(d, ((a + b) / 2, cy - 70), lab, lf, (255, 220, 160))
    if spec.get("note") and p > 0.6:
        ctext(d, (W // 2, H - 170), spec["note"], F(BOLD, 60), ACC)
    return im


def draw_headline(spec, p, base):
    im = base.copy(); d = ImageDraw.Draw(im)
    sc = 0.9 + 0.1 * ease(p / 0.3)
    pw, ph = int(1300 * sc), int(760 * sc)
    x0, y0 = (W - pw) // 2, (H - ph) // 2
    paper = Image.new("RGB", (pw, ph), (236, 228, 210)); pd = ImageDraw.Draw(paper)
    pd.text((pw // 2, 70), spec.get("paper", "THE DAILY NEWS"), font=ImageFont.truetype(SERIF, int(64 * sc)), fill=(20, 20, 20), anchor="mm")
    pd.line([(40, 130), (pw - 40, 130)], fill=(30, 30, 30), width=4)
    pd.text((pw // 2, 170), spec.get("date", ""), font=F(SEMI, int(40 * sc)), fill=(60, 60, 60), anchor="mm")
    words = spec["text"].split(" "); lines, cur = [], ""
    hf = F(BOLD, int(78 * sc))
    for w in words:
        t = (cur + " " + w).strip()
        if pd.textlength(t, font=hf) > pw - 140:
            lines.append(cur); cur = w
        else:
            cur = t
    lines.append(cur)
    reveal = ease((p - 0.15) / 0.5)
    for i, ln in enumerate(lines):
        if reveal * len(lines) > i:
            pd.text((pw // 2, 300 + i * 100 * sc), ln, font=hf, fill=(15, 15, 15), anchor="mm")
    for j in range(6):
        y = int(ph - 220 + j * 30)
        pd.line([(70, y), (pw - 70, y)], fill=(170, 165, 150), width=8)
    paper = paper.rotate(-2, expand=True, fillcolor=BG)
    im.paste(paper, ((W - paper.width) // 2, (H - paper.height) // 2))
    return im


def draw_text(spec, p, base):
    im = base.copy(); d = ImageDraw.Draw(im)
    t = spec["text"]; n = max(1, int(len(t) * ease(p / 0.5)))
    ctext(d, (W // 2, H // 2 - 40), t[:n], F(BOLD, 110), (255, 255, 255))
    if spec.get("sub") and p > 0.45:
        ctext(d, (W // 2, H // 2 + 110), spec["sub"], F(SEMI, 56), ACC)
    return im


DRAW = {"chart": draw_chart, "flow": draw_flow, "headline": draw_headline, "text": draw_text}


def render(spec, seconds, out):
    base = background()
    n = int(seconds * FPS) + 1
    enc = subprocess.Popen(["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                            "-c:v", "libx264", "-preset", "veryfast", "-crf", "23", "-pix_fmt", "yuv420p", "-t", f"{seconds:.3f}", out],
                           stdin=subprocess.PIPE)
    fn = DRAW[spec["type"]]
    for f in range(n):
        enc.stdin.write(fn(spec, f / max(n - 1, 1), base).tobytes())
    enc.stdin.close(); enc.wait()
