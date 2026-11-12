"""Historia de aviso del Reel 12-financiacion (1080x1920) -> historias/2026-11-13-viernes-reel.jpg"""
import asyncio, os
from playwright.async_api import async_playwright
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
F = "/tmp/mont/fonts/ttf/"
html = f"""<html><head><style>
@font-face{{font-family:M;src:url(file://{F}Montserrat-Medium.ttf);font-weight:500}}
@font-face{{font-family:M;src:url(file://{F}Montserrat-ExtraBold.ttf);font-weight:800}}
@font-face{{font-family:M;src:url(file://{F}Montserrat-Bold.ttf);font-weight:700}}
body{{margin:0}}</style></head><body><div style="position:relative;overflow:hidden;width:1080px;height:1920px;font-family:M;color:#fff">
<div style="position:absolute;inset:0;background:linear-gradient(160deg,#3A62FF 0%,#1F4BFF 45%,#1430B8 100%)"></div>
<svg width="1080" height="1920" style="position:absolute;inset:0;mix-blend-mode:overlay;opacity:.4"><filter id="n"><feTurbulence type="fractalNoise" baseFrequency="0.85" numOctaves="3"/><feColorMatrix type="saturate" values="0"/></filter><rect width="100%" height="100%" filter="url(#n)"/></svg>
<div style="position:absolute;left:96px;right:96px;top:250px">
 <span style="display:inline-block;background:#0A0A0A;padding:14px 26px;border-radius:999px;font-size:30px;font-weight:800;letter-spacing:.12em">▶ NUEVO VÍDEO</span>
 <div style="margin-top:36px;font-size:92px;font-weight:800;line-height:1.04;letter-spacing:-.02em">¿El dinero te <span style="color:#0A0A0A">frena</span>?</div>
 <p style="margin:30px 0 0;font-size:44px;font-weight:500;line-height:1.3;color:#E6EBFF">4 formas de financiar tu negocio en 40 segundos.</p>
</div>
<div style="position:absolute;left:50%;top:760px;width:520px;margin-left:-260px;transform:rotate(-4deg);box-shadow:0 40px 90px #000a;border-radius:18px;overflow:hidden">
 <img src="file://{ROOT}/12-financiacion/portada-reel.jpg" style="width:520px;display:block">
 <div style="position:absolute;left:50%;top:50%;width:150px;height:150px;margin:-75px 0 0 -75px;border-radius:50%;background:#ffffffe6;display:flex;align-items:center;justify-content:center"><div style="width:0;height:0;border-left:56px solid #1F4BFF;border-top:34px solid transparent;border-bottom:34px solid transparent;margin-left:14px"></div></div>
</div>
<div style="position:absolute;bottom:220px;left:0;width:1080px;text-align:center;font-size:44px;font-weight:800">Lo tienes en mi perfil <span style="color:#0A0A0A">↓</span></div>
<div style="position:absolute;bottom:140px;left:0;width:1080px;text-align:center;font-size:30px;font-weight:700;color:#E6EBFF">@alejandro.segura.asesor</div>
</div></body></html>"""
async def m():
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path="/usr/bin/google-chrome", args=["--allow-file-access-from-files"])
        pg = await b.new_page(viewport={"width": 1080, "height": 1920})
        open("/tmp/hist-reel.html", "w").write(html)
        await pg.goto("file:///tmp/hist-reel.html"); await pg.evaluate("document.fonts.ready"); await pg.wait_for_timeout(300)
        await pg.screenshot(path=os.path.join(ROOT, "historias", "2026-11-13-viernes-reel.jpg"), type="jpeg", quality=92)
        await b.close()
asyncio.run(m())
print("ok")
