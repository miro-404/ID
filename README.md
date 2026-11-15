# Oficina de Agentes Académicos

Un equipo de agentes de IA (Claude) que produce **investigación académica**: estados del arte, revisiones sistemáticas, artículos, capítulos de tesis, proyectos, ensayos e informes con datos propios.

Cada producción empieza con una **entrevista** que funciona como plantilla. En ella se define:

1. El tema.
2. El tipo de producto.
3. La disciplina.
4. El tipo de investigación (documental, cuantitativa, cualitativa o mixta).
5. El idioma, el estilo de citación, la extensión y el período.
6. **Qué agentes trabajarán en esa producción.** La oficina sugiere un equipo según el producto y tú lo ajustas.
7. Los datos propios, si se usa el analista de datos.
8. Si quieres aprobar el plan y el borrador antes de seguir.

## El equipo

| # | Agente | Qué hace |
|---|---|---|
| 1 | **Director de investigación** (siempre) | Preguntas, objetivos, alcance, estructura e instrucciones al equipo |
| 2 | **Metodólogo** | Diseño, criterios de inclusión y exclusión, ecuaciones de búsqueda, plan de análisis |
| 3 | **Buscador bibliográfico** | Busca en OpenAlex, Semantic Scholar y arXiv; registra cada búsqueda |
| 4 | **Cribador** | Incluye o excluye cada registro con un criterio explícito; arma el flujo PRISMA |
| 5 | **Lector-analista** | Matriz de extracción, síntesis temática, debates y vacíos |
| 6 | **Analista de datos** | Analiza tu CSV o Excel con código: descriptivos, pruebas, tablas y figuras |
| 7 | **Redactor académico** | Escribe el documento con la estructura del producto y tu estilo de citación |
| 8 | **Verificador de citas** | Comprueba con Crossref que cada referencia exista y respalde lo afirmado |
| 9 | **Revisor par** | Evalúa como revisor de revista y devuelve el texto al redactor (hasta N rondas) |

Las dependencias se resuelven solas. Por ejemplo, si eliges el verificador, se añade el redactor; si eliges el cribador, se añade el buscador.

```
Entrevista → ficha.yaml
   Director → Metodólogo → Buscador → Cribador → Lector → Analista de datos
                                                              ↓
                          ┌──────── Redactor ◄────────────────┘
                          ↓            ▲
                     Verificador ──────┤  (rondas de corrección)
                     Revisor par ──────┘
                          ↓
                   DOCUMENTO_FINAL.md
```

## Instalación

**Windows (PowerShell):**

```powershell
git clone https://github.com/miro-404/ID.git
cd ID
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -e .
copy .env.example .env
notepad .env        # pega tu ANTHROPIC_API_KEY y guarda
```

**macOS / Linux:**

```bash
git clone https://github.com/miro-404/ID.git
cd ID
python3 -m venv .venv && source .venv/bin/activate
pip install -e .
cp .env.example .env    # y completa ANTHROPIC_API_KEY
```

El archivo `.env` se lee automáticamente al ejecutar la oficina desde la carpeta del proyecto.

## Uso

```bash
oficina nueva                 # entrevista + producción
oficina nueva --solo-ficha    # solo crea la ficha, para editarla antes
oficina ejecutar producciones/<carpeta>   # ejecuta o retoma una producción
oficina agentes               # catálogo de agentes, productos y disciplinas
```

(Sin instalar el paquete, también funciona `python -m oficina ...`.)

Si la ejecución se interrumpe, `oficina ejecutar` retoma desde el último paso sin entregar.

## Qué entrega cada producción

En `producciones/<fecha>-<tema>/` quedan:

| Archivo | Contenido |
|---|---|
| `ficha.yaml` | Las decisiones de la entrevista; se puede editar y reutilizar |
| `01_plan_director.md` | Plan de investigación |
| `02_metodologia.md` | Diseño, criterios y ecuaciones de búsqueda |
| `03_informe_busqueda.md` | Informe y registro reproducible de búsquedas |
| `04_cribado.md` | Flujo PRISMA y decisión por registro |
| `05_matriz_y_sintesis.md` | Matriz de extracción y síntesis temática |
| `06_analisis_datos.md` y `figuras/` | Resultados del análisis de datos propios |
| `07_borrador_vN.md`, `08_verificacion_vN.md`, `09_revision_par_vN.md` | Historial de borradores y revisiones |
| **`DOCUMENTO_FINAL.md`** | El producto terminado |
| `corpus.json`, `registro_busquedas.json`, `uso_tokens.json` | Datos de trabajo y consumo |

Para pasar el resultado a Word: `pandoc DOCUMENTO_FINAL.md -o documento.docx`.

## Personalizar la plantilla

- **Productos, disciplinas y agentes:** `oficina/catalogo.py`.
- **Instrucciones de cada agente:** `oficina/prompts/<agente>.md`. Los principios comunes están en `_base.md`.
- **Modelo y esfuerzo por agente:** `oficina/config.py` o variables de entorno (`OFICINA_MODELO`, `OFICINA_MODELO_<AGENTE>`). Por defecto, todos usan Claude Opus 5.5 con razonamiento adaptativo y respaldo automático si el modelo declina una petición.

## Integridad académica

La oficina está diseñada para **no inventar fuentes**:

- El redactor solo puede citar fuentes del corpus encontrado por el buscador.
- Cada cita lleva oculto el identificador de su fuente.
- El verificador comprueba cada DOI en Crossref.

Aun así, el resultado es un **borrador de investigación** que debe revisar una persona responsable antes de usarlo o publicarlo. Declara el uso de IA según las normas de tu institución o de la revista.

## Pendiente

- Conectores para PubMed, ERIC, SciELO y Redalyc. Hoy se cubren en parte a través de OpenAlex.
- Lectura de texto completo en PDF de acceso abierto. Hoy se trabaja con título, resumen y metadatos.
- Exportar la bibliografía a BibTeX o RIS (Zotero, Mendeley).
