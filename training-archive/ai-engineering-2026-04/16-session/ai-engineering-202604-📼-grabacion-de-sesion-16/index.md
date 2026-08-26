---
title: "📼 Grabación de sesión 16"
source_url: "https://training.lidr.co/posts/ai-engineering-202604-%F0%9F%93%BC-grabacion-de-sesion-16"
archived_at: "2026-08-26T16:26:11.705Z"
group: "16-session"
---

# 📼 Grabación de sesión 16

#### Video

[Video](https://player.vimeo.com/video/1220257317?h=da9239837b)

Hola a todos,

Aquí tenéis el resumen de lo que vimos ayer con Antonio.

**Producción no es subir el proyecto a un servidor.**Un flujo de despliegue merece ese nombre cuando cumple cuatro propiedades: arranca con un solo comando y sin pasos manuales que haya que recordar, expone una única puerta pública, se repite exactamente igual lo dispare quien lo dispare, y es observable de principio a fin. Si el despliegue depende de que una persona concreta se acuerde de algo, todavía no está en producción.

**Tres capas y una sola puerta.**Navegador por HTTPS, gateway (en el ejemplo Caddy), backend de negocio como único servicio publicado, y por debajo una red interna privada con el servicio de IA en FastAPI, Postgres con pgvector, la base relacional y Redis. Ningún servicio interno publica puerto. En la instancia solo están abiertos el 22, el 80 y el 443, y en un entorno real el SSH se limita además por IP de origen.

**Se despliega una imagen, no un commit.**Las imágenes son inmutables y quedan registradas, y eso es lo que convierte un rollback en apuntar a una imagen anterior en lugar de en una noche larga. Por eso también se separan por servicio: cambiar el color de un botón no debería reconstruir el servicio de IA.

**Los secretos nunca viajan en la imagen.**En el pipeline solo hacen falta la clave SSH y el host. El fichero de entorno vive en el servidor, enterrado bajo permisos. Si pierdes el repositorio, no pierdes ninguna clave.

**El pipeline, en orden:**detectar qué ha cambiado, testear el código, comprobar el contrato entre capas, empaquetar las imágenes y desplegar. La detección de cambios por carpetas es lo que evita reconstruirlo todo en cada push.

### La parte específica de IA, que es donde está el valor

**Nunca llames al modelo dentro del flujo de integración continua.**Cuatro razones: el CI necesita determinismo puro (el mismo commit debe dar el mismo resultado), llamar al modelo es lento y te puede llevar el despliegue a horas, consume rate limits de la herramienta, y cuesta dinero. Y hay una razón de fondo más importante: un test que falla al azar no es una señal, y acabas aprendiendo a ignorarlo. En el despliegue no puedes permitirte perder atención.

Lo que sí se comprueba es el contrato: que las rutas de la API respondan, que el modelo de datos sea consistente entre el backend de negocio y el servicio de IA, que no aparezcan 500 donde debería haber respuesta. Los tests usan escenarios, no llamadas reales. La calidad de las respuestas del modelo se mide en otro sitio, con golden set y evals, y eso es exactamente lo que veremos en la sesión 16.

**Escalar horizontalmente rompe tres cosas.**Las sesiones conversacionales que viven en memoria, los procesos en segundo plano que empiezan en una instancia y siguen en otra, y el pool de conexiones a base de datos. Este último es el error que más cuesta diagnosticar la primera vez: si cada réplica abre cien conexiones y la base soporta doscientas, la tercera instancia satura el sistema y empiezan los 502 sin causa aparente. Las respuestas son sacar el estado del proceso a Redis, usar colas de verdad para el trabajo diferido, ajustar los pools por instancia y apoyarse en réplicas de solo lectura.

**El health check no puede compartir pool con el tráfico de la aplicación.**Si tres estimaciones concurrentes bloquean los tres hilos del servidor web, la sonda de salud empieza a fallar, el contenedor se reinicia solo y pierdes todo el trabajo en curso. Y el servidor nunca llegó a caerse: solo estaba ocupado.

**El swap de contenedores se complica con IA.**Una petición web tradicional dura milisegundos. Una petición contra un modelo puede irse a treinta o cincuenta segundos. Eso significa que casi cualquier despliegue en una plataforma activa deja a alguien a medias. No puedes apagar el contenedor viejo mientras haya una llamada al modelo en vuelo: si cortas, no pierdes solo esa respuesta, rompes el contexto de toda la conversación. Hay que esperar a que el estado esté guardado y el usuario redirigido.

**Encolar ya no resuelve todo.**Con procesos lentos, encolar sin límite mantiene el sistema saturado para siempre. La alternativa que se está imponiendo es rechazar con un 503 antes de entrar al flujo de ejecución, acompañado de reintentos escalonados. Y ese 503 es además una métrica: si salta diez minutos una vez por semana, no hay problema; si salta todos los días, el sistema se ha quedado pequeño.

**Referencias de coste y capacidad**de la instancia del ejemplo, para que tengáis un orden de magnitud: una t3.small ronda los 26 dólares al mes y una medium unos 50 euros. Esa instancia da para tres hilos de Puma y unas cinco operaciones simultáneas contra el LLM. Lo que limita no es el tamaño de la conversación, es la concurrencia contra el modelo y la RAM disponible.

**Rollback de la release completa.**Si uno de los servicios de una release no despliega, vuelven atrás todos. Convivir con una versión nueva y una vieja bajo el mismo balanceador es pedir problemas. Y cuando algo falla al pasar de staging a producción, el sospechoso habitual no son las versiones: son los datos legacy que no pasan una validación nueva.

### Recursos mencionados

- 

Kamal, la suite de despliegue que usa Antonio habitualmente:[https://kamal-deploy.org](https://kamal-deploy.org)

- 

Caddy, el proxy inverso del ejemplo, configurable por YAML y más sencillo que nginx a cambio de ser más limitado

- 

Precios de instancias EC2 para calcular vuestro entorno:[https://aws.amazon.com/ec2/pricing/on-demand/](https://aws.amazon.com/ec2/pricing/on-demand/)

Explore More PostsReady to move on to the next Section?[Mark as Complete](#)[Previous6️⃣ Módulo: Despliegue y puesta en producción](https://training.lidr.co/posts/ai-engineering-202604-6️⃣-modulo-despliegue-y-puesta-en-produccion)[NextSesión 15. Puesta en producción de proyectos, arquitectura e infra — 77 min](https://training.lidr.co/posts/ai-engineering-202604-sesion-15-puesta-en-produccion-de-proyectos-arquitectura-e-infra-77-min)
