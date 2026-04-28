Objetivo
Construir la estructura base del Proyecto 1: una aplicación FastAPI con un endpoint que reciba el texto de una transcripción de reunión y devuelva una estimación de software generada por un LLM, utilizando arquitectura CAG (contexto estático inyectado en el prompt).

Al finalizar este ejercicio, tendrás un servicio funcional que:

Recibe una transcripción de reunión vía API REST

Inyecta contexto estático (ejemplos de estimaciones previas) directamente en el prompt

Envía la petición a un LLM (OpenAI o Anthropic)

Devuelve la estimación generada como respuesta JSON

Contexto del proyecto
Este es el inicio del proyecto que ejecutaremos a lo largo del programa.

La arquitectura inicial es CAG: todo el contexto que necesita el modelo viaja en cada llamada — no hay base de datos, no hay retrieval, no hay persistencia.


Dependencias necesarias:
- fastapi
- uvicorn[standard]
- pydantic-settings
- openai y/o anthropic (según el proveedor que uses)
- python-dotenv

Requisito de versión:
- Python 3.11 o superior