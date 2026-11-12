# Voz (em_alex, Kokoro, gratis) colocada en los segundos exactos de la animación + campanitas suaves.
# Uso: KOKORO_DIR=carpeta python3 audio.py guion.json salida.wav
# guion.json: {"lines": [...], "starts": [seg de inicio de cada frase], "duration": seg, "sfx": [{"t","f","dur","v"}]}
# Imprime [[inicio, fin], ...] de cada frase: comprueba que ninguna frase pisa a la siguiente.
import json, os, sys
import numpy as np, soundfile as sf
from kokoro_onnx import Kokoro
g = json.load(open(sys.argv[1])); d = os.environ.get("KOKORO_DIR", ".")
k = Kokoro(os.path.join(d, "kokoro-v1.0.onnx"), os.path.join(d, "voices-v1.0.bin"))
sr = 24000; out = np.zeros(int(sr * g["duration"]), np.float32); tl = []
for ln, st in zip(g["lines"], g["starts"]):
    a, sr = k.create(ln, voice="em_alex", speed=g.get("speed", 1.0), lang="es")
    idx = np.where(np.abs(a) > 0.01)[0]; a = a[max(0, idx[0] - 240): idx[-1] + 480]
    i = int(st * sr); out[i:i + len(a)] += a[:len(out) - i]; tl.append([st, round(st + len(a) / sr, 2)])
for s in g.get("sfx", []):
    n = int(s["dur"] * sr); x = np.arange(n) / sr; f = s["f"]; v = s["v"]
    w = v * np.sin(2 * np.pi * f * x) * np.exp(-x * 3.5) + v * 0.4 * np.sin(4 * np.pi * f * x) * np.exp(-x * 5)
    i = int(s["t"] * sr); out[i:i + n] += w[:len(out) - i]
sf.write(sys.argv[2], np.clip(out, -1, 1), sr); print(tl)
for (a, b), (c, _) in zip(tl, tl[1:]):
    if b > c - 0.25: print(f"AVISO: la frase que acaba en {b} pisa a la siguiente ({c})")
