from collections.abc import Mapping

from agent_techie.agents.model import StructuredModel
from agent_techie.graph.state import CodeChange, ReviewFinding, ReviewReport, TestReport


class ReviewerAgent:
    """Review proposed changes and test results."""

    def __init__(self, model: StructuredModel | None = None) -> None:
        self.model = model

    def run(
        self,
        change: CodeChange | Mapping[str, object],
        tests: TestReport | Mapping[str, object],
        user_request: str = "",
    ) -> ReviewReport:
        change = CodeChange.model_validate(change)
        tests = TestReport.model_validate(tests)
        if self.model is not None:
            report = self.model.generate(
                "Review the proposed code as a careful senior engineer. Find concrete "
                "correctness, security, reliability, and maintainability problems. "
                "Reference a file and line when available and recommend a specific "
                "fix. Do not assert tests passed unless the test report says so. "
                "Approve only if the proposal has code and no important unresolved "
                "findings.",
                (
                    f"Task: {user_request}\n"
                    f"Proposed code and change summary:\n{change.model_dump_json()}\n"
                    f"Test report:\n{tests.model_dump_json()}"
                ),
                ReviewReport,
            )
            report.review_mode = "llm"
            if not change.file_contents:
                report.findings.append("The proposal contains no source file contents")
                report.approved = False
            if not tests.passed:
                report.findings.append("Tests did not pass")
                report.approved = False
            if report.findings or any(
                finding.severity in ("critical", "high") for finding in report.details
            ):
                report.approved = False
            return report

        findings: list[str] = []
        if not change.changes:
            findings.append("The change contains no implementation steps")
        if not tests.passed:
            findings.append("Tests did not pass")
        details = [
            ReviewFinding(severity="high", issue=finding) for finding in findings
        ]
        return ReviewReport(
            approved=not findings,
            findings=findings,
            details=details,
            summary=(
                "Deterministic checks passed; no substantive source-code review "
                "was performed"
            )
            if not findings
            else "Changes need attention",
        )
