"""Command line entry point: ``python -m code_review_eval``."""

import argparse
import sys
from pathlib import Path

from .analysis import write_report
from .judge import JudgeError, get_judge
from .pipeline import run_judge, run_tests
from .runner import DEFAULT_TIMEOUT, RunnerError


def build_parser():
    parser = argparse.ArgumentParser(
        prog="code_review_eval",
        description="Compare two candidate solutions per task and produce preference data.",
    )
    parser.add_argument("--tasks", default="tasks", help="tasks directory (default: tasks)")
    parser.add_argument(
        "--results", default="results/test_results.json", help="where test results are stored"
    )
    parser.add_argument("--preferences", default="preferences.jsonl", help="judge output file")
    parser.add_argument("--report", default="report.md", help="analysis report file")

    commands = parser.add_subparsers(dest="command", required=True)
    for name, text in (
        ("run-tests", "run every candidate against its tests"),
        ("judge", "score candidates and write preferences"),
        ("analyze", "compare judge picks with test results"),
        ("all", "run-tests, judge and analyze in one go"),
    ):
        sub = commands.add_parser(name, help=text)
        if name in ("run-tests", "all"):
            sub.add_argument("--backend", choices=("docker", "local"), default="docker")
            sub.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT)
            sub.add_argument("--rebuild", action="store_true", help="rebuild the runner image")
        if name in ("judge", "all"):
            sub.add_argument("--judge", choices=("auto", "mock", "llm"), default="auto")
    return parser


def main(argv=None):
    args = build_parser().parse_args(argv)
    try:
        if args.command in ("run-tests", "all"):
            results = run_tests(
                args.tasks, args.results, args.backend, args.timeout, args.rebuild
            )
            passing = sum(1 for result in results if result["passed"])
            print(f"ran {len(results)} candidates ({passing} fully passing) -> {args.results}")
        if args.command in ("judge", "all"):
            judge = get_judge(args.judge)
            rows = run_judge(args.tasks, args.preferences, judge)
            print(f"judged {len(rows)} tasks with the {judge.name} judge -> {args.preferences}")
        if args.command in ("analyze", "all"):
            for path in (args.results, args.preferences):
                if not Path(path).is_file():
                    raise FileNotFoundError(f"{path} not found; run the earlier steps first")
            summary = write_report(args.results, args.preferences, args.report)
            rate = summary["agreement_rate"]
            shown = "n/a" if rate is None else f"{rate:.0%}"
            print(
                f"agreement {summary['agreed']}/{summary['decisive']} ({shown}) -> {args.report}"
            )
    except (RunnerError, JudgeError, FileNotFoundError, ValueError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 1
    return 0
