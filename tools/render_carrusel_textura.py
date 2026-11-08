import asyncio
from playwright.async_api import async_playwright
F="/tmp/mont/fonts/ttf/"
FONTS=f"""@font-face{{font-family:M;src:url(file://{F}Montserrat-Medium.ttf);font-weight:500}}
@font-face{{font-family:M;src:url(file://{F}Montserrat-Bold.ttf);font-weight:700}}
@font-face{{font-family:M;src:url(file://{F}Montserrat-ExtraBold.ttf);font-weight:800}}"""
GRAIN='<svg style="position:absolute;inset:0;width:100%;height:100%;mix-blend-mode:overlay;opacity:{o}" xmlns="http://www.w3.org/2000/svg"><filter id="n"><feTurbulence type="fractalNoise" baseFrequency="0.85" numOctaves="3" stitchTiles="stitch"/><feColorMatrix type="saturate" values="0"/></filter><rect width="100%" height="100%" filter="url(#n)"/></svg>'
BLUE_BG='<div style="position:absolute;inset:0;background:linear-gradient(160deg,#3A62FF 0%,#1F4BFF 45%,#1636C9 100%)"></div><div style="position:absolute;inset:0;background:radial-gradient(800px 700px at 12% 8%,#ffffff22,transparent 70%)"></div>'+GRAIN.format(o=.45)
BLACK_BG='<div style="position:absolute;inset:0;background:#070708"></div><div style="position:absolute;inset:0;background:radial-gradient(900px 800px at 90% 100%,#1F4BFF55,transparent 70%),radial-gradient(600px 500px at 0% 0%,#1F4BFF1a,transparent 70%)"></div>'+GRAIN.format(o=.35)
def slide(W,H,bg,deco,body,n,total,last,sub,hl,pad=(190,88)):
    py,px=pad
    foot = f'<div style="position:absolute;right:{px}px;bottom:{py-60}px;font-size:{34 if W==1080 and H==1350 else 40}px;font-weight:700;color:#fff">Escríbeme por privado <span style="color:{hl}">→</span></div>' if last else f'<div style="position:absolute;right:{px}px;bottom:{py-70}px;font-size:64px;font-weight:500;color:{hl}">→</div>'
    cnt = f'<div style="position:absolute;right:{px}px;top:{py-90}px;font-size:28px;font-weight:700;letter-spacing:.08em;color:{sub}">{n} / {total}</div>' if total else ''
    return f"""<html><head><style>{FONTS}body{{margin:0}}</style></head><body><div style="position:relative;overflow:hidden;width:{W}px;height:{H}px;font-family:M;color:#fff">{bg}{deco}{cnt}{body}{foot if n else ''}</div></body></html>"""
def T(txt,size=104,top=None,bottom=None,hl="#fff",bar=True,px=88,extra=""):
    pos = f"top:{top}px" if top is not None else f"bottom:{bottom}px"
    b = f'<div style="width:120px;height:10px;background:{hl};margin-top:48px"></div>' if bar else ''
    return f'<div style="position:absolute;left:{px}px;right:{px}px;{pos}"><div style="font-size:{size}px;font-weight:800;line-height:1.06;letter-spacing:-0.02em">{txt}</div>{b}{extra}</div>'
P=lambda t,c: f'<p style="margin:40px 0 0;font-size:44px;font-weight:500;line-height:1.35;color:{c}">{t}</p>'

# 09 DELEGAR (azul, palabra destacada negra). Elemento: "7" gigante en contorno (una semana fuera)
K='<span style="color:#0A0A0A">'
seven='<div style="position:absolute;right:-60px;bottom:-560px;font-size:1250px;font-weight:800;line-height:1;color:transparent;-webkit-text-stroke:4px #0A0A0A;opacity:.35">7</div>'
d=[
 slide(1080,1350,BLUE_BG,seven,T(f'Si te vas una semana, ¿tu empresa sigue {K}funcionando</span>?',top=300,hl="#0A0A0A"),1,3,False,"#E6EBFF","#0A0A0A"),
 slide(1080,1350,BLUE_BG,'',T(f'Cuando todo pasa por ti, el {K}cuello de botella</span> eres tú.',size=96,bottom=420,hl="#0A0A0A",extra=P("No es falta de equipo. Es que nadie más sabe decidir.","#E6EBFF")),2,3,False,"#E6EBFF","#0A0A0A"),
 slide(1080,1350,BLUE_BG,'',T(f'¿Cuántas decisiones al día pasan {K}solo por ti</span>?',size=96,top=300,bar=False,extra=P("Ordenar quién decide qué es el primer paso para salir del día a día.","#E6EBFF").replace("margin:40px","margin:130px")),3,3,True,"#E6EBFF","#0A0A0A"),
]
# 10 CLIENTES / VENTAS (negro, palabra destacada azul). Elemento: camino discontinuo que serpentea (no sabes por dónde viene)
B='<span style="color:#1F4BFF">'
path='<svg style="position:absolute;inset:0" width="1080" height="1350"><g transform="translate(0,230)"><path d="M-40 1180 C 220 1040, 120 860, 420 880 S 760 1120, 820 860 S 980 520, 1140 600" fill="none" stroke="#1F4BFF" stroke-width="5" stroke-dasharray="22 18" opacity=".8"/><circle cx="1000" cy="560" r="12" fill="#1F4BFF"/></g></svg>'
grid='<div style="position:absolute;inset:0;background-image:linear-gradient(#ffffff0e 2px,transparent 2px),linear-gradient(90deg,#ffffff0e 2px,transparent 2px);background-size:108px 108px;-webkit-mask-image:linear-gradient(180deg,transparent,#000 50%,transparent)"></div>'
v=[
 slide(1080,1350,BLACK_BG,grid+path,T(f'¿Sabes de dónde vendrá tu {B}próximo cliente</span>?',top=300,hl="#1F4BFF"),1,3,False,"#B8BCC8","#1F4BFF"),
 slide(1080,1350,BLACK_BG,'',T(f'Si solo depende del boca a boca, no lo controlas tú. Lo controla la {B}suerte</span>.',size=88,top=360,hl="#1F4BFF"),2,3,False,"#B8BCC8","#1F4BFF"),
 slide(1080,1350,BLACK_BG,'<div style="position:absolute;left:-380px;bottom:-420px;width:760px;height:760px;border-radius:50%;border:3px solid #1F4BFF;opacity:.5"></div>',T(f'Un mes flojo no avisa. Saber cómo entran tus clientes, {B}sí</span>.',size=92,top=300,bar=False,extra=P("Ahí empieza vender con cabeza y no con suerte.","#B8BCC8").replace("margin:40px","margin:110px")),3,3,True,"#B8BCC8","#1F4BFF"),
]
# HISTORIAS DESTACADO "CÓMO TRABAJO" (1080x1920, negro con luz azul)
SB=BLACK_BG
def st(head,txt,n,last=False,big=False):
    body=f'<div style="position:absolute;left:96px;right:96px;top:{560 if big else 420}px"><div style="font-size:30px;font-weight:700;letter-spacing:.14em;color:#1F4BFF">{head}</div><div style="margin-top:36px;font-size:{120 if big else 84}px;font-weight:800;line-height:1.08;letter-spacing:-0.02em">{txt}</div><div style="width:120px;height:10px;background:#1F4BFF;margin-top:56px"></div></div>'
    cta = '<div style="position:absolute;left:96px;bottom:360px;font-size:46px;font-weight:700">Escríbeme por privado <span style="color:#1F4BFF">→</span></div>' if last else ''
    h='<div style="position:absolute;bottom:170px;left:0;width:1080px;text-align:center;font-size:30px;font-weight:700;color:#B8BCC8">@alejandro.segura.asesor</div>'
    dots=''.join(f'<div style="width:{60 if i==n else 24}px;height:8px;border-radius:4px;background:{"#1F4BFF" if i==n else "#ffffff40"}"></div>' for i in range(1,5))
    return f"""<html><head><style>{FONTS}body{{margin:0}}</style></head><body><div style="position:relative;overflow:hidden;width:1080px;height:1920px;font-family:M;color:#fff">{SB}<div style="position:absolute;left:96px;top:230px;display:flex;gap:12px">{dots}</div>{body}{cta}{h}</div></body></html>"""
c=[
 st("CÓMO TRABAJO","Entender.<br><span style='color:#1F4BFF'>Priorizar.</span><br>Decidir.",1,big=True),
 st("PARA QUIÉN","Para el empresario que apaga fuegos todo el día y no llega a lo <span style='color:#1F4BFF'>importante</span>.",2),
 st("CÓMO EMPEZAMOS","Una primera conversación. Me cuentas tu empresa y te digo con sinceridad si puedo <span style='color:#1F4BFF'>aportarte</span> algo.",3),
 st("Y DESPUÉS","Ordeno qué tocar primero y por qué. La decisión siempre es <span style='color:#1F4BFF'>tuya</span>.",4,last=True),
]
jobs=[(f"09-delegar-{i+1}",h,1080,1350) for i,h in enumerate(d)]+[(f"10-proximo-cliente-{i+1}",h,1080,1350) for i,h in enumerate(v)]+[(f"como-trabajo-{i+1}",h,1080,1920) for i,h in enumerate(c)]
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch(executable_path="/usr/bin/google-chrome",args=["--allow-file-access-from-files"])
        for n,h,W,H in jobs:
            pg=await b.new_page(viewport={"width":W,"height":H})
            open(f"{n}.html","w").write(h); await pg.goto(f"file:///home/claude/semana/{n}.html"); await pg.evaluate("document.fonts.ready"); await pg.wait_for_timeout(300)
            await pg.screenshot(path=f"{n}.png"); await pg.close()
        await b.close()
asyncio.run(main())
from PIL import Image
def sheet(names,w,h,out):
    s=Image.new("RGB",(len(names)*(w+20)+20,h+40),"white")
    for i,n in enumerate(names): s.paste(Image.open(n+".png").resize((w,h)),(20+i*(w+20),20))
    s.save(out)
sheet([f"09-delegar-{i}" for i in (1,2,3)],400,500,"prev-09.png")
sheet([f"10-proximo-cliente-{i}" for i in (1,2,3)],400,500,"prev-10.png")
sheet([f"como-trabajo-{i}" for i in (1,2,3,4)],300,533,"prev-ct.png")
print("ok")
