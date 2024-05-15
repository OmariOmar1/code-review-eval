"""Score two candidates against the rubric and pick a winner.

``HeuristicJudge`` works from static analysis of the source only. It is never
shown the test results.
"""

import ast
import re
from dataclasses import dataclass
from pathlib import Path

from .tasks import CANDIDATES

CRITERIA = ("correctness", "readability", "edge_case_handling", "test_quality")
RUBRIC_PATH = Path(__file__).resolve().parent.parent / "RUBRIC.md"

# Correctness counts double when the judge totals its scores.
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
# Heuristic judge
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
    """Cheap static signals used by the judge."""
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


class HeuristicJudge:
    """Judge based on static heuristics. Deterministic."""

    name = "heuristic"

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
