from collections.abc import Mapping

from agent_techie.graph.state import CodeChange, ReviewReport, TestReport


class ReviewerAgent:
    """Review proposed changes and test results without an LLM or network."""

    def run(
        self,
        change: CodeChange | Mapping[str, object],
        tests: TestReport | Mapping[str, object],
    ) -> ReviewReport:
        change = CodeChange.model_validate(change)
        tests = TestReport.model_validate(tests)
        findings: list[str] = []
        if not change.changes:
            findings.append("The change contains no implementation steps")
        if not tests.passed:
            findings.append("Tests did not pass")
        return ReviewReport(
            approved=not findings,
            findings=findings,
            summary="Change is ready for approval"
            if not findings
            else "Changes need attention",
        )
