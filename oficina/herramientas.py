"""Herramientas académicas que usan los agentes.

Todas consultan fuentes abiertas y gratuitas. Cada resultado se acumula en el
CORPUS de la producción y cada búsqueda queda en el REGISTRO (reproducibilidad).
"""

from __future__ import annotations

import json
import os
import xml.etree.ElementTree as ET
from datetime import datetime
from typing import Any

import httpx2 as httpx
from anthropic import beta_tool

_UA = {"User-Agent": "oficina-agentes-academicos/0.1 (+https://github.com)"}
_TIMEOUT = 30.0

# Estado compartido de la producción en curso (lo inicializa el orquestador).
CORPUS: dict[str, dict[str, Any]] = {}
REGISTRO: list[dict[str, Any]] = []


def reiniciar(corpus: dict | None = None, registro: list | None = None) -> None:
    CORPUS.clear()
    CORPUS.update(corpus or {})
    REGISTRO.clear()
    REGISTRO.extend(registro or [])


def _get(url: str, params: dict | None = None, headers: dict | None = None) -> httpx.Response:
    h = dict(_UA)
    if headers:
        h.update(headers)
    r = httpx.get(url, params=params, headers=h, timeout=_TIMEOUT, follow_redirects=True)
    r.raise_for_status()
    return r


def _clave(doi: str | None, respaldo: str) -> str:
    return f"doi:{doi.lower()}" if doi else respaldo


def _agregar(item: dict[str, Any]) -> dict[str, Any]:
    clave = item["id"]
    previo = CORPUS.get(clave, {})
    combinado = {**item, **{k: v for k, v in previo.items() if v}}
    combinado["fuentes"] = sorted(set(previo.get("fuentes", [])) | set(item.get("fuentes", [])))
    CORPUS[clave] = combinado
    return combinado


def _registrar(base: str, consulta: str, filtros: str, total: int | None, devueltos: int) -> None:
    REGISTRO.append(
        {
            "fecha": datetime.now().isoformat(timespec="seconds"),
            "base": base,
            "consulta": consulta,
            "filtros": filtros,
            "total_reportado": total,
            "devueltos": devueltos,
        }
    )


def _resumen_corto(item: dict[str, Any]) -> dict[str, Any]:
    resumen = item.get("resumen") or ""
    return {
        "id": item["id"],
        "titulo": item.get("titulo"),
        "anio": item.get("anio"),
        "autores": item.get("autores", [])[:4],
        "revista": item.get("revista"),
        "citas": item.get("citas"),
        "resumen": resumen[:600] + ("…" if len(resumen) > 600 else ""),
    }


def _abstract_openalex(inv: dict[str, list[int]] | None) -> str:
    if not inv:
        return ""
    pos = sorted((i, w) for w, idxs in inv.items() for i in idxs)
    return " ".join(w for _, w in pos)


def _openalex_a_item(w: dict[str, Any]) -> dict[str, Any]:
    doi = (w.get("doi") or "").replace("https://doi.org/", "") or None
    loc = w.get("primary_location") or {}
    fuente = loc.get("source") or {}
    oa = w.get("open_access") or {}
    return {
        "id": _clave(doi, w.get("id", "")),
        "doi": doi,
        "titulo": w.get("display_name"),
        "anio": w.get("publication_year"),
        "autores": [a["author"]["display_name"] for a in w.get("authorships", []) if a.get("author")],
        "revista": fuente.get("display_name"),
        "tipo": w.get("type"),
        "idioma": w.get("language"),
        "citas": w.get("cited_by_count"),
        "acceso_abierto": oa.get("is_oa"),
        "url_pdf": oa.get("oa_url"),
        "resumen": _abstract_openalex(w.get("abstract_inverted_index")),
        "fuentes": ["OpenAlex"],
    }


# ---------------------------------------------------------------------------
# Herramientas expuestas a los agentes
# ---------------------------------------------------------------------------


@beta_tool
def buscar_openalex(consulta: str, desde_anio: int = 0, hasta_anio: int = 0, idioma: str = "", maximo: int = 25) -> str:
    """Busca trabajos académicos en OpenAlex (base abierta, multidisciplinaria, >250M documentos).

    Args:
        consulta: Términos de búsqueda en texto libre (OpenAlex no usa operadores booleanos complejos; usa términos clave).
        desde_anio: Año mínimo de publicación (0 = sin límite).
        hasta_anio: Año máximo de publicación (0 = sin límite).
        idioma: Código ISO 639-1 para filtrar por idioma (ej. "es", "en"); vacío = todos.
        maximo: Número de resultados a devolver (1-50).
    """
    filtros = []
    if desde_anio:
        filtros.append(f"from_publication_date:{desde_anio}-01-01")
    if hasta_anio:
        filtros.append(f"to_publication_date:{hasta_anio}-12-31")
    if idioma:
        filtros.append(f"language:{idioma}")
    params: dict[str, Any] = {"search": consulta, "per-page": max(1, min(maximo, 50))}
    if filtros:
        params["filter"] = ",".join(filtros)
    if os.getenv("OPENALEX_EMAIL"):
        params["mailto"] = os.environ["OPENALEX_EMAIL"]
    try:
        data = _get("https://api.openalex.org/works", params).json()
    except httpx.HTTPError as e:
        return f"Error consultando OpenAlex: {e}"
    items = [_agregar(_openalex_a_item(w)) for w in data.get("results", [])]
    _registrar("OpenAlex", consulta, params.get("filter", ""), data.get("meta", {}).get("count"), len(items))
    return json.dumps(
        {"total_en_base": data.get("meta", {}).get("count"), "resultados": [_resumen_corto(i) for i in items]},
        ensure_ascii=False,
    )


@beta_tool
def buscar_semantic_scholar(consulta: str, desde_anio: int = 0, maximo: int = 20) -> str:
    """Busca artículos en Semantic Scholar (fuerte en computación, biomedicina y ciencias).

    Args:
        consulta: Términos de búsqueda.
        desde_anio: Año mínimo de publicación (0 = sin límite).
        maximo: Número de resultados (1-50).
    """
    params: dict[str, Any] = {
        "query": consulta,
        "limit": max(1, min(maximo, 50)),
        "fields": "title,year,authors,abstract,externalIds,citationCount,venue,openAccessPdf",
    }
    if desde_anio:
        params["year"] = f"{desde_anio}-"
    headers = {"x-api-key": os.environ["SEMANTIC_SCHOLAR_API_KEY"]} if os.getenv("SEMANTIC_SCHOLAR_API_KEY") else None
    try:
        data = _get("https://api.semanticscholar.org/graph/v1/paper/search", params, headers).json()
    except httpx.HTTPError as e:
        return f"Error consultando Semantic Scholar (puede ser límite de tasa; reintenta más tarde u otra base): {e}"
    items = []
    for p in data.get("data", []):
        doi = (p.get("externalIds") or {}).get("DOI")
        items.append(
            _agregar(
                {
                    "id": _clave(doi, f"s2:{p.get('paperId')}"),
                    "doi": doi,
                    "titulo": p.get("title"),
                    "anio": p.get("year"),
                    "autores": [a.get("name") for a in p.get("authors", [])],
                    "revista": p.get("venue"),
                    "citas": p.get("citationCount"),
                    "url_pdf": (p.get("openAccessPdf") or {}).get("url"),
                    "resumen": p.get("abstract") or "",
                    "fuentes": ["Semantic Scholar"],
                }
            )
        )
    _registrar("Semantic Scholar", consulta, params.get("year", ""), data.get("total"), len(items))
    return json.dumps({"total_en_base": data.get("total"), "resultados": [_resumen_corto(i) for i in items]}, ensure_ascii=False)


@beta_tool
def buscar_arxiv(consulta: str, maximo: int = 20) -> str:
    """Busca preprints en arXiv (física, matemática, computación, estadística, etc.).

    Args:
        consulta: Términos de búsqueda; admite sintaxis de arXiv como ti:, abs:, AND, OR.
        maximo: Número de resultados (1-50).
    """
    params = {"search_query": f"all:{consulta}" if ":" not in consulta else consulta, "max_results": max(1, min(maximo, 50))}
    try:
        xml = _get("https://export.arxiv.org/api/query", params).text
    except httpx.HTTPError as e:
        return f"Error consultando arXiv: {e}"
    ns = {"a": "http://www.w3.org/2005/Atom", "arxiv": "http://arxiv.org/schemas/atom"}
    raiz = ET.fromstring(xml)
    items = []
    for e in raiz.findall("a:entry", ns):
        doi_el = e.find("arxiv:doi", ns)
        doi = doi_el.text if doi_el is not None else None
        arxiv_id = (e.findtext("a:id", default="", namespaces=ns)).rsplit("/", 1)[-1]
        items.append(
            _agregar(
                {
                    "id": _clave(doi, f"arxiv:{arxiv_id}"),
                    "doi": doi,
                    "titulo": " ".join((e.findtext("a:title", default="", namespaces=ns)).split()),
                    "anio": int((e.findtext("a:published", default="0000", namespaces=ns))[:4]),
                    "autores": [a.findtext("a:name", default="", namespaces=ns) for a in e.findall("a:author", ns)],
                    "revista": "arXiv (preprint)",
                    "url_pdf": f"https://arxiv.org/pdf/{arxiv_id}",
                    "resumen": " ".join((e.findtext("a:summary", default="", namespaces=ns)).split()),
                    "fuentes": ["arXiv"],
                }
            )
        )
    _registrar("arXiv", consulta, "", None, len(items))
    return json.dumps({"resultados": [_resumen_corto(i) for i in items]}, ensure_ascii=False)


@beta_tool
def verificar_doi(doi: str) -> str:
    """Verifica en Crossref que un DOI exista y devuelve sus metadatos oficiales (título, autores, año, revista).

    Args:
        doi: El DOI, con o sin prefijo https://doi.org/.
    """
    doi = doi.strip().replace("https://doi.org/", "").replace("http://dx.doi.org/", "")
    try:
        m = _get(f"https://api.crossref.org/works/{doi}").json()["message"]
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            return json.dumps({"doi": doi, "existe": False}, ensure_ascii=False)
        return f"Error consultando Crossref: {e}"
    except httpx.HTTPError as e:
        return f"Error consultando Crossref: {e}"
    fecha = (m.get("issued") or {}).get("date-parts", [[None]])[0]
    return json.dumps(
        {
            "doi": doi,
            "existe": True,
            "titulo": (m.get("title") or [""])[0],
            "autores": [f"{a.get('family', '')}, {a.get('given', '')}".strip(", ") for a in m.get("author", [])],
            "anio": fecha[0] if fecha else None,
            "revista": (m.get("container-title") or [""])[0],
            "volumen": m.get("volume"),
            "numero": m.get("issue"),
            "paginas": m.get("page"),
            "editorial": m.get("publisher"),
            "tipo": m.get("type"),
        },
        ensure_ascii=False,
    )


@beta_tool
def leer_fuente(id: str) -> str:
    """Devuelve la ficha completa (con resumen íntegro) de una fuente ya encontrada en el corpus.

    Args:
        id: Identificador de la fuente en el corpus (ej. "doi:10.1000/xyz" o "arxiv:2401.00001").
    """
    item = CORPUS.get(id)
    if not item:
        return f"No hay ninguna fuente con id {id!r} en el corpus."
    return json.dumps(item, ensure_ascii=False)


@beta_tool
def listar_corpus(solo_incluidas: bool = False) -> str:
    """Lista las fuentes reunidas hasta ahora en el corpus de esta producción.

    Args:
        solo_incluidas: Si es true, devuelve solo las fuentes que el cribado marcó como incluidas.
    """
    items = [i for i in CORPUS.values() if not solo_incluidas or i.get("decision") == "incluida"]
    return json.dumps([_resumen_corto(i) | {"decision": i.get("decision")} for i in items], ensure_ascii=False)


HERRAMIENTAS_BUSQUEDA = [buscar_openalex, buscar_semantic_scholar, buscar_arxiv]
