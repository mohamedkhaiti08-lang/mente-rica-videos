# Estilo "Noche" — estilo OFICIAL de la cuenta halal (@muslimtoons10) desde el 12 nov 2026

Mohamed lo eligió el 12 nov 2026 ("me encanta, quiero estos vídeos desde ahora en adelante").
Referencia: la cuenta "Baraka Digital" (muzbuild) en TikTok. Imitar el estilo, NUNCA copiar sus temas ni guiones.
Vídeo modelo: `ejemplo_tacano_generoso.mp4` (+ `ejemplo_fotogramas.png`). Míralo (saca fotogramas) antes de cada vídeo.

## Estética (obligatoria)
- Cielo nocturno con estrellas que titilan; estrella islámica de 8 puntas arriba en el centro con halo turquesa.
- Línea de suelo blanca hacia y=1180; debajo, tierra casi negra con polvo y 5 capas onduladas (lo que pasa "por dentro": raíces, semillas, luz).
- Personajes: figuras de palitos blancas (cabeza redonda rellena, trazos gruesos redondeados) con un halo suave. Sin caras, sin colores en la ropa.
- Paleta: negro azulado, blanco crema, turquesa (luz/recompensa) y dorado suave solo para objetos de valor (monedas, luz).
- Textos: mayúsculas monoespaciadas con letras muy espaciadas (función `spaced`), blancos; etiquetas arriba de cada personaje.
- El cielo se va iluminando en turquesa según avanza la historia (la recompensa se "ve").
- Movimiento suave y calmado, nada brusco. Algo cambia cada 1,5-2,5 s.

## Estructura (formato principal: comparación en el tiempo)
1. Dos personajes con etiquetas opuestas (DESCUIDADO/CONSTANTE, TACAÑO/GENEROSO, IMPACIENTE/PACIENTE, EL QUE SE QUEJA/EL AGRADECIDO, EL QUE CALLA/EL QUE CHISMEA...) y contador "DÍA 1".
2. Cada uno hace su elección (subtítulo corto centrado en y≈540).
3. Salto de días ("DÍA 10", "DÍA 30"...) con pulso en la etiqueta; las consecuencias se ven crecer (raíces, árbol, luz, grietas, oscuridad).
4. Pregunta de tensión grande en el centro ("¿QUIÉN TIENE MÁS?") con 2-3 s de silencio.
5. Giro final: el cielo se ilumina, el bueno recibe la recompensa, el otro se apaga.
6. Fuente (Corán sura:aleya o hadiz con número, comprobada en quran.com / sunnah.com) en letras espaciadas.
7. Frase final corta y redonda tipo lema ("DA. NO PIERDES NADA.", "HAZ TU PARTE.").
8. Pregunta al espectador + "COMENTA ↓".
Variantes permitidas para no repetir siempre lo mismo: un solo personaje que cambia con los días, "lo que ves vs lo que Allah ve" (arriba/abajo del suelo), o una metáfora visual (semilla, lámpara, vaso que se llena, camino que se divide). Siempre con la misma estética.

## Técnica
- `ejemplo_tacano_generoso.py` es el motor de referencia: copia el archivo, conserva fondo, estrellas, estrella8, figura y poses, raíces, árbol, monedas, `spaced` y el resplandor, y cambia la línea de tiempo y los objetos de la historia. Añade poses u objetos nuevos con el mismo estilo cuando haga falta.
- Prueba fotogramas sueltos: `python3 motor.py x 0.1 5 12 20` (guarda f_*.png). Vídeo: `python3 motor.py video.mp4`.
- Voz: `audio.py` con un guion.json como `ejemplo_guion.json` (lines + starts + duration + sfx). Voz em_alex, frases cortas, pausas largas (estilo calmado). Sin música. Une con ffmpeg: `-c:v copy -c:a aac -b:a 128k -shortest`.
- 1080x1920, 30 fps, 25-35 s (regla: 35 s como máximo).
- Zona segura: nada de texto importante en los 300 px de abajo ni en los 150 px de la derecha (la tierra de abajo es decorativa).
