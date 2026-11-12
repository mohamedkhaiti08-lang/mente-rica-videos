# Banco de situaciones de cruce (todas comprobadas en fuentes oficiales; ver FUENTES.md).
# Cada tipo: respuesta correcta, de qué lado viene el otro, pregunta, frases de voz (variantes) y rótulo corto.
import random

TIPOS = {
 "der_sin": dict(resp="NO", lados=["der"], actor="coche", senal=None, pregunta="¿Tienes prioridad?",
     voz_q=["¿Tienes prioridad?", "¿Pasas tú o pasa él?", "¿Quién pasa primero?"],
     voz_r=["No. No hay señales, y viene por tu derecha: pasa él.", "No. Sin señales, manda la derecha: pasa él primero."],
     rotulo="SIN SEÑALES: PASA EL DE LA DERECHA", norma="Art. 57 RGC"),
 "izq_sin": dict(resp="SÍ", lados=["izq"], actor="coche", senal=None, pregunta="¿Tienes prioridad?",
     voz_q=["¿Tienes prioridad?", "¿Y aquí, quién pasa?"],
     voz_r=["Sí. No hay señales, y viene por tu izquierda: pasas tú.", "Sí. Tú vienes por su derecha: pasas tú."],
     rotulo="VIENE POR TU IZQUIERDA: PASAS TÚ", norma="Art. 57 RGC"),
 "stop_otro": dict(resp="SÍ", lados=["der", "izq"], actor="coche", senal="stop_otro", pregunta="¿Tienes prioridad?",
     voz_q=["Fíjate bien. ¿Tienes prioridad?", "Mira las señales. ¿Pasas tú?"],
     voz_r=["Sí. Él tiene un stop: debe parar y dejarte pasar.", "Sí. El stop es suyo: te tiene que ceder el paso."],
     rotulo="ÉL TIENE STOP: TE CEDE EL PASO", norma="Señal R-2"),
 "ceda_otro": dict(resp="SÍ", lados=["der", "izq"], actor="coche", senal="ceda_otro", pregunta="¿Tienes prioridad?",
     voz_q=["Mira bien las señales. ¿Tienes prioridad?", "¿Quién tiene que ceder?"],
     voz_r=["Sí. Él tiene un ceda el paso: pasas tú.", "Sí. El ceda el paso es suyo: te deja pasar."],
     rotulo="ÉL TIENE CEDA EL PASO: PASAS TÚ", norma="Señal R-1"),
 "stop_mio": dict(resp="NO", lados=["der", "izq"], actor="coche", senal="stop_mio", pregunta="¿Tienes prioridad?",
     voz_q=["¿Tienes prioridad?", "Ojo a tu derecha. ¿Pasas?"],
     voz_r=["No. Tienes un stop: para y cede el paso a todos.", "No. El stop es tuyo: te paras y pasa él."],
     rotulo="TIENES STOP: CEDE EL PASO", norma="Señal R-2"),
 "ceda_mio": dict(resp="NO", lados=["der", "izq"], actor="coche", senal="ceda_mio", pregunta="¿Tienes prioridad?",
     voz_q=["¿Tienes prioridad?", "¿Pasas tú?"],
     voz_r=["No. Tienes un ceda el paso: pasa él primero.", "No. El ceda el paso es tuyo: espera."],
     rotulo="TIENES CEDA EL PASO: ESPERA", norma="Señal R-1"),
 "peaton": dict(resp="NO", lados=["izq", "der"], actor="peaton", senal=None, pregunta="¿Puedes pasar?",
     voz_q=["¿Puedes pasar?", "¿Sigues o paras?"],
     voz_r=["No. En el paso de peatones, el peatón tiene prioridad.", "No. Está en el paso de peatones: pasa él primero."],
     rotulo="PASO DE PEATONES: PASA EL PEATÓN", norma="Art. 65 RGC"),
 "sem_rojo": dict(resp="NO", lados=["der", "izq"], actor="coche", senal="sem_rojo", pregunta="¿Puedes pasar?",
     voz_q=["¿Puedes pasar?", "¿Sigues o esperas?"],
     voz_r=["No. Tu semáforo está en rojo: esperas.", "No. Rojo es rojo: te quedas parado."],
     rotulo="SEMÁFORO EN ROJO: ESPERA", norma="Art. 146 RGC"),
 "sem_verde": dict(resp="SÍ", lados=["der"], actor="coche", senal="sem_verde", pregunta="¿Tienes prioridad?",
     voz_q=["Viene uno por la derecha. ¿Tienes prioridad?", "¿Quién pasa aquí?"],
     voz_r=["Sí. El semáforo manda más que la regla de la derecha: pasas tú.", "Sí. Tienes verde: pasas tú, aunque venga por la derecha."],
     rotulo="EL SEMÁFORO MANDA: PASAS TÚ", norma="Art. 133 RGC"),
 "ambulancia": dict(resp="NO", lados=["izq", "der"], actor="ambulancia", senal=None, pregunta="¿Tienes prioridad?",
     voz_q=["¿Tienes prioridad?", "¿Y ahora qué?"],
     voz_r=["No. Una ambulancia en servicio de urgencia siempre tiene prioridad.", "No. Con luces de emergencia, pasa la ambulancia."],
     rotulo="AMBULANCIA DE URGENCIA: PASA ELLA", norma="Art. 67 RGC"),
}

INTROS = ["¿Circularías bien? Tres cruces, tres segundos.", "¿Aprobarías el práctico? Tres cruces, tres segundos.",
          "Tres cruces. Tres segundos para cada uno. ¿Los aciertas?", "¿Sabes quién pasa primero? Tres cruces."]
FINALES = ["¿Cuántas has acertado? Dímelo en comentarios.", "¿Cuántas has acertado? Pon tu número abajo.",
           "¿Tres de tres? Escríbelo en comentarios.", "Comenta cuántas has acertado."]
ORD = ["uno", "dos", "tres"]

def elegir(rng, evitar=()):
    """3 tipos distintos, con al menos un SÍ y un NO, evitando los usados recientemente si se puede."""
    pool = [t for t in TIPOS if t not in evitar] or list(TIPOS)
    for _ in range(200):
        tr = rng.sample(pool if len(pool) >= 3 else list(TIPOS), 3)
        r = {TIPOS[t]["resp"] for t in tr}
        if len(r) == 2: return tr
    return tr
