"""Judges that score two candidates against the rubric and pick a winner.

``LLMJudge`` asks a language model. ``MockJudge`` is a deterministic set of
static-analysis heuristics so the whole pipeline can run offline. Neither
judge is shown the test results.
"""

import ast
import json
import os
import re
from dataclasses import dataclass
from pathlib import Path

from .tasks import CANDIDATES

CRITERIA = ("correctness", "readability", "edge_case_handling", "test_quality")
API_KEY_ENV = "ANTHROPIC_API_KEY"
MODEL_ENV = "JUDGE_MODEL"
MAX_TOKENS = 8192
RUBRIC_PATH = Path(__file__).resolve().parent.parent / "RUBRIC.md"

# Correctness counts double when the mock judge totals its scores.
WEIGHTS = {"correctness": 2, "readability": 1, "edge_case_handling": 1, "test_quality": 1}


class JudgeError(RuntimeError):
    """The judge could not produce a usable verdict."""


@dataclass
class Verdict:
    """A judge's scores for both candidates plus its preferred one."""

    task_id: str
    scores: dict
    winner: str
    reason: str
    judge: str

    def to_dict(self):
        return {
            "task_id": self.task_id,
            "scores": self.scores,
            "winner": self.winner,
            "reason": self.reason,
            "judge": self.judge,
        }


def validate_verdict(data):
    """Check a raw verdict dict and return ``(scores, winner, reason)``."""
    if not isinstance(data, dict):
        raise JudgeError("verdict is not an object")
    scores = data.get("scores")
    if not isinstance(scores, dict) or set(scores) != set(CANDIDATES):
        raise JudgeError("verdict must have scores for exactly A and B")
    clean = {}
    for label in CANDIDATES:
        candidate_scores = scores[label]
        if not isinstance(candidate_scores, dict) or set(candidate_scores) != set(CRITERIA):
            raise JudgeError(f"candidate {label} must be scored on: {', '.join(CRITERIA)}")
        for criterion, value in candidate_scores.items():
            if isinstance(value, bool) or not isinstance(value, int) or not 1 <= value <= 5:
                raise JudgeError(f"{label}.{criterion} must be an integer from 1 to 5")
        clean[label] = {criterion: candidate_scores[criterion] for criterion in CRITERIA}
    winner = data.get("winner")
    if winner not in CANDIDATES:
        raise JudgeError(f"winner must be A or B, got {winner!r}")
    reason = data.get("reason")
    if not isinstance(reason, str) or not reason.strip():
        raise JudgeError("reason must be a non-empty string")
    return clean, winner, " ".join(reason.split())


# --------------------------------------------------------------------------
# Mock judge
# --------------------------------------------------------------------------


def _clamp(value):
    return max(1, min(5, int(round(value))))


def _max_depth(node, depth=0):
    nesting = (ast.For, ast.While, ast.If, ast.With, ast.Try)
    deepest = depth
    for child in ast.iter_child_nodes(node):
        child_depth = depth + 1 if isinstance(child, nesting) else depth
        deepest = max(deepest, _max_depth(child, child_depth))
    return deepest


def code_features(source):
    """Cheap static signals used by the mock judge."""
    lines = source.splitlines()
    features = {
        "parses": True,
        "max_line": max((len(line) for line in lines), default=0),
        "doctests": len(re.findall(r"^\s*>>> ", source, re.MULTILINE)),
        "doctest_errors": source.count("Traceback (most recent call last)"),
        "compound_lines": sum(
            1 for line in lines if ";" in line or re.match(r"\s*(if|for|while)\b.*:\s*\S", line)
        ),
        "docstrings": 0,
        "short_names": 0,
        "names": 0,
        "guards": 0,
        "depth": 0,
    }
    try:
        tree = ast.parse(source)
    except SyntaxError:
        features["parses"] = False
        return features

    names = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.FunctionDef, ast.ClassDef)):
            if ast.get_docstring(node):
                features["docstrings"] += 1
        if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store):
            names.add(node.id)
        elif isinstance(node, ast.arg) and node.arg != "self":
            names.add(node.arg)
        if isinstance(node, (ast.Raise, ast.Try)):
            features["guards"] += 1
        elif isinstance(node, ast.If):
            test = node.test
            if isinstance(test, ast.UnaryOp) and isinstance(test.op, ast.Not):
                features["guards"] += 1
            elif isinstance(test, ast.Compare) and any(
                isinstance(c, ast.Constant) and c.value in (0, 1, None, "", -1)
                for c in [test.left, *test.comparators]
            ):
                features["guards"] += 1
        elif isinstance(node, ast.Call) and getattr(node.func, "id", "") == "isinstance":
            features["guards"] += 1
    features["names"] = len(names)
    features["short_names"] = sum(1 for name in names if len(name) == 1)
    features["depth"] = _max_depth(tree)
    return features


def heuristic_scores(source):
    """Score one candidate on the four rubric criteria from static signals."""
    f = code_features(source)
    if not f["parses"]:
        return {criterion: 1 for criterion in CRITERIA}

    readability = 3
    readability += 1 if f["docstrings"] else -1
    if f["names"] and f["short_names"] / f["names"] > 0.4:
        readability -= 1
    elif f["max_line"] <= 88:
        readability += 1
    if f["max_line"] > 100 or f["compound_lines"]:
        readability -= 1
    if f["depth"] > 3:
        readability -= 1

    edge = 2 + f["guards"] + (1 if f["doctest_errors"] else 0)

    if f["doctests"] == 0:
        tests = 1
    else:
        tests = 1 + min(f["doctests"], 3) + (1 if f["doctest_errors"] or f["doctests"] >= 5 else 0)

    # Without running anything, guess correctness from how careful the code looks.
    correctness = 3 + (0.5 if f["guards"] else -0.5) + (0.5 if f["doctests"] >= 3 else 0)
    correctness += 0.5 if f["docstrings"] else -0.5

    return {
        "correctness": _clamp(correctness),
        "readability": _clamp(readability),
        "edge_case_handling": _clamp(edge),
        "test_quality": _clamp(tests),
    }


def weighted_total(scores):
    return sum(scores[criterion] * WEIGHTS[criterion] for criterion in CRITERIA)


class MockJudge:
    """Offline judge based on static heuristics. Deterministic."""

    name = "mock"

    def judge(self, task):
        scores = {label: heuristic_scores(task.candidates[label]) for label in CANDIDATES}
        totals = {label: weighted_total(scores[label]) for label in CANDIDATES}
        if totals["A"] != totals["B"]:
            winner = max(CANDIDATES, key=lambda label: totals[label])
        else:
            # Tie: prefer the shorter solution, then A.
            lengths = {label: len(task.candidates[label].splitlines()) for label in CANDIDATES}
            winner = "B" if lengths["B"] < lengths["A"] else "A"
        loser = "B" if winner == "A" else "A"
        gaps = {c: scores[winner][c] - scores[loser][c] for c in CRITERIA}
        best = max(CRITERIA, key=lambda c: gaps[c])
        if gaps[best] > 0:
            reason = (
                f"Candidate {winner} scores higher on {best.replace('_', ' ')} "
                f"({scores[winner][best]} vs {scores[loser][best]}) with a weighted total of "
                f"{totals[winner]} against {totals[loser]}."
            )
        else:
            reason = (
                f"Both candidates score {totals[winner]} overall, so the shorter "
                f"solution, candidate {winner}, is preferred."
            )
        return Verdict(task.task_id, scores, winner, reason, self.name)


# --------------------------------------------------------------------------
# LLM judge
# --------------------------------------------------------------------------

SYSTEM_PROMPT = """You are reviewing two candidate solutions to a small Python task.

Score each candidate from 1 to 5 on every criterion in the rubric below, then
pick the candidate a careful reviewer would merge. You only have the source
code, so reason about what the code actually does on the inputs the task
describes, including boundary and invalid input, rather than trusting
docstrings or how tidy it looks.

<rubric>
{rubric}
</rubric>

Reply with a single JSON object and nothing else, in exactly this shape:

{{"scores": {{"A": {{"correctness": 1, "readability": 1, "edge_case_handling": 1, "test_quality": 1}},
            "B": {{"correctness": 1, "readability": 1, "edge_case_handling": 1, "test_quality": 1}}}},
 "winner": "A",
 "reason": "one sentence naming the deciding difference"}}

Every score is an integer from 1 to 5 and "winner" is "A" or "B"."""

USER_PROMPT = """<task>
{prompt}
</task>

<candidate_a>
{a}
</candidate_a>

<candidate_b>
{b}
</candidate_b>"""


def build_messages(task, rubric):
    """Return ``(system, messages)`` for one task."""
    system = SYSTEM_PROMPT.format(rubric=rubric.strip())
    user = USER_PROMPT.format(
        prompt=task.prompt.strip(),
        a=task.candidates["A"].rstrip(),
        b=task.candidates["B"].rstrip(),
    )
    return system, [{"role": "user", "content": user}]


def extract_json(text):
    """Parse the JSON object in a model reply, tolerating code fences around it."""
    start, end = text.find("{"), text.rfind("}")
    if start == -1 or end <= start:
        raise JudgeError("response did not contain a JSON object")
    try:
        return json.loads(text[start : end + 1])
    except json.JSONDecodeError as error:
        raise JudgeError("response was not valid JSON") from error


class LLMJudge:
    """Judge backed by the Anthropic Messages API."""

    name = "llm"

    def __init__(self, client=None, model=None, rubric=None):
        self.model = model or os.environ.get(MODEL_ENV)
        if not self.model:
            raise JudgeError(f"{MODEL_ENV} is not set; it must name the model to judge with")
        self.rubric = rubric if rubric is not None else RUBRIC_PATH.read_text()
        if client is None:
            api_key = os.environ.get(API_KEY_ENV)
            if not api_key:
                raise JudgeError(f"{API_KEY_ENV} is not set; use the mock judge instead")
            import anthropic

            client = anthropic.Anthropic(api_key=api_key)
        self.client = client

    def judge(self, task):
        import anthropic

        system, messages = build_messages(task, self.rubric)
        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=MAX_TOKENS,
                system=system,
                messages=messages,
            )
        except anthropic.RateLimitError as error:
            raise JudgeError(f"{task.task_id}: rate limited after retries: {error}") from error
        except anthropic.APIStatusError as error:
            raise JudgeError(
                f"{task.task_id}: API returned {error.status_code}: {error.message}"
            ) from error
        except anthropic.APIConnectionError as error:
            raise JudgeError(f"{task.task_id}: could not reach the API: {error}") from error

        if response.stop_reason != "end_turn":
            raise JudgeError(f"{task.task_id}: response ended with {response.stop_reason!r}")
        text = next((block.text for block in response.content if block.type == "text"), None)
        if text is None:
            raise JudgeError(f"{task.task_id}: response had no text block")
        try:
            scores, winner, reason = validate_verdict(extract_json(text))
        except JudgeError as error:
            raise JudgeError(f"{task.task_id}: {error}") from error
        return Verdict(task.task_id, scores, winner, reason, self.name)


def get_judge(kind="auto"):
    """Build a judge. ``auto`` uses the LLM judge when an API key is present."""
    if kind == "auto":
        kind = "llm" if os.environ.get(API_KEY_ENV) else "mock"
    if kind == "mock":
        return MockJudge()
    if kind == "llm":
        return LLMJudge()
    raise ValueError(f"unknown judge: {kind!r}")
