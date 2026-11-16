# Oficina de Agentes Académicos

Este repositorio es una oficina de agentes de IA que produce investigación académica (estados del arte, revisiones sistemáticas, artículos, capítulos de tesis, proyectos, ensayos e informes con datos propios).

- Para iniciar o retomar una producción, usa el comando `/investigacion` (`.claude/skills/investigacion/SKILL.md`). El coordinador hace la entrevista inicial y llama a los subagentes de `.claude/agents/`.
- La plantilla (productos, disciplinas, agentes, dependencias y archivos) está en `plantilla/catalogo.md`. Los principios que todo agente cumple están en `plantilla/principios.md`.
- Las búsquedas y verificaciones académicas se hacen con `herramientas/academico.py` (solo biblioteca estándar de Python, sin claves).
- Cada producción vive en `producciones/<fecha>-<tema>/` y no se sube a git.
- La carpeta `oficina/` es la versión alternativa en Python que usa la API de Anthropic (de pago). No hace falta para el modo Claude Code.
- Integridad académica: nunca inventar fuentes, DOI, datos ni citas.
