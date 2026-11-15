"""Línea de comandos de la oficina.

  python -m oficina nueva              Entrevista inicial + ejecución de la producción
  python -m oficina nueva --solo-ficha Solo crea la ficha (para editarla antes de ejecutar)
  python -m oficina ejecutar RUTA      Ejecuta o retoma una producción (carpeta o ficha.yaml)
  python -m oficina agentes            Muestra el catálogo de agentes y productos
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

from .catalogo import AGENTES, DISCIPLINAS, PRODUCTOS
from .entrevista import entrevistar
from .ficha import Ficha

RAIZ_PRODUCCIONES = Path("producciones")


def _cargar_env(ruta: Path = Path(".env")) -> None:
    """Carga variables de un archivo .env (sin sobrescribir las ya definidas)."""
    if not ruta.is_file():
        return
    for linea in ruta.read_text(encoding="utf-8-sig").splitlines():
        linea = linea.strip()
        if not linea or linea.startswith("#") or "=" not in linea:
            continue
        clave, valor = linea.split("=", 1)
        clave, valor = clave.strip(), valor.strip().strip('"').strip("'")
        if valor and clave not in os.environ:
            os.environ[clave] = valor


def _preparar_consola() -> None:
    """Evita errores de codificación con tildes y símbolos en PowerShell/CMD."""
    for flujo in (sys.stdout, sys.stderr):
        try:
            flujo.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError):
            pass
    if os.name == "nt":
        os.system("")  # activa los colores ANSI en la consola de Windows


def _ejecutar(ficha: Ficha, carpeta: Path) -> None:
    from .orquestador import Oficina, OficinaError

    try:
        Oficina(ficha, carpeta).ejecutar()
    except OficinaError as e:
        sys.exit(f"\n✖ {e}")
    except KeyboardInterrupt:
        sys.exit(f"\nInterrumpido. Retoma con: python -m oficina ejecutar {carpeta}")
    print(f"\n✅ Producción lista: {carpeta / 'DOCUMENTO_FINAL.md'}")


def main() -> None:
    _preparar_consola()
    _cargar_env()
    ap =argparse.ArgumentParser(prog="oficina", description="Oficina de Agentes Académicos")
    sub = ap.add_subparsers(dest="cmd", required=True)
    n = sub.add_parser("nueva", help="Nueva producción (entrevista inicial)")
    n.add_argument("--solo-ficha", action="store_true", help="Crear la ficha sin ejecutar")
    e = sub.add_parser("ejecutar", help="Ejecutar o retomar una producción")
    e.add_argument("ruta", type=Path, help="Carpeta de la producción o su ficha.yaml")
    sub.add_parser("agentes", help="Ver catálogo")
    args = ap.parse_args()

    if args.cmd == "agentes":
        print("AGENTES")
        for a in AGENTES.values():
            print(f"  {a.id:<15} {a.nombre:<26} {a.descripcion}")
        print("\nPRODUCTOS")
        for p in PRODUCTOS.values():
            print(f"  {p.id:<21} {p.nombre:<40} agentes: {', '.join(p.agentes_recomendados)}")
        print("\nDISCIPLINAS")
        for d in DISCIPLINAS.values():
            print(f"  {d.id:<12} {d.nombre:<55} {d.estilo_citacion}")
        return

    if args.cmd == "nueva":
        ficha = entrevistar()
        carpeta = RAIZ_PRODUCCIONES / ficha.slug()
        ruta = ficha.guardar(carpeta)
        print(f"\nFicha guardada en {ruta}")
        if args.solo_ficha:
            print(f"Edítala si quieres y luego ejecuta: python -m oficina ejecutar {carpeta}")
            return
        if input("¿Iniciar la producción ahora? (s/n) [s]: ").strip().lower() not in ("", "s", "si", "sí", "y"):
            print(f"Cuando quieras: python -m oficina ejecutar {carpeta}")
            return
        _ejecutar(ficha, carpeta)
        return

    ruta: Path = args.ruta
    carpeta = ruta.parent if ruta.name == "ficha.yaml" else ruta
    _ejecutar(Ficha.cargar(carpeta / "ficha.yaml"), carpeta)


if __name__ == "__main__":
    main()
