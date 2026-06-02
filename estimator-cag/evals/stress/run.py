from __future__ import annotations

import argparse
import asyncio
import csv
from dataclasses import dataclass
from pathlib import Path
from statistics import mean
import time
from typing import Any

import httpx

from evals.stress.fixtures.build_pdfs import TEXT_FACT, build_all
from evals.stress.metrics import CostBudgetMetric, LatencyBudgetMetric, MemoryDriftMetric
from evals.stress.scenarios import get_scenarios


DEFAULT_OUTPUT = Path("evals/stress/results.csv")
DEFAULT_REPORT = Path("evals/stress/REPORT.md")


@dataclass(frozen=True)
class RunnerConfig:
    base_url: str | None
    scenarios: list[str]
    attachment_sizes: list[int]
    turn_counts: list[int]
    repeats: int
    output_path: Path
    report_path: Path
    provider: str
    model: str | None
    friendly_name: str | None
    latency_budget_ms: int
    cost_budget_usd: float


def _parse_csv_int_list(raw: str) -> list[int]:
    return [int(part.strip()) for part in raw.split(",") if part.strip()]


def parse_args() -> RunnerConfig:
    parser = argparse.ArgumentParser()
    parser.add_argument("--http", dest="base_url", default=None)
    parser.add_argument("--scenarios", default="growing,pivot,contradiction")
    parser.add_argument("--attachment-sizes", default="0,5,20,50,100")
    parser.add_argument("--turn-counts", default="1,3,6,10,20")
    parser.add_argument("--repeats", type=int, default=3)
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT))
    parser.add_argument("--report", default=str(DEFAULT_REPORT))
    parser.add_argument("--provider", default="openai")
    parser.add_argument("--model", default="gpt-4o-mini")
    parser.add_argument("--friendly-name", dest="friendly_name", default="openai")
    parser.add_argument("--latency-budget-ms", type=int, default=4000)
    parser.add_argument("--cost-budget-usd", type=float, default=0.01)
    args = parser.parse_args()
    return RunnerConfig(
        base_url=args.base_url,
        scenarios=[item.strip() for item in args.scenarios.split(",") if item.strip()],
        attachment_sizes=_parse_csv_int_list(args.attachment_sizes),
        turn_counts=_parse_csv_int_list(args.turn_counts),
        repeats=args.repeats,
        output_path=Path(args.output),
        report_path=Path(args.report),
        provider=args.provider,
        model=args.model or None,
        friendly_name=args.friendly_name or None,
        latency_budget_ms=args.latency_budget_ms,
        cost_budget_usd=args.cost_budget_usd,
    )


class SessionClient:
    def __init__(self, config: RunnerConfig) -> None:
        self.config = config
        self._client: httpx.AsyncClient | None = None

    async def __aenter__(self) -> "SessionClient":
        if self.config.base_url:
            self._client = httpx.AsyncClient(base_url=self.config.base_url.rstrip("/"), timeout=180.0)
        else:
            from httpx import ASGITransport
            from app.main import app

            self._client = httpx.AsyncClient(
                transport=ASGITransport(app=app),
                base_url="http://testserver",
                timeout=180.0,
            )
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        if self._client is not None:
            await self._client.aclose()

    async def create_session(self) -> str:
        response = await self._client.post("/api/v1/sessions")
        response.raise_for_status()
        return response.json()["session_id"]

    async def estimate_turn(
        self,
        session_id: str,
        *,
        transcript: str,
        attachment_path: Path | None = None,
    ) -> dict[str, Any]:
        params: dict[str, str] = {"provider": self.config.provider}
        if self.config.friendly_name:
            params["friendly_name"] = self.config.friendly_name
        if self.config.model:
            params["model"] = self.config.model

        data = {
            "transcript": transcript,
            "project_type": "web_saas",
            "detail_level": "summary",
            "output_format": "line_items",
        }
        files = None
        if attachment_path is not None:
            files = {"attachments": (attachment_path.name, attachment_path.read_bytes(), "application/pdf")}

        response = await self._client.post(
            f"/api/v1/sessions/{session_id}/estimate",
            params=params,
            data=data,
            files=files,
        )
        response.raise_for_status()
        return await self.get_session_detail(session_id)

    async def get_session_detail(self, session_id: str) -> dict[str, Any]:
        response = await self._client.get(f"/api/v1/sessions/{session_id}")
        response.raise_for_status()
        return response.json()


def _row_base(
    *,
    scenario_name: str,
    repeat_index: int,
    turn_limit: int,
    attachment_size_kb: int,
    expected_fact: str,
    iteration_kind: str,
) -> dict[str, Any]:
    return {
        "scenario_name": scenario_name,
        "repeat_index": repeat_index,
        "turn_limit": turn_limit,
        "attachment_size_kb": attachment_size_kb,
        "expected_fact": expected_fact,
        "iteration_kind": iteration_kind,
    }


def _serialize_row(
    base: dict[str, Any],
    observation: dict[str, Any],
    metrics: dict[str, float],
) -> dict[str, Any]:
    row = dict(base)
    row.update(
        {
            "turn_index": observation.get("turn_index", 0),
            "session_id": observation.get("session_id", ""),
            "enriched_transcript_chars": observation.get("enriched_transcript_chars", 0),
            "attachments_total_chars": observation.get("attachments_total_chars", 0),
            "messages_in_window": observation.get("messages_in_window", 0),
            "anchors_count": observation.get("anchors_count", 0),
            "summary_chars": observation.get("summary_chars", 0),
            "tokens_in": observation.get("tokens_in", 0),
            "tokens_out": observation.get("tokens_out", 0),
            "cost_usd": observation.get("cost_usd", 0.0),
            "latency_ms": observation.get("latency_ms", 0.0),
            "cache_hit_kind": observation.get("cache_hit_kind", "none"),
            "last_resolved_tier": observation.get("last_resolved_tier", ""),
            "provider": observation.get("provider", ""),
            "model": observation.get("model", ""),
        }
    )
    row.update(metrics)
    return row


def _attach_iteration_audit(rows: list[dict[str, Any]], elapsed_ms: float) -> None:
    audit = {
        "iteration_total_turns": len(rows),
        "iteration_total_tokens_in": sum(int(item.get("tokens_in", 0)) for item in rows),
        "iteration_total_tokens_out": sum(int(item.get("tokens_out", 0)) for item in rows),
        "iteration_total_cost_usd": round(sum(float(item.get("cost_usd", 0.0)) for item in rows), 8),
        "iteration_total_latency_ms": round(sum(float(item.get("latency_ms", 0.0)) for item in rows), 2),
        "iteration_wall_clock_ms": round(elapsed_ms, 2),
    }
    for row in rows:
        row.update(audit)


async def _run_multi_turn_scenarios(config: RunnerConfig, client: SessionClient) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    latency_metric = LatencyBudgetMetric(config.latency_budget_ms)
    cost_metric = CostBudgetMetric(config.cost_budget_usd)

    for scenario in get_scenarios(config.scenarios):
        for turn_limit in config.turn_counts:
            scoped = scenario.slice(turn_limit)
            for repeat_index in range(1, config.repeats + 1):
                session_id = await client.create_session()
                iteration_started_at = time.perf_counter()
                iteration_rows: list[dict[str, Any]] = []
                for turn in scoped.turns:
                    detail = await client.estimate_turn(session_id, transcript=turn.transcript)
                    observation = detail["last_turn_observed"]
                    memory_metric = MemoryDriftMetric(turn.fact_to_remember)
                    metrics = {
                        "latency_budget_score": latency_metric.evaluate(observation).score,
                        "cost_budget_score": cost_metric.evaluate(observation).score,
                        "memory_drift_score": memory_metric.evaluate(observation).score,
                    }
                    iteration_rows.append(
                        _serialize_row(
                            _row_base(
                                scenario_name=scenario.name,
                                repeat_index=repeat_index,
                                turn_limit=turn_limit,
                                attachment_size_kb=0,
                                expected_fact=turn.fact_to_remember,
                                iteration_kind="multi_turn",
                            ),
                            observation,
                            metrics,
                        )
                    )
                _attach_iteration_audit(
                    iteration_rows,
                    elapsed_ms=(time.perf_counter() - iteration_started_at) * 1000,
                )
                rows.extend(iteration_rows)
    return rows


async def _run_attachment_scenario(config: RunnerConfig, client: SessionClient) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    latency_metric = LatencyBudgetMetric(config.latency_budget_ms)
    cost_metric = CostBudgetMetric(config.cost_budget_usd)
    memory_metric = MemoryDriftMetric(TEXT_FACT, where=["assistant_text"])
    generated = {path.stem.split("_")[1].replace("kb", ""): path for path in build_all(config.attachment_sizes)}

    for attachment_size in config.attachment_sizes:
        attachment_path = generated.get(str(attachment_size))
        for repeat_index in range(1, config.repeats + 1):
            session_id = await client.create_session()
            iteration_started_at = time.perf_counter()
            transcript = (
                "Necesitamos una estimación inicial para el proyecto Helios con alcance comercial y operativo. "
                "Resume también el contenido del documento adjunto si existe."
            )
            detail = await client.estimate_turn(session_id, transcript=transcript, attachment_path=attachment_path)
            observation = detail["last_turn_observed"]
            metrics = {
                "latency_budget_score": latency_metric.evaluate(observation).score,
                "cost_budget_score": cost_metric.evaluate(observation).score,
                "memory_drift_score": memory_metric.evaluate(observation).score,
            }
            iteration_rows = [
                _serialize_row(
                    _row_base(
                        scenario_name="attachment_stress",
                        repeat_index=repeat_index,
                        turn_limit=1,
                        attachment_size_kb=attachment_size,
                        expected_fact=TEXT_FACT,
                        iteration_kind="attachment",
                    ),
                    observation,
                    metrics,
                )
            ]
            _attach_iteration_audit(
                iteration_rows,
                elapsed_ms=(time.perf_counter() - iteration_started_at) * 1000,
            )
            rows.extend(iteration_rows)
    return rows


def _write_csv(rows: list[dict[str, Any]], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = list(rows[0].keys())
    with output_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _percentile(values: list[float], percentile: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    index = max(0, min(len(ordered) - 1, round((percentile / 100) * (len(ordered) - 1))))
    return float(ordered[index])


def _group_rows(rows: list[dict[str, Any]]) -> dict[tuple[str, int], list[dict[str, Any]]]:
    grouped: dict[tuple[str, int], list[dict[str, Any]]] = {}
    for row in rows:
        key = (str(row["scenario_name"]), int(row["attachment_size_kb"]))
        grouped.setdefault(key, []).append(row)
    return grouped


def _render_summary_table(rows: list[dict[str, Any]]) -> str:
    lines = [
        "| scenario | attachment_kb | p50_latency_ms | p95_latency_ms | total_cost_usd | total_tokens_in | total_tokens_out | wall_clock_ms | exact_hit_rate | semantic_hit_rate | mean_recall |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for (scenario_name, attachment_size), group in sorted(_group_rows(rows).items()):
        latencies = [float(item["latency_ms"]) for item in group]
        total_cost = sum(float(item["cost_usd"]) for item in group)
        total_tokens_in = sum(int(item["tokens_in"]) for item in group)
        total_tokens_out = sum(int(item["tokens_out"]) for item in group)
        total_wall_clock = sum(
            float(item["iteration_wall_clock_ms"])
            for item in group
            if int(item["turn_index"]) == int(item["iteration_total_turns"])
        )
        exact_hit_rate = mean(1.0 if item["cache_hit_kind"] == "exact" else 0.0 for item in group)
        semantic_hit_rate = mean(1.0 if item["cache_hit_kind"] == "semantic" else 0.0 for item in group)
        mean_recall = mean(float(item["memory_drift_score"]) for item in group)
        lines.append(
            f"| {scenario_name} | {attachment_size} | {_percentile(latencies, 50):.2f} | {_percentile(latencies, 95):.2f} | {total_cost:.6f} | {total_tokens_in} | {total_tokens_out} | {total_wall_clock:.2f} | {exact_hit_rate:.2f} | {semantic_hit_rate:.2f} | {mean_recall:.2f} |"
        )
    return "\n".join(lines)


def _render_curve_table(rows: list[dict[str, Any]], x_key: str, y_key: str, title: str) -> str:
    lines = [f"### {title}", "", f"| {x_key} | {y_key} |", "|---:|---:|"]
    for row in rows:
        lines.append(f"| {row[x_key]} | {row[y_key]} |")
    return "\n".join(lines)


def _render_cost_curve(rows: list[dict[str, Any]]) -> str:
    lines = ["### Coste acumulado vs turno", "", "| scenario | turn_index | cumulative_cost_usd |", "|---|---:|---:|"]
    by_scenario: dict[str, float] = {}
    ordered = sorted(rows, key=lambda item: (item["scenario_name"], int(item["repeat_index"]), int(item["turn_limit"]), int(item["turn_index"])))
    for row in ordered:
        scenario_name = str(row["scenario_name"])
        by_scenario[scenario_name] = by_scenario.get(scenario_name, 0.0) + float(row["cost_usd"])
        lines.append(f"| {scenario_name} | {row['turn_index']} | {by_scenario[scenario_name]:.6f} |")
    return "\n".join(lines)


def _render_report(rows: list[dict[str, Any]], report_path: Path) -> None:
    report_path.parent.mkdir(parents=True, exist_ok=True)
    ordered_by_tokens = sorted(rows, key=lambda item: float(item["tokens_in"]))
    ordered_by_turn = sorted(rows, key=lambda item: (str(item["scenario_name"]), int(item["turn_limit"]), int(item["turn_index"])))
    ordered_by_memory = sorted(rows, key=lambda item: (int(item["turn_limit"]), int(item["turn_index"])))

    recall_values = [float(item["memory_drift_score"]) for item in rows]
    mean_recall = mean(recall_values) if recall_values else 0.0
    p95_latency = _percentile([float(item["latency_ms"]) for item in rows], 95)
    max_turn = max(int(item["turn_index"]) for item in rows)
    total_cost = sum(float(item["cost_usd"]) for item in rows)
    total_tokens_in = sum(int(item["tokens_in"]) for item in rows)
    total_tokens_out = sum(int(item["tokens_out"]) for item in rows)
    total_wall_clock = sum(
        float(item["iteration_wall_clock_ms"])
        for item in rows
        if int(item["turn_index"]) == int(item["iteration_total_turns"])
    )

    report = "\n".join(
        [
            "# Stress Test Report",
            "",
            "## Auditoría de la corrida",
            "",
            f"- Filas de datos: {len(rows)}",
            f"- Tokens de entrada totales: {total_tokens_in}",
            f"- Tokens de salida totales: {total_tokens_out}",
            f"- Coste total USD: {total_cost:.6f}",
            f"- Tiempo total observado de iteraciones: {total_wall_clock:.2f} ms",
            "- Intervalos multi-turno ejecutados: 1, 3, 6, 10, 20",
            "",
            "## Resumen",
            "",
            _render_summary_table(rows),
            "",
            "## Curvas",
            "",
            _render_curve_table(ordered_by_tokens[:40], "tokens_in", "latency_ms", "Latencia vs tokens"),
            "",
            _render_cost_curve(ordered_by_turn[:80]),
            "",
            _render_curve_table(ordered_by_memory[:80], "turn_index", "memory_drift_score", "Recall vs N"),
            "",
            "## Lectura",
            "",
            (
                f"El CAG de esta base empieza a mostrar su límite cuando el historial crece y la observabilidad revela "
                f"que el `messages_in_window` queda topado mientras el volumen de tokens y la latencia siguen creciendo. "
                f"En esta corrida el P95 de latencia llegó a {p95_latency:.2f} ms, el recall medio del fact-tracker quedó en {mean_recall:.2f} y el coste total fue {total_cost:.6f} USD."
            ),
            "",
            (
                f"La dimensión dominante en esta muestra es la memoria contextual: el sistema mantiene coste y contrato HTTP, "
                f"pero la pérdida de hechos exactos se hace visible conforme aumenta `turn_index` hasta {max_turn}. "
                "Eso justifica el salto a RAG cuando el proyecto requiere recordar hechos antiguos sin volver a inyectarlos completos en cada turno."
            ),
            "",
            "## Notas de adaptación",
            "",
            "- Este repo no implementa `anchors` ni `summary` persistidos como en el material de clase; se reportan explícitamente como `0` o vacío para que la limitación quede visible.",
            "- El runner usa el snapshot enriquecido de `GET /api/v1/sessions/{id}` en lugar de parsear logs, porque esta base ya persiste estado por sesión y eso hace determinista la extracción del CSV.",
            "- Para PDFs sintéticos se usa generación determinista local y conversión vía Docling Serve.",
        ]
    )
    report_path.write_text(report + "\n", encoding="utf-8")


async def main() -> None:
    config = parse_args()
    run_started_at = time.perf_counter()
    async with SessionClient(config) as client:
        rows: list[dict[str, Any]] = []
        rows.extend(await _run_multi_turn_scenarios(config, client))
        rows.extend(await _run_attachment_scenario(config, client))
    _write_csv(rows, config.output_path)
    _render_report(rows, config.report_path)
    run_elapsed_ms = round((time.perf_counter() - run_started_at) * 1000, 2)
    print(f"Wrote {len(rows)} rows to {config.output_path} in {run_elapsed_ms} ms")


if __name__ == "__main__":
    asyncio.run(main())
