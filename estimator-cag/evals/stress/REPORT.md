# Stress Test Report

## Auditoría de la corrida

- Filas de datos: 375
- Tokens de entrada totales: 699805
- Tokens de salida totales: 118970
- Coste total USD: 0.176353
- Tiempo total observado de iteraciones: 2821452.33 ms
- Intervalos multi-turno ejecutados: 1, 3, 6, 10, 20

## Resumen

| scenario | attachment_kb | p50_latency_ms | p95_latency_ms | total_cost_usd | total_tokens_in | total_tokens_out | wall_clock_ms | exact_hit_rate | semantic_hit_rate | mean_recall |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| attachment_stress | 0 | 8051.13 | 8745.32 | 0.000903 | 1635 | 1096 | 24516.10 | 0.00 | 0.00 | 0.00 |
| attachment_stress | 5 | 6725.04 | 8954.47 | 0.000986 | 2556 | 1005 | 29351.92 | 0.00 | 0.00 | 0.00 |
| attachment_stress | 20 | 7761.44 | 8533.77 | 0.001103 | 2556 | 1200 | 41772.41 | 0.00 | 0.00 | 0.00 |
| attachment_stress | 50 | 6853.00 | 7669.44 | 0.000991 | 2556 | 1013 | 56588.33 | 0.00 | 0.00 | 0.00 |
| attachment_stress | 100 | 7254.77 | 7944.50 | 0.001054 | 2550 | 1119 | 93965.03 | 0.00 | 0.00 | 0.00 |
| contradiction | 0 | 6430.61 | 10440.60 | 0.064159 | 252473 | 43813 | 824379.07 | 0.00 | 0.00 | 0.95 |
| growing | 0 | 6957.37 | 9888.69 | 0.052610 | 214823 | 33977 | 834177.07 | 0.00 | 0.00 | 0.80 |
| pivot | 0 | 7924.90 | 10860.16 | 0.054547 | 220656 | 35747 | 916702.40 | 0.00 | 0.00 | 1.00 |

## Curvas

### Latencia vs tokens

| tokens_in | latency_ms |
|---:|---:|
| 528 | 4277.44 |
| 528 | 3740.31 |
| 528 | 4148.99 |
| 528 | 6327.29 |
| 528 | 3842.55 |
| 528 | 2494.24 |
| 528 | 3774.56 |
| 528 | 3041.66 |
| 528 | 3644.77 |
| 528 | 3593.17 |
| 528 | 3804.11 |
| 528 | 4112.03 |
| 528 | 4582.12 |
| 528 | 4151.88 |
| 528 | 3592.13 |
| 529 | 4957.45 |
| 529 | 3766.94 |
| 529 | 4197.64 |
| 529 | 3335.17 |
| 529 | 3630.43 |
| 529 | 3408.25 |
| 529 | 2788.42 |
| 529 | 3312.99 |
| 529 | 2985.56 |
| 529 | 3308.94 |
| 529 | 4677.27 |
| 529 | 2942.51 |
| 529 | 4873.79 |
| 529 | 3058.41 |
| 529 | 1909.36 |
| 536 | 3940.1 |
| 536 | 4002.21 |
| 536 | 7082.25 |
| 536 | 5118.47 |
| 536 | 4749.89 |
| 536 | 4159.01 |
| 536 | 4760.23 |
| 536 | 4452.19 |
| 536 | 6181.53 |
| 536 | 4951.72 |

### Coste acumulado vs turno

| scenario | turn_index | cumulative_cost_usd |
|---|---:|---:|
| attachment_stress | 1 | 0.000289 |
| attachment_stress | 1 | 0.000657 |
| attachment_stress | 1 | 0.001025 |
| attachment_stress | 1 | 0.001348 |
| attachment_stress | 1 | 0.001678 |
| attachment_stress | 1 | 0.002000 |
| attachment_stress | 1 | 0.002321 |
| attachment_stress | 1 | 0.002689 |
| attachment_stress | 1 | 0.002989 |
| attachment_stress | 1 | 0.003356 |
| attachment_stress | 1 | 0.003648 |
| attachment_stress | 1 | 0.003945 |
| attachment_stress | 1 | 0.004313 |
| attachment_stress | 1 | 0.004681 |
| attachment_stress | 1 | 0.005038 |
| contradiction | 1 | 0.000176 |
| contradiction | 1 | 0.000398 |
| contradiction | 2 | 0.000755 |
| contradiction | 3 | 0.001181 |
| contradiction | 1 | 0.001369 |
| contradiction | 2 | 0.001680 |
| contradiction | 3 | 0.002082 |
| contradiction | 4 | 0.002554 |
| contradiction | 5 | 0.003093 |
| contradiction | 6 | 0.003697 |
| contradiction | 1 | 0.003892 |
| contradiction | 2 | 0.004198 |
| contradiction | 3 | 0.004608 |
| contradiction | 4 | 0.005081 |
| contradiction | 5 | 0.005621 |
| contradiction | 6 | 0.006226 |
| contradiction | 7 | 0.006895 |
| contradiction | 8 | 0.007596 |
| contradiction | 9 | 0.008309 |
| contradiction | 10 | 0.009024 |
| contradiction | 1 | 0.009232 |
| contradiction | 2 | 0.009548 |
| contradiction | 1 | 0.009721 |
| contradiction | 1 | 0.009929 |
| contradiction | 2 | 0.010225 |
| contradiction | 3 | 0.010602 |
| contradiction | 1 | 0.010770 |
| contradiction | 2 | 0.011051 |
| contradiction | 3 | 0.011443 |
| contradiction | 4 | 0.011904 |
| contradiction | 5 | 0.012432 |
| contradiction | 6 | 0.013025 |
| contradiction | 1 | 0.013229 |
| contradiction | 2 | 0.013577 |
| contradiction | 3 | 0.013998 |
| contradiction | 4 | 0.014483 |
| contradiction | 5 | 0.015034 |
| contradiction | 6 | 0.015651 |
| contradiction | 7 | 0.016333 |
| contradiction | 8 | 0.017044 |
| contradiction | 9 | 0.017757 |
| contradiction | 10 | 0.018471 |
| contradiction | 1 | 0.018670 |
| contradiction | 2 | 0.018944 |
| contradiction | 1 | 0.019153 |
| contradiction | 1 | 0.019317 |
| contradiction | 2 | 0.019632 |
| contradiction | 3 | 0.020037 |
| contradiction | 1 | 0.020237 |
| contradiction | 2 | 0.020554 |
| contradiction | 3 | 0.020967 |
| contradiction | 4 | 0.021444 |
| contradiction | 5 | 0.021987 |
| contradiction | 6 | 0.022596 |
| contradiction | 1 | 0.022782 |
| contradiction | 2 | 0.023137 |
| contradiction | 3 | 0.023556 |
| contradiction | 4 | 0.024040 |
| contradiction | 5 | 0.024591 |
| contradiction | 6 | 0.025206 |
| contradiction | 7 | 0.025886 |
| contradiction | 8 | 0.026599 |
| contradiction | 9 | 0.027311 |
| contradiction | 10 | 0.028024 |
| contradiction | 1 | 0.028207 |

### Recall vs N

| turn_index | memory_drift_score |
|---:|---:|
| 1 | 1.0 |
| 1 | 1.0 |
| 1 | 1.0 |
| 1 | 1.0 |
| 1 | 1.0 |
| 1 | 1.0 |
| 1 | 1.0 |
| 1 | 1.0 |
| 1 | 1.0 |
| 1 | 0.0 |
| 1 | 0.0 |
| 1 | 0.0 |
| 1 | 0.0 |
| 1 | 0.0 |
| 1 | 0.0 |
| 1 | 0.0 |
| 1 | 0.0 |
| 1 | 0.0 |
| 1 | 0.0 |
| 1 | 0.0 |
| 1 | 0.0 |
| 1 | 0.0 |
| 1 | 0.0 |
| 1 | 0.0 |
| 1 | 1.0 |
| 1 | 1.0 |
| 1 | 1.0 |
| 1 | 1.0 |
| 1 | 1.0 |
| 1 | 1.0 |
| 1 | 1.0 |
| 1 | 1.0 |
| 1 | 1.0 |
| 2 | 1.0 |
| 2 | 1.0 |
| 2 | 1.0 |
| 2 | 1.0 |
| 2 | 1.0 |
| 2 | 1.0 |
| 2 | 1.0 |
| 2 | 1.0 |
| 2 | 1.0 |
| 3 | 1.0 |
| 3 | 1.0 |
| 3 | 1.0 |
| 3 | 1.0 |
| 3 | 1.0 |
| 3 | 1.0 |
| 3 | 1.0 |
| 3 | 1.0 |
| 3 | 1.0 |
| 1 | 1.0 |
| 1 | 1.0 |
| 1 | 1.0 |
| 1 | 1.0 |
| 1 | 1.0 |
| 1 | 1.0 |
| 1 | 1.0 |
| 1 | 1.0 |
| 1 | 1.0 |
| 2 | 1.0 |
| 2 | 1.0 |
| 2 | 1.0 |
| 2 | 1.0 |
| 2 | 1.0 |
| 2 | 1.0 |
| 2 | 1.0 |
| 2 | 1.0 |
| 2 | 1.0 |
| 3 | 1.0 |
| 3 | 1.0 |
| 3 | 1.0 |
| 3 | 1.0 |
| 3 | 1.0 |
| 3 | 1.0 |
| 3 | 1.0 |
| 3 | 1.0 |
| 3 | 1.0 |
| 4 | 1.0 |
| 4 | 1.0 |

## Lectura

El CAG de esta base empieza a mostrar su límite cuando el historial crece y la observabilidad revela que el `messages_in_window` queda topado mientras el volumen de tokens y la latencia siguen creciendo. En esta corrida el P95 de latencia llegó a 10248.62 ms, el recall medio del fact-tracker quedó en 0.88 y el coste total fue 0.176353 USD.

La dimensión dominante en esta muestra es la memoria contextual: el sistema mantiene coste y contrato HTTP, pero la pérdida de hechos exactos se hace visible conforme aumenta `turn_index` hasta 20. Eso justifica el salto a RAG cuando el proyecto requiere recordar hechos antiguos sin volver a inyectarlos completos en cada turno.

## Notas de adaptación

- Este repo no implementa `anchors` ni `summary` persistidos como en el material de clase; se reportan explícitamente como `0` o vacío para que la limitación quede visible.
- El runner usa el snapshot enriquecido de `GET /api/v1/sessions/{id}` en lugar de parsear logs, porque esta base ya persiste estado por sesión y eso hace determinista la extracción del CSV.
- Para PDFs sintéticos se usa generación determinista local y conversión vía Docling Serve.
