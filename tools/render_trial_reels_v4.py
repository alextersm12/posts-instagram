"""Trial Reels v4 (más visual, "que dé dopamina"): cada escena con su propio mundo de color y movimiento.
gancho = noche con orbes de color y partículas · problema = degradado naranja/rosa con icono animado
giro = amarillo con trama de puntos · lista = papel con casillas que se marcan · CTA = azul con rayos y confeti.
Transición con zoom-blur + destello en cada cambio de escena; palabras clave en etiquetas de color.
Reutiliza textos, voces y tiempos de render_trial_reels_v3.py.  Uso: python3 tools/render_trial_reels_v4.py t1e ..."""
import asyncio, json, os, subprocess, sys
import numpy as np
from playwright.async_api import async_playwright

sys.path.insert(0, os.path.dirname(__file__))
import render_trial_reels_v3 as V3  # noqa: E402
from render_12_reel import write_wav, tone, whoosh, SR, FPS, F  # noqa: E402

OUTDIR, WORK = V3.OUTDIR, "/tmp/trial4"

HTML = r"""<html><head><style>
@font-face{font-family:M;src:url(file://__F__Montserrat-Bold.ttf);font-weight:700}
@font-face{font-family:M;src:url(file://__F__Montserrat-ExtraBold.ttf);font-weight:800}
@font-face{font-family:M;src:url(file://__F__Montserrat-Black.ttf);font-weight:900}
body{margin:0;background:#000}
#v{position:relative;overflow:hidden;width:1080px;height:1920px;font-family:M;color:#fff}
.bg{position:absolute;inset:0}
.m{display:inline-block;margin:0 .09em .06em}
.tag{display:inline-block;padding:.02em .2em .08em;border-radius:.18em}
</style></head><body><div id="v">
<div class="bg" id="world"></div>
<div class="bg" id="cam"></div>
<div class="bg" style="background:radial-gradient(1200px 1600px at 50% 48%,transparent 60%,#0000004d 100%)"></div>
<svg class="bg" width="1080" height="1920" style="mix-blend-mode:overlay;opacity:.22"><filter id="n"><feTurbulence type="fractalNoise" baseFrequency="0.9" numOctaves="2" stitchTiles="stitch"/><feColorMatrix type="saturate" values="0"/></filter><rect width="100%" height="100%" filter="url(#n)"/></svg>
<div class="bg" id="prog" style="height:12px;bottom:auto;width:0"></div>
<div id="handle" style="position:absolute;left:0;right:0;bottom:150px;text-align:center;font-size:30px;font-weight:700;opacity:.85">@alejandro.segura.asesor</div>
<div class="bg" id="flash" style="background:#fff;opacity:0"></div>
</div>
<script>
const C=__C__, VEND=__VEND__, TOTAL=__TOTAL__, KW="__KW__", TOPIC="__TOPIC__";
const cl=x=>Math.max(0,Math.min(1,x)), oc=p=>1-Math.pow(1-p,3), ob=p=>{const c1=1.7,c3=c1+1;return 1+c3*Math.pow(p-1,3)+c1*Math.pow(p-1,2)};
function rnd(i){const x=Math.sin(i*12.9898+78.233)*43758.5453;return x-Math.floor(x)}
const SS=[];C.forEach((c,i)=>{if(!i||C[i-1].sc!=c.sc)SS.push({t:c.t,sc:c.sc})});SS.push({t:VEND,sc:'cta'});
const SC_END=k=>k+1<SS.length?SS[k+1].t:TOTAL;
// estilo de cada escena: fondo, color de texto, etiqueta de palabra clave
const STY={hook:{fg:'#fff',tb:'#1F4BFF',tc:'#fff'},line:{fg:'#fff',tb:'#1F4BFF',tc:'#fff'},
 turn:{fg:'#fff',tb:'#fff',tc:'#1236C9'},list:{fg:'#0A0A0A',tb:'#1F4BFF',tc:'#fff'},cta:{fg:'#fff',tb:'#1F4BFF',tc:'#fff'}};
const ICON={t1:'<circle cx="100" cy="100" r="80"/><path d="M100 50 V100 L135 120"/>',
 t2:'<path d="M140 55 A60 60 0 1 0 140 145"/><path d="M45 88 H120 M45 112 H120"/>',
 t3:'<path d="M40 50 H160 M40 100 H160 M40 150 H160"/><path d="M20 50 h0 M20 100 h0 M20 150 h0"/>'};
function world(sc,t,lt,dur){
 const grid=(c,o)=>`<div style="position:absolute;left:-600px;right:-600px;top:1300px;height:1300px;transform:perspective(700px) rotateX(72deg);transform-origin:top;background-image:linear-gradient(${c} 2px,transparent 2px),linear-gradient(90deg,${c} 2px,transparent 2px);background-size:120px 120px;background-position:0 ${(t*60)%120}px;opacity:${o};-webkit-mask-image:linear-gradient(transparent,#000 30%,#000 60%,transparent)"></div>`;
 const glass=(x,y,w,h,r,extra)=>`<div style="position:absolute;left:${x}px;top:${y}px;width:${w}px;height:${h}px;border-radius:${r}px;background:linear-gradient(135deg,#ffffff1f,#ffffff08);border:2px solid #ffffff26;box-shadow:0 30px 80px #00000066,inset 0 1px 0 #ffffff33">${extra||''}</div>`;
 if(sc=='hook'){ // noche azul marino con luces suaves, bokeh y suelo en rejilla
  let h=`<div class="bg" style="background:linear-gradient(#0B1224,#05070D)"></div>`;
  const O=[['#1F4BFF',540,620,700],['#3A2E8F',150,1300,520],['#0E6BA8',950,1450,480]];
  O.forEach((o,i)=>{const x=o[1]+120*Math.sin(t*.4+i*1.7),y=o[2]+90*Math.cos(t*.35+i),r=o[3]*(1+.08*Math.sin(t*.9+i));
   h+=`<div class="bg" style="background:radial-gradient(${r}px ${r}px at ${x}px ${y}px,${o[0]}66,transparent 70%)"></div>`});
  for(let i=0;i<14;i++){const x=rnd(i)*1080+Math.sin(t*.3+i)*20,y=rnd(i+3)*1920+Math.cos(t*.25+i)*25,s=40+rnd(i+5)*90;
   h+=`<div style="position:absolute;left:${x}px;top:${y}px;width:${s}px;height:${s}px;border-radius:50%;background:radial-gradient(#8fb0ff55,transparent 70%);opacity:${.3+.4*rnd(i+7)}"></div>`}
  return h+grid('#3d63ff40',1)}
 if(sc=='line'){ // grafito con paneles de cristal y una línea de gráfico que baja
  let pts='';for(let i=0;i<=12;i++){const x=130+i*68,y=1250+i*24+Math.sin(i*1.3)*60;pts+=`${i?'L':'M'}${x} ${y.toFixed(0)} `}
  const dl=2000*(1-oc(cl(lt/1.6)));
  return `<div class="bg" style="background:radial-gradient(1100px 900px at 30% 20%,#232838,#0E1016 75%)"></div>`+
  `<div class="bg" style="background:radial-gradient(700px 700px at ${800+60*Math.sin(t*.5)}px 1500px,#1F4BFF40,transparent 70%)"></div>`+
  glass(90,1120+12*Math.sin(t*.8),900,480,40,'')+
  `<svg class="bg" width="1080" height="1920"><path d="${pts}" fill="none" stroke="#5B7BFF" stroke-width="8" stroke-linecap="round" stroke-dasharray="2000" stroke-dashoffset="${dl}"/>`+
  [0,1,2,3].map(i=>`<line x1="130" x2="950" y1="${1180+i*110}" y2="${1180+i*110}" stroke="#ffffff14" stroke-width="2"/>`).join('')+`</svg>`+
  glass(760,200+10*Math.sin(t*.9+1),220,220,110,`<svg width="216" height="216" viewBox="0 0 200 200"><g fill="none" stroke="#fff" stroke-width="9" stroke-linecap="round" transform="translate(30 30) scale(.7)">${ICON[TOPIC]}</g></svg>`)}
 if(sc=='turn'){ // azul profundo con anillos que laten y un barrido de luz
  const sw=((lt*.6)%1.4-.2)*1600; let rings='';
  for(let i=0;i<5;i++){const r=((lt*120+i*160)%800)+60;rings+=`<circle cx="540" cy="820" r="${r}" fill="none" stroke="#ffffff" stroke-opacity="${.22*(1-r/860)}" stroke-width="3"/>`}
  return `<div class="bg" style="background:radial-gradient(1000px 1000px at 50% 40%,#2A56FF,#1236C9 55%,#081A66)"></div>`+
  `<svg class="bg" width="1080" height="1920">${rings}</svg>`+
  `<div class="bg" style="background:linear-gradient(115deg,transparent ${sw-200}px,#ffffff18 ${sw}px,transparent ${sw+200}px)"></div>`}
 if(sc=='list'){ // marfil con tarjetas limpias y casillas que se marcan
  const q=dur/3; let h=`<div class="bg" style="background:radial-gradient(1200px 1200px at 50% 30%,#FFFFFF,#ECEEF3 80%)"></div>`;
  for(let i=0;i<3;i++){const a=oc(cl((lt-i*q+.3)/.35)), ck=cl((lt-i*q-.2)/.25), y=1110+i*175;
   h+=`<div style="position:absolute;left:140px;top:${y}px;width:800px;height:135px;border-radius:30px;background:#fff;box-shadow:0 18px 50px #0A0A0A1f;transform:translateY(${(1-a)*80}px);opacity:${a};display:flex;align-items:center;padding-left:36px;box-sizing:border-box">`+
   `<div style="width:72px;height:72px;border-radius:50%;border:5px solid ${ck>0?'#1F4BFF':'#0A0A0A26'};background:${ck>0?'#1F4BFF':'transparent'};display:flex;align-items:center;justify-content:center">`+
   `<svg width="46" height="46" viewBox="0 0 50 50"><path d="M10 26 L21 37 L41 14" fill="none" stroke="#fff" stroke-width="7" stroke-linecap="round" stroke-linejoin="round" stroke-dasharray="60" stroke-dashoffset="${60*(1-ck)}"/></svg></div>`+
   `<div style="margin-left:30px;height:20px;width:${380+i*60}px;border-radius:10px;background:#0A0A0A14"></div></div>`}
  return h}
 // CTA: azul marino con resplandor y partículas que suben
 let h=`<div class="bg" style="background:radial-gradient(900px 900px at 50% 40%,#1F4BFF77,transparent 70%),linear-gradient(#0B1224,#05070D)"></div>`;
 for(let i=0;i<30;i++){const x=rnd(i)*1080,y=1920-((rnd(i+3)*1920+t*(60+rnd(i+4)*80))%2000),s=4+rnd(i+5)*6;
  h+=`<div style="position:absolute;left:${x}px;top:${y}px;width:${s}px;height:${s}px;border-radius:50%;background:#8fb0ff;opacity:${.3+.4*rnd(i+6)}"></div>`}
 return h+grid('#3d63ff33',.8)}
function render(t){
 let k=0;while(k+1<SS.length&&t>=SS[k+1].t)k++;
 const sc=SS[k].sc, lt=t-SS[k].t, dur=SC_END(k)-SS[k].t, S=STY[sc];
 // transición: zoom-blur + destello al entrar en escena (no en la primera)
 const tr=k?1-oc(cl(lt/.32)):0;
 const W=document.getElementById('world');
 W.innerHTML=world(sc,t,lt,dur);
 W.style.transform=`scale(${1+.25*tr}) rotate(${tr*4}deg)`; W.style.filter=tr>0.01?`blur(${tr*14}px)`:'';
 document.getElementById('flash').style.opacity=k?Math.max(0,.55-lt*3.2):0;
 let h='';
 if(t<VEND){
  let ci=0;while(ci+1<C.length&&t>=C[ci+1].t)ci++;
  const c=C[ci],ct=t-c.t, HOOK=c.sc=='hook';
  const n=c.ws.reduce((a,w)=>a+w.w.length,0), lng=Math.max(...c.ws.map(w=>w.w.length));
  let fs=Math.min(c.ws.length==1?230:(n>13?140:n>9?160:182), Math.floor(950/(Math.max(lng, c.ws.length>1?Math.min(n+c.ws.length-1,12):lng)*.72)));
  if(HOOK)fs=n>40?108:n>34?116:n>24?130:146;
  const y=HOOK?820:(c.sc=='list'?640:(c.sc=='line'?720:800));
  let ws='';
  c.ws.forEach((w,j)=>{
   const on=HOOK?(t>=w.t-.03||j==0):true; if(!HOOK&&t<w.t-.03&&ci)return;
   const p=HOOK?(j==0?1:cl((t-w.t+.03)/.12)):(ci==0?1:cl((t-w.t+.03)/.22)), q=ob(p);
   const tag=w.hi?`class="tag" style="background:${S.tb};color:${S.tc};transform:rotate(${(rnd(ci*7+j)-.5)*6}deg) scale(${HOOK?(j==0?1:ob(cl((t-w.t+.03)/.18))):ob(cl((t-w.t)/.25))})"`:`style="color:${S.fg}"`;
   ws+=`<span class="m" style="opacity:${HOOK?(on?1:0):cl(p*3)};transform:translateY(${(1-q)*(HOOK?30:60)}px) scale(${HOOK?.7+.3*q:.6+.4*q})"><span ${tag} ${w.hi?'':''}>${w.w}</span></span>`});
  const pop=HOOK?1:1+.18*(1-oc(cl(ct/.2))), rot=HOOK?0:(rnd(ci)-.5)*5;
  const sh=(sc=='list')?'none':'0 12px 40px #00000066';
  h=`<div style="position:absolute;left:60px;right:60px;top:${y}px;transform:translateY(-50%) scale(${pop}) rotate(${rot}deg);filter:blur(${HOOK?0:(1-oc(cl(ct/.15)))*6}px);text-align:center;font-size:${fs}px;font-weight:900;line-height:1.06;letter-spacing:-.03em;text-shadow:${sh}">${ws}</div>`;
 } else {
  const ct=t-VEND, m=d=>ob(cl((ct-d)/.35));
  h=`<div style="position:absolute;left:0;right:0;top:520px;text-align:center;font-weight:900;letter-spacing:-.03em;text-shadow:0 12px 40px #0000004d">`+
  `<div style="font-size:110px;transform:scale(${m(0)})">Escríbeme</div>`+
  `<div style="display:inline-block;margin:24px 0;font-size:170px;padding:0 .25em .06em;border-radius:.16em;background:linear-gradient(135deg,#ffffff2e,#ffffff0d);border:3px solid #5B7BFF;box-shadow:0 0 60px #1F4BFF99;color:#fff;transform:rotate(-2deg) scale(${m(.15)*(1+.04*Math.sin(ct*8))})">${KW}</div>`+
  `<div style="font-size:110px;transform:scale(${m(.3)})">por privado</div></div>`;
  const a=oc(cl((ct-.5)/.4)),bob=Math.sin(ct*6)*16;
  h+=`<svg width="140" height="260" style="position:absolute;left:470px;top:${1240+bob}px;opacity:${a}"><path d="M70 10 L70 230 M25 190 L70 240 L115 190" fill="none" stroke="#fff" stroke-width="12" stroke-linecap="round" stroke-linejoin="round"/></svg>`;
 }
 const cam=document.getElementById('cam');cam.innerHTML=h;
 const shk=k&&lt<.25?(1-lt/.25)*18:0; cam.style.transform=`translate(${shk*Math.sin(t*90)}px,${shk*Math.cos(t*70)}px)`;
 const dark=(sc=='list');
 document.getElementById('handle').style.color=dark?'#0A0A0A':'#fff';
 const pr=document.getElementById('prog');pr.style.width=(t/TOTAL*1080)+'px';pr.style.background=sc=='turn'?'#fff':'#1F4BFF';
}
</script></body></html>"""


def sfx(C, total, vend):
    """Más ritmo: pop en cada trozo, whoosh + golpe por escena, subida antes del CTA, 'ding' en cada casilla y base con pulso."""
    out = np.zeros(int(SR * (total + 1)))

    def put(sig, at):
        i = max(0, int(at * SR))
        out[i:i + len(sig)] += sig[:max(0, len(out) - i)]
    thud, wh = tone(110, 40, .45, .8, 7), whoosh(.4, .45)
    pop = tone(900, 500, .07, .18, 40)
    ding = tone(1760, 1760, .35, .16, 9) + tone(2637, 2637, .35, .08, 11)
    prev, ss = None, []
    for c in C:
        if c["sc"] != prev:
            put(wh, c["t"] - .28); put(thud, c["t"]); ss.append((c["t"], c["sc"]))
        else:
            put(pop, c["t"])
        prev = c["sc"]
    ss.append((vend, "cta"))
    for i, (t0, sc) in enumerate(ss[:-1]):
        if sc == "list":
            d = ss[i + 1][0] - t0
            for j in range(3):
                put(ding, t0 + j * d / 3 + .2)
    n = int(SR * 1.2)
    riser = np.sin(2 * np.pi * np.cumsum(np.linspace(200, 1200, n)) / SR) * np.linspace(0, .12, n)
    put(riser, vend - 1.2); put(wh, vend - .28); put(thud, vend)
    beat, t, k = 60 / 118, 0.0, 0
    kick = tone(80, 40, .25, .45, 12)
    hat = np.random.default_rng(3).normal(0, .045, int(SR * .03)) * np.exp(-np.linspace(0, 6, int(SR * .03)))
    while t < total - .3:
        put(kick, t); put(hat, t + beat / 2)
        if k % 4 == 0:
            f = [55, 49, 65.4, 58.3][(k // 4) % 4]
            nn = int(SR * beat * 4); tt = np.arange(nn) / SR
            put(.05 * (np.sin(2 * np.pi * f * tt) + .5 * np.sin(2 * np.pi * f * 2.003 * tt)) * np.sin(np.linspace(0, np.pi, nn)), t)
        t += beat; k += 1
    e, n = int(SR * total), int(SR * .8)
    out[e - n:e] *= np.linspace(1, 0, n); out[e:] = 0
    return out


def page(rid):
    C, audio, vend, total = V3.build(rid)
    html = (HTML.replace("__F__", F).replace("__C__", json.dumps(C, ensure_ascii=False)).replace("__VEND__", str(vend))
            .replace("__TOTAL__", str(total)).replace("__KW__", V3.KW[rid[:2]]).replace("__TOPIC__", rid[:2]))
    return C, audio, vend, total, html


async def render_one(b, rid):
    C, audio, vend, total, html = page(rid)
    wd = f"{WORK}/{rid}"
    os.makedirs(wd, exist_ok=True)
    for f in os.listdir(wd):
        if f.endswith(".jpg"):
            os.remove(os.path.join(wd, f))
    open(f"{wd}/reel.html", "w").write(html)
    pg = await b.new_page(viewport={"width": 1080, "height": 1920})
    await pg.goto(f"file://{wd}/reel.html")
    await pg.evaluate("document.fonts.ready")
    for i in range(int(total * FPS)):
        await pg.evaluate(f"render({i / FPS})")
        await pg.screenshot(path=f"{wd}/f{i:05d}.jpg", type="jpeg", quality=95)
    await pg.close()
    write_wav(f"{wd}/sfx.wav", sfx(C, total, vend))
    voz = np.zeros(int(SR * (total + 1)), np.float32)
    for at, x in audio:
        i = max(0, int(at * SR))
        voz[i:i + len(x)] += x[:len(voz) - i]
    write_wav(f"{wd}/voz.wav", voz)
    out = os.path.join(OUTDIR, f"r4-{rid}.mp4")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-framerate", str(FPS), "-i", f"{wd}/f%05d.jpg",
                    "-i", f"{wd}/sfx.wav", "-i", f"{wd}/voz.wav", "-filter_complex",
                    "[1:a]volume=0.32[s];[2:a]highpass=f=70,acompressor=threshold=-20dB:ratio=3:attack=5:release=80,"
                    "volume=1.4[v];[s][v]amix=inputs=2:duration=first:normalize=0,loudnorm=I=-14:TP=-1.5[a]",
                    "-map", "0:v", "-map", "[a]", "-c:v", "libx264", "-preset", "slow", "-crf", "18",
                    "-profile:v", "high", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k",
                    "-ar", "48000", "-shortest", "-movflags", "+faststart", out], check=True)
    print(rid, round(total, 1), "s", os.path.getsize(out) // 1024, "KB", "portada_ms", int((C[1]["t"] - .25) * 1000))


async def main(ids):
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path="/opt/pw-browsers/chromium", args=["--allow-file-access-from-files"])
        for rid in ids:
            await render_one(b, rid)
        await b.close()


if __name__ == "__main__":
    asyncio.run(main(sys.argv[1:]))
