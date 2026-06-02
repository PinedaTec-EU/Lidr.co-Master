from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ScenarioTurn:
    turn_index: int
    transcript: str
    fact_to_remember: str


@dataclass(frozen=True)
class ScenarioDefinition:
    name: str
    description: str
    turns: list[ScenarioTurn]

    def slice(self, turn_count: int) -> "ScenarioDefinition":
        return ScenarioDefinition(
            name=self.name,
            description=self.description,
            turns=self.turns[:turn_count],
        )


def _growing_turns() -> list[ScenarioTurn]:
    facts = [
        "Nimbus",
        "SSO",
        "multi-tenant",
        "audit log",
        "CSV export",
        "role permissions",
        "billing dashboard",
        "email alerts",
        "SLA 99.9",
        "launch in Q4",
        "data residency EU",
        "mobile responsive",
        "SAML",
        "usage analytics",
        "webhooks",
        "bulk import",
        "approval workflow",
        "partner portal",
        "disaster recovery",
        "24x7 support",
    ]
    transcripts = [
        "Proyecto Nimbus para operaciones B2B. Necesitamos un portal base con dashboard y gestión interna.",
        "Añadimos SSO corporativo como requisito obligatorio para Nimbus.",
        "El portal Nimbus ahora debe ser multi-tenant para varios clientes.",
        "También hace falta audit log completo para acciones críticas.",
        "El cliente pide exporte CSV de usuarios y facturas.",
        "Se añade un modelo de role permissions más granular.",
        "Piden billing dashboard con consumo y renovación.",
        "Necesitamos email alerts configurables para incidencias y cobros.",
        "El SLA objetivo del proyecto Nimbus será 99.9 por ciento.",
        "La fecha objetivo cambia: lanzamiento comercial en Q4.",
        "Añadir requisito de data residency EU para clientes regulados.",
        "La interfaz debe ser mobile responsive en tablet y móvil.",
        "Se incorpora federación SAML además de SSO básico.",
        "Necesitan usage analytics para admins de cuenta.",
        "Añadir webhooks para integraciones externas.",
        "Quieren bulk import desde hojas CSV grandes.",
        "Se suma approval workflow para altas y cambios críticos.",
        "Habrá partner portal para distribuidores.",
        "Necesitan disaster recovery documentado y probado.",
        "El soporte esperado pasa a 24x7 con guardias.",
    ]
    return [
        ScenarioTurn(turn_index=index + 1, transcript=transcripts[index], fact_to_remember=facts[index])
        for index in range(len(facts))
    ]


def _pivot_turns() -> list[ScenarioTurn]:
    facts = [
        "Orion",
        "React",
        "PostgreSQL",
        "Node.js",
        "Flutter",
        "mobile app",
        "offline mode",
        "push notifications",
        "camera uploads",
        "tablet-first",
        "field teams",
        "route planning",
        "signature capture",
        "geo-fencing",
        "device sync",
        "warehouse mode",
        "barcode scan",
        "battery saving",
        "release in pilot",
        "Play Store",
    ]
    transcripts = [
        "Proyecto Orion para equipos de campo con un panel web inicial.",
        "La primera decisión técnica: frontend React para Orion.",
        "Persistencia principal en PostgreSQL.",
        "Backend API en Node.js.",
        "Pivot importante: ya no será panel web, será una app Flutter.",
        "El producto final debe priorizar experiencia mobile app.",
        "Necesitamos offline mode para trabajo sin cobertura.",
        "Añadir push notifications para avisos críticos.",
        "La app debe soportar camera uploads de incidencias.",
        "Diseño tablet-first para supervisores de ruta.",
        "Se confirma uso por field teams de mantenimiento.",
        "Se añade route planning en los recorridos.",
        "Necesitamos signature capture en cierres de visita.",
        "Añadir geo-fencing para validación de presencia.",
        "Habrá device sync al recuperar conectividad.",
        "También existirá warehouse mode para almacén.",
        "Se incorpora barcode scan para inventario.",
        "Optimizar battery saving en dispositivos de campo.",
        "Primero saldrá como release in pilot con un cliente.",
        "Distribución final prevista en Play Store empresarial.",
    ]
    return [
        ScenarioTurn(turn_index=index + 1, transcript=transcripts[index], fact_to_remember=facts[index])
        for index in range(len(facts))
    ]


def _contradiction_turns() -> list[ScenarioTurn]:
    facts = [
        "Atlas",
        "budget 30000 EUR",
        "deadline 8 weeks",
        "team 3",
        "budget 80000 EUR",
        "deadline 16 weeks",
        "team 5",
        "priority compliance",
        "scope fixed",
        "scope expanding",
        "budget approved",
        "budget frozen",
        "urgent migration",
        "legacy SOAP",
        "replace CRM",
        "keep CRM",
        "on-premise",
        "cloud first",
        "board visibility",
        "phase 1 only",
    ]
    transcripts = [
        "Proyecto Atlas para modernizar un sistema interno de ventas.",
        "El presupuesto confirmado por ahora es budget 30000 EUR.",
        "Se esperaba una entrega en deadline 8 weeks.",
        "La capacidad inicial del proveedor es team 3.",
        "Nueva reunión: el sponsor eleva el marco a budget 80000 EUR.",
        "También acepta mover la entrega a deadline 16 weeks.",
        "Se amplía el equipo previsto a team 5.",
        "La prioridad principal pasa a ser compliance.",
        "Por ahora se habla de scope fixed para cerrar pronto.",
        "Contradicción posterior: el negocio pide scope expanding con nuevas áreas.",
        "Finanzas comenta que el budget approved ya está en comité.",
        "Después legal pide budget frozen hasta nueva revisión.",
        "La migración se cataloga como urgent migration.",
        "El sistema legado sigue siendo legacy SOAP.",
        "En un momento se planteó replace CRM por completo.",
        "Más tarde dirección cambia a keep CRM y solo integrar.",
        "Infraestructura heredada sigue on-premise.",
        "Arquitectura propone de nuevo cloud first para el futuro.",
        "El proyecto requiere board visibility semanal.",
        "La primera fase se limita a phase 1 only.",
    ]
    return [
        ScenarioTurn(turn_index=index + 1, transcript=transcripts[index], fact_to_remember=facts[index])
        for index in range(len(facts))
    ]


SCENARIOS: dict[str, ScenarioDefinition] = {
    "growing": ScenarioDefinition(
        name="growing",
        description="Proyecto con alcance creciente y acumulativo.",
        turns=_growing_turns(),
    ),
    "pivot": ScenarioDefinition(
        name="pivot",
        description="Proyecto que pivota de stack y de forma de producto.",
        turns=_pivot_turns(),
    ),
    "contradiction": ScenarioDefinition(
        name="contradiction",
        description="Proyecto con información contradictoria entre turnos.",
        turns=_contradiction_turns(),
    ),
}


def get_scenarios(names: list[str] | None = None) -> list[ScenarioDefinition]:
    selected_names = names or list(SCENARIOS.keys())
    return [SCENARIOS[name] for name in selected_names]
