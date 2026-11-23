"""Reels v4 (23-nov-2026): más visuales y con más ritmo, a petición de Alejandro.
- Cada frase tiene su escena ilustrada y animada (SVG/CSS), con paleta propia: nada de fondo fijo azul.
- Cortes con flash + sacudida, zoom de golpe, partículas, subtítulos grandes tipo caption (2-3 palabras, pop),
  palabra clave resaltada en color, barra de progreso, grano fino.
- Sonido: whoosh/golpe en cada corte, "pop" por trozo de subtítulo, ritmo suave de fondo, subida antes del cierre.
Uso: python3 tools/render_reel_v4.py spec.json salida.mp4 [--voz DIR] [--preview]
  spec.json: {"keyword": "PLAN", "clips": [{"id": "hook", "text": "...", "scene": "silla", "est": 3.9}, ...]}
  Con --voz DIR usa DIR/<id>.mp3 (Rafa N) y sincroniza los subtítulos con la voz; sin voz usa "est" (segundos).
"""
import asyncio, json, os, re, subprocess, sys, wave
import numpy as np
from playwright.async_api import async_playwright

FPS, SR = 30, 44100
F = os.environ.get("FONTS", "/tmp/mont/fonts/ttf/")
TEMPO, GAP, CTA_HOLD = 1.08, .14, 1.6


def load_pcm(path):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-ac", "1", "-ar", str(SR), "-f", "s16le", "-"],
                         capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.int16).astype(np.float32) / 32768


def write_wav(path, x):
    x = np.clip(x / max(1.0, np.abs(x).max() / .9), -1, 1)
    with wave.open(path, "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((x * 32767).astype(np.int16).tobytes())


def tone(f0, f1, dur, vol=.5, decay=8):
    t = np.arange(int(SR * dur)) / SR
    f = np.linspace(f0, f1, len(t))
    return vol * np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-decay * t)


def noise(dur, vol, shape="swell", seed=1):
    n = int(SR * dur); x = np.random.default_rng(seed).normal(0, 1, n)
    x = np.convolve(x, np.ones(6) / 6, "same")
    env = np.sin(np.linspace(0, np.pi, n)) ** 2 if shape == "swell" else np.linspace(0, 1, n) ** 2
    return vol * x * env


def speech_segments(path):
    x = load_pcm(path)
    err = subprocess.run(["ffmpeg", "-i", path, "-af", "silencedetect=noise=-35dB:d=0.12", "-f", "null", "-"],
                         capture_output=True, text=True).stderr
    ss = [float(v) for v in re.findall(r"silence_start: ([\d.]+)", err)]
    se = [float(v) for v in re.findall(r"silence_end: ([\d.]+)", err)]
    dur, segs, cur = len(x) / SR, [], 0.0
    for a, b in zip(ss, se):
        if a - cur > .05: segs.append((cur, a))
        cur = b
    if dur - cur > .05: segs.append((cur, dur))
    return x, segs or [(0, dur)]


def words_in(text, a, b):
    ws = text.replace("«", "").replace("»", "").split()
    L = [len(re.sub(r"\W", "", w)) + 2 for w in ws]
    out, t = [], a
    for w, l in zip(ws, L):
        out.append((t, w)); t += (b - a) * l / sum(L)
    return out


def build(spec, voz):
    t, words, audio, scenes, vend = .2, [], [], [], None
    for c in spec["clips"]:
        if c["scene"] == "dm":
            vend = t
        if voz:
            fast = f"/tmp/v4work/{c['id']}.wav"
            subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", f"{voz}/{c['id']}.mp3", "-af",
                            f"atempo={TEMPO}", "-ac", "1", "-ar", str(SR), fast], check=True)
            x, segs = speech_segments(fast)
            a0, b1 = segs[0][0], segs[-1][1]
            audio.append((t - a0, x)); d = b1 - a0
        else:
            d = c["est"]
        sc = c["scene"] if isinstance(c["scene"], list) else [c["scene"]]
        for j, name in enumerate(sc):
            scenes.append({"t": round(t + d * j / len(sc) - (.12 if j else 0), 3), "scene": name, "id": c["id"]})
        for wt, w in words_in(c["text"], t, t + d):
            words.append({"t": round(wt, 3), "w": w, "id": c["id"]})
        t += d + GAP
    end = t
    if vend is None:
        vend = end
    # trozos de 1-3 palabras
    HI = set(spec.get("hi", []))
    chunks, cur = [], []
    for i, w in enumerate(words):
        cur.append(w)
        last = i == len(words) - 1 or words[i + 1]["id"] != w["id"]
        if last or len(cur) == 3 or re.search(r"[.,:?…]$", w["w"]) or sum(len(x["w"]) for x in cur) > 14:
            chunks.append({"t": cur[0]["t"], "ws": [{"w": x["w"], "t": x["t"],
                           "hi": re.sub(r"[^\wáéíóúñ]", "", x["w"].lower()) in HI} for x in cur]})
            cur = []
    return chunks, scenes, audio, vend, max(end + .9, vend + CTA_HOLD)


HTML = open(os.path.join(os.path.dirname(__file__), "reel_v4_template.html")).read()


def sfx(chunks, scenes, total, vend):
    out = np.zeros(int(SR * (total + 1)))

    def put(sig, at):
        i = int(max(0, at) * SR); out[i:i + len(sig)] += sig[:max(0, len(out) - i)]
    for k, s in enumerate(scenes):
        put(noise(.4, .28, seed=k), s["t"] - .32)
        put(tone(120, 40, .5, .75, 6), s["t"])
    for c in chunks:
        put(tone(900, 500, .05, .12, 40), c["t"])
    put(noise(1.6, .25, "rise", 9), vend - 1.6)
    put(tone(1320, 1320, .6, .25, 5) + tone(1760, 1760, .6, .15, 5), vend + .05)
    beat, t, k = 60 / 112, 0.0, 0
    while t < total - .2:
        if k % 2 == 0: put(tone(65, 40, .28, .45, 12), t)
        put(noise(.04, .05, seed=k + 50), t + beat / 2)
        t += beat; k += 1
    e, n = int(SR * total), int(SR * .6)
    out[e - n:e] *= np.linspace(1, 0, n); out[e:] = 0
    return out


async def render(spec_path, out, voz, preview):
    spec = json.load(open(spec_path))
    os.makedirs("/tmp/v4work/frames", exist_ok=True)
    for f in os.listdir("/tmp/v4work/frames"): os.remove(f"/tmp/v4work/frames/{f}")
    chunks, scenes, audio, vend, total = build(spec, voz)
    html = (HTML.replace("__F__", F).replace("__C__", json.dumps(chunks, ensure_ascii=False))
            .replace("__S__", json.dumps(scenes)).replace("__VEND__", str(vend)).replace("__TOTAL__", str(total))
            .replace("__KW__", spec["keyword"]))
    open("/tmp/v4work/reel.html", "w").write(html)
    step = 3 if preview else 1
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path=os.environ.get("CHROME", "/opt/pw-browsers/chromium"), args=["--allow-file-access-from-files"])
        pg = await b.new_page(viewport={"width": 1080, "height": 1920})
        await pg.goto("file:///tmp/v4work/reel.html"); await pg.evaluate("document.fonts.ready")
        n = int(total * FPS)
        for i in range(0, n, step):
            await pg.evaluate(f"render({i / FPS})")
            await pg.screenshot(path=f"/tmp/v4work/frames/f{i // step:05d}.jpg", type="jpeg", quality=95)
        await b.close()
    write_wav("/tmp/v4work/sfx.wav", sfx(chunks, scenes, total, vend))
    voz_track = np.zeros(int(SR * (total + 1)), np.float32)
    for at, x in audio:
        i = max(0, int(at * SR)); voz_track[i:i + len(x)] += x[:len(voz_track) - i]
    write_wav("/tmp/v4work/voz.wav", voz_track)
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-framerate", str(FPS // step), "-i", "/tmp/v4work/frames/f%05d.jpg",
                    "-i", "/tmp/v4work/sfx.wav", "-i", "/tmp/v4work/voz.wav", "-filter_complex",
                    "[1:a]volume=0.32[s];[2:a]highpass=f=70,acompressor=threshold=-20dB:ratio=3:attack=5:release=80,volume=1.4[v];"
                    "[s][v]amix=inputs=2:duration=first:normalize=0,loudnorm=I=-14:TP=-1.5[a]",
                    "-map", "0:v", "-map", "[a]", "-r", str(FPS), "-c:v", "libx264", "-preset", "medium", "-crf", "18",
                    "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-t", f"{total:.2f}",
                    "-movflags", "+faststart", out], check=True)
    print(out, round(total, 1), "s")


if __name__ == "__main__":
    a = sys.argv[1:]
    voz = a[a.index("--voz") + 1] if "--voz" in a else None
    asyncio.run(render(a[0], a[1], voz, "--preview" in a))
