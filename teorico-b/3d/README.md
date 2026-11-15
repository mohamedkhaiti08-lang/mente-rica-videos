# Vídeos 3D — Teórico B en 30s

Formato ÚNICO de la cuenta desde el 12 nov 2026 (decisión de Mohamed): coche 3D, cámara detrás, ciudad low-poly, 3 situaciones con SÍ/NO.
**15 nov 2026 (Mohamed): los vídeos se parecían demasiado. Mismo estilo 3D, pero ahora hay 4 TEMAS y hay que rotarlos** (ver "Temas"). Referencia de estilo: vídeos de cruces 3D tipo TeoTest
(cámara detrás del coche, ciudad low-poly, "CRUCE 1 DE 3 · ¿Tienes prioridad?", SÍ/NO, cuenta atrás y respuesta). Nunca copiar su marca.

## Cómo se genera un vídeo
```
pip install --break-system-packages bpy kokoro-onnx soundfile pillow numpy
# modelo de voz (una vez): kokoro-v1.0.onnx y voices-v1.0.bin en KOKORO_DIR
KOKORO_DIR=/ruta python3 generar.py --seed 20261113 --out salida            # elige 3 cruces al azar (al menos un SÍ y un NO)
KOKORO_DIR=/ruta python3 generar.py --seed N --out salida --evitar der_sin,peaton   # evita tipos usados hace poco
KOKORO_DIR=/ruta python3 generar.py --seed N --out salida --tipos stop_mio,peaton,sem_verde --hora tarde
KOKORO_DIR=/ruta python3 generar.py --seed N --out salida --prueba 6 15 26  # solo fotogramas sueltos para revisar
```
Salida: salida/video.mp4 (1080x1920, ~33-36 s), guion.json (tipos, textos, tiempos), spec.json, frames/.
Tiempo: ~1 min de preparación + ~2 s por fotograma con 2 procesos → unos 20 min por vídeo.

## Temas (--tema)
| Tema | Pregunta | Cabecera | Situaciones |
|---|---|---|---|
| prioridad | ¿Tienes prioridad? / ¿Puedes pasar? | CRUCE 1 DE 3 | las 10 de cruces (der_sin, stop_otro, peaton, ambulancia...) |
| giro | ¿Puedes girar a la derecha/izquierda? ¿Puedes cambiar de sentido? | CALLE 1 DE 3 | r302_der, r302_izq, r303_izq, r303_der, r303_sentido, r101_der (señal + intermitente del coche) |
| aparcar | ¿Puedes aparcar aquí? / ¿Puedes parar un momento? | SITIO 1 DE 3 | amarilla_cont(_parar), amarilla_disc(_parar), zigzag, vado, paso_cebra, r308(_parar), plaza_blanca (hueco libre con chincheta naranja que se pone verde/roja) |
| mezcla | "Examen relámpago" | PRUEBA 1 DE 3 | uno de cada tema en orden aleatorio |

Rotación obligatoria: nunca el mismo tema dos vídeos seguidos; en 2 días (4 vídeos) salen los 4 temas. Sin --tema el generador elige al azar.
Ejemplo: `KOKORO_DIR=~/kok python3 generar.py --seed N --out salida --tema giro --evitar r303_der`

## Variedad
- 10 situaciones (tipos.py): der_sin, izq_sin, stop_otro, ceda_otro, stop_mio, ceda_mio, peaton, sem_rojo, sem_verde, ambulancia,
  con lado izquierda/derecha cuando aplica y varias frases de voz por tipo.
- La semilla cambia la ciudad: 5 paletas de fachadas, alturas, balcones, toldos, árboles, farolas, coches aparcados, peatones,
  color de los coches, hora (día o atardecer).
- Combinaciones: miles. No repetir el mismo trío de tipos en 7 días.

## Añadir situaciones nuevas
1. Comprobar la norma en fuente oficial y apuntarla en FUENTES.md.
2. Añadir el tipo en tipos.py (respuesta, lados, frases, rótulo) y su escenografía en generar.py (actores/señales) y, si hace falta, el modelo en motor3d.py.
3. Probar con --prueba y revisar los fotogramas antes de publicar nada.

## Si el render se corta (límite de tiempo de un comando o reinicio)
generar.py reanuda: solo renderiza los fotogramas que faltan. Alternativa por tandas de menos de 10 minutos:
```
KOKORO_DIR=~/kok python3 teorico-b/3d/generar.py --seed N --out /tmp/vN --prueba 0.5   # crea spec.json y guion.json
python3 teorico-b/3d/tanda.py /tmp/vN 230      # repetir hasta que diga "quedan 0" (unos 9 min por tanda)
KOKORO_DIR=~/kok python3 teorico-b/3d/generar.py --seed N --out /tmp/vN               # monta el vídeo final (~5-8 min)
```
