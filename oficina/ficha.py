"""La ficha de producción: todo lo que se decide al inicio de cada investigación."""

from __future__ import annotations

import re
import unicodedata
from dataclasses import asdict, dataclass, field
from datetime import date
from pathlib import Path

import yaml


@dataclass
class Ficha:
    tema: str
    producto: str  # id en catalogo.PRODUCTOS
    disciplina: str  # id en catalogo.DISCIPLINAS o texto libre
    tipo_investigacion: str  # id en catalogo.TIPOS_INVESTIGACION
    agentes: list[str]  # ids en catalogo.AGENTES, en orden de ejecución
    idioma: str = "español"
    estilo_citacion: str = "APA 7"
    extension_palabras: int = 6000
    anios: str = ""  # p. ej. "2015-2026"; vacío = sin restricción
    contexto: str = ""  # notas libres: población, país, enfoque, etc.
    archivo_datos: str = ""  # ruta a CSV/Excel si se usa el analista de datos
    puntos_control: bool = True  # pausar para que apruebes plan y borrador
    rondas_revision: int = 2
    creada: str = field(default_factory=lambda: date.today().isoformat())

    # -- persistencia -------------------------------------------------------

    def guardar(self, carpeta: Path) -> Path:
        carpeta.mkdir(parents=True, exist_ok=True)
        ruta = carpeta / "ficha.yaml"
        ruta.write_text(yaml.safe_dump(asdict(self), allow_unicode=True, sort_keys=False), encoding="utf-8")
        return ruta

    @classmethod
    def cargar(cls, ruta: Path) -> "Ficha":
        datos = yaml.safe_load(ruta.read_text(encoding="utf-8"))
        return cls(**datos)

    def slug(self) -> str:
        texto = unicodedata.normalize("NFKD", self.tema).encode("ascii", "ignore").decode()
        texto = re.sub(r"[^a-zA-Z0-9]+", "-", texto).strip("-").lower()
        return f"{self.creada}-{texto[:50] or 'produccion'}"
