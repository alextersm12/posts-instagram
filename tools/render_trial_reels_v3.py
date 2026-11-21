"""Trial Reels v3 (más dinámicos y más calidad): 1080x1920 nítido, transiciones con cortinilla, palabra gigante en contorno de fondo, subrayado animado en vez de emojis.
Basado en v2: tipografía cinética palabra a palabra, sincronizada con la voz de Rafa N.
Cada 2-3 palabras cambia la composición (fondo negro / azul / blanco, zoom, giro, sacudida), con un golpe de sonido.
Reutiliza los textos y las voces de render_trial_reels.py (un clip por escena en /tmp/voz).
Uso: python3 tools/render_trial_reels_v2.py [id ...]   Salida: trial/r2-<id>.mp4 (720x1280)."""
import asyncio, json, os, re, subprocess, sys
import numpy as np
from playwright.async_api import async_playwright

sys.path.insert(0, os.path.dirname(__file__))
from render_12_reel import write_wav, tone, whoosh, load_pcm, SR, FPS, F  # noqa: E402

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
OUTDIR = os.path.join(ROOT, "trial")
WORK = "/tmp/trial3"
VOZ = os.environ.get("VOZ_DIR", "/tmp/voz")
TEMPO = 1.08  # voz un poco más rápida
GAP = .12     # pausa entre frases
CTA_HOLD = 1.8

# Lo que dice cada clip (tal cual se generó en ElevenLabs)
SAY = {
    "t1a": "¿Podrías irte una semana sin que tu negocio se pare?",
    "t1c": "Si mañana te pones malo… ¿tu negocio abre?",
    "t1d": "¿Cuántas cosas de tu empresa solo sabes hacer tú?",
    "t2c": "¿Sabes qué cliente te hace perder dinero?",
    "t2d": "¿Cuánto te queda limpio de cada venta?",
    "t3c": "Lunes, 9 de la mañana: ¿qué es lo primero que haces?",
    "t3d": "Si todo es urgente… ¿qué haces primero?",
    "t1b": "Si todo pasa por ti, tu negocio no es libre. Y tú tampoco.",
    "t1-line": "Presupuestos. Quejas. Pagos. Todo te espera a ti.",
    "t1-turn": "No es falta de tiempo. Es falta de orden.",
    "t1-list": "Prueba esto. Uno: apunta lo que haces en una semana. Dos: marca lo que solo puedes hacer tú. Tres: lo demás, a un proceso o a una persona.",
    "t1-cta": "¿Qué sería lo primero que soltarías? Escríbeme «tiempo» por privado.",
    "t2a": "¿Vendes más que hace un año… y te queda lo mismo?",
    "t2b": "Vender más no es lo mismo que ganar más.",
    "t2-line": "Más ventas traen más horas, más costes… y más descuentos.",
    "t2-turn": "No importa cuánto entra. Importa cuánto se queda.",
    "t2-list": "Mira tres cosas. Qué servicio te deja más margen. Qué cliente te cuesta más de lo que paga. Y qué descuento das sin pensarlo.",
    "t2-cta": "¿Sabes cuál de tus servicios te deja más? Escríbeme «margen» por privado.",
    "t3a": "¿Cuántas cosas tienes apuntadas para esta semana?",
    "t3b": "Hacerlo todo es la forma más rápida de no avanzar.",
    "t3-line": "Cuando todo es urgente… nada lo es.",
    "t3-turn": "No necesitas hacer más. Necesitas elegir.",
    "t3-list": "Entender, priorizar, decidir. Escribe todo lo pendiente. Quédate con tres: lo que da dinero o libera tiempo. Y lo demás, a la semana que viene.",
    "t3-cta": "¿Cuál es tu prioridad número uno esta semana? Escríbeme «orden» por privado.",
}
KW = {"t1": "TIEMPO", "t2": "MARGEN", "t3": "ORDEN"}
HI = {"semana", "malo", "abre", "tú", "perder", "limpio", "venta", "lunes", "primero", "pare", "libre", "tampoco", "todo", "tiempo", "orden", "uno", "dos", "tres", "soltarías",
      "vendes", "mismo", "ganar", "horas", "costes", "descuentos", "entra", "queda", "margen", "cliente",
      "descuento", "más", "urgente", "nada", "elegir", "avanzar", "pendiente", "dinero", "decidir",
      "priorizar", "entender", "prioridad", "persona", "proceso", "ti", "pagos", "quejas", "presupuestos"}
EMOJI = {"semana": "📅", "pagos": "💸", "quejas": "📞", "presupuestos": "🧾", "orden": "🧭", "tiempo": "⏳",
         "dinero": "💶", "margen": "📊", "descuentos": "🏷️", "descuento": "🏷️", "urgente": "🚨",
         "elegir": "🎯", "avanzar": "🚀", "proceso": "⚙️", "horas": "⏰", "costes": "📉", "pendiente": "📝"}


def speech_segments(path):
    x = load_pcm(path)
    err = subprocess.run(["ffmpeg", "-i", path, "-af", "silencedetect=noise=-35dB:d=0.12", "-f", "null", "-"],
                         capture_output=True, text=True).stderr
    ss = [float(v) for v in re.findall(r"silence_start: ([\d.]+)", err)]
    se = [float(v) for v in re.findall(r"silence_end: ([\d.]+)", err)]
    dur, segs, cur = len(x) / SR, [], 0.0
    for a, b in zip(ss, se):
        if a - cur > .05:
            segs.append((cur, a))
        cur = b
    if len(ss) == len(se) and dur - cur > .05:
        segs.append((cur, dur))
    return x, segs


def phrases(text):
    parts = re.split(r"(?<=[.,:?…])\s+", text.replace("«", "").replace("»", ""))
    return [p.split() for p in parts if p.strip()]


def word_times(text, segs):
    """Reparte las palabras por los trozos de voz; dentro de cada trozo, según su longitud."""
    ph = phrases(text)
    words = [w for p in ph for w in p]
    if len(segs) == len(ph):
        groups = list(zip(ph, segs))
    else:  # si no cuadra, un solo bloque desde el primer al último sonido
        groups = [(words, (segs[0][0], segs[-1][1]))]
    out = []
    for ws, (a, b) in groups:
        L = [len(re.sub(r"\W", "", w)) + 2 for w in ws]
        t = a
        for w, l in zip(ws, L):
            out.append((t, w))
            t += (b - a) * l / sum(L)
    return out


def build(rid):
    keys = [rid] + [f"{rid[:2]}-{k}" for k in ("line", "turn", "list", "cta")]
    audio, words, t = [], [], .15
    os.makedirs(f"{WORK}/{rid}", exist_ok=True)
    for k in keys:
        src = f"{VOZ}/{k}.mp3"
        fast = f"{WORK}/{rid}/{k}.wav"
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", src, "-af", f"atempo={TEMPO}", "-ac", "1",
                        "-ar", str(SR), fast], check=True)
        x, segs = speech_segments(fast)
        a0, b1 = segs[0][0], segs[-1][1]
        audio.append((t - a0, x))
        for wt, w in word_times(SAY[k], segs):
            words.append([round(t + wt - a0, 3), w, k.split("-")[-1] if "-" in k else "hook"])
        t += b1 - a0 + GAP
    voice_end = t
    # trozos de 1-3 palabras: corta en puntuación o cada 3 palabras / 16 letras
    chunks, cur = [], []
    for i, (wt, w, sc) in enumerate(words):
        cur.append(i)
        txt = " ".join(words[j][1] for j in cur)
        nxt_scene = i + 1 < len(words) and words[i + 1][2] != sc
        if (sc != "hook" and (re.search(r"[.,:?…]$", w) or len(cur) == 3 or len(txt) > 16)) or (False) or nxt_scene or i == len(words) - 1:
            chunks.append(cur)
            cur = []
    C = []
    for ci, idx in enumerate(chunks):
        ws = [{"t": words[j][0], "w": words[j][1],
               "hi": re.sub(r"[^\wáéíóúñ]", "", words[j][1].lower()) in HI} for j in idx]
        emo = next((EMOJI[k] for k in (re.sub(r"[^\wáéíóúñ]", "", x["w"].lower()) for x in ws) if k in EMOJI), "")
        C.append({"t": ws[0]["t"], "ws": ws, "sc": words[idx[0]][2], "emo": emo})
    return C, audio, voice_end, voice_end + CTA_HOLD


BIG = {"t1": {"a": "?", "b": "TÚ", "c": "?", "d": "TÚ", "line": "TODO", "turn": "ORDEN", "list": "1·2·3", "cta": "TIEMPO"},
       "t2": {"a": "?", "b": "+€", "c": "€", "d": "€", "line": "MÁS", "turn": "MARGEN", "list": "1·2·3", "cta": "MARGEN"},
       "t3": {"a": "?", "b": "TODO", "c": "9:00", "d": "?", "line": "URGENTE", "turn": "ELEGIR", "list": "1·2·3", "cta": "ORDEN"}}


HTML = r"""<html><head><style>
@font-face{font-family:M;src:url(file://%(F)sMontserrat-Medium.ttf);font-weight:500}
@font-face{font-family:M;src:url(file://%(F)sMontserrat-Bold.ttf);font-weight:700}
@font-face{font-family:M;src:url(file://%(F)sMontserrat-ExtraBold.ttf);font-weight:800}
@font-face{font-family:M;src:url(file://%(F)sMontserrat-Black.ttf);font-weight:900}
body{margin:0;background:#000}
#v{position:relative;overflow:hidden;width:1080px;height:1920px;font-family:M;color:#fff}
.bg{position:absolute;inset:0}
.m{display:inline-block;overflow:hidden;vertical-align:bottom;padding:.06em .02em .1em;margin:0 .1em}
.w{display:inline-block;position:relative}
.m{padding-bottom:.2em;margin-bottom:-.12em}
.u{position:absolute;left:-.04em;bottom:-.1em;height:.13em;border-radius:.07em}
</style></head><body><div id="v">
<div class="bg" id="L0"></div><div class="bg" id="L1"></div><div class="bg" id="FX"></div>
<div class="bg" id="big" style="display:flex;align-items:center;justify-content:center;font-weight:900;font-size:560px;letter-spacing:-.04em;white-space:nowrap;color:transparent"></div>
<div id="cam" class="bg"></div>
<div class="bg" style="background:radial-gradient(1100px 1500px at 50%% 48%%,transparent 55%%,#00000073 100%%)"></div>
<svg class="bg" width="1080" height="1920" style="mix-blend-mode:overlay;opacity:.32"><filter id="n"><feTurbulence type="fractalNoise" baseFrequency="0.9" numOctaves="3" seed="%(SEED)s" stitchTiles="stitch"/><feColorMatrix type="saturate" values="0"/></filter><rect width="100%%" height="100%%" filter="url(#n)"/></svg>
<div class="bg" id="prog" style="height:10px;bottom:auto;width:0"></div>
<div id="handle" style="position:absolute;left:0;right:0;bottom:150px;text-align:center;font-size:30px;font-weight:700;letter-spacing:.02em;opacity:.8">@alejandro.segura.asesor</div>
</div>
<script>
const C=%(C)s, VEND=%(VEND)s, TOTAL=%(TOTAL)s, KW="%(KW)s", BIG=%(BIG)s, HK="%(HK)s";
const cl=x=>Math.max(0,Math.min(1,x)), oc=p=>1-Math.pow(1-p,3), eio=p=>p<.5?4*p*p*p:1-Math.pow(-2*p+2,3)/2,
 ob=p=>{const c1=1.5,c3=c1+1;return 1+c3*Math.pow(p-1,3)+c1*Math.pow(p-1,2)};
function rnd(i){const x=Math.sin(i*12.9898)*43758.5453;return x-Math.floor(x)}
const SCN={hook:0,line:0,turn:1,list:2,cta:0};
const BGS=['radial-gradient(1000px 1000px at 85%% 90%%,#1F4BFF70,transparent 70%%),radial-gradient(800px 700px at 0%% 0%%,#1F4BFF2e,transparent 70%%),linear-gradient(#0b0c10,#050506)',
 'radial-gradient(1000px 1000px at 15%% 8%%,#5a7dff,transparent 70%%),radial-gradient(900px 900px at 100%% 100%%,#1236d6,transparent 70%%),#1F4BFF',
 'radial-gradient(1100px 1100px at 50%% 35%%,#ffffff,#e6e9f2 85%%)'];
// inicio de cada escena
const SS=[];C.forEach((c,i)=>{if(!i||C[i-1].sc!=c.sc)SS.push({t:c.t,sc:c.sc})});SS.push({t:VEND,sc:'cta'});
function bgHTML(st,t){
 if(st==0){ // negro: dos luces azules que orbitan + suelo en rejilla con perspectiva que avanza + barrido de luz
  const ax=540+380*Math.sin(t*.35), ay=1500+160*Math.cos(t*.27), bx=200+260*Math.cos(t*.22), by=300+180*Math.sin(t*.3);
  const off=(t*90)%%120, sw=((t*.18)%%1.6-.3)*1600;
  return `<div class="bg" style="background:linear-gradient(#08090d,#030304)"></div>`+
  `<div class="bg" style="background:radial-gradient(760px 760px at ${ax}px ${ay}px,#1F4BFF8c,transparent 70%%),radial-gradient(620px 620px at ${bx}px ${by}px,#1F4BFF40,transparent 70%%)"></div>`+
  `<div style="position:absolute;left:-600px;right:-600px;top:1280px;height:1400px;transform:perspective(700px) rotateX(72deg);transform-origin:top;background-image:linear-gradient(#3d63ff59 3px,transparent 3px),linear-gradient(90deg,#3d63ff59 3px,transparent 3px);background-size:120px 120px;background-position:0 ${off}px;-webkit-mask-image:linear-gradient(transparent,#000 30%%,#000 60%%,transparent)"></div>`+
  `<div class="bg" style="background:linear-gradient(115deg,transparent ${sw-220}px,#ffffff0d ${sw}px,transparent ${sw+220}px)"></div>`;}
 if(st==1){ // azul: degradado con profundidad + ondas negras finas que se mueven
  let w='';for(let i=0;i<9;i++){let d='';for(let x=-40;x<=1120;x+=40){const y=1180+i*52+Math.sin(x/170+t*1.3+i*.55)*(40+i*6);d+=`${d?'L':'M'}${x} ${y.toFixed(1)} `}
   w+=`<path d="${d}" fill="none" stroke="#0A0A0A" stroke-opacity="${.12+i*.035}" stroke-width="2.4"/>`}
  const gx=300+200*Math.sin(t*.4);
  return `<div class="bg" style="background:radial-gradient(1000px 900px at ${gx}px 250px,#6f8dff,transparent 70%%),radial-gradient(900px 900px at 100%% 100%%,#0d2bbf,transparent 70%%),#1F4BFF"></div>`+
  `<svg class="bg" width="1080" height="1920">${w}</svg>`;}
 // claro: papel milimetrado que se desplaza, luz cálida y sombra suave
 const off=(t*30)%%60;
 return `<div class="bg" style="background:radial-gradient(1200px 1100px at 50%% 35%%,#ffffff,#e3e7f1 85%%)"></div>`+
 `<div class="bg" style="background-image:linear-gradient(#1F4BFF1f 2px,transparent 2px),linear-gradient(90deg,#1F4BFF1f 2px,transparent 2px),linear-gradient(#1F4BFF0d 1px,transparent 1px),linear-gradient(90deg,#1F4BFF0d 1px,transparent 1px);background-size:240px 240px,240px 240px,60px 60px,60px 60px;background-position:0 ${off}px;-webkit-mask-image:radial-gradient(900px 1200px at 50%% 45%%,#000 30%%,transparent 85%%)"></div>`;
}
function bgAt(t){let k=0;while(k+1<SS.length&&t>=SS[k+1].t)k++;return k}
function render(t){
 const cam=document.getElementById('cam'), L0=document.getElementById('L0'), L1=document.getElementById('L1');
 const k=bgAt(t), sc=SS[k].sc, st=SCN[sc], prev=k?SCN[SS[k-1].sc]:st, lt=t-SS[k].t;
 // cortinilla circular al cambiar de escena
 L0.innerHTML=bgHTML(prev,t); L1.innerHTML=bgHTML(st,t);
 const wp=prev==st?1:eio(cl(lt/.5)); L1.style.clipPath=`circle(${wp*1300}px at 540px 1000px)`;
 const fg=st==2?'#0A0A0A':'#fff', acc=st==1?'#0A0A0A':'#1F4BFF';
 // palabra gigante en contorno, entra deslizando y deriva
 const bk=sc=='hook'?HK:sc, bw=BIG[bk]||'';
 const bigE=document.getElementById('big');
 bigE.textContent=bw; bigE.style.webkitTextStroke=`3px ${st==2?'#1F4BFF55':(st==1?'#ffffff55':'#1F4BFF77')}`;
 bigE.style.transform=`translateX(${(1-oc(cl(lt/.9)))*300-lt*14}px) scale(${1.05+lt*.006})`;
 bigE.style.opacity=cl(lt/.4)*.9; bigE.style.top=(sc=='hook'?880:860)-960+'px'; bigE.style.bottom='auto'; bigE.style.height='1920px'; bigE.style.fontSize=(bw.length>5?380:560)+'px';
 let h='';
 if(t<VEND){
  let ci=0;while(ci+1<C.length&&t>=C[ci+1].t)ci++;
  const c=C[ci],ct=t-c.t;
  const n=c.ws.reduce((a,w)=>a+w.w.length,0);
  const lng=Math.max(...c.ws.map(w=>w.w.length)), base=c.ws.length==1?220:(n>13?138:n>9?156:178);
  const fs=Math.min(base, Math.floor(940/(Math.max(lng, c.ws.length>1?Math.min(n+c.ws.length-1,12):lng)*.72)));
  const y=sc=='hook'?880:860;
  let ws='';
  const HOOK=c.sc=='hook'; let fs2=fs; if(HOOK){fs2=n>34?112:n>24?126:140}
  c.ws.forEach((w,j)=>{if(HOOK){const on=t>=w.t-.03||j==0, col=w.hi?acc:fg;
    ws+=`<span class="m"><span class="w" style="color:${col};opacity:${on?1:.28};text-shadow:0 10px 40px #00000059">${w.w}</span></span>`;return}
   if(t<w.t-.03&&!(ci==0))return;const p=ci==0?1:cl((t-w.t+.03)/.32),q=oc(p);
   const col=w.hi?acc:fg, sh=st==2?'none':'0 10px 40px #00000059';
   const ul=w.hi?`<span class="u" style="background:${st==1?'#fff':'#1F4BFF'};width:${oc(cl((t-w.t-.12)/.35))*104}%%"></span>`:'';
   ws+=`<span class="m"><span class="w" style="color:${col};text-shadow:${sh};transform:translateY(${(1-q)*105}%%)">${w.w}${ul}</span></span>`});
  const zin=1+.06*(1-oc(cl(ct/.35)))+.012*ct;
  h+=`<div style="position:absolute;left:70px;right:70px;top:${y}px;transform:translateY(-50%%) scale(${zin});text-align:center;font-size:${fs2}px;font-weight:900;line-height:1.02;letter-spacing:-.035em">${ws}</div>`;
 } else {
  const ct=t-VEND;
  const m=(s,d)=>oc(cl((ct-d)/.4));
  h+=`<div style="position:absolute;left:96px;right:96px;top:560px;font-size:100px;font-weight:900;line-height:1.08;letter-spacing:-.03em">`+
   `<span class="m"><span class="w" style="transform:translateY(${(1-m(0,0))*105}%%)">Escríbeme</span></span><br>`+
   `<span class="m"><span class="w" style="transform:translateY(${(1-m(0,.12))*105}%%);color:#1F4BFF">${KW}<span class="u" style="background:#fff;width:${oc(cl((ct-.4)/.4))*104}%%"></span></span></span><br>`+
   `<span class="m"><span class="w" style="transform:translateY(${(1-m(0,.24))*105}%%)">por privado</span></span></div>`;
  const a=oc(cl((ct-.5)/.4)),bob=Math.sin(ct*5)*12, dl=600*(1-oc(cl((ct-.5)/.6)));
  h+=`<svg width="140" height="320" style="position:absolute;left:96px;top:${1090+bob}px;opacity:${a}"><path d="M70 10 L70 290 M30 250 L70 296 L110 250" fill="none" stroke="#1F4BFF" stroke-width="6" stroke-linecap="round" stroke-linejoin="round" stroke-dasharray="600" stroke-dashoffset="${dl}"/></svg>`;
 }
 cam.innerHTML=h;
 document.getElementById('handle').style.color=st==2?'#0A0A0A':'#fff';
 const pr=document.getElementById('prog');pr.style.width=(t/TOTAL*1080)+'px';pr.style.background=st==1?'#fff':'#1F4BFF';
}
</script></body></html>"""


def sfx(C, total, vend):
    """Capa sonora discreta: whoosh + golpe grave en cada cambio de escena y un pulso suave de fondo."""
    out = np.zeros(int(SR * (total + 1)))

    def put(sig, at):
        i = int(at * SR)
        out[i:i + len(sig)] += sig[:max(0, len(out) - i)]
    thud, wh, tick = tone(110, 42, .45, .7, 7), whoosh(.45, .35), tone(2400, 2400, .015, .05, 120)
    prev = None
    for c in C:
        if c["sc"] != prev:
            put(wh, max(0, c["t"] - .3))
            put(thud, c["t"])
        else:
            put(tick, c["t"])
        prev = c["sc"]
    put(wh, max(0, vend - .3))
    put(thud, vend)
    beat, t, k = 60 / 100, 0.0, 0
    kick = tone(70, 38, .3, .35, 10)
    while t < total - .3:
        if k % 2 == 0:
            put(kick, t)
        if k % 4 == 0:
            f = [55, 49, 65.4, 58.3][(k // 4) % 4]
            n = int(SR * beat * 4)
            tt = np.arange(n) / SR
            pad = .05 * (np.sin(2 * np.pi * f * tt) + .5 * np.sin(2 * np.pi * f * 2.003 * tt)) * np.sin(np.linspace(0, np.pi, n))
            put(pad, t)
        t += beat
        k += 1
    e, n = int(SR * total), int(SR * .8)
    out[e - n:e] *= np.linspace(1, 0, n)
    out[e:] = 0
    return out


async def render_one(b, rid):
    C, audio, vend, total = build(rid)
    wd = f"{WORK}/{rid}"
    for f in os.listdir(wd):
        if f.endswith(".jpg"):
            os.remove(os.path.join(wd, f))
    open(f"{wd}/reel.html", "w").write(HTML % {"F": F, "C": json.dumps(C, ensure_ascii=False), "VEND": vend,
                                                "TOTAL": total, "KW": KW[rid[:2]], "SEED": 1,
                                                "BIG": json.dumps(BIG[rid[:2]], ensure_ascii=False), "HK": rid[2]})
    pg = await b.new_page(viewport={"width": 1080, "height": 1920})
    await pg.goto(f"file://{wd}/reel.html")
    await pg.evaluate("document.fonts.ready")
    for i in range(int(total * FPS)):
        await pg.evaluate(f"render({i / FPS})")
        await pg.screenshot(path=f"{wd}/f{i:05d}.jpg", type="jpeg", quality=97)
    await pg.close()
    write_wav(f"{wd}/sfx.wav", sfx(C, total, vend))
    voz = np.zeros(int(SR * (total + 1)), np.float32)
    for at, x in audio:
        i = max(0, int(at * SR))
        voz[i:i + len(x)] += x[:len(voz) - i]
    write_wav(f"{wd}/voz.wav", voz)
    out = os.path.join(OUTDIR, f"r3-{rid}.mp4")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-framerate", str(FPS), "-i", f"{wd}/f%05d.jpg",
                    "-i", f"{wd}/sfx.wav", "-i", f"{wd}/voz.wav", "-filter_complex",
                    "[1:a]volume=0.3[s];[2:a]highpass=f=70,acompressor=threshold=-20dB:ratio=3:attack=5:release=80,"
                    "volume=1.4[v];[s][v]amix=inputs=2:duration=first:normalize=0,loudnorm=I=-14:TP=-1.5[a]",
                    "-map", "0:v", "-map", "[a]", "-c:v", "libx264", "-preset", "slow", "-crf", "17",
                    "-profile:v", "high", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k",
                    "-ar", "48000", "-shortest", "-movflags", "+faststart", out], check=True)
    print(rid, round(total, 1), "s", len(C), "trozos", os.path.getsize(out) // 1024, "KB")


async def main(ids):
    os.makedirs(OUTDIR, exist_ok=True)
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path="/opt/pw-browsers/chromium", args=["--allow-file-access-from-files"])
        for rid in ids:
            await render_one(b, rid)
        await b.close()


if __name__ == "__main__":
    asyncio.run(main(sys.argv[1:] or [f"t{i}{h}" for i in (1, 2, 3) for h in "ab"]))
