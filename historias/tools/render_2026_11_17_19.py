"""Historias martes 17-nov y jueves 19-nov con llamada a la acción (se publican solas desde Metricool,
así que la CTA va en la imagen: respuesta por mensaje privado). Ejecutar desde la raíz del repo."""
import asyncio
from playwright.async_api import async_playwright
F="/tmp/mont/fonts/ttf/"
FONTS=f"""@font-face{{font-family:M;src:url(file://{F}Montserrat-Medium.ttf);font-weight:500}}
@font-face{{font-family:M;src:url(file://{F}Montserrat-Bold.ttf);font-weight:700}}
@font-face{{font-family:M;src:url(file://{F}Montserrat-ExtraBold.ttf);font-weight:800}}"""
GRAIN='''<svg style="position:absolute;inset:0;width:100%;height:100%;mix-blend-mode:overlay;opacity:{o}" xmlns="http://www.w3.org/2000/svg"><filter id="n"><feTurbulence type="fractalNoise" baseFrequency="0.85" numOctaves="3" stitchTiles="stitch"/><feColorMatrix type="saturate" values="0"/></filter><rect width="100%" height="100%" filter="url(#n)"/></svg>'''
def page(bg_layers, hl, sub, title, subtxt):
    return f"""<html><head><style>{FONTS}body{{margin:0}}</style></head><body>
<div style="position:relative;overflow:hidden;width:1080px;height:1920px;font-family:M">
{bg_layers}
<div style="position:absolute;left:96px;right:96px;top:330px">
<h1 style="margin:0;font-size:116px;font-weight:800;line-height:1.05;letter-spacing:-0.02em;color:#fff">{title}</h1>
<div style="width:140px;height:10px;background:{hl};margin-top:56px"></div>
</div>
<div style="position:absolute;bottom:170px;left:0;width:1080px;text-align:center;font-size:30px;font-weight:700;letter-spacing:.04em;color:{sub};opacity:.85">@alejandro.segura.asesor</div>
</div></body></html>"""

# MARTES (negro): luz azul difusa + interrogación en contorno + rejilla que se desvanece + grano
martes_bg = """
<div style="position:absolute;inset:0;background:#070708"></div>
<div style="position:absolute;inset:0;background:radial-gradient(900px 900px at 85% 95%,#1F4BFF66,transparent 70%),radial-gradient(700px 600px at 0% 0%,#1F4BFF1f,transparent 70%)"></div>
<div style="position:absolute;inset:0;background-image:linear-gradient(#ffffff10 2px,transparent 2px),linear-gradient(90deg,#ffffff10 2px,transparent 2px);background-size:108px 108px;-webkit-mask-image:linear-gradient(180deg,transparent 0%,#000 45%,#000 75%,transparent 100%)"></div>
<div style="position:absolute;right:-300px;bottom:-330px;font-size:1700px;font-weight:800;line-height:1;color:transparent;-webkit-text-stroke:4px #1F4BFF;opacity:.55">?</div>
""" + GRAIN.format(o=.35)

# MIÉRCOLES (azul): degradado con profundidad + ondas finas concéntricas + grano
rings="".join(f'<div style="position:absolute;width:{d}px;height:{d}px;border-radius:50%;border:{w}px solid #0A0A0A;opacity:{op};right:{-d//2+60}px;bottom:{-d//2+60}px"></div>'
              for d,w,op in [(360,30,.85),(620,3,.45),(860,3,.32),(1100,3,.22),(1340,3,.14),(1580,3,.08)])
miercoles_bg = f"""
<div style="position:absolute;inset:0;background:linear-gradient(160deg,#3A62FF 0%,#1F4BFF 45%,#1636C9 100%)"></div>
<div style="position:absolute;inset:0;background:radial-gradient(800px 700px at 15% 10%,#ffffff22,transparent 70%)"></div>
{rings}
""" + GRAIN.format(o=.45)


def cta(txt, bg, fg):
    return (f'<div style="position:absolute;left:96px;right:96px;bottom:330px;display:flex;align-items:center;gap:24px">'
            f'<div style="background:{bg};color:{fg};padding:26px 40px;border-radius:999px;font-size:44px;font-weight:800;white-space:nowrap">{txt}</div>'
            f'<div style="font-size:70px">👇</div></div>')
items = {
 "historias/2026-11-17-martes.jpg": page(martes_bg,"#1F4BFF","#C9CDD8",
    'Si mañana te fueras una semana, ¿qué se <span style="color:#1F4BFF">rompería</span> primero en tu negocio?',"")
    .replace("font-size:116px","font-size:100px").replace("</div></body>", cta("Respóndeme a esta historia","#1F4BFF","#fff")+"</div></body>"),
 "historias/2026-11-19-jueves.jpg": page(miercoles_bg,"#0A0A0A","#E6EBFF",
    '¿Cuántas horas a la semana son de verdad <span style="color:#0A0A0A">para&nbsp;ti</span>?',"")
    .replace("font-size:116px","font-size:100px").replace("</div></body>", '<div style="position:absolute;left:96px;right:96px;top:1060px;font-size:44px;font-weight:700;line-height:1.3;color:#E6EBFF">Para ti, tu familia, tus amigos.<br>No para el negocio.</div>'+cta("Respóndeme con un número","#0A0A0A","#fff")+"</div></body>"),
}
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch(executable_path="/usr/bin/google-chrome",args=["--allow-file-access-from-files"])
        pg=await b.new_page(viewport={"width":1080,"height":1920})
        for path,h in items.items():
            open("/tmp/hcta.html","w").write(h)
            await pg.goto("file:///tmp/hcta.html"); await pg.evaluate("document.fonts.ready"); await pg.wait_for_timeout(400)
            await pg.screenshot(path=path,type="jpeg",quality=92)
        await b.close()
asyncio.run(main())
print("ok")
