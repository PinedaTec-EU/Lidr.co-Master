version: 1.0
id: 48042E857AA94366A24C14B6F75E9647
name: test-estimate-endpoint
description: Prueba el endpoint POST /api/v1/estimate con una transcripción de reunión real y valida que la respuesta contiene una estimación
output: true
input: []
references:
  apis:
    - name: estimator-cag
      definition: estimator-cag
      version: "1.0"
stages:
  - name: call-estimate
    kind: Endpoint
    apiRef: estimator-cag
    endpoint: /api/v1/estimate
    httpVerb: POST
    expectedStatus: 200
    headers:
      Content-Type: application/json
    body: >-
      {
        "transcript": "Reunión con cliente del sector salud. Necesitan una app web para gestión de citas médicas con pacientes, historial clínico resumido, recordatorios automáticos por email y SMS, y un panel de administración para el personal médico. El sistema debe integrarse con su ERP actual vía API REST. Esperan lanzarlo en 3 meses con un equipo pequeño."
      }
    output:
      estimation: "{{response.body.estimation}}"
      http_status: "{{response.status}}"
endStage:
  output:
    estimation: "{{stage:call-estimate.output.estimation}}"
    http_status: "{{stage:call-estimate.output.http_status}}"
