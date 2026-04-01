from __future__ import annotations
from app.llm.schemas import EDAReviewResult, Severity, Priority


_SEV_ICON = {
    Severity.HIGH:   "🔴",
    Severity.MEDIUM: "🟡",
    Severity.LOW:    "🟢",
}
_PRI_LABEL = {
    Priority.MUST:     "[MUST]",
    Priority.SHOULD:   "[SHOULD]",
    Priority.OPTIONAL: "[OPTIONAL]",
}


class ReportAssembler:

    def to_markdown(self, result: EDAReviewResult) -> str:
        src = result.overview.get("source_file", "dataset")
        rows = result.overview.get("rows", "?")
        cols = result.overview.get("cols", "?")
        score = result.overview.get("quality_score", "?")

        lines: list[str] = [
            f"# EDA Review — {src}",
            f"> {rows:,} rows · {cols} columns · quality score {score}\n",
        ]

        lines.append("## Data Quality Issues\n")
        if not result.issues:
            lines.append("No issues detected.\n")
        else:
            for issue in result.issues:
                icon  = _SEV_ICON[issue.severity]
                label = issue.severity.value.upper()
                lines += [
                    f"### {icon} `{issue.col}` — {label}",
                    f"**What:** {issue.detail}",
                    f"**Impact:** {issue.impact}\n",
                ]

        lines.append("## Preprocessing Recommendations\n")
        if not result.prep_steps:
            lines.append("No preprocessing required.\n")
        else:
            for step in result.prep_steps:
                label  = _PRI_LABEL[step.priority]
                target = f"`{step.col}`" if step.col else "dataset"
                lines += [
                    f"**{label}** `{step.action}` → {target}",
                    f"{step.rationale}\n",
                ]

        lines.append("## Analytical Opportunities\n")
        lines += [f"- {opp}" for opp in result.opportunities]

        return "\n".join(lines)