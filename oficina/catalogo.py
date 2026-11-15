"""Catálogo de la oficina: tipos de producto, disciplinas, tipos de investigación y agentes.

Este archivo es la "plantilla maestra". Para añadir un producto, una disciplina
o un agente nuevo, basta con agregarlo aquí (y su prompt en oficina/prompts/).
"""

from __future__ import annotations

from dataclasses import dataclass, field

# ---------------------------------------------------------------------------
# Agentes
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Agente:
    id: str
    nombre: str
    descripcion: str
    obligatorio: bool = False
    requiere: tuple[str, ...] = ()  # agentes de los que depende


# El orden de este diccionario es el orden de ejecución en la producción.
AGENTES: dict[str, Agente] = {
    a.id: a
    for a in [
        Agente(
            "director",
            "Director de investigación",
            "Convierte el tema en preguntas y objetivos, arma el plan y coordina.",
            obligatorio=True,
        ),
        Agente(
            "metodologo",
            "Metodólogo",
            "Define el diseño, criterios de inclusión/exclusión y ecuaciones de búsqueda.",
        ),
        Agente(
            "buscador",
            "Buscador bibliográfico",
            "Busca literatura en OpenAlex, Crossref, Semantic Scholar y arXiv; registra cada búsqueda.",
        ),
        Agente(
            "cribador",
            "Cribador",
            "Filtra fuentes por título/resumen con criterios explícitos y arma el flujo PRISMA.",
            requiere=("buscador",),
        ),
        Agente(
            "lector",
            "Lector-analista",
            "Extrae objetivo, método, muestra, hallazgos y limitaciones a una matriz; detecta vacíos.",
            requiere=("buscador",),
        ),
        Agente(
            "analista_datos",
            "Analista de datos",
            "Analiza tus datos propios (CSV/Excel) con código: descriptivos, pruebas y gráficos.",
        ),
        Agente(
            "redactor",
            "Redactor académico",
            "Escribe el documento con la estructura del producto y el estilo de citación elegido.",
        ),
        Agente(
            "verificador",
            "Verificador de citas",
            "Comprueba que cada referencia exista (DOI) y respalde lo que el texto afirma.",
            requiere=("redactor",),
        ),
        Agente(
            "revisor",
            "Revisor par",
            "Evalúa el borrador como un revisor de revista y pide correcciones al redactor.",
            requiere=("redactor",),
        ),
    ]
}

# ---------------------------------------------------------------------------
# Tipos de producto
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Producto:
    id: str
    nombre: str
    descripcion: str
    agentes_recomendados: tuple[str, ...]
    estructura: tuple[str, ...]
    extension_palabras: int = 6000


TODOS_DOCUMENTALES = ("director", "metodologo", "buscador", "cribador", "lector", "redactor", "verificador", "revisor")

PRODUCTOS: dict[str, Producto] = {
    p.id: p
    for p in [
        Producto(
            "estado_arte",
            "Estado del arte",
            "Panorama crítico de lo que se ha investigado sobre el tema.",
            ("director", "metodologo", "buscador", "lector", "redactor", "verificador", "revisor"),
            ("Introducción", "Metodología de la revisión", "Desarrollo por ejes temáticos",
             "Vacíos y tendencias", "Conclusiones", "Referencias"),
            7000,
        ),
        Producto(
            "revision_sistematica",
            "Revisión sistemática (PRISMA)",
            "Revisión reproducible con protocolo, cribado y síntesis de evidencia.",
            TODOS_DOCUMENTALES,
            ("Resumen", "Introducción", "Métodos (protocolo, fuentes, criterios, cribado)",
             "Resultados (flujo PRISMA, características de estudios, síntesis)",
             "Discusión", "Limitaciones", "Conclusiones", "Referencias"),
            8000,
        ),
        Producto(
            "revision_alcance",
            "Revisión de alcance (scoping review)",
            "Mapea la extensión y naturaleza de la evidencia disponible.",
            TODOS_DOCUMENTALES,
            ("Resumen", "Introducción", "Métodos (PRISMA-ScR)", "Resultados (mapa de evidencia)",
             "Discusión", "Conclusiones", "Referencias"),
            7000,
        ),
        Producto(
            "articulo",
            "Artículo científico (IMRyD)",
            "Artículo listo para someter a revista.",
            ("director", "metodologo", "buscador", "lector", "redactor", "verificador", "revisor"),
            ("Título", "Resumen y palabras clave", "Introducción", "Métodos", "Resultados",
             "Discusión", "Conclusiones", "Referencias"),
            6000,
        ),
        Producto(
            "capitulo_tesis",
            "Capítulo de tesis (marco teórico)",
            "Marco teórico/conceptual sólidamente referenciado.",
            ("director", "buscador", "lector", "redactor", "verificador", "revisor"),
            ("Introducción al capítulo", "Antecedentes", "Bases teóricas", "Definición de conceptos clave",
             "Síntesis del capítulo", "Referencias"),
            9000,
        ),
        Producto(
            "proyecto",
            "Proyecto / anteproyecto de investigación",
            "Propuesta con problema, justificación, objetivos y metodología.",
            ("director", "metodologo", "buscador", "lector", "redactor", "verificador", "revisor"),
            ("Título", "Planteamiento del problema", "Justificación", "Objetivos (general y específicos)",
             "Marco teórico breve", "Metodología", "Cronograma", "Resultados esperados", "Referencias"),
            5000,
        ),
        Producto(
            "ensayo",
            "Ensayo académico",
            "Texto argumentativo con tesis defendida con evidencia.",
            ("director", "buscador", "lector", "redactor", "verificador", "revisor"),
            ("Introducción y tesis", "Argumentos", "Contraargumentos y réplica", "Conclusión", "Referencias"),
            3500,
        ),
        Producto(
            "informe_datos",
            "Informe de investigación con datos propios",
            "Reporte de un estudio empírico a partir de tus datos.",
            ("director", "metodologo", "buscador", "lector", "analista_datos", "redactor", "verificador", "revisor"),
            ("Resumen", "Introducción", "Métodos", "Resultados", "Discusión", "Conclusiones", "Referencias", "Anexos"),
            6000,
        ),
    ]
}

# ---------------------------------------------------------------------------
# Disciplinas
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Disciplina:
    id: str
    nombre: str
    estilo_citacion: str
    bases_sugeridas: tuple[str, ...] = field(default=())


DISCIPLINAS: dict[str, Disciplina] = {
    d.id: d
    for d in [
        Disciplina("salud", "Ciencias de la salud", "Vancouver", ("PubMed", "OpenAlex", "SciELO")),
        Disciplina("educacion", "Educación", "APA 7", ("OpenAlex", "ERIC", "SciELO", "Redalyc")),
        Disciplina("sociales", "Ciencias sociales y humanas", "APA 7", ("OpenAlex", "SciELO", "Redalyc")),
        Disciplina("psicologia", "Psicología", "APA 7", ("OpenAlex", "PubMed", "SciELO")),
        Disciplina("ingenieria", "Ingeniería y tecnología", "IEEE", ("OpenAlex", "arXiv", "Crossref")),
        Disciplina("computacion", "Ciencias de la computación", "IEEE", ("OpenAlex", "arXiv", "Semantic Scholar")),
        Disciplina("economia", "Economía y administración", "APA 7", ("OpenAlex", "RePEc", "SciELO")),
        Disciplina("derecho", "Derecho", "APA 7", ("OpenAlex", "SciELO", "Redalyc")),
        Disciplina("ambientales", "Ciencias ambientales y agrarias", "APA 7", ("OpenAlex", "Crossref", "SciELO")),
        Disciplina("basicas", "Ciencias básicas (física, química, biología, matemática)", "APA 7",
                   ("OpenAlex", "arXiv", "PubMed")),
    ]
}

TIPOS_INVESTIGACION: dict[str, str] = {
    "documental": "Documental / bibliográfica (sin datos propios)",
    "cuantitativa": "Empírica cuantitativa",
    "cualitativa": "Empírica cualitativa",
    "mixta": "Mixta",
}

ESTILOS_CITACION = ("APA 7", "Vancouver", "IEEE", "Chicago autor-fecha", "MLA 9", "ISO 690")


def resolver_dependencias(seleccion: list[str]) -> tuple[list[str], list[str]]:
    """Devuelve (agentes_finales_en_orden, avisos).

    Añade los obligatorios y las dependencias que falten, y mantiene el orden canónico.
    """
    elegidos = set(seleccion)
    avisos: list[str] = []
    for a in AGENTES.values():
        if a.obligatorio and a.id not in elegidos:
            elegidos.add(a.id)
            avisos.append(f"Se añadió «{a.nombre}» porque es obligatorio.")
    cambio = True
    while cambio:
        cambio = False
        for aid in list(elegidos):
            for dep in AGENTES[aid].requiere:
                if dep not in elegidos:
                    elegidos.add(dep)
                    cambio = True
                    avisos.append(
                        f"Se añadió «{AGENTES[dep].nombre}» porque «{AGENTES[aid].nombre}» lo necesita."
                    )
    return [aid for aid in AGENTES if aid in elegidos], avisos
