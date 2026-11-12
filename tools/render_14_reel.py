"""Reel 14-tres-cifras (1080x1920, 30 fps, azul). Viernes 20-nov-2026.
Uso: python3 tools/render_14_reel.py voz.mp3
Salida: 14-tres-cifras/reel-tres-cifras.mp4 y 14-tres-cifras/portada-reel-tres-cifras.jpg
Reutiliza utilidades de tools/render_12_reel.py."""
import asyncio, json, os, re, subprocess, sys
import numpy as np
from playwright.async_api import async_playwright

sys.path.insert(0, os.path.dirname(__file__))
from render_12_reel import load_pcm, write_wav, tone, whoosh, SR, FPS, F  # noqa: E402

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
OUTDIR = os.path.join(ROOT, "14-tres-cifras")
WORK = "/tmp/reel14"
LEAD, GAP_IN, GAP_SCENE, TAIL = 0.35, 0.14, 0.3, 1.6
# toma de ElevenLabs (Rafa N) con 23 trozos de voz; sublista = trozos unidos conservando su pausa natural
GROUPS = [[0], [[1, 2], 3, 4], [[5, 6], 7, 8], [[9, 10], 11, 12], [[13, 14], [15, 16]], [17, 18], [19, 20], [21, 22]]


def prepare(voice):
    x = load_pcm(voice)
    out = subprocess.run(["ffmpeg", "-i", voice, "-af", "silencedetect=noise=-38dB:d=0.18", "-f", "null", "-"],
                         capture_output=True, text=True).stderr
    ss = [float(v) for v in re.findall(r"silence_start: ([\d.]+)", out)]
    se = [float(v) for v in re.findall(r"silence_end: ([\d.]+)", out)]
    chunks, cur = [], 0.0
    for a, b in zip(ss, se):
        if a - cur > 0.05:
            chunks.append((cur, a))
        cur = b
    if len(x) / SR - cur > 0.1:
        chunks.append((cur, len(x) / SR))
    need = sum(len(g) if not isinstance(g, list) else sum(len(k) if isinstance(k, list) else 1 for k in g) for g in GROUPS)
    if len(chunks) != need:
        sys.exit(f"{len(chunks)} trozos detectados; GROUPS espera {need}")
    pieces, S, D, t = [np.zeros(int(LEAD * SR), np.float32)], [], [], LEAD
    for g in GROUPS:
        S.append(t - 0.05)
        D.append([])
        for j, k in enumerate(g):
            a, b = (chunks[k[0]][0], chunks[k[-1]][1]) if isinstance(k, list) else chunks[k]
            a, b = max(0, a - 0.04), b + 0.06
            D[-1].append(t - S[-1])
            seg = x[int(a * SR):int(b * SR)]
            gap = GAP_IN if j < len(g) - 1 else GAP_SCENE
            pieces += [seg, np.zeros(int(gap * SR), np.float32)]
            t += len(seg) / SR + gap
    os.makedirs(WORK, exist_ok=True)
    write_wav(f"{WORK}/voz.wav", np.concatenate(pieces))
    return S, t + TAIL, f"{WORK}/voz.wav", D


HEAD = r"""<html><head><style>
@font-face{font-family:M;src:url(file://%(F)sMontserrat-Medium.ttf);font-weight:500}
@font-face{font-family:M;src:url(file://%(F)sMontserrat-Bold.ttf);font-weight:700}
@font-face{font-family:M;src:url(file://%(F)sMontserrat-ExtraBold.ttf);font-weight:800}
body{margin:0;background:#000}
#v{position:relative;overflow:hidden;width:1080px;height:1920px;font-family:M;color:#fff}
.bg{position:absolute;inset:0}.it{position:absolute}.k{color:#0A0A0A}.b{color:#1F4BFF}
.chip{display:inline-block;background:#0A0A0A;color:#fff;padding:14px 26px;border-radius:999px;font-size:30px;font-weight:800;letter-spacing:.12em}
.tag{position:absolute;padding:16px 28px;border-radius:999px;background:#fff;color:#1F4BFF;font-size:38px;font-weight:800;white-space:nowrap;box-shadow:0 14px 30px #0A0A0A40}
</style></head><body><div id="v">
<div class="bg" style="background:linear-gradient(160deg,#3A62FF 0%%,#1F4BFF 45%%,#1430B8 100%%)"></div>
<div class="bg" id="black" style="background:radial-gradient(900px 900px at 50%% 45%%,#1F4BFF55,transparent 70%%),#070708;opacity:0"></div>
<div class="bg" style="background-image:linear-gradient(#ffffff12 2px,transparent 2px),linear-gradient(90deg,#ffffff12 2px,transparent 2px);background-size:90px 90px;opacity:.6"></div>
<div id="cam" class="bg"></div>
<svg class="bg" width="1080" height="1920" style="mix-blend-mode:overlay;opacity:.4"><filter id="n"><feTurbulence type="fractalNoise" baseFrequency="0.85" numOctaves="3" stitchTiles="stitch"/><feColorMatrix type="saturate" values="0"/></filter><rect width="100%%" height="100%%" filter="url(#n)"/></svg>
"""

HTML = HEAD + r"""<div class="bg" id="prog" style="height:12px;bottom:auto;background:#0A0A0A;width:0"></div>
<div class="it" style="left:0;right:0;bottom:120px;text-align:center;font-size:32px;font-weight:700;opacity:.85">@alejandro.segura.asesor</div>
<div class="bg" id="flash" style="background:#fff;opacity:0"></div>
</div>
<script>
const S=%(S)s, TOTAL=%(TOTAL)s, D=%(D)s;
const cl=x=>Math.max(0,Math.min(1,x)), oc=p=>1-Math.pow(1-p,3), ob=p=>{const c1=1.9,c3=c1+1;return 1+c3*Math.pow(p-1,3)+c1*Math.pow(p-1,2)};
const TAGS=[['Previsión de cobros',90,600],['Impuestos',620,660],['Previsión de pagos',140,800],['Costes fijos',580,880],['IVA',120,990],['Nóminas',330,1060],['Stock',740,1100],['Deudas',90,1200],['Precios',480,1250],['Rentabilidad por cliente',140,1370],['Tesorería',640,1470],['Presupuesto',200,1570]];
function die(x,y,rot,pips,sz=190){const p={1:[[.5,.5]],2:[[.27,.27],[.73,.73]],3:[[.25,.25],[.5,.5],[.75,.75]],4:[[.27,.27],[.73,.27],[.27,.73],[.73,.73]],5:[[.25,.25],[.75,.25],[.5,.5],[.25,.75],[.75,.75]],6:[[.27,.22],[.73,.22],[.27,.5],[.73,.5],[.27,.78],[.73,.78]]}[pips];
 return `<svg width="${sz}" height="${sz}" viewBox="0 0 100 100" style="position:absolute;left:${x}px;top:${y}px;transform:rotate(${rot}deg);filter:drop-shadow(0 20px 30px #000a)"><rect x="4" y="4" width="92" height="92" rx="18" fill="#fff"/>${p.map(([a,b])=>`<circle cx="${a*100}" cy="${b*100}" r="8" fill="#1F4BFF"/>`).join('')}</svg>`}
function render(t){
 let s=0;while(s+1<S.length&&t>=S[s+1])s++;
 const st=S[s],en=s+1<S.length?S[s+1]:TOTAL,lt=t-st,Ld=en-st,d=D[s];
 let h='',sh=0,black=false;
 const it=(html,x,y,an,dl,extra='')=>{const p=cl((lt-dl)/.38);let tr='',op=1;
  if(an=='pop'){const q=ob(p);tr=`translateY(${(1-q)*60}px) scale(${.6+.4*q})`;op=cl(p*3)}
  else if(an=='slam'){const q=ob(p);tr=`scale(${1+1.2*(1-q)})`;op=cl(p*4)}
  else if(an=='slideL'){const q=ob(p);tr=`translateX(${(1-q)*-1100}px)`}
  h+=`<div class="it" style="left:${x}px;top:${y}px;transform:${tr};opacity:${op};transform-origin:left center;${extra}">${html}</div>`};
 const kick=(dl,a=20)=>{const k=lt-dl-.1;if(k>0&&k<.25)sh=Math.max(sh,(1-k/.25)*a)};
 const head=(num,word)=>{it(`<span class="chip">${num} DE 3</span>`,90,300,'pop',0);it(`<div style="font-size:150px;font-weight:800;letter-spacing:-.03em;line-height:1">${word}</div>`,90,390,'slam',0);kick(0)
  h+=`<div style="position:absolute;right:-40px;top:1150px;font-size:700px;font-weight:800;line-height:1;color:transparent;-webkit-text-stroke:5px #0A0A0A;opacity:.3">${num}</div>`};
 if(s==0){const q=oc(cl(lt/.6));
  h+=`<div style="position:absolute;right:-60px;top:200px;font-size:1100px;font-weight:800;line-height:1;color:#0A0A0A;opacity:${.25*q};transform:scale(${.6+.4*q})">3</div>`;
  it(`<div style="font-size:110px;font-weight:800;line-height:1.02;letter-spacing:-.03em">Si no sabes<br>estas <span class="k">3 cifras</span>…</div>`,90,560,'pop',0);
  const b=cl((lt-1.7)/.35);it(`<div style="font-size:100px;font-weight:800;line-height:1.05">estás decidiendo<br><span style="position:relative">a ciegas.<span style="position:absolute;left:-10px;right:-10px;top:30%%;height:45%%;background:#0A0A0A;transform:scaleX(${oc(b)});transform-origin:left"></span></span></div>`,90,980,'pop',1.5);kick(1.95)}
 if(s==1){head('1','Facturación');
  it(`<div style="font-size:64px;font-weight:700">Lo que vendes.</div>`,90,620,'pop',d[1]);
  const bars=[.35,.5,.62,.8,1];bars.forEach((v,i)=>{const q=ob(cl((lt-d[1]-i*.08)/.4));h+=`<div style="position:absolute;left:${110+i*120}px;bottom:${560}px;width:90px;height:${v*360*q}px;background:#fff;border-radius:10px 10px 0 0;opacity:.9"></div>`});
  it(`<div style="background:#0A0A0A;padding:22px 34px;font-size:64px;font-weight:800;transform:rotate(-3deg)">Vender <span class="b">≠</span> ganar</div>`,90,1420,'slam',d[2]);kick(d[2]+.05)}
 if(s==2){head('2','Margen');
  it(`<div style="font-size:52px;font-weight:700;line-height:1.2">Lo que te queda<br>después de pagar<br>lo que te cuesta vender.</div>`,90,600,'pop',d[1]);
  const q=oc(cl((lt-d[1]-.3)/1.6)),W=900;
  h+=`<div style="position:absolute;left:90px;top:960px;width:${W}px;height:150px;border-radius:20px;background:#fff;overflow:hidden"><div style="position:absolute;left:0;top:0;bottom:0;width:${W*.88*q}px;background:#0A0A0A"></div></div>`;
  it(`<div style="font-size:34px;font-weight:800;color:#E6EBFF">LO QUE FACTURAS</div>`,90,900,'pop',d[1]);
  it(`<div style="font-size:34px;font-weight:800">COSTES ${'→'.repeat(3)}</div>`,110,1135,'pop',d[1]+.4);
  it(`<div style="font-size:34px;font-weight:800;color:#0A0A0A;background:#fff;padding:8px 16px;border-radius:10px">MARGEN ↑</div>`,800,1135,'pop',d[1]+1.6);
  it(`<div style="font-size:60px;font-weight:800;line-height:1.1">Facturas mucho.<br>Te queda <span class="k">muy poco</span>.</div>`,90,1300,'slam',d[2]);kick(d[2]+.05)}
 if(s==3){head('3','Caja');
  it(`<div style="font-size:52px;font-weight:700;line-height:1.2">El dinero que hay<br>de verdad en el banco.</div>`,90,600,'pop',d[1]);
  it(`<div style="width:400px;height:300px;background:#fff;border-radius:18px;color:#1F4BFF;padding:30px;box-sizing:border-box"><div style="font-size:32px;font-weight:800;color:#0A0A0A">EN EL PAPEL</div><div style="font-size:62px;font-weight:800;margin-top:40px">Beneficio ✓</div></div>`,90,880,'pop',d[2]);
  it(`<div style="width:400px;height:300px;background:#0A0A0A;border-radius:18px;padding:30px;box-sizing:border-box"><div style="font-size:32px;font-weight:800;color:#E6EBFF">EN EL BANCO</div><div style="font-size:62px;font-weight:800;margin-top:40px;color:#FF4B4B">Vacío</div></div>`,590,880,'pop',d[2]+.6);
  it(`<div style="background:#FF3B3B;padding:18px 30px;font-size:50px;font-weight:800;transform:rotate(-6deg);border:5px solid #fff">NÓMINAS SIN PAGAR</div>`,110,1290,'slam',d[2]+2.2);kick(d[2]+2.25)}
 if(s==4){it(`<div style="font-size:120px;font-weight:800;letter-spacing:-.03em;line-height:1">Ojo.<br>No es <span class="k">todo</span>.</div>`,90,280,'slam',0);kick(0);
  const n=TAGS.length;TAGS.forEach(([tx,x,y],i)=>{const dl=d[1]+i*((Ld-d[1]-.4)/n);const q=ob(cl((lt-dl)/.3));if(lt>dl)h+=`<div class="tag" style="left:${x}px;top:${y}px;transform:scale(${q}) rotate(${(i%%2?3:-3)}deg)">${tx}</div>`})}
 if(s==5){const v=1-oc(cl(lt/.35));
  TAGS.forEach(([tx,x,y],i)=>{if(v>0)h+=`<div class="tag" style="left:${x}px;top:${y}px;transform:translateY(${(1-v)*900}px) rotate(${(1-v)*(i%%2?40:-40)}deg);opacity:${v}">${tx}</div>`});
  it(`<div style="font-size:66px;font-weight:700;line-height:1.15">Pero si ni siquiera<br>llevas estas tres…</div>`,90,330,'pop',0);
  ['Facturación','Margen','Caja'].forEach((w,i)=>it(`<div style="font-size:120px;font-weight:800;letter-spacing:-.03em">${w}</div>`,90,620+i*170,'slideL',.25+i*.18));
  black=lt>d[1];it(`<div style="background:#FF3B3B;padding:22px 36px;font-size:76px;font-weight:800;transform:rotate(-3deg)">tienes un problema.</div>`,90,1200,'slam',d[1]);kick(d[1],26)}
 if(s==6){black=true;
  it(`<div style="font-size:110px;font-weight:800;letter-spacing:-.03em;line-height:1.02">Estás<br>decidiendo<br>a <span class="b">ciegas</span>.</div>`,90,300,'slam',0);kick(0);
  if(lt>d[1]){const r=cl((lt-d[1])/1.2),e=oc(r);
   h+=die(-250+e*420,1050-Math.abs(Math.sin(r*Math.PI*3))*(1-r)*260,(1-e)*-900+12,r<1?1+Math.floor(lt*12)%%6:5);
   h+=die(1200-e*560,1100-Math.abs(Math.sin(r*Math.PI*3+1))*(1-r)*220,(1-e)*800-14,r<1?1+Math.floor(lt*11+3)%%6:2);}
  it(`<div style="font-size:62px;font-weight:800;line-height:1.15">Cada decisión,<br>un <span class="b">juego de azar</span>.</div>`,90,1420,'pop',d[1]+.2);if(lt>d[1]+1.15&&lt<d[1]+1.4)sh=14}
 if(s==7){it(`<div style="font-size:130px;font-weight:800;letter-spacing:-.03em;line-height:1">¿Te sabes<br>las <span class="k">tres</span>?</div>`,90,420,'slam',0);kick(0);
  it(`<div style="font-size:60px;font-weight:700">Escríbeme</div>`,90,860,'pop',d[1]);
  it(`<div style="background:#0A0A0A;padding:24px 46px;border-radius:999px;font-size:110px;font-weight:800;letter-spacing:.04em;box-shadow:0 0 80px #0A0A0A88">NÚMEROS</div>`,90,960,'slam',d[1]+.35);kick(d[1]+.4);
  it(`<div style="font-size:60px;font-weight:700">por privado y lo vemos.</div>`,90,1210,'pop',d[1]+.8);
  it(`<svg width="150" height="150" viewBox="0 0 24 24"><path d="M22 3 2 10.5l7.5 3L13 21z M9.5 13.5 22 3" fill="none" stroke="#fff" stroke-width="1.6" stroke-linejoin="round"/></svg>`,830,1330,'pop',d[1]+1.1)}
 const cam=document.getElementById('cam');cam.innerHTML=h;
 cam.style.transform=`scale(${1+.035*cl(lt/Ld)}) translate(${sh*Math.sin(t*90)}px,${sh*Math.cos(t*70)}px)`;
 document.getElementById('black').style.opacity=black?1:0;
 document.getElementById('flash').style.opacity=Math.max(0,.5-lt*4.5);
 const pr=document.getElementById('prog');pr.style.width=(t/TOTAL*1080)+'px';pr.style.background=black?'#1F4BFF':'#0A0A0A';
}
</script></body></html>"""

COVER = HEAD + r"""
<div class="it" style="right:-80px;top:620px;font-size:1250px;font-weight:800;line-height:1;color:transparent;-webkit-text-stroke:6px #0A0A0A;opacity:.35">3</div>
<div class="it" style="left:90px;right:90px;top:430px">
 <span class="chip">LO MÍNIMO</span>
 <div style="margin-top:40px;font-size:136px;font-weight:800;line-height:1;letter-spacing:-.03em">¿Te sabes<br>estas <span class="k">3 cifras</span>?</div>
 <div style="margin-top:60px;display:flex;flex-direction:column;gap:22px;align-items:flex-start">
  <span style="background:#fff;color:#1F4BFF;padding:16px 30px;border-radius:999px;font-size:52px;font-weight:800">1 · Facturación</span>
  <span style="background:#fff;color:#1F4BFF;padding:16px 30px;border-radius:999px;font-size:52px;font-weight:800">2 · Margen</span>
  <span style="background:#fff;color:#1F4BFF;padding:16px 30px;border-radius:999px;font-size:52px;font-weight:800">3 · Caja</span>
 </div>
</div></div></body></html>"""


def sfx(S, D, total):
    out = np.zeros(int(SR * (total + 1)))

    def put(sig, at):
        i = int(at * SR)
        out[i:i + len(sig)] += sig[:max(0, len(out) - i)]
    pop, thud, tick = tone(900, 400, .12, .35, 30), tone(120, 45, .35, .9, 10), tone(1800, 1800, .03, .25, 80)
    for i, st in enumerate(S):
        put(whoosh(), max(0, st - .15))
        d = D[i]
        if i == 0:
            put(thud, st + 1.95)
        elif i in (1, 2, 3):
            put(thud, st + .05)
            put(pop, st + d[1])
            put(thud, st + d[2] + .05)
            if i == 3:
                put(thud, st + d[2] + 2.25)
        elif i == 4:
            put(thud, st + .05)
            end = S[i + 1]
            for k in range(12):
                put(pop, st + d[1] + k * ((end - st - d[1] - .4) / 12))
        elif i == 5:
            put(whoosh(.4, .5), st)
            put(thud, st + d[1])
            put(tone(300, 80, .4, .8, 6), st + d[1])
        elif i == 6:
            put(thud, st + .05)
            for k in range(10):
                put(tick, st + d[1] + k * .11)
            put(thud, st + d[1] + 1.2)
        elif i == 7:
            put(thud, st + .05)
            put(pop, st + d[1])
            put(thud, st + d[1] + .4)
            put(tone(600, 1200, .25, .4, 6), st + d[1] + 1.1)
    beat, t = 60 / 112, S[0]
    kick = tone(90, 40, .25, .55, 14)
    hat = np.random.default_rng(2).normal(0, .06, int(SR * .04)) * np.exp(-np.linspace(0, 6, int(SR * .04)))
    while t < total - .3:
        put(kick, t)
        put(hat, t + beat / 2)
        t += beat
    return out


async def render(S, total, D):
    for f in os.listdir(WORK):
        if f.endswith(".jpg"):
            os.remove(os.path.join(WORK, f))
    open(f"{WORK}/reel.html", "w").write(HTML % {"F": F, "S": json.dumps(S), "TOTAL": total, "D": json.dumps(D)})
    open(f"{WORK}/portada.html", "w").write(COVER % {"F": F})
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path="/usr/bin/google-chrome", args=["--allow-file-access-from-files"])
        pg = await b.new_page(viewport={"width": 1080, "height": 1920})
        await pg.goto(f"file://{WORK}/portada.html")
        await pg.evaluate("document.fonts.ready")
        await pg.wait_for_timeout(300)
        await pg.screenshot(path=os.path.join(OUTDIR, "portada-reel-tres-cifras.jpg"), type="jpeg", quality=92)
        await pg.goto(f"file://{WORK}/reel.html")
        await pg.evaluate("document.fonts.ready")
        for i in range(int(total * FPS)):
            await pg.evaluate(f"render({i / FPS})")
            await pg.screenshot(path=f"{WORK}/f{i:05d}.jpg", type="jpeg", quality=88)
        await b.close()


def main():
    os.makedirs(OUTDIR, exist_ok=True)
    S, total, voice, D = prepare(sys.argv[1])
    print("escenas:", [round(x, 2) for x in S], "total:", round(total, 2))
    asyncio.run(render(S, total, D))
    write_wav(f"{WORK}/sfx.wav", sfx(S, D, total))
    out = os.path.join(OUTDIR, "reel-tres-cifras.mp4")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-framerate", str(FPS), "-i", f"{WORK}/f%05d.jpg",
                    "-i", f"{WORK}/sfx.wav", "-i", voice, "-filter_complex",
                    "[1:a]volume=0.4[s];[2:a]volume=1.5[v];[s][v]amix=inputs=2:duration=first:normalize=0[a]",
                    "-map", "0:v", "-map", "[a]", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "20",
                    "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", out], check=True)
    print("ok", out)


if __name__ == "__main__":
    main()
