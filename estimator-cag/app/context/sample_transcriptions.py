from pathlib import Path


SAMPLE_TRANSCRIPTIONS_DIR = Path(__file__).resolve().parents[2] / "sample-transcriptions"


def list_sample_transcriptions() -> list[str]:
    if not SAMPLE_TRANSCRIPTIONS_DIR.exists():
        return []

    return sorted(
        path.name
        for path in SAMPLE_TRANSCRIPTIONS_DIR.iterdir()
        if path.is_file() and path.suffix == ".md"
    )


def read_sample_transcription(filename: str) -> str:
    path = SAMPLE_TRANSCRIPTIONS_DIR / filename
    if not path.exists() or path.suffix != ".md":
        raise ValueError(f"Unknown sample transcription '{filename}'")

    return path.read_text(encoding="utf-8").strip()
