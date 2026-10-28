# -*- coding: utf-8 -*-
"""Guida, giro guidato, novità e testi dell'assistente in SPAGNOLO. Caricato da app_dispensa.py dopo info_sezioni.py.
Per le schermate Farmacia / I miei documenti / Utilità i nomi dei pulsanti restano come si vedono sullo schermo (in italiano)."""
GUIDA_TR["es"] = {
    "d_assistente": ("🤖 El asistente digital (el robotito)",
        """Es el **robotito amarillo y azul** de abajo a la derecha, con la cara redonda. **Tócalo** y se abre su panel.

Qué sabe hacer:
- **📖 Explícame esta página**: te cuenta en voz alta para qué sirve la página en la que estás.
- **🧭 Recorrido guiado**: te explica toda la app paso a paso (Siguiente y Atrás).
- **🆕 Qué hay de nuevo**: te dice las novedades y dónde encontrarlas.
- **🎤 Haz una pregunta**: toca, habla (por ejemplo «¿cómo añado una foto al documento?») y te responde con la guía. Funciona en Chrome para Android.
- También puedes **escribir** la pregunta en la casilla.

**Voz:** usa la voz del teléfono. Si no quieres oírlo, toca **🔊 Voz: activa** para apagarla.

**Para desactivarlo:** toca **⛔ Desactivar asistente** en su panel. Para reactivarlo abre el botón rojo **Toca para información** y toca **✅ Activar** en el recuadro del asistente. La elección queda guardada en el teléfono.""",
        "asistente robot robotito voz habla microfono escucha pregunta recorrido novedades desactivar activar apagar ayuda"),
    "d_inizio": ("🚀 Para qué sirve y cómo se empieza",
        """**Para qué sirve:** guarda la lista de lo que tienes en casa, de cuándo caduca y de qué contiene. Te avisa antes de que algo se estropee.

**Para empezar, 5 pasos:**
1. Toca la pestaña **➕ Añadir** de abajo.
2. Fotografía el producto (o sáltalo).
3. Escribe el nombre, cuántas unidades tienes y la **fecha de caducidad**.
4. Toca el botón para guardar.
5. Vuelve a la pestaña **🏠 Despensa**: el producto está ahí, con el color de la caducidad.

La despensa es **solo tuya**: cada persona tiene su contraseña y nadie ve los productos de los demás.""",
        "empezar comenzar primeros pasos que es para que sirve como funciona introduccion uso"),
    "d_aggiungere": ("➕ Cómo añadir un producto",
        """1. Toca **➕ Añadir** (pestaña de abajo).
2. Arriba está la zona de la **foto**: toca **📷 Hacer la foto** (se abre la cámara trasera) o **📁 Subir desde el teléfono**.
3. Escribe el **nombre** y la **marca**.
4. Escribe el **código de barras** a mano (son los números bajo las barras): la app rellena sola ingredientes, valores y alérgenos, si el producto es conocido.
5. Escribe **cuántas unidades**, cuánto **pesa** o cuántos **litros**.
6. Elige la **fecha de caducidad**.
7. En **«¿Dónde lo pones?»** elige: Despensa, Nevera, Congelador, Bodega, Tienda, Almacén u Otro. La **Categoría** es texto libre.
8. Elige **para quién es**: adultos, bebés (0-2 años) o animales.
9. Guarda.

Si no tienes ninguna información basta el **nombre, las unidades y la caducidad**.""",
        "añadir anadir insertar nuevo producto codigo de barras qr rellenar donde nevera congelador bodega categoria cantidad unidades peso litros escribir"),
    "d_foto": ("📸 La foto del producto: toma, regla y recorte",
        """1. Toca **📷 Hacer la foto** o **📁 Subir desde el teléfono**.
2. La app quita el **fondo** y **endereza** sola el producto.
3. Debajo aparece el **editor**: arrastra la **regla** para girar la foto y arrastra el **marco** para recortar los bordes.
4. Cuando esté perfecta toca **💾 Guardar posición y recorte**.
5. Luego guarda el producto.

Si el editor no funciona, abre **🛠️ Controles de reserva**: hay deslizadores para girar y recortar.""",
        "foto fotografiar tomar camara girar rotar enderezar recortar cortar fondo recorte regla marco imagen"),
    "d_colori": ("🎨 Los colores y los avisos de caducidad",
        """- 🟢 **Verde**: faltan más de 2 meses. Todo tranquilo.
- 🟠 **Naranja**: caduca en menos de 2 meses. Conviene usarlo.
- 🔴 **Rojo**: caduca en menos de 1 mes. Úsalo pronto.
- ⚫ **Oscuro**: ya ha caducado.

Arriba ves los **contadores** de colores y los avisos con cuántas unidades, gramos o litros están a punto de caducar.

Cada sección tiene su **sonido**: adultos los sonidos de siempre; bebés un sonido para la niña (2 meses), uno para el niño (1 mes) y ambos si ha caducado; animales el gato (2 meses), el perro (1 mes) y el león si ha caducado.

Si has activado **Telegram** o el **correo**, el aviso llega también allí.""",
        "colores caducidad avisos verde naranja rojo caducado contadores sonido sonidos sirena notificacion aviso cuando caduca"),
    "d_allergeni": ("🌾 Alérgenos, ingredientes, vegano y sin gluten",
        """1. Abre el **menú de la izquierda** (la flecha **»** arriba a la izquierda) y elige **tus alergias**.
2. Los productos con un alérgeno tienen un **botón amarillo** con su nombre (por ejemplo *Gluten*): tócalo y se abre la **composición**, con las palabras peligrosas resaltadas.
3. Si el alérgeno es **peligroso para ti** aparece la **sirena parpadeante**, con escrito a quién está contraindicado.
4. En cada ficha está el botón **Ingredientes**: abre todo el texto para leer, en tu idioma.
5. Los botones **Vegano** y **Vegetariano** aparecen solo si el producto lo es de verdad. El botón **Sin gluten** tiene el borde dorado.""",
        "alergenos alergia gluten ingredientes vegano vegetariano sin gluten composicion intolerancia sirena peligroso"),
    "d_pulsanti": ("🔘 Los botones de cada producto: Eliminar, Info, Editar",
        """En **Fichas**, bajo cada producto hay tres botones:
- **Eliminar**: quita el producto. Si tienes el mismo producto con varias caducidades, te pregunta **qué entrada** eliminar.
- **Info**: abre la guía completa con todos los símbolos.
- **Editar**: cambia cualquier dato (nombre, caducidad, foto, cantidad…).

En **Tabla** se marca la casilla 🗑️ de la fila y luego se toca **Eliminar las filas marcadas** o **Editar la fila marcada** (para editar marca una sola fila).""",
        "eliminar borrar papelera editar modificar cambiar corregir info tabla fichas vista"),
    "d_icone": ("🧭 Los iconos Farmacia, Mis documentos y Utilidades",
        """En el Inicio, junto a los controles de búsqueda, hay **tres iconos que laten**:
- **🏥 Farmacia**: medicamentos, terapias, visitas, tarjeta sanitaria.
- **📁 Mis documentos**: DNI, carné de conducir, tarjeta sanitaria con sus caducidades.
- **🧰 Utilidades**: apps y sitios útiles, como Velocity Music.

Toca uno para abrirlo; para volver toca **← Volver a la despensa**. En cada página, arriba, está el botón rojo **Toca para información** con la guía.""",
        "iconos farmacia documentos utilidades inicio paginas navegar menu donde encuentro"),
    "d_cercare": ("🔎 Buscar y filtrar los productos",
        """Arriba en la Despensa hay tres controles:
1. **🔎 Buscar**: escribe el nombre o la marca.
2. **Mostrar**: elige *Todos*, *Solo por caducar (2 meses)*, *Solo rojos (1 mes)* o *Caducados*.
3. **Vista**: *Fichas* (con fotos grandes) o *Tabla* (lista compacta).""",
        "buscar busqueda encontrar filtro filtrar mostrar vista fichas tabla lista"),
    "d_spesa": ("🛒 Lista de la compra y folletos",
        """- Cuando un producto **se acaba** va solo a la pestaña **🛒 Compra**.
- En la pestaña Compra puedes tocar **He consumido uno** para restar una unidad.
- En la ficha del producto, a la derecha de la cantidad, está el enlace a los **folletos** de supermercados, hipermercados y descuentos: elige la **ciudad**, mira las ofertas y toca el botón para poner el producto en la **lista de la compra**, con el nombre de la tienda.""",
        "compra lista de la compra comprar folletos ofertas supermercado consumido acabado ciudad tienda"),
    "d_gestisci": ("✏️ Gestionar muchos productos a la vez",
        """La pestaña **✏️ Gestionar** sirve para cambiar de una vez **cantidad, caducidades y notas** de muchos productos, sin abrirlos uno por uno.""",
        "gestionar modificar muchos varios productos juntos cantidad caducidades notas"),
    "d_account": ("👤 Contraseña, idioma y mensajes",
        """- **Contraseña:** te la da quien gestiona la app. En el primer acceso puedes cambiarla. Es solo tuya.
- **Idioma:** en el menú de la izquierda está **🌐 Idioma / Language**.
- **Mensajes y sugerencias:** para una idea, un problema o una petición usa la pestaña **✉️ Mensajes / 💬 Sugerencias**: la lee el administrador.""",
        "contraseña contrasena password cuenta acceso idioma language mensajes sugerencias administrador problema peticion cambiar"),
    "d_aiuto": ("🛟 Si algo no va bien",
        """1. **Recarga la página** del navegador.
2. ¿No aparece la foto? Usa **🛠️ Controles de reserva** o elige otra foto.
3. El micrófono para dictar funciona en **Chrome para Android**: toca una vez para encenderlo, otra para apagarlo.
4. Si el problema continúa, escríbelo en la pestaña **Mensajes**: ayuda al administrador a arreglarlo.""",
        "problema error no funciona ayuda bloqueado foto no aparece microfono dictado"),

    "f_cosa": ("🚀 Para qué sirve la Farmacia",
        """Aquí mantienes en orden los **medicamentos de casa** y las **caducidades**, las **terapias**, las **visitas**, las **vacunas**, tu **médico** y tu **ficha sanitaria**.

La app te **recuerda** y organiza lo que introduces tú. **No da consejos médicos** y no cambia las terapias: para dosis y tratamientos sigue siempre al médico o al farmacéutico.""",
        "farmacia que es para que sirve medicamentos empezar introduccion"),
    "f_profili": ("👤 Los perfiles de la familia y el grupo sanguíneo",
        """Cada persona tiene un **perfil** (hasta 12): mamá, papá, hijos…
1. Arriba elige el perfil en **👤 Profilo**.
2. Para añadir uno abre **👥 Gestisci profili**, escribe el nombre y toca **Aggiungi profilo**.
3. En el mismo sitio puedes cambiar el nombre y elegir el **🩸 grupo sanguíneo**: aparece como una **gota** de color junto al perfil.
4. Para borrar un perfil marca la confirmación y toca **Elimina profilo** (se borran también todos sus datos).""",
        "perfil perfiles familia persona grupo sanguineo gota nombre añadir borrar"),
    "f_medicinale": ("💊 Cómo añadir un medicamento",
        """1. Toca **➕ Aggiungi medicinale**.
2. Arriba la **foto del envase**: **📷 Scatta la foto** o **📁 Carica dal telefono**; luego endereza con la regla, recorta con el marco y toca **💾 Salva posizione e ritaglio**.
3. Escribe **nombre**, **principio activo**, **dosis**, **forma** (comprimidos, jarabe…) y **cantidad**.
4. Elige la **caducidad** y **para quién es**.
5. Toca **Salva**.

Puedes reutilizar una foto ya guardada desde el **archivo de fotos**. Al medicamento puedes adjuntar el **prospecto** (PDF, foto o enlace).""",
        "medicamento medicamentos farmaco añadir envase foto caducidad principio activo dosis prospecto archivo"),
    "f_scadenze": ("🎨 Caducidades y alergias a fármacos",
        """- 🟠 **Naranja**: caduca en menos de 2 meses. 🔴 **Rojo**: en menos de 1 mes. ⚫ **Caducado**: tirar de forma correcta.
- En la ficha del perfil puedes escribir las **alergias a fármacos**: si un medicamento contiene ese principio activo aparece un **aviso rojo**.""",
        "caducidad colores alergia alergias farmacos aviso rojo naranja caducado"),
    "f_terapie": ("📅 Las terapias y el calendario",
        """1. Abre la pestaña **📅 Terapie**.
2. Añade una terapia: **medicamento**, **días**, **horas** y cantidad.
3. A la hora fijada toca **Presa** (tomada) para anotar la toma: queda en el **historial**.
4. Una terapia puede estar **activa**, **suspendida** o **terminada**. Las terapias de prueba se pueden **eliminar**.
5. El **calendario** muestra la semana y el mes.
6. El **Informe para el médico** (periodo a elegir) se imprime o se abre en Excel.""",
        "terapia terapias calendario toma tomada horas informe medico historial pastilla dosis"),
    "f_visite": ("🩺 Visitas, pruebas e informes",
        """1. Abre la pestaña **🩺 Visite** y toca para añadir.
2. Escribe **fecha**, **tipo de visita o prueba**, **médico**, **motivo** y las **indicaciones para los controles**.
3. Si hay, escribe la fecha de la **próxima cita**.
4. Adjunta los **informes**: foto o PDF.""",
        "visita visitas examen prueba informe analisis cita especialista adjuntar"),
    "f_vaccini": ("💉 Vacunas y cartilla de vacunación",
        """En la pestaña **💉 Vaccini** registras las vacunas de cada perfil y adjuntas la **cartilla de vacunación** (foto o PDF).""",
        "vacuna vacunas vacunacion cartilla"),
    "f_scheda": ("🩸 La ficha sanitaria y «Il mio dottore»",
        """- Toca el recuadro del **grupo sanguíneo** para abrir la **ficha sanitaria**: patologías, alergias a fármacos, intervenciones, historia clínica y vacunas.
- Al lado encuentras **Il mio dottore** (Mi médico): elige médico o médica, luego escribe nombre, dirección, teléfono, correo, el **horario** (una fila por día: desde, hasta, notas), el **sustituto** y las notas.""",
        "ficha sanitaria medico medico de cabecera patologias intervenciones historia clinica horario telefono correo sustituto"),
    "f_tessera": ("🪪 Tarjeta sanitaria y expediente sanitario",
        """Arriba, junto a la médica, está la insignia azul claro **Tessera sanitaria · Fascicolo sanitario** (late suavemente para llamar la atención). Tócala.

**La tarjeta**
1. Toca **👁️ Mostra fronte e retro della tessera**: la ves en grande.
2. La tarjeta se toma de **I miei documenti**. Si aún no la has introducido aparece un aviso con el botón **📁 Vai a I miei documenti**: elige **Tessera sanitaria** y haz la foto de anverso y reverso. El aviso desaparece solo en cuanto la has introducido.

**Los enlaces en línea** (uno para el expediente sanitario electrónico, uno para las vacunas, uno para los gastos sanitarios deducibles)
1. Abre la página en el navegador y **copia la dirección** de la barra de arriba.
2. Vuelve aquí y **pégala** en la casilla correcta.
3. Toca **💾 Salva**.
4. Desde ese momento aparece un botón **🔗**: al tocarlo se abre directamente la página.
5. Para cambiar el enlace toca **✏️ Modifica**; para quitarlo toca **🗑️ Togli il link**.

Los enlaces están separados para cada perfil de la familia.""",
        "tarjeta sanitaria tessera expediente sanitario electronico fse enlace link direccion vacunas en linea gastos deducibles anverso reverso insignia"),
    "f_aperta": ("🔎 Encuentra una farmacia abierta",
        """Toca el botón grande **🔎 Trova una farmacia aperta** de arriba: la app busca las farmacias abiertas cerca de ti.""",
        "farmacia abierta encontrar buscar cerca guardia noche"),
    "f_avvisi": ("🔔 Avisos por Telegram, correo y SMS",
        """Los avisos te recuerdan las caducidades (a 60, 30, 14 y 7 días, 1 día y el mismo día) y, si quieres, la hora de las terapias. Elige **uno o más canales**.

### 📱 Telegram, paso a paso
**Qué necesitas:** la app Telegram en el teléfono y dos minutos. Telegram es gratis.

1. **Instala Telegram** desde Play Store (Android) o App Store (iPhone) y crea tu cuenta: te pide el número de móvil.
2. **Abre el bot de la app.** Dentro de Telegram toca la lupa 🔍 de arriba y busca **Dispensa Leo**.
3. Toca **Iniciar** (o escribe `/start`). **Este paso es importante:** si no lo haces, el bot no puede escribirte.
4. **Descubre tu número (Chat ID).** Busca el bot **@userinfobot**, ábrelo y toca **Iniciar**: te responde con tu **Id**, un número (por ejemplo `123456789`). Mantenlo pulsado para copiarlo. Es un bot gratuito que solo te dice ese número.
5. **Vuelve a esta página.** Abre **🔔 Scegli come ricevere gli avvisi**, marca **📱 Telegram**, pega el número en el campo **Chat ID** (solo números) y toca **Salva**.
6. **Hecho.** Los avisos llegan de ese bot, a partir del próximo envío automático (normalmente a la mañana siguiente).

**Si no llega nada:** comprueba que has tocado *Iniciar* en el bot (paso 3) y que el número es correcto, sin espacios ni letras.

### ✉️ Correo
**Para el correo es facilísimo: basta tu dirección.** No hacen falta contraseñas ni otros ajustes.

1. Abre **🔔 Scegli come ricevere gli avvisi**.
2. Marca **✉️ Email**.
3. Escribe **tu dirección de correo** en el campo (por ejemplo `nombre@gmail.com`) y comprueba que es correcta.
4. Toca **Salva**.

Los mensajes salen de la dirección de correo de la app. **La primera vez mira también en Spam o Promociones** y, si lo encuentras allí, márcalo como «No es spam»: desde ese momento llegará al correo normal.

### 💬 SMS
Son de pago y normalmente no están activos: pregunta al administrador.

Opcional: marca **«Nei messaggi non scrivere i nomi dei medicinali»** (no escribir los nombres de los medicamentos en los mensajes) si quieres más privacidad.""",
        "avisos notificaciones telegram chat id bot iniciar start userinfobot correo email sms recordatorio mensaje recibir activar numero gmail spam"),
    "f_report": ("🧾 Informe completo y datos",
        """En **🧾 I miei dati personali e report completo** escribe nombre y apellidos y descargas un **informe para imprimir** con todo lo que has introducido. El archivo **JSON** contiene los mismos datos como copia de seguridad.
Contiene datos sanitarios: no lo compartas con quien no debe verlo.""",
        "informe completo imprimir exportar descargar datos personales copia pdf json"),

    "u_cosa": ("🧰 Para qué sirve la página Utilidades",
        """Reúne **apps y sitios útiles** en un solo lugar. Cada uno tiene un gran **botón que late**: tócalo y se inicia.

Bajo el botón está el **nombre** de la app: al tocarlo se abre el **prospecto**, una explicación sencilla de qué hace y de sus ventajas.

Por ahora hay **Velocity Music** (el play azul claro) y **Wimbi** (el pato con auriculares); aquí se añadirán otras utilidades.""",
        "utilidades pagina apps botones iniciar coleccion sitios que es para que sirve"),
    "u_avviare": ("▶️ Cómo iniciar una app",
        """1. Desde el Inicio toca el icono **🧰 Utilità** (junto a Farmacia y I miei documenti).
2. Toca el **botón grande** con el símbolo ▶️: la app se abre en una pestaña nueva del navegador.
3. Para volver aquí, cierra esa pestaña o vuelve atrás.""",
        "iniciar abrir arrancar play boton app enlace velocity music musica"),
    "u_bugiardino": ("📖 Cómo leer el prospecto",
        """1. Bajo el botón está la **placa con el nombre** de la app.
2. **Tócala**: se abre una ventana con la explicación (qué es, ventajas, dirección).
3. Dentro también está el botón **🎵 Avvia** para abrir la app.
4. Para cerrar la ventana toca la **X** de arriba.""",
        "prospecto explicacion placa nombre leer descripcion ventajas informacion"),
    "u_wimbi": ("🦆 Wimbi",
        """Wimbi es una app de música: **escribes una canción o un artista, tocas un resultado y suena**. No hace falta registrarse, las listas se quedan en tu dispositivo, la música **sigue sonando con la pantalla apagada** y la app está disponible en **17 idiomas**.

Toca el **pato con auriculares** para iniciarla, o el texto verde **Wimbi** para leer el prospecto completo.
Dirección: https://wimbi.app/it/""",
        "wimbi pato auriculares musica canciones artista lista reproduccion pantalla apagada idiomas sin cuenta"),
    "u_velocity": ("🎵 Velocity Music",
        """Es un reproductor y gestor de música que permite escuchar **gratis** la biblioteca de YouTube, **sin publicidad** y **sin suscripciones**. Se puede usar **como invitado**, sin crear una cuenta. El proyecto aún está en desarrollo pero ya se puede usar.

Dirección: https://velocitymusic.uk/""",
        "velocity music youtube gratis publicidad reproductor canciones escuchar radio"),

    "x_cosa": ("🚀 Para qué sirve «Mis documentos»",
        """Aquí guardas tus **documentos personales** (DNI, carné de conducir, pasaporte, tarjeta sanitaria, permisos, seguros…) con las **fotos de anverso y reverso** y las **caducidades**.

La app te avisa **6 meses antes** (primer aviso, naranja) y **3 meses antes** (segundo aviso, rojo y más intenso), así tienes tiempo para renovarlos.""",
        "documentos que es para que sirve dni carne pasaporte tarjeta sanitaria empezar introduccion"),
    "x_aggiungere": ("➕ Cómo añadir un documento",
        """1. Elige de quién es el documento en **👤 Documenti di**.
2. Toca **➕ Aggiungi un documento**.
3. Elige el **tipo** de la lista. Si no está, escríbelo en la casilla **«Non lo trovi?»**.
4. Escribe **número**, **expedido por**, **fecha de expedición** y **fecha de caducidad**. Si nunca caduca, marca **«Questo documento non scade»**.
5. Haz la **foto de anverso y reverso** (mira la guía de abajo).
6. Toca **💾 Salva il documento**.""",
        "añadir insertar nuevo documento tipo numero expedido caducidad no caduca guardar"),
    "x_foto": ("📷 Foto de anverso y reverso (con el fondo quitado y enderezada)",
        """Hay **dos bloques iguales: 📄 Fronte (Anverso) y 📄 Retro (Reverso)**. Para cada uno:
1. Toca **📷 Scatta la foto** (cámara trasera) **o** **📁 Carica dal telefono** si ya tienes la foto.
2. La app quita el **fondo** y **endereza** sola el documento.
3. Debajo aparece el **editor**: arrastra la **regla** para girar y el **marco** para recortar.
4. Cuando esté perfecta toca **💾 Salva posizione e ritaglio**.
5. Si el documento se ha recortado mal marca **«Tieni anche lo sfondo»**: la imagen queda entera y la ajustas solo a mano.
6. Si te has equivocado de foto toca **🗑️ Togli questa foto**.
7. Al final toca **💾 Salva il documento**: las fotos se guardan junto con los datos.

Para un **PDF** u otras páginas usa el campo **«Altri file»** bajo el formulario.""",
        "foto hacer anverso reverso subir recortar fondo enderezar girar regla marco imagen documento"),
    "x_colori": ("🎨 Los colores y los avisos de caducidad",
        """- 🟢 **Verde**: caduca en más de 6 meses.
- 🟠 **Naranja, primer aviso**: caduca en menos de 6 meses.
- 🔴 **Rojo, segundo aviso**: caduca en menos de 3 meses. Aparece un recuadro de alarma.
- ⚫ **Caducado**: renovar enseguida.

Arriba ves los contadores. Si has activado **Telegram** o el **correo** (se hace en la Farmacia, en **Scegli come ricevere gli avvisi**), los avisos llegan también allí.""",
        "colores caducidad avisos naranja rojo caducado seis meses tres meses renovar alarma telegram correo"),
    "x_cercare": ("🔎 Buscar y filtrar los documentos",
        """Sobre la lista está el campo **Buscar**: escribe el tipo, el número, el organismo o una nota. Al lado elige una **categoría** para ver solo esos.""",
        "buscar busqueda encontrar filtro categoria lista"),
    "x_modificare": ("✏️ Editar, abrir y eliminar",
        """- **Abrir una foto:** toca el nombre del archivo bajo el documento: la ves grande y puedes **descargarla**.
- **Editar:** toca **Modifica**, cambia los datos o añade más fotos, luego guarda.
- **Quitar una sola foto:** en Modifica, en la lista **Già allegato**, toca 🗑️ junto al archivo.
- **Eliminar el documento:** toca **Elimina** y confirma.""",
        "editar modificar cambiar eliminar borrar abrir adjunto descargar quitar foto"),
    "x_tipi": ("⚙️ Los tipos de documento",
        """Al final de la página abre **⚙️ Gestisci i tipi di documento**: puedes **añadir** tus tipos, **quitarlos** u **ocultar** los que no usas.""",
        "tipos tipo categorias nuevo tipo ocultar catalogo"),
    "x_privacy": ("🔒 Privacidad",
        """Los documentos contienen datos personales: **no compartas** capturas ni archivos con quien no debe verlos. Cada persona ve solo los suyos.""",
        "privacidad seguridad datos personales compartir"),

    "tour1": ("¡Bienvenido!", "Hola, soy tu asistente. Te hago un recorrido rápido por la app. Con los botones Siguiente y Atrás vas a tu ritmo, y puedes pararme cuando quieras."),
    "tour2": ("La Despensa", "En la Despensa guardas la lista de lo que tienes en casa. Toca Añadir, fotografía el producto, escribe el nombre y la caducidad. Los colores te dicen cuándo actuar: verde tranquilo, naranja en menos de dos meses, rojo en menos de un mes."),
    "tour3": ("Alérgenos e ingredientes", "Si eliges tus alergias en el menú de la izquierda, los productos peligrosos para ti se reconocen enseguida y aparece una sirena. En cada ficha el botón Ingredientes muestra la composición."),
    "tour4": ("La Farmacia", "Con el primer icono entras en la Farmacia: medicamentos con caducidad, terapias con recordatorios en Telegram o correo, visitas, vacunas y un perfil para cada persona de la familia."),
    "tour5": ("Tarjeta sanitaria", "En la Farmacia, junto a la médica, está la insignia azul claro de la tarjeta sanitaria: muestra anverso y reverso y te deja guardar los enlaces al expediente sanitario, a las vacunas y a los gastos deducibles."),
    "tour6": ("Mis documentos", "Con el segundo icono entras en Mis documentos. Haz la foto del documento: la app quita el fondo, lo endereza y prueba a leer tipo, número y caducidad. Siempre puedes corregir los campos. Te avisa seis y tres meses antes de la caducidad."),
    "tour7": ("Las Utilidades", "Con el tercer icono entras en las Utilidades: apps útiles como Velocity Music y Wimbi. Toca el botón para iniciarlas y el nombre para leer el prospecto."),
    "tour8": ("Ayuda siempre a mano", "Arriba, en cada página, está el botón rojo Toca para información, con la guía y la búsqueda. Y aquí estoy yo: tócame cuando quieras, también con el micrófono. Si no te sirvo, me desactivas desde el panel y me reactivas desde el botón rojo. ¡Buen trabajo!"),

    "nov1": ("Asistente digital", "El robotito redondo de abajo a la derecha: tócalo y te explica la app en voz alta, también con el micrófono"),
    "nov2": ("Nueva utilidad: Wimbi", "Inicio → Utilidades → el pato con auriculares; toca el texto verde para el prospecto"),
    "nov3": ("Nueva página «Utilidades»", "Inicio → tercer icono azul claro «Utilità», junto a Farmacia y I miei documenti"),
    "nov4": ("Guía en cada página", "Botón rojo «Toca para información» arriba, con explicaciones y búsqueda"),
    "nov5": ("Tarjeta sanitaria y expediente", "Farmacia → insignia azul claro junto a la médica"),
    "nov6": ("Documentos: foto y lectura automática", "Mis documentos → «Aggiungi un documento»"),
}

UI_TR["es"] = {
    "dlg_titolo": "📖 Guía e información",
    "dlg_hint": "Toca un tema para abrirlo. O escribe abajo lo que quieres saber.",
    "dlg_cerca_label": "🔎 ¿Qué quieres saber?",
    "dlg_cerca_ph": "p. ej. cómo hago la foto del reverso del documento",
    "dlg_trovato": "**Esto es lo que he encontrado:**",
    "dlg_nulla": "No he encontrado una respuesta con estas palabras. Prueba a escribirlo de otra forma (por ejemplo una sola palabra: *foto*, *caducidad*, *contraseña*) o escribe una sugerencia en la pestaña Mensajes.",
    "dlg_tutti": "Todos los temas",
    "dlg_nota_it": "ℹ️ Las pantallas de esta sección por ahora están en italiano: los nombres de los botones están escritos como los ves en pantalla.",
    "dlg_asst": "**🤖 Asistente digital** (el robotito que habla y te ayuda)",
    "dlg_on": "✅ Activar", "dlg_off": "⛔ Desactivar",
    "info_help": "Toca para leer cómo se usa esta sección", "info_fallback": "ℹ️ Información y guía",
    "sez_dispensa": "🏠 Despensa", "sez_farmacia": "🏥 Farmacia", "sez_documenti": "📁 Mis documentos", "sez_utilita": "🧰 Utilidades",
    "a_aria": "Asistente digital", "a_rileggi": "📖 Explícame esta página", "a_giro": "🧭 Recorrido guiado de la app",
    "a_novita": "🆕 Qué hay de nuevo", "a_mic": "🎤 Haz una pregunta", "a_indietro": "◀ Atrás", "a_avanti": "Siguiente ▶", "a_fine": "Fin",
    "a_ph": "Escribe aquí tu pregunta…", "a_chiedi": "Preguntar", "a_voce_on": "🔊 Voz: activa", "a_voce_off": "🔇 Voz: apagada",
    "a_silenzio": "⏹ Silencio", "a_off": "⛔ Desactivar asistente", "a_ascolto_btn": "⏹ Escuchando…",
    "a_ascolto_t": "Te escucho", "a_ascolto_x": "Habla ahora: por ejemplo «¿cómo añado una foto al documento?»",
    "a_mic_t": "Micrófono", "a_mic_no": "En este teléfono no puedo escucharte: escribe la pregunta abajo.",
    "a_mic_perm": "Permite al navegador usar el micrófono para hablar conmigo.",
    "a_mic_err": "Ahora no puedo usar la voz: escribe la pregunta abajo.",
    "a_nulla_t": "No he oído nada", "a_nulla_x": "Inténtalo de nuevo: toca el micrófono y habla.",
    "a_dimmi_t": "Dime", "a_dimmi_x": "Escribe o di lo que quieres saber.",
    "a_off_t": "¿Quieres que me desactive?",
    "a_off_x": "Toca el botón «⛔ Desactivar asistente» de abajo. Me reactivas desde el botón rojo «Toca para información».",
    "a_trov_t": "No he encontrado la respuesta",
    "a_trov_x": "Prueba con otras palabras (por ejemplo solo una: foto, caducidad, contraseña) o elige un tema abajo.",
    "a_nov_none_t": "Novedades", "a_nov_none_x": "Por ahora no hay novedades recientes. ¡Te aviso cuando lleguen!",
    "a_nov_voce": "Estas son las novedades.", "a_nov_trovi": "La encuentras así:", "a_nov_t": "Qué hay de nuevo",
    "a_fine_t": "Fin del recorrido", "a_fine_x": "¡Listo! Si necesitas algo más, pregúntame.",
    "a_toast_off": "Asistente desactivado. Lo reactivas desde «Toca para información».", "a_toast_on": "Asistente activo: toca el robotito.",
    "a_vedi": "Toca un tema de abajo para saber más.",
    "i_silenzio": "silencio calla basta para chitón", "i_off": "desactiv apag", "i_ass": "asistente robot",
    "i_novita": "novedad nuevo nueva actualiz", "i_giro": "recorrido tutorial guia empez", "i_saluto": "hola buenos buenas ayuda",
}
