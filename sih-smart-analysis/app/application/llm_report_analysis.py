from __future__ import annotations

from collections.abc import Iterator

from app.config import Settings
from app.domain.models import AnalysisResult, RunReport


class LLMReportAnalyst:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    def enrich(self, result: AnalysisResult, reports: list[RunReport]) -> AnalysisResult:
        if not self._settings.llm_enabled:
            return result

        try:
            insight = self.generate_insight(result, reports)
        except Exception as exc:
            insight = f"LLM analysis unavailable: {exc}"

        if not insight:
            return result

        return AnalysisResult(
            mode=result.mode,
            workflow=result.workflow,
            environment=result.environment,
            current_run_id=result.current_run_id,
            health_score=result.health_score,
            summary=result.summary,
            failure_type=result.failure_type,
            regressions=result.regressions,
            recommendations=result.recommendations,
            sources=result.sources,
            llm_insights=insight,
        )

    def generate_insight(self, result: AnalysisResult, reports: list[RunReport]) -> str | None:
        from litellm import completion

        response = completion(
            model=self._settings.llm_model,
            max_tokens=self._settings.llm_max_tokens,
            messages=self.messages(result, reports),
        )
        return response.choices[0].message.content

    def stream_insight(self, result: AnalysisResult, reports: list[RunReport]) -> Iterator[str]:
        if not self._settings.llm_enabled:
            return

        from litellm import completion

        stream = completion(
            model=self._settings.llm_model,
            max_tokens=self._settings.llm_max_tokens,
            messages=self.messages(result, reports),
            stream=True,
        )
        for chunk in stream:
            delta = chunk.choices[0].delta
            if isinstance(delta, dict):
                content = delta.get("content")
            else:
                content = getattr(delta, "content", None)
            if content:
                yield content

    def messages(self, result: AnalysisResult, reports: list[RunReport]) -> list[dict[str, str]]:
        return [
            {
                "role": "system",
                "content": (
                    "Eres un analista senior de calidad e integraciones SIH. "
                    "Evalua reports de ejecucion con rigor operativo: calcula medias, "
                    "compara latencias, detecta problemas probables, riesgos de regresion "
                    "y siguientes acciones. Antes de responder, razona internamente sobre "
                    "timings, endpoints, codigos HTTP, outputs y diferencias entre "
                    "modelos/proveedores; no muestres cadena de pensamiento, solo el "
                    "resultado estructurado. No te limites a repetir el score determinista. "
                    "Responde en español, concreto y en Markdown."
                ),
            },
            {
                "role": "user",
                "content": self._build_prompt(result, reports),
            },
        ]

    def count_tokens(self, *, messages: list[dict[str, str]] | None = None, text: str | None = None) -> int:
        try:
            from litellm import token_counter

            return int(token_counter(model=self._settings.llm_model, messages=messages, text=text))
        except Exception:
            source = text or " ".join(message["content"] for message in messages or [])
            return max(1, len(source) // 4) if source else 0

    def _build_prompt(self, result: AnalysisResult, reports: list[RunReport]) -> str:
        report_lines = []
        for report in reports:
            stages = "\n".join(self._stage_line(stage) for stage in report.stages)
            run_context = f"\n  contexto ejecucion: {report.context}" if report.context else ""
            report_lines.append(
                f"- {report.run_id} | {report.started_at.isoformat()} | "
                f"{report.status} | {report.duration_ms}ms{run_context}\n"
                f"  stages:\n{stages}"
            )

        regression_lines = [
            f"- {signal.stage}: {signal.signal} ({signal.severity}) - {signal.evidence}"
            for signal in result.regressions
        ] or ["- sin regresiones detectadas por reglas"]

        return f"""Resultado determinista:
- modo: {result.mode}
- workflow: {result.workflow}
- environment: {result.environment}
- current_run_id: {result.current_run_id}
- health_score: {result.health_score}
- failure_type: {result.failure_type}
- summary: {result.summary}

Señales detectadas:
{chr(10).join(regression_lines)}

Resumen cuantitativo de tiempos:
{self._timing_summary(reports)}

Reports usados como contexto:
{chr(10).join(report_lines)}

Genera:
1. Diagnóstico probable con confianza alta/media/baja.
2. Tabla Markdown de stages/endpoints con media, mínimo, máximo, última duración y desviación de la última ejecución frente a la media.
3. Problemas concretos o señales sospechosas vistas en outputs/stages.
4. Riesgos o problemas latentes no obvios, separando rendimiento, contrato, autenticación y dependencias.
5. Siguientes acciones recomendadas, priorizadas.
6. Qué dato falta para confirmar la hipótesis.

Haz un análisis más profundo de lo habitual, pero no inventes datos que no estén en el contexto."""

    def _stage_line(self, stage) -> str:
        context = f", contexto={stage.context}" if stage.context else ""
        endpoint = ""
        if stage.http_method or stage.request_uri:
            endpoint = f", endpoint={stage.http_method or '-'} {stage.request_uri or '-'}"
        return (
            f"  - {stage.name}: {stage.status}, {stage.duration_ms}ms, "
            f"http={stage.http_status}, error={stage.error_type}, "
            f"message={stage.message}{endpoint}{context}"
        )

    def _timing_summary(self, reports: list[RunReport]) -> str:
        by_target: dict[str, list[int]] = {}
        for report in reports:
            for stage in report.stages:
                target = self._timing_target(stage)
                by_target.setdefault(target, []).append(stage.duration_ms)

        if not by_target:
            return "- sin datos de tiempos por stage"

        lines = []
        for target, durations in sorted(by_target.items()):
            average = sum(durations) / len(durations)
            latest = durations[0]
            delta = latest - average
            delta_percent = (delta / average * 100) if average else 0
            lines.append(
                f"- {target}: n={len(durations)}, media={average:.0f}ms, "
                f"min={min(durations)}ms, max={max(durations)}ms, "
                f"ultima={latest}ms, desviacion_ultima={delta:+.0f}ms ({delta_percent:+.1f}%)"
            )
        return "\n".join(lines)

    def _timing_target(self, stage) -> str:
        if stage.request_uri:
            method = stage.http_method or "-"
            return f"{stage.name} | {method} {stage.request_uri}"
        return stage.name
