from __future__ import annotations

import re
from collections import Counter

from app.domain.models import RunReport


class RunSemanticText:
    def build(self, run: RunReport) -> str:
        failed = " ".join(
            f"{stage.name} {stage.status} {stage.error_type} {stage.http_status or ''} {stage.message or ''}"
            for stage in run.stages
        )
        return f"{run.workflow} {run.environment} {run.version} {run.status} {failed}"


class TokenSimilarity:
    def score(self, left: str, right: str) -> float:
        left_counts = self._tokens(left)
        right_counts = self._tokens(right)
        if not left_counts or not right_counts:
            return 0.0

        intersection = set(left_counts) & set(right_counts)
        numerator = sum(left_counts[token] * right_counts[token] for token in intersection)
        left_norm = sum(value * value for value in left_counts.values()) ** 0.5
        right_norm = sum(value * value for value in right_counts.values()) ** 0.5
        return numerator / (left_norm * right_norm)

    def _tokens(self, text: str) -> Counter[str]:
        return Counter(re.findall(r"[a-z0-9_:-]+", text.lower()))

