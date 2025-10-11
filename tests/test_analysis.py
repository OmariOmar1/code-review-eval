import pytest

from code_review_eval.analysis import (
    analyze,
    objective_winner,
    render_report,
    wilson_interval,
)
from code_review_eval.judge import CRITERIA


def result(task_id, candidate, passed, total=4):
    return {
        "task_id": task_id,
        "candidate": candidate,
        "tests_passed": passed,
        "tests_total": total,
        "runtime_s": 0.01,
    }


def preference(task_id, winner, a_correct=3, b_correct=3):
    scores = {label: {criterion: 3 for criterion in CRITERIA} for label in "AB"}
    scores["A"]["correctness"] = a_correct
    scores["B"]["correctness"] = b_correct
    return {
        "task_id": task_id,
        "scores": scores,
        "winner": winner,
        "reason": f"{winner} is better.",
        "judge": "mock",
    }


RESULTS = [
    result("t1", "A", 4), result("t1", "B", 2),  # A wins
    result("t2", "A", 1), result("t2", "B", 4),  # B wins
    result("t3", "A", 4), result("t3", "B", 4),  # tie
    result("t4", "A", 0), result("t4", "B", 3),  # B wins
]
PREFERENCES = [
    preference("t1", "A", 5, 2),
    preference("t2", "A", 4, 2),
    preference("t3", "B", 3, 3),
    preference("t4", "B", 1, 4),
]


def test_objective_winner():
    assert objective_winner(result("t", "A", 3), result("t", "B", 1)) == "A"
    assert objective_winner(result("t", "A", 1), result("t", "B", 3)) == "B"
    assert objective_winner(result("t", "A", 2), result("t", "B", 2)) == "tie"


def test_agreement_excludes_ties():
    summary = analyze(RESULTS, PREFERENCES)
    assert summary["tasks"] == 4
    assert summary["decisive"] == 3
    assert summary["ties"] == 1
    assert summary["agreed"] == 2
    assert summary["agreement_rate"] == pytest.approx(2 / 3)
    assert [row["agrees"] for row in summary["rows"]] == [True, False, None, True]


def test_correctness_order_and_pick_counts():
    summary = analyze(RESULTS, PREFERENCES)
    assert summary["correctness_order_agreed"] == 3
    assert summary["judge_picks"] == {"A": 2, "B": 2}
    assert summary["objective_picks"] == {"A": 1, "B": 2, "tie": 1}
    assert summary["mean_scores"]["A"]["correctness"] == 3.25


def test_all_ties_gives_undefined_rate():
    summary = analyze(RESULTS[4:6], PREFERENCES[2:3])
    assert summary["agreement_rate"] is None
    assert "undefined" in render_report(summary)


def test_mismatched_inputs_are_rejected():
    with pytest.raises(ValueError, match="different tasks"):
        analyze(RESULTS, PREFERENCES[:2])
    with pytest.raises(ValueError, match="both candidates"):
        analyze(RESULTS[:1], PREFERENCES[:1])


def test_wilson_interval():
    assert wilson_interval(0, 0) == (0.0, 0.0)
    low, high = wilson_interval(7, 8)
    assert 0.5 < low < 0.875 < high <= 1.0
    assert wilson_interval(8, 8)[1] == 1.0


def test_report_lists_disagreements():
    report = render_report(analyze(RESULTS, PREFERENCES), backend="local")
    assert "**2 of 3**" in report
    assert "| t2 | 1/4 | 4/4 | B | A | **no** |" in report
    assert "- **t2**: tests favour B" in report
    assert "`local`" in report
