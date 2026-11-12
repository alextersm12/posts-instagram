"""Carrusel 13-esclavo (azul, 3 diapositivas, versión gráfica). Lunes 16-nov-2026.
Uso: python3 tools/render_13_esclavo.py -> 13-esclavo/1..3.jpg
Requiere Montserrat en /tmp/mont/fonts/ttf."""
import asyncio, os
from playwright.async_api import async_playwright
from PIL import Image

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
OUT = os.path.join(ROOT, "13-esclavo")
F = "/tmp/mont/fonts/ttf/"
FONTS = f"""@font-face{{font-family:M;src:url(file://{F}Montserrat-Medium.ttf);font-weight:500}}
@font-face{{font-family:M;src:url(file://{F}Montserrat-Bold.ttf);font-weight:700}}
@font-face{{font-family:M;src:url(file://{F}Montserrat-ExtraBold.ttf);font-weight:800}}"""
GRAIN = ('<svg width="1080" height="1350" style="position:absolute;inset:0;mix-blend-mode:overlay;opacity:.42">'
         '<filter id="n"><feTurbulence type="fractalNoise" baseFrequency="0.85" numOctaves="3"/>'
         '<feColorMatrix type="saturate" values="0"/></filter><rect width="100%" height="100%" filter="url(#n)"/></svg>')
BLUE = ('<div style="position:absolute;inset:0;background:linear-gradient(160deg,#3A62FF 0%,#1F4BFF 45%,#1430B8 100%)"></div>'
        '<div style="position:absolute;inset:0;background:radial-gradient(800px 700px at 12% 8%,#ffffff26,transparent 70%),'
        'radial-gradient(700px 600px at 100% 100%,#0A0A0A45,transparent 70%)"></div>')
W, H, PY, PX = 1080, 1350, 190, 88
K = '<span style="color:#0A0A0A">'
SUB = "#E6EBFF"


def page(n, inner, deco="", last=False):
    cnt = f'<div style="position:absolute;right:{PX}px;top:{PY-90}px;font-size:28px;font-weight:700;letter-spacing:.08em;color:{SUB}">{n} / 3</div>'
    foot = (f'<div style="position:absolute;right:{PX}px;bottom:{PY-60}px;font-size:34px;font-weight:700">Escríbeme por privado <span style="color:#0A0A0A">→</span></div>'
            if last else f'<div style="position:absolute;right:{PX}px;bottom:{PY-70}px;font-size:64px;font-weight:500;color:#0A0A0A">→</div>')
    return (f'<html><head><style>{FONTS}body{{margin:0}}</style></head><body>'
            f'<div style="position:relative;overflow:hidden;width:{W}px;height:{H}px;font-family:M;color:#fff">'
            f'{BLUE}{deco}{GRAIN}{cnt}{inner}{foot}</div></body></html>')


def link(cx, cy, rot, w=300, h=150, sw=22, color="#0A0A0A", op=1, gap=False):
    """Eslabón de cadena (óvalo alargado). gap=True lo dibuja abierto (roto)."""
    dash = f'stroke-dasharray="{(w+h)*1.25} 140"' if gap else ""
    return (f'<rect x="{cx-w/2}" y="{cy-h/2}" width="{w}" height="{h}" rx="{h/2}" fill="none" stroke="{color}" '
            f'stroke-width="{sw}" opacity="{op}" {dash} transform="rotate({rot} {cx} {cy})"/>')


# ---------- 1 · gancho: cadena cruzando ----------
chain = ('<svg width="1080" height="1350" style="position:absolute;inset:0">'
         + link(140, 1150, -18, color="#0A0A0A", op=.9)
         + link(370, 1075, -18, h=120, sw=20, color="#fff", op=.85)
         + link(600, 1000, -18, color="#0A0A0A", op=.9)
         + link(830, 925, -18, h=120, sw=20, color="#fff", op=.85)
         + link(1060, 850, -18, color="#0A0A0A", op=.9)
         + '</svg>')
s1 = page(1, f'''
<div style="position:absolute;left:{PX}px;right:{PX}px;top:{PY+60}px">
  <div style="font-size:66px;font-weight:700;line-height:1.15;color:{SUB}">Montaste un negocio<br>para ser libre.</div>
  <div style="margin-top:40px;font-size:132px;font-weight:800;line-height:.98;letter-spacing:-0.035em">Ahora eres<br>su {K}esclavo</span>.</div>
</div>''', deco=chain)

# ---------- 2 · el bucle ----------
cx, cy, r = 540, 760, 250
nodes = [("Abres", -90), ("Apagas<br>fuegos", 30), ("Cierras", 150)]
import math
arcs = ""
for i in range(3):
    a0 = math.radians(-90 + i * 120 + 24)
    a1 = math.radians(-90 + (i + 1) * 120 - 24)
    x0, y0 = cx + r * math.cos(a0), cy + r * math.sin(a0)
    x1, y1 = cx + r * math.cos(a1), cy + r * math.sin(a1)
    arcs += f'<path d="M{x0:.0f} {y0:.0f} A{r} {r} 0 0 1 {x1:.0f} {y1:.0f}" fill="none" stroke="#0A0A0A" stroke-width="12" stroke-linecap="round" marker-end="url(#ar)"/>'
loop = (f'<svg width="1080" height="1350" style="position:absolute;inset:0"><defs><marker id="ar" markerWidth="6" markerHeight="6" '
        f'refX="3" refY="3" orient="auto"><path d="M0 0 L6 3 L0 6z" fill="#0A0A0A"/></marker></defs>{arcs}</svg>')
pills = "".join(
    f'<div style="position:absolute;left:{cx + r*math.cos(math.radians(a)) - 150:.0f}px;top:{cy + r*math.sin(math.radians(a)) - 55:.0f}px;'
    f'width:300px;height:110px;display:flex;align-items:center;justify-content:center;text-align:center;background:#fff;color:#1F4BFF;'
    f'border-radius:999px;font-size:{34 if "<br>" in t else 42}px;font-weight:800;line-height:1.05;box-shadow:0 18px 40px #0A0A0A40">{t}</div>'
    for t, a in nodes)
s2 = page(2, f'''{loop}{pills}
<div style="position:absolute;left:{cx-170}px;top:{cy-50}px;width:340px;text-align:center;font-size:40px;font-weight:800;line-height:1.1">Y mañana,<br>igual.</div>
<div style="position:absolute;left:{PX}px;right:{PX}px;top:{PY+20}px;font-size:84px;font-weight:800;line-height:1.02;letter-spacing:-.02em">Ya no decides.<br>{K}Sobrevives</span>.</div>''')

# ---------- 3 · salir: eslabón roto + CTA ----------
broken = ('<svg width="1080" height="1350" style="position:absolute;inset:0">'
          + link(760, 820, -25, w=360, h=180, sw=24, color="#0A0A0A", op=.9, gap=True)
          + link(500, 940, -25, w=300, h=140, sw=20, color="#fff", op=.5)
          + '</svg>')
s3 = page(3, f'''
<div style="position:absolute;left:{PX}px;right:{PX}px;top:{PY+40}px">
  <div style="font-size:72px;font-weight:800;line-height:1.08;letter-spacing:-.02em">Salir del bucle empieza por mirarlo {K}desde fuera</span>.</div>
  <div style="display:inline-block;margin-top:70px;background:#fff;color:#1F4BFF;padding:22px 36px;font-size:72px;font-weight:800;transform:rotate(-2deg);box-shadow:0 18px 40px #0A0A0A40">¿Te ayudo a salir?</div>
</div>''', deco=broken, last=True)


async def main():
    os.makedirs(OUT, exist_ok=True)
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path="/usr/bin/google-chrome", args=["--allow-file-access-from-files"])
        for i, html in enumerate([s1, s2, s3], 1):
            pg = await b.new_page(viewport={"width": W, "height": H})
            open("/tmp/esc.html", "w").write(html)
            await pg.goto("file:///tmp/esc.html")
            await pg.evaluate("document.fonts.ready")
            await pg.wait_for_timeout(300)
            await pg.screenshot(path="/tmp/esc.png")
            await pg.close()
            Image.open("/tmp/esc.png").convert("RGB").save(os.path.join(OUT, f"{i}.jpg"), quality=92)
        await b.close()


asyncio.run(main())
print("ok")
