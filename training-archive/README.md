# Training Archive

Archivado local de contenidos de `training.lidr.co` en formato reproducible para lectura y repaso offline.

## Estructura

- `ai-engineering-2026-04/00-intro/`, `00-pre-course/`, `01-session/`, `02-session/`...
  - agrupación directa por bloque o sesión
- `ai-engineering-2026-04/<grupo>/<slug>/index.md`
  - export final en Markdown
- `ai-engineering-2026-04/<grupo>/<slug>/assets/`
  - imágenes y ficheros auxiliares descargados para lectura offline
- `ai-engineering-2026-04/manifest.json`
  - estado del archivado, inventario descubierto y progreso

## Flujo

1. Capturar HTML renderizado y assets observados desde el navegador autenticado.
2. Descargar las imágenes relevantes.
3. Generar directamente `index.md` y `assets/` dentro de su carpeta de sesión.
4. Regenerar `manifest.json`.

## Nota

El crawl debe ejecutarse de forma espaciada para evitar bloqueos por navegación agresiva entre lecciones.
