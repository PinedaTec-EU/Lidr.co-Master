---
title: "📜 Política de Gestión de Repositorios"
source_url: "https://training.lidr.co/posts/ai-engineering-202604-📜-politica-de-gestion-de-repositorios"
archived_at: "2026-06-12T09:20:28.361Z"
group: "00-intro"
---

# 📜 Política de Gestión de Repositorios

![Antonio Perez](./assets/c3eccac37426c36f.jpg)

[Antonio Perez](https://training.lidr.co/members/36030888)
### 1. Objetivo

Establecer lineamientos claros para la gestión de repositorios de proyectos dentro del programa AI Engineering, equilibrando la visibilidad profesional de los alumnos con la protección de información sensible y la calidad exigida en entornos de producción.

Este enfoque es coherente con el objetivo del programa: construir sistemas de IA reales, no solo prototipos

### 2. Clasificación de repositorios

#### 2.1 Repositorios públicos

Los repositorios pueden ser públicos cuando cumplan con las siguientes condiciones:

- 

El proyecto es representativo de un sistema de IA real (no solo una demo o wrapper básico)

- 

Puede formar parte del portfolio profesional como AI Engineer

- 

No contiene información sensible o confidencial

- 

Incluye documentación técnica adecuada (README + arquitectura + decisiones clave)

- 

Refleja buenas prácticas de ingeniería (estructura, testing, modularidad, etc.)

#### 2.2 Repositorios privados

Se recomienda mantener repositorios privados en los siguientes casos:

- 

El proyecto contiene credenciales, tokens o claves de acceso

- 

Se utilizan APIs reales con facturación o acceso a datos sensibles

- 

Se trabaja con datos reales de empresa o datasets no públicos

- 

Incluye lógica interna, arquitectura propietaria o decisiones no publicables

- 

El sistema no está preparado para ser expuesto (ej. sin guardrails, sin validación, sin seguridad)

### 3. Buenas prácticas obligatorias

Para todos los repositorios, especialmente los públicos, se deben cumplir las siguientes prácticas:

- 

No incluir archivos.enven el repositorio

- 

No exponer claves API, tokens, contraseñas o credenciales

- 

No incluir datos reales de usuarios o información personal

- 

Utilizar.env.examplepara documentar variables necesarias

- 

Emplear datos ficticios o anonimizados

- 

Incluir un README técnico con:

- 

Setup

- 

Arquitectura

- 

Decisiones de diseño

- 

Limitaciones del sistema

Adicionalmente, en AI Engineering:

- 

Documentar la arquitectura del sistema (CAG, RAG, agentes, etc.)

- 

Explicar cómo se gestiona:

- 

latencia

- 

coste

- 

calidad (evaluación)

- 

seguridad (guardrails)

- 

Incluir trazabilidad básica (logs, debugging o evaluación si aplica)

### 4. Responsabilidad

Cada alumno es responsable del contenido que publica en sus repositorios.

AI Engineering trabaja con sistemas que pueden implicar datos reales, costes y riesgos operativos, por lo que la responsabilidad individual es crítica.

LIDR no se hace responsable por la exposición de información sensible derivada de un uso inadecuado de estas prácticas.

### 5. Enfoque de visibilidad

La publicación de repositorios forma parte del posicionamiento profesional como AI Engineer.

A diferencia de AI4Devs, aquí no se busca solo mostrar uso de herramientas, sino capacidad de:

- 

Diseñar arquitectura

- 

Tomar decisiones técnicas

- 

Construir sistemas robustos

- 

Pensar en producción

Se recomienda priorizar calidad sobre cantidad:
Es mejor un proyecto sólido y bien documentado que varios incompletos.

### 6. Recomendaciones adicionales

- 

Revisar el repositorio antes de hacerlo público (especialmente dependencias y claves)

- 

Utilizar herramientas de escaneo de secretos

- 

Documentar decisiones técnicas (no solo código)

- 

Incluir diagramas de arquitectura cuando sea posible

- 

Validar que el proyecto no es solo un “wrapper” de API, sino un sistema con lógica propia

- 

En caso de duda, mantener el repositorio privado
