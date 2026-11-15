"""Orquestador: ejecuta al equipo de agentes elegido en la ficha, en orden.

Cada paso guarda su entrega en la carpeta de la producción. Si la ejecución se
interrumpe, al volver a lanzarla se retoma desde el primer paso sin entrega.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Literal

import anthropic
from pydantic import BaseModel

from . import config, herramientas
from .catalogo import AGENTES, DISCIPLINAS, PRODUCTOS, TIPOS_INVESTIGACION
from .ficha import Ficha

PROMPTS = Path(__file__).parent / "prompts"


class Decision(BaseModel):
    id: str
    decision: Literal["incluida", "excluida", "duplicado"]
    criterio: str
    motivo: str


class Cribado(BaseModel):
    decisiones: list[Decision]


class OficinaError(RuntimeError):
    pass


class Oficina:
    def __init__(self, ficha: Ficha, carpeta: Path, client: anthropic.Anthropic | None = None):
        self.ficha = ficha
        self.carpeta = carpeta
        self.client = client or anthropic.Anthropic()
        self.uso: dict[str, dict[str, int]] = self._leer_json("uso_tokens.json", {})
        herramientas.reiniciar(self._leer_json("corpus.json", {}), self._leer_json("registro_busquedas.json", []))

    # ------------------------------------------------------------------ util

    def _ruta(self, nombre: str) -> Path:
        return self.carpeta / nombre

    def _leer_json(self, nombre: str, defecto: Any) -> Any:
        p = self._ruta(nombre)
        return json.loads(p.read_text(encoding="utf-8")) if p.exists() else defecto

    def _guardar_json(self, nombre: str, datos: Any) -> None:
        self._ruta(nombre).write_text(json.dumps(datos, ensure_ascii=False, indent=2), encoding="utf-8")

    def _guardar_estado(self) -> None:
        self._guardar_json("corpus.json", herramientas.CORPUS)
        self._guardar_json("registro_busquedas.json", herramientas.REGISTRO)
        self._guardar_json("uso_tokens.json", self.uso)

    def _leer(self, nombre: str) -> str | None:
        p = self._ruta(nombre)
        return p.read_text(encoding="utf-8") if p.exists() else None

    def _escribir(self, nombre: str, texto: str) -> None:
        self._ruta(nombre).write_text(texto, encoding="utf-8")
        print(f"   ✔ guardado {self._ruta(nombre)}")

    def _system(self, agente: str) -> list[dict]:
        texto = (PROMPTS / "_base.md").read_text(encoding="utf-8") + "\n\n" + (PROMPTS / f"{agente}.md").read_text(encoding="utf-8")
        return [{"type": "text", "text": texto, "cache_control": {"type": "ephemeral"}}]

    def _contar(self, agente: str, msg: Any) -> None:
        u = msg.usage
        acc = self.uso.setdefault(agente, {"entrada": 0, "salida": 0, "cache_lectura": 0})
        acc["entrada"] += u.input_tokens or 0
        acc["salida"] += u.output_tokens or 0
        acc["cache_lectura"] += getattr(u, "cache_read_input_tokens", 0) or 0

    @staticmethod
    def _texto(msg: Any) -> str:
        return "\n".join(b.text for b in msg.content if b.type == "text").strip()

    def _revisar_parada(self, agente: str, msg: Any) -> None:
        if msg.stop_reason == "refusal":
            det = getattr(msg, "stop_details", None)
            raise OficinaError(f"El modelo declinó la tarea del agente «{agente}»: {getattr(det, 'explanation', '')}")
        if msg.stop_reason == "max_tokens":
            print(f"   ⚠ «{agente}» alcanzó el límite de tokens; la entrega puede estar incompleta.")

    def _params(self, agente: str, max_tokens: int) -> dict:
        m = config.modelo(agente)
        return {
            "model": m,
            "max_tokens": max_tokens,
            "system": self._system(agente),
            "thinking": {"type": "adaptive"},
            "output_config": {"effort": config.ESFUERZO.get(agente, "high")},
            **config.opciones_respaldo(m),
        }

    # --------------------------------------------------------- llamadas LLM

    def llamar(self, agente: str, mensaje: str | list, max_tokens: int = 64000) -> str:
        """Llamada sin herramientas, en streaming (entregas largas)."""
        with self.client.beta.messages.stream(
            **self._params(agente, max_tokens), messages=[{"role": "user", "content": mensaje}]
        ) as stream:
            msg = stream.get_final_message()
        self._contar(agente, msg)
        self._revisar_parada(agente, msg)
        return self._texto(msg)

    def llamar_con_herramientas(self, agente: str, mensaje: str | list, tools: list, **extra: Any) -> tuple[str, list]:
        """Bucle agéntico con herramientas (tool runner del SDK)."""
        runner = self.client.beta.messages.tool_runner(
            **self._params(agente, 16000),
            tools=tools,
            max_iterations=40,
            messages=[{"role": "user", "content": mensaje}],
            **extra,
        )
        mensajes = []
        for msg in runner:
            mensajes.append(msg)
            self._contar(agente, msg)
        if not mensajes:
            raise OficinaError(f"«{agente}» no devolvió respuesta.")
        final = mensajes[-1]
        self._revisar_parada(agente, final)
        return self._texto(final), mensajes

    # ------------------------------------------------------------ expediente

    def resumen_ficha(self) -> str:
        f = self.ficha
        prod = PRODUCTOS[f.producto]
        disc = DISCIPLINAS[f.disciplina].nombre if f.disciplina in DISCIPLINAS else f.disciplina
        bases = ", ".join(DISCIPLINAS[f.disciplina].bases_sugeridas) if f.disciplina in DISCIPLINAS else "a criterio"
        return (
            "## Ficha de la producción\n"
            f"- Tema: {f.tema}\n"
            f"- Producto: {prod.nombre} — {prod.descripcion}\n"
            f"- Estructura base del producto: {'; '.join(prod.estructura)}\n"
            f"- Disciplina: {disc} (bases sugeridas: {bases})\n"
            f"- Tipo de investigación: {TIPOS_INVESTIGACION.get(f.tipo_investigacion, f.tipo_investigacion)}\n"
            f"- Idioma: {f.idioma}\n"
            f"- Estilo de citación: {f.estilo_citacion}\n"
            f"- Extensión aproximada: {f.extension_palabras} palabras\n"
            f"- Período: {f.anios or 'sin restricción'}\n"
            f"- Contexto/enfoque: {f.contexto or 'no especificado'}\n"
            f"- Equipo: {', '.join(AGENTES[a].nombre for a in f.agentes)}\n"
        )

    def expediente(self, *pasos: str) -> str:
        partes = [self.resumen_ficha()]
        for nombre in pasos:
            texto = self._leer(nombre)
            if texto:
                partes.append(f"## Entrega previa: {nombre}\n\n{texto}")
        return "\n\n".join(partes)

    def corpus_incluido(self, con_resumen: bool) -> str:
        items = [i for i in herramientas.CORPUS.values() if i.get("decision", "incluida") == "incluida"]
        lineas = []
        for i in items:
            ref = {k: i.get(k) for k in ("id", "doi", "titulo", "anio", "autores", "revista", "tipo", "citas")}
            if con_resumen:
                ref["resumen"] = i.get("resumen") or "(sin resumen disponible)"
            lineas.append(json.dumps(ref, ensure_ascii=False))
        return f"## Corpus de fuentes incluidas ({len(items)})\n" + "\n".join(lineas)

    # ---------------------------------------------------- punto de control

    def punto_control(self, nombre: str, agente: str, rehacer) -> None:
        if not self.ficha.puntos_control:
            return
        while True:
            print(f"\n⏸  Revisa {self._ruta(nombre)}")
            r = input("   Enter para aprobar, o escribe tus observaciones para que se rehaga: ").strip()
            if not r:
                return
            print(f"   ↻ {AGENTES[agente].nombre} incorpora tus observaciones…")
            self._escribir(nombre, rehacer(r))
            self._guardar_estado()

    # -------------------------------------------------------------- pasos

    def paso_director(self) -> None:
        nombre = "01_plan_director.md"
        if self._leer(nombre):
            return
        base = self.resumen_ficha() + "\n\nElabora el plan de investigación."
        self._escribir(nombre, self.llamar("director", base))
        self.punto_control(
            nombre, "director",
            lambda obs: self.llamar("director", f"{base}\n\n## Plan anterior\n{self._leer(nombre)}\n\n## Observaciones del investigador responsable\n{obs}\n\nEntrega el plan completo corregido."),
        )

    def paso_metodologo(self) -> None:
        nombre = "02_metodologia.md"
        if self._leer(nombre):
            return
        base = self.expediente("01_plan_director.md") + "\n\nDiseña la metodología."
        self._escribir(nombre, self.llamar("metodologo", base))
        self.punto_control(
            nombre, "metodologo",
            lambda obs: self.llamar("metodologo", f"{base}\n\n## Metodología anterior\n{self._leer(nombre)}\n\n## Observaciones\n{obs}\n\nEntrega la metodología completa corregida."),
        )

    def paso_buscador(self) -> None:
        nombre = "03_informe_busqueda.md"
        if self._leer(nombre):
            return
        texto, _ = self.llamar_con_herramientas(
            "buscador",
            self.expediente("01_plan_director.md", "02_metodologia.md") + "\n\nEjecuta la estrategia de búsqueda.",
            herramientas.HERRAMIENTAS_BUSQUEDA,
        )
        self._guardar_estado()
        registro = "\n".join(
            f"| {r['fecha']} | {r['base']} | {r['consulta']} | {r['filtros']} | {r['total_reportado']} | {r['devueltos']} |"
            for r in herramientas.REGISTRO
        )
        texto += (
            f"\n\n## Registro de búsquedas (automático)\n\n| Fecha | Base | Consulta | Filtros | Total en base | Recuperados |\n"
            f"|---|---|---|---|---|---|\n{registro}\n\nRegistros únicos en el corpus: {len(herramientas.CORPUS)}\n"
        )
        self._escribir(nombre, texto)

    def paso_cribador(self) -> None:
        nombre = "04_cribado.md"
        if self._leer(nombre):
            return
        items = list(herramientas.CORPUS.values())
        if not items:
            self._escribir(nombre, "No hay registros en el corpus para cribar.")
            return
        decisiones: dict[str, Decision] = {}
        criterios = self.expediente("01_plan_director.md", "02_metodologia.md")
        for inicio in range(0, len(items), 40):  # lotes para no saturar la salida
            lote = items[inicio : inicio + 40]
            registros = "\n".join(
                json.dumps({k: i.get(k) for k in ("id", "titulo", "anio", "tipo", "idioma", "revista", "resumen")}, ensure_ascii=False)
                for i in lote
            )
            resp = self.client.beta.messages.parse(
                **self._params("cribador", 16000),
                messages=[{"role": "user", "content": f"{criterios}\n\n## Registros a cribar\n{registros}\n\nDecide sobre cada registro."}],
                output_format=Cribado,
            )
            self._contar("cribador", resp)
            self._revisar_parada("cribador", resp)
            for d in resp.parsed_output.decisiones:
                decisiones[d.id] = d
            print(f"   · cribados {min(inicio + 40, len(items))}/{len(items)}")
        for i in items:
            d = decisiones.get(i["id"])
            i["decision"] = d.decision if d else "incluida"
            i["motivo_cribado"] = f"{d.criterio}: {d.motivo}" if d else "sin decisión explícita; se incluye por defecto"
        self._guardar_estado()
        n_inc = sum(1 for i in items if i["decision"] == "incluida")
        n_dup = sum(1 for i in items if i["decision"] == "duplicado")
        n_exc = len(items) - n_inc - n_dup
        filas = "\n".join(f"| {i['id']} | {(i.get('titulo') or '')[:90]} | {i['decision']} | {i['motivo_cribado']} |" for i in items)
        self._escribir(
            nombre,
            "# Cribado por título y resumen\n\n"
            "## Flujo PRISMA\n\n"
            f"```\nRegistros identificados ............ {len(items)}\n"
            f"  └ Duplicados eliminados ........... {n_dup}\n"
            f"Registros cribados ................. {len(items) - n_dup}\n"
            f"  └ Excluidos por título/resumen .... {n_exc}\n"
            f"Estudios incluidos ................. {n_inc}\n```\n\n"
            "## Decisiones\n\n| id | Título | Decisión | Criterio y motivo |\n|---|---|---|---|\n" + filas + "\n",
        )

    def paso_lector(self) -> None:
        nombre = "05_matriz_y_sintesis.md"
        if self._leer(nombre):
            return
        msg = (
            self.expediente("01_plan_director.md", "02_metodologia.md")
            + "\n\n" + self.corpus_incluido(con_resumen=True)
            + "\n\nElabora la matriz de extracción y la síntesis."
        )
        self._escribir(nombre, self.llamar("lector", msg))

    def paso_analista(self) -> None:
        nombre = "06_analisis_datos.md"
        if self._leer(nombre):
            return
        ruta = Path(self.ficha.archivo_datos)
        if not ruta.is_file():
            raise OficinaError(f"No encuentro el archivo de datos: {ruta}")
        with ruta.open("rb") as fh:
            subido = self.client.files.upload(file=(ruta.name, fh))
        contenido = [
            {"type": "text", "text": self.expediente("01_plan_director.md", "02_metodologia.md")
             + f"\n\nEl archivo de datos «{ruta.name}» está disponible en el entorno de ejecución. Realiza el análisis."},
            {"type": "container_upload", "file_id": subido.id},
        ]
        texto, mensajes = self.llamar_con_herramientas(
            "analista_datos", contenido, [{"type": "code_execution_20260521", "name": "code_execution"}]
        )
        self._descargar_archivos(mensajes)
        self._escribir(nombre, texto)

    def _descargar_archivos(self, mensajes: list) -> None:
        destino = self._ruta("figuras")
        for msg in mensajes:
            for b in msg.content:
                if b.type != "bash_code_execution_tool_result":
                    continue
                res = b.content
                if getattr(res, "type", "") != "bash_code_execution_result":
                    continue
                for ref in res.content or []:
                    if ref.type != "bash_code_execution_output":
                        continue
                    meta = self.client.files.retrieve_metadata(ref.file_id)
                    nombre = Path(meta.filename).name
                    if nombre in ("", ".", ".."):
                        continue
                    destino.mkdir(exist_ok=True)
                    self.client.files.download(ref.file_id).write_to_file(destino / nombre)
                    print(f"   ✔ figura/tabla {destino / nombre}")

    def _material_redaccion(self) -> str:
        return (
            self.expediente("01_plan_director.md", "02_metodologia.md", "04_cribado.md", "05_matriz_y_sintesis.md", "06_analisis_datos.md")
            + "\n\n" + self.corpus_incluido(con_resumen=False)
        )

    def paso_redaccion_y_revision(self) -> None:
        version = 1
        while self._leer(f"07_borrador_v{version + 1}.md"):
            version += 1
        borrador = f"07_borrador_v{version}.md"
        if not self._leer(borrador):
            self._escribir(borrador, self.llamar("redactor", self._material_redaccion() + "\n\nRedacta el documento completo."))

        for ronda in range(version, version + max(self.ficha.rondas_revision, 0)):
            borrador = f"07_borrador_v{ronda}.md"
            observaciones = []
            aprobado = True
            if "verificador" in self.ficha.agentes:
                nombre = f"08_verificacion_v{ronda}.md"
                if not self._leer(nombre):
                    texto, _ = self.llamar_con_herramientas(
                        "verificador",
                        f"{self.resumen_ficha()}\n\n## Borrador a verificar\n\n{self._leer(borrador)}",
                        [herramientas.leer_fuente, herramientas.verificar_doi, herramientas.listar_corpus],
                    )
                    self._escribir(nombre, texto)
                v = self._leer(nombre) or ""
                if "VEREDICTO: APROBADO" not in v:
                    aprobado = False
                    observaciones.append(f"## Observaciones del verificador de citas\n\n{v}")
            if "revisor" in self.ficha.agentes:
                nombre = f"09_revision_par_v{ronda}.md"
                if not self._leer(nombre):
                    self._escribir(nombre, self.llamar(
                        "revisor", f"{self.expediente('01_plan_director.md', '02_metodologia.md')}\n\n## Borrador a revisar\n\n{self._leer(borrador)}"
                    ))
                r = self._leer(nombre) or ""
                if "VEREDICTO: ACEPTAR" not in r:
                    aprobado = False
                    observaciones.append(f"## Observaciones del revisor par\n\n{r}")
            if aprobado:
                print(f"   ✔ Borrador v{ronda} aprobado.")
                break
            print(f"   ↻ Ronda {ronda}: el redactor corrige.")
            self._escribir(
                f"07_borrador_v{ronda + 1}.md",
                self.llamar("redactor", self._material_redaccion()
                            + f"\n\n## Borrador actual (v{ronda})\n\n{self._leer(borrador)}\n\n" + "\n\n".join(observaciones)
                            + "\n\nEntrega el documento completo corregido."),
            )
        # el último borrador es el final
        version = 1
        while self._leer(f"07_borrador_v{version + 1}.md"):
            version += 1
        final = f"07_borrador_v{version}.md"
        self.punto_control(
            final, "redactor",
            lambda obs: self.llamar("redactor", self._material_redaccion()
                                    + f"\n\n## Borrador actual\n\n{self._leer(final)}\n\n## Observaciones del investigador responsable\n{obs}"
                                    + "\n\nEntrega el documento completo corregido."),
        )
        self._escribir("DOCUMENTO_FINAL.md", self._leer(final) or "")

    # -------------------------------------------------------------- run

    def ejecutar(self) -> Path:
        self.carpeta.mkdir(parents=True, exist_ok=True)
        pasos = {
            "director": self.paso_director,
            "metodologo": self.paso_metodologo,
            "buscador": self.paso_buscador,
            "cribador": self.paso_cribador,
            "lector": self.paso_lector,
            "analista_datos": self.paso_analista,
            "redactor": self.paso_redaccion_y_revision,
        }
        try:
            for agente in self.ficha.agentes:
                if agente in pasos:  # verificador y revisor van dentro del ciclo del redactor
                    print(f"\n▶ {AGENTES[agente].nombre}")
                    pasos[agente]()
                    self._guardar_estado()
        finally:
            self._guardar_estado()
        total_in = sum(v["entrada"] for v in self.uso.values())
        total_out = sum(v["salida"] for v in self.uso.values())
        print(f"\nTokens usados: {total_in:,} de entrada, {total_out:,} de salida (detalle en uso_tokens.json)")
        return self.carpeta
