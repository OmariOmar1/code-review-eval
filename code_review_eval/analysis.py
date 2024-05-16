"""Compare the judge's picks with the objective test results."""

import json
import math
from pathlib import Path

from .judge import CRITERIA
from .pipeline import read_jsonl
from .tasks import CANDIDATES


def objective_winner(result_a, result_b):
    """The candidate that passes more tests, or ``"tie"``."""
    if result_a["tests_passed"] > result_b["tests_passed"]:
        return "A"
    if result_b["tests_passed"] > result_a["tests_passed"]:
        return "B"
    return "tie"


def wilson_interval(successes, total, z=1.96):
    """95% Wilson score interval for a proportion."""
    if total == 0:
        return (0.0, 0.0)
    p = successes / total
    denominator = 1 + z * z / total
    centre = (p + z * z / (2 * total)) / denominator
    margin = z * math.sqrt(p * (1 - p) / total + z * z / (4 * total * total)) / denominator
    return (max(0.0, centre - margin), min(1.0, centre + margin))


def _sign(value):
    return (value > 0) - (value < 0)


def analyze(results, preferences):
    """Join test results with judge verdicts and compute agreement.

    ``results`` is the list of per-candidate run results and ``preferences``
    the list of judge rows. Tasks present in only one of them are an error.
    """
    by_task = {}
    for result in results:
        by_task.setdefault(result["task_id"], {})[result["candidate"]] = result
    verdicts = {row["task_id"]: row for row in preferences}
    if set(by_task) != set(verdicts):
        mismatch = sorted(set(by_task) ^ set(verdicts))
        raise ValueError(f"test results and preferences cover different tasks: {mismatch}")

    rows = []
    for task_id in sorted(by_task):
        runs = by_task[task_id]
        if set(runs) != set(CANDIDATES):
            raise ValueError(f"{task_id}: expected results for both candidates")
        verdict = verdicts[task_id]
        objective = objective_winner(runs["A"], runs["B"])
        score_gap = verdict["scores"]["A"]["correctness"] - verdict["scores"]["B"]["correctness"]
        test_gap = runs["A"]["tests_passed"] - runs["B"]["tests_passed"]
        rows.append(
            {
                "task_id": task_id,
                "tests": {
                    label: f'{runs[label]["tests_passed"]}/{runs[label]["tests_total"]}'
                    for label in CANDIDATES
                },
                "runtime_s": {label: runs[label]["runtime_s"] for label in CANDIDATES},
                "objective_winner": objective,
                "judge_winner": verdict["winner"],
                "agrees": None if objective == "tie" else verdict["winner"] == objective,
                "correctness_order_agrees": _sign(score_gap) == _sign(test_gap),
                "reason": verdict["reason"],
            }
        )

    decisive = [row for row in rows if row["agrees"] is not None]
    agreed = sum(1 for row in decisive if row["agrees"])
    mean_scores = {
        label: {
            criterion: round(
                sum(v["scores"][label][criterion] for v in preferences) / len(preferences), 2
            )
            for criterion in CRITERIA
        }
        for label in CANDIDATES
    } if preferences else {}
    return {
        "judge": preferences[0].get("judge", "unknown") if preferences else "unknown",
        "tasks": len(rows),
        "decisive": len(decisive),
        "ties": len(rows) - len(decisive),
        "agreed": agreed,
        "agreement_rate": agreed / len(decisive) if decisive else None,
        "agreement_interval": wilson_interval(agreed, len(decisive)),
        "correctness_order_agreed": sum(1 for row in rows if row["correctness_order_agrees"]),
        "judge_picks": {
            label: sum(1 for row in rows if row["judge_winner"] == label) for label in CANDIDATES
        },
        "objective_picks": {
            label: sum(1 for row in rows if row["objective_winner"] == label)
            for label in (*CANDIDATES, "tie")
        },
        "mean_scores": mean_scores,
        "rows": rows,
    }


def _mark(value):
    return {True: "yes", False: "**no**", None: "n/a"}[value]


def render_report(summary, backend="unknown"):
    """Render the analysis summary as Markdown."""
    lines = ["# Judge vs. Tests Report", ""]
    lines.append(f"- Judge: `{summary['judge']}`")
    lines.append(f"- Test backend: `{backend}`")
    lines.append(f"- Tasks: {summary['tasks']}")
    lines.append("")
    lines.append("## Headline")
    lines.append("")
    if summary["agreement_rate"] is None:
        lines.append("No task had a decisive objective winner, so agreement is undefined.")
    else:
        low, high = summary["agreement_interval"]
        lines.append(
            f"The judge picked the candidate that passes more tests in "
            f"**{summary['agreed']} of {summary['decisive']}** decisive tasks "
            f"(**{summary['agreement_rate']:.0%}**, 95% Wilson interval "
            f"{low:.0%} to {high:.0%})."
        )
    lines.append("")
    lines.append(
        f"{summary['ties']} task(s) were objective ties (both candidates pass the same "
        "number of tests) and are left out of the agreement rate."
    )
    lines.append("")
    lines.append(
        f"The judge's correctness scores ranked the candidates the same way as the tests "
        f"(including ties) in {summary['correctness_order_agreed']} of {summary['tasks']} tasks."
    )
    lines.append("")
    lines.append("## Per task")
    lines.append("")
    lines.append("| Task | A tests | B tests | Objective | Judge | Agree |")
    lines.append("|------|---------|---------|-----------|-------|-------|")
    for row in summary["rows"]:
        lines.append(
            f"| {row['task_id']} | {row['tests']['A']} | {row['tests']['B']} | "
            f"{row['objective_winner']} | {row['judge_winner']} | {_mark(row['agrees'])} |"
        )
    lines.append("")
    disagreements = [row for row in summary["rows"] if row["agrees"] is False]
    lines.append("## Disagreements")
    lines.append("")
    if not disagreements:
        lines.append("None.")
    for row in disagreements:
        lines.append(
            f"- **{row['task_id']}**: tests favour {row['objective_winner']} "
            f"({row['tests']['A']} vs {row['tests']['B']}), judge picked "
            f"{row['judge_winner']}. Judge's reason: {row['reason']}"
        )
    lines.append("")
    lines.append("## Pick distribution")
    lines.append("")
    lines.append("| | A | B | Tie |")
    lines.append("|---|---|---|-----|")
    objective = summary["objective_picks"]
    judge = summary["judge_picks"]
    lines.append(f"| Tests | {objective['A']} | {objective['B']} | {objective['tie']} |")
    lines.append(f"| Judge | {judge['A']} | {judge['B']} | n/a |")
    lines.append("")
    lines.append("## Mean judge scores")
    lines.append("")
    lines.append("| Candidate | " + " | ".join(c.replace("_", " ") for c in CRITERIA) + " |")
    lines.append("|---|" + "---|" * len(CRITERIA))
    for label in CANDIDATES:
        scores = summary["mean_scores"].get(label, {})
        lines.append(
            f"| {label} | " + " | ".join(f"{scores.get(c, 0):.2f}" for c in CRITERIA) + " |"
        )
    lines.append("")
    return "\n".join(lines)


def write_report(results_path, preferences_path, report_path):
    """Read the two output files, analyse them and write ``report.md``."""
    payload = json.loads(Path(results_path).read_text())
    summary = analyze(payload["results"], read_jsonl(preferences_path))
    Path(report_path).write_text(render_report(summary, backend=payload.get("backend", "unknown")))
    return summary
