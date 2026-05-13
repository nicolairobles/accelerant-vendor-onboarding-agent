import json
import subprocess
import sys

from vendor_agent.evaluator import run_eval
from vendor_agent.pipeline import run_case


CASES_ROOT = "data/source-package/Candidate_package/cases"


def test_all_cases_match_expected_baselines(tmp_path):
    report = run_eval(report_path=tmp_path / "eval_report.json")

    assert report["passed"] is True
    assert report["case_count"] == 3
    assert report["failed_count"] == 0


def test_case_outputs_have_expected_risk_profiles():
    packets = {
        case_id: run_case_path(case_id)
        for case_id in ["case_001", "case_002", "case_003"]
    }

    assert packets["case_001"].facts.risk.tier == "high"
    assert packets["case_001"].facts.duplicate_vendor.matched is True
    assert "CFO" not in packets["case_001"].approval_route.required_reviewers

    assert packets["case_002"].facts.risk.tier == "low"
    assert packets["case_002"].approval_route.required_reviewers == [
        "Business owner",
        "Procurement manager",
    ]
    assert not any(finding.function == "Security" for finding in packets["case_002"].findings)
    assert not any(finding.function == "Legal" for finding in packets["case_002"].findings)

    assert packets["case_003"].facts.risk.tier == "high"
    assert packets["case_003"].facts.budget.status == "insufficient"
    assert "CFO" in packets["case_003"].approval_route.required_reviewers


def test_cli_eval_writes_report(tmp_path):
    report = tmp_path / "eval_report.json"
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "vendor_agent.cli",
            "eval",
            "--cases-root",
            CASES_ROOT,
            "--report",
            str(report),
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    assert "Eval result: passed" in result.stdout
    payload = json.loads(report.read_text(encoding="utf-8"))
    assert payload["passed"] is True
    assert payload["passed_count"] == 3


def run_case_path(case_id):
    from pathlib import Path

    return run_case(Path(CASES_ROOT) / case_id)
