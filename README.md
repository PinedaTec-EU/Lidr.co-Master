# LIdrMaster

Repositorio de ejercicios y extensiones alrededor de CAG, RAG y ejecución determinista de workflows con SphereIntegrationHub.

## Proyectos

| Proyecto | Puerto | Rol | Fase IA |
|----------|--------|-----|---------|
| [`estimator-cag`](./estimator-cag) | `8000` | API que estima proyectos software desde una transcripción | CAG |
| [`sih-smart-analysis`](./sih-smart-analysis) | `8010` | API que ejecuta workflows SIH y analiza reports históricos | CAG ahora, RAG preparado |

## Relación entre piezas

```mermaid
flowchart LR
    User["Usuario / UI / curl"]
    SIH["SIH CLI<br/>~/.dotnet/tools/sih"]
    Workflow[".sphere/workflows/test-estimate-endpoint.workflow"]
    Estimator["estimator-cag API<br/>FastAPI :8000"]
    Reports[".sphere/workflows/output<br/>JSON + HTML reports"]
    Smart["sih-smart-analysis API<br/>FastAPI :8010"]
    CAG["Recent CAG<br/>últimas 5 ejecuciones"]
    RAG["Semantic RAG<br/>histórico similar"]

    User --> Smart
    User --> Estimator
    Smart -->|POST /executions/run| SIH
    SIH --> Workflow
    Workflow -->|HTTP stages| Estimator
    SIH --> Reports
    Smart --> Reports
    Smart --> CAG
    Smart --> RAG
```

## Fases

```mermaid
flowchart TD
    A["Fase 0<br/>API piloto estimator-cag"] --> B["Fase 1<br/>SIH ejecuta workflow determinista"]
    B --> C["Fase 2<br/>SIH genera reports JSON/HTML"]
    C --> D["Fase 3<br/>sih-smart-analysis CAG<br/>analiza últimas 5 ejecuciones"]
    D --> E["Fase 4<br/>sih-smart-analysis RAG<br/>recupera ejecuciones similares del histórico"]
    E --> F["Fase 5<br/>Dashboards / tendencias / regresiones"]
```

## API Versioning

Ambas APIs exponen sus endpoints funcionales bajo `/api/v1`.

La transición de CAG a RAG en `sih-smart-analysis` no exige cambiar de versión si se mantiene el contrato externo y solo cambia la estrategia interna del controller/use case. Si aparece un contrato incompatible, por ejemplo otro shape de respuesta o un modelo de fuentes distinto, entonces se debería añadir `/api/v2` manteniendo `/api/v1` estable.

## Repo Skills

Este repo incluye skills locales para mantener disciplina de trabajo:

| Skill | Propósito |
|-------|-----------|
| [keep-project-docs-updated](./.codex/skills/keep-project-docs-updated/SKILL.md) | Mantener actualizado el README del proyecto afectado cuando cambien APIs, arquitectura, fases, configuración, SIH, CAG/RAG o tests. |
| [make-functional-commits](./.codex/skills/make-functional-commits/SKILL.md) | Preparar commits pequeños, funcionales, validados y con documentación incluida cuando corresponda. |
