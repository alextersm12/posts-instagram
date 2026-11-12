"""Carrusel 12-financiacion (azul, 7 diapositivas, explicativo).
Uso: python3 tools/render_12_financiacion.py  -> genera 12-financiacion/1..7.jpg
Requiere Montserrat en /tmp/mont/fonts/ttf (git clone github.com/JulietaUla/Montserrat /tmp/mont)."""
import asyncio, os, sys
from playwright.async_api import async_playwright
from PIL import Image

# Mismo fondo y fuentes que tools/render_carrusel_textura.py
F="/tmp/mont/fonts/ttf/"
FONTS=f"""@font-face{{font-family:M;src:url(file://{F}Montserrat-Medium.ttf);font-weight:500}}
@font-face{{font-family:M;src:url(file://{F}Montserrat-Bold.ttf);font-weight:700}}
@font-face{{font-family:M;src:url(file://{F}Montserrat-ExtraBold.ttf);font-weight:800}}"""
GRAIN='<svg style="position:absolute;inset:0;width:100%;height:100%;mix-blend-mode:overlay;opacity:{o}" xmlns="http://www.w3.org/2000/svg"><filter id="n"><feTurbulence type="fractalNoise" baseFrequency="0.85" numOctaves="3" stitchTiles="stitch"/><feColorMatrix type="saturate" values="0"/></filter><rect width="100%" height="100%" filter="url(#n)"/></svg>'
BLUE_BG='<div style="position:absolute;inset:0;background:linear-gradient(160deg,#3A62FF 0%,#1F4BFF 45%,#1636C9 100%)"></div><div style="position:absolute;inset:0;background:radial-gradient(800px 700px at 12% 8%,#ffffff22,transparent 70%)"></div>'+GRAIN.format(o=.45)

OUT = os.path.join(os.path.dirname(__file__), "..", "12-financiacion")
W, H, PY, PX = 1080, 1350, 190, 88
K = '<span style="color:#0A0A0A">'
SUB = "#E6EBFF"
TOTAL = 7


def page(n, inner, deco="", last=False):
    cnt = f'<div style="position:absolute;right:{PX}px;top:{PY-90}px;font-size:28px;font-weight:700;letter-spacing:.08em;color:{SUB}">{n} / {TOTAL}</div>'
    foot = (f'<div style="position:absolute;right:{PX}px;bottom:{PY-60}px;font-size:34px;font-weight:700">Escríbeme por privado <span style="color:#0A0A0A">→</span></div>'
            if last else f'<div style="position:absolute;right:{PX}px;bottom:{PY-70}px;font-size:64px;font-weight:500;color:#0A0A0A">→</div>')
    return f"""<html><head><style>{FONTS}body{{margin:0}}</style></head><body>
<div style="position:relative;overflow:hidden;width:{W}px;height:{H}px;font-family:M;color:#fff">{BLUE_BG}{deco}{cnt}{inner}{foot}</div></body></html>"""


def giant(ch, right=None, left=None, bottom=-420, size=1150, op=.35):
    side = f"right:{right}px" if right is not None else f"left:{left}px"
    return f'<div style="position:absolute;{side};bottom:{bottom}px;font-size:{size}px;font-weight:800;line-height:1;color:transparent;-webkit-text-stroke:4px #0A0A0A;opacity:{op}">{ch}</div>'


def big(title, sub, top=300):
    return (f'<div style="position:absolute;left:{PX}px;right:{PX}px;top:{top}px">'
            f'<div style="font-size:108px;font-weight:800;line-height:1.05;letter-spacing:-0.02em">{title}</div>'
            f'<div style="width:120px;height:10px;background:#0A0A0A;margin-top:48px"></div>'
            f'<p style="margin:44px 0 0;font-size:50px;font-weight:500;line-height:1.3;color:{SUB}">{sub}</p></div>')


def lista(label, title, items, pro, contra, extra=""):
    lis = "".join(
        f'<div style="display:flex;gap:22px;margin-top:34px;font-size:44px;font-weight:500;line-height:1.3">'
        f'<span style="color:#0A0A0A;font-weight:800">—</span><span>{t}</span></div>' for t in items)
    pc = (f'<div style="display:flex;gap:16px;margin-top:56px;font-size:34px;font-weight:700">'
          f'<span style="background:#0A0A0A;padding:12px 22px;border-radius:6px">+ {pro}</span>'
          f'<span style="border:3px solid #0A0A0A;padding:9px 22px;border-radius:6px">− {contra}</span></div>')
    return (f'<div style="position:absolute;left:{PX}px;right:{PX}px;top:{PY+70}px">'
            f'<div style="font-size:30px;font-weight:800;letter-spacing:.14em;color:#0A0A0A">{label}</div>'
            f'<div style="margin-top:30px;font-size:84px;font-weight:800;line-height:1.08;letter-spacing:-0.02em">{title}</div>'
            f'<div style="margin-top:14px">{lis}</div>{pc}{extra}</div>')


slides = [
    page(1, big(f"El dinero no es lo que te {K}frena</span>.", "Es no saber a dónde vas."), giant("€", right=-60, bottom=-330, size=1000, op=.45)),
    page(2, lista("1 · SIN PEDIR A NADIE", f"Empieza con lo que {K}tienes</span>.",
                  ["Ahorra con gastos mínimos y empieza pequeño.",
                   "Cobra por adelantado: señal o preventa.",
                   "Negocia pagar a tus proveedores a 30–60 días."],
                  "No debes nada", "Es más lento")),
    page(3, lista("2 · CON UN SOCIO O INVERSOR", f"Alguien que pone {K}dinero</span>.",
                  ["Un socio que entra en tu negocio.",
                   "Business angels: inversores particulares.",
                   "Crowdfunding: muchas personas aportan poco."],
                  "Más capital", "Compartes decisiones",
                  extra=f'<p style="margin:36px 0 0;font-size:38px;font-weight:700;line-height:1.3">¿Buscas socio? Antes de meter dinero, alguien tiene que {K}mirar los números</span>.</p>')),
    page(4, lista("3 · AYUDAS PÚBLICAS", f"Dinero que no se {K}devuelve</span>.",
                  ["Tarifa plana: 80 €/mes de cuota el primer año.",
                   "Cuota cero (Andalucía): la Junta te devuelve esos 80 €, si la convocatoria está abierta.",
                   "Capitalizar el paro: cobras de golpe lo que te queda para invertirlo."],
                  "No se devuelve", "Requisitos y plazos")),
    page(5, lista("4 · PRÉSTAMOS", f"Deuda, pero con {K}ayuda</span>.",
                  ["Microcréditos sin aval (MicroBank).",
                   "ENISA Jóvenes: préstamo público para sociedades limitadas.",
                   "Banco con aval de Garántia, la sociedad de garantía andaluza."],
                  "Dinero rápido", "Hay que devolverlo")),
    page(6, big(f"Ninguna sirve sin un {K}plan</span>.", "Quien quiere llegar a la Z de golpe, abandona en la C."), giant("Z", right=-60)),
    page(7, big(f"Empieza por la {K}A</span>.", "¿Sabes cuál es la tuya?"), giant("A", right=-120), last=True),
]


async def main():
    os.makedirs(OUT, exist_ok=True)
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path="/usr/bin/google-chrome", args=["--allow-file-access-from-files"])
        for i, html in enumerate(slides, 1):
            pg = await b.new_page(viewport={"width": W, "height": H})
            tmp = f"/tmp/fin-{i}.html"
            open(tmp, "w").write(html)
            await pg.goto(f"file://{tmp}")
            await pg.evaluate("document.fonts.ready")
            await pg.wait_for_timeout(300)
            await pg.screenshot(path=f"/tmp/fin-{i}.png")
            await pg.close()
            Image.open(f"/tmp/fin-{i}.png").convert("RGB").save(os.path.join(OUT, f"{i}.jpg"), quality=92)
        await b.close()


asyncio.run(main())
print("ok")
