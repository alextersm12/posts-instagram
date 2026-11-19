"""Trial Reels de prueba (ronda 1, 23-25 nov 2026): 3 temas x 2 ganchos, solo texto en pantalla + sonido.
Mismo cuerpo dentro de cada tema; solo cambia el gancho (A = pregunta, B = afirmación) para medir el gancho aislado.
Voz en off de ElevenLabs (Rafa N), un clip por escena; las escenas duran lo que su frase. Lleva etiqueta de IA.
Uso: python3 tools/render_trial_reels.py [id ...]   (ids: t1a t1b t2a t2b t3a t3b; sin ids, todos)
Salida: trial/r1-<id>.mp4 (720x1280, < 3 MB)."""
import asyncio, json, os, re, subprocess, sys
import numpy as np
from playwright.async_api import async_playwright

sys.path.insert(0, os.path.dirname(__file__))
from render_12_reel import write_wav, tone, whoosh, SR, FPS, F  # noqa: E402

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
OUTDIR = os.path.join(ROOT, "trial")
WORK = "/tmp/trial"
DUR = {"hook": 2.9, "line": 2.7, "turn": 3.0, "list": 4.8, "cta": 3.4}

TOPICS = {
    "t1": {  # trabajar menos
        "sym": "clock", "kw": "TIEMPO",
        "hooks": {"a": "¿Podrías irte<br>una semana<br>sin que tu<br>negocio <span class=b>se pare</span>?",
                  "b": "Si todo<br>pasa por ti,<br>tu negocio<br>no es libre.<br><span class=b>Tú tampoco.</span>"},
        "body": [
            ("line", "Presupuestos.<br>Quejas. Pagos.<br><span class=dim>Todo te espera a ti.</span>"),
            ("turn", ["No es falta de tiempo.", "Es falta<br>de orden."]),
            ("list", ["Prueba esto:", ["Apunta lo que haces en una semana", "Marca lo que solo puedes hacer tú",
                                       "Lo demás: un proceso o una persona"]]),
            ("cta", "¿Qué sería lo primero<br>que <span class=b>soltarías</span>?"),
        ]},
    "t2": {  # ganar más
        "sym": "euro", "kw": "MARGEN",
        "hooks": {"a": "¿Vendes más<br>que hace un año<br>y te queda<br><span class=b>lo mismo</span>?",
                  "b": "Vender más<br>no es lo mismo<br>que <span class=b>ganar más</span>."},
        "body": [
            ("line", "Más ventas traen<br>más horas,<br>más costes<br><span class=dim>y más descuentos.</span>"),
            ("turn", ["No importa cuánto entra.", "Importa cuánto<br>se queda."]),
            ("list", ["Mira tres cosas:", ["Qué servicio te deja más margen", "Qué cliente te cuesta más de lo que paga",
                                          "Qué descuento das sin pensarlo"]]),
            ("cta", "¿Sabes cuál de tus servicios<br>te deja <span class=b>más</span>?"),
        ]},
    "t3": {  # ordenar
        "sym": "three", "kw": "ORDEN",
        "hooks": {"a": "¿Cuántas cosas<br>tienes apuntadas<br>para <span class=b>“esta<br>semana”</span>?",
                  "b": "Hacerlo todo<br>es la forma<br>más rápida<br>de <span class=b>no avanzar</span>."},
        "body": [
            ("line", "Cuando todo<br>es urgente,<br><span class=dim>nada lo es.</span>"),
            ("turn", ["No necesitas hacer más.", "Necesitas<br>elegir."]),
            ("list", ["Entender · Priorizar · Decidir", ["Escribe todo lo pendiente",
                                                       "Quédate con 3: lo que da dinero o libera tiempo",
                                                       "Lo demás, a la semana que viene"]]),
            ("cta", "¿Cuál es tu prioridad<br><span class=b>número 1</span> esta semana?"),
        ]},
}

HTML = r"""<html><head><style>
@font-face{font-family:M;src:url(file://%(F)sMontserrat-Medium.ttf);font-weight:500}
@font-face{font-family:M;src:url(file://%(F)sMontserrat-Bold.ttf);font-weight:700}
@font-face{font-family:M;src:url(file://%(F)sMontserrat-ExtraBold.ttf);font-weight:800}
body{margin:0;background:#000}
#v{position:relative;overflow:hidden;width:1080px;height:1920px;font-family:M;color:#fff}
.bg{position:absolute;inset:0}.it{position:absolute}.b{color:#1F4BFF}.dim{color:#9AA0AE}
#blue .b{color:#0A0A0A}
</style></head><body><div id="v">
<div class="bg" style="background:radial-gradient(900px 900px at 85%% 88%%,#1F4BFF5a,transparent 70%%),radial-gradient(700px 600px at 0%% 0%%,#1F4BFF22,transparent 70%%),#070708"></div>
<div class="bg" id="blue" style="background:radial-gradient(900px 900px at 20%% 10%%,#4d72ff,transparent 70%%),#1F4BFF;opacity:0"></div>
<div class="bg" style="background-image:linear-gradient(#ffffff10 2px,transparent 2px),linear-gradient(90deg,#ffffff10 2px,transparent 2px);background-size:90px 90px;-webkit-mask-image:linear-gradient(#000,transparent 75%%)"></div>
<div id="sym" class="bg"></div>
<div id="cam" class="bg"></div>
<svg class="bg" width="1080" height="1920" style="mix-blend-mode:overlay;opacity:.4"><filter id="n"><feTurbulence type="fractalNoise" baseFrequency="0.85" numOctaves="3" stitchTiles="stitch"/><feColorMatrix type="saturate" values="0"/></filter><rect width="100%%" height="100%%" filter="url(#n)"/></svg>
<div class="bg" id="prog" style="height:12px;bottom:auto;background:#1F4BFF;width:0"></div>
<div class="it" style="left:0;right:0;bottom:130px;text-align:center;font-size:32px;font-weight:700;opacity:.85">@alejandro.segura.asesor</div>
<div class="bg" id="flash" style="background:#fff;opacity:0"></div>
</div>
<script>
const SC=%(SC)s, S=%(S)s, P=%(P)s, TOTAL=%(TOTAL)s, SYM="%(SYM)s", KW="%(KW)s";
const cl=x=>Math.max(0,Math.min(1,x)), oc=p=>1-Math.pow(1-p,3), ob=p=>{const c1=1.9,c3=c1+1;return 1+c3*Math.pow(p-1,3)+c1*Math.pow(p-1,2)};
function symbol(t){
 const st='fill="none" stroke="#1F4BFF" stroke-width="10" opacity=".35"';
 if(SYM=='clock'){const a=t*40;return `<svg width="1080" height="1920" style="position:absolute;left:0;top:0"><circle cx="760" cy="1450" r="300" ${st}/><g transform="rotate(${a} 760 1450)"><path d="M760 1450 L760 1230" stroke="#1F4BFF" stroke-width="12" opacity=".45" stroke-linecap="round"/></g><g transform="rotate(${a/12} 760 1450)"><path d="M760 1450 L900 1450" stroke="#1F4BFF" stroke-width="12" opacity=".45" stroke-linecap="round"/></g></svg>`}
 if(SYM=='euro')return `<div style="position:absolute;right:-40px;bottom:180px;font-size:900px;font-weight:800;line-height:1;color:transparent;-webkit-text-stroke:8px #1F4BFF;opacity:.32;transform:translateY(${-t*6}px)">€</div>`;
 return `<div style="position:absolute;right:20px;bottom:160px;font-size:1000px;font-weight:800;line-height:1;color:transparent;-webkit-text-stroke:8px #1F4BFF;opacity:.32;transform:translateY(${-t*6}px)">3</div>`;
}
function render(t){
 let s=0;while(s+1<S.length&&t>=S[s+1])s++;
 const [type,data]=SC[s],lt=t-S[s],Ld=(s+1<S.length?S[s+1]:TOTAL)-S[s];
 let h='',sh=0,blue=false;
 const it=(html,x,y,an,dl,extra='')=>{const p=cl((lt-dl)/.38);let tr='',op=1;
  if(an=='pop'){const q=ob(p);tr=`translateY(${(1-q)*60}px) scale(${.7+.3*q})`;op=cl(p*3)}
  else if(an=='slam'){const q=ob(p);tr=`scale(${1+1.1*(1-q)})`;op=cl(p*4)}
  else if(an=='slide'){const q=oc(p);tr=`translateX(${(1-q)*900}px)`;op=cl(p*2)}
  h+=`<div class="it" style="left:${x}px;top:${y}px;transform:${tr};opacity:${op};transform-origin:left center;${extra}">${html}</div>`};
 const kick=(dl,a=18)=>{const k=lt-dl-.1;if(k>0&&k<.25)sh=Math.max(sh,(1-k/.25)*a)};
 if(type=='hook'){it(`<div style="white-space:nowrap;font-size:92px;font-weight:800;line-height:1.04;letter-spacing:-.03em">${data}</div>`,80,520,'slam',0);kick(0,24)}
 if(type=='line'){it(`<div style="white-space:nowrap;font-size:84px;font-weight:800;line-height:1.08;letter-spacing:-.02em">${data}</div>`,80,600,'pop',0);kick(.05,10)}
 if(type=='turn'){const tb=P[s][0];blue=lt>tb;
  it(`<div style="font-size:64px;font-weight:700;color:${blue?'#0A0A0A':'#B8BCC8'}">${data[0]}</div>`,80,520,'pop',0);
  if(blue){it(`<div style="font-size:168px;font-weight:800;line-height:1;letter-spacing:-.04em">${data[1]}</div>`,80,720,'slam',tb);kick(tb,26)}}
 if(type=='list'){it(`<div style="font-size:60px;font-weight:800;color:#1F4BFF">${data[0]}</div>`,80,420,'pop',0);
  data[1].forEach((x,i)=>{const dl=P[s][i];
   it(`<div style="width:900px;display:flex;gap:34px;align-items:flex-start;background:#ffffff0d;border-left:12px solid #1F4BFF;border-radius:18px;padding:34px 36px"><div style="flex:none;font-size:74px;font-weight:800;line-height:1;color:#1F4BFF">${i+1}</div><div style="font-size:58px;font-weight:800;line-height:1.12">${x}</div></div>`,80,600+i*300,'slide',dl);kick(dl+.1,8)})}
 if(type=='cta'){it(`<div style="width:920px;font-size:92px;font-weight:800;line-height:1.05;letter-spacing:-.02em">${data}</div>`,80,560,'slam',0);kick(0);
  it(`<div style="font-size:54px;font-weight:700;color:#C9CDD8">Escríbeme <span style="color:#fff;font-weight:800;border-bottom:6px solid #1F4BFF">${KW}</span> por privado</div>`,80,1080,'pop',.9);
  const a=oc(cl((lt-1.3)/.4)),bob=Math.sin(lt*6)*10;
  h+=`<svg width="120" height="220" style="position:absolute;left:80px;top:${1180+bob}px;opacity:${a}"><path d="M60 10 L60 190 M20 150 L60 195 L100 150" fill="none" stroke="#1F4BFF" stroke-width="8" stroke-linecap="round" stroke-linejoin="round"/></svg>`}
 document.getElementById('cam').innerHTML=h;
 document.getElementById('cam').style.transform=`scale(${1+.03*cl(lt/Ld)}) translate(${sh*Math.sin(t*90)}px,${sh*Math.cos(t*70)}px)`;
 document.getElementById('sym').innerHTML=blue?'':symbol(t);
 document.getElementById('blue').style.opacity=blue?1:0;
 document.getElementById('flash').style.opacity=Math.max(0,.45-lt*4.5);
 const pr=document.getElementById('prog');pr.style.width=(t/TOTAL*1080)+'px';pr.style.background=blue?'#0A0A0A':'#1F4BFF';
}
</script></body></html>"""


VOZ = os.environ.get("VOZ_DIR", "/tmp/voz")  # clips de Rafa N: <id>.mp3 (gancho) y tN-line/turn/list/cta.mp3
# pausas (por orden) tras las que entra cada punto de la lista, según las tomas del 20-nov
LIST_GAPS = {"t1": [0, 2, 4], "t2": [0, 1, 2], "t3": [2, 4, 7]}
PAD = {"hook": .45, "line": .4, "turn": .5, "list": .5, "cta": 1.6}


def clip_info(path):
    """Duración útil del clip (sin silencio final) y finales de pausas internas."""
    from render_12_reel import load_pcm
    x = load_pcm(path)
    err = subprocess.run(["ffmpeg", "-i", path, "-af", "silencedetect=noise=-35dB:d=0.12", "-f", "null", "-"],
                         capture_output=True, text=True).stderr
    ss = [float(v) for v in re.findall(r"silence_start: ([\d.]+)", err)]
    se = [float(v) for v in re.findall(r"silence_end: ([\d.]+)", err)]
    dur = len(x) / SR
    end = ss[-1] if len(ss) > len(se) else dur
    gaps = [(b - a, b) for a, b in zip(ss, se) if a > .05 and b < end - .05]
    return x, end, gaps


def scenes(rid):
    tp = TOPICS[rid[:2]]
    sc = [("hook", tp["hooks"][rid[2]])] + tp["body"]
    files = [f"{VOZ}/{rid}.mp3"] + [f"{VOZ}/{rid[:2]}-{t}.mp3" for t, _ in tp["body"]]
    S, P, clips, t = [], [], [], 0.0
    for (typ, _), f in zip(sc, files):
        x, end, gaps = clip_info(f)
        S.append(round(t, 3))
        lead = .12
        if typ == "turn":
            g = max(gaps) if gaps else (0, end / 2)
            P.append([lead + g[1] - .05])
        elif typ == "list":
            idx = LIST_GAPS.get(rid[:2])
            g = [gaps[i] for i in idx] if idx and len(gaps) > max(idx) else \
                sorted(sorted(gaps, reverse=True)[:3], key=lambda z: z[1])
            while len(g) < 3:
                g.append((0, end * (len(g) + 1) / 4))
            P.append([lead + z[1] - .1 for z in g])
        else:
            P.append([])
        clips.append((t + lead, x[:int(end * SR)]))
        t += lead + end + PAD[typ]
    return sc, S, t, tp, P, clips


def sfx(sc, S, total, seed, P):
    out = np.zeros(int(SR * (total + 1)))

    def put(sig, at):
        i = int(at * SR)
        out[i:i + len(sig)] += sig[:max(0, len(out) - i)]
    thud, pop = tone(120, 45, .35, .9, 10), tone(900, 400, .12, .3, 30)
    for (typ, _), st, pp in zip(sc, S, P):
        if st > 0:
            put(whoosh(), st - .15)
        if typ in ("hook", "cta"):
            put(thud, st + .05)
        elif typ == "line":
            put(pop, st + .05)
        elif typ == "turn":
            put(thud, st + pp[0])
        elif typ == "list":
            for v in pp:
                put(pop, st + v)
    # base rítmica suave
    beat, t = 60 / 108, 0.0
    kick = tone(90, 40, .25, .5, 14)
    hat = np.random.default_rng(seed).normal(0, .05, int(SR * .04)) * np.exp(-np.linspace(0, 6, int(SR * .04)))
    bass = [55, 55, 65.4, 49]
    k = 0
    while t < total - .4:
        put(kick, t)
        put(hat, t + beat / 2)
        if k % 2 == 0:
            put(tone(bass[(k // 2) % 4], bass[(k // 2) % 4], beat * 1.8, .18, 1.2), t)
        t += beat
        k += 1
    fade = np.ones(len(out))
    n = int(SR * .8)
    e = int(SR * total)
    fade[e - n:e] = np.linspace(1, 0, n)
    fade[e:] = 0
    return out * fade


async def render_one(b, rid):
    sc, S, total, tp, P, clips = scenes(rid)
    wd = f"{WORK}/{rid}"
    os.makedirs(wd, exist_ok=True)
    for f in os.listdir(wd):
        os.remove(os.path.join(wd, f))
    html = HTML % {"F": F, "SC": json.dumps(sc, ensure_ascii=False), "S": json.dumps(S), "P": json.dumps(P), "TOTAL": total,
                   "SYM": tp["sym"], "KW": tp["kw"]}
    open(f"{wd}/reel.html", "w").write(html)
    pg = await b.new_page(viewport={"width": 1080, "height": 1920})
    await pg.goto(f"file://{wd}/reel.html")
    await pg.evaluate("document.fonts.ready")
    for i in range(int(total * FPS)):
        await pg.evaluate(f"render({i / FPS})")
        await pg.screenshot(path=f"{wd}/f{i:05d}.jpg", type="jpeg", quality=90)
    await pg.close()
    write_wav(f"{wd}/sfx.wav", sfx(sc, S, total, hash(rid) % 1000, P))
    voz = np.zeros(int(SR * (total + 1)), np.float32)
    for at, x in clips:
        i = int(at * SR)
        voz[i:i + len(x)] += x[:len(voz) - i]
    write_wav(f"{wd}/voz.wav", voz)
    out = os.path.join(OUTDIR, f"r1-{rid}.mp4")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-framerate", str(FPS), "-i", f"{wd}/f%05d.jpg",
                    "-i", f"{wd}/sfx.wav", "-i", f"{wd}/voz.wav", "-filter_complex",
                    "[1:a]volume=0.22[s];[2:a]volume=1.4[v];[s][v]amix=inputs=2:duration=first:normalize=0,"
                    "loudnorm=I=-14:TP=-1.5[a]", "-map", "0:v", "-map", "[a]",
                    "-vf", "scale=720:1280:flags=lanczos", "-c:v", "libx264",
                    "-preset", "slow", "-crf", "26", "-maxrate", "1200k", "-bufsize", "2400k",
                    "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "96k", "-ar", "44100",
                    "-shortest", "-movflags", "+faststart", out], check=True)
    print(rid, round(total, 1), "s", os.path.getsize(out) // 1024, "KB")


async def main(ids):
    os.makedirs(OUTDIR, exist_ok=True)
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path="/opt/pw-browsers/chromium", args=["--allow-file-access-from-files"])
        for rid in ids:
            await render_one(b, rid)
        await b.close()


if __name__ == "__main__":
    asyncio.run(main(sys.argv[1:] or [f"t{i}{h}" for i in (1, 2, 3) for h in "ab"]))
