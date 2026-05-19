import pytest

from app.context import sample_transcriptions


def test_list_sample_transcriptions_returns_markdown_files() -> None:
    files = sample_transcriptions.list_sample_transcriptions()

    assert "meeting-health-clinic.md" in files


def test_read_sample_transcription_returns_text() -> None:
    content = sample_transcriptions.read_sample_transcription("meeting-health-clinic.md")

    assert "clínica privada" in content
    assert len(content) > 50


def test_read_sample_transcription_rejects_unknown_file() -> None:
    with pytest.raises(ValueError, match="Unknown sample transcription"):
        sample_transcriptions.read_sample_transcription("missing.md")
