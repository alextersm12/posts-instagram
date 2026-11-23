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
const STY={hook:{fg:'#fff',tb:'#1F4BFF',tc:'#fff'},line:{fg:'#fff',tb:'#0A0A0A',tc:'#fff'},
 turn:{fg:'#0A0A0A',tb:'#0A0A0A',tc:'#FFD400'},list:{fg:'#0A0A0A',tb:'#19C37D',tc:'#fff'},cta:{fg:'#fff',tb:'#FFD400',tc:'#0A0A0A'}};
const ICON={t1:'<circle cx="100" cy="100" r="80"/><path d="M100 50 V100 L135 120"/>',
 t2:'<path d="M140 55 A60 60 0 1 0 140 145"/><path d="M45 88 H120 M45 112 H120"/>',
 t3:'<path d="M40 50 H160 M40 100 H160 M40 150 H160"/><path d="M20 50 h0 M20 100 h0 M20 150 h0"/>'};
function world(sc,t,lt,dur){
 if(sc=='hook'){ // noche con orbes de color que respiran y partículas que suben
  let h=`<div class="bg" style="background:#06070d"></div>`;
  const O=[['#1F4BFF',540,700,620],['#7B2FFF',180,1250,520],['#00C2FF',900,1500,480],['#FF3D77',850,300,380]];
  O.forEach((o,i)=>{const x=o[1]+140*Math.sin(t*.6+i*1.7),y=o[2]+120*Math.cos(t*.5+i),r=o[3]*(1+.12*Math.sin(t*1.3+i));
   h+=`<div class="bg" style="background:radial-gradient(${r}px ${r}px at ${x}px ${y}px,${o[0]}88,transparent 70%)"></div>`});
  for(let i=0;i<46;i++){const x=rnd(i)*1080,sp=40+rnd(i+9)*90,y=(1920-((rnd(i+3)*1920+t*sp)%2000)),s=3+rnd(i+5)*7;
   h+=`<div style="position:absolute;left:${x}px;top:${y}px;width:${s}px;height:${s}px;border-radius:50%;background:#fff;opacity:${.25+.5*rnd(i+7)}"></div>`}
  return h}
 if(sc=='line'){ // degradado cálido con rayas que se mueven y el icono del tema girando
  const off=(t*120)%160, rot=t*40;
  return `<div class="bg" style="background:linear-gradient(160deg,#FF8A1F,#FF3D77 70%,#C2186B)"></div>`+
  `<div class="bg" style="background:repeating-linear-gradient(135deg,#ffffff14 0 40px,transparent 40px 80px);background-position:${off}px 0"></div>`+
  `<svg width="520" height="520" viewBox="0 0 200 200" style="position:absolute;left:280px;top:1180px;transform:rotate(${Math.sin(t*1.5)*12}deg) scale(${1+.05*Math.sin(t*4)});opacity:.9"><g fill="none" stroke="#fff" stroke-width="10" stroke-linecap="round">${ICON[TOPIC]}</g></svg>`+
  `<div style="position:absolute;left:-200px;top:-200px;width:700px;height:700px;border:6px solid #ffffff30;border-radius:50%;transform:rotate(${rot}deg)"></div>`}
 if(sc=='turn'){ // amarillo con trama de puntos y rayos
  const off=(t*40)%56, rot=t*12;
  return `<div class="bg" style="background:#FFD400"></div>`+
  `<div class="bg" style="background:conic-gradient(from ${rot}deg at 50% 45%,#ffffff55 0 10deg,transparent 10deg 30deg,#ffffff55 30deg 40deg,transparent 40deg 60deg,#ffffff55 60deg 70deg,transparent 70deg 90deg,#ffffff55 90deg 100deg,transparent 100deg 120deg,#ffffff55 120deg 130deg,transparent 130deg 150deg,#ffffff55 150deg 160deg,transparent 160deg 180deg,#ffffff55 180deg 190deg,transparent 190deg 210deg,#ffffff55 210deg 220deg,transparent 220deg 240deg,#ffffff55 240deg 250deg,transparent 250deg 270deg,#ffffff55 270deg 280deg,transparent 280deg 300deg,#ffffff55 300deg 310deg,transparent 310deg 330deg,#ffffff55 330deg 340deg,transparent 340deg 360deg)"></div>`+
  `<div class="bg" style="background-image:radial-gradient(#0A0A0A33 22%,transparent 24%);background-size:56px 56px;background-position:${off}px ${off}px;-webkit-mask-image:linear-gradient(transparent 55%,#000)"></div>`}
 if(sc=='list'){ // papel con tres casillas que se marcan
  const q=dur/3; let h=`<div class="bg" style="background:#F4F1EA"></div><div class="bg" style="background-image:linear-gradient(#0A0A0A0d 2px,transparent 2px);background-size:100% 64px"></div>`;
  for(let i=0;i<3;i++){const a=oc(cl((lt-i*q+.3)/.35)), ck=cl((lt-i*q-.2)/.25), y=1130+i*170;
   h+=`<div style="position:absolute;left:150px;top:${y}px;width:780px;height:130px;border-radius:28px;background:#fff;box-shadow:0 14px 40px #0000001f;transform:translateX(${(1-a)*900}px);display:flex;align-items:center;padding-left:34px;box-sizing:border-box">`+
   `<div style="width:70px;height:70px;border-radius:18px;border:6px solid ${ck>0?'#19C37D':'#0A0A0A33'};background:${ck>0?'#19C37D':'transparent'};display:flex;align-items:center;justify-content:center">`+
   `<svg width="50" height="50" viewBox="0 0 50 50"><path d="M8 26 L21 38 L43 12" fill="none" stroke="#fff" stroke-width="8" stroke-linecap="round" stroke-linejoin="round" stroke-dasharray="60" stroke-dashoffset="${60*(1-ck)}"/></svg></div>`+
   `<div style="margin-left:30px;height:22px;width:${380+i*60}px;border-radius:11px;background:#0A0A0A1a"></div></div>`}
  return h}
 // CTA: azul con rayos girando y confeti
 let h=`<div class="bg" style="background:radial-gradient(1000px 1000px at 50% 30%,#4d72ff,#1F4BFF 55%,#0d2bbf)"></div>`+
 `<div class="bg" style="background:repeating-conic-gradient(from ${t*25}deg at 50% 38%,#ffffff1c 0 9deg,transparent 9deg 22deg)"></div>`;
 const cols=['#FFD400','#fff','#FF3D77','#19C37D','#0A0A0A'];
 for(let i=0;i<60;i++){const x=rnd(i)*1080+Math.sin(lt*2+i)*30, y=-60+((lt*(380+rnd(i+2)*420)+rnd(i+4)*400)), r=lt*300*(rnd(i+6)-.5);
  if(y<1980)h+=`<div style="position:absolute;left:${x}px;top:${y}px;width:${14+rnd(i+8)*14}px;height:${8+rnd(i+9)*8}px;background:${cols[i%5]};transform:rotate(${r}deg)"></div>`}
 return h}
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
   const p=HOOK||ci==0?1:cl((t-w.t+.03)/.22), q=ob(p);
   const tag=w.hi?`class="tag" style="background:${S.tb};color:${S.tc};transform:rotate(${(rnd(ci*7+j)-.5)*6}deg) scale(${HOOK&&!on?1:(HOOK&&j==0?1:ob(cl((t-w.t)/.25)))})"`:`style="color:${S.fg}"`;
   ws+=`<span class="m" style="opacity:${HOOK?(on?1:.3):cl(p*3)};transform:translateY(${(1-q)*60}px) scale(${.6+.4*q})"><span ${tag} ${w.hi?'':''}>${w.w}</span></span>`});
  const pop=HOOK?1:1+.18*(1-oc(cl(ct/.2))), rot=HOOK?0:(rnd(ci)-.5)*5;
  const sh=(sc=='turn'||sc=='list')?'none':'0 12px 40px #00000066';
  h=`<div style="position:absolute;left:60px;right:60px;top:${y}px;transform:translateY(-50%) scale(${pop}) rotate(${rot}deg);filter:blur(${HOOK?0:(1-oc(cl(ct/.15)))*6}px);text-align:center;font-size:${fs}px;font-weight:900;line-height:1.06;letter-spacing:-.03em;text-shadow:${sh}">${ws}</div>`;
 } else {
  const ct=t-VEND, m=d=>ob(cl((ct-d)/.35));
  h=`<div style="position:absolute;left:0;right:0;top:520px;text-align:center;font-weight:900;letter-spacing:-.03em;text-shadow:0 12px 40px #0000004d">`+
  `<div style="font-size:110px;transform:scale(${m(0)})">Escríbeme</div>`+
  `<div style="display:inline-block;margin:24px 0;font-size:170px;padding:0 .25em .06em;border-radius:.16em;background:#FFD400;color:#0A0A0A;transform:rotate(-3deg) scale(${m(.15)*(1+.04*Math.sin(ct*8))})">${KW}</div>`+
  `<div style="font-size:110px;transform:scale(${m(.3)})">por privado</div></div>`;
  const a=oc(cl((ct-.5)/.4)),bob=Math.sin(ct*6)*16;
  h+=`<svg width="140" height="260" style="position:absolute;left:470px;top:${1240+bob}px;opacity:${a}"><path d="M70 10 L70 230 M25 190 L70 240 L115 190" fill="none" stroke="#fff" stroke-width="12" stroke-linecap="round" stroke-linejoin="round"/></svg>`;
 }
 const cam=document.getElementById('cam');cam.innerHTML=h;
 const shk=k&&lt<.25?(1-lt/.25)*18:0; cam.style.transform=`translate(${shk*Math.sin(t*90)}px,${shk*Math.cos(t*70)}px)`;
 const dark=(sc=='turn'||sc=='list');
 document.getElementById('handle').style.color=dark?'#0A0A0A':'#fff';
 const pr=document.getElementById('prog');pr.style.width=(t/TOTAL*1080)+'px';pr.style.background=sc=='turn'?'#0A0A0A':(sc=='cta'?'#FFD400':'#1F4BFF');
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
