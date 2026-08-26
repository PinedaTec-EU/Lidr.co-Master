---
title: "✍️Dockerización del proyecto 🔴"
source_url: "https://training.lidr.co/posts/ai-engineering-202604-%E2%9C%8D%EF%B8%8Fdockerizacion-del-proyecto-%F0%9F%94%B4"
archived_at: "2026-08-26T16:26:18.058Z"
group: "15-session"
---

# ✍️Dockerización del proyecto 🔴

⏳Tiempo estimado: 5 min

🚨La fecha límite: lunes 17 de agosto a las 23:59 de tu hora local.

## 

## Contexto

Hasta ahora has arrancado el Proyecto 2 (sistema de estimación) a mano: en una terminal levantas el backend de negocio (Rails), en otra el servicio IA (FastAPI), y por tu cuenta tienes corriendo la base de datos relacional y la base de datos vectorial. Eso vale para desarrollar, pero no es reproducible ni desplegable: depende de tu máquina, de tus versiones y de que recuerdes el orden de arranque.

En este ejercicio vas a**containerizar el proyecto como microservicios separados**y a orquestarlos condocker-compose, de forma que todo el sistema arranque con un único comando y las tres capas se comuniquen entre contenedores. Es el paso previo imprescindible para el despliegue en cloud que haremos en el directo.

Recuerda la nomenclatura del programa:**servicio IA**es el backend Python/FastAPI (encapsula CAG/RAG y agentes) y**backend de negocio**es la capa Rails (usuarios, sesiones, persistencia, reglas de negocio). Evitamos la palabra "backend" a secas porque hay dos.

## Objetivo

Al terminar debes tener undocker-compose.ymlque levante:

1. 

**backend de negocio**(Rails) — expuesto al host, es el único punto de entrada público.

1. 

**servicio IA**(FastAPI) — accesible**solo**desde la red interna de compose, nunca publicado al host.

1. 

**base de datos relacional**(PostgreSQL) — datastore del backend de negocio.

1. 

**base de datos vectorial**— datastore del servicio IA (usa el motor que ya empleas en el proyecto).

Y que una**estimación end-to-end**(usuario → backend de negocio → servicio IA → BBDD vectorial → respuesta) funcione íntegramente dentro de los contenedores.

## Requisitos previos

- 

Docker y Docker Compose instalados (docker --version,docker compose version).

- 

El repositorio del Proyecto 2 tal como quedó tras la Sesión 14.

- 

Tu clave de API del proveedor de LLM disponible como variable de entorno (no la escribas en ningún fichero versionado).

## Paso 1 — Estructura de carpetas

Organiza el repositorio para que cada servicio sea autocontenido. Una estructura de referencia:
project-2/ ├── business-backend/ # Rails app (frontend + backend de negocio) │ └── Dockerfile ├── ai-service/ # FastAPI app (servicio IA) │ └── Dockerfile ├── .env.example # plantilla de variables (SÍ se versiona) ├── .env # valores reales (NO se versiona) └── docker-compose.yml

Añade.enva tu.gitignoresi no está ya.

## Paso 2 —Dockerfiledel servicio IA (Python / FastAPI)

Usa una imagen slim y sirve la app conuvicorn. Ejemplo de referencia (adáptalo a tu gestor de dependencias):

dockerfile
# ai-service/Dockerfile FROM python:3.12-slim # Avoid interactive prompts and keep the image small ENV PYTHONUNBUFFERED=1 \ PYTHONDONTWRITEBYTECODE=1 WORKDIR /app # Install dependencies first to leverage layer caching COPY requirements.txt . RUN pip install --no-cache-dir -r requirements.txt # Copy the application code COPY . . EXPOSE 8000 # Healthcheck hits a lightweight endpoint that does NOT call the LLM HEALTHCHECK --interval=30s --timeout=5s --retries=3 \ CMD python -c "import urllib.request; urllib.request.urlopen('<http://localhost:8000/health>')" || exit 1 CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

Asegúrate de exponer un endpoint/healthen el servicio IA que responda sin llamar al LLM (por ejemplo, comprobando que la app está viva y, opcionalmente, que la BBDD vectorial responde):

python
# ai-service/app/main.py (extract) from fastapi import FastAPI app = FastAPI(title="AI Service", version="1.0.0") @app.get("/health") def health() -> dict: # Liveness only — must be cheap and must NOT call the LLM return {"status": "ok"}
## Paso 3 —Dockerfiledel backend de negocio (Rails)

dockerfile
# business-backend/Dockerfile FROM ruby:3.3-slim ENV RAILS_ENV=production \ BUNDLE_WITHOUT="development:test" # System packages needed to build gems and run Rails RUN apt-get update -qq && \ apt-get install -y --no-install-recommends build-essential libpq-dev nodejs && \ rm -rf /var/lib/apt/lists/* WORKDIR /app COPY Gemfile Gemfile.lock ./ RUN bundle install COPY . . # Precompile assets at build time (adjust if you use a JS bundler) RUN bundle exec rake assets:precompile EXPOSE 3000 CMD ["bin/rails", "server", "-b", "0.0.0.0", "-p", "3000"]

El patrón es independiente del stack: si tu backend de negocio no es Rails, aplica el mismo esquema (instalar dependencias, copiar código, exponer el puerto, arrancar el servidor). Lo relevante es que sea un contenedor autocontenido.

## Paso 4 — Variables de entorno

Define un.env.examplecon**todas**las claves necesarias, sin valores reales, para que el ejercicio sea reproducible:

dotenv
# .env.example # LLM provider LLM_API_KEY= # AI service AI_SERVICE_PORT=8000 # Internal service-to-service auth (business backend -> AI service) AI_SERVICE_TOKEN=change-me # Relational DB POSTGRES_USER=app POSTGRES_PASSWORD=change-me POSTGRES_DB=estimation # How the business backend reaches the AI service (internal DNS name) AI_SERVICE_URL=http://ai-service:8000

Copia.env.examplea.envy rellena los valores reales en local. Fíjate enAI_SERVICE_URL: dentro de compose los servicios se resuelven por su**nombre de servicio**, no porlocalhost.

## Paso 5 —docker-compose.yml

Levanta las cuatro piezas. Punto clave de seguridad:**el servicio IA no publica puertos al host**(no llevaports:), solo es alcanzable por la red interna; el único servicio conports:es el backend de negocio.

yaml
# docker-compose.yml services: business-backend: build: ./business-backend ports: - "3000:3000" # public entry point environment: DATABASE_URL: postgres://${POSTGRES_USER}:${POSTGRES_PASSWORD}@postgres:5432/${POSTGRES_DB} AI_SERVICE_URL: ${AI_SERVICE_URL} AI_SERVICE_TOKEN: ${AI_SERVICE_TOKEN} depends_on: postgres: condition: service_healthy ai-service: condition: service_healthy ai-service: build: ./ai-service # No "ports:" on purpose — internal only, not reachable from the host environment: LLM_API_KEY: ${LLM_API_KEY} AI_SERVICE_TOKEN: ${AI_SERVICE_TOKEN} VECTOR_DB_URL: <http://vector-db:6333> depends_on: - vector-db postgres: image: postgres:16 environment: POSTGRES_USER: ${POSTGRES_USER} POSTGRES_PASSWORD: ${POSTGRES_PASSWORD} POSTGRES_DB: ${POSTGRES_DB} volumes: - postgres_data:/var/lib/postgresql/data healthcheck: test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER}"] interval: 10s timeout: 5s retries: 5 vector-db: image: qdrant/qdrant:latest # replace with the vector engine you use volumes: - vector_data:/qdrant/storage volumes: postgres_data: vector_data:

Sustituye la imagen devector-dby elVECTOR_DB_URLpor el motor vectorial que ya utilices en el proyecto (Qdrant, Chroma, pgvector sobre el propio Postgres, etc.). Si usas pgvector, la BBDD vectorial y la relacional pueden ser el mismo contenedor.

## Paso 6 — Autenticación entre servicios

El servicio IA no debe aceptar peticiones de cualquiera solo por estar en la red interna. Añade una comprobación mínima de token de servicio en el servicio IA:

python
# ai-service/app/security.py import os from fastapi import Header, HTTPException EXPECTED_TOKEN = os.environ["AI_SERVICE_TOKEN"] def verify_service_token(x_service_token: str = Header(...)) -> None: if x_service_token != EXPECTED_TOKEN: raise HTTPException(status_code=401, detail="Invalid service token")

Y protege el endpoint de estimación con esa dependencia (el/healthse deja sin proteger para que el healthcheck funcione).

Desde el backend de negocio, la llamada al servicio IA incluye el token. El patrón es independiente del stack; en Ruby/Rails:

ruby
# business-backend/app/clients/ai_service_client.rb require "net/http" require "json" class AiServiceClient def initialize @base_url = ENV.fetch("AI_SERVICE_URL") @token = ENV.fetch("AI_SERVICE_TOKEN") end def estimate(payload) uri = URI("#{@base_url}/v1/estimate") request = Net::HTTP::Post.new(uri) request["Content-Type"] = "application/json" request["X-Service-Token"] = @token request.body = payload.to_json response = Net::HTTP.start(uri.host, uri.port) { |http| http.request(request) } JSON.parse(response.body) end end
## Paso 7 — Arrancar y verificar

bash
docker compose build docker compose up

Comprobaciones que debes superar:

1. 

docker compose psmuestra los cuatro servicios arriba yai-service/postgresen estadohealthy.

1. 

Desde el host,http://localhost:3000sirve el frontend del backend de negocio.

1. 

Desde el host, el servicio IA**no**es accesible directamente (no hay puerto publicado) — verifica quehttp://localhost:8000no responde.

1. 

Una estimación lanzada desde la interfaz recorre el flujo completo y devuelve un resultado coherente, es decir: backend de negocio → servicio IA (con token) → BBDD vectorial → respuesta.

1. 

Reinicias todo condocker compose down && docker compose upy el sistema vuelve a funcionar sin pasos manuales (persistencia de datos vía volúmenes).

## Entregables

Sube a tu repositorio del Proyecto 2:

- 

ai-service/Dockerfileybusiness-backend/Dockerfile.

- 

docker-compose.yml.

- 

.env.examplecon todas las variables necesarias (sin valores reales).

- 

Endpoint/healthen el servicio IA y verificación de token de servicio.

- 

UnREADMEcorto (docs/deployment-local.md) con el comando de arranque y las 5 comprobaciones anteriores.

**No**subas tu.envni ninguna clave real.

Envía por mail a[lia@lidr.co](mailto:lia@lidr.co)el enlace a la rama (URL completa de GitHub) y el enlace (o captura) de una ejecución completa dedocker compose upmostrando las cinco comprobaciones del Paso 7, al menos dos días antes de la sesión en vivo. Las entregas posteriores no entran en la revisión.

## Cómo llegar preparado al directo

Trae anotado**qué NO te funcionó**: errores de build, problemas de networking entre contenedores, servicios que arrancan en mal orden, el servicio IA inalcanzable o alcanzable cuando no debería. El primer bloque del directo (15 min) es precisamente para resolver estos problemas en común antes de pasar al despliegue en cloud.

Si te bloqueas del todo, en el repositorio de la solución tienes una versión funcional de referencia; intenta primero resolverlo por tu cuenta y úsala como último recurso o para contrastar.

Explore More PostsThis Lesson is complete.[PreviousSesión 15. Puesta en producción de proyectos, arquitectura e infra — 77 min](https://training.lidr.co/posts/ai-engineering-202604-sesion-15-puesta-en-produccion-de-proyectos-arquitectura-e-infra-77-min)[Next📄 Que entendemos por producción 🔴 — 14 min](https://training.lidr.co/posts/ai-engineering-202604-📄-que-entendemos-por-produccion-🔴-14-min)
