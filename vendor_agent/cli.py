"""Command line interface for deterministic vendor triage."""

import argparse
import json
from pathlib import Path
from typing import List, Optional

from .evaluator import DEFAULT_BASELINE, DEFAULT_CASES_ROOT, DEFAULT_REPORT, run_eval
from .pipeline import run_case


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(prog="vendor_agent")
    subparsers = parser.add_subparsers(dest="command", required=True)

    run_parser = subparsers.add_parser("run", help="Run deterministic triage for a case")
    run_parser.add_argument("--case", required=True, help="Path to case directory")
    run_parser.add_argument("--out", required=True, help="Path to write decision packet JSON")
    run_parser.add_argument(
        "--trace-out",
        help="Optional path to write trace JSON; defaults to <out stem>.trace.json",
    )

    eval_parser = subparsers.add_parser("eval", help="Run deterministic regression evals")
    eval_parser.add_argument(
        "--cases-root",
        default=str(DEFAULT_CASES_ROOT),
        help="Directory containing case_001, case_002, and case_003",
    )
    eval_parser.add_argument(
        "--baseline",
        default=str(DEFAULT_BASELINE),
        help="Path to expected eval baseline JSON",
    )
    eval_parser.add_argument(
        "--report",
        default=str(DEFAULT_REPORT),
        help="Path to write eval report JSON",
    )

    args = parser.parse_args(argv)
    if args.command == "run":
        return _run(args.case, args.out, args.trace_out)
    if args.command == "eval":
        return _eval(args.cases_root, args.baseline, args.report)
    return 1


def _run(case_dir: str, out_path: str, trace_out: Optional[str]) -> int:
    packet = run_case(Path(case_dir))
    out = Path(out_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    payload = packet.model_dump(mode="json")
    out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    trace_path = Path(trace_out) if trace_out else out.with_name(out.stem + ".trace.json")
    trace_payload = [entry.model_dump(mode="json") for entry in packet.trace]
    trace_path.write_text(
        json.dumps(trace_payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print("Wrote decision packet: %s" % out)
    print("Wrote trace: %s" % trace_path)
    print("Status: %s" % packet.status)
    return 0


def _eval(cases_root: str, baseline: str, report: str) -> int:
    eval_report = run_eval(Path(cases_root), Path(baseline), Path(report))
    print("Wrote eval report: %s" % report)
    print(
        "Eval result: %s (%s/%s passed)"
        % (
            "passed" if eval_report["passed"] else "failed",
            eval_report["passed_count"],
            eval_report["case_count"],
        )
    )
    for case in eval_report["cases"]:
        if not case["passed"]:
            print("%s failures:" % case["case_id"])
            for failure in case["failures"]:
                print("- %s" % failure)
    return 0 if eval_report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
