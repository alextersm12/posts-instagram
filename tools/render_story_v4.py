"""Historias en vídeo (1080x1920) con las escenas del motor de reels v4.
Uso: python3 tools/render_story_v4.py spec.json salida.mp4
spec: {"scene": "silla", "dur": 8, "top": ["Si mañana", "no vas…"], "hi": ["no vas…"],
       "bottom": "Te leo por privado", "hole": true}
"hole" deja libre la franja 1250-1600 para la encuesta que se añade desde el móvil."""
import asyncio, json, os, subprocess, sys
from playwright.async_api import async_playwright
FPS = 30
D = os.path.dirname(os.path.abspath(__file__))
FONTS = os.environ.get("MONT", "/tmp/mont/fonts/ttf/")

def page(spec):
    h = open(os.path.join(D, "reel_v4_template.html")).read()
    h = h.replace("__F__", FONTS).replace("__C__", "[]").replace("__S__", "[]").replace("__VEND__", "1e9") \
         .replace("__TOTAL__", str(spec["dur"])).replace("__KW__", spec.get("kw", ""))
    extra = """<script>
const SP=%s;
function story(t){
 const st=document.getElementById('stage');
 st.style.transform=`scale(${1.0+.02*t})`;
 st.innerHTML=SC[SP.scene](t+ (SP.offset||0));
 if(SP.hole) st.innerHTML+=`<div class="a" style="background:linear-gradient(transparent 1150px,#000c 1300px,#000c 1640px,transparent 1800px)"></div>`;
 let h='';SP.top.forEach((l,i)=>{const p=ob(cl((t-.25-i*.45)/.3));if(t<.2+i*.45)return;
  h+=`<div class="cap" style="top:${(SP.ty||260)+i*150}px;font-size:${SP.fs||130}px;transform:scale(${.6+.4*p});opacity:${cl(p*2)}"><span class="cw" style="color:${SP.hi&&SP.hi.includes(l)?'#FFE14D':'#fff'}">${l}</span></div>`});
 if(SP.bottom){const p=oc(cl((t-(SP.bt||2.2))/.4));
  h+=`<div style="position:absolute;left:0;right:0;top:1660px;text-align:center;opacity:${p};transform:translateY(${(1-p)*30}px)">
   <div style="font-weight:800;font-size:56px;color:#fff;text-shadow:0 4px 18px #000">${SP.bottom}</div>
   <svg width="60" height="110" style="margin-top:14px"><path d="M30 0 L30 ${50+20*Math.sin(t*4)} M14 ${36+20*Math.sin(t*4)} L30 ${54+20*Math.sin(t*4)} L46 ${36+20*Math.sin(t*4)}" stroke="#4d7cff" stroke-width="5" fill="none" stroke-linecap="round"/></svg></div>`}
 document.getElementById('cap').innerHTML=h;
 document.getElementById('prog').style.display='none';
 document.getElementById('handle').style.bottom='70px';
}
</script>""" % json.dumps(spec)
    return h.replace("</body>", extra + "</body>")

async def main(spec_path, out):
    spec = json.load(open(spec_path))
    work = "/tmp/v4work/story/frames"; os.makedirs(work, exist_ok=True)
    for f in os.listdir(work): os.remove(os.path.join(work, f))
    open("/tmp/v4work/story/s.html", "w").write(page(spec))
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path=os.environ.get("CHROME", "/opt/pw-browsers/chromium"))
        pg = await b.new_page(viewport={"width": 1080, "height": 1920})
        await pg.goto("file:///tmp/v4work/story/s.html"); await pg.wait_for_timeout(500)
        for i in range(int(spec["dur"] * FPS)):
            await pg.evaluate(f"story({i / FPS})")
            await pg.screenshot(path=f"{work}/f{i:05d}.jpg", type="jpeg", quality=95)
        await b.close()
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-framerate", str(FPS), "-i", f"{work}/f%05d.jpg",
                    "-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo", "-shortest",
                    "-c:v", "libx264", "-crf", "18", "-pix_fmt", "yuv420p", "-c:a", "aac", out], check=True)
    print(out)

if __name__ == "__main__":
    asyncio.run(main(sys.argv[1], sys.argv[2]))
