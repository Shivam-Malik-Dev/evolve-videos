"""Thumbnail maker: python3 thumbnail.py bg.png out.png "LINE1" "LINE2" "TAG" [down|up|none]"""
import sys
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance
import os
FD=os.path.expanduser("~/.fonts"); RQ=ImageFont.Layout.RAQM
W,H=1920,1080
bg=Image.open(sys.argv[1]).convert("RGB").resize((W,H))
bg=ImageEnhance.Brightness(bg.filter(ImageFilter.GaussianBlur(3))).enhance(0.45)
d=ImageDraw.Draw(bg)
# left dark gradient for text
grad=Image.new("L",(W,H)); gd=ImageDraw.Draw(grad)
for x in range(W): gd.line([(x,0),(x,H)],fill=int(210*max(0,1-x/(W*0.75))))
bg=Image.composite(Image.new("RGB",(W,H),(0,0,0)),bg,grad); d=ImageDraw.Draw(bg)
l1,l2,tag=sys.argv[3],sys.argv[4],sys.argv[5]; arrow=sys.argv[6] if len(sys.argv)>6 else "down"
f1=ImageFont.truetype(f"{FD}/Mukta-ExtraBold.ttf",250,layout_engine=RQ)
f2=ImageFont.truetype(f"{FD}/Mukta-ExtraBold.ttf",170,layout_engine=RQ)
ft=ImageFont.truetype(f"{FD}/Mukta-ExtraBold.ttf",80,layout_engine=RQ)
# tag pill
tw=d.textlength(tag,font=ft); d.rounded_rectangle([90,90,90+tw+80,210],radius=30,fill=(220,30,30)); d.text((130,150),tag,font=ft,fill="white",anchor="lm")
for dx,dy in [(8,8)]:
    d.text((90+dx,330+dy),l1,font=f1,fill=(0,0,0),anchor="lm"); d.text((95+dx,620+dy),l2,font=f2,fill=(0,0,0),anchor="lm")
d.text((90,330),l1,font=f1,fill=(255,214,0),anchor="lm",stroke_width=6,stroke_fill=(0,0,0))
d.text((95,620),l2,font=f2,fill=(255,255,255),anchor="lm",stroke_width=6,stroke_fill=(0,0,0))
if arrow!="none":
    col=(235,40,40) if arrow=="down" else (40,200,90)
    pts=[(1480,260),(1600,470),(1680,400),(1820,820)] if arrow=="down" else [(1350,800),(1500,600),(1580,670),(1760,280)]
    d.line(pts,fill=col,width=40,joint="curve")
    x,y=pts[-1]; px,py=pts[-2]
    import math; a=math.atan2(y-py,x-px)
    tip=[(x+60*math.cos(a),y+60*math.sin(a)),(x+70*math.cos(a+2.4),y+70*math.sin(a+2.4)),(x+70*math.cos(a-2.4),y+70*math.sin(a-2.4))]
    d.polygon(tip,fill=col)
bg.save(sys.argv[2]); bg.resize((1280,720),Image.LANCZOS).save(sys.argv[2].replace(".png","_1280.png"))
