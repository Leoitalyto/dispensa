# -*- coding: utf-8 -*-
"""Instrucciones actualizadas el 20/11/2026 — ESPAÑOL (ver guida_aggiornamento.py)."""

ga_traduci("es", {
    "x_campanello": ("🔔 La campanita: avisos de esta sección", """En cada sección, debajo de los botones de colores, está **🔔 Avisos de esta sección**. Tócala: una ventana te dice **cómo están configurados los avisos** y **qué está por vencer**.

Desde ahí puedes cambiar:
- **Recibir los avisos de esta sección**: el interruptor los enciende o apaga.
- **Cuántos días antes**: elige los días (0 = el mismo día).
- **Elijo yo la hora**: márcalo, elige la hora y pulsa **Intro** en el teclado. Sin hora elegida los avisos llegan por la mañana.
- **Dónde recibir los avisos**: «como las otras secciones» o elige entre **Telegram, Email, WhatsApp, SMS**.
- **Calendario**: activa «Ver estos avisos también en el calendario» y pulsa **Descargar el calendario**; abre el archivo y Android propone **Google Calendar**. Si cambia una fecha, descárgalo y ábrelo otra vez (se actualizan, no se duplican).
- **Volver como antes** lo deja todo como estaba.

Pulsa **💾 Guardar**. **Antes** escribe tus contactos (Telegram, email, WhatsApp, SMS) en **Salud → Elige cómo recibir los avisos**: sin contacto ese canal no funciona. Los avisos los envía un programa automático: a veces con unos minutos de retraso; un mensaje perdido se recupera en 3 horas, una sola vez.""",
                     "campanita avisos días hora canales telegram email whatsapp sms sonido calendario google calendar"),
    "x_riuso_archivio": ("🗂️ Reutilizar un archivo que ya está en el archivo", """Si ya tienes un archivo o una foto en el archivo **no tienes que rehacerlos**:
- **Salud** (visitas, recetas, documentos, vacunas): debajo de «haz o elige un archivo» está **🗂️ O adjunta desde el archivo**. Escribe para buscar, elige el archivo y guarda: se usa el mismo archivo, sin copiarlo.
- **Casa, Trabajo (nóminas), Coche, Animales**: en el recuadro donde subes un archivo abre **🗂️ O elige un archivo que ya está en el archivo**, elígelo y pulsa **📥 Usar este archivo**: se lee como si lo acabaras de subir.
- **Despensa** (foto del producto): **🗂️ Elegir del archivo** muestra las fotos ya usadas, también de productos terminados.""",
                         "archivo reutilizar foto ya guardado elegir del archivo adjuntar sin rehacer"),
    "x_numeri_utili": ("📞 Números útiles y 📅 Citas", """En cada sección (menos la Despensa), debajo de la campanita, hay dos botones.

**📞 Números útiles** es tu agenda de quien hace falta en esa sección: **nombre, oficio, ámbito, teléfono de la oficina y móvil, horario, web, email, dirección**.
- Si hay un trabajo, marca **«Hay un presupuesto»**: estado, importe, **fechas de inicio y fin** y el **PDF o la foto del presupuesto**.
- En **«Documentos recibidos»** pon PDF, fotos, facturas, contratos.
- Con **«Abrir presupuesto, archivos y pagos»** anotas **anticipos, plazos y saldo** y ves cuánto has pagado y cuánto falta.
- Hay también **Notas** y botones para llamar, WhatsApp, email, abrir el mapa o la web.

**¿De quién son?** En **Salud, Mis documentos y Casa**, donde eliges una persona, números y citas están **separados por persona**.

**📅 Citas**: **nombre, función, fecha, hora, teléfono, motivo y notas**. Arriba ves las **próximas**, por fecha; las pasadas o hechas están abajo. Con **«Poner en el calendario del teléfono»** la cita entra en el calendario con un aviso.""",
                       "números útiles agenda citas presupuesto pagos anticipo saldo contactos calendario"),
    "x_conti_casa": ("💶 Llevar las cuentas", """En **Casa** toca **💶 Llevar las cuentas**. Añade todas las partidas que quieras: **cuentas corrientes** (con el banco), **Postepay**, **libretas postales**, **BOT, BTP**, fondos, acciones, bonos postales, efectivo. Ves el **total** arriba y abajo, los **subtotales** por tipo y un campo de **Notas**. Para los títulos del Estado puedes anotar el vencimiento. **Cada persona tiene sus cuentas**: si en Casa elegiste, por ejemplo, a tu madre, el botón pasa a **«Cuentas de …»**. Las cuentas de una persona no se mezclan con las de los demás.""",
                     "cuentas dinero banco cuenta corriente postepay ahorro bonos btp bot total subtotal persona"),
    "x_badante": ("👵 Cuidadora (solo administrador)", """En **Casa**, solo para el administrador, está **👵 Cuidadora**.
- Fija la **tarifa** (normalmente 20 € por 2 horas), los días que viene y desde qué día contar.
- **Cada día cuenta solo como «ha venido»** (2 horas, la tarifa habitual), desde el día de la primera entrega de dinero: toca **❌ No ha venido** solo si no vino; si se quedó más o menos horas usa **«Otro día u otro importe»**.
- Con **«He dado dinero a mi madre»** anotas cuánto y cuándo.
- La app calcula lo que queda y **hasta cuándo alcanza el dinero**.
- **🔔 Avisos de la cuidadora** te avisa **3 días antes** y **el último día** (puedes cambiar los días).
- Hay también **contactos de la cuidadora** y **notas**.""",
                  "cuidadora badante horas tarifa ha venido dinero madre avisos"),
    "x_interruttori": ("💡 Selectores tipo interruptor", """En toda la app los selectores de píldora (para elegir persona, casa, vehículo…) funcionan como **interruptores**: el **activo es azul neón y late**, los demás parecen **apagados**.""",
                       "interruptor selector píldora activo neón"),
    "x_ia": ("🤖 Inteligencia artificial: documentos, manuscritos, testigos, idiomas", """Con las **claves** de los servicios de inteligencia artificial (gratuitos: Groq, Google Gemini, OpenRouter, NVIDIA, Cloudflare, Cohere, Hugging Face, SambaNova con crédito de prueba; **DeepSeek** de pago, opcional) la app:
- **lee y clasifica los documentos sanitarios** (qué documento es, área médica, prueba, fechas, médico, centro, conclusiones). Si está **escrito a mano**, lo leen **varios servicios** y un «árbitro» compara las lecturas: ves **quién lo leyó**, los **límites** y **qué comprobar** en el papel. Nada se guarda sin tu confirmación;
- **reconoce los testigos del coche**, comparando varias lecturas cuando la foto es dudosa;
- **traduce las páginas** al idioma elegido (la primera vez que se abre una página; luego queda guardado para todos);
- hace que **el asistente** responda en el idioma elegido.
Si un servicio está agotado o lento, la app pasa sola al siguiente.

**DeepSeek es de pago**: solo lo usan **el administrador** y las personas que él elige (Utilidades → 🤖 → DeepSeek → **🔒 Quién puede usarlo**). En la misma fila se ve el **💰 crédito restante**. Las traducciones automáticas nunca usan servicios de pago.

Las claves las pone el administrador en **Utilidades → 🤖 Inteligencia artificial**, con la guía paso a paso; **🔄 Volver a comprobar las claves** y la **prueba** de cada servicio dicen si funciona. Atención: con las claves gratuitas de Google los textos pueden usarse para mejorar sus modelos.""",
             "inteligencia artificial ia claves gemini groq openrouter nvidia cloudflare cohere hugging face sambanova deepseek crédito quién puede usarlo manuscrito testigos traducción"),
    "x_compleanni": ("🎂 Cumpleaños: las fichas de las personas", """En **Utilidades → 🎂 Cumpleaños** toca la **insignia «Feliz cumpleaños»** para abrir la lista (tócala otra vez para cerrarla).

- **➕ Añadir una persona**: nombre y fecha de nacimiento (si no sabes el año marca **«No sé el año»**). Lo demás es opcional: **foto, lugar de nacimiento, apellido, apodo, móvil, teléfono, WhatsApp, Telegram, email, dirección, web, ideas de regalo, notas**. En **«Quién es para ti»**, si eliges **Otro**, puedes escribir tú la palabra justa.
- **La foto**: toca «Elegir la foto»; **pellizca con dos dedos** para ampliar y **arrastra** para moverla hasta que la cara quede en el óvalo. Después puedes **🔄 Recentrar** la foto.
- Cada persona tiene su **ficha con marco de neón** del color de su **signo del zodiaco**, elegido por la fecha. **Los signos se mueven** (Aries da un cabezazo con ojos de fuego, Piscis nadan despacio, Cáncer camina de lado…).
- Debajo de la ficha hay botones para **llamar, WhatsApp, Telegram, email, web**. La lista va por **próximo cumpleaños** («🎉 ¡Hoy!» si es hoy).
- Si **la persona ya no está**, marca **🕯️ Esta persona ya no está**: aparece una **vela encendida**, la ficha pasa a **En memoria** y encuentras **⚰️ Dónde descansa** (tipo de sepultura, cementerio, posición, concesión, lámpara votiva, teléfono y horario del cementerio, fotos de la lápida), la **oración del descanso eterno**, **✍️ un pensamiento** y **🎙️ un mensaje de voz**.
- El **botón verde ⏻** dentro de la ficha abre el **📖 Diario de los recuerdos** (ver su ficha).
- ✏️ **Modificar** cambia los datos (lo que no tocas queda como estaba); 🗑️ **Eliminar** manda la ficha a la Papelera.""",
                     "cumpleaños signo zodiaco ficha persona foto contactos whatsapp telegram fallecido vela memoria sepultura diario"),
    "x_diario": ("📖 El Diario de los recuerdos (fotos, textos, música)", """Dentro de la ficha de cada persona en **🎂 Cumpleaños**, abajo a la derecha, está el **botón verde ⏻**. Tócalo: **la ficha desaparece y se abre el diario**, con las fotos apiladas como las páginas de un libro.

- **Pasar páginas**: **◀ Atrás** y **Adelante ▶** arriba. El **botón rojo ⏻**, entre los dos, cierra el diario y vuelve la ficha.
- **Desplazamiento automático**: las fotos pasan solas cada **7 segundos**; en **⏱️ Desplazamiento automático** eliges los segundos o lo apagas. Cada foto **entra y sale con un efecto siempre distinto**.
- **Añadir fotos**: **➕ Añadir más fotos** (las que quieras, no hay límite). Para cada foto ves una **vista previa**: **pellizcas** con dos dedos para ampliar y **arrastras** para mover; puedes escribir **textos de colores** (color, letra, tamaño, posición) y poner **iconos** (corazones, flores, velas…). Luego **💾 Guardar la página**. Las fotos se aligeran solas sin perder calidad.
- **Cambiar después**: con **✏️ Textos e iconos** quitas o cambias textos e iconos cuando quieras; **↩️ Deshacer el último cambio** lo deja como estaba (la foto original nunca se toca). En **🗂️ Gestionar las páginas** mueves una página **⬆️ ⬇️**, **🔄 cambias la foto** o la **🗑️ eliminas**.
- **Música**: en **🎵 Música del diario** elige un archivo **MP3** (se guarda solo). Empieza al tocar el botón verde; abajo la **barra del volumen** (toca o arrastra) y ▶/🔊 para la pausa. Para cambiarla, elige otro archivo.""",
                 "diario de los recuerdos diario fotos páginas botón verde rojo desplazamiento música mp3 volumen textos iconos efectos gestionar páginas cumpleaños"),
    "f_ia_documenti": ("🤖 Hacer releer y reclasificar los documentos por la IA", """En **Salud → Documentos sanitarios** abre **🤖 Reclasificar los documentos con la IA**.

1. Ves **«Por revisar: X de Y»**: la IA lee **solo los documentos todavía no revisados** (marca «Releer también los ya revisados» para releerlos todos).
2. Toca **🔍 Prueba: leer y clasificar**. Aparece un **recuadro siempre abierto** que se actualiza solo: a qué documento ha llegado, desde hace cuántos segundos, a qué servicio pregunta, cuántos ha leído, cuánto falta. Los puntos **●●●○** que se mueven indican que está trabajando.
3. **Puedes usar otras apps o apagar la pantalla**: la lectura sigue sola. Cada documento se guarda en cuanto se lee, así que nada se pierde.
4. Un documento que se queda bloqueado se **salta tras unos 2 minutos** («demasiado lento, saltado») y se reintenta la próxima vez. **⏹ Detener la lectura** guarda los ya leídos.
5. Las **🟡 Propuestas de la IA por confirmar** aparecen en el mismo recuadro, una por documento: deja marcado lo que esté bien y toca **✅ Aplicar**; **✖ No aplicar** lo deja todo como está. Lo que corregiste a mano no se toca.

También **🔄 Releer los documentos ya archivados** (lectura sin IA) muestra **«Por releer: X de Y»** y no vuelve a proponer los ya hechos.""",
                       "reclasificar documentos ia inteligencia artificial releer lectura en curso propuestas aplicar revisados segundo plano otras apps detener"),
    "f_numeri_doc": ("🔢 El N.º de los documentos sanitarios (para el médico)", """Cada documento sanitario tiene un **número**: el **N.º 1 es el más reciente**, luego hacia abajo hasta el más antiguo. Lo ves en un **recuadro verde** en cada ficha y en la columna **N°** del **resumen PDF** de Salud.

**Para qué sirve:** das el resumen al médico; él te dice «tráeme el 4, el 12 y el 17». Escribe el número (por ejemplo **12**) en la casilla **🔍 Buscar** de los Documentos sanitarios y aparece **solo ese documento**.

**Atención:** cuando añades un documento nuevo, pasa a ser el N.º 1 y los demás **bajan uno**. Si mientras tanto añadiste documentos, **vuelve a crear el resumen PDF**. En el PDF las fechas ya no se parten en dos líneas.""",
                     "número documentos n.º médico resumen pdf buscar número orden más reciente tráeme"),
    "f_gruppo": ("🩸 Grupo sanguíneo y certificado", """En la ficha de la persona en **Salud**: si falta el grupo sanguíneo, toca **🩸 Introducir el grupo sanguíneo**, elígelo y guarda. Puedes cambiarlo cuando quieras con **Modificar**.

Debajo puedes **adjuntar el certificado del grupo sanguíneo** (PDF o foto): elige el archivo y se guarda solo. Lo ves, lo descargas o lo quitas cuando quieras.""",
                 "grupo sanguíneo sangre certificado adjuntar pdf foto ficha persona"),
    "f_wiki": ("📖 «¿Qué es?»: explicación sencilla de Wikipedia", """En **Salud → Documentos sanitarios** y en **Salud → Medicamentos** está el desplegable **📖 ¿Qué es? Explicación sencilla (Wikipedia)**.

Escribe el nombre de una **prueba, una enfermedad o un medicamento** (por ejemplo *ecodoppler*, *duloxetina*): si hay varias entradas elige la correcta y lee **dos líneas de explicación**, en el idioma de la app, con el botón para abrir la página completa.

Es **información general**, gratuita: **no es un consejo médico**. Para tu caso pregunta siempre al médico o al farmacéutico.""",
               "qué es explicación wikipedia prueba enfermedad medicamento significado palabra informe"),
    "x_meteo": ("🌦️ Avisos meteorológicos útiles", """Avisos **solo cuando hacen falta**, arriba en las secciones:
- **Salud**: **calor fuerte** (beber a menudo, no salir de 11 a 17, cuidado con mayores y niños) y **frío intenso**;
- **Coche**: **helada** (hielo en el parabrisas y en las carreteras), **lluvia fuerte**, **rachas de viento**;
- **Animales**: **calor** (paseos temprano o por la noche, asfalto que quema, agua fresca, nunca en el coche) y **frío**.

**Para activarlos:** **Utilidades → 🌦️ Avisos meteorológicos** → escribe tu ciudad → elige la correcta → **💾 Usar esta ciudad**. Ahí ves también las temperaturas de los próximos días y puedes **apagar** los avisos. Cada uno elige su ciudad.

Las previsiones son de **Open-Meteo**: gratuito, sin claves ni registro, para uso no comercial.""",
                "tiempo meteorológico avisos calor frío helada lluvia viento ciudad previsión open-meteo"),
    "x_voci_libere": ("✍️ Un nombre a tu elección en las listas con «Otro»", """En las listas desplegables que tienen la opción **Otro** (tipos de documento, habitaciones, especies de animales, sepulturas, funciones de los médicos, categorías de la comunidad, formas de pago, «Quién es para ti», documentos INPS…):
1. elige **Otro**;
2. aparece **✍️ ¿No está en la lista? Escribe el nombre que quieras**: escribe el nombre exacto (por ejemplo **Ecocert**);
3. guarda como siempre: se guarda **tu nombre**, no «Otro».

En las fichas con el botón de confirmar abajo la casilla está siempre, debajo de la lista, y vale solo si elegiste «Otro». **El nombre queda en la lista**: la próxima vez ya lo encuentras, antes de «Otro».""",
                      "otro nombre a elección lista desplegable escribir nombre opción personalizada ecocert no está en la lista"),
    "x_lingua": ("🌐 El idioma de la app", """**Se entra en el idioma que ves en la página de acceso.** Si quieres otro idioma, elígelo en el menú **🌐 Lingua / Language** antes de tocar **Entrar**: queda guardado.

El teléfono recuerda el **último idioma usado**: la próxima vez la página de acceso ya se abre en ese idioma. Dentro de la app el idioma se cambia desde el menú **☰** arriba a la izquierda.

Todas las páginas están en el idioma elegido: las frases nuevas se traducen solas la primera vez que se abre una página (tarda más o menos un minuto) y luego quedan guardadas para todos. También **el asistente** responde en el idioma elegido.""",
                 "idioma italiano inglés español francés alemán rumano árabe portugués cambiar idioma acceso traducción"),
}, {
    "nv_diario": ("Diario de los recuerdos", "Utilidades → 🎂 Cumpleaños → botón verde ⏻ en la ficha: fotos, textos, iconos, música"),
    "nv_ia": ("Documentos leídos por la IA", "Salud → Documentos sanitarios → 🤖 Reclasificar: funciona aunque uses otras apps"),
    "nv_numeri": ("N.º de los documentos", "Salud → Documentos sanitarios: el N.º 1 es el más reciente; busca por número"),
    "nv_meteo": ("Avisos meteorológicos", "Utilidades → 🌦️ Avisos meteorológicos: elige tu ciudad"),
    "nv_wiki": ("¿Qué es?", "Salud → Documentos sanitarios y Medicamentos: explicación sencilla de Wikipedia"),
    "nv_altro": ("Nombres a elección", "En las listas con «Otro»: escribe el nombre que quieras"),
})


ga_traduci('es', {"l_festivita": ('📅 Días festivos en el Control de horas', 'En **Trabajo → 🧮 Control de horas**, después de cargar la hoja de horas y la nómina, está **📅 Días festivos**.\n\nLa app conoce sola los **festivos nacionales** (también el **Lunes de Pascua**, que cambia cada año) y la **fiesta del patrón** de tu ciudad, que eliges una vez en **⛪ Fiesta del patrón y festivos del año** (para Turín: San Juan, 24 de junio) y luego tocas **💾 Recordar el patrón**.\n- **Aviso rojo**: trabajaste un día festivo que en la hoja **no está marcado como festivo**. Ves los días, las horas y una estimación de lo que podrías perder (el festivo se paga al 65%, las horas extra normales al 20%). Marca «festivo» en la hoja y vuelve a cargarla, o pregunta a la oficina de nóminas.\n- **Aviso amarillo**: un día está marcado como festivo pero no es festivo ni domingo: compruébalo (puede valer una regla de tu contrato).\n\nLos festivos vienen de **Nager.Date** (gratuito, sin clave); si no responde, los calcula la app.', 'festivos días festivos lunes de pascua patrón control de horas nómina horas extra')}, {})


ga_traduci('es', {"x_lettore": ('🤖 Releer y recatalogar los documentos con la IA (todas las secciones)', 'Al final de **Mis documentos**, **Casa** (pestaña 📚 Documentos), **Trabajo**, **Coche** y **Animales** está **🤖 Releer y recatalogar con la IA** (en Salud está «🤖 Reclasificar los documentos con la IA»).\n\n**Cómo lee:** en **dos tiempos**: primero entiende **qué documento es**, luego lee los datos con la **ficha adecuada para ese tipo** (para el DNI: número, emisión, caducidad; para la factura: periodo, importe, vencimiento, POD/PDR…). Después **comprueba** los datos: código fiscal, número del documento de identidad o del pasaporte, matrícula, bastidor, IBAN, fechas (caducidad después de la emisión, nunca la fecha de nacimiento en lugar de otra). Un dato que no pasa los controles queda **🟠 por verificar** y no se propone.\n\n1. Abre el desplegable: ves **«Por revisar: X de Y»**. Toca **🔍 Leer y catalogar**.\n2. Aparece el **recuadro en directo**: puedes usar otras apps, la lectura sigue; cada documento se guarda en cuanto se lee.\n3. Las **🟡 Propuestas por confirmar** muestran qué cambiaría: deja marcado lo correcto y toca **✅ Aplicar**; **✖ No aplicar** lo deja todo como está.\n\nTambién los documentos **nuevos** (foto del DNI, facturas, pólizas, documentos del veterinario) se leen con el mismo método.', 'releer recatalogar documentos ia controles código fiscal número fechas propuestas aplicar')}, {})

# 20/11 sera: di chi è il documento · biglietto da visita
ga_traduci('es', {'x_smistamento': ('👥 De quién es el documento y adónde va (mamá, su casa, su salud)', "Cuando la IA lee un documento también entiende **a quién va dirigido** (destinatario de la carta, titular de la factura, paciente del informe) y **en qué sección va**.\n\n**Primero, una sola vez:** en **🤖 Rileggi e ricataloga con l'IA** (Mis documentos o Casa) o en **🤖 Riclassifica** (Salud) toca **👥 Di chi sono i documenti: persone e case** (De quién son los documentos: personas y casas):\n- para cada persona escribe **nombre y apellidos como aparecen en los documentos** (p. ej. para «Mamá»: Maria Teresa Ianniciello) y, si lo sabes, el **código fiscal**;\n- para cada casa elige **de quién es** (p. ej. «Casa de mamá» → Mamá). Toca **💾 Salva** (Guardar).\n\n**Después la app propone sola:**\n- 🏠 **En qué casa**: la carta del administrador dirigida a mamá va a la **casa de mamá** (con su administración);\n- 👤 **De quién es**: el DNI de mamá va a los **documentos de mamá**; el informe médico de mamá va a **sus documentos sanitarios**;\n- 📦 **Se mueve a**: un informe médico guardado en Casa o en Mis documentos va a la **Salud** de la persona correcta; un documento de identidad guardado en Casa va a **Mis documentos**.\n\nLos documentos **nuevos** se leen **solos** en cuanto los subes (en segundo plano): al volver a abrir la sección encuentras la propuesta. Nada se mueve sin **✅ Applica** (Aplicar). Lo mismo vale para tus documentos.", 'de quién titular destinatario mamá madre persona casa administración salud mover sección correcta código fiscal nombre apellido documentos propuesta'), 'x_biglietto': ('📇 Tarjeta de visita en Números útiles', 'En **Casa, Salud, Trabajo, Coche y Animales → 📞 Numeri utili → ➕ Aggiungi** (Números útiles → Añadir) está **📇 Fotografa un biglietto da visita** (Fotografía una tarjeta de visita).\n1. Haz la foto (también anverso y reverso) y toca **🔎 Leggi il biglietto** (Leer la tarjeta).\n2. La IA escribe sola **nombre o empresa, persona de contacto, oficio, teléfono, móvil, email, web, dirección, horarios** (el NIF/IVA va en las notas). **Revisa** y corrige si hace falta.\n3. Si ya habéis usado sus servicios marca **✅ Abbiamo già usato le sue prestazioni** (Ya hemos usado sus servicios) y escribe **cuándo** y **qué hizo** (y cómo fue). También está el campo **📝 Note** (Notas).\n4. Toca **✅ Salva** (Guardar).\n\nEn la ficha encuentras los botones para contactarlo enseguida: **📞 Llamar, 💬 WhatsApp, ✉️ Email, ✈️ Telegram, 💬 SMS** (el +39 se añade solo).', 'tarjeta de visita foto números útiles contactos teléfono whatsapp email telegram sms ya usado trabajos hechos cuándo notas artesano')}, {'nv_smista': ('De quién es el documento', 'La IA pone los documentos de mamá en sus cosas: casa, salud, documentos'), 'nv_biglietto': ('Tarjeta de visita', 'Números útiles → ➕ Añadir → 📇 Fotografía una tarjeta de visita')})
