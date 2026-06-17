---
title: "🗒️ Tokenización: conceptos avanzados 🔴 — 39 min"
source_url: "https://training.lidr.co/posts/ai-engineering-202604-🗒️-tokenizacion-conceptos-avanzados-🔴-39-min"
archived_at: "2026-06-12T09:21:25.284Z"
group: "01-session"
---

# 🗒️ Tokenización: conceptos avanzados 🔴 — 39 min

![Antonio Perez](./assets/c3eccac37426c36f.jpg)

[Antonio Perez](https://training.lidr.co/members/36030888)

⏳Tiempo estimado: 39 min

## El problema que resuelve la tokenización

Los modelos de lenguaje no leen texto. No ven palabras, ni frases, ni párrafos. Un transformer opera exclusivamente sobre secuencias de números enteros. La tokenización es el proceso que convierte texto legible por humanos en una secuencia de IDs numéricos que el modelo puede procesar, y viceversa.

Cuando envías el string"How long would a database migration take?"a una API, lo que llega al modelo es algo como[4438, 1317, 1053, 264, 7316, 12507, 1935, 30]. Cada número es un**token**: una unidad discreta que el modelo ha aprendido a manejar durante su entrenamiento. La calidad de esta conversión afecta directamente a la calidad de las respuestas, al coste de cada llamada, y al rendimiento del sistema.

Para un AI Engineer, entender la tokenización no es un ejercicio académico. Es entender la unidad de medida fundamental de todo tu stack: cada decisión de diseño — la longitud de tu system prompt, el idioma en el que operas, el formato de datos que inyectas como contexto — se traduce en tokens, y los tokens se traducen en dinero y en latencia.

## 1. De texto a números: el flujo completo

El proceso de tokenización tiene tres fases:

**Fase 1 — Codificación a bytes:**El texto se convierte a su representación en bytes usando UTF-8. El carácterAocupa 1 byte, el carácterñocupa 2 bytes, y un emoji como🚀ocupa 4 bytes. Esto es importante: los idiomas con caracteres no-ASCII (español, chino, árabe) consumen más bytes por carácter.

**Fase 2 — Pre-tokenización:**El texto se divide en fragmentos usando reglas (normalmente expresiones regulares) que separan por espacios, puntuación y categorías de caracteres (letras, números, símbolos). Estas reglas garantizan que ciertos merges nunca crucen fronteras de categoría — un número nunca se fusionará con una letra.

**Fase 3 — BPE (Byte Pair Encoding):**Dentro de cada fragmento, el algoritmo BPE aplica una tabla de merges aprendida durante el entrenamiento del tokenizador para combinar bytes en tokens cada vez más grandes. El resultado es una secuencia de IDs numéricos.

Veámoslo en código:

python
import tiktoken enc = tiktoken.encoding_for_model("gpt-4o-mini") text = "PostgreSQL migration" tokens = enc.encode(text) print(f"Text: '{text}'") print(f"Token IDs: {tokens}") print(f"Count: {len(tokens)} tokens") print() # Reverse: see what each token represents for token_id in tokens: decoded = enc.decode([token_id]) print(f" ID {token_id:>6d} → '{decoded}'")

Salida aproximada:
Text: 'PostgreSQL migration' Token IDs: [5765, 48528, 12507] Count: 3 tokens ID 5765 → 'Postgre' ID 48528 → 'SQL' ID 12507 → ' migration'

Observa que" migration"incluye el espacio anterior como parte del token. Esto no es un error — es una decisión de diseño del tokenizador que afecta a cómo el modelo procesa el texto.

## 2. BPE: el algoritmo que domina la industria

Byte Pair Encoding es el algoritmo de tokenización usado por GPT-2, GPT-3, GPT-4, GPT-5, Llama, Mistral, y la mayoría de LLMs actuales. Fue propuesto originalmente en 1994 como un algoritmo de compresión de datos, y adaptado al procesamiento de lenguaje natural en 2015.

### Cómo funciona el entrenamiento de un tokenizador BPE

El entrenamiento del tokenizador (que es independiente del entrenamiento del modelo) sigue un proceso iterativo:

1. 

Se parte de un vocabulario base de 256 tokens (uno por cada valor de byte posible)

1. 

Se escanea un corpus de texto grande y se cuenta la frecuencia de cada par adyacente de tokens

1. 

Se fusiona el par más frecuente en un nuevo token y se añade al vocabulario

1. 

Se repite hasta alcanzar el tamaño de vocabulario deseado

python
# Simplified BPE training illustration (educational, not production) # Starting vocabulary: individual characters # Training corpus: "the cat in the hat" # Iteration 1: most frequent pair is ('t', 'h') → merge into 'th' # Iteration 2: most frequent pair is ('th', 'e') → merge into 'the' # Iteration 3: most frequent pair is ('a', 't') → merge into 'at' # ...and so on for thousands of iterations # The result is a merge table: an ordered list of pairs to merge # This table IS the tokenizer — it defines how text is broken into tokens

El resultado del entrenamiento es una**tabla de merges**ordenada: una lista de pares de tokens que deben fusionarse, en el orden en que fueron aprendidos. Esta tabla es lo que define el tokenizador. Cuando tokenizas un texto nuevo, el algoritmo aplica estas mismas reglas de merge en el mismo orden.

### Tamaños de vocabulario actuales

El tamaño del vocabulario ha crecido significativamente en los últimos años:

python
import tiktoken # Different tokenizers have different vocabulary sizes encodings = { "gpt-2": "gpt2", # ~50K tokens (2019) "gpt-3.5/4": "cl100k_base", # ~100K tokens (2023) "gpt-4o": "o200k_base", # ~200K tokens (2024) } for label, encoding_name in encodings.items(): enc = tiktoken.get_encoding(encoding_name) print(f"{label:15s} → {encoding_name:15s} → {enc.n_vocab:>7,} tokens")

Un vocabulario más grande significa secuencias de tokens más cortas (menos cómputo en el transformer), mejor cobertura multilingüe, pero matrices de embedding más grandes. La tendencia es clara: los vocabularios se han cuadruplicado en tres años.

### BPE vs otros algoritmos

Existen tres algoritmos principales de tokenización para LLMs:

**BPE (Byte Pair Encoding)**— El estándar de facto. Usado por GPT, Llama, Mistral. Parte de caracteres individuales y fusiona los pares más frecuentes iterativamente. La variante moderna es**byte-level BPE**, que opera sobre los 256 valores de byte posibles en lugar de sobre caracteres Unicode, lo que elimina el problema de caracteres desconocidos.

**WordPiece**— Usado por BERT. Similar a BPE pero el criterio de merge no es frecuencia bruta sino la maximización de la verosimilitud del corpus de entrenamiento. En la práctica, produce resultados similares a BPE.

**Unigram**— Usado por T5 y ALBERT. Toma el enfoque opuesto: empieza con un vocabulario enorme y va eliminando tokens cuya ausencia causa el menor incremento de loss. Captura mejor las terminaciones morfológicas (-ing,-tion,-mente) que BPE.

En el ecosistema actual, BPE domina aplastantemente para modelos generativos. Si trabajas con APIs de OpenAI, Anthropic o modelos open source, estás usando BPE.

## 3. Lo que el tokenizador revela: patrones que te afectan en producción

### 3.1. El español consume más tokens que el inglés

Esta es probablemente la implicación más directa para productos que operan en español:

python
import tiktoken enc = tiktoken.encoding_for_model("gpt-4o-mini") comparisons = [ ("English", "What are the main risks of migrating to microservices?"), ("Spanish", "¿Cuáles son los principales riesgos de migrar a microservicios?"), ("French", "Quels sont les principaux risques de la migration vers les microservices?"), ("Japanese", "マイクロサービスへの移行の主なリスクは何ですか？"), ] print(f"{'Language':12s} {'Characters':>12s} {'Tokens':>8s} {'Chars/token':>12s}") print("-" * 48) for language, text in comparisons: tokens = enc.encode(text) ratio = len(text) / len(tokens) print(f"{language:12s} {len(text):>12d} {len(tokens):>8d} {ratio:>11.1f}")

El resultado típico muestra que el español consume entre un 20% y un 40% más de tokens que el inglés para el mismo contenido semántico. El japonés y el chino pueden consumir el doble o más. Esto se debe a que el corpus de entrenamiento del tokenizador está dominado por texto en inglés: las palabras en inglés aparecen con más frecuencia, generan más merges, y se representan con menos tokens.

**Implicación práctica:**Si tu producto opera en español, tu system prompt en español consume más tokens que el equivalente en inglés, tu contexto inyectado consume más tokens, y las respuestas del modelo consumen más tokens. Todo esto se multiplica por cada llamada y cada turno de conversación.

**Decisión de diseño:**Algunos equipos escriben sus system prompts en inglés (aunque la respuesta sea en español) para reducir el consumo de tokens de entrada. Cada turno reenvía el system prompt completo — si tu prompt ocupa 200 tokens en español y 150 en inglés, la diferencia acumulada en una conversación de 20 turnos es de 1.000 tokens de entrada adicionales.

### 3.2. El código es relativamente eficiente en tokens

python
import tiktoken enc = tiktoken.encoding_for_model("gpt-4o-mini") code_samples = { "Python function": '''def calculate_total(items, tax_rate=0.21): subtotal = sum(item.price for item in items) return subtotal * (1 + tax_rate)''', "JSON payload": '''{ "project": "payment-migration", "team_size": 5, "estimated_weeks": 12, "confidence": "medium", "risks": ["data-loss", "downtime", "integration-failures"] }''', "SQL query": '''SELECT u.name, COUNT(o.id) as order_count, SUM(o.total) as revenue FROM users u JOIN orders o ON u.id = o.user_id WHERE o.created_at >= '2024-01-01' GROUP BY u.name HAVING SUM(o.total) > 1000 ORDER BY revenue DESC;''', } for label, code in code_samples.items(): tokens = enc.encode(code) words = len(code.split()) print(f"{label:20s}: {len(tokens):>4d} tokens, {len(code):>4d} chars, {words:>3d} words")

El código se tokeniza de forma relativamente eficiente porque los keywords de programación (def,return,SELECT,FROM) son muy frecuentes en el corpus de entrenamiento del tokenizador y tienen tokens dedicados. Sin embargo, los nombres de variables y funciones específicos de tu dominio (calculate_total,payment-migration) se fragmentan más.

**Implicación práctica:**Cuando inyectas código fuente como contexto para un LLM (por ejemplo, para code review o para generar tests), el coste en tokens es menor de lo que intuitivamente esperarías. Un archivo de 100 líneas de Python puede consumir solo 300-500 tokens.

### 3.3. Los espacios, saltos de línea e indentación son tokens

python
import tiktoken enc = tiktoken.encoding_for_model("gpt-4o-mini") # Leading spaces matter texts = [ "Hello", " Hello", " Hello", " Hello", ] for text in texts: tokens = enc.encode(text) decoded = [f"'{enc.decode([t])}'" for t in tokens] print(f"'{text}' → {len(tokens)} tokens: {decoded}")

Para el tokenizador,"Hello"y" Hello"(con espacio) son tokens completamente diferentes con IDs distintos. Esto tiene implicaciones sutiles: si tu código construye prompts concatenando strings sin cuidado, puedes estar alimentando al modelo con tokens inesperados.

La indentación en JSON y en código también consume tokens. Un JSON compacto (sin indentación ni saltos de línea) consume significativamente menos tokens que el mismo JSON formateado con pretty-print:

python
import tiktoken import json enc = tiktoken.encoding_for_model("gpt-4o-mini") data = { "project": "migration", "tasks": [ {"name": "schema-analysis", "hours": 40}, {"name": "data-transfer", "hours": 80}, {"name": "testing", "hours": 60} ] } compact = json.dumps(data) pretty = json.dumps(data, indent=2) compact_tokens = enc.encode(compact) pretty_tokens = enc.encode(pretty) print(f"Compact JSON: {len(compact):>4d} chars → {len(compact_tokens):>3d} tokens") print(f"Pretty JSON: {len(pretty):>4d} chars → {len(pretty_tokens):>3d} tokens") print(f"Overhead: {len(pretty_tokens) - len(compact_tokens)} extra tokens ({(len(pretty_tokens)/len(compact_tokens) - 1)*100:.0f}% more)")

**Implicación práctica:**Cuando inyectas datos estructurados (JSON, YAML) como contexto para el modelo, envíalos en formato compacto. La indentación añade legibilidad para humanos pero no aporta nada al modelo y consume tokens innecesarios. En contextos donde cada token cuenta (ventanas de contexto llenas, conversaciones largas), esta optimización es relevante.

### 3.4. Los números se tokenizan de forma inconsistente

python
import tiktoken enc = tiktoken.encoding_for_model("gpt-4o-mini") numbers = ["42", "100", "1000", "12345", "99999", "123456789"] for num in numbers: tokens = enc.encode(num) decoded = [f"'{enc.decode([t])}'" for t in tokens] print(f"{num:>12s} → {len(tokens)} token(s): {decoded}")

Los números se fragmentan de formas impredecibles:"100"puede ser un solo token mientras que"101"se divide en"10"+"1". Esto explica por qué los LLMs son notoriamente malos en aritmética: el modelo nunca ve los dígitos individuales alineados para poder hacer cálculos columna por columna. Cuando ve el token"1234", lo ve como una unidad semántica opaca, no como la secuencia 1-2-3-4.

**Implicación práctica:**Nunca dependas de un LLM para hacer cálculos aritméticos precisos. Si tu producto necesita sumar, multiplicar o comparar números, hazlo en tu código y pasa el resultado al modelo. Los LLMs son herramientas de lenguaje, no calculadoras.

### 3.5. Los tokens especiales

Además de los tokens de texto, cada tokenizador incluye**tokens especiales**que marcan estructura: inicio/fin de mensaje, separadores de roles, delimitadores de herramientas, etc.

python
import tiktoken enc = tiktoken.encoding_for_model("gpt-4o-mini") # Special tokens are typically not accessible through normal encoding # but they exist in the vocabulary special_tokens = { "<|endoftext|>": "End of text / message separator", "<|im_start|>": "Start of a message (used in chat format)", "<|im_end|>": "End of a message (used in chat format)", } print("Special tokens in the GPT-4o tokenizer:") for token, description in special_tokens.items(): print(f" {token:20s} → {description}")

Estos tokens son invisibles para ti como usuario de la API — el SDK los gestiona automáticamente. Pero consumen tokens y forman parte del conteo que ves enusage.input_tokens. Por eso el número de tokens que la API reporta siempre es ligeramente mayor que el que obtienes al tokenizar solo tu texto: los tokens especiales de formato de chat se añaden por encima.

## 4. Tokenización y ventanas de contexto

### 4.1. Qué es la ventana de contexto

La ventana de contexto es el número máximo de tokens que un modelo puede procesar en una sola llamada. Este límite incluye**todo**: system prompt + historial de mensajes + entrada del usuario + respuesta del modelo. No es solo tu input — la respuesta del modelo también cuenta dentro de la ventana.

python
# Context window sizes (as of early 2026) context_windows = { "gpt-4o-mini": 128_000, "gpt-5.4": 200_000, "claude-haiku-4-5": 200_000, "claude-sonnet-4-6": 200_000, "gemini-2.5-flash": 1_048_576, # 1M tokens "gemini-3-pro": 2_097_152, # 2M tokens } print(f"{'Model':25s} {'Context window':>15s} {'~Pages of text':>15s}") print("-" * 58) for model, tokens in context_windows.items(): # Rough estimate: 1 page ≈ 500 words ≈ 670 tokens pages = tokens / 670 print(f"{model:25s} {tokens:>15,} {pages:>14,.0f}")
### 4.2. Cómo se llena la ventana en una conversación

El aspecto más contra-intuitivo de la ventana de contexto es cómo crece en conversaciones multi-turno:

python
import tiktoken enc = tiktoken.encoding_for_model("gpt-4o-mini") SYSTEM_PROMPT = """You are a principal software architect specializing in payment systems, PCI-DSS compliance, and large-scale distributed architectures. You have led monolith-to-microservices migrations at three fintech companies processing over $1B in annual transactions.""" # Simulated conversation: each turn adds to the cumulative input conversation = [ ("user", "We're planning to migrate our payment service from a Rails monolith to microservices."), ("assistant", "Before diving into the migration strategy, I need to understand your current architecture..."), ("user", "We process about 50,000 transactions per day, PostgreSQL 16, Redis for caching."), ("assistant", "With 50K daily transactions, you're in a range where a careful strangler-fig pattern..."), ("user", "What about PCI-DSS compliance during the migration? We can't afford downtime."), ("assistant", "PCI-DSS compliance during migration is your highest-risk area. You need to maintain..."), ("user", "Our team is 8 backend engineers. How should we split the work?"), ("assistant", "With 8 engineers, I'd recommend splitting into two streams running in parallel..."), ("user", "Give me a rough timeline with milestones."), ] system_tokens = len(enc.encode(SYSTEM_PROMPT)) overhead_per_message = 4 # Approximate overhead from special tokens per message print(f"System prompt: {system_tokens} tokens (sent with EVERY turn)\\n") print(f"{'Turn':>5s} {'Role':>10s} {'Msg tokens':>12s} {'Cumul. input':>14s} {'System %':>10s}") print("-" * 55) cumulative = system_tokens for i, (role, text) in enumerate(conversation): msg_tokens = len(enc.encode(text)) + overhead_per_message cumulative += msg_tokens system_pct = (system_tokens / cumulative) * 100 print(f"{i+1:>5d} {role:>10s} {msg_tokens:>12d} {cumulative:>14d} {system_pct:>9.1f}%")

Cada turno acumula todos los tokens anteriores. El system prompt se reenvía con cada llamada. En el turno 9, estás pagando el system prompt por novena vez, más todo el historial de la conversación.

**Implicación práctica:**En una conversación de 20 turnos con un system prompt de 500 tokens, los tokens del system prompt acumulan 10.000 tokens de entrada extra. Esto es coste puro sin valor añadido. Estrategias de mitigación:

- 

**Prompt caching**(Anthropic ofrece 90% de descuento en cache hits, OpenAI también lo soporta)

- 

**Truncado de historial**(mantener solo los últimos N turnos)

- 

**Resumen de turnos anteriores**(comprimir el historial en un resumen breve)

- 

previous_response_id(OpenAI gestiona el contexto y optimiza caché internamente)

### 4.3. Contar tokens antes de enviar

Gemini ofrece un endpoint gratuitocount_tokens()para estimar el consumo antes de la llamada. Para OpenAI, puedes usartiktokenlocalmente:

python
import tiktoken def estimate_call_tokens(system_prompt, messages, model="gpt-4o-mini"): """ Estimate the number of input tokens for an API call. This is an approximation — the actual count includes special tokens added by the API that we can't perfectly replicate locally. """ enc = tiktoken.encoding_for_model(model) total = len(enc.encode(system_prompt)) total += 4 # Overhead for system message formatting for msg in messages: total += len(enc.encode(msg["content"])) total += 4 # Overhead per message (role tokens, delimiters) total += 2 # Priming tokens for the assistant's response return total # Example: estimate before calling the API system = "You are a technical assistant." messages = [ {"role": "user", "content": "What is Docker?"}, {"role": "assistant", "content": "Docker is a platform for containerizing applications..."}, {"role": "user", "content": "How does it compare to virtual machines?"}, ] estimated = estimate_call_tokens(system, messages) print(f"Estimated input tokens: {estimated}") print(f"Estimated input cost (gpt-4o-mini): ${(estimated / 1_000_000) * 0.15:.6f}")

La estimación local es una aproximación — la API añade tokens especiales de formato que no podemos replicar exactamente. Pero es lo suficientemente precisa para estimaciones de coste y para verificar que no excedes la ventana de contexto antes de enviar la llamada.

## 5. Tokenización y coste: las matemáticas que importan

### 5.1. La asimetría input/output

En todos los proveedores, los tokens de salida son más caros que los de entrada. La ratio varía:

python
# Price asymmetry across providers (USD per 1M tokens, April 2026) pricing = { "gpt-4o-mini": {"input": 0.15, "output": 0.60, "ratio": 0.60/0.15}, "gpt-5.4-mini": {"input": 0.75, "output": 4.50, "ratio": 4.50/0.75}, "gpt-5.4": {"input": 2.50, "output": 15.00, "ratio": 15.00/2.50}, "claude-haiku-4-5": {"input": 1.00, "output": 5.00, "ratio": 5.00/1.00}, "claude-sonnet-4-6": {"input": 3.00, "output": 15.00, "ratio": 15.00/3.00}, "gemini-2.5-flash": {"input": 0.15, "output": 0.60, "ratio": 0.60/0.15}, } print(f"{'Model':25s} {'Input':>10s} {'Output':>10s} {'Ratio':>8s}") print("-" * 56) for model, p in pricing.items(): print(f"{model:25s} ${p['input']:>8.2f} ${p['output']:>8.2f} {p['ratio']:>7.1f}x")

**Implicación práctica:**Optimizar la longitud de las respuestas tiene más impacto en tu factura que optimizar la longitud del prompt. Un system prompt que dice"Maximum 200 words"o"Respond in exactly 3 sentences"no es solo una cuestión de UX — es una palanca de coste directa.

### 5.2. Proyección de coste a escala

python
# Production cost model # Scenario: SaaS product with an AI assistant feature USERS = 10_000 SESSIONS_PER_USER_DAY = 2 TURNS_PER_SESSION = 5 DAYS_PER_MONTH = 30 # Token consumption per turn (realistic estimates) SYSTEM_PROMPT_TOKENS = 300 # A production-grade prompt AVG_USER_MESSAGE = 50 # Typical user input AVG_HISTORY_GROWTH = 100 # Accumulated history per turn AVG_OUTPUT_TOKENS = 200 # Model response # Calculate average input tokens per turn (grows with conversation) avg_input_per_turn = SYSTEM_PROMPT_TOKENS + AVG_USER_MESSAGE + (AVG_HISTORY_GROWTH * 2.5) total_turns_month = USERS * SESSIONS_PER_USER_DAY * TURNS_PER_SESSION * DAYS_PER_MONTH total_input_tokens = total_turns_month * avg_input_per_turn total_output_tokens = total_turns_month * AVG_OUTPUT_TOKENS models = { "gpt-4o-mini": {"input": 0.15, "output": 0.60}, "claude-haiku-4-5": {"input": 1.00, "output": 5.00}, "gpt-5.4": {"input": 2.50, "output": 15.00}, } print(f"Scenario: {USERS:,} users × {SESSIONS_PER_USER_DAY} sessions/day × {TURNS_PER_SESSION} turns/session") print(f"Total turns/month: {total_turns_month:,}") print(f"Total input tokens/month: {total_input_tokens:,.0f}") print(f"Total output tokens/month: {total_output_tokens:,.0f}") print(f"\\n{'Model':25s} {'Input cost':>12s} {'Output cost':>12s} {'Total/month':>12s}") print("-" * 65) for model, prices in models.items(): input_cost = (total_input_tokens / 1_000_000) * prices["input"] output_cost = (total_output_tokens / 1_000_000) * prices["output"] total = input_cost + output_cost print(f"{model:25s} ${input_cost:>10.2f} ${output_cost:>10.2f} ${total:>10.2f}")

Esta proyección muestra por qué la elección de modelo es una decisión de negocio. La diferencia entregpt-4o-miniygpt-5.4para el mismo volumen puede ser de 10-30x en coste mensual. En muchos casos, la calidad de respuesta del modelo más barato es suficiente para la tarea — y el ahorro financia otras mejoras del producto.

### 5.3. Prompt caching: la optimización más impactante

Anthropic y OpenAI ofrecen prompt caching: si una porción del input (típicamente el system prompt y el contexto inyectado) se repite entre llamadas, los tokens repetidos se sirven desde caché con un descuento significativo.

python
# Prompt caching impact calculation SYSTEM_PROMPT_TOKENS = 300 TURNS_PER_MONTH = 3_000_000 # From the scenario above # Without caching: system prompt billed at full price every turn no_cache_input = SYSTEM_PROMPT_TOKENS * TURNS_PER_MONTH # With caching: first call at full price, subsequent calls at 90% discount (Anthropic) # Assuming 95% cache hit rate CACHE_HIT_RATE = 0.95 CACHE_DISCOUNT = 0.90 cache_miss_tokens = SYSTEM_PROMPT_TOKENS * TURNS_PER_MONTH * (1 - CACHE_HIT_RATE) cache_hit_tokens = SYSTEM_PROMPT_TOKENS * TURNS_PER_MONTH * CACHE_HIT_RATE # Cost comparison for claude-haiku-4-5 PRICE_PER_M = 1.00 # USD per 1M input tokens CACHED_PRICE_PER_M = PRICE_PER_M * (1 - CACHE_DISCOUNT) cost_no_cache = (no_cache_input / 1_000_000) * PRICE_PER_M cost_with_cache = ( (cache_miss_tokens / 1_000_000) * PRICE_PER_M + (cache_hit_tokens / 1_000_000) * CACHED_PRICE_PER_M ) savings = cost_no_cache - cost_with_cache savings_pct = (savings / cost_no_cache) * 100 print(f"System prompt tokens per month: {no_cache_input:,.0f}") print(f"\\nWithout caching: ${cost_no_cache:.2f}") print(f"With caching: ${cost_with_cache:.2f}") print(f"Monthly savings: ${savings:.2f} ({savings_pct:.0f}%)")

Profundizaremos en prompt caching en la Sesión 03 cuando construyamos la capa de abstracción de proveedores.

## 6. Limitaciones fundamentales de la tokenización

### 6.1. El modelo no ve letras

Cuando pides a un LLM que cuente las letras de una palabra o que la deletree al revés, estás pidiéndole algo que contradice su representación interna. La palabra"Strawberry"puede ser un único token (ID 92850). El modelo ve el token 92850, no las letras S-t-r-a-w-b-e-r-r-y. Para él, es una unidad semántica opaca que ha aprendido a asociar con el concepto de una fruta roja, pero no tiene acceso a su composición interna de caracteres.

python
import tiktoken enc = tiktoken.encoding_for_model("gpt-4o-mini") words = ["hello", "Strawberry", "tokenization", "microservices", "PostgreSQL"] for word in words: tokens = enc.encode(word) parts = [f"'{enc.decode([t])}'" for t in tokens] single = "single token" if len(tokens) == 1 else f"{len(tokens)} tokens" print(f" {word:20s} → {single:15s} → {parts}")
### 6.2. La tokenización no es uniforme entre proveedores

Cada proveedor entrena su propio tokenizador con su propio corpus y su propio tamaño de vocabulario. El mismo texto produce secuencias de tokens diferentes — y longitudes diferentes — según el proveedor:

python
import tiktoken # OpenAI tokenizer enc_openai = tiktoken.encoding_for_model("gpt-4o-mini") text = "Analyzing the performance impact of database connection pooling in a microservices architecture" openai_tokens = enc_openai.encode(text) print(f"OpenAI (o200k_base): {len(openai_tokens)} tokens") # Anthropic and Google use different tokenizers that we can't access via tiktoken # but the principle is the same: different vocabulary = different token counts # In practice, Anthropic typically produces 5-15% more tokens than OpenAI for English text print(f"Anthropic (estimate): ~{int(len(openai_tokens) * 1.10)} tokens") print(f"Gemini (estimate): ~{int(len(openai_tokens) * 0.95)} tokens")

**Implicación práctica:**No puedes usartiktokenpara estimar exactamente los tokens que consumirá una llamada a Anthropic o a Gemini. Para Anthropic, la estimación será aproximada (típicamente un 5-15% más que OpenAI para texto en inglés). Para Gemini, puedes usar su endpoint gratuitocount_tokens().

### 6.3. Tokens "glitch"

En 2023, investigadores descubrieron que ciertos tokens producían comportamientos erráticos en GPT-3.5 y GPT-4. El caso más famoso fue el token"SolidGoldMagikarp"— un username de Reddit que aparecía con suficiente frecuencia en el corpus del tokenizador como para obtener su propio token, pero que era tan raro en el corpus de entrenamiento del modelo que su embedding quedó esencialmente aleatorio.

La causa raíz:**los datos de entrenamiento del tokenizador y los datos de entrenamiento del modelo no son los mismos**. Un token puede existir en el vocabulario pero no haber sido visto lo suficiente durante el entrenamiento del modelo como para tener un embedding significativo. Los tokenizadores modernos (comoo200k_basede GPT-4o) han eliminado la mayoría de estos tokens glitch, pero el problema fundamental persiste como una limitación arquitectural.

## 7. Herramientas prácticas para trabajar con tokens

### 7.1. tiktoken: el tokenizador de OpenAI

python
import tiktoken # Load tokenizer for a specific model enc = tiktoken.encoding_for_model("gpt-4o-mini") # Or load by encoding name directly enc = tiktoken.get_encoding("o200k_base") # Encode: text → token IDs tokens = enc.encode("Hello, world!") print(f"Token IDs: {tokens}") # Decode: token IDs → text text = enc.decode(tokens) print(f"Decoded: {text}") # Decode individual tokens to see the breakdown for t in tokens: print(f" {t} → '{enc.decode([t])}'") # Count tokens in a text (most common use case) text = "Your system prompt or user message here" token_count = len(enc.encode(text)) print(f"Token count: {token_count}")
### 7.2. Gemini count_tokens: conteo gratuito antes de la llamada

python
from google import genai client = genai.Client() # Count tokens before making the API call (free, no charge) result = client.models.count_tokens( model="gemini-2.5-flash", contents="Your text here..." ) print(f"Token count: {result.total_tokens}")
### 7.3. Función auxiliar para estimación de costes

python
import tiktoken def estimate_cost( system_prompt, user_message, expected_output_tokens=200, model="gpt-4o-mini" ): """ Estimate the cost of an API call before making it. Uses tiktoken for input estimation and a manual estimate for output. """ pricing = { "gpt-4o-mini": {"input": 0.15, "output": 0.60}, "gpt-5.4-mini": {"input": 0.75, "output": 4.50}, "claude-haiku-4-5": {"input": 1.00, "output": 5.00}, "gemini-2.5-flash": {"input": 0.15, "output": 0.60}, } enc = tiktoken.encoding_for_model("gpt-4o-mini") # Approximation for all models input_tokens = len(enc.encode(system_prompt)) + len(enc.encode(user_message)) + 8 prices = pricing.get(model, {"input": 1.0, "output": 5.0}) input_cost = (input_tokens / 1_000_000) * prices["input"] output_cost = (expected_output_tokens / 1_000_000) * prices["output"] return { "input_tokens": input_tokens, "output_tokens": expected_output_tokens, "input_cost": input_cost, "output_cost": output_cost, "total_cost": input_cost + output_cost, } # Example usage estimate = estimate_cost( system_prompt="You are a principal architect specializing in distributed systems...", user_message="How should we approach migrating our payment service?", expected_output_tokens=300, model="gpt-4o-mini" ) print(f"Estimated input: {estimate['input_tokens']} tokens (${estimate['input_cost']:.6f})") print(f"Estimated output: {estimate['output_tokens']} tokens (${estimate['output_cost']:.6f})") print(f"Estimated total: ${estimate['total_cost']:.6f}")
## Resumen: lo que un AI Engineer necesita saber sobre tokens

1. 

**Los tokens no son palabras.**Son fragmentos de texto de longitud variable producidos por BPE. Una palabra puede ser 1 token o 5, dependiendo de su frecuencia en el corpus del tokenizador.

1. 

**El idioma importa.**El español consume un 20-40% más de tokens que el inglés para el mismo contenido semántico. Esto afecta directamente a tu factura.

1. 

**Los tokens de salida son 3-6x más caros que los de entrada.**Controlar la longitud de las respuestas (conmax_output_tokensy con instrucciones explícitas de brevedad) tiene más impacto en coste que optimizar el prompt.

1. 

**Cada turno de conversación reenvía todo el historial.**El coste de una conversación crece cuadráticamente, no linealmente. Gestionar el contexto no es una optimización — es un requisito de viabilidad económica.

1. 

**Los tokenizadores varían entre proveedores.**No puedes usar tiktoken para calcular exactamente los tokens de Anthropic o Gemini. Usa tiktoken como aproximación y los metadatos de la respuesta para el cálculo real.

1. 

**El formato de tus datos consume tokens.**JSON con pretty-print, indentación innecesaria, y saltos de línea extras consumen tokens sin aportar valor al modelo.

1. 

**Los modelos no ven letras ni dígitos individuales.**No delegues aritmética ni manipulación de strings a un LLM — hazlo en tu código.

## Referencias

- 

Andrej Karpathy,*Let's Build the GPT Tokenizer*(video + minBPE):[github.com/karpathy/minbpe](https://github.com/karpathy/minbpe)

- 

tiktoken (OpenAI):[github.com/openai/tiktoken](https://github.com/openai/tiktoken)

- 

Sebastian Raschka,*Implementing BPE from Scratch*:[sebastianraschka.com/blog/2025/bpe-from-scratch.html](https://sebastianraschka.com/blog/2025/bpe-from-scratch.html)

- 

Hugging Face,*Tokenization Algorithms*:[huggingface.co/docs/transformers/tokenizer_summary](https://huggingface.co/docs/transformers/tokenizer_summary)

- 

Sennrich et al. 2015,*Neural Machine Translation of Rare Words with Subword Units*(paper original de BPE para NLP)

- 

Tiktokenizer (visualizador web interactivo):[tiktokenizer.vercel.app](http://tiktokenizer.vercel.app)
