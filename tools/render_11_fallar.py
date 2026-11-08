src=open('render.py').read().split('# 09 DELEGAR')[0]
exec(src)
import asyncio
from playwright.async_api import async_playwright
K='<span style="color:#0A0A0A">'
def hold(x,y,s,rot):
    return f'<path d="M0 -{s} C {s*.9} -{s*.9}, {s*1.1} {s*.2}, {s*.4} {s*.8} C -{s*.3} {s*1.1}, -{s*1.1} {s*.5}, -{s} -{s*.2} C -{s*.9} -{s*.8}, -{s*.4} -{s*1.05}, 0 -{s} Z" transform="translate({x},{y}) rotate({rot})" fill="none" stroke="#0A0A0A" stroke-width="4"/><circle cx="{x}" cy="{y}" r="{s*.18:.0f}" fill="none" stroke="#0A0A0A" stroke-width="3" transform="translate(0,0)"/>'
def wall(holds,route=None,op=.4):
    r=f'<path d="{route}" fill="none" stroke="#0A0A0A" stroke-width="4" stroke-dasharray="18 16"/>' if route else ''
    return f'<svg style="position:absolute;inset:0;opacity:{op}" width="1080" height="1350">{r}{"".join(hold(*h) for h in holds)}</svg>'
w1=wall([(860,960,60,10),(660,1110,44,-30),(980,820,40,40),(470,1260,38,15)],op=.45)
w2=wall([(160,1250,42,20),(380,1130,38,-15),(600,1200,46,35),(800,1060,40,-40)],route="M160 1250 L380 1130 L600 1200 L800 1060 L900 990",op=.45)
w3=wall([(760,1020,58,25)],op=.35)
Q='<div style="font-size:150px;font-weight:800;line-height:.6;color:#0A0A0A;opacity:.85;margin-bottom:10px">“</div>'
s=[
 slide(1080,1350,BLUE_BG,w1,T(Q+f'En España nos reímos del que falla.<br>{K}Así nos va.</span>',size=100,top=250,hl="#0A0A0A"),1,3,False,"#E6EBFF","#0A0A0A"),
 slide(1080,1350,BLUE_BG,w2,T(f'Quien decide, a veces falla. Quien no decide, {K}falla siempre</span>.',size=88,top=300,hl="#0A0A0A",extra=P("Como en la escalada: no llegas, te caes, vuelves a probar… y un día ese paso es fácil.","#E6EBFF")),2,3,False,"#E6EBFF","#0A0A0A"),
 slide(1080,1350,BLUE_BG,w3,T(f'Lo que no es normal es {K}rendirse</span>.',size=110,top=300,bar=True,hl="#0A0A0A",extra=P("¿Qué decisión llevas tiempo sin volver a intentar?","#E6EBFF")),3,3,True,"#E6EBFF","#0A0A0A"),
]
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch(executable_path="/usr/bin/google-chrome",args=["--allow-file-access-from-files"])
        for i,h in enumerate(s,1):
            pg=await b.new_page(viewport={"width":1080,"height":1350})
            open(f"f{i}.html","w").write(h); await pg.goto(f"file:///home/claude/semana/f{i}.html"); await pg.evaluate("document.fonts.ready"); await pg.wait_for_timeout(300)
            await pg.screenshot(path=f"11-fallar-{i}.png"); await pg.close()
        await b.close()
asyncio.run(main())
from PIL import Image
sh=Image.new("RGB",(3*420+20,540),"white")
for i in (1,2,3): sh.paste(Image.open(f"11-fallar-{i}.png").resize((400,500)),(20+(i-1)*420,20))
sh.save("prev-11.png"); print("ok")
