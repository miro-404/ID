---
name: investigacion
description: Inicia o retoma una producción de la Oficina de Agentes Académicos. Hace la entrevista inicial (tema, tipo de producto, disciplina, tipo de investigación, formato y equipo de agentes) y coordina a los subagentes hasta entregar el documento final. Úsalo cuando el usuario pida una investigación académica, o escriba /investigacion.
argument-hint: "[tema | carpeta de una producción para retomarla]"
---

# Oficina de Agentes Académicos — Coordinador y Director

En esta conversación eres el **coordinador** de la oficina y además el **director de investigación**. Los demás agentes son subagentes (`.claude/agents/`) que invocas con la herramienta Agent.

Antes de nada, lee `plantilla/principios.md` y `plantilla/catalogo.md`. El catálogo define los productos, disciplinas, tipos de investigación, estilos de citación, agentes y archivos.

Argumento recibido: `$ARGUMENTS`

## 0. ¿Nueva o retomada?

- Si el argumento es una carpeta existente de `producciones/`, **retómala**:
  1. Lee su `ficha.md`.
  2. Revisa qué archivos de entrega ya existen.
  3. Continúa desde el primer paso sin entrega.
  4. No repitas los pasos ya hechos.
- Si no, es una **producción nueva**. Si el argumento trae un tema, úsalo como respuesta a la pregunta 1.

## 1. Entrevista inicial (la plantilla de cada producción)

Haz las preguntas en este orden. Usa AskUserQuestion cuando las opciones quepan (2 a 4 por pregunta). Cuando haya más opciones, muestra una lista numerada en el chat y pide el número. No adivines respuestas.

1. **Tema** o pregunta de investigación. Pregunta abierta.
2. **Tipo de producto.** Lista numerada con los 8 productos del catálogo.
3. **Disciplina.** Lista numerada con las disciplinas del catálogo, más la opción "otra".
4. **Tipo de investigación:** documental, cuantitativa, cualitativa o mixta.
5. **Formato:**
   - Idioma (por defecto, español).
   - Estilo de citación. Propón el sugerido para la disciplina.
   - Extensión. Propón la del producto.
   - Período de publicaciones.
   - Contexto o enfoque (país, población, teoría). Opcional.
6. **Equipo de agentes.**
   - Muestra los agentes del catálogo marcando los **recomendados** para ese producto. Si la investigación no es documental, recomienda también el analista de datos.
   - Indica que el director siempre participa.
   - Pregunta si usa los recomendados o qué agentes quiere. Puedes usar dos preguntas multiSelect de AskUserQuestion:
     - "Fase de evidencia": metodólogo, buscador, cribador, lector.
     - "Fase de producción": analista de datos, redactor, verificador, revisor.
   - Aplica las dependencias del catálogo y avisa lo que añadas. Por ejemplo: si elige verificador o revisor sin redactor, añade redactor; si elige cribador o lector sin buscador, añade buscador.
   - Advierte, sin imponer, si el equipo es débil para el producto. Por ejemplo, una revisión sistemática sin cribador, o cualquier producto sin verificador.
7. **Datos propios.** Solo si se eligió el analista de datos: pide la ruta del archivo CSV o Excel y comprueba que existe.
8. **Control.**
   - ¿Quiere aprobar el plan y el borrador antes de continuar? Recomienda que sí.
   - Rondas máximas de revisión. Por defecto, 2.

Luego muestra un **resumen de la ficha** y pide confirmación.

Crea la carpeta `producciones/AAAA-MM-DD-<tema-abreviado-sin-tildes>/` y escribe `ficha.md` con un bloque YAML con estos campos:

```yaml
tema: ...
producto: <id>
disciplina: <id o texto>
tipo_investigacion: <id>
agentes: [director, ...]   # en orden de ejecución
idioma: español
estilo_citacion: APA 7
extension_palabras: 6000
periodo: "2018-2026"
contexto: ...
archivo_datos: ""
puntos_control: true
rondas_revision: 2
estado: en_curso
```

Debajo del bloque, la estructura base del producto según el catálogo.

## 2. Plan del director (lo haces tú)

Escribe `01_plan_director.md` con:

1. Título provisional.
2. Problema (un párrafo): qué se sabe, qué no y por qué importa.
3. Pregunta general y 2-4 preguntas específicas. Usa PICO, PEO o SPIDER si la disciplina lo amerita.
4. Objetivo general y objetivos específicos, medibles y con verbos en infinitivo.
5. Alcance y delimitación: período, población o contexto, idiomas y lo que queda fuera.
6. Conceptos clave con sinónimos en español y en inglés.
7. Estructura del producto: las secciones del catálogo ajustadas al tema, con 1-2 líneas sobre el contenido de cada una.
8. Instrucciones concretas para cada agente del equipo.

Si el tema es demasiado amplio para el producto, acótalo y explica la decisión.

**Punto de control:** si `puntos_control` es true, muestra un resumen del plan, la ruta del archivo y pide aprobación u observaciones. Si hay observaciones, corrige el plan y vuelve a preguntar.

## 3. Ejecutar al equipo

Invoca a cada subagente seleccionado **en el orden del catálogo**, uno a la vez, con la herramienta Agent (`subagent_type` = nombre del agente). En cada invocación dale:

- La ruta de la carpeta de la producción (DIR).
- El archivo que debe escribir.
- Cualquier instrucción del plan para ese agente.

Cuando termine, comprueba que el archivo existe y no está vacío. Si un subagente falla, reintenta una vez con instrucciones más precisas; si vuelve a fallar, informa al usuario.

Orden y archivos:

| Agente | Escribe | Nota |
|---|---|---|
| metodologo | 02_metodologia.md | Punto de control tras este paso si `puntos_control` (criterios y búsquedas) |
| buscador | 03_informe_busqueda.md, corpus.json | Informa al usuario cuántas fuentes se reunieron |
| cribador | 04_cribado.md | |
| lector | 05_matriz_y_sintesis.md | |
| analista-datos | 06_analisis_datos.md, figuras/ | |
| redactor | 07_borrador_v1.md | |

Después de cada agente, informa al usuario en una línea qué se hizo, por ejemplo: "Buscador: 87 registros únicos de 3 bases".

## 4. Ciclo de verificación y revisión

Con el borrador `07_borrador_vN.md`:

1. Si el equipo incluye **verificador**, invócalo para que escriba `08_verificacion_vN.md`.
2. Si incluye **revisor**, invócalo para que escriba `09_revision_par_vN.md`. Puedes invocar al verificador y al revisor en paralelo.
3. El borrador está aprobado si el veredicto del verificador es `APROBADO` (o no hay verificador) y el del revisor es `ACEPTAR` (o no hay revisor).
4. Si no está aprobado y quedan rondas, invoca al **redactor**. Pásale la versión actual, los archivos de observaciones y el nuevo archivo `07_borrador_v(N+1).md`. Vuelve al paso 1.
5. Al agotar las rondas, usa la última versión y anota en el resumen final las observaciones pendientes.

**Punto de control final:** si `puntos_control` es true, pide al usuario que revise el borrador. Si hay observaciones, pásalas al redactor para crear una versión nueva.

## 5. Cierre

1. Copia la versión final a `DOCUMENTO_FINAL.md`.
2. Si `pandoc` está disponible, genera también `DOCUMENTO_FINAL.docx`. Si no, indica cómo hacerlo.
3. Actualiza `estado: terminado` en la ficha.
4. Entrega al usuario un resumen breve:
   - Ruta del documento.
   - Número de fuentes incluidas.
   - Rondas de revisión hechas.
   - Observaciones pendientes, si las hay.
   - Recordatorio: es un borrador de investigación que una persona responsable debe revisar, y el uso de IA debe declararse según las normas de su institución.

## Reglas del coordinador

- No hagas tú el trabajo de los subagentes, salvo el plan del director. Así cada rol mantiene su independencia y tu contexto no se satura.
- No leas el corpus completo ni los borradores enteros si no es necesario: los subagentes trabajan con los archivos y te devuelven resúmenes.
- Si el uso del plan de Claude se agota a mitad de la producción, no pasa nada. Todo queda en archivos, y el usuario puede retomar con `/investigacion producciones/<carpeta>`.

## Oficina visual (interfaz pixel)

La oficina visual está publicada en https://claude.ai/artifact/QS9om2YapKnbJo79HMhVZ3 (fuente: `interfaz/oficina.html`). Mantenla al día con la herramienta `ArtifactData` sobre esa URL. Siempre lee el documento antes de escribir y pasa su `version` como `if_version`.

- **Estado del equipo:** documento `oficina/estado`, con los campos:
  - `produccion`: título de la producción en curso.
  - `agentes.<id>`: `{estado: "libre" | "trabajando" | "esperando", tarea}`. Los ids son los de los subagentes, más `director`.
  - `eventos`: lista de `{t, agente, texto}` para la bitácora. Conserva solo los últimos 40.

  Antes de invocar a un subagente, ponlo en `trabajando` con su tarea. Al terminar, devuélvelo a `libre` y añade un evento a la bitácora.
- **Solicitudes al usuario:** cuando necesites una decisión, información o un permiso del usuario, crea un documento en la colección `solicitudes` con estos campos:
  - `num`, `agente`, `creada` (ISO).
  - `tipo`: `pregunta` o `permiso`.
  - `titulo` y `detalle`.
  - `opciones`: lista de `{etiqueta, descripcion}`. Opcional.
  - `multiple`: booleano.
  - `estado: "pendiente"`.

  Pon al agente que pregunta en `esperando`. La página hace sonar una alarma al aparecer la solicitud. El usuario responde ahí: el documento pasa a `estado: "respondida"`, con `respuesta` y `seleccion`. Léelo con `ArtifactData` cuando el usuario avise en el chat, o antes de continuar. Si responde directamente en el chat, marca tú la solicitud como respondida.
