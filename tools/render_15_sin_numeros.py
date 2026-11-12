"""Carrusel 15-sin-numeros (negro, 3 diapositivas, versión gráfica). Jueves 19-nov-2026.
Uso: python3 tools/render_15_sin_numeros.py -> 15-sin-numeros/1..3.jpg"""
import asyncio, os
from playwright.async_api import async_playwright
from PIL import Image

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
OUT = os.path.join(ROOT, "15-sin-numeros")
F = "/tmp/mont/fonts/ttf/"
FONTS = f"""@font-face{{font-family:M;src:url(file://{F}Montserrat-Medium.ttf);font-weight:500}}
@font-face{{font-family:M;src:url(file://{F}Montserrat-Bold.ttf);font-weight:700}}
@font-face{{font-family:M;src:url(file://{F}Montserrat-ExtraBold.ttf);font-weight:800}}"""
GRAIN = ('<svg width="1080" height="1350" style="position:absolute;inset:0;mix-blend-mode:overlay;opacity:.35">'
         '<filter id="n"><feTurbulence type="fractalNoise" baseFrequency="0.85" numOctaves="3"/>'
         '<feColorMatrix type="saturate" values="0"/></filter><rect width="100%" height="100%" filter="url(#n)"/></svg>')
BLACK = ('<div style="position:absolute;inset:0;background:#070708"></div>'
         '<div style="position:absolute;inset:0;background:radial-gradient(900px 800px at 90% 100%,#1F4BFF55,transparent 70%),'
         'radial-gradient(600px 500px at 0% 0%,#1F4BFF1a,transparent 70%)"></div>'
         '<div style="position:absolute;inset:0;background-image:linear-gradient(#ffffff0e 2px,transparent 2px),'
         'linear-gradient(90deg,#ffffff0e 2px,transparent 2px);background-size:90px 90px;'
         '-webkit-mask-image:linear-gradient(180deg,transparent,#000 50%,transparent)"></div>')
W, H, PY, PX = 1080, 1350, 190, 88
B = '<span style="color:#1F4BFF">'
SUB = "#B8BCC8"


def page(n, inner, deco="", last=False):
    cnt = f'<div style="position:absolute;right:{PX}px;top:{PY-90}px;font-size:28px;font-weight:700;letter-spacing:.08em;color:{SUB}">{n} / 3</div>'
    foot = (f'<div style="position:absolute;right:{PX}px;bottom:{PY-60}px;font-size:34px;font-weight:700">Escríbeme por privado <span style="color:#1F4BFF">→</span></div>'
            if last else f'<div style="position:absolute;right:{PX}px;bottom:{PY-70}px;font-size:64px;font-weight:500;color:#1F4BFF">→</div>')
    return (f'<html><head><style>{FONTS}body{{margin:0}}</style></head><body>'
            f'<div style="position:relative;overflow:hidden;width:{W}px;height:{H}px;font-family:M;color:#fff">'
            f'{BLACK}{deco}{GRAIN}{cnt}{inner}{foot}</div></body></html>')


# 1 · pantalla de calculadora con interrogaciones
calc = ('<div style="position:absolute;left:88px;right:88px;top:720px;height:300px;border:5px solid #1F4BFF;border-radius:36px;'
        'background:#1F4BFF14;display:flex;align-items:center;justify-content:flex-end;padding:0 56px;box-sizing:border-box">'
        '<span style="font-size:190px;font-weight:800;letter-spacing:.05em;color:transparent;-webkit-text-stroke:4px #1F4BFF">¿?.¿??</span>'
        '<span style="font-size:120px;font-weight:800;color:#1F4BFF;margin-left:24px">€</span></div>'
        '<div style="position:absolute;left:120px;top:690px;background:#070708;padding:0 16px;font-size:28px;font-weight:800;letter-spacing:.14em;color:#1F4BFF">FACTURACIÓN DEL MES</div>')
s1 = page(1, f'''<div style="position:absolute;left:{PX}px;right:{PX}px;top:{PY+70}px;font-size:104px;font-weight:800;line-height:1.02;letter-spacing:-.03em">Hay empresas que no saben ni lo que {B}facturan</span>.</div>''', deco=calc)

# 2 · deciden igual
chips = "".join(f'<span style="display:inline-block;margin:0 14px 18px 0;padding:16px 30px;border-radius:999px;border:3px solid #fff;font-size:44px;font-weight:700">{t}</span>'
                for t in ["Contratan", "Bajan precios", "Piden préstamos", "Invierten"])
s2 = page(2, f'''<div style="position:absolute;left:{PX}px;right:{PX}px;top:{PY+30}px">
 <div style="font-size:66px;font-weight:800;line-height:1.1">Y aun así deciden cada día:</div>
 <div style="margin-top:44px">{chips}</div>
 <div style="margin-top:30px;font-size:52px;font-weight:700;color:{SUB}">…a ciegas.</div>
 <div style="margin-top:80px;font-size:84px;font-weight:800;line-height:1.05;letter-spacing:-.02em">Decidir sin números no es decidir.<br>Es {B}apostar</span>.</div>
</div>''')

# 3 · lo mínimo
ghost = "".join(f'<span style="display:inline-block;margin:0 12px 14px 0;padding:10px 22px;border-radius:999px;border:2px solid #ffffff40;color:#ffffff70;font-size:30px;font-weight:700">{t}</span>'
                for t in ["Previsión de cobros", "Previsión de pagos", "Impuestos", "Costes fijos", "IVA", "Stock", "…y mil cosas más"])
must = "".join(f'<div style="display:flex;align-items:center;gap:24px;margin-top:20px;padding:22px 30px;border-radius:22px;background:#1F4BFF;font-size:44px;font-weight:800">'
               f'<span style="flex:none;width:58px;height:58px;border-radius:50%;background:#fff;color:#1F4BFF;display:flex;align-items:center;justify-content:center;font-size:30px">{i}</span>{t}</div>'
               for i, t in enumerate(["Cuánto entra", "Cuánto te queda", "Cuánto tienes en el banco"], 1))
s3 = page(3, f'''<div style="position:absolute;left:{PX}px;right:{PX}px;top:{PY-10}px">
 <div>{ghost}</div>
 <div style="margin-top:26px;font-size:62px;font-weight:800;line-height:1.08">Pero como mínimo,<br>sabe estas {B}3</span>:</div>
 <div style="margin-top:16px">{must}</div>
 <div style="margin-top:34px;font-size:40px;font-weight:700;color:{SUB}">Mañana te explico cada una.</div>
</div>''', last=True)


async def main():
    os.makedirs(OUT, exist_ok=True)
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path="/usr/bin/google-chrome", args=["--allow-file-access-from-files"])
        for i, html in enumerate([s1, s2, s3], 1):
            pg = await b.new_page(viewport={"width": W, "height": H})
            open("/tmp/s15.html", "w").write(html)
            await pg.goto("file:///tmp/s15.html")
            await pg.evaluate("document.fonts.ready")
            await pg.wait_for_timeout(300)
            await pg.screenshot(path="/tmp/s15.png")
            await pg.close()
            Image.open("/tmp/s15.png").convert("RGB").save(os.path.join(OUT, f"{i}.jpg"), quality=92)
        await b.close()


asyncio.run(main())
print("ok")
