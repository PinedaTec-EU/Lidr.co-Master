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
                    "Evalua reports de ejecucion, detecta problemas probables, "
                    "riesgos de regresion y siguientes acciones. Responde en español, "
                    "conciso y en Markdown."
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
            stages = "; ".join(
                (
                    f"{stage.name}: {stage.status}, {stage.duration_ms}ms, "
                    f"http={stage.http_status}, error={stage.error_type}"
                )
                for stage in report.stages
            )
            report_lines.append(
                f"- {report.run_id} | {report.started_at.isoformat()} | "
                f"{report.status} | {report.duration_ms}ms | {stages}"
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

Reports usados como contexto:
{chr(10).join(report_lines)}

Genera:
1. Diagnóstico probable.
2. Riesgos o problemas latentes no obvios.
3. Siguientes acciones recomendadas.
4. Qué dato falta para confirmar la hipótesis."""
