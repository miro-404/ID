# Catálogo de la oficina (plantilla de producción)

Este archivo define las opciones de la entrevista inicial. Para añadir un producto, disciplina o agente, edítalo aquí (y crea el agente en `.claude/agents/`).

## Tipos de producto

| id | Producto | Agentes recomendados | Estructura base | Extensión |
|---|---|---|---|---|
| estado_arte | Estado del arte | metodologo, buscador, lector, redactor, verificador, revisor | Introducción; Metodología de la revisión; Desarrollo por ejes temáticos; Vacíos y tendencias; Conclusiones; Referencias | 7000 |
| revision_sistematica | Revisión sistemática (PRISMA 2020) | metodologo, buscador, cribador, lector, redactor, verificador, revisor | Resumen; Introducción; Métodos (protocolo, fuentes, criterios, cribado); Resultados (flujo PRISMA, características, síntesis); Discusión; Limitaciones; Conclusiones; Referencias | 8000 |
| revision_alcance | Revisión de alcance (PRISMA-ScR) | metodologo, buscador, cribador, lector, redactor, verificador, revisor | Resumen; Introducción; Métodos; Resultados (mapa de evidencia); Discusión; Conclusiones; Referencias | 7000 |
| articulo | Artículo científico (IMRyD) | metodologo, buscador, lector, redactor, verificador, revisor | Título; Resumen y palabras clave; Introducción; Métodos; Resultados; Discusión; Conclusiones; Referencias | 6000 |
| capitulo_tesis | Capítulo de tesis (marco teórico) | buscador, lector, redactor, verificador, revisor | Introducción al capítulo; Antecedentes; Bases teóricas; Definición de conceptos clave; Síntesis; Referencias | 9000 |
| proyecto | Proyecto / anteproyecto de investigación | metodologo, buscador, lector, redactor, verificador, revisor | Título; Planteamiento del problema; Justificación; Objetivos; Marco teórico breve; Metodología; Cronograma; Resultados esperados; Referencias | 5000 |
| ensayo | Ensayo académico | buscador, lector, redactor, verificador, revisor | Introducción y tesis; Argumentos; Contraargumentos y réplica; Conclusión; Referencias | 3500 |
| informe_datos | Informe de investigación con datos propios | metodologo, buscador, lector, analista-datos, redactor, verificador, revisor | Resumen; Introducción; Métodos; Resultados; Discusión; Conclusiones; Referencias; Anexos | 6000 |

El **director** participa siempre. Si el tipo de investigación no es documental, se recomienda además el **analista-datos**.

## Disciplinas

| id | Disciplina | Estilo de citación sugerido | Bases sugeridas |
|---|---|---|---|
| salud | Ciencias de la salud | Vancouver | OpenAlex, PubMed (vía OpenAlex), Semantic Scholar |
| educacion | Educación | APA 7 | OpenAlex (incluye SciELO y Redalyc) |
| sociales | Ciencias sociales y humanas | APA 7 | OpenAlex (incluye SciELO y Redalyc) |
| psicologia | Psicología | APA 7 | OpenAlex, Semantic Scholar |
| ingenieria | Ingeniería y tecnología | IEEE | OpenAlex, arXiv, Semantic Scholar |
| computacion | Ciencias de la computación | IEEE | OpenAlex, arXiv, Semantic Scholar |
| economia | Economía y administración | APA 7 | OpenAlex, arXiv (econ) |
| derecho | Derecho | APA 7 | OpenAlex |
| ambientales | Ciencias ambientales y agrarias | APA 7 | OpenAlex, Semantic Scholar |
| basicas | Ciencias básicas | APA 7 | OpenAlex, arXiv, Semantic Scholar |

También se admite una disciplina escrita libremente.

## Tipos de investigación

- **documental**: documental / bibliográfica, sin datos propios.
- **cuantitativa**: empírica cuantitativa.
- **cualitativa**: empírica cualitativa.
- **mixta**: mixta.

## Estilos de citación

APA 7 · Vancouver · IEEE · Chicago autor-fecha · MLA 9 · ISO 690

## Agentes y dependencias (en orden de ejecución)

| Orden | Agente (subagente) | Función | Requiere |
|---|---|---|---|
| 1 | director (el coordinador) | Plan: preguntas, objetivos, alcance, estructura | — (obligatorio) |
| 2 | metodologo | Diseño, criterios, ecuaciones de búsqueda, plan de análisis | — |
| 3 | buscador | Búsqueda en OpenAlex, Semantic Scholar, arXiv | — |
| 4 | cribador | Inclusión/exclusión y flujo PRISMA | buscador |
| 5 | lector | Matriz de extracción y síntesis | buscador |
| 6 | analista-datos | Análisis de datos propios con Python | archivo de datos |
| 7 | redactor | Documento completo | — |
| 8 | verificador | Verificación de cada cita | redactor |
| 9 | revisor | Revisión par y rondas de corrección | redactor |

## Archivos de cada producción (`producciones/<fecha>-<tema>/`)

| Archivo | Lo escribe |
|---|---|
| ficha.md | coordinador (entrevista) |
| 01_plan_director.md | director |
| 02_metodologia.md | metodologo |
| 03_informe_busqueda.md, corpus.json, registro_busquedas.json | buscador |
| 04_cribado.md | cribador |
| 05_matriz_y_sintesis.md | lector |
| 06_analisis_datos.md, figuras/ | analista-datos |
| 07_borrador_vN.md | redactor |
| 08_verificacion_vN.md | verificador |
| 09_revision_par_vN.md | revisor |
| DOCUMENTO_FINAL.md | coordinador |
