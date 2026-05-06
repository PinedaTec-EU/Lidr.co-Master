from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class SihRunCommand:
    workflow: Path
    environment: str
    catalog: Path | None = None
    varsfile: Path | None = None
    report_format: str = "both"
    capture_http: str = "bodies"
    refresh_cache: bool = False
    mocked: bool = False


@dataclass(frozen=True)
class SihRunResult:
    exit_code: int
    stdout: str
    stderr: str

    @property
    def succeeded(self) -> bool:
        return self.exit_code == 0


class SihCliRunner:
    def __init__(self, command: Path) -> None:
        self._command = command

    def run(self, command: SihRunCommand) -> SihRunResult:
        args = [
            str(self._command),
            "--workflow",
            str(command.workflow),
            "--env",
            command.environment,
            "--report-format",
            command.report_format,
            "--capture-http",
            command.capture_http,
        ]

        if command.catalog:
            args.extend(["--catalog", str(command.catalog)])
        if command.varsfile:
            args.extend(["--varsfile", str(command.varsfile)])
        if command.refresh_cache:
            args.append("--refresh-cache")
        if command.mocked:
            args.append("--mocked")

        completed = subprocess.run(args, capture_output=True, text=True, check=False)
        return SihRunResult(
            exit_code=completed.returncode,
            stdout=completed.stdout,
            stderr=completed.stderr,
        )
