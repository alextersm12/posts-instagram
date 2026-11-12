import asyncio
from playwright.async_api import async_playwright
F="/tmp/mont/fonts/ttf/"
html=f"""<html><head><style>
@font-face{{font-family:M;src:url(file://{F}Montserrat-Medium.ttf);font-weight:500}}
@font-face{{font-family:M;src:url(file://{F}Montserrat-ExtraBold.ttf);font-weight:800}}
@font-face{{font-family:M;src:url(file://{F}Montserrat-Bold.ttf);font-weight:700}}
body{{margin:0}}</style></head><body><div style="position:relative;overflow:hidden;width:1080px;height:1920px;font-family:M;color:#fff;background:#070708">
<div style="position:absolute;inset:0;background:radial-gradient(900px 900px at 85% 70%,#1F4BFF77,transparent 70%),radial-gradient(600px 500px at 0% 10%,#1F4BFF22,transparent 70%)"></div>
<div style="position:absolute;right:-120px;top:760px;font-size:1100px;font-weight:800;line-height:1;color:transparent;-webkit-text-stroke:5px #1F4BFF;opacity:.6">€</div>
<svg width="1080" height="1920" style="position:absolute;inset:0;mix-blend-mode:overlay;opacity:.35"><filter id="n"><feTurbulence type="fractalNoise" baseFrequency="0.85" numOctaves="3"/><feColorMatrix type="saturate" values="0"/></filter><rect width="100%" height="100%" filter="url(#n)"/></svg>
<div style="position:absolute;left:90px;right:90px;top:430px">
<span style="display:inline-block;background:#1F4BFF;padding:14px 26px;border-radius:999px;font-size:30px;font-weight:800;letter-spacing:.12em">4 FORMAS DE FINANCIARTE</span>
<div style="margin-top:40px;font-size:150px;font-weight:800;line-height:1;letter-spacing:-.03em">El dinero<br>no es lo que<br>te <span style="color:#1F4BFF">frena</span>.</div>
<div style="display:inline-block;margin-top:50px;background:#fff;color:#0A0A0A;padding:18px 30px;font-size:52px;font-weight:800;transform:rotate(-2deg)">Es no saber a dónde vas.</div>
</div>

</div></body></html>"""
async def m():
  async with async_playwright() as p:
    b=await p.chromium.launch(executable_path="/usr/bin/google-chrome",args=["--allow-file-access-from-files"])
    pg=await b.new_page(viewport={"width":1080,"height":1920}); open('/tmp/cover.html','w').write(html)
    await pg.goto("file:///tmp/cover.html"); await pg.evaluate("document.fonts.ready"); await pg.wait_for_timeout(200)
    await pg.screenshot(path="/home/claude/posts-instagram/12-financiacion/portada-reel.jpg",type="jpeg",quality=90)
    await b.close()
asyncio.run(m())
