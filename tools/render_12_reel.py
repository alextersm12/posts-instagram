"""Reel 12-financiacion (1080x1920, 30 fps): animación dinámica sincronizada con la voz en off.
Uso: python3 tools/render_12_reel.py [voz.mp3]
  - Con voz: corta las frases por silencios, las junta con pausas cortas y ajusta cada escena y tarjeta a su frase.
  - Sin voz: usa duraciones estimadas.
Salida: 12-financiacion/reel.mp4
Requiere Montserrat en /tmp/mont/fonts/ttf, ffmpeg y Playwright con Chrome."""
import asyncio, json, os, re, subprocess, sys, wave
import numpy as np
from playwright.async_api import async_playwright

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
WORK = "/tmp/reel12"
FPS = 30
SR = 44100
F = "/tmp/mont/fonts/ttf/"
EST = [2.0, 1.8, 2.4, 3.6, 2.4, 3.4, 3.4, 2.4, 3.0, 2.0]  # duraciones estimadas por frase
TAIL = 0.9  # pausa tras la última frase antes del cierre
END = 3.6  # duración de la escena final (llamada a la acción, sin voz)


GROUPS = [[0], [1], [2, 3], [4, 5], [6, 7], [8, 9, 10], [11, 12, 13], [14, 15], [16], [17]]  # frases de voz por escena
LEAD, GAP_IN, GAP_SCENE = 0.4, 0.18, 0.32


def load_pcm(path):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-ac", "1", "-ar", str(SR), "-f", "s16le", "-"],
                         capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.int16).astype(np.float32) / 32768


def prepare(voice):
    """Devuelve (inicios de escena, duración total, voz recompuesta o None, D).
    D[s] = segundos (desde el inicio de la escena s) en que empieza cada frase de esa escena.
    Con voz: se cortan las frases por silencios y se recomponen con pausas cortas (más ritmo)."""
    if not voice:
        st, t, D = [], LEAD, []
        for d in EST:
            st.append(t)
            D.append([0, d * .45, d * .7])
            t += d
        st.append(t + TAIL)
        D.append([0])
        return st, st[-1] + END, None, D
    x = load_pcm(voice)
    out = subprocess.run(["ffmpeg", "-i", voice, "-af", "silencedetect=noise=-35dB:d=0.28", "-f", "null", "-"],
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
    if len(chunks) != sum(len(g) for g in GROUPS):
        sys.exit(f"Se detectaron {len(chunks)} frases y se esperaban {sum(len(g) for g in GROUPS)}: revisa el audio o GROUPS")
    pieces, S, D, t = [np.zeros(int(LEAD * SR), np.float32)], [], [], LEAD
    for g in GROUPS:
        S.append(t - 0.06)
        D.append([])
        for j, k in enumerate(g):
            a, b = chunks[k]
            a, b = max(0, a - 0.04), b + 0.06
            D[-1].append(t - S[-1])
            seg = x[int(a * SR):int(b * SR)]
            pieces.append(seg)
            t += len(seg) / SR
            gap = GAP_IN if j < len(g) - 1 else GAP_SCENE
            pieces.append(np.zeros(int(gap * SR), np.float32))
            t += gap
    v = np.concatenate(pieces)
    path = f"{WORK}/voz.wav"
    os.makedirs(WORK, exist_ok=True)
    write_wav(path, v * 1.0)
    S.append(t + TAIL)
    D.append([0])
    return S, S[-1] + END, path, D


HTML = r"""<html><head><style>
@font-face{font-family:M;src:url(file://%(F)sMontserrat-Medium.ttf);font-weight:500}
@font-face{font-family:M;src:url(file://%(F)sMontserrat-Bold.ttf);font-weight:700}
@font-face{font-family:M;src:url(file://%(F)sMontserrat-ExtraBold.ttf);font-weight:800}
body{margin:0;background:#000}
#v{position:relative;overflow:hidden;width:1080px;height:1920px;font-family:M;color:#fff}
.bg{position:absolute;inset:0}
.it{position:absolute;will-change:transform,opacity}
.k{color:#0A0A0A}.b{color:#1F4BFF}
.chip{display:inline-block;background:#0A0A0A;color:#fff;padding:14px 26px;border-radius:999px;font-size:30px;font-weight:800;letter-spacing:.12em}
.card{display:flex;align-items:center;gap:26px;width:860px;padding:26px 30px;border-radius:24px;background:#ffffff26;border:2px solid #ffffff55;font-size:42px;font-weight:600;line-height:1.2}
.card i{flex:none;width:58px;height:58px;border-radius:50%%;background:#0A0A0A;display:flex;align-items:center;justify-content:center;font-style:normal;font-size:28px;font-weight:800}
</style></head><body><div id="v">
<div class="bg" id="blue" style="background:linear-gradient(160deg,#3A62FF 0%%,#1F4BFF 45%%,#1430B8 100%%)"></div>
<div class="bg" id="black" style="background:radial-gradient(900px 900px at 50%% 45%%,#1F4BFF55,transparent 70%%),#070708;opacity:0"></div>
<div class="bg" id="grid" style="background-image:linear-gradient(#ffffff14 2px,transparent 2px),linear-gradient(90deg,#ffffff14 2px,transparent 2px);background-size:90px 90px"></div>
<div id="cam" class="bg"></div>
<svg class="bg" width="1080" height="1920" style="mix-blend-mode:overlay;opacity:.4"><filter id="n"><feTurbulence type="fractalNoise" baseFrequency="0.85" numOctaves="3" stitchTiles="stitch"/><feColorMatrix type="saturate" values="0"/></filter><rect width="100%%" height="100%%" filter="url(#n)"/></svg>
<div class="bg" id="prog" style="top:0;height:12px;background:#0A0A0A;width:0"></div>
<div class="it" style="left:0;right:0;bottom:120px;text-align:center;font-size:32px;font-weight:700;opacity:.85">@alejandro.segura.asesor</div>
<div class="bg" id="flash" style="background:#fff;opacity:0"></div>
</div>
<script>
const S=%(S)s, TOTAL=%(TOTAL)s, ICONS=%(ICONS)s, D=%(D)s;
const cl=x=>Math.max(0,Math.min(1,x)), oc=p=>1-Math.pow(1-p,3);
const ob=p=>{const c1=1.9,c3=c1+1;return 1+c3*Math.pow(p-1,3)+c1*Math.pow(p-1,2)};
const el=(h,x,y,extra='')=>`<div class="it" data-a style="left:${x}px;top:${y}px;${extra}">${h}</div>`;
// escenas: lista de [html, x, y, anim, delay, extra]
const forma=(num,label,title,icon,items,dl,extra=[])=>[
 [`<div style="font-size:620px;font-weight:800;line-height:1;color:transparent;-webkit-text-stroke:5px #0A0A0A;opacity:.35;letter-spacing:-.05em">${num}</div>`,330,1050,'slideR',0],
 [`<span class="chip">${num} · ${label}</span>`,90,330,'pop',0],
 [ICONS[icon],820,250,'spin',.1],
 [`<div style="width:700px;font-size:96px;font-weight:800;line-height:1.02;letter-spacing:-.02em">${title}</div>`,90,450,'slam',.05],
 ...items.map((t,i)=>[`<div class="card"><i>${i+1}</i><span>${t}</span></div>`,90,800+i*165,'slideL',dl[i]]),...extra];
const SC=[
 [[`<div style="font-size:1300px;font-weight:800;line-height:1;color:#0A0A0A;opacity:.18">€</div>`,180,380,'zoom',0],
  [`<div style="font-size:150px;font-weight:800;line-height:1;letter-spacing:-.03em">El dinero</div>`,90,560,'pop',0],
  [`<div style="font-size:150px;font-weight:800;line-height:1;letter-spacing:-.03em">no es lo que</div>`,90,720,'pop',.35],
  [`<div style="font-size:150px;font-weight:800;line-height:1;letter-spacing:-.03em">te <span class="k">frena</span>.</div>`,90,880,'slam',.75]],
 [[`<div style="font-size:150px;font-weight:800;line-height:1;letter-spacing:-.03em;opacity:.25">El dinero no es lo que te frena.</div>`,90,420,'none',0,'width:900px'],
  [`<div style="background:#fff;color:#1F4BFF;padding:26px 40px;font-size:76px;font-weight:800;transform:rotate(-3deg)">Es no saber<br>a dónde vas.</div>`,110,900,'slam',0]],
 [[`<div id="cnt" style="font-size:760px;font-weight:800;line-height:1;color:#0A0A0A">4</div>`,330,330,'count',0],
  [`<div style="font-size:92px;font-weight:800;line-height:1.05;text-align:center;width:900px">formas de<br>financiar tu negocio</div>`,90,1180,'slideL',.3],
  [`<div style="background:#fff;color:#1F4BFF;padding:18px 34px;font-size:64px;font-weight:800;transform:rotate(-4deg)">Apunta ✍️</div>`,620,1460,'slam',(D[2][1]||1.8)]],
 forma('01','SIN PEDIR A NADIE','Empieza con lo que <span class="k">tienes</span>.','monedas',['Ahorra.','Empieza pequeño.','Cobra por adelantado.'],[D[3][1],D[3][1]+.55,D[3][1]+1.3]),
 forma('02','SOCIO O INVERSOR','Alguien que pone <span class="k">dinero</span>.','personas',['Un socio que entra.','Un inversor.','Business angels o crowdfunding.'],[D[4][0]+.7,D[4][0]+1.3,D[4][0]+1.8],
   [[`<div style="display:flex;gap:18px;font-size:40px;font-weight:800"><span style="background:#0A0A0A;padding:16px 28px;border-radius:999px">+ Más capital</span><span style="border:4px solid #0A0A0A;padding:12px 28px;border-radius:999px">− Compartes decisiones</span></div>`,90,1300,'pop',D[4][1]]]),
 forma('03','AYUDAS PÚBLICAS','Dinero que no se <span class="k">devuelve</span>.','documento',['Tarifa plana: 80 €/mes.','Cuota cero, si se convoca.','Capitalizar el paro.'],[D[5][1],D[5][2],D[5][2]+1.3]),
 forma('04','PRÉSTAMOS','Deuda, pero con <span class="k">ayuda</span>.','banco',['Microcréditos sin aval.','ENISA si eres joven (-40).'],[D[6][2],D[6][2]+1.4]),
 [[`<div style="font-size:170px;font-weight:800;line-height:1;letter-spacing:-.03em">Ninguna<br>sirve sin<br>un <span class="b">plan</span>.</div>`,90,620,'slam',0]],
 [[`<div style="font-size:84px;font-weight:800;line-height:1.08">Quien quiere llegar<br>a la <span class="b">Z</span> de golpe…</div>`,90,520,'pop',0],
  [`<svg width="1080" height="420" id="track"></svg>`,0,880,'none',0],
  [`<div style="font-size:84px;font-weight:800">…abandona en la <span class="b">C</span>.</div>`,90,1330,'slam',1.55]],
 [[`<div style="font-size:170px;font-weight:800;line-height:1;letter-spacing:-.03em">Empieza<br>por la <span class="k">A</span>.</div>`,90,420,'slam',0],
  [`<div id="steps"></div>`,0,0,'none',0]],
 [[`<div style="font-size:1400px;font-weight:800;line-height:1;color:transparent;-webkit-text-stroke:6px #1F4BFF;opacity:.45">A</div>`,120,380,'zoom',0],
  [`<div style="font-size:150px;font-weight:800;line-height:1;letter-spacing:-.03em">¿Cuál es<br>tu <span class="b">A</span>?</div>`,90,470,'slam',0],
  [`<div style="font-size:60px;font-weight:700;line-height:1.25">Escríbeme</div>`,90,900,'pop',.7],
  [`<div style="background:#1F4BFF;padding:22px 44px;border-radius:999px;font-size:110px;font-weight:800;letter-spacing:.04em;box-shadow:0 0 80px #1F4BFFaa">PLAN</div>`,90,1000,'slam',1.0],
  [`<div style="font-size:60px;font-weight:700;line-height:1.25">por privado y lo vemos.</div>`,90,1230,'pop',1.4],
  [`<svg width="150" height="150" viewBox="0 0 24 24"><path d="M22 3 2 10.5l7.5 3L13 21z M9.5 13.5 22 3" fill="none" stroke="#fff" stroke-width="1.6" stroke-linejoin="round"/></svg>`,840,1210,'spin',1.6]]];
const blackScenes=new Set([7,8,10]);
const shakeAt=[[0,.75],[1,0],[3,.05],[4,.05],[5,.05],[6,.05],[7,0],[8,1.55],[9,0],[10,0],[10,1.0]];
let cur=-1;
function trackSVG(p){ // p 0..1 progreso de la escena 8
 const xs=[150,390,630],L="ABC";let s='';
 const d=oc(cl(p/0.45));const x2=150+(630-150)*d;
 s+=`<path d="M150 210 L${x2} 210" stroke="#fff" stroke-width="12" stroke-linecap="round"/>`;
 xs.forEach((x,i)=>{const q=cl((p-i*.18)/.15);const r=56*ob(q);s+=`<circle cx="${x}" cy="210" r="${Math.max(0,r)}" fill="${i<2?'#1F4BFF':'#fff'}"/><text x="${x}" y="230" text-anchor="middle" font-family="M" font-weight="800" font-size="56" fill="${i<2?'#fff':'#1F4BFF'}" opacity="${q}">${L[i]}</text>`});
 const z=cl((p-.3)/.2);s+=`<path d="M690 210 L900 210" stroke="#fff" stroke-width="8" stroke-dasharray="4 28" stroke-linecap="round" opacity="${z*.6}"/><circle cx="960" cy="210" r="56" fill="none" stroke="#fff" stroke-width="6" stroke-dasharray="12 12" opacity="${z*.6}"/><text x="960" y="230" text-anchor="middle" font-family="M" font-weight="800" font-size="56" fill="#fff" opacity="${z*.6}">Z</text>`;
 const x=cl((p-.52)/.1);const sc=1+2*(1-ob(x));if(x>0)s+=`<g transform="translate(630 70) scale(${sc})" opacity="${x}"><path d="M-40 -40 L40 40 M40 -40 L-40 40" stroke="#FF3B3B" stroke-width="16" stroke-linecap="round"/></g>`;
 return s;}
function stepsHTML(p){let s='';for(let i=0;i<3;i++){const q=ob(cl((p-.15-i*.18)/.3));const h=(260+i*230)*q;
 s+=`<div style="position:absolute;left:${90+i*310}px;top:${1560-h}px;width:280px;height:${h}px;border-radius:20px 20px 0 0;${i==0?'background:#0A0A0A':'border:6px solid #0A0A0A;border-bottom:none;box-sizing:border-box'};overflow:hidden"><div style="position:absolute;left:30px;top:16px;font-size:${i==0?130:96}px;font-weight:800;${i==0?'color:#fff':'color:transparent;-webkit-text-stroke:3px #0A0A0A'}">${"ABC"[i]}</div></div>`}return s}
function render(t){
 let s=S.length-1;while(s>0&&t<S[s])s--; if(t<S[0])s=0;
 const st=S[s], en=s+1<S.length?S[s+1]:TOTAL, lt=t-st;
 const cam=document.getElementById('cam');
 if(s!==cur){cur=s;cam.innerHTML=SC[s].map(a=>el(a[0],a[1],a[2],a[5]||'')).join('');}
 const its=cam.querySelectorAll('[data-a]');
 SC[s].forEach((a,i)=>{const e=its[i],an=a[3],p=cl((lt-a[4])/0.38);let tr='',op=1;
  if(an=='pop'){const q=ob(p);tr=`translateY(${(1-q)*60}px) scale(${.6+.4*q})`;op=cl(p*3)}
  else if(an=='slam'){const q=ob(p);tr=`scale(${1+1.2*(1-q)})`;op=cl(p*4)}
  else if(an=='slideL'){const q=ob(p);tr=`translateX(${(1-q)*-1100}px)`}
  else if(an=='slideR'){const q=oc(p);tr=`translateX(${(1-q)*900}px)`}
  else if(an=='spin'){const q=ob(p);tr=`rotate(${(1-q)*-180}deg) scale(${q})`}
  else if(an=='zoom'){tr=`scale(${.7+.4*oc(cl(lt/2))})`}
  else if(an=='count'){const q=cl(lt/0.7);e.querySelector('#cnt').textContent=Math.max(1,Math.ceil(q*4));tr=`scale(${1+.15*Math.sin(q*Math.PI*4)*(1-q)})`}
  e.style.transform=tr;e.style.opacity=op;});
 if(s==8)document.getElementById('track').innerHTML=trackSVG(lt/Math.max(1.6,en-st));
 if(s==9)document.getElementById('steps').innerHTML=stepsHTML(lt/1.2);
 // cámara: empuje lento + sacudida
 let sh=0;shakeAt.forEach(([sc,d])=>{if(sc==s){const k=lt-d-.12;if(k>0&&k<.25)sh=Math.max(sh,(1-k/.25)*18)}});
 const z=1+.04*cl(lt/Math.max(.1,en-st));
 cam.style.transform=`scale(${z}) translate(${sh*Math.sin(t*90)}px,${sh*Math.cos(t*70)}px)`;
 document.getElementById('flash').style.opacity=Math.max(0,.55-lt*4.5);
 document.getElementById('black').style.opacity=blackScenes.has(s)?1:0;
 document.getElementById('grid').style.opacity=blackScenes.has(s)?.4:.25;
 document.getElementById('prog').style.width=(t/TOTAL*1080)+'px';
 document.getElementById('prog').style.background=blackScenes.has(s)?'#1F4BFF':'#0A0A0A';
}
</script></body></html>"""

SW = 'fill="none" stroke="#fff" stroke-width="9" stroke-linecap="round" stroke-linejoin="round"'
ICONS = {
    "monedas": f'<svg width="190" height="190" viewBox="0 0 200 200"><g {SW}><ellipse cx="80" cy="150" rx="55" ry="18"/><path d="M25 150v-24M135 150v-24"/><ellipse cx="80" cy="126" rx="55" ry="18"/><path d="M25 126v-24M135 126v-24"/><ellipse cx="80" cy="102" rx="55" ry="18" fill="#0A0A0A"/><circle cx="150" cy="58" r="34"/><text x="150" y="72" text-anchor="middle" font-family="M" font-weight="800" font-size="40" fill="#fff" stroke="none">€</text></g></svg>',
    "personas": f'<svg width="190" height="190" viewBox="0 0 200 200"><g {SW}><circle cx="70" cy="70" r="28"/><path d="M20 165c0-32 22-52 50-52s50 20 50 52"/><circle cx="135" cy="62" r="24" fill="#0A0A0A"/><path d="M108 108c9-6 17-8 27-8 26 0 45 19 45 50"/></g></svg>',
    "documento": f'<svg width="190" height="190" viewBox="0 0 200 200"><g {SW}><path d="M50 20h70l35 35v125H50z"/><path d="M120 20v35h35"/><path d="M75 95h55M75 120h55"/><circle cx="140" cy="155" r="30" fill="#0A0A0A"/><path d="M127 155l9 9 17-18"/></g></svg>',
    "banco": f'<svg width="190" height="190" viewBox="0 0 200 200"><g {SW}><path d="M20 70l80-45 80 45z"/><path d="M40 85v65M80 85v65M120 85v65M160 85v65"/><path d="M20 170h160"/></g></svg>',
}


# ---------- efectos de sonido sintetizados ----------


def tone(f0, f1, dur, vol=.5, decay=8):
    t = np.arange(int(SR * dur)) / SR
    f = np.linspace(f0, f1, len(t))
    return vol * np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-decay * t)


def whoosh(dur=.35, vol=.35):
    n = int(SR * dur)
    x = np.random.default_rng(1).normal(0, 1, n)
    env = np.sin(np.linspace(0, np.pi, n)) ** 2
    # filtro paso bajo móvil sencillo
    y, a = np.zeros(n), 0.0
    for i in range(n):
        k = .05 + .5 * (i / n)
        a += k * (x[i] - a)
        y[i] = a
    return vol * y / (np.abs(y).max() + 1e-9) * env


def sfx_track(S, total):
    out = np.zeros(int(SR * (total + 1)))

    def put(sig, at):
        i = int(at * SR)
        out[i:i + len(sig)] += sig[:max(0, len(out) - i)]
    pop, thud, tick = tone(900, 400, .12, .35, 30), tone(120, 45, .35, .9, 10), tone(1800, 1800, .03, .25, 80)
    for i, st in enumerate(S):
        put(whoosh(), max(0, st - .15))
        if i == 0:
            for d in (0, .35):
                put(pop, st + d)
            put(thud, st + .8)
        elif i == 1:
            put(thud, st + .05)
        elif i == 2:
            for k in range(4):
                put(tick, st + k * .175)
        elif 3 <= i <= 6:
            put(thud, st + .1)
            for k in range(3):
                put(pop, st + .4 + k * .28)
        elif i == 7:
            put(thud, st + .05)
        elif i == 8:
            put(tone(300, 80, .4, .8, 6), st + 1.55)
        elif i == 9:
            put(thud, st + .05)
            for k in range(3):
                put(pop, st + .2 + k * .18)
        elif i == 10:
            put(thud, st + .05)
            put(pop, st + .7)
            put(thud, st + 1.0)
            put(pop, st + 1.4)
            put(tone(600, 1200, .25, .4, 6), st + 1.6)
    # base rítmica suave a 110 bpm
    beat = 60 / 110
    kick, hat = tone(90, 40, .25, .55, 14), np.random.default_rng(2).normal(0, .06, int(SR * .04)) * np.exp(-np.linspace(0, 6, int(SR * .04)))
    t = S[0]
    while t < total - .3:
        put(kick, t)
        put(hat, t + beat / 2)
        t += beat
    return out


def write_wav(path, x):
    x = np.clip(x / max(1.0, np.abs(x).max() / .9), -1, 1)
    with wave.open(path, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes((x * 32767).astype(np.int16).tobytes())


async def frames(S, total, D):
    os.makedirs(WORK, exist_ok=True)
    for f in os.listdir(WORK):
        if f.endswith(".jpg"):
            os.remove(os.path.join(WORK, f))
    html = HTML % {"F": F, "S": json.dumps(S), "TOTAL": total, "ICONS": json.dumps(ICONS), "D": json.dumps(D)}
    open(f"{WORK}/reel.html", "w").write(html)
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path="/usr/bin/google-chrome", args=["--allow-file-access-from-files"])
        pg = await b.new_page(viewport={"width": 1080, "height": 1920})
        await pg.goto(f"file://{WORK}/reel.html")
        await pg.evaluate("document.fonts.ready")
        n = int(total * FPS)
        for i in range(n):
            await pg.evaluate(f"render({i / FPS})")
            await pg.screenshot(path=f"{WORK}/f{i:05d}.jpg", type="jpeg", quality=88)
        await b.close()


def main():
    voice_in = sys.argv[1] if len(sys.argv) > 1 else None
    S, total, voice, D = prepare(voice_in)
    print("escenas:", [round(x, 2) for x in S], "total:", round(total, 2))
    asyncio.run(frames(S, total, D))
    write_wav(f"{WORK}/sfx.wav", sfx_track(S, total))
    out = os.path.join(ROOT, "12-financiacion", "reel.mp4")
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-framerate", str(FPS), "-i", f"{WORK}/f%05d.jpg", "-i", f"{WORK}/sfx.wav"]
    if voice:
        cmd += ["-i", voice, "-filter_complex",
                "[1:a]volume=0.4[s];[2:a]volume=1.5[v];[s][v]amix=inputs=2:duration=first:normalize=0[a]",
                "-map", "0:v", "-map", "[a]"]
    else:
        cmd += ["-map", "0:v", "-map", "1:a"]
    cmd += ["-c:v", "libx264", "-pix_fmt", "yuv420p", "-preset", "medium", "-crf", "20", "-c:a", "aac", "-b:a", "192k",
            "-shortest", "-movflags", "+faststart", out]
    subprocess.run(cmd, check=True)
    print("ok", out)


if __name__ == "__main__":
    main()
