"""Trial Reels v2 (más dinámicos): tipografía cinética palabra a palabra, sincronizada con la voz de Rafa N.
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
WORK = "/tmp/trial2"
VOZ = os.environ.get("VOZ_DIR", "/tmp/voz")
TEMPO = 1.08  # voz un poco más rápida
GAP = .12     # pausa entre frases
CTA_HOLD = 1.8

# Lo que dice cada clip (tal cual se generó en ElevenLabs)
SAY = {
    "t1a": "¿Podrías irte una semana sin que tu negocio se pare?",
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
HI = {"semana", "pare", "libre", "tampoco", "todo", "tiempo", "orden", "uno", "dos", "tres", "soltarías",
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
        if re.search(r"[.,:?…]$", w) or len(cur) == 3 or len(txt) > 16 or nxt_scene or i == len(words) - 1:
            chunks.append(cur)
            cur = []
    C = []
    for ci, idx in enumerate(chunks):
        ws = [{"t": words[j][0], "w": words[j][1],
               "hi": re.sub(r"[^\wáéíóúñ]", "", words[j][1].lower()) in HI} for j in idx]
        emo = next((EMOJI[k] for k in (re.sub(r"[^\wáéíóúñ]", "", x["w"].lower()) for x in ws) if k in EMOJI), "")
        C.append({"t": ws[0]["t"], "ws": ws, "sc": words[idx[0]][2], "emo": emo})
    return C, audio, voice_end, voice_end + CTA_HOLD


HTML = r"""<html><head><style>
@font-face{font-family:M;src:url(file://%(F)sMontserrat-Bold.ttf);font-weight:700}
@font-face{font-family:M;src:url(file://%(F)sMontserrat-ExtraBold.ttf);font-weight:800}
@font-face{font-family:M;src:url(file://%(F)sMontserrat-Black.ttf);font-weight:900}
body{margin:0;background:#000}
#v{position:relative;overflow:hidden;width:1080px;height:1920px;font-family:M;color:#fff}
.bg{position:absolute;inset:0}
.w{display:inline-block;margin:0 .14em;transform-origin:center bottom}
.hi{padding:0 .12em;border-radius:.12em}
</style></head><body><div id="v">
<div class="bg" id="b0" style="background:radial-gradient(900px 900px at 80%% 85%%,#1F4BFF66,transparent 70%%),radial-gradient(700px 600px at 0%% 0%%,#1F4BFF26,transparent 70%%),#070708"></div>
<div class="bg" id="b1" style="background:radial-gradient(900px 900px at 20%% 10%%,#4d72ff,transparent 70%%),#1F4BFF;opacity:0"></div>
<div class="bg" id="b2" style="background:radial-gradient(900px 900px at 50%% 40%%,#ffffff,#e9ecf5 80%%);opacity:0"></div>
<div class="bg" id="grid" style="background-image:linear-gradient(#ffffff12 2px,transparent 2px),linear-gradient(90deg,#ffffff12 2px,transparent 2px);background-size:90px 90px"></div>
<div id="cam" class="bg"></div>
<svg class="bg" width="1080" height="1920" style="mix-blend-mode:overlay;opacity:.38"><filter id="n"><feTurbulence type="fractalNoise" baseFrequency="0.85" numOctaves="3" stitchTiles="stitch"/><feColorMatrix type="saturate" values="0"/></filter><rect width="100%%" height="100%%" filter="url(#n)"/></svg>
<div class="bg" id="prog" style="height:12px;bottom:auto;background:#1F4BFF;width:0"></div>
<div id="handle" style="position:absolute;left:0;right:0;bottom:130px;text-align:center;font-size:32px;font-weight:700;opacity:.85">@alejandro.segura.asesor</div>
<div class="bg" id="flash" style="background:#fff;opacity:0"></div>
</div>
<script>
const C=%(C)s, VEND=%(VEND)s, TOTAL=%(TOTAL)s, KW="%(KW)s";
const cl=x=>Math.max(0,Math.min(1,x)), oc=p=>1-Math.pow(1-p,3), ob=p=>{const c1=2.2,c3=c1+1;return 1+c3*Math.pow(p-1,3)+c1*Math.pow(p-1,2)};
function rnd(i){const x=Math.sin(i*12.9898)*43758.5453;return x-Math.floor(x)}
function style(i,c){ if(c.sc=='hook')return i%%2?1:0; if(c.sc=='turn')return 1; if(c.sc=='cta')return 0; return [0,1,0,2][i%%4]}
function render(t){
 const cam=document.getElementById('cam');
 let ci=0;while(ci+1<C.length&&t>=C[ci+1].t)ci++;
 let st=0,h='';
 if(t<VEND){
  const c=C[ci],lt=t-c.t;st=style(ci,c);
  const fg=st==2?'#0A0A0A':'#fff', hb=st==1?'#0A0A0A':'#1F4BFF', hc='#fff';
  const n=c.ws.reduce((a,w)=>a+w.w.length,0);
  const lng=Math.max(...c.ws.map(w=>w.w.length)), base=c.ws.length==1?200:(n>13?120:n>9?135:155);
  const fs=Math.min(base, Math.floor(900/(Math.max(lng, c.ws.length>1?Math.min(n+c.ws.length-1,12):lng)*.72)));
  const rot=(rnd(ci)-.5)*6, y=(c.sc=='hook'?700:620)+(rnd(ci+7)-.5)*160;
  let ws='';
  c.ws.forEach((w,j)=>{const p=cl((t-w.t)/.18);if(t<w.t-.02)return;const q=ob(p);
   const s=w.hi?`background:${hb};color:${hc}`:`color:${fg}`;
   ws+=`<span class="w ${w.hi?'hi':''}" style="${s};transform:translateY(${(1-q)*70}px) scale(${.5+.5*q});opacity:${cl(p*3)}">${w.w}</span>`});
  const zin=1+.35*(1-oc(cl(lt/.22)))+.04*lt;
  h+=`<div style="position:absolute;left:60px;right:60px;top:${y}px;text-align:center;font-size:${fs}px;font-weight:900;line-height:1.08;letter-spacing:-.03em;transform:rotate(${rot}deg) scale(${zin})">${ws}</div>`;
  if(c.emo){const p=ob(cl((lt-.08)/.3));h+=`<div style="position:absolute;left:${rnd(ci+3)>.5?720:120}px;top:${y-260}px;font-size:200px;transform:scale(${p}) rotate(${(rnd(ci+5)-.5)*30}deg)">${c.emo}</div>`}
  const k=lt;const sh=k<.18?(1-k/.18)*22:0;
  cam.style.transform=`translate(${sh*Math.sin(t*95)}px,${sh*Math.cos(t*77)}px)`;
  document.getElementById('flash').style.opacity=Math.max(0,.35-lt*3.5);
 } else {
  const lt=t-VEND;st=0;
  h+=`<div style="position:absolute;left:80px;right:80px;top:560px;font-size:96px;font-weight:900;line-height:1.05;transform:scale(${ob(cl(lt/.3))});transform-origin:left">Escríbeme<br><span style="background:#1F4BFF;padding:0 .15em">${KW}</span><br>por privado</div>`;
  const a=oc(cl((lt-.3)/.4)),bob=Math.sin(lt*7)*14;
  h+=`<svg width="160" height="300" style="position:absolute;left:80px;top:${1080+bob}px;opacity:${a}"><path d="M80 10 L80 270 M25 215 L80 280 L135 215" fill="none" stroke="#1F4BFF" stroke-width="12" stroke-linecap="round" stroke-linejoin="round"/></svg>`;
  cam.style.transform='';document.getElementById('flash').style.opacity=0;
 }
 cam.innerHTML=h;
 ['b0','b1','b2'].forEach((id,i)=>document.getElementById(id).style.opacity=i==st?1:0);
 document.getElementById('grid').style.opacity=st==2?0:1;
 document.getElementById('handle').style.color=st==2?'#0A0A0A':'#fff';
 const pr=document.getElementById('prog');pr.style.width=(t/TOTAL*1080)+'px';pr.style.background=st==1?'#0A0A0A':'#1F4BFF';
}
</script></body></html>"""


def sfx(C, total, vend):
    out = np.zeros(int(SR * (total + 1)))

    def put(sig, at):
        i = int(at * SR)
        out[i:i + len(sig)] += sig[:max(0, len(out) - i)]
    thud, pop, wh = tone(120, 45, .3, .8, 12), tone(1000, 450, .09, .25, 34), whoosh(.25, .25)
    prev = None
    for c in C:
        if c["sc"] != prev:
            put(wh, max(0, c["t"] - .18))
            put(thud, c["t"])
        else:
            put(pop, c["t"])
        prev = c["sc"]
    put(thud, vend)
    beat, t = 60 / 124, 0.0
    kick = tone(90, 40, .22, .5, 14)
    hat = np.random.default_rng(3).normal(0, .05, int(SR * .035)) * np.exp(-np.linspace(0, 6, int(SR * .035)))
    k = 0
    while t < total - .3:
        put(kick, t)
        put(hat, t + beat / 2)
        if k % 2 == 0:
            f = [55, 55, 65.4, 49][(k // 2) % 4]
            put(tone(f, f, beat * 1.8, .16, 1.2), t)
        t += beat
        k += 1
    e, n = int(SR * total), int(SR * .6)
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
                                                "TOTAL": total, "KW": KW[rid[:2]]})
    pg = await b.new_page(viewport={"width": 1080, "height": 1920})
    await pg.goto(f"file://{wd}/reel.html")
    await pg.evaluate("document.fonts.ready")
    for i in range(int(total * FPS)):
        await pg.evaluate(f"render({i / FPS})")
        await pg.screenshot(path=f"{wd}/f{i:05d}.jpg", type="jpeg", quality=90)
    await pg.close()
    write_wav(f"{wd}/sfx.wav", sfx(C, total, vend))
    voz = np.zeros(int(SR * (total + 1)), np.float32)
    for at, x in audio:
        i = max(0, int(at * SR))
        voz[i:i + len(x)] += x[:len(voz) - i]
    write_wav(f"{wd}/voz.wav", voz)
    out = os.path.join(OUTDIR, f"r2-{rid}.mp4")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-framerate", str(FPS), "-i", f"{wd}/f%05d.jpg",
                    "-i", f"{wd}/sfx.wav", "-i", f"{wd}/voz.wav", "-filter_complex",
                    "[1:a]volume=0.25[s];[2:a]volume=1.4[v];[s][v]amix=inputs=2:duration=first:normalize=0,"
                    "loudnorm=I=-14:TP=-1.5[a]", "-map", "0:v", "-map", "[a]",
                    "-vf", "scale=720:1280:flags=lanczos", "-c:v", "libx264", "-preset", "slow", "-crf", "26",
                    "-maxrate", "1500k", "-bufsize", "3000k", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "96k",
                    "-ar", "44100", "-shortest", "-movflags", "+faststart", out], check=True)
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
