import pytest

from code_review_eval.judge import (
    CRITERIA,
    HeuristicJudge,
    JudgeError,
    code_features,
    heuristic_scores,
    validate_verdict,
)
from code_review_eval.tasks import load_tasks

from .conftest import BAD, GOOD, TASKS_DIR


def verdict(winner="A", reason="A is correct and B is not.", **overrides):
    scores = {label: {criterion: 3 for criterion in CRITERIA} for label in "AB"}
    data = {"scores": scores, "winner": winner, "reason": reason}
    data.update(overrides)
    return data


def test_validate_accepts_good_verdict():
    scores, winner, reason = validate_verdict(verdict(reason="  A is\nbetter. "))
    assert winner == "A"
    assert reason == "A is better."
    assert list(scores["A"]) == list(CRITERIA)


@pytest.mark.parametrize(
    "broken",
    [
        "not a dict",
        verdict(winner="C"),
        verdict(winner="tie"),
        verdict(reason=""),
        verdict(scores={"A": {}}),
        verdict(scores={"A": {c: 3 for c in CRITERIA}, "B": {c: 6 for c in CRITERIA}}),
        verdict(scores={"A": {c: 3 for c in CRITERIA}, "B": {c: 0 for c in CRITERIA}}),
        verdict(scores={"A": {c: 3 for c in CRITERIA}, "B": {c: 2.5 for c in CRITERIA}}),
        verdict(scores={"A": {c: 3 for c in CRITERIA}, "B": {c: True for c in CRITERIA}}),
        verdict(scores={"A": {c: 3 for c in CRITERIA}, "B": {"correctness": 3}}),
    ],
)
def test_validate_rejects_bad_verdicts(broken):
    with pytest.raises(JudgeError):
        validate_verdict(broken)


def test_code_features():
    features = code_features(GOOD)
    assert features["parses"]
    assert features["docstrings"] == 1
    assert features["doctests"] == 1
    assert not code_features("def broken(:\n")["parses"]


def test_heuristic_scores_in_range_and_ordered():
    good, bad = heuristic_scores(GOOD), heuristic_scores(BAD)
    for scores in (good, bad):
        assert set(scores) == set(CRITERIA)
        assert all(isinstance(v, int) and 1 <= v <= 5 for v in scores.values())
    assert good["test_quality"] > bad["test_quality"]
    assert good["readability"] > bad["readability"]


def test_unparseable_code_scores_minimum():
    assert set(heuristic_scores("def broken(:\n").values()) == {1}


def test_judge_prefers_documented_candidate(task):
    result = HeuristicJudge().judge(task)
    assert result.winner == "A"
    assert result.judge == "heuristic"
    assert result.reason.endswith(".")
    validate_verdict(result.to_dict())


def test_judge_is_deterministic_on_real_tasks():
    judge = HeuristicJudge()
    for task in load_tasks(TASKS_DIR):
        first, second = judge.judge(task).to_dict(), judge.judge(task).to_dict()
        assert first == second
        validate_verdict(first)
