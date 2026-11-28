"""Reel / Short cover images (1080x1920, text kept inside the 3:4 profile-grid safe area y=240..1680).

python3 cover.py series  <bg_image> out.png "<series title>" "<day label>" "<subtitle>"
python3 cover.py story   <bg_image> out.png "<line 1>" "<line 2>" "<tag>"
"""
import os, sys
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance

W, H = 1080, 1920
FD = os.path.expanduser("~/.fonts")
RQ = ImageFont.Layout.RAQM
SAFFRON, CREAM = (255, 153, 51), (255, 240, 214)


def F(name, size):
    return ImageFont.truetype(os.path.join(FD, name), size, layout_engine=RQ)


def base(bg_path):
    im = Image.open(bg_path).convert("RGB")
    sc = max(W / im.width, H / im.height)
    im = im.resize((int(im.width * sc) + 1, int(im.height * sc) + 1), Image.LANCZOS)
    x, y = (im.width - W) // 2, max(0, (im.height - H) // 3)
    im = im.crop((x, y, x + W, y + H))
    im = ImageEnhance.Contrast(im).enhance(1.08)
    # dark gradients top & bottom for text
    g = Image.new("L", (W, H), 0); d = ImageDraw.Draw(g)
    for yy in range(H):
        a = 0
        if yy < 700: a = int(200 * (1 - yy / 700) ** 1.4)
        if yy > 1050: a = max(a, int(235 * ((yy - 1050) / (H - 1050)) ** 1.1))
        d.line([(0, yy), (W, yy)], fill=a)
    return Image.composite(Image.new("RGB", (W, H), (8, 6, 4)), im, g)


def shadow_text(d, xy, text, font, fill, anchor="mm", stroke=6):
    d.text((xy[0] + 5, xy[1] + 6), text, font=font, fill=(0, 0, 0), anchor=anchor, stroke_width=stroke, stroke_fill=(0, 0, 0))
    d.text(xy, text, font=font, fill=fill, anchor=anchor, stroke_width=stroke, stroke_fill=(20, 8, 0))


def series(bg, out, title, day, sub):
    im = base(bg); d = ImageDraw.Draw(im)
    shadow_text(d, (W // 2, 215), title, F("Mukta-ExtraBold.ttf", 118), SAFFRON)
    # day badge
    bf = F("Mukta-ExtraBold.ttf", 120); tw = d.textlength(day, font=bf)
    bx0, by0 = W / 2 - tw / 2 - 60, 1290
    d.rounded_rectangle([bx0, by0, W / 2 + tw / 2 + 60, by0 + 190], radius=40, fill=SAFFRON, outline=(255, 230, 180), width=6)
    d.text((W / 2, by0 + 92), day, font=bf, fill=(45, 15, 0), anchor="mm")
    shadow_text(d, (W // 2, 1560), sub, F("Mukta-Bold.ttf", 60), CREAM, stroke=4)
    d.text((W // 2, 1650), "EVOLVE UNFILTERED", font=F("Mukta-Bold.ttf", 38), fill=(230, 200, 160), anchor="mm")
    im.save(out)


def story(bg, out, l1, l2, tag):
    im = base(bg); d = ImageDraw.Draw(im)
    tf = F("Mukta-ExtraBold.ttf", 52); tw = d.textlength(tag, font=tf)
    d.rounded_rectangle([W / 2 - tw / 2 - 36, 270, W / 2 + tw / 2 + 36, 360], radius=45, fill=(200, 30, 30))
    d.text((W / 2, 314), tag, font=tf, fill="white", anchor="mm")
    shadow_text(d, (W // 2, 1310), l1, F("Mukta-ExtraBold.ttf", 120), (255, 214, 0))
    shadow_text(d, (W // 2, 1460), l2, F("Mukta-ExtraBold.ttf", 96), (255, 255, 255))
    d.text((W // 2, 1640), "EVOLVE UNFILTERED", font=F("Mukta-Bold.ttf", 38), fill=(230, 200, 160), anchor="mm")
    im.save(out)


if __name__ == "__main__":
    kind = sys.argv[1]
    (series if kind == "series" else story)(*sys.argv[2:7])
