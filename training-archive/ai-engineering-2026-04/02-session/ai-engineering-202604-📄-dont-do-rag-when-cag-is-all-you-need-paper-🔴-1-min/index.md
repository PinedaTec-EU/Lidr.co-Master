---
title: "📄 Don´t do RAG when CAG is all you need (paper) 🔴— 1 min"
source_url: "https://training.lidr.co/posts/ai-engineering-202604-📄-dont-do-rag-when-cag-is-all-you-need-paper-🔴-1-min"
archived_at: "2026-06-12T09:22:05.618Z"
group: "02-session"
---

# 📄 Don´t do RAG when CAG is all you need (paper) 🔴— 1 min

![Antonio Perez](./assets/c3eccac37426c36f.jpg)

[Antonio Perez](https://training.lidr.co/members/36030888)

⏳Tiempo estimado: 1 min

## 

Aquí tenéis como complemento el paper fundacional de CAG presentado por Chan et al. en la ACM Web Conference 2025. Propone precargar todo el conocimiento relevante en la ventana de contexto del LLM mediante KV-cache precomputado, eliminando la necesidad de retrieval en tiempo real y reduciendo significativamente la latencia y complejidad del sistema.

Incluye benchmarks en SQuAD y HotPotQA donde CAG iguala o supera a RAG en precisión, con tiempos de generación notablemente menores. Es la base teórica de la arquitectura que implementamos en el proyecto, especialmente en escenarios donde el conocimiento es acotado y puede cargarse íntegramente en contexto.

[https://arxiv.org/html/2412.15605v1](https://arxiv.org/html/2412.15605v1)
