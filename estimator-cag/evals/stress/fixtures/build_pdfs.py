from __future__ import annotations

from pathlib import Path

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas


GENERATED_DIR = Path(__file__).resolve().parent / "generated"
TEXT_FACT = "Attachment fact: latency-budget-anchor"


def _build_target_text(target_kb: int) -> str:
    line = (
        "Synthetic attachment for estimator-cag stress testing. "
        f"{TEXT_FACT}. Scope marker for deterministic recall checks. "
        "This paragraph is repeated to reach the requested approximate file size.\n"
    )
    target_bytes = target_kb * 1024
    buffer = line
    while len(buffer.encode("utf-8")) < target_bytes:
        buffer += line
    return buffer


def build_pdf(target_kb: int) -> Path:
    GENERATED_DIR.mkdir(parents=True, exist_ok=True)
    output_path = GENERATED_DIR / f"attach_{target_kb}kb.pdf"
    text = _build_target_text(target_kb)

    pdf = canvas.Canvas(str(output_path), pagesize=A4)
    width, height = A4
    cursor_y = height - 48
    for paragraph in text.splitlines():
        remaining = paragraph
        while remaining:
            chunk = remaining[:95]
            pdf.drawString(40, cursor_y, chunk)
            remaining = remaining[95:]
            cursor_y -= 16
            if cursor_y < 48:
                pdf.showPage()
                cursor_y = height - 48
    pdf.save()
    return output_path


def build_all(target_sizes_kb: list[int]) -> list[Path]:
    return [build_pdf(size) for size in target_sizes_kb if size > 0]


if __name__ == "__main__":
    build_all([5, 20, 50, 100])
