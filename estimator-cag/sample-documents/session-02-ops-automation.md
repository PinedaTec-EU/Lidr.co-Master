# Reunión 2 - Automatización de Operaciones

## Contexto

Empresa de logística regional con 4 almacenes y 2 centros de cross-docking.  
Necesitan reducir trabajo manual del equipo de operaciones y consolidar trazabilidad.

## Necesidades principales

- Crear una herramienta interna web para incidencias operativas.
- Registrar retrasos, roturas, faltantes y reentregas.
- Asignar incidencias por centro y responsable.
- Generar reportes semanales para dirección.
- Integración con Slack para avisos urgentes.

## Condiciones de entrega

- Primera release en 6 semanas.
- Debe funcionar bien en tablet dentro del almacén.
- Roles mínimos: operador, supervisor y dirección.
- Historial auditable de cambios.

## Pistas técnicas

- Stack preferido: FastAPI + React.
- Base de datos: PostgreSQL.
- Despliegue previsto en Azure.

## Preguntas abiertas

1. ¿Se necesita también adjuntar fotos desde móvil?
2. ¿Habrá integración futura con el TMS?
3. ¿El reporte semanal debe exportarse a Excel o basta con PDF?
