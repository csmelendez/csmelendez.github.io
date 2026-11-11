from PIL import Image, ImageDraw, ImageFont
import sys
W,H=1200,630; RED=(179,0,51); INK=(40,54,60); GREY=(86,101,108); BG=(246,247,250); LINE=(218,223,226)
D="/usr/share/fonts/truetype/dejavu/"; f=lambda n,s: ImageFont.truetype(D+n,s)
B,R="DejaVuSans-Bold.ttf","DejaVuSans.ttf"
im=Image.new("RGB",(W,H),BG); d=ImageDraw.Draw(im); d.rectangle([0,0,22,H],fill=RED)
x=70
d.text((x,62),"RECURSOS DOCENTES ABIERTOS",font=f(B,24),fill=RED)
d.text((x,104),"Herramientas y materiales",font=f(B,52),fill=INK)
d.text((x,166),"de tecnología sanitaria",font=f(B,52),fill=INK)
cols=[("MDR/IVDR",["Clasificador de","productos sanitarios"]),("PICO",["Buscador de","evidencia"]),("Vídeos",["Protocolos de","electromedicina"])]
cx=x
for big,lab in cols:
    d.rounded_rectangle([cx,262,cx+330,432],radius=16,fill=(255,255,255),outline=LINE,width=2)
    d.text((cx+24,286),big,font=f(B,46),fill=RED)
    d.text((cx+24,356),lab[0],font=f(R,24),fill=GREY)
    d.text((cx+24,388),lab[1],font=f(R,24),fill=GREY)
    cx+=356
d.text((x,462),"Gratuitos · Sin registro · Funcionan en el navegador",font=f(R,24),fill=INK)
d.line([(70,520),(W-70,520)],fill=LINE,width=2)
d.text((x,545),"César Sánchez Meléndez",font=f(B,26),fill=INK)
d.text((x,582),"Profesor titular · Universidad de Castilla-La Mancha",font=f(R,22),fill=GREY)
im.save(sys.argv[1],optimize=True); print("ok")
