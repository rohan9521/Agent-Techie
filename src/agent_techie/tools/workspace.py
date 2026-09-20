"""Least-privilege repository filesystem and command tools."""

import os
import shlex
import subprocess
from dataclasses import dataclass
from pathlib import Path


class ToolSecurityError(PermissionError):
    """Raised when a tool request escapes its configured policy."""


@dataclass(frozen=True)
class CommandResult:
    returncode: int
    stdout: str
    stderr: str


class WorkspaceTools:
    def __init__(
        self,
        root: str | os.PathLike[str],
        allowed_commands: set[str] | None = None,
        max_output_bytes: int = 1_000_000,
    ) -> None:
        self.root = Path(root).resolve()
        self.root.mkdir(parents=True, exist_ok=True)
        self.allowed_commands = allowed_commands or {"git", "pytest", "ruff", "mypy"}
        self.max_output_bytes = max_output_bytes

    def resolve(self, relative_path: str) -> Path:
        candidate = (self.root / relative_path).resolve()
        if candidate != self.root and self.root not in candidate.parents:
            raise ToolSecurityError("path is outside the workspace")
        return candidate

    def read_file(self, relative_path: str) -> str:
        return self.resolve(relative_path).read_text(encoding="utf-8")

    def write_file(self, relative_path: str, content: str) -> None:
        target = self.resolve(relative_path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")

    def list_files(self, relative_path: str = ".") -> list[str]:
        base = self.resolve(relative_path)
        return sorted(
            str(path.relative_to(self.root))
            for path in base.rglob("*")
            if path.is_file()
        )

    def run_command(self, command: str, timeout: float = 30.0) -> CommandResult:
        parts = shlex.split(command)
        if not parts or parts[0] not in self.allowed_commands:
            raise ToolSecurityError("command is not allowlisted")
        if any(
            token in command for token in (";", "&&", "||", "|", ">", "<", "`", "$(")
        ):
            raise ToolSecurityError("shell operators are not allowed")
        completed = subprocess.run(
            parts,
            cwd=self.root,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
            env={"PATH": os.environ.get("PATH", "")},
        )
        return CommandResult(
            completed.returncode,
            completed.stdout[: self.max_output_bytes],
            completed.stderr[: self.max_output_bytes],
        )
