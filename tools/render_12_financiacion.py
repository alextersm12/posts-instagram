"""Carrusel 12-financiacion (azul, 7 diapositivas, explicativo, versión gráfica) + historia de aviso.
Uso: python3 tools/render_12_financiacion.py
  -> 12-financiacion/1..7.jpg (1080x1350) y historias/2026-11-13-viernes-post.jpg (1080x1920)
Requiere Montserrat en /tmp/mont/fonts/ttf (git clone github.com/JulietaUla/Montserrat /tmp/mont)."""
import asyncio, os
from playwright.async_api import async_playwright
from PIL import Image

F = "/tmp/mont/fonts/ttf/"
FONTS = f"""@font-face{{font-family:M;src:url(file://{F}Montserrat-Medium.ttf);font-weight:500}}
@font-face{{font-family:M;src:url(file://{F}Montserrat-Bold.ttf);font-weight:700}}
@font-face{{font-family:M;src:url(file://{F}Montserrat-ExtraBold.ttf);font-weight:800}}"""
GRAIN = ('<svg style="position:absolute;inset:0;width:100%;height:100%;mix-blend-mode:overlay;opacity:{o}" '
         'xmlns="http://www.w3.org/2000/svg"><filter id="n"><feTurbulence type="fractalNoise" baseFrequency="0.85" '
         'numOctaves="3" stitchTiles="stitch"/><feColorMatrix type="saturate" values="0"/></filter>'
         '<rect width="100%" height="100%" filter="url(#n)"/></svg>')
BLUE = ('<div style="position:absolute;inset:0;background:linear-gradient(160deg,#3A62FF 0%,#1F4BFF 45%,#1430B8 100%)"></div>'
        '<div style="position:absolute;inset:0;background:radial-gradient(800px 700px at 12% 8%,#ffffff26,transparent 70%),'
        'radial-gradient(700px 600px at 100% 100%,#0A0A0A40,transparent 70%)"></div>')
GRID = ('<div style="position:absolute;inset:0;background-image:linear-gradient(#ffffff14 2px,transparent 2px),'
        'linear-gradient(90deg,#ffffff14 2px,transparent 2px);background-size:90px 90px;'
        '-webkit-mask-image:radial-gradient(700px 600px at 85% 15%,#000,transparent 75%)"></div>')

ROOT = os.path.join(os.path.dirname(__file__), "..")
W, H, PY, PX = 1080, 1350, 190, 88
K = '<span style="color:#0A0A0A">'
SUB = "#E6EBFF"
TOTAL = 7

# Iconos de línea (blanco, 200x200)
S = 'fill="none" stroke="#fff" stroke-width="9" stroke-linecap="round" stroke-linejoin="round"'
ICONS = {
    "monedas": f'<svg width="200" height="200" viewBox="0 0 200 200"><g {S}><ellipse cx="80" cy="150" rx="55" ry="18"/>'
               f'<path d="M25 150v-24M135 150v-24"/><ellipse cx="80" cy="126" rx="55" ry="18"/><path d="M25 126v-24M135 126v-24"/>'
               f'<ellipse cx="80" cy="102" rx="55" ry="18" fill="#0A0A0A"/><circle cx="150" cy="58" r="34"/><text x="150" y="72" text-anchor="middle" font-family="M" font-weight="800" font-size="40" fill="#fff" stroke="none">€</text></g></svg>',
    "personas": f'<svg width="200" height="200" viewBox="0 0 200 200"><g {S}><circle cx="70" cy="70" r="28"/>'
                f'<path d="M20 165c0-32 22-52 50-52s50 20 50 52"/><circle cx="135" cy="62" r="24" fill="#0A0A0A"/>'
                f'<path d="M108 108c9-6 17-8 27-8 26 0 45 19 45 50"/></g></svg>',
    "documento": f'<svg width="200" height="200" viewBox="0 0 200 200"><g {S}><path d="M50 20h70l35 35v125H50z"/>'
                 f'<path d="M120 20v35h35"/><path d="M75 95h55M75 120h55"/><circle cx="140" cy="155" r="30" fill="#0A0A0A"/>'
                 f'<path d="M127 155l9 9 17-18"/></g></svg>',
    "banco": f'<svg width="200" height="200" viewBox="0 0 200 200"><g {S}><path d="M20 70l80-45 80 45z"/>'
             f'<path d="M40 85v65M80 85v65M120 85v65M160 85v65"/><path d="M20 170h160"/></g></svg>',
}


def wrap(inner, w=W, h=H):
    return (f'<html><head><style>{FONTS}body{{margin:0}}</style></head><body>'
            f'<div style="position:relative;overflow:hidden;width:{w}px;height:{h}px;font-family:M;color:#fff">{inner}</div></body></html>')


def page(n, inner, deco="", last=False, grid=True):
    cnt = f'<div style="position:absolute;right:{PX}px;top:{PY-90}px;font-size:28px;font-weight:700;letter-spacing:.08em;color:{SUB}">{n} / {TOTAL}</div>'
    foot = (f'<div style="position:absolute;right:{PX}px;bottom:{PY-60}px;font-size:34px;font-weight:700">Escríbeme por privado <span style="color:#0A0A0A">→</span></div>'
            if last else f'<div style="position:absolute;right:{PX}px;bottom:{PY-70}px;font-size:64px;font-weight:500;color:#0A0A0A">→</div>')
    return wrap(BLUE + (GRID if grid else "") + deco + GRAIN.format(o=.42) + cnt + inner + foot)


def chip(txt, dark=True):
    bg = "background:#0A0A0A;color:#fff" if dark else "border:3px solid #0A0A0A;color:#0A0A0A"
    return f'<span style="display:inline-block;{bg};padding:12px 22px;border-radius:999px;font-size:26px;font-weight:800;letter-spacing:.12em">{txt}</span>'


# ---------- 1 · portada ----------
euro = ''.join(
    f'<div style="position:absolute;right:{-150+o}px;bottom:{-300+o}px;font-size:980px;font-weight:800;line-height:1;'
    f'color:transparent;-webkit-text-stroke:{4 if i else 0}px #0A0A0A;opacity:{.18+i*.12}">€</div>' for i, o in enumerate((60, 30, 0)))
euro += '<div style="position:absolute;right:-150px;bottom:-300px;font-size:980px;font-weight:800;line-height:1;color:#0A0A0A;opacity:.22">€</div>'
s1 = page(1, f'''
<div style="position:absolute;left:{PX}px;top:{PY+40}px">{chip("GUÍA RÁPIDA")}</div>
<div style="position:absolute;left:{PX}px;right:{PX}px;top:{PY+150}px">
  <div style="font-size:124px;font-weight:800;line-height:1;letter-spacing:-0.03em">El dinero<br>no es lo que<br>te {K}frena</span>.</div>
  <div style="display:inline-block;margin-top:50px;background:#fff;color:#1F4BFF;padding:16px 28px;font-size:46px;font-weight:800;transform:rotate(-2deg)">Es no saber a dónde vas.</div>
  <div style="margin-top:70px;font-size:36px;font-weight:700;color:{SUB}">4 formas de financiar tu negocio <span style="color:#0A0A0A">↓</span></div>
</div>''', deco=euro)


# ---------- 2-5 · las 4 formas ----------
def forma(n, num, label, title, icon, items, pro, contra, extra=""):
    big_num = (f'<div style="position:absolute;right:-30px;bottom:-140px;font-size:640px;font-weight:800;line-height:1;'
               f'color:transparent;-webkit-text-stroke:4px #0A0A0A;opacity:.28;letter-spacing:-0.05em">{num}</div>')
    cards = "".join(
        f'<div style="display:flex;align-items:center;gap:26px;margin-top:20px;padding:22px 28px;border-radius:22px;'
        f'background:#ffffff1f;border:2px solid #ffffff40;backdrop-filter:blur(4px)">'
        f'<span style="flex:none;width:52px;height:52px;border-radius:50%;background:#0A0A0A;display:flex;align-items:center;'
        f'justify-content:center;font-size:26px;font-weight:800">{i}</span>'
        f'<span style="font-size:37px;font-weight:500;line-height:1.25">{t}</span></div>' for i, t in enumerate(items, 1))
    pc = (f'<div style="display:flex;gap:16px;margin-top:34px;font-size:32px;font-weight:700">'
          f'<span style="background:#0A0A0A;padding:12px 24px;border-radius:999px">+ {pro}</span>'
          f'<span style="border:3px solid #0A0A0A;padding:9px 24px;border-radius:999px">− {contra}</span></div>')
    body = (f'<div style="position:absolute;right:{PX-10}px;top:{PY+10}px">{ICONS[icon]}</div>'
            f'<div style="position:absolute;left:{PX}px;right:{PX}px;top:{PY+40}px">{chip(num + " · " + label)}'
            f'<div style="margin-top:34px;width:680px;font-size:82px;font-weight:800;line-height:1.04;letter-spacing:-0.02em">{title}</div>'
            f'<div style="margin-top:26px">{cards}</div>{pc}{extra}</div>')
    return page(n, body, deco=big_num, grid=False)


s2 = forma(2, "01", "SIN PEDIR A NADIE", f"Empieza con lo que {K}tienes</span>.", "monedas",
           ["Ahorra con gastos mínimos y empieza pequeño.",
            "Cobra por adelantado: señal o preventa.",
            "Paga a tus proveedores a 30–60 días."],
           "No debes nada", "Es más lento")
s3 = forma(3, "02", "SOCIO O INVERSOR", f"Alguien que pone {K}dinero</span>.", "personas",
           ["Un socio que entra en tu negocio.",
            "Business angels: inversores particulares.",
            "Crowdfunding: muchas personas aportan poco."],
           "Más capital", "Compartes decisiones",
           extra=f'<p style="margin:30px 0 0;font-size:36px;font-weight:700;line-height:1.3">¿Buscas socio? Antes de meter dinero, alguien tiene que {K}mirar los números</span>.</p>')
s4 = forma(4, "03", "AYUDAS PÚBLICAS", f"Dinero que no se {K}devuelve</span>.", "documento",
           ["Tarifa plana: 80 €/mes de cuota el primer año.",
            "Cuota cero (Andalucía): la Junta te devuelve esos 80 €, si está abierta.",
            "Capitalizar el paro: cobras de golpe lo que te queda."],
           "No se devuelve", "Requisitos y plazos")
s5 = forma(5, "04", "PRÉSTAMOS", f"Deuda, pero con {K}ayuda</span>.", "banco",
           ["Microcréditos sin aval (MicroBank).",
            "ENISA Jóvenes: préstamo público para SL.",
            "Banco con aval de Garántia (Andalucía)."],
           "Dinero rápido", "Hay que devolverlo")

# ---------- 6 · camino A → Z que se rompe en la C ----------
xs = [110, 300, 490]
track = ('<svg style="position:absolute;left:0;top:760px" width="1080" height="320">'
         '<path d="M110 160 L490 160" stroke="#fff" stroke-width="10" stroke-linecap="round"/>'
         '<path d="M530 160 L960 160" stroke="#0A0A0A" stroke-width="8" stroke-dasharray="4 26" stroke-linecap="round" opacity=".7"/>'
         + ''.join(f'<circle cx="{x}" cy="160" r="46" fill="{"#0A0A0A" if i < 2 else "#fff"}"/>'
                   f'<text x="{x}" y="176" text-anchor="middle" font-family="M" font-weight="800" font-size="46" '
                   f'fill="{"#fff" if i < 2 else "#1F4BFF"}">{l}</text>' for i, (x, l) in enumerate(zip(xs, "ABC")))
         + '<circle cx="960" cy="160" r="46" fill="none" stroke="#0A0A0A" stroke-width="6" stroke-dasharray="10 10"/>'
         '<text x="960" y="176" text-anchor="middle" font-family="M" font-weight="800" font-size="46" fill="#0A0A0A">Z</text>'
         '<path d="M470 40 l40 40 M510 40 l-40 40" stroke="#0A0A0A" stroke-width="10" stroke-linecap="round"/>'
         '<text x="490" y="270" text-anchor="middle" font-family="M" font-weight="700" font-size="30" fill="#fff">aquí abandona</text></svg>')
s6 = page(6, f'''
<div style="position:absolute;left:{PX}px;right:{PX}px;top:{PY+90}px">
  <div style="font-size:112px;font-weight:800;line-height:1.02;letter-spacing:-0.03em">Ninguna sirve<br>sin un {K}plan</span>.</div>
  <p style="margin:44px 0 0;font-size:46px;font-weight:500;line-height:1.3;color:{SUB}">Quien quiere llegar a la Z de golpe, abandona en la C.</p>
</div>{track}''')

# ---------- 7 · escalones A, B, C ----------
steps = ''.join(
    f'<div style="position:absolute;left:{PX + i*300}px;bottom:{PY+20}px;width:270px;height:{150 + i*140}px;border-radius:18px 18px 0 0;'
    f'{"background:#0A0A0A" if i == 0 else "border:5px solid #0A0A0A;border-bottom:none;box-sizing:border-box"}">'
    f'<div style="position:absolute;left:28px;top:18px;font-size:{110 if i == 0 else 80}px;font-weight:800;'
    f'color:{"#fff" if i == 0 else "transparent"};{"" if i == 0 else "-webkit-text-stroke:3px #0A0A0A"}">{l}</div></div>'
    for i, l in enumerate("ABC"))
s7 = page(7, f'''
<div style="position:absolute;left:{PX}px;right:{PX}px;top:{PY+40}px">
  <div style="font-size:124px;font-weight:800;line-height:1;letter-spacing:-0.03em">Empieza<br>por la {K}A</span>.</div>
  <p style="margin:40px 0 0;font-size:48px;font-weight:700;line-height:1.3">¿Sabes cuál es la tuya?</p>
</div>{steps}''', last=True, grid=False)

# ---------- historia de aviso (1080x1920) ----------
story = wrap(f'''<div style="position:absolute;inset:0;background:#070708"></div>
<div style="position:absolute;inset:0;background:radial-gradient(900px 800px at 50% 45%,#1F4BFF66,transparent 70%)"></div>
{GRAIN.format(o=.35)}
<div style="position:absolute;left:96px;right:96px;top:300px">{chip("NUEVO POST")}
  <div style="margin-top:40px;font-size:96px;font-weight:800;line-height:1.04;letter-spacing:-0.02em">¿El dinero te <span style="color:#1F4BFF">frena</span>?</div>
  <p style="margin:40px 0 0;font-size:46px;font-weight:500;line-height:1.3;color:#B8BCC8">4 formas de financiar tu negocio, con sus pros y contras.</p>
</div>
<div style="position:absolute;left:50%;top:860px;width:600px;margin-left:-300px;transform:rotate(-4deg);box-shadow:0 40px 90px #000a">
  <img src="file://{os.path.abspath(os.path.join(ROOT, '12-financiacion', '1.jpg'))}" style="width:600px;display:block;border-radius:14px">
</div>
<div style="position:absolute;bottom:200px;left:0;width:1080px;text-align:center;font-size:40px;font-weight:800">Lo tienes en mi perfil <span style="color:#1F4BFF">↓</span></div>
<div style="position:absolute;bottom:130px;left:0;width:1080px;text-align:center;font-size:30px;font-weight:700;color:#B8BCC8">@alejandro.segura.asesor</div>''',
             1080, 1920)


async def shot(b, html, path, w, h):
    pg = await b.new_page(viewport={"width": w, "height": h})
    tmp = "/tmp/fin-render.html"
    open(tmp, "w").write(html)
    await pg.goto(f"file://{tmp}")
    await pg.evaluate("document.fonts.ready")
    await pg.wait_for_timeout(300)
    await pg.screenshot(path="/tmp/fin-render.png")
    await pg.close()
    Image.open("/tmp/fin-render.png").convert("RGB").save(path, quality=92)


async def main():
    os.makedirs(os.path.join(ROOT, "12-financiacion"), exist_ok=True)
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path="/usr/bin/google-chrome", args=["--allow-file-access-from-files"])
        for i, html in enumerate([s1, s2, s3, s4, s5, s6, s7], 1):
            await shot(b, html, os.path.join(ROOT, "12-financiacion", f"{i}.jpg"), W, H)
        await shot(b, story, os.path.join(ROOT, "historias", "2026-11-13-viernes-post.jpg"), 1080, 1920)
        await b.close()


asyncio.run(main())
print("ok")
