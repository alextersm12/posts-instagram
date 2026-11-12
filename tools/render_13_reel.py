"""Reel 13-esclavo (1080x1920, 30 fps). Lunes 16-nov-2026.
Uso: python3 tools/render_13_reel.py [voz.mp3]
  - Con voz: corta por silencios, junta las frases hasta tener 7 (una por escena) uniendo las pausas más cortas,
    las recompone con pausas breves y sincroniza cada escena.
  - Sin voz: duraciones estimadas.
Salida: 13-esclavo/reel-esclavo.mp4
Reutiliza utilidades de tools/render_12_reel.py."""
import asyncio, json, os, re, subprocess, sys
import numpy as np
from playwright.async_api import async_playwright

sys.path.insert(0, os.path.dirname(__file__))
from render_12_reel import load_pcm, write_wav, tone, whoosh, SR, FPS, F  # noqa: E402

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
WORK = "/tmp/reel13"
EST = [2.2, 2.0, 2.6, 1.8, 2.2, 2.8, 2.2]
LEAD, GAP, TAIL = 0.35, 0.28, 1.6
N = len(EST)


def prepare(voice):
    if not voice:
        S, t = [], LEAD
        for d in EST:
            S.append(t)
            t += d
        return S, t + TAIL, None, [[0, d * .33, d * .66] for d in EST]
    x = load_pcm(voice)
    out = subprocess.run(["ffmpeg", "-i", voice, "-af", "silencedetect=noise=-38dB:d=0.18", "-f", "null", "-"],
                         capture_output=True, text=True).stderr
    ss = [float(v) for v in re.findall(r"silence_start: ([\d.]+)", out)]
    se = [float(v) for v in re.findall(r"silence_end: ([\d.]+)", out)]
    chunks, cur = [], 0.0
    for a, b in zip(ss, se):
        if a - cur > 0.05:
            chunks.append([cur, a])
        cur = b
    if len(x) / SR - cur > 0.1:
        chunks.append([cur, len(x) / SR])
    if len(chunks) == 12:  # toma de ElevenLabs con una pausa entre cada frase corta
        groups = [[0], [1], [2, 3, 4], [5, 6], [7, 8], [9], [10, 11]]
    else:
        groups = None
    # si no, unir por las pausas más cortas hasta quedarnos con N frases
    while groups is None and len(chunks) > N:
        gaps = [chunks[i + 1][0] - chunks[i][1] for i in range(len(chunks) - 1)]
        i = int(np.argmin(gaps))
        chunks[i] = [chunks[i][0], chunks[i + 1][1]]
        del chunks[i + 1]
    if groups is None:
        if len(chunks) < N:
            sys.exit(f"Solo {len(chunks)} frases detectadas; se esperaban {N}")
        groups = [[i] for i in range(N)]
    pieces, S, Dsub, t = [np.zeros(int(LEAD * SR), np.float32)], [], [], LEAD
    for g in groups:
        S.append(t - 0.05)
        Dsub.append([])
        for j, k in enumerate(g):
            a, b = chunks[k]
            a, b = max(0, a - 0.04), b + 0.06
            Dsub[-1].append(t - S[-1])
            seg = x[int(a * SR):int(b * SR)]
            gap = GAP if j == len(g) - 1 else 0.12
            pieces += [seg, np.zeros(int(gap * SR), np.float32)]
            t += len(seg) / SR + gap
    os.makedirs(WORK, exist_ok=True)
    path = f"{WORK}/voz.wav"
    write_wav(path, np.concatenate(pieces))
    return S, t + TAIL, path, Dsub


HTML = r"""<html><head><style>
@font-face{font-family:M;src:url(file://%(F)sMontserrat-Medium.ttf);font-weight:500}
@font-face{font-family:M;src:url(file://%(F)sMontserrat-Bold.ttf);font-weight:700}
@font-face{font-family:M;src:url(file://%(F)sMontserrat-ExtraBold.ttf);font-weight:800}
body{margin:0;background:#000}
#v{position:relative;overflow:hidden;width:1080px;height:1920px;font-family:M;color:#fff}
.bg{position:absolute;inset:0}.it{position:absolute}.k{color:#0A0A0A}.b{color:#1F4BFF}
.pill{position:absolute;width:330px;height:120px;margin:-60px 0 0 -165px;display:flex;align-items:center;justify-content:center;text-align:center;border-radius:999px;font-weight:800;line-height:1.05;box-shadow:0 18px 40px #0A0A0A40}
</style></head><body><div id="v">
<div class="bg" style="background:linear-gradient(160deg,#3A62FF 0%%,#1F4BFF 45%%,#1430B8 100%%)"></div>
<div class="bg" id="black" style="background:radial-gradient(900px 900px at 50%% 45%%,#1F4BFF55,transparent 70%%),#070708;opacity:0"></div>
<div id="cam" class="bg"></div>
<svg class="bg" width="1080" height="1920" style="mix-blend-mode:overlay;opacity:.4"><filter id="n"><feTurbulence type="fractalNoise" baseFrequency="0.85" numOctaves="3" stitchTiles="stitch"/><feColorMatrix type="saturate" values="0"/></filter><rect width="100%%" height="100%%" filter="url(#n)"/></svg>
<div class="bg" id="prog" style="height:12px;bottom:auto;background:#0A0A0A;width:0"></div>
<div class="it" style="left:0;right:0;bottom:120px;text-align:center;font-size:32px;font-weight:700;opacity:.85">@alejandro.segura.asesor</div>
<div class="bg" id="flash" style="background:#fff;opacity:0"></div>
</div>
<script>
const S=%(S)s, TOTAL=%(TOTAL)s, DS=%(DS)s;
const cl=x=>Math.max(0,Math.min(1,x)), oc=p=>1-Math.pow(1-p,3), ob=p=>{const c1=1.9,c3=c1+1;return 1+c3*Math.pow(p-1,3)+c1*Math.pow(p-1,2)};
const link=(cx,cy,rot,w,h,sw,col,op,dash='')=>`<rect x="${cx-w/2}" y="${cy-h/2}" width="${w}" height="${h}" rx="${h/2}" fill="none" stroke="${col}" stroke-width="${sw}" opacity="${op}" ${dash} transform="rotate(${rot} ${cx} ${cy})"/>`;
function chain(dy){let s='';for(let i=0;i<6;i++){const x=40+i*215,y=1520-i*80+dy;s+=link(x,y,-20,300,i%%2?120:150,i%%2?20:24,i%%2?'#fff':'#0A0A0A',.92)}return `<svg width="1080" height="1920" style="position:absolute;left:0;top:0">${s}</svg>`}
function loop(rot,hi,cx=540,cy=1050,r=290){
 let s='';for(let i=0;i<3;i++){const a0=(-90+i*120+24)*Math.PI/180,a1=(-90+(i+1)*120-24)*Math.PI/180;
  s+=`<path d="M${cx+r*Math.cos(a0)} ${cy+r*Math.sin(a0)} A${r} ${r} 0 0 1 ${cx+r*Math.cos(a1)} ${cy+r*Math.sin(a1)}" fill="none" stroke="#0A0A0A" stroke-width="14" stroke-linecap="round" marker-end="url(#ar)"/>`}
 let svg=`<svg width="1080" height="1920" style="position:absolute;left:0;top:0"><defs><marker id="ar" markerWidth="6" markerHeight="6" refX="3" refY="3" orient="auto"><path d="M0 0 L6 3 L0 6z" fill="#0A0A0A"/></marker></defs><g transform="rotate(${rot} ${cx} ${cy})">${s}</g></svg>`;
 const L=[['Abres',-90],['Apagas<br>fuegos',30],['Cierras',150]];
 L.forEach(([t,a],i)=>{const q=hi[i];const x=cx+r*Math.cos(a*Math.PI/180),y=cy+r*Math.sin(a*Math.PI/180);
  svg+=`<div class="pill" style="left:${x}px;top:${y}px;transform:scale(${.4+.6*ob(cl(q*1.5))+.12*Math.max(0,1-Math.abs(q-.5)*4)});opacity:${cl(q*3)};background:#fff;color:#1F4BFF;font-size:${t.includes('<br>')?38:46}px">${t}</div>`});
 return svg}
const T=(h,x,y,an,d)=>({h,x,y,an,d});
let cur=-1;
function render(t){
 let s=0;while(s+1<S.length&&t>=S[s+1])s++;
 const st=S[s],en=s+1<S.length?S[s+1]:TOTAL,lt=t-st,D=en-st;
 const cam=document.getElementById('cam');let h='',sh=0,z=1+.04*cl(lt/D),black=false;
 const it=(html,x,y,an,d,extra='')=>{const p=cl((lt-d)/.38);let tr='',op=1;
  if(an=='pop'){const q=ob(p);tr=`translateY(${(1-q)*60}px) scale(${.6+.4*q})`;op=cl(p*3)}
  else if(an=='slam'){const q=ob(p);tr=`scale(${1+1.2*(1-q)})`;op=cl(p*4)}
  h+=`<div class="it" style="left:${x}px;top:${y}px;transform:${tr};opacity:${op};transform-origin:left center;${extra}">${html}</div>`};
 const kick=(d)=>{const k=lt-d-.1;if(k>0&&k<.25)sh=Math.max(sh,(1-k/.25)*20)};
 if(s==0){it(`<div style="font-size:120px;font-weight:800;line-height:1.02;letter-spacing:-.03em">Montaste<br>un negocio<br>para ser <span class="k">libre</span>.</div>`,90,620,'pop',0)}
 if(s==1){const q=ob(cl(lt/.5));h+=chain((1-q)*-900);kick(.4);
  it(`<div style="font-size:66px;font-weight:700;line-height:1.15;opacity:.6">Montaste un negocio<br>para ser libre.</div>`,90,420,'none',0);
  it(`<div style="font-size:140px;font-weight:800;line-height:.98;letter-spacing:-.035em">¿Y ahora<br>eres su<br><span class="k">esclavo</span>?</div>`,90,640,'slam',.15)}
 if(s==2||s==3){const base=s==2?lt:S[3]-S[2]+lt;const sp=s==2?60:60+260*lt;const rot=(s==2?base*50:(S[3]-S[2])*50+lt*sp)%%360;
  const p=s==2?[0,1,2].map(i=>cl((lt-(DS[2][i]??D*i*.33)+.05)/.3)):[1,1,1];
  h+=loop(rot,p);
  it(`<div style="font-size:96px;font-weight:800;line-height:1.02;letter-spacing:-.02em">${s==2?'Todos los días,<br>lo mismo.':'Y mañana…<br><span class="k">igual</span>.'}</div>`,90,330,s==2?'pop':'slam',0);
  if(s==3)kick(.2)}
 if(s==4){black=true;const sb=DS[4][1]??D*.45;kick(0);kick(sb);
  it(`<div style="font-size:150px;font-weight:800;line-height:1;letter-spacing:-.03em">Ya no<br>decides.</div>`,90,520,'slam',0);
  it(`<div style="font-size:170px;font-weight:800;line-height:1;letter-spacing:-.03em" class="b">Sobrevives.</div>`,90,900,'slam',sb)}
 if(s==5){const q=oc(cl(lt/1.2));const sc=1.6-1.15*q;
  h+=`<div style="position:absolute;inset:0;transform:scale(${sc}) translateY(${q*260}px);transform-origin:540px 1050px;opacity:${.35+.65*q}">${loop(lt*120,[1,1,1])}</div>`;
  it(`<div style="font-size:92px;font-weight:800;line-height:1.05;letter-spacing:-.02em">Salir del bucle<br>empieza por<br>mirarlo <span class="k">desde fuera</span>.</div>`,90,300,'pop',.2)}
 if(s==6){const q=oc(cl((lt-.15)/.5));kick(.15);
  const a=`<svg width="1080" height="1920" style="position:absolute;left:0;top:0">${link(540-q*260,1250+q*120,-25-q*30,360,180,24,'#0A0A0A',.9,'stroke-dasharray="560 140"')}${link(560+q*260,1250-q*80,-25+q*40,300,140,20,'#fff',.6)}</svg>`;
  h+=a;if(lt>.15&&lt<.45)h+=`<div style="position:absolute;left:470px;top:1180px;width:140px;height:140px;border-radius:50%%;background:radial-gradient(#fff,#fff0 70%%);opacity:${1-(lt-.15)/.3}"></div>`;
  it(`<div style="background:#fff;color:#1F4BFF;padding:26px 44px;font-size:96px;font-weight:800;transform:rotate(-3deg);box-shadow:0 18px 40px #0A0A0A40">¿Te ayudo<br>a salir?</div>`,90,420,'slam',0);
  it(`<div style="font-size:64px;font-weight:800">Escríbeme por privado <span class="k">→</span></div>`,90,1620,'pop',.7)}
 cam.innerHTML=h;
 cam.style.transform=`scale(${z}) translate(${sh*Math.sin(t*90)}px,${sh*Math.cos(t*70)}px)`;
 document.getElementById('black').style.opacity=black?1:0;
 document.getElementById('flash').style.opacity=Math.max(0,.5-lt*4.5);
 const pr=document.getElementById('prog');pr.style.width=(t/TOTAL*1080)+'px';pr.style.background=black?'#1F4BFF':'#0A0A0A';
}
</script></body></html>"""


def sfx(S, total):
    out = np.zeros(int(SR * (total + 1)))

    def put(sig, at):
        i = int(at * SR)
        out[i:i + len(sig)] += sig[:max(0, len(out) - i)]
    pop, thud = tone(900, 400, .12, .35, 30), tone(120, 45, .35, .9, 10)
    chainhit = tone(1600, 900, .25, .35, 12)
    chainhit[:int(SR * .2)] += tone(2400, 1500, .2, .2, 15)
    for i, st in enumerate(S):
        put(whoosh(), max(0, st - .15))
        D = (S[i + 1] if i + 1 < len(S) else total) - st
        if i == 0:
            put(pop, st)
        elif i == 1:
            put(thud, st + .45)
            put(chainhit, st + .45)
        elif i == 2:
            for k in range(3):
                put(pop, st + k * D * .33)
        elif i == 3:
            put(thud, st + .25)
        elif i == 4:
            put(thud, st + .05)
            put(thud, st + D * .45)
        elif i == 6:
            put(tone(2000, 600, .3, .45, 10), st + .15)
            put(thud, st + .2)
            put(pop, st + .75)
    beat, t = 60 / 112, S[0]
    kick = tone(90, 40, .25, .55, 14)
    hat = np.random.default_rng(2).normal(0, .06, int(SR * .04)) * np.exp(-np.linspace(0, 6, int(SR * .04)))
    while t < total - .3:
        put(kick, t)
        put(hat, t + beat / 2)
        t += beat
    return out


async def frames(S, total, DS):
    os.makedirs(WORK, exist_ok=True)
    for f in os.listdir(WORK):
        if f.endswith(".jpg"):
            os.remove(os.path.join(WORK, f))
    open(f"{WORK}/reel.html", "w").write(HTML % {"F": F, "S": json.dumps(S), "TOTAL": total, "DS": json.dumps(DS)})
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path="/usr/bin/google-chrome", args=["--allow-file-access-from-files"])
        pg = await b.new_page(viewport={"width": 1080, "height": 1920})
        await pg.goto(f"file://{WORK}/reel.html")
        await pg.evaluate("document.fonts.ready")
        for i in range(int(total * FPS)):
            await pg.evaluate(f"render({i / FPS})")
            await pg.screenshot(path=f"{WORK}/f{i:05d}.jpg", type="jpeg", quality=88)
        await b.close()


def main():
    S, total, voice, DS = prepare(sys.argv[1] if len(sys.argv) > 1 else None)
    print("escenas:", [round(x, 2) for x in S], "total:", round(total, 2))
    asyncio.run(frames(S, total, DS))
    write_wav(f"{WORK}/sfx.wav", sfx(S, total))
    out = os.path.join(ROOT, "13-esclavo", "reel-esclavo.mp4")
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-framerate", str(FPS), "-i", f"{WORK}/f%05d.jpg", "-i", f"{WORK}/sfx.wav"]
    if voice:
        cmd += ["-i", voice, "-filter_complex", "[1:a]volume=0.4[s];[2:a]volume=1.5[v];[s][v]amix=inputs=2:duration=first:normalize=0[a]",
                "-map", "0:v", "-map", "[a]"]
    else:
        cmd += ["-map", "0:v", "-map", "1:a"]
    cmd += ["-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "20", "-c:a", "aac", "-b:a", "192k", "-shortest",
            "-movflags", "+faststart", out]
    subprocess.run(cmd, check=True)
    print("ok", out)


if __name__ == "__main__":
    main()
