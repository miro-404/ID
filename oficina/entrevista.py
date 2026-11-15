"""Entrevista inicial: se ejecuta al comenzar cada producción y genera la ficha.

Pregunta, en este orden:
  1. Tema
  2. Tipo de producto
  3. Disciplina
  4. Tipo de investigación
  5. Idioma, estilo de citación, extensión y período
  6. Qué agentes trabajarán en esta producción
  7. Datos propios (si se usa el analista de datos)
  8. Puntos de control humanos
"""

from __future__ import annotations

from pathlib import Path

from .catalogo import (
    AGENTES,
    DISCIPLINAS,
    ESTILOS_CITACION,
    PRODUCTOS,
    TIPOS_INVESTIGACION,
    resolver_dependencias,
)
from .ficha import Ficha


def _titulo(texto: str) -> None:
    print(f"\n\033[1m── {texto} ──\033[0m")


def _texto(pregunta: str, defecto: str = "", obligatorio: bool = False) -> str:
    sufijo = f" [{defecto}]" if defecto else ""
    while True:
        r = input(f"{pregunta}{sufijo}: ").strip()
        if r:
            return r
        if defecto or not obligatorio:
            return defecto
        print("  Este dato es obligatorio.")


def _menu(pregunta: str, opciones: list[tuple[str, str]], defecto: int | None = None, permitir_otro: bool = False) -> str:
    """Muestra un menú numerado y devuelve el id elegido (o texto libre si permitir_otro)."""
    print(pregunta)
    for i, (_, etiqueta) in enumerate(opciones, 1):
        print(f"  {i}. {etiqueta}")
    if permitir_otro:
        print(f"  {len(opciones) + 1}. Otra (escribirla)")
    while True:
        r = _texto("Elige un número", str(defecto) if defecto else "", obligatorio=True)
        if r.isdigit():
            n = int(r)
            if 1 <= n <= len(opciones):
                return opciones[n - 1][0]
            if permitir_otro and n == len(opciones) + 1:
                return _texto("Escríbela", obligatorio=True)
        print("  Opción no válida.")


def _si_no(pregunta: str, defecto: bool = True) -> bool:
    r = _texto(pregunta + " (s/n)", "s" if defecto else "n").lower()
    return r.startswith("s") or r.startswith("y")


def elegir_agentes(recomendados: tuple[str, ...]) -> list[str]:
    print("Agentes disponibles (★ = recomendado para este producto, ● = obligatorio):")
    ids = list(AGENTES)
    for i, aid in enumerate(ids, 1):
        a = AGENTES[aid]
        marca = "●" if a.obligatorio else ("★" if aid in recomendados else " ")
        print(f"  {i}. {marca} {a.nombre:<26} {a.descripcion}")
    print("Pulsa Enter para usar los recomendados, o escribe los números separados por comas (ej. 1,3,5,7).")
    while True:
        r = input("Agentes: ").strip()
        if not r:
            seleccion = list(recomendados)
            break
        try:
            nums = [int(x) for x in r.replace(" ", "").split(",") if x]
            seleccion = [ids[n - 1] for n in nums]
            break
        except (ValueError, IndexError):
            print("  Lista no válida.")
    finales, avisos = resolver_dependencias(seleccion)
    for aviso in avisos:
        print(f"  ⚠ {aviso}")
    print("Equipo final: " + " → ".join(AGENTES[a].nombre for a in finales))
    return finales


def entrevistar() -> Ficha:
    print("\n\033[1mOficina de Agentes Académicos — nueva producción\033[0m")

    _titulo("1. Tema")
    tema = _texto("¿Sobre qué tema o pregunta vamos a investigar?", obligatorio=True)

    _titulo("2. Tipo de producto")
    producto_id = _menu("¿Qué vamos a producir?", [(p.id, f"{p.nombre} — {p.descripcion}") for p in PRODUCTOS.values()])
    producto = PRODUCTOS[producto_id]

    _titulo("3. Disciplina")
    disciplina = _menu("¿En qué disciplina se enmarca?", [(d.id, d.nombre) for d in DISCIPLINAS.values()], permitir_otro=True)
    estilo_def = DISCIPLINAS[disciplina].estilo_citacion if disciplina in DISCIPLINAS else "APA 7"

    _titulo("4. Tipo de investigación")
    defecto_tipo = 2 if producto_id == "informe_datos" else 1
    tipo = _menu("¿Qué tipo de investigación es?", list(TIPOS_INVESTIGACION.items()), defecto=defecto_tipo)

    _titulo("5. Formato")
    idioma = _texto("Idioma del documento", "español")
    estilos = [(e, e) for e in ESTILOS_CITACION]
    estilo = _menu("Estilo de citación", estilos, defecto=ESTILOS_CITACION.index(estilo_def) + 1 if estilo_def in ESTILOS_CITACION else 1)
    extension = int(_texto("Extensión aproximada en palabras", str(producto.extension_palabras)))
    anios = _texto("Período de publicaciones a considerar (ej. 2015-2026, Enter = sin límite)")
    contexto = _texto("Contexto o enfoque (país, población, teoría, etc.; opcional)")

    _titulo("6. Equipo de agentes")
    recomendados = producto.agentes_recomendados
    if tipo != "documental" and "analista_datos" not in recomendados:
        recomendados = recomendados + ("analista_datos",)
    agentes = elegir_agentes(recomendados)

    archivo_datos = ""
    if "analista_datos" in agentes:
        _titulo("7. Datos propios")
        while True:
            archivo_datos = _texto("Ruta al archivo de datos (CSV o Excel)", obligatorio=True)
            if Path(archivo_datos).expanduser().is_file():
                archivo_datos = str(Path(archivo_datos).expanduser().resolve())
                break
            print("  No encuentro ese archivo.")

    _titulo("8. Control")
    puntos_control = _si_no("¿Quieres aprobar el plan y el borrador antes de continuar?", True)
    rondas = int(_texto("Rondas máximas de revisión par", "2")) if "revisor" in agentes else 0

    return Ficha(
        tema=tema,
        producto=producto_id,
        disciplina=disciplina,
        tipo_investigacion=tipo,
        agentes=agentes,
        idioma=idioma,
        estilo_citacion=estilo,
        extension_palabras=extension,
        anios=anios,
        contexto=contexto,
        archivo_datos=archivo_datos,
        puntos_control=puntos_control,
        rondas_revision=rondas,
    )
