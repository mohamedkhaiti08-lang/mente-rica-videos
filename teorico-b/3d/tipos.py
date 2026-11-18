# Banco de situaciones de cruce (todas comprobadas en fuentes oficiales; ver FUENTES.md).
# Cada tipo: respuesta correcta, de qué lado viene el otro, pregunta, frases de voz (variantes) y rótulo corto.
import random

TIPOS = {
 "der_sin": dict(tema="prioridad", escena="cruce", grupo="der_sin", resp="NO", lados=["der"], actor="coche", senal=None, pregunta="¿Tienes prioridad?",
     voz_q=["¿Tienes prioridad?", "¿Pasas tú o pasa él?", "¿Quién pasa primero?"],
     voz_r=["No. No hay señales, y viene por tu derecha: pasa él.", "No. Sin señales, manda la derecha: pasa él primero."],
     rotulo="SIN SEÑALES: PASA EL DE LA DERECHA", norma="Art. 57 RGC"),
 "izq_sin": dict(tema="prioridad", escena="cruce", grupo="izq_sin", resp="SÍ", lados=["izq"], actor="coche", senal=None, pregunta="¿Tienes prioridad?",
     voz_q=["¿Tienes prioridad?", "¿Y aquí, quién pasa?"],
     voz_r=["Sí. No hay señales, y viene por tu izquierda: pasas tú.", "Sí. Tú vienes por su derecha: pasas tú."],
     rotulo="VIENE POR TU IZQUIERDA: PASAS TÚ", norma="Art. 57 RGC"),
 "stop_otro": dict(tema="prioridad", escena="cruce", grupo="stop_otro", resp="SÍ", lados=["der", "izq"], actor="coche", senal="stop_otro", pregunta="¿Tienes prioridad?",
     voz_q=["Fíjate bien. ¿Tienes prioridad?", "Mira las señales. ¿Pasas tú?"],
     voz_r=["Sí. Él tiene un stop: debe parar y dejarte pasar.", "Sí. El stop es suyo: te tiene que ceder el paso."],
     rotulo="ÉL TIENE STOP: TE CEDE EL PASO", norma="Señal R-2"),
 "ceda_otro": dict(tema="prioridad", escena="cruce", grupo="ceda_otro", resp="SÍ", lados=["der", "izq"], actor="coche", senal="ceda_otro", pregunta="¿Tienes prioridad?",
     voz_q=["Mira bien las señales. ¿Tienes prioridad?", "¿Quién tiene que ceder?"],
     voz_r=["Sí. Él tiene un ceda el paso: pasas tú.", "Sí. El ceda el paso es suyo: te deja pasar."],
     rotulo="ÉL TIENE CEDA EL PASO: PASAS TÚ", norma="Señal R-1"),
 "stop_mio": dict(tema="prioridad", escena="cruce", grupo="stop_mio", resp="NO", lados=["der", "izq"], actor="coche", senal="stop_mio", pregunta="¿Tienes prioridad?",
     voz_q=["¿Tienes prioridad?", "Ojo a la señal. ¿Pasas?"],
     voz_r=["No. Tienes un stop: para y cede el paso a todos.", "No. El stop es tuyo: te paras y pasa él."],
     rotulo="TIENES STOP: CEDE EL PASO", norma="Señal R-2"),
 "ceda_mio": dict(tema="prioridad", escena="cruce", grupo="ceda_mio", resp="NO", lados=["der", "izq"], actor="coche", senal="ceda_mio", pregunta="¿Tienes prioridad?",
     voz_q=["¿Tienes prioridad?", "¿Pasas tú?"],
     voz_r=["No. Tienes un ceda el paso: pasa él primero.", "No. El ceda el paso es tuyo: espera."],
     rotulo="TIENES CEDA EL PASO: ESPERA", norma="Señal R-1"),
 "peaton": dict(tema="prioridad", escena="cruce", grupo="peaton", resp="NO", lados=["izq", "der"], actor="peaton", senal=None, pregunta="¿Puedes pasar?",
     voz_q=["¿Puedes pasar?", "¿Sigues o paras?"],
     voz_r=["No. En el paso de peatones, el peatón tiene prioridad.", "No. Está en el paso de peatones: pasa él primero."],
     rotulo="PASO DE PEATONES: PASA EL PEATÓN", norma="Art. 65 RGC"),
 "sem_rojo": dict(tema="prioridad", escena="cruce", grupo="sem_rojo", resp="NO", lados=["der", "izq"], actor="coche", senal="sem_rojo", pregunta="¿Puedes pasar?",
     voz_q=["¿Puedes pasar?", "¿Sigues o esperas?"],
     voz_r=["No. Tu semáforo está en rojo: esperas.", "No. Rojo es rojo: te quedas parado."],
     rotulo="SEMÁFORO EN ROJO: ESPERA", norma="Art. 146 RGC"),
 "sem_verde": dict(tema="prioridad", escena="cruce", grupo="sem_verde", resp="SÍ", lados=["der"], actor="coche", senal="sem_verde", pregunta="¿Tienes prioridad?",
     voz_q=["Viene uno por la derecha. ¿Tienes prioridad?", "¿Quién pasa aquí?"],
     voz_r=["Sí. El semáforo manda más que la regla de la derecha: pasas tú.", "Sí. Tienes verde: pasas tú, aunque venga por la derecha."],
     rotulo="EL SEMÁFORO MANDA: PASAS TÚ", norma="Art. 133 RGC"),
 "ambulancia": dict(tema="prioridad", escena="cruce", grupo="ambulancia", resp="NO", lados=["izq", "der"], actor="ambulancia", senal=None, pregunta="¿Tienes prioridad?",
     voz_q=["¿Tienes prioridad?", "¿Y ahora qué?"],
     voz_r=["No. Una ambulancia en servicio de urgencia siempre tiene prioridad.", "No. Con luces de emergencia, pasa la ambulancia."],
     rotulo="AMBULANCIA DE URGENCIA: PASA ELLA", norma="Art. 67 RGC"),

 # ---------- tema GIRO (señales R-302, R-303, R-101) ----------
 "r302_der": dict(tema="giro", escena="giro", grupo="r302", resp="NO", senal="r302", giro="der", pregunta="¿Puedes girar a la derecha?",
     voz_q=["Quieres girar a la derecha. ¿Puedes?", "Mira la señal. ¿Puedes girar a la derecha?"],
     voz_r=["No. Esa señal prohíbe girar a la derecha.", "No. Flecha a la derecha tachada: giro prohibido."],
     rotulo="R-302: PROHIBIDO GIRAR A LA DERECHA", norma="Señal R-302"),
 "r302_izq": dict(tema="giro", escena="giro", grupo="r302", resp="SÍ", senal="r302", giro="izq", pregunta="¿Puedes girar a la izquierda?",
     voz_q=["Ahora quieres ir a la izquierda. ¿Puedes?", "Ojo, que es trampa. ¿Puedes girar a la izquierda?"],
     voz_r=["Sí. Esa señal solo prohíbe girar a la derecha.", "Sí. Lo prohibido es la derecha, no la izquierda."],
     rotulo="SOLO PROHÍBE LA DERECHA: SÍ PUEDES", norma="Señal R-302"),
 "r303_izq": dict(tema="giro", escena="giro", grupo="r303", resp="NO", senal="r303", giro="izq", pregunta="¿Puedes girar a la izquierda?",
     voz_q=["Quieres girar a la izquierda. ¿Puedes?", "¿Giras a la izquierda?"],
     voz_r=["No. Esa señal prohíbe girar a la izquierda.", "No. Flecha a la izquierda tachada: prohibido."],
     rotulo="R-303: PROHIBIDO GIRAR A LA IZQUIERDA", norma="Señal R-303"),
 "r303_der": dict(tema="giro", escena="giro", grupo="r303", resp="SÍ", senal="r303", giro="der", pregunta="¿Puedes girar a la derecha?",
     voz_q=["Ojo, que es trampa. ¿Puedes girar a la derecha?", "Quieres ir a la derecha. ¿Puedes?"],
     voz_r=["Sí. Esa señal solo prohíbe girar a la izquierda.", "Sí. Lo prohibido es la izquierda: a la derecha puedes."],
     rotulo="SOLO PROHÍBE LA IZQUIERDA: SÍ PUEDES", norma="Señal R-303"),
 "r303_sentido": dict(tema="giro", escena="giro", grupo="r303", resp="NO", senal="r303", giro="izq", pregunta="¿Puedes cambiar de sentido?",
     voz_q=["Quieres dar la vuelta. ¿Puedes cambiar de sentido aquí?", "La señal no dice nada de dar la vuelta. ¿Puedes?"],
     voz_r=["No. Esta señal también prohíbe cambiar de sentido.", "No. Prohibido girar a la izquierda incluye el cambio de sentido."],
     rotulo="TAMBIÉN PROHÍBE CAMBIAR DE SENTIDO", norma="Señal R-303"),
 "r101_der": dict(tema="giro", escena="giro", grupo="r101", resp="NO", senal="r101", giro="der", pregunta="¿Puedes girar a la derecha?",
     voz_q=["Quieres entrar en esa calle de la derecha. ¿Puedes?", "Mira bien esa calle. ¿Puedes girar a la derecha?"],
     voz_r=["No. Esa calle tiene entrada prohibida.", "No. Señal de entrada prohibida: no puedes entrar."],
     rotulo="ENTRADA PROHIBIDA: NO PUEDES ENTRAR", norma="Señal R-101"),
 # ---------- tema APARCAR (marcas en el bordillo, vado, paso de peatones, R-308) ----------
 "amarilla_cont": dict(tema="aparcar", escena="aparcar", grupo="amarilla_cont", resp="NO", marca="amarilla_cont", pregunta="¿Puedes aparcar aquí?",
     voz_q=["Hay un hueco libre. ¿Puedes aparcar aquí?", "Mira el bordillo. ¿Aparcas aquí?"],
     voz_r=["No. Línea amarilla continua: prohibido parar y estacionar.", "No. Con amarilla continua no puedes ni parar."],
     rotulo="AMARILLA CONTINUA: NI PARAR NI APARCAR", norma="Art. 171 RGC"),
 "amarilla_cont_parar": dict(tema="aparcar", escena="aparcar", grupo="amarilla_cont", resp="NO", marca="amarilla_cont", pregunta="¿Puedes parar un momento?",
     voz_q=["Solo un minuto, para recoger a alguien. ¿Puedes parar aquí?", "No vas a aparcar, solo parar. ¿Puedes?"],
     voz_r=["No. Con línea amarilla continua no puedes ni parar.", "No. La amarilla continua prohíbe parar y estacionar."],
     rotulo="AMARILLA CONTINUA: NI PARAR NI APARCAR", norma="Art. 171 RGC"),
 "amarilla_disc": dict(tema="aparcar", escena="aparcar", grupo="amarilla_disc", resp="NO", marca="amarilla_disc", pregunta="¿Puedes aparcar aquí?",
     voz_q=["Hay sitio. ¿Puedes aparcar aquí?", "Línea a trozos. ¿Aparcas?"],
     voz_r=["No. Amarilla discontinua: puedes parar, pero no aparcar.", "No. Con amarilla discontinua está prohibido estacionar."],
     rotulo="AMARILLA DISCONTINUA: PARAR SÍ, APARCAR NO", norma="Art. 171 RGC"),
 "amarilla_disc_parar": dict(tema="aparcar", escena="aparcar", grupo="amarilla_disc", resp="SÍ", marca="amarilla_disc", pregunta="¿Puedes parar un momento?",
     voz_q=["Solo un momento, para dejar a alguien. ¿Puedes parar?", "No vas a aparcar, solo parar. ¿Puedes?"],
     voz_r=["Sí. Con amarilla discontinua puedes parar, pero no aparcar.", "Sí. La discontinua solo prohíbe estacionar."],
     rotulo="AMARILLA DISCONTINUA: PARAR SÍ, APARCAR NO", norma="Art. 171 RGC"),
 "zigzag": dict(tema="aparcar", escena="aparcar", grupo="zigzag", resp="NO", marca="zigzag", pregunta="¿Puedes aparcar aquí?",
     voz_q=["Hueco libre. ¿Puedes aparcar aquí?", "Fíjate en el suelo. ¿Aparcas?"],
     voz_r=["No. El zigzag amarillo prohíbe estacionar: está reservado.", "No. Zigzag amarillo: prohibido aparcar."],
     rotulo="ZIGZAG AMARILLO: PROHIBIDO ESTACIONAR", norma="Art. 171 RGC"),
 "vado": dict(tema="aparcar", escena="aparcar", grupo="vado", resp="NO", marca="vado", pregunta="¿Puedes aparcar aquí?",
     voz_q=["Sitio perfecto. ¿Puedes aparcar aquí?", "Mira la pared. ¿Aparcas aquí?"],
     voz_r=["No. Delante de un vado señalizado está prohibido aparcar.", "No. Es un vado: no puedes aparcar delante."],
     rotulo="VADO: PROHIBIDO APARCAR", norma="Art. 94 RGC"),
 "paso_cebra": dict(tema="aparcar", escena="aparcar", grupo="paso_cebra", resp="NO", marca="paso_cebra", pregunta="¿Puedes parar un momento?",
     voz_q=["No viene nadie. ¿Puedes parar aquí un momento?", "Es solo un segundo. ¿Puedes parar aquí?"],
     voz_r=["No. En un paso de peatones no puedes ni parar.", "No. Parar en el paso de peatones está prohibido."],
     rotulo="PASO DE PEATONES: NI PARAR NI APARCAR", norma="Art. 91 y 94 RGC"),
 "r308": dict(tema="aparcar", escena="aparcar", grupo="r308", resp="NO", marca="r308", pregunta="¿Puedes aparcar aquí?",
     voz_q=["Hueco libre. ¿Puedes aparcar aquí?", "Mira la señal. ¿Aparcas?"],
     voz_r=["No. Esa señal prohíbe estacionar en este lado.", "No. Señal de estacionamiento prohibido."],
     rotulo="R-308: ESTACIONAMIENTO PROHIBIDO", norma="Señal R-308"),
 "r308_parar": dict(tema="aparcar", escena="aparcar", grupo="r308", resp="SÍ", marca="r308", pregunta="¿Puedes parar un momento?",
     voz_q=["Ojo, que es trampa. ¿Puedes parar aquí un momento?", "Solo vas a parar. ¿Puedes?"],
     voz_r=["Sí. Esa señal prohíbe aparcar, pero puedes parar.", "Sí. Una sola raya: prohibido estacionar, pero parar sí."],
     rotulo="R-308: PARAR SÍ, APARCAR NO", norma="Señal R-308"),
 "plaza_blanca": dict(tema="aparcar", escena="aparcar", grupo="plaza_blanca", resp="SÍ", marca="plaza_blanca", pregunta="¿Puedes aparcar aquí?",
     voz_q=["Por fin, un hueco. ¿Puedes aparcar aquí?", "Plaza libre. ¿Aparcas?"],
     voz_r=["Sí. Plaza marcada en blanco y sin prohibiciones: puedes aparcar.", "Sí. Líneas blancas y ninguna señal: adelante."],
     rotulo="PLAZA EN BLANCO: SÍ PUEDES APARCAR", norma="Art. 170 RGC"),
}

INTROS = ["¿Circularías bien? Tres cruces, tres segundos.", "¿Aprobarías el práctico? Tres cruces, tres segundos.",
          "Tres cruces. Tres segundos para cada uno. ¿Los aciertas?", "¿Sabes quién pasa primero? Tres cruces."]
FINALES = ["¿Cuántas has acertado? Dímelo en comentarios.", "¿Cuántas has acertado? Pon tu número abajo.",
           "¿Tres de tres? Escríbelo en comentarios.", "Comenta cuántas has acertado."]
ORD = ["uno", "dos", "tres"]

TEMAS = {
 "prioridad": dict(cab="CRUCE", voz="Cruce", tit=("EXAMEN PRÁCTICO", "¿Circularías bien?"), sub="3 CRUCES · 3 SEGUNDOS", intros=INTROS),
 "giro": dict(cab="CALLE", voz="Calle", tit=("SEÑALES DE GIRO", "¿Puedes girar?"), sub="3 CALLES · 3 SEGUNDOS",
              intros=["¿Sabes dónde puedes girar? Tres calles, tres segundos.", "Tres señales. ¿Puedes girar o no?",
                      "Si fallas una de estas, suspendes. ¿Puedes girar aquí?", "Hay trampa. Tres calles, tres segundos."]),
 "aparcar": dict(cab="SITIO", voz="Sitio", tit=("APARCAR Y PARAR", "¿Puedes aparcar aquí?"), sub="3 SITIOS · 3 SEGUNDOS",
                 intros=["Tres sitios libres. ¿En cuáles puedes aparcar?", "¿Te multarían? Tres sitios, tres segundos.",
                         "¿Aparcarías aquí? Tres huecos, tres segundos.", "Parar o aparcar. ¿Sabes la diferencia?"]),
 "mezcla": dict(cab="PRUEBA", voz="Prueba", tit=("EXAMEN RELÁMPAGO", "3 pruebas distintas"), sub="CRUCE · GIRO · APARCAR",
                intros=["Examen relámpago: un cruce, un giro y un sitio para aparcar.", "Tres pruebas distintas. ¿Las pasas todas?",
                        "Cruce, giro y aparcar. ¿Aciertas las tres?"]),
}

def elegir(rng, evitar=(), tema="prioridad"):
    """3 tipos de grupos distintos, con al menos un SÍ y un NO, evitando los usados recientemente si se puede.
    tema 'mezcla' = uno de cada tema (prioridad, giro, aparcar) en orden aleatorio."""
    def ok(tr):
        return len({TIPOS[t]["resp"] for t in tr}) == 2 and len({TIPOS[t]["grupo"] for t in tr}) == 3
    if tema == "mezcla":
        pools = [[t for t in TIPOS if TIPOS[t]["tema"] == m] for m in ("prioridad", "giro", "aparcar")]
        pools = [[t for t in p if t not in evitar] or p for p in pools]
        for _ in range(500):
            tr = [rng.choice(p) for p in pools]
            if ok(tr): rng.shuffle(tr); return tr
        return tr
    todos = [t for t in TIPOS if TIPOS[t]["tema"] == tema]
    pool = [t for t in todos if t not in evitar]
    if len(pool) < 3: pool = todos
    for _ in range(500):
        tr = rng.sample(pool, 3)
        if ok(tr): return tr
    for _ in range(500):
        tr = rng.sample(todos, 3)
        if ok(tr): return tr
    return tr
