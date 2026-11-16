#!/usr/bin/env python3
"""Herramientas académicas para los subagentes de la oficina (solo biblioteca estándar).

No requiere instalar nada: basta Python 3.9+. Consulta fuentes abiertas y gratuitas
y guarda todo en la carpeta de la producción:
  corpus.json             fuentes encontradas (sin duplicados, unidas por DOI)
  registro_busquedas.json cada búsqueda realizada (reproducibilidad)

Uso (desde la raíz del repositorio):
  python herramientas/academico.py openalex  --prod DIR --q "términos" [--desde 2018] [--hasta 2026] [--idioma es] [--max 25]
  python herramientas/academico.py semantic  --prod DIR --q "términos" [--desde 2018] [--max 20]
  python herramientas/academico.py arxiv     --prod DIR --q "términos" [--max 20]
  python herramientas/academico.py doi       --doi 10.xxxx/yyyy
  python herramientas/academico.py corpus    --prod DIR [--incluidas] [--completo] [--pendientes]
  python herramientas/academico.py fuente    --prod DIR --id "doi:10.xxxx/yyyy"
  python herramientas/academico.py cribar    --prod DIR --archivo decisiones.json
  python herramientas/academico.py prisma    --prod DIR
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path
from typing import Any

UA = "oficina-agentes-academicos/0.2 (investigacion academica; https://github.com/miro-404/ID)"
TIMEOUT = 40

for _f in (sys.stdout, sys.stderr):
    try:
        _f.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass


# --------------------------------------------------------------------- red


def _get(url: str, params: dict | None = None, headers: dict | None = None, intentos: int = 3) -> bytes:
    if params:
        url += "?" + urllib.parse.urlencode(params)
    h = {"User-Agent": UA, **(headers or {})}
    for i in range(intentos):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=h), timeout=TIMEOUT) as r:
                return r.read()
        except urllib.error.HTTPError as e:
            if e.code in (429, 500, 502, 503, 504) and i < intentos - 1:
                time.sleep(3 * (i + 1))
                continue
            raise
        except urllib.error.URLError:
            if i < intentos - 1:
                time.sleep(3 * (i + 1))
                continue
            raise
    raise RuntimeError("inalcanzable")


# ------------------------------------------------------------- estado


class Produccion:
    def __init__(self, carpeta: str):
        self.dir = Path(carpeta)
        self.dir.mkdir(parents=True, exist_ok=True)
        self.p_corpus = self.dir / "corpus.json"
        self.p_registro = self.dir / "registro_busquedas.json"
        self.corpus: dict[str, dict[str, Any]] = self._leer(self.p_corpus, {})
        self.registro: list[dict[str, Any]] = self._leer(self.p_registro, [])

    @staticmethod
    def _leer(p: Path, defecto: Any) -> Any:
        return json.loads(p.read_text(encoding="utf-8")) if p.exists() else defecto

    def guardar(self) -> None:
        self.p_corpus.write_text(json.dumps(self.corpus, ensure_ascii=False, indent=1), encoding="utf-8")
        self.p_registro.write_text(json.dumps(self.registro, ensure_ascii=False, indent=1), encoding="utf-8")

    def agregar(self, item: dict[str, Any]) -> tuple[dict[str, Any], bool]:
        clave = item["id"]
        previo = self.corpus.get(clave)
        if previo is None:
            self.corpus[clave] = item
            return item, True
        for k, v in item.items():
            if v and not previo.get(k):
                previo[k] = v
        previo["fuentes"] = sorted(set(previo.get("fuentes", [])) | set(item.get("fuentes", [])))
        return previo, False

    def registrar(self, base: str, consulta: str, filtros: str, total: Any, devueltos: int, nuevos: int) -> None:
        self.registro.append({
            "fecha": datetime.now().isoformat(timespec="seconds"),
            "base": base, "consulta": consulta, "filtros": filtros,
            "total_en_base": total, "recuperados": devueltos, "nuevos_en_corpus": nuevos,
        })


def _clave(doi: str | None, respaldo: str) -> str:
    return f"doi:{doi.lower()}" if doi else respaldo


def _corto(i: dict[str, Any], largo_resumen: int = 350) -> dict[str, Any]:
    res = i.get("resumen") or ""
    d = {
        "id": i["id"], "titulo": i.get("titulo"), "anio": i.get("anio"),
        "autores": (i.get("autores") or [])[:3] + (["et al."] if len(i.get("autores") or []) > 3 else []),
        "revista": i.get("revista"), "citas": i.get("citas"),
    }
    if largo_resumen:
        d["resumen"] = res[:largo_resumen] + ("…" if len(res) > largo_resumen else "")
    if i.get("decision"):
        d["decision"] = i["decision"]
    return d


def _imprimir(obj: Any) -> None:
    print(json.dumps(obj, ensure_ascii=False, indent=1))


# ------------------------------------------------------------ fuentes


def _abstract_openalex(inv: dict | None) -> str:
    if not inv:
        return ""
    return " ".join(w for _, w in sorted((i, w) for w, idx in inv.items() for i in idx))


def cmd_openalex(a: argparse.Namespace) -> None:
    prod = Produccion(a.prod)
    filtros = []
    if a.desde:
        filtros.append(f"from_publication_date:{a.desde}-01-01")
    if a.hasta:
        filtros.append(f"to_publication_date:{a.hasta}-12-31")
    if a.idioma:
        filtros.append(f"language:{a.idioma}")
    params: dict[str, Any] = {"search": a.q, "per-page": max(1, min(a.max, 50))}
    if filtros:
        params["filter"] = ",".join(filtros)
    if os.getenv("OPENALEX_EMAIL"):
        params["mailto"] = os.environ["OPENALEX_EMAIL"]
    data = json.loads(_get("https://api.openalex.org/works", params))
    salida, nuevos = [], 0
    for w in data.get("results", []):
        doi = (w.get("doi") or "").replace("https://doi.org/", "") or None
        loc = w.get("primary_location") or {}
        oa = w.get("open_access") or {}
        item, es_nuevo = prod.agregar({
            "id": _clave(doi, w.get("id", "")), "doi": doi, "titulo": w.get("display_name"),
            "anio": w.get("publication_year"),
            "autores": [x["author"]["display_name"] for x in w.get("authorships", []) if x.get("author")],
            "revista": (loc.get("source") or {}).get("display_name"), "tipo": w.get("type"),
            "idioma": w.get("language"), "citas": w.get("cited_by_count"),
            "acceso_abierto": oa.get("is_oa"), "url_pdf": oa.get("oa_url"),
            "resumen": _abstract_openalex(w.get("abstract_inverted_index")), "fuentes": ["OpenAlex"],
        })
        nuevos += es_nuevo
        salida.append(_corto(item))
    total = data.get("meta", {}).get("count")
    prod.registrar("OpenAlex", a.q, params.get("filter", ""), total, len(salida), nuevos)
    prod.guardar()
    _imprimir({"total_en_base": total, "recuperados": len(salida), "nuevos": nuevos,
               "corpus_total": len(prod.corpus), "resultados": salida})


def cmd_semantic(a: argparse.Namespace) -> None:
    prod = Produccion(a.prod)
    params: dict[str, Any] = {
        "query": a.q, "limit": max(1, min(a.max, 50)),
        "fields": "title,year,authors,abstract,externalIds,citationCount,venue,openAccessPdf,publicationTypes",
    }
    if a.desde:
        params["year"] = f"{a.desde}-"
    headers = {"x-api-key": os.environ["SEMANTIC_SCHOLAR_API_KEY"]} if os.getenv("SEMANTIC_SCHOLAR_API_KEY") else None
    data = json.loads(_get("https://api.semanticscholar.org/graph/v1/paper/search", params, headers))
    salida, nuevos = [], 0
    for p in data.get("data") or []:
        doi = (p.get("externalIds") or {}).get("DOI")
        item, es_nuevo = prod.agregar({
            "id": _clave(doi, f"s2:{p.get('paperId')}"), "doi": doi, "titulo": p.get("title"),
            "anio": p.get("year"), "autores": [x.get("name") for x in p.get("authors", [])],
            "revista": p.get("venue"), "tipo": ", ".join(p.get("publicationTypes") or []) or None,
            "citas": p.get("citationCount"), "url_pdf": (p.get("openAccessPdf") or {}).get("url"),
            "resumen": p.get("abstract") or "", "fuentes": ["Semantic Scholar"],
        })
        nuevos += es_nuevo
        salida.append(_corto(item))
    prod.registrar("Semantic Scholar", a.q, params.get("year", ""), data.get("total"), len(salida), nuevos)
    prod.guardar()
    _imprimir({"total_en_base": data.get("total"), "recuperados": len(salida), "nuevos": nuevos,
               "corpus_total": len(prod.corpus), "resultados": salida})


def cmd_arxiv(a: argparse.Namespace) -> None:
    prod = Produccion(a.prod)
    q = a.q if ":" in a.q else f"all:{a.q}"
    raiz = ET.fromstring(_get("https://export.arxiv.org/api/query", {"search_query": q, "max_results": max(1, min(a.max, 50))}))
    ns = {"a": "http://www.w3.org/2005/Atom", "arxiv": "http://arxiv.org/schemas/atom"}
    salida, nuevos = [], 0
    for e in raiz.findall("a:entry", ns):
        doi_el = e.find("arxiv:doi", ns)
        doi = doi_el.text if doi_el is not None else None
        aid = e.findtext("a:id", default="", namespaces=ns).rsplit("/", 1)[-1]
        item, es_nuevo = prod.agregar({
            "id": _clave(doi, f"arxiv:{aid}"), "doi": doi,
            "titulo": " ".join(e.findtext("a:title", default="", namespaces=ns).split()),
            "anio": int(e.findtext("a:published", default="0000", namespaces=ns)[:4]),
            "autores": [x.findtext("a:name", default="", namespaces=ns) for x in e.findall("a:author", ns)],
            "revista": "arXiv (preprint, sin revisión por pares)", "tipo": "preprint",
            "url_pdf": f"https://arxiv.org/pdf/{aid}",
            "resumen": " ".join(e.findtext("a:summary", default="", namespaces=ns).split()), "fuentes": ["arXiv"],
        })
        nuevos += es_nuevo
        salida.append(_corto(item))
    prod.registrar("arXiv", a.q, "", None, len(salida), nuevos)
    prod.guardar()
    _imprimir({"recuperados": len(salida), "nuevos": nuevos, "corpus_total": len(prod.corpus), "resultados": salida})


def cmd_doi(a: argparse.Namespace) -> None:
    doi = a.doi.strip()
    for pref in ("https://doi.org/", "http://doi.org/", "https://dx.doi.org/", "http://dx.doi.org/", "doi:"):
        if doi.lower().startswith(pref):
            doi = doi[len(pref):]
    try:
        m = json.loads(_get(f"https://api.crossref.org/works/{urllib.parse.quote(doi)}"))["message"]
    except urllib.error.HTTPError as e:
        if e.code == 404:
            _imprimir({"doi": doi, "existe": False})
            return
        raise
    fecha = ((m.get("issued") or {}).get("date-parts") or [[None]])[0]
    _imprimir({
        "doi": doi, "existe": True, "titulo": (m.get("title") or [""])[0],
        "autores": [f"{x.get('family', '')}, {x.get('given', '')}".strip(", ") for x in m.get("author", [])],
        "anio": fecha[0] if fecha else None, "revista": (m.get("container-title") or [""])[0],
        "volumen": m.get("volume"), "numero": m.get("issue"), "paginas": m.get("page"),
        "editorial": m.get("publisher"), "tipo": m.get("type"),
    })


def cmd_corpus(a: argparse.Namespace) -> None:
    prod = Produccion(a.prod)
    items = list(prod.corpus.values())
    if a.incluidas:
        items = [i for i in items if i.get("decision", "incluida") == "incluida"]
    if a.pendientes:
        items = [i for i in items if not i.get("decision")]
    if a.desde_n or a.hasta_n:
        items = items[a.desde_n : a.hasta_n or None]
    if a.completo:
        _imprimir(items)
    else:
        _imprimir({"total": len(items), "fuentes": [_corto(i, 0 if a.sin_resumen else 350) for i in items]})


def cmd_fuente(a: argparse.Namespace) -> None:
    prod = Produccion(a.prod)
    item = prod.corpus.get(a.id) or prod.corpus.get(a.id.lower())
    _imprimir(item if item else {"error": f"No hay ninguna fuente con id {a.id!r} en el corpus."})


def cmd_cribar(a: argparse.Namespace) -> None:
    """Aplica decisiones de cribado: JSON con lista de {id, decision, criterio, motivo}."""
    prod = Produccion(a.prod)
    decisiones = json.loads(Path(a.archivo).read_text(encoding="utf-8"))
    aplicadas, faltan = 0, []
    for d in decisiones:
        item = prod.corpus.get(d["id"])
        if not item:
            faltan.append(d["id"])
            continue
        if d["decision"] not in ("incluida", "excluida", "duplicado"):
            faltan.append(f"{d['id']} (decisión no válida: {d['decision']})")
            continue
        item["decision"] = d["decision"]
        item["motivo_cribado"] = f"{d.get('criterio', '')}: {d.get('motivo', '')}".strip(": ")
        aplicadas += 1
    prod.guardar()
    pendientes = sum(1 for i in prod.corpus.values() if not i.get("decision"))
    _imprimir({"aplicadas": aplicadas, "ids_no_encontrados": faltan, "pendientes_de_decision": pendientes})


def cmd_prisma(a: argparse.Namespace) -> None:
    prod = Produccion(a.prod)
    items = list(prod.corpus.values())
    n = len(items)
    dup = sum(1 for i in items if i.get("decision") == "duplicado")
    exc = sum(1 for i in items if i.get("decision") == "excluida")
    inc = sum(1 for i in items if i.get("decision") == "incluida")
    pend = n - dup - exc - inc
    por_base: dict[str, int] = {}
    for r in prod.registro:
        por_base[r["base"]] = por_base.get(r["base"], 0) + r.get("recuperados", 0)
    print("Registros recuperados por base: " + ", ".join(f"{k}: {v}" for k, v in por_base.items()))
    print(f"""```
Registros identificados (únicos) ...... {n}
  └ Duplicados eliminados ............. {dup}
Registros cribados .................... {n - dup}
  └ Excluidos por título/resumen ...... {exc}
Estudios incluidos .................... {inc}
Sin decisión .......................... {pend}
```""")


# --------------------------------------------------------------- main


def main() -> None:
    ap = argparse.ArgumentParser(description="Herramientas académicas de la oficina")
    sub = ap.add_subparsers(dest="cmd", required=True)

    def con_prod(nombre: str) -> argparse.ArgumentParser:
        p = sub.add_parser(nombre)
        p.add_argument("--prod", required=True, help="Carpeta de la producción")
        return p

    p = con_prod("openalex"); p.add_argument("--q", required=True); p.add_argument("--desde", type=int, default=0)
    p.add_argument("--hasta", type=int, default=0); p.add_argument("--idioma", default=""); p.add_argument("--max", type=int, default=25)
    p = con_prod("semantic"); p.add_argument("--q", required=True); p.add_argument("--desde", type=int, default=0)
    p.add_argument("--max", type=int, default=20)
    p = con_prod("arxiv"); p.add_argument("--q", required=True); p.add_argument("--max", type=int, default=20)
    p = sub.add_parser("doi"); p.add_argument("--doi", required=True)
    p = con_prod("corpus"); p.add_argument("--incluidas", action="store_true"); p.add_argument("--pendientes", action="store_true")
    p.add_argument("--completo", action="store_true"); p.add_argument("--sin-resumen", action="store_true")
    p.add_argument("--desde-n", type=int, default=0); p.add_argument("--hasta-n", type=int, default=0)
    p = con_prod("fuente"); p.add_argument("--id", required=True)
    p = con_prod("cribar"); p.add_argument("--archivo", required=True)
    con_prod("prisma")

    a = ap.parse_args()
    try:
        globals()[f"cmd_{a.cmd}"](a)
    except urllib.error.HTTPError as e:
        sys.exit(f"Error HTTP {e.code} consultando la base ({e.url}). Si es 429, espera un minuto y reintenta o usa otra base.")
    except urllib.error.URLError as e:
        sys.exit(f"No se pudo conectar: {e.reason}. Revisa tu conexión a internet.")


if __name__ == "__main__":
    main()
