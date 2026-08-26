---
title: "6️⃣ Módulo: Despliegue y puesta en producción"
source_url: "https://training.lidr.co/posts/ai-engineering-202604-6%EF%B8%8F%E2%83%A3-modulo-despliegue-y-puesta-en-produccion"
archived_at: "2026-08-26T16:26:08.500Z"
group: "98-misc"
---

# 6️⃣ Módulo: Despliegue y puesta en producción

![Antonio Perez](./assets/c3eccac37426c36f.jpg)

[Antonio Perez](https://training.lidr.co/members/36030888)

En este módulo tomas el sistema que has construido durante los módulos anteriores —el que recibe una transcripción, extrae requisitos, recupera presupuestos históricos, orquesta sus agentes y devuelve una estimación con su nivel de confianza y sus fuentes— y dejas de tratarlo como algo que solo sabe arrancar en tu portátil.

Hasta ahora, "funciona" significaba que corría en tu máquina, con el orden de arranque que solo tú recuerdas y las claves exportadas en tu terminal. En este módulo cambias de perspectiva otra vez: pasas de tener un sistema que funciona a tener un sistema que se puede operar, sin que dependa de vosotros estar delante.

Esto implica entender que:

- 

Producción no es un lugar (un servidor en la nube), sino un conjunto de promesas: el sistema arranca igual en cualquier máquina, sobrevive a que una pieza falle, lo puede operar alguien que no lo escribió, y es seguro por defecto.

- 

Hay una decisión que ordena toda la arquitectura: qué pieza mira a internet y cuál no. En vuestro sistema, el servicio IA —quien custodia la clave del LLM— no se expone jamás.

- 

Reproducible no es lo mismo que operable: un sistema que solo entendéis vosotros, aunque arranque con un comando, sigue sin estar listo para producción.

A lo largo del módulo vas a llevar tu proyecto por el camino completo entre "funciona en mi máquina" y "está en producción": documentar el sistema para quien lo va a operar y usar, decidir dónde partirlo en servicios y diseñar el contrato entre ellos, empaquetar cada pieza en un contenedor, montar un pipeline que teste tu código sin depender del modelo, y desplegarlo en infraestructura real respetando la frontera público/privado.

👉Al finalizar este módulo:

- 

Habrás documentado tu sistema para sus tres audiencias reales: quien lo integra, quien lo opera y quien lo usa.

- 

Sabrás cuándo una frontera entre servicios compra algo (lenguaje, escalado, despliegue, aislamiento de fallos) y cuándo es solo complejidad de más.

- 

Habrás contenerizado tu proyecto con Docker y lo levantarás entero con un único comando vía docker-compose.

- 

Entenderás por qué el pipeline de CI/CD no debe llamar al modelo real, y qué debe testear en su lugar.

- 

Habrás desplegado tu sistema en cloud, con el servicio IA y las bases de datos en red privada, y el backend de negocio como único punto de entrada público.

Cómo operamos en este módulo Este módulo cierra el ciclo de construcción del programa, y el pre-work pesa más de lo habitual: antes del directo tienes que haber dockerizado tu proyecto y comprobado que arranca íntegro con docker-compose.

✓ Completa el ejercicio de dockerización antes de la sesión. Es entrega obligatoria: sin tu proyecto contenerizado, no hay sobre qué desplegar en el directo.

✓ El mentor traerá el sistema ya documentado, partido en servicios y contenerizado, y lo desplegará en cloud en tiempo real. Verás las decisiones aplicadas sobre un sistema real, no solo explicadas.

✓ Explicaremos por qué cada frontera y cada capa está donde está: qué compra separar el servicio IA del backend de negocio, por qué el contrato entre ambos se diseña así, y por qué el pipeline no toca el modelo.

✓ Haremos demostraciones del despliegue en vivo. Veremos cómo se materializa la frontera público/privado sobre infraestructura real, y qué pasa si os equivocáis de lado.

✓ Reservamos tiempo para tus bloqueos concretos. El primer bloque del directo es para resolver lo que no te funcionó en el pre-work, antes de pasar al despliegue en cloud.

Para aprovechar la sesión: completa el pre-work y llega con anotado qué no te funcionó (errores de build, problemas de networking entre contenedores, el servicio IA alcanzable cuando no debería). Trae dudas concretas sobre tu propio despliegue, no sobre teoría.

- 

![image](./assets/2192662394-0eb8d23df48ae83a2319b2709e830c17a7a531e99127527766b2102b7e7851bc-d_1280.jpg)

![image](./assets/2192662394-0eb8d23df48ae83a2319b2709e830c17a7a531e99127527766b2102b7e7851bc-d_1280-2.jpg)

[📼 Grabación de sesión 16

- Visibility: Visible
- Unlocking: None
- Completion: Button
- Comments: On
- Thumbnail: Default
](https://training.lidr.co/posts/ai-engineering-202604-📼-grabacion-de-sesion-16)Video Hola a todos, Aquí tenéis el resumen de lo que vimos ayer con Antonio. Producción no es subir el proyecto a un...
Explore More Posts[Previous🆙 Evalúa el contenido de este Módulo](https://training.lidr.co/posts/ai-engineering-202604-🆙-evalua-el-contenido-de-este-modulo-98724381)[Next📼 Grabación de sesión 16](https://training.lidr.co/posts/ai-engineering-202604-📼-grabacion-de-sesion-16)
