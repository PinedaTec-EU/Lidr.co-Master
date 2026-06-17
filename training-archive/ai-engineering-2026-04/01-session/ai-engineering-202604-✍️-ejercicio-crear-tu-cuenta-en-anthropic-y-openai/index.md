---
title: "✍️ Ejercicio - Crear tu cuenta en Anthropic y OpenAI"
source_url: "https://training.lidr.co/posts/ai-engineering-202604-✍️-ejercicio-crear-tu-cuenta-en-anthropic-y-openai"
archived_at: "2026-06-12T09:20:59.817Z"
group: "01-session"
---

# ✍️ Ejercicio - Crear tu cuenta en Anthropic y OpenAI

![Antonio Perez](./assets/c3eccac37426c36f.jpg)

[Antonio Perez](https://training.lidr.co/members/36030888)

## Alta en las APIs de OpenAI y Anthropic

⚠****Completa este ejercicio antes de abordar el ejercicio de código (parte 2).

## Objetivo

Crear una cuenta de desarrollador en OpenAI y/o en Anthropic, configurar la facturación en al menos uno de los dos proveedores, y generar una API key funcional que utilizarás durante todo el programa.

## Entregable

No hay entrega formal. Al finalizar este ejercicio debes tener:

- 

Cuenta activa en**OpenAI Platform**con una API key generada

- 

Cuenta activa en**Anthropic Console**con una API key generada

- 

Facturación configurada y crédito disponible en**al menos uno**de los dos proveedores (el que elijas como principal para el ejercicio de código)

## Parte🅰— OpenAI

### 1. Crear la cuenta

1. 

Ve a[platform.openai.com](http://platform.openai.com)— esta es la plataforma de API, separada de[chatgpt.com](http://chatgpt.com)

1. 

Haz clic en**Sign up**

1. 

Regístrate con tu email, o usa tu cuenta de Google o Microsoft

1. 

Verifica tu email y completa la verificación por SMS con tu número de teléfono

Si ya tienes una cuenta de ChatGPT, puedes usar las mismas credenciales para acceder a la plataforma de API. Sin embargo, la facturación de la API es independiente de tu suscripción a ChatGPT.

### 2. Configurar la facturación

1. 

Una vez dentro del dashboard, ve a**Settings → Billing**o accede directamente a[platform.openai.com/settings/organization/billing](https://platform.openai.com/settings/organization/billing/overview)

1. 

Haz clic en**Add credit**e introduce los datos de tu tarjeta de crédito o débito

1. 

Añade un mínimo de**5 USD**de crédito (suficiente para semanas de uso en el programa)

1. 

**Recomendado:**Configura un límite de gasto mensual para evitar sorpresas. La sección de Usage Limits te permite definir un tope

OpenAI funciona con un sistema de crédito prepago. Sin saldo, las llamadas a la API devuelven error.

### 3. Generar la API key

1. 

Ve a**API Keys**en el menú lateral, o accede directamente a[platform.openai.com/api-keys](https://platform.openai.com/api-keys)

1. 

Haz clic en**Create new secret key**

1. 

Dale un nombre descriptivo (por ejemplo,master-ai-engineering)

1. 

Copia la key inmediatamente y guárdala en un lugar seguro

**La key solo se muestra una vez.**Si cierras el diálogo sin copiarla, no podrás recuperarla y tendrás que generar una nueva. Usa un gestor de contraseñas o un archivo seguro.

### Verificación

Confirma que tu setup es correcto revisando estos puntos:

- 

[ ] Tienes acceso al dashboard en[platform.openai.com](http://platform.openai.com)

- 

[ ] Tu saldo en Billing es superior a 0 USD

- 

[ ] Tienes una API key copiada y guardada (empieza porsk-)

## Parte🅱— Anthropic

### 1. Crear la cuenta

1. 

Ve a[console.anthropic.com](http://console.anthropic.com)

1. 

Haz clic en**Sign up**o**Continue with Google**

1. 

Completa el registro con tu email y verifica tu cuenta

1. 

Es posible que Anthropic te pida verificación por SMS con tu número de teléfono

Las cuentas nuevas pueden recibir una pequeña cantidad de créditos gratuitos para pruebas iniciales. Si los tienes disponibles, te pedirá verificar tu número de teléfono para reclamarlos.

### 2. Configurar la facturación

1. 

En el menú lateral del console, ve a**Settings → Billing**o accede directamente a[console.anthropic.com/settings/billing](https://console.anthropic.com/settings/billing)

1. 

Selecciona el plan**Build**(pay-as-you-go) — es el adecuado para uso individual

1. 

Introduce los datos de tu tarjeta y compra un mínimo de**5 USD**en créditos

1. 

**Recomendado:**Configura un límite de gasto mensual en la misma sección de Billing

Anthropic funciona con un sistema de crédito prepago similar al de OpenAI. Sin crédito, las llamadas devuelven error.

### 3. Generar la API key

1. 

En el menú lateral, haz clic en el icono de llave o navega a**API Keys**, o accede directamente a[console.anthropic.com/settings/keys](https://console.anthropic.com/settings/keys)

1. 

Haz clic en**Create Key**

1. 

Dale un nombre descriptivo (por ejemplo,master-ai-engineering)

1. 

Copia la key inmediatamente y guárdala en un lugar seguro

Igual que con OpenAI,**la key solo se muestra una vez.**Las keys de Anthropic empiezan porsk-ant-.

### Verificación

Confirma que tu setup es correcto revisando estos puntos:

- 

[ ] Tienes acceso al dashboard en[console.anthropic.com](http://console.anthropic.com)

- 

[ ] Tienes crédito disponible (gratuito o comprado)

- 

[ ] Tienes una API key copiada y guardada (empieza porsk-ant-)

### ⚠Seguridad de las API keys

Trata tus API keys como contraseñas. Cualquier persona con acceso a tu key puede hacer llamadas que se cargarán a tu cuenta. Tres reglas básicas:

1. 

**Nunca las escribas directamente en tu código.**Usa variables de entorno o el gestor de Secrets de Google Colab (ver la guía de Colab del programa).

1. 

**Nunca las subas a un repositorio.**Ni público ni privado. Añade.enva tu.gitignore.

1. 

**Si sospechas que una key ha sido expuesta**, revócala inmediatamente desde el dashboard del proveedor y genera una nueva.
