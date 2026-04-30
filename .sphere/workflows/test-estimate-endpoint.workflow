version: 1.0
id: 48042E857AA94366A24C14B6F75E9647
name: test-estimate-endpoint
description: Llama al mismo endpoint /estimate con la misma transcripción usando openai y ollama, y compara los resultados para validar ambos outputs
output: true
input: []
references:
  apis:
    - name: estimator-cag
      definition: estimator-cag
      version: "1.0"
stages:
  - name: call-openai
    kind: Endpoint
    apiRef: estimator-cag
    endpoint: /api/v1/estimate
    httpVerb: POST
    expectedStatus: 200
    message: "Llamando a friendly_name openai"
    headers:
      Content-Type: application/json
    body: >-
      {
        "transcription": "Reunión con cliente del sector salud. Necesitan una app web para gestión de citas médicas con pacientes, historial clínico resumido, recordatorios automáticos por email y SMS, y un panel de administración para el personal médico. El sistema debe integrarse con su ERP actual vía API REST. Esperan lanzarlo en 3 meses con un equipo pequeño.",
        "friendly_name": "openai"
      }
    output:
      friendly_name: "openai"
      estimation: "{{response.body.estimation}}"
      model: "{{response.body.model}}"
      provider: "{{response.body.provider}}"
      tokens_prompt: "{{response.body.tokens_used.prompt}}"
      tokens_completion: "{{response.body.tokens_used.completion}}"
      tokens_total: "{{response.body.tokens_used.total}}"
      http_status: "{{response.status}}"

  - name: call-ollama
    kind: Endpoint
    apiRef: estimator-cag
    endpoint: /api/v1/estimate
    httpVerb: POST
    expectedStatus: 200
    message: "Llamando a friendly_name ollama"
    headers:
      Content-Type: application/json
    body: >-
      {
        "transcription": "Reunión con cliente del sector salud. Necesitan una app web para gestión de citas médicas con pacientes, historial clínico resumido, recordatorios automáticos por email y SMS, y un panel de administración para el personal médico. El sistema debe integrarse con su ERP actual vía API REST. Esperan lanzarlo en 3 meses con un equipo pequeño.",
        "friendly_name": "ollama"
      }
    output:
      friendly_name: "ollama"
      estimation: "{{response.body.estimation}}"
      model: "{{response.body.model}}"
      provider: "{{response.body.provider}}"
      tokens_prompt: "{{response.body.tokens_used.prompt}}"
      tokens_completion: "{{response.body.tokens_used.completion}}"
      tokens_total: "{{response.body.tokens_used.total}}"
      http_status: "{{response.status}}"

endStage:
  output:
    openai_friendly_name: "{{stage:call-openai.output.friendly_name}}"
    openai_provider: "{{stage:call-openai.output.provider}}"
    openai_model: "{{stage:call-openai.output.model}}"
    openai_http_status: "{{stage:call-openai.output.http_status}}"
    openai_tokens_total: "{{stage:call-openai.output.tokens_total}}"
    openai_estimation: "{{stage:call-openai.output.estimation}}"
    ollama_friendly_name: "{{stage:call-ollama.output.friendly_name}}"
    ollama_provider: "{{stage:call-ollama.output.provider}}"
    ollama_model: "{{stage:call-ollama.output.model}}"
    ollama_http_status: "{{stage:call-ollama.output.http_status}}"
    ollama_tokens_total: "{{stage:call-ollama.output.tokens_total}}"
    ollama_estimation: "{{stage:call-ollama.output.estimation}}"
