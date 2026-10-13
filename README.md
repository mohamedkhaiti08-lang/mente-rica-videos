# Mente Rica – vídeos diarios

Cuenta de TikTok / YouTube Shorts sobre **psicología del dinero para jóvenes**, presentada por **Moni** (una moneda dorada animada).

- `videos/` – un MP4 vertical (1080x1920, ~40 s, sin audio) por día: `AAAA-MM-DD-tema.mp4`.
- `plantilla/render.py` – plantilla del estilo visual (fondo verde oscuro, tipografía Inter Display, Moni, animaciones). Se renderiza con Python (Pillow + NumPy) y ffmpeg.
- `temas.md` – lista de temas ya publicados, para no repetir.

Cada día a las 13:15 (hora de Madrid) se genera un vídeo nuevo y se envía el enlace por Gmail. El audio se añade a mano al publicar.

## Cómo hacer un vídeo nuevo con la plantilla

1. Copia `plantilla/render.py` a una carpeta de trabajo.
2. Conserva todo lo de arriba (fondo, partículas, `text_img`, `pop_words`, tarjetas, Moni, `draw_ui`, `flash`, `render_frame`).
3. Reescribe solo las funciones `sceneN`, la lista `SCENES`, las ventanas `TALK` (cuando Moni habla) y `DUR`.
4. Prueba fotogramas: `python3 render.py stills 3 10 17 24 31 38` y revisa que nada se corte ni se solape.
5. Renderiza: `python3 render.py video salida.mp4`, y comprime con `ffmpeg -i salida.mp4 -c:v libx264 -crf 23 -preset slow -pix_fmt yuv420p -c:a copy -movflags +faststart videos/AAAA-MM-DD-tema.mp4`.
