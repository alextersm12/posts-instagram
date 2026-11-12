"""Portada del Reel 13-esclavo (1080x1920, azul) -> 13-esclavo/portada-reel-esclavo.jpg
El texto queda dentro de la franja central 1080x1440 (lo que se ve en la cuadrícula del perfil)."""
import asyncio, os
from playwright.async_api import async_playwright
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
F = "/tmp/mont/fonts/ttf/"


def link(cx, cy, rot, w, h, sw, col, op):
    return (f'<rect x="{cx-w/2}" y="{cy-h/2}" width="{w}" height="{h}" rx="{h/2}" fill="none" stroke="{col}" '
            f'stroke-width="{sw}" opacity="{op}" transform="rotate({rot} {cx} {cy})"/>')


chain = "".join(link(40 + i * 215, 1500 - i * 80, -20, 300, 120 if i % 2 else 150, 20 if i % 2 else 24,
                     "#fff" if i % 2 else "#0A0A0A", .9) for i in range(6))
html = f"""<html><head><style>
@font-face{{font-family:M;src:url(file://{F}Montserrat-Bold.ttf);font-weight:700}}
@font-face{{font-family:M;src:url(file://{F}Montserrat-ExtraBold.ttf);font-weight:800}}
body{{margin:0}}</style></head><body><div style="position:relative;overflow:hidden;width:1080px;height:1920px;font-family:M;color:#fff">
<div style="position:absolute;inset:0;background:linear-gradient(160deg,#3A62FF 0%,#1F4BFF 45%,#1430B8 100%)"></div>
<div style="position:absolute;inset:0;background:radial-gradient(800px 700px at 12% 20%,#ffffff26,transparent 70%),radial-gradient(700px 600px at 100% 100%,#0A0A0A45,transparent 70%)"></div>
<svg width="1080" height="1920" style="position:absolute;inset:0">{chain}</svg>
<svg width="1080" height="1920" style="position:absolute;inset:0;mix-blend-mode:overlay;opacity:.42"><filter id="n"><feTurbulence type="fractalNoise" baseFrequency="0.85" numOctaves="3"/><feColorMatrix type="saturate" values="0"/></filter><rect width="100%" height="100%" filter="url(#n)"/></svg>
<div style="position:absolute;left:90px;right:90px;top:470px">
 <div style="font-size:66px;font-weight:700;line-height:1.15;color:#E6EBFF">Montaste un negocio<br>para ser libre.</div>
 <div style="margin-top:40px;font-size:150px;font-weight:800;line-height:.98;letter-spacing:-.035em">¿Y ahora<br>eres su<br><span style="color:#0A0A0A">esclavo</span>?</div>
</div></div></body></html>"""


async def m():
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path="/usr/bin/google-chrome", args=["--allow-file-access-from-files"])
        pg = await b.new_page(viewport={"width": 1080, "height": 1920})
        open("/tmp/portada13.html", "w").write(html)
        await pg.goto("file:///tmp/portada13.html")
        await pg.evaluate("document.fonts.ready")
        await pg.wait_for_timeout(300)
        await pg.screenshot(path=os.path.join(ROOT, "13-esclavo", "portada-reel-esclavo.jpg"), type="jpeg", quality=92)
        await b.close()

asyncio.run(m())
print("ok")
