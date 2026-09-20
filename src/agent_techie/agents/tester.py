from collections.abc import Mapping

from agent_techie.graph.state import CodeChange, TestReport


class TesterAgent:
    """Return a deterministic test result for a proposed change.

    Real command execution is deliberately delegated to ``WorkspaceTools`` and is
    opt-in, so tests and deployments do not require a checkout or a shell.
    """

    def run(
        self, change: CodeChange | Mapping[str, object], command: str = ""
    ) -> TestReport:
        change = CodeChange.model_validate(change)
        if not change.changes:
            return TestReport(
                passed=False, command=command, failures=["No implementation plan"]
            )
        return TestReport(
            passed=True,
            command=command or "not-run (dry-run)",
            output="Deterministic validation passed; execution was not requested.",
        )
