import json
from types import SimpleNamespace

import pytest

from code_review_eval import judge as judge_module
from code_review_eval.judge import (
    CRITERIA,
    JudgeError,
    LLMJudge,
    MockJudge,
    build_messages,
    code_features,
    extract_json,
    get_judge,
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


class FakeClient:
    """Stands in for the API client and records the request."""

    def __init__(self, text, stop_reason="end_turn"):
        self.request = None
        self._response = SimpleNamespace(
            stop_reason=stop_reason, content=[SimpleNamespace(type="text", text=text)]
        )
        self.messages = SimpleNamespace(create=self._create)

    def _create(self, **kwargs):
        self.request = kwargs
        return self._response


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


def test_mock_judge_prefers_documented_candidate(task):
    result = MockJudge().judge(task)
    assert result.winner == "A"
    assert result.judge == "mock"
    assert result.reason.endswith(".")
    validate_verdict(result.to_dict())


def test_mock_judge_is_deterministic_on_real_tasks():
    judge = MockJudge()
    for task in load_tasks(TASKS_DIR):
        first, second = judge.judge(task).to_dict(), judge.judge(task).to_dict()
        assert first == second
        validate_verdict(first)


def test_build_messages_contains_task_and_both_candidates(task):
    system, messages = build_messages(task, "RUBRIC TEXT")
    assert "RUBRIC TEXT" in system
    content = messages[0]["content"]
    assert task.prompt.strip() in content
    assert task.candidates["A"].rstrip() in content
    assert task.candidates["B"].rstrip() in content
    assert content.index("<candidate_a>") < content.index("<candidate_b>")


def test_llm_judge_parses_response(task):
    client = FakeClient(json.dumps(verdict(winner="B", reason="B handles empty input.")))
    result = LLMJudge(client=client, model="test-model", rubric="rubric").judge(task)
    assert result.winner == "B"
    assert result.judge == "llm"
    assert result.task_id == task.task_id
    assert client.request["model"] == "test-model"
    assert "JSON object" in client.request["system"]
    assert "tests_passed" not in client.request["messages"][0]["content"]


@pytest.mark.parametrize(
    "text, stop_reason",
    [
        ("not json", "end_turn"),
        (json.dumps(verdict(winner="nobody")), "end_turn"),
        (json.dumps(verdict()), "max_tokens"),
        (json.dumps(verdict()), "refusal"),
    ],
)
def test_llm_judge_rejects_bad_responses(task, text, stop_reason):
    judge = LLMJudge(client=FakeClient(text, stop_reason), model="m", rubric="rubric")
    with pytest.raises(JudgeError):
        judge.judge(task)


def test_extract_json_handles_code_fences():
    assert extract_json('```json\n{"a": {"b": 1}}\n```') == {"a": {"b": 1}}
    for text in ("", "no braces", "} backwards {", "{not json}"):
        with pytest.raises(JudgeError):
            extract_json(text)


def test_llm_judge_accepts_fenced_reply(task):
    client = FakeClient("```json\n" + json.dumps(verdict(winner="B")) + "\n```")
    assert LLMJudge(client=client, model="m", rubric="r").judge(task).winner == "B"


def test_llm_judge_needs_api_key(monkeypatch):
    monkeypatch.delenv(judge_module.API_KEY_ENV, raising=False)
    with pytest.raises(JudgeError, match=judge_module.API_KEY_ENV):
        LLMJudge(model="m")


def test_llm_judge_needs_model(monkeypatch):
    monkeypatch.delenv(judge_module.MODEL_ENV, raising=False)
    with pytest.raises(JudgeError, match=judge_module.MODEL_ENV):
        LLMJudge(client=FakeClient("{}"), rubric="r")


def test_model_can_be_set_from_environment(monkeypatch):
    monkeypatch.setenv(judge_module.MODEL_ENV, "some-model")
    assert LLMJudge(client=FakeClient("{}"), rubric="r").model == "some-model"


def test_get_judge_auto_falls_back_to_mock(monkeypatch):
    monkeypatch.delenv(judge_module.API_KEY_ENV, raising=False)
    assert isinstance(get_judge("auto"), MockJudge)
    assert isinstance(get_judge("mock"), MockJudge)
    with pytest.raises(ValueError):
        get_judge("oracle")


def test_get_judge_auto_uses_llm_when_key_present(monkeypatch):
    monkeypatch.setenv(judge_module.API_KEY_ENV, "test-key")
    monkeypatch.setenv(judge_module.MODEL_ENV, "some-model")
    assert isinstance(get_judge("auto"), LLMJudge)
