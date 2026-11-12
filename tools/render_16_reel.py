"""Reel 16-clientes (1080x1920, 30 fps, negro). Jueves 19-nov-2026.
Uso: python3 tools/render_16_reel.py voz.mp3
Salida: 16-clientes/reel-clientes.mp4 y 16-clientes/portada-reel-clientes.jpg
Reutiliza utilidades de tools/render_12_reel.py."""
import asyncio, json, os, re, subprocess, sys
import numpy as np
from playwright.async_api import async_playwright

sys.path.insert(0, os.path.dirname(__file__))
from render_12_reel import load_pcm, write_wav, tone, whoosh, SR, FPS, F  # noqa: E402

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
OUTDIR = os.path.join(ROOT, "16-clientes")
WORK = "/tmp/reel16"
LEAD, GAP_IN, GAP_SCENE, TAIL = 0.35, 0.14, 0.3, 1.6
# toma de ElevenLabs (Rafa N) con 10 trozos de voz
GROUPS = [[0, 1], [2], [3], [4], [5], [6, 7], [8], [9]]


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
<div class="bg" style="background:radial-gradient(900px 900px at 85%% 90%%,#1F4BFF66,transparent 70%%),radial-gradient(700px 600px at 0%% 0%%,#1F4BFF22,transparent 70%%),#070708"></div>
<div class="bg" id="black" style="background:#1F4BFF;opacity:0"></div>
<div class="bg" style="background-image:linear-gradient(#ffffff12 2px,transparent 2px),linear-gradient(90deg,#ffffff12 2px,transparent 2px);background-size:90px 90px;opacity:.6"></div>
<div id="cam" class="bg"></div>
<svg class="bg" width="1080" height="1920" style="mix-blend-mode:overlay;opacity:.4"><filter id="n"><feTurbulence type="fractalNoise" baseFrequency="0.85" numOctaves="3" stitchTiles="stitch"/><feColorMatrix type="saturate" values="0"/></filter><rect width="100%%" height="100%%" filter="url(#n)"/></svg>
"""

HTML = HEAD + r"""<div class="bg" id="prog" style="height:12px;bottom:auto;background:#1F4BFF;width:0"></div>
<div class="it" style="left:0;right:0;bottom:120px;text-align:center;font-size:32px;font-weight:700;opacity:.85">@alejandro.segura.asesor</div>
<div class="bg" id="flash" style="background:#fff;opacity:0"></div>
</div>
<script>
const S=%(S)s, TOTAL=%(TOTAL)s, D=%(D)s;
const cl=x=>Math.max(0,Math.min(1,x)), oc=p=>1-Math.pow(1-p,3), ob=p=>{const c1=1.9,c3=c1+1;return 1+c3*Math.pow(p-1,3)+c1*Math.pow(p-1,2)};
const GOOD=new Set([3,10,16]);
function person(x,y,sz,col,op,sc=1){return `<svg width="${sz}" height="${sz}" viewBox="0 0 100 100" style="position:absolute;left:${x}px;top:${y}px;opacity:${op};transform:scale(${sc})"><circle cx="50" cy="34" r="18" fill="${col}"/><path d="M16 92c0-22 15-36 34-36s34 14 34 36z" fill="${col}"/></svg>`}
function card(title,icon,x,y,rot,crossed=0,extra=''){return `<div style="position:absolute;left:${x}px;top:${y}px;width:820px;padding:34px 40px;border-radius:28px;background:#fff;color:#0A0A0A;transform:rotate(${rot}deg);box-shadow:0 30px 60px #000a;display:flex;align-items:center;gap:30px;${extra}">
 <div style="flex:none;width:110px;height:110px;border-radius:24px;background:#1F4BFF;display:flex;align-items:center;justify-content:center;font-size:64px">${icon}</div>
 <div><div style="font-size:26px;font-weight:800;letter-spacing:.14em;color:#1F4BFF">CLIENTE</div><div style="font-size:52px;font-weight:800;line-height:1.1">${title}</div></div>
 ${crossed>0?`<svg width="820" height="200" style="position:absolute;left:0;top:50%%;margin-top:-100px"><path d="M30 170 L${30+760*crossed} ${170-140*crossed}" stroke="#FF3B3B" stroke-width="16" stroke-linecap="round"/></svg>`:''}</div>`}
function render(t){
 let s=0;while(s+1<S.length&&t>=S[s+1])s++;
 const st=S[s],en=s+1<S.length?S[s+1]:TOTAL,lt=t-st,Ld=en-st,d=D[s];
 let h='',sh=0,blue=false;
 const it=(html,x,y,an,dl,extra='')=>{const p=cl((lt-dl)/.38);let tr='',op=1;
  if(an=='pop'){const q=ob(p);tr=`translateY(${(1-q)*60}px) scale(${.6+.4*q})`;op=cl(p*3)}
  else if(an=='slam'){const q=ob(p);tr=`scale(${1+1.2*(1-q)})`;op=cl(p*4)}
  h+=`<div class="it" style="left:${x}px;top:${y}px;transform:${tr};opacity:${op};transform-origin:left center;${extra}">${html}</div>`};
 const kick=(dl,a=20)=>{const k=lt-dl-.1;if(k>0&&k<.25)sh=Math.max(sh,(1-k/.25)*a)};
 if(s==0){const sel=lt>d[1];
  for(let i=0;i<20;i++){const x=110+(i%%5)*180,y=880+Math.floor(i/5)*190,q=ob(cl((lt-i*.04)/.3));const good=GOOD.has(i);
   const op=sel?(good?1:Math.max(.12,1-(lt-d[1])*3)):1;h+=person(x,y,150,sel&&good?'#1F4BFF':'#fff',op*q,sel&&good?1+.15*ob(cl((lt-d[1])/.4)):1)}
  it(`<div style="font-size:104px;font-weight:800;line-height:1;letter-spacing:-.03em">No necesitas<br>más clientes.</div>`,90,330,'pop',0);
  if(sel){it(`<div style="font-size:94px;font-weight:800;line-height:1;letter-spacing:-.03em">Necesitas <span class="b">mejores</span>.</div>`,90,560,'slam',d[1]);kick(d[1])}}
 const intro=(i)=>{it(`<div style="font-size:60px;font-weight:700;color:#B8BCC8">Hay clientes que…</div>`,90,330,'none',0)};
 if(s>=1&&s<=3){intro();
  const cards=[['Pide descuento<br>en cada factura','🏷️'],['Paga tarde','⏰'],['Te llama<br>un domingo','📞']];
  for(let i=0;i<s;i++){const appear=i==s-1?ob(cl(lt/.4)):1;const x=130,y=520+i*300;
   h+=`<div style="position:absolute;inset:0;transform:translateX(${(1-appear)*1100}px)">${card(cards[i][0],cards[i][1],x-40+i*20,y,i%%2?2:-2)}</div>`}
  kick(.25,14)}
 if(s==4){intro();const cards=[['Pide descuento<br>en cada factura','🏷️'],['Paga tarde','⏰'],['Te llama<br>un domingo','📞']];
  cards.forEach((c,i)=>{const cr=oc(cl((lt-.9-i*.35)/.3));h+=card(c[0],c[1],90+i*20,520+i*300,i%%2?2:-2,cr)});
  it(`<div style="background:#FF3B3B;padding:20px 30px;font-size:46px;font-weight:800;white-space:nowrap;transform:rotate(-3deg)">…y son los que menos te dejan.</div>`,90,1460,'slam',.5);kick(.55);
  for(let i=0;i<3;i++)kick(.9+i*.35,12)}
 if(s==5){blue=true;it(`<div style="font-size:84px;font-weight:800;line-height:1.05">Los que más crecen<br>no tienen más clientes:</div>`,90,520,'pop',0);
  it(`<div style="font-size:170px;font-weight:800;line-height:1;letter-spacing:-.03em;color:#0A0A0A">eligen<br>mejor.</div>`,90,860,'slam',d[1]);kick(d[1],24)}
 if(s==6){const q=oc(cl(lt/.6));
  h+=`<svg width="1080" height="1920" style="position:absolute;left:0;top:0">${[260,190,120,50].map((r,i)=>`<circle cx="540" cy="1080" r="${r*q}" fill="none" stroke="${i%%2?'#fff':'#1F4BFF'}" stroke-width="${i==3?0:14}" ${i==3?'fill="#1F4BFF"':''}/>`).join('')}</svg>`;
  const a=oc(cl((lt-.6)/.35));h+=`<svg width="1080" height="1920" style="position:absolute;left:0;top:0"><g transform="translate(${1100-560*a} ${560+520*a}) rotate(-35)"><path d="M0 0 L-260 0" stroke="#fff" stroke-width="14" stroke-linecap="round"/><path d="M0 0 L-40 -24 M0 0 L-40 24" stroke="#fff" stroke-width="14" stroke-linecap="round"/></g></svg>`;
  if(lt>.95&&lt<1.2)sh=16;
  for(let i=0;i<10;i++){const ang=i/10*Math.PI*2,fly=oc(cl((lt-1.4-i*.05)/.6)),r=420+fly*700;if(![1,4,7].includes(i))h+=person(540+Math.cos(ang)*r-60,1080+Math.sin(ang)*r-60,120,'#fff',1-fly);else h+=person(540+Math.cos(ang)*360-60,1080+Math.sin(ang)*360-60,120,'#1F4BFF',cl(lt*3))}
  it(`<div style="font-size:72px;font-weight:800;line-height:1.08">Una meta clara.<br>Y apartan lo que<br><span class="b">no les acerca</span>.</div>`,90,300,'pop',0)}
 if(s==7){it(`<div style="width:880px;font-size:88px;font-weight:800;line-height:1.04;letter-spacing:-.02em">¿Qué cliente te está <span class="b">restando</span> más de lo que te da?</div>`,90,420,'slam',0);kick(0);
  it(`<div style="background:#1F4BFF;padding:24px 44px;border-radius:999px;font-size:60px;font-weight:800">Escríbeme por privado ✈</div>`,90,1200,'pop',1.2)}
 const cam=document.getElementById('cam');cam.innerHTML=h;
 cam.style.transform=`scale(${1+.035*cl(lt/Ld)}) translate(${sh*Math.sin(t*90)}px,${sh*Math.cos(t*70)}px)`;
 document.getElementById('black').style.opacity=blue?1:0;
 document.getElementById('flash').style.opacity=Math.max(0,.5-lt*4.5);
 const pr=document.getElementById('prog');pr.style.width=(t/TOTAL*1080)+'px';pr.style.background=blue?'#0A0A0A':'#1F4BFF';
}
</script></body></html>"""

COVER = HEAD + r"""
<div class="it" style="left:90px;right:90px;top:470px">
 <div style="font-size:124px;font-weight:800;line-height:1;letter-spacing:-.03em;white-space:nowrap">No necesitas<br>más clientes.</div>
 <div style="margin-top:50px;display:inline-block;background:#1F4BFF;padding:20px 36px;font-size:80px;font-weight:800;white-space:nowrap;transform:rotate(-2deg)">Necesitas mejores.</div>
</div>
<div class="it" style="left:110px;top:1240px;display:flex;gap:30px">
 <svg width="140" height="140" viewBox="0 0 100 100" opacity=".25"><circle cx="50" cy="34" r="18" fill="#fff"/><path d="M16 92c0-22 15-36 34-36s34 14 34 36z" fill="#fff"/></svg>
 <svg width="140" height="140" viewBox="0 0 100 100"><circle cx="50" cy="34" r="18" fill="#1F4BFF"/><path d="M16 92c0-22 15-36 34-36s34 14 34 36z" fill="#1F4BFF"/></svg>
 <svg width="140" height="140" viewBox="0 0 100 100" opacity=".25"><circle cx="50" cy="34" r="18" fill="#fff"/><path d="M16 92c0-22 15-36 34-36s34 14 34 36z" fill="#fff"/></svg>
 <svg width="140" height="140" viewBox="0 0 100 100"><circle cx="50" cy="34" r="18" fill="#1F4BFF"/><path d="M16 92c0-22 15-36 34-36s34 14 34 36z" fill="#1F4BFF"/></svg>
 <svg width="140" height="140" viewBox="0 0 100 100" opacity=".25"><circle cx="50" cy="34" r="18" fill="#fff"/><path d="M16 92c0-22 15-36 34-36s34 14 34 36z" fill="#fff"/></svg>
</div></div></body></html>"""


def sfx(S, D, total):
    out = np.zeros(int(SR * (total + 1)))

    def put(sig, at):
        i = int(at * SR)
        out[i:i + len(sig)] += sig[:max(0, len(out) - i)]
    pop, thud = tone(900, 400, .12, .35, 30), tone(120, 45, .35, .9, 10)
    scratch = tone(1400, 300, .18, .35, 14)
    for i, st in enumerate(S):
        put(whoosh(), max(0, st - .15))
        d = D[i]
        if i == 0:
            for k in range(0, 20, 3):
                put(pop, st + k * .04)
            put(thud, st + d[1])
        elif i in (1, 2, 3):
            put(thud, st + .25)
        elif i == 4:
            put(thud, st + .55)
            for k in range(3):
                put(scratch, st + .9 + k * .35)
        elif i == 5:
            put(thud, st + d[1])
        elif i == 6:
            put(tone(500, 900, .2, .4, 8), st + .1)
            put(thud, st + .95)
            put(whoosh(.5, .45), st + 1.4)
        elif i == 7:
            put(thud, st + .05)
            put(tone(600, 1200, .25, .4, 6), st + 1.2)
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
        await pg.screenshot(path=os.path.join(OUTDIR, "portada-reel-clientes.jpg"), type="jpeg", quality=92)
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
    out = os.path.join(OUTDIR, "reel-clientes.mp4")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-framerate", str(FPS), "-i", f"{WORK}/f%05d.jpg",
                    "-i", f"{WORK}/sfx.wav", "-i", voice, "-filter_complex",
                    "[1:a]volume=0.4[s];[2:a]volume=1.5[v];[s][v]amix=inputs=2:duration=first:normalize=0[a]",
                    "-map", "0:v", "-map", "[a]", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "20",
                    "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", out], check=True)
    print("ok", out)


if __name__ == "__main__":
    main()
