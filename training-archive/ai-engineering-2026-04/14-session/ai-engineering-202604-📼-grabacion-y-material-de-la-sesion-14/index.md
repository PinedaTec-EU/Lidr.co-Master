---
title: "📼 Grabación y material de la sesión 14"
source_url: "https://training.lidr.co/posts/ai-engineering-202604-%F0%9F%93%BC-grabacion-y-material-de-la-sesion-14"
archived_at: "2026-08-26T16:26:05.402Z"
group: "14-session"
---

# 📼 Grabación y material de la sesión 14

![Antonio Perez](./assets/c3eccac37426c36f.jpg)

[Antonio Perez](https://training.lidr.co/members/36030888)

# Video

[Video](https://player.vimeo.com/video/1212657307?h=37b1bc7727)

## Diapositivas
[Sesi_n_14.pdf](https://media2-production.mightynetworks.com/asset/8936e83e-8fcf-4219-9ca1-91098feb74d7/Sesi_n_14.pdf)

**La idea central de la clase**

Un sistema de agentes de verdad no funciona como un programa lineal, paso a paso. Los agentes toman decisiones por su cuenta y necesitan cierta independencia entre ellos. Por eso el protagonista fue el**supervisor**: un agente que reparte el trabajo según lo que va encontrando, no según un guion fijo.

#### **Errores típicos al construir estos sistemas**

Antonio los mostró con un script que simula fallos comunes:

- 

**Enrutado que no converge**: el sistema vuelve una y otra vez al mismo agente sin decidirse, disparando el costo sin que nadie lo note. Solución: poner un límite de reintentos por agente.

- 

**Estado compartido roto**: el sistema se cuelga tras una interrupción, o dos agentes se pisan el estado entre sí (similar a las condiciones de carrera o al patrón Redux). Siempre debe existir una única versión válida del estado, y el supervisor es quien la cuida.

#### **Cómo funciona el supervisor**

Reemplaza al agente único que antes generaba toda la estimación de un tirón. Ahora decide, paso a paso, a qué especialista le pasa el turno (extractor de requerimientos, buscador de presupuestos, generador de estimaciones, validador de coherencia).

Dos detalles clave:

- 

El supervisor usa un modelo barato y rápido (GPT-4 mini en el ejemplo) solo para decidir a quién le toca hablar, no para el trabajo pesado. Separar "quién decide el tráfico" de "quién hace el trabajo" es de las formas más simples de controlar el costo.

- 

No confundir elestimation_idinterno (entre agentes) con el ID de estimación que ve la aplicación. Son cosas distintas.

#### **Caso 1: Competición entre agentes**

En vez de un solo agente, el supervisor lanza dos en paralelo con criterios distintos (uno conservador, otro agresivo) y compara resultados.

En la demo: estimación agresiva = 585 días, conservadora = 1.317 días (diferencia de 732 días). Con esa disparidad, el sistema calculó un puntaje de confianza bajísimo y marcó el caso para revisión humana.

**Punto más importante de la clase**: ese cálculo de divergencia es determinista, no depende de ningún modelo. La ejecución puede usar modelos, pero el juicio sobre si algo es confiable tiene que ser un cálculo fijo y reproducible, nunca algo que se le pregunte a otro modelo.

#### **¿Cuándo es sobreingeniería?**

Debate abierto en la clase: para algo puntual como armar un presupuesto, toda esta arquitectura puede ser excesiva. Antonio usa algo mucho más simple en su consultora, porque no hace más de 3 o 4 estimaciones por semana.

**Regla que nos ha dejado**: lo que decide cuánta automatización necesitan es el volumen de trabajo.

- 

Poco volumen, cada caso vale mucho (ej. estimación de software) → apóyense en una persona.

- 

Mucho volumen y repetitivo (ej. miles de imágenes o registros por día) → ahí conviene más automatización.

#### **Caso 2: Sandboxing a nivel de agente**

Para cuando un agente puede escribir en una base de datos, archivo o propuesta. Tres capas de contención:

1. 

Se da el permiso asumiendo el riesgo, pero cada escritura queda sujeta a verificación.

1. 

Antes de ejecutar cualquier acción se valida de forma determinista (sin modelo) que el agente tiene permiso, que los argumentos son válidos y que trabaja sobre la estimación correcta.

1. 

Se audita todo, incluidos los intentos denegados: no solo lo que se escribió, sino los intentos bloqueados, porque es una señal temprana útil.

#### **Alucinaciones y trazabilidad**

Por defecto se consideran inválidas y se rechazan, salvo en contextos creativos donde conviene aflojar los controles. En cualquier caso donde la información llega a un cliente o se guarda en base de datos, la tolerancia es cero: todo dato debe poder rastrearse hasta su fuente.

#### **Manejo de logs a gran escala**

No revisarlos a mano. Delegar en un agente de análisis que cruce las trazas con un Golden Set de referencia y devuelva un informe priorizado. Para guardarlos: no meterlos en las tablas de la base de datos (se vuelven lentas), sino como archivos de texto o Markdown en un bucket tipo S3, organizados por fecha, guardando solo la URL de referencia.

En la demo usaron Logfire; para cuando la aplicación crece, Antonio mencionó AWS CloudWatch como alternativa.

#### **Debate: ¿dividir el supervisor en agentes más chicos?**

Pineda propuso separar enrutado y validación para escalar horizontalmente (como microservicios).

Antonio explicó por qué no lo recomienda aquí: dividir implica pasar más contexto entre agentes (sube el costo), y generar una estimación no es una tarea atómica y paralelizable como sí lo sería procesar miles de imágenes por separado. Quedó como una cuestión de balance según el caso, no una regla fija.

#### **Herramientas mencionadas**

- 

**Logfire**(Pydantic): usado en la demo:[https://pydantic.dev/logfire](https://pydantic.dev/logfire)

- 

**AWS CloudWatch**: alternativa mencionada:[https://aws.amazon.com/es/cloudwatch/](https://aws.amazon.com/es/cloudwatch/)

- 

**Elastic Stack / ELK**: mencionado por Pineda:[https://www.elastic.co/es/elastic-stack](https://www.elastic.co/es/elastic-stack)

- 

**NATS**: broker de mensajería, surgió en el debate sobre escalar:[https://nats.io/](https://nats.io/)

- 

**Docker**: nombrado de paso, pensando en la próxima sesión:[https://www.docker.com/](https://www.docker.com/)

También se mencionaron SOC 2 y FIPS 140-2 como ejemplo de estándares de cumplimiento dentro de un caso límite armado a propósito, no como algo a implementar en el ejercicio.

#### **Próxima sesión**

**Será el 20 de agosto:**Infraestructura y despliegue (Docker, nube, arquitecturas multiservicio). Si ya tienen experiencia en despliegue, la van a encontrar más básica de lo habitual: está pensada para quienes recién se familiarizan con el tema.

#### **Para cerrar**

La recomendación de Antonio: no se lancen a construir arquitecturas de agentes complicadas desde el día uno. Empiecen simple y avancen de a poco. Un sistema de agentes se descontrola fácil y el costo escala rápido si no está controlado.

Buenas vacaciones, nos vemos el 20 de agosto.

Aquí el[ROTI](https://training.lidr.co/posts/ayudanos-a-mejorar-cuentanos-cual-fue-tu-roti-del-5-al-1-y-deja-tus-comentarios-abajo-para-que-el-equipo-pueda-mejorar-cada-semana-como-valorarias-esta-sesion-14-104976758?utm_source=manual)por si no has participado en la sesión en vivo
Explore More PostsReady to move on to the next Section?[Mark as Complete](#)[Previous📼 Grabación y material de la sesión 13](https://training.lidr.co/posts/ai-engineering-202604-📼-grabacion-y-material-de-la-sesion-13)[NextSesión 12: Introducción a agentes de IA — 123 min](https://training.lidr.co/posts/ai-engineering-202604-sesion-12-introduccion-a-agentes-de-ia-123-min)
