---
title: "📄  Configuración del entorno en local 🔴 — 13 min"
source_url: "https://training.lidr.co/posts/ai-engineering-202604-📄-configuracion-del-entorno-en-local-🔴-13-min"
archived_at: "2026-06-12T09:20:45.553Z"
group: "00-pre-course"
---

# 📄 Configuración del entorno en local 🔴 — 13 min

![Antonio Perez](./assets/c3eccac37426c36f.jpg)

[Antonio Perez](https://training.lidr.co/members/36030888)

Tiempo estimado: 13 min

## Guía de Configuración del Entorno de Desarrollo

Antes de arrancar con la primera sesión del programa, necesitas tener instaladas y funcionando las herramientas base sobre las que construiremos todos los proyectos. Esta guía te acompaña paso a paso en la instalación de cada una de ellas.

No te preocupes si alguna de estas herramientas es nueva para ti — están pensadas para ser sencillas de poner en marcha, y en las primeras sesiones las usaremos juntas para que todo encaje de forma natural.

## 1. Docker y Docker Compose

Docker es la primera herramienta que debes instalar, porque el resto del entorno de desarrollo del programa (Python, FastAPI, PostgreSQL) se ejecutará dentro de contenedores Docker. Esto garantiza que todos los alumnos trabajemos exactamente con el mismo entorno, independientemente de si usas macOS, Windows o Linux.

### ¿Qué es Docker?

Docker es una plataforma que permite empaquetar aplicaciones y todas sus dependencias en unidades aisladas llamadas**contenedores**. Un contenedor es como una caja que incluye todo lo necesario para ejecutar un servicio: el sistema operativo base, las librerías, el código y la configuración. A diferencia de una máquina virtual, los contenedores son ligeros y arrancan en segundos.

**Docker Compose**es una herramienta complementaria que permite definir y levantar múltiples contenedores con un solo comando. En nuestro caso, lo usaremos para levantar simultáneamente el servicio FastAPI, la base de datos PostgreSQL y el frontend, todo con un simpledocker-compose up.

### Instalación

La forma más sencilla de instalar Docker es a través de**Docker Desktop**, que incluye tanto Docker como Docker Compose y proporciona una interfaz gráfica para gestionar tus contenedores.

### macOS

1. 

Ve a[docker.com/get-started](https://www.docker.com/get-started/)y descarga**Docker Desktop for Mac**(selecciona la versión para Apple Silicon o Intel según tu procesador).

1. 

Abre el archivo.dmgdescargado y arrastra el icono de Docker a la carpeta Aplicaciones.

1. 

Abre Docker Desktop desde Aplicaciones. La primera vez te pedirá aceptar los términos de servicio.

1. 

Espera a que el icono de la ballena en la barra de menú deje de parpadear — eso indica que Docker está listo.

### Windows

1. 

Asegúrate de tener**WSL 2**(Windows Subsystem for Linux) habilitado. Si no lo tienes, abre PowerShell como administrador y ejecuta:

powershell

wsl --install

Reinicia el equipo si es necesario.

1. 

Descarga**Docker Desktop for Windows**desde[docker.com/get-started](https://www.docker.com/get-started/).

1. 

Ejecuta el instalador y asegúrate de que la opción "Use WSL 2 instead of Hyper-V" esté marcada.

1. 

Completa la instalación y reinicia si te lo pide.

1. 

Abre Docker Desktop y acepta los términos de servicio.

### Linux (Ubuntu/Debian)

En Linux puedes instalar Docker Engine directamente sin Docker Desktop:

bash
# Actualizar paquetes e instalar dependencias sudo apt-get update sudo apt-get install -y ca-certificates curl gnupg # Añadir la clave GPG oficial de Docker sudo install -m 0755 -d /etc/apt/keyrings curl -fsSL <https://download.docker.com/linux/ubuntu/gpg> | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg # Añadir el repositorio de Docker echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] <https://download.docker.com/linux/ubuntu> $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null # Instalar Docker Engine y Docker Compose sudo apt-get update sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin # Añadir tu usuario al grupo docker (para no necesitar sudo) sudo usermod -aG docker $USER

Cierra sesión y vuelve a entrar para que el cambio de grupo surta efecto.

### Verificación

Abre una terminal y ejecuta:

bash
docker --version docker compose version docker run hello-world

Si todo está correcto, verás las versiones instaladas y un mensaje de bienvenida de Docker confirmando que la instalación funciona.

### Para ampliar

- 

**Documentación oficial de Docker**:[docs.docker.com](https://docs.docker.com/)— referencia completa de todos los comandos y configuraciones.

- 

**Guía oficial "Get Started"**:[docs.docker.com/get-started](https://docs.docker.com/get-started/)— tutorial interactivo paso a paso de Docker.

- 

**Docker para principiantes (español)**:[freeCodeCamp - Guía de Docker para principiantes](https://www.freecodecamp.org/espanol/news/guia-de-docker-para-principiantes-como-crear-tu-primera-aplicacion-docker/)— tutorial práctico en español para crear tu primera aplicación con Docker.

- 

**Tutorial Docker en español**:[Imagina Formación - Aprende Docker](https://imaginaformacion.com/tutoriales/aprende-docker-tutorial-de-primeros-pasos)— guía actualizada con los conceptos principales y primeros pasos.

## 2. uv — Gestor de paquetes y entornos Python

uves un gestor de paquetes y proyectos Python escrito en Rust, creado por Astral (los mismos creadores deruff). Reemplaza a herramientas comopip,virtualenv,poetryypyenven una sola utilidad que es entre 10 y 100 veces más rápida.

### ¿Por qué uv y no pip?

Si vienes de otros lenguajes, piensa enuvcomo el equivalente abundleren Ruby onpmen JavaScript. Frente a pip,uvofrece resolución de dependencias determinista con lockfiles, gestión integrada de entornos virtuales, e instalación de versiones de Python sin necesidad de herramientas adicionales comopyenv.

No necesitas tener Python instalado previamente —uvpuede instalarlo por ti.

### [Instalación](https://astral.sh/uv/install.sh)macOS / Linux

Tras la instalación, reinicia tu terminal o ejecuta el comando que te indica la salida del script para actualizar el PATH.

### Windows (PowerShell)

powershell
powershell -ExecutionPolicy ByPass -c "irm <https://astral.sh/uv/install.ps1> | iex"
### Alternativa (si ya tienes pip)

bash

pip install uv

### Verificación

bash

uv --version

### Primeros pasos con uv

Una vez instalado, puedes usaruvpara instalar Python y gestionar tu proyecto:

bash
# Instalar Python 3.11 (la versión que usaremos en el programa) uv python install 3.11 # Crear un nuevo proyecto uv init mi-proyecto cd mi-proyecto # Añadir dependencias uv add fastapi # Ejecutar un script uv run python main.py

El comandouv initcrea automáticamente la estructura del proyecto con unpyproject.tomly un entorno virtual aislado. No necesitas crear ni activar el entorno virtual manualmente —uv runse encarga de todo.

### Para ampliar

- 

**Documentación oficial de uv**:[docs.astral.sh/uv](https://docs.astral.sh/uv/)— referencia completa y guías oficiales.

- 

**Guía de instalación de Python con uv**:[docs.astral.sh/uv/guides/install-python](https://docs.astral.sh/uv/guides/install-python/)— cómo gestionar versiones de Python.

- 

**"Managing Python Projects With uv" (Real Python)**:[realpython.com/python-uv](https://realpython.com/python-uv/)— tutorial exhaustivo con ejemplos prácticos paso a paso.

- 

**"uv: An In-Depth Guide" (SaaS Pegasus)**:[saaspegasus.com/guides/uv-deep-dive](https://www.saaspegasus.com/guides/uv-deep-dive/)— guía en profundidad sobre por qué uv es el futuro del empaquetado Python.

- 

**Tutorial de DataCamp sobre uv**:[datacamp.com/tutorial/python-uv](https://www.datacamp.com/tutorial/python-uv)— introducción completa con comparativas frente a pip y poetry.

## 3. FastAPI — Framework para los servicios de IA

FastAPI es el framework Python con el que construiremos todos los servicios de backend de IA a lo largo del programa. Es rápido, moderno, y genera documentación interactiva de tu API de forma automática.

### ¿Qué es FastAPI?

FastAPI es un framework web para construir APIs con Python 3.7+ basado en type hints estándar de Python. Se apoya en dos pilares:**Starlette**para la parte web y de rendimiento asíncrono, y**Pydantic**para la validación y serialización de datos. Cuando defines un endpoint en FastAPI, el framework genera automáticamente documentación interactiva (Swagger UI) accesible desde el navegador.

### Instalación

FastAPI se instala como una dependencia más de tu proyecto Python. Si estás usandouv(que es lo que haremos en el programa):

bash
# Dentro de tu proyecto uv add "fastapi[standard]"

La opción[standard]incluye FastAPI junto con Uvicorn (el servidor ASGI que ejecuta la aplicación) y otras dependencias útiles para desarrollo.

Si prefieres usar pip directamente:

bash

pip install "fastapi[standard]"

**Nota:**Recuerda poner"fastapi[standard]"entre comillas para que funcione correctamente en todas las terminales.

### Tu primera aplicación FastAPI

Crea un archivomain.pycon el siguiente contenido:

python
from fastapi import FastAPI app = FastAPI() @app.get("/") def read_root(): return {"mensaje": "¡Hola desde FastAPI!"} @app.get("/items/{item_id}") def read_item(item_id: int, q: str | None = None): return {"item_id": item_id, "q": q}

Ejecuta la aplicación:

bash
# Con uv uv run fastapi dev main.py # O directamente con uvicorn uvicorn main:app --reload

Abre tu navegador enhttp://127.0.0.1:8000y verás la respuesta JSON. Ve ahttp://127.0.0.1:8000/docspara acceder a la documentación interactiva generada automáticamente.

### Verificación

Si ves la documentación Swagger con tus dos endpoints listados, FastAPI está funcionando correctamente.

### Para ampliar

- 

**Documentación oficial de FastAPI**:[fastapi.tiangolo.com](https://fastapi.tiangolo.com/)— tutorial completo, guía avanzada y referencia de API.

- 

**Tutorial oficial en español**:[fastapi.tiangolo.com/es/tutorial](https://fastapi.tiangolo.com/es/tutorial/)— la documentación oficial traducida al español.

- 

**"Get Started With FastAPI" (Real Python)**:[realpython.com/get-started-with-fastapi](https://realpython.com/get-started-with-fastapi/)— tutorial introductorio bien estructurado.

- 

**Tutorial de FastAPI (VS Code)**:[code.visualstudio.com/docs/python/tutorial-fastapi](https://code.visualstudio.com/docs/python/tutorial-fastapi)— guía oficial de Microsoft para trabajar con FastAPI en VS Code.

- 

**"FastAPI: la herramienta definitiva" (español)**:[cosasdedevs.com/fastapi](https://cosasdedevs.com/fastapi/)— colección de tutoriales en español desde cero.

- 

**Tutorial CRUD con FastAPI (español)**:[kinsta.com/es/blog/fastapi](https://kinsta.com/es/blog/fastapi/)— guía práctica para construir una aplicación CRUD completa.

## 4. Verificación final del entorno

Una vez que tengas todo instalado, ejecuta estos comandos para confirmar que tu entorno está listo:

bash
# Docker docker --version docker compose version # uv y Python uv --version uv python list # Debería mostrar Python 3.11 instalado # FastAPI (desde un proyecto con uv) uv run fastapi --version

Si todos los comandos devuelven versiones sin errores, estás listo para la primera sesión.
