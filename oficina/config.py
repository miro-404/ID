"""Configuración de modelos y esfuerzo por agente.

Puedes cambiar el modelo de toda la oficina con la variable de entorno
OFICINA_MODELO, o el de un agente concreto con OFICINA_MODELO_<AGENTE>
(p. ej. OFICINA_MODELO_CRIBADOR=claude-haiku-5-5).
"""

from __future__ import annotations

import os

MODELO_POR_DEFECTO = "claude-opus-5-5"

# Esfuerzo de razonamiento por agente: low | medium | high | xhigh | max
ESFUERZO: dict[str, str] = {
    "director": "high",
    "metodologo": "high",
    "buscador": "medium",
    "cribador": "low",
    "lector": "high",
    "analista_datos": "high",
    "redactor": "high",
    "verificador": "medium",
    "revisor": "high",
}

# Modelos que admiten el respaldo automático del servidor si el modelo principal
# declina una petición (fallbacks="default").
_MODELOS_CON_RESPALDO = {"claude-opus-5-5", "claude-opus-5", "claude-sonnet-5-5", "claude-fable-5-2", "claude-fable-5-1"}
BETA_RESPALDO = "server-side-fallback-2026-07-01"


def modelo(agente: str) -> str:
    return os.getenv(f"OFICINA_MODELO_{agente.upper()}") or os.getenv("OFICINA_MODELO") or MODELO_POR_DEFECTO


def opciones_respaldo(nombre_modelo: str) -> dict:
    if nombre_modelo in _MODELOS_CON_RESPALDO:
        return {"betas": [BETA_RESPALDO], "fallbacks": "default"}
    return {}
