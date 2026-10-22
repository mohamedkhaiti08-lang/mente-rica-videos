# Voz del narrador (Alex, español de España) con Kokoro, sin servicios de pago.
# Uso: python3 voz.py guion.json salida.wav tiempos.json
#   guion.json: {"lines": ["Frase 1.", "¿Pregunta?", ...], "speed": 1.0, "pause": 0.35}
#   Genera salida.wav (voz completa) y tiempos.json con [[inicio, fin], ...] de cada frase,
#   para que cada escena empiece justo cuando empieza su frase.
# Preparación (una vez por sesión):
#   pip install --break-system-packages kokoro-onnx soundfile
#   curl -sSL -o kokoro-v1.0.onnx https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/kokoro-v1.0.onnx
#   curl -sSL -o voices-v1.0.bin  https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/voices-v1.0.bin
import json, os, sys
import numpy as np
import soundfile as sf
from kokoro_onnx import Kokoro

VOICE = "em_alex"
cfg = json.load(open(sys.argv[1]))
model_dir = os.environ.get("KOKORO_DIR", ".")
k = Kokoro(os.path.join(model_dir, "kokoro-v1.0.onnx"), os.path.join(model_dir, "voices-v1.0.bin"))
speed, pause = cfg.get("speed", 1.0), cfg.get("pause", 0.35)

parts, times, t, sr = [np.zeros(int(24000 * 0.15), dtype=np.float32)], [], 0.15, 24000
for line in cfg["lines"]:
    a, sr = k.create(line, voice=VOICE, speed=speed, lang="es")
    # recorta silencios al principio y al final para que los tiempos sean exactos
    idx = np.where(np.abs(a) > 0.01)[0]
    if len(idx): a = a[max(0, idx[0] - 240): idx[-1] + 480]
    times.append([round(t, 2), round(t + len(a) / sr, 2)])
    parts += [a.astype(np.float32), np.zeros(int(sr * pause), dtype=np.float32)]
    t += len(a) / sr + pause

sf.write(sys.argv[2], np.concatenate(parts), sr)
json.dump(times, open(sys.argv[3], "w"))
print(f"{len(times)} frases, {t:.2f} s")
