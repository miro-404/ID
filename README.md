# Oficina de Agentes Académicos

Un equipo de agentes de IA que produce **investigación académica**: estados del arte, revisiones sistemáticas, revisiones de alcance, artículos, capítulos de tesis, proyectos, ensayos e informes con datos propios.

Funciona **dentro de Claude Code** y usa tu plan de Claude (Pro o Max). **No necesitas clave de API ni pagas por uso.**

## Cómo funciona

Escribes `/investigacion` en Claude Code y el coordinador te hace una **entrevista inicial**, que funciona como plantilla de cada producción:

1. Tema.
2. Tipo de producto.
3. Disciplina.
4. Tipo de investigación: documental, cuantitativa, cualitativa o mixta.
5. Idioma, estilo de citación, extensión, período y contexto.
6. **Qué agentes trabajarán en esta producción.** Se te sugiere un equipo según el producto y tú decides.
7. Archivo de datos, si usas al analista de datos.
8. Si quieres aprobar el plan y el borrador antes de continuar.

Luego el coordinador llama a cada agente (subagente de Claude Code) en orden. Cada uno deja su entrega en `producciones/<fecha>-<tema>/`.

## El equipo

| # | Agente | Qué hace |
|---|---|---|
| 1 | **Director de investigación** (siempre) | Preguntas, objetivos, alcance, estructura e instrucciones al equipo |
| 2 | **Metodólogo** | Diseño, criterios de inclusión y exclusión, ecuaciones de búsqueda, plan de análisis |
| 3 | **Buscador bibliográfico** | Busca en OpenAlex, Semantic Scholar y arXiv; registra cada búsqueda |
| 4 | **Cribador** | Incluye o excluye cada fuente con criterio explícito; flujo PRISMA |
| 5 | **Lector-analista** | Matriz de extracción, síntesis temática, debates y vacíos |
| 6 | **Analista de datos** | Analiza tu CSV o Excel con Python: descriptivos, pruebas, tablas y figuras |
| 7 | **Redactor académico** | Escribe el documento con la estructura del producto y tu estilo de citación |
| 8 | **Verificador de citas** | Comprueba con Crossref que cada referencia exista y respalde lo afirmado |
| 9 | **Revisor par** | Evalúa como revisor de revista y devuelve el texto al redactor (rondas de corrección) |

```
/investigacion → entrevista → ficha.md
   Director → Metodólogo → Buscador → Cribador → Lector → Analista de datos
                                                              ↓
                          ┌──────── Redactor ◄────────────────┘
                          ↓            ▲
                     Verificador ──────┤  (rondas de corrección)
                     Revisor par ──────┘
                          ↓
                   DOCUMENTO_FINAL.md
```

## Requisitos

- **Claude Code**, en la app de escritorio, la web o la terminal, con tu cuenta de Claude.
- **Python 3.9 o superior** en tu computadora (https://www.python.org/downloads/; en Windows, marca "Add python.exe to PATH"). Las búsquedas académicas lo usan. No hay que instalar paquetes.
- **Opcional:** `pandoc`, para obtener el documento final en Word.

## Uso

1. Abre esta carpeta del repositorio en Claude Code.
2. Escribe:
   ```
   /investigacion
   ```
   También puedes poner el tema directamente: `/investigacion Uso de IA generativa en la evaluación formativa universitaria`.
3. Responde la entrevista y aprueba el plan.
4. Para retomar una producción interrumpida:
   ```
   /investigacion producciones/2026-11-16-mi-tema
   ```

La primera vez, Claude Code te pedirá permiso para ejecutar `herramientas/academico.py`. Elige "permitir siempre" para no repetirlo en cada búsqueda.

## Límite de uso del plan

Una producción grande, como una revisión sistemática completa, consume bastante uso de tu plan de Claude. Si se agota, todo queda guardado en archivos: espera a que se renueve y retoma con `/investigacion producciones/<carpeta>`.

## Qué entrega cada producción

En `producciones/<fecha>-<tema>/`:

| Archivo | Contenido |
|---|---|
| `ficha.md` | Decisiones de la entrevista |
| `01_plan_director.md` | Plan de investigación |
| `02_metodologia.md` | Diseño, criterios y ecuaciones de búsqueda |
| `03_informe_busqueda.md` | Informe y registro reproducible de búsquedas |
| `04_cribado.md` | Flujo PRISMA y decisión por fuente |
| `05_matriz_y_sintesis.md` | Matriz de extracción y síntesis |
| `06_analisis_datos.md`, `figuras/`, `analisis/` | Análisis de datos propios, reproducible |
| `07_borrador_vN.md`, `08_verificacion_vN.md`, `09_revision_par_vN.md` | Historial de versiones y revisiones |
| **`DOCUMENTO_FINAL.md`** (y `.docx` si hay pandoc) | El producto terminado |
| `corpus.json`, `registro_busquedas.json` | Fuentes y búsquedas |

## Personalizar la plantilla

- **Productos, disciplinas, agentes y archivos:** `plantilla/catalogo.md`.
- **Principios comunes:** `plantilla/principios.md`.
- **Instrucciones de cada agente:** `.claude/agents/<agente>.md`. Ahí también puedes cambiar el modelo de un agente, por ejemplo `model: sonnet` o `model: haiku` para gastar menos uso del plan.
- **Entrevista y coordinación:** `.claude/skills/investigacion/SKILL.md`.
- **Herramientas de búsqueda:** `herramientas/academico.py`.

## Integridad académica

La oficina está diseñada para **no inventar fuentes**:

- El redactor solo puede citar fuentes del corpus encontrado por el buscador.
- Cada cita lleva oculto el id de su fuente.
- El verificador comprueba cada DOI en Crossref.

Aun así, el resultado es un **borrador de investigación** que debe revisar una persona responsable. Declara el uso de IA según las normas de tu institución o de la revista.

## Versión alternativa con la API (opcional, de pago)

La carpeta `oficina/` contiene la misma oficina como programa independiente en Python, que llama a la API de Anthropic. Sirve para automatizar producciones sin Claude Code, pero **requiere una clave de API de pago**. No hace falta para el uso normal.

```bash
pip install -e .
oficina nueva
```
