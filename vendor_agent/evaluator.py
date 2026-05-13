"""Regression eval harness for deterministic triage cases."""

import json
from pathlib import Path
from typing import Dict, List

from .pipeline import run_case


DEFAULT_CASES_ROOT = Path("data/source-package/Candidate_package/cases")
DEFAULT_BASELINE = Path("evals/seed-cases.json")
DEFAULT_REPORT = Path("evals/reports/eval_report.json")


def run_eval(
    cases_root: Path = DEFAULT_CASES_ROOT,
    baseline_path: Path = DEFAULT_BASELINE,
    report_path: Path = DEFAULT_REPORT,
) -> Dict[str, object]:
    baseline = json.loads(Path(baseline_path).read_text(encoding="utf-8"))
    case_results = []
    for case in baseline["cases"]:
        case_id = case["case_id"]
        packet = run_case(Path(cases_root) / case_id)
        failures = _evaluate_case(packet, case["expected"])
        case_results.append(
            {
                "case_id": case_id,
                "passed": not failures,
                "failures": failures,
                "observed": {
                    "status": packet.status,
                    "approval_status": packet.approval_route.status,
                    "risk_tier": packet.facts.risk.tier,
                    "budget_status": packet.facts.budget.status,
                    "duplicate_vendor_matched": packet.facts.duplicate_vendor.matched,
                    "required_reviewers": packet.approval_route.required_reviewers,
                    "missing_information": [item.item for item in packet.missing_information],
                    "finding_count": len(packet.findings),
                    "evidence_count": len(packet.evidence),
                    "trace_count": len(packet.trace),
                },
            }
        )

    report = {
        "passed": all(result["passed"] for result in case_results),
        "case_count": len(case_results),
        "passed_count": len([result for result in case_results if result["passed"]]),
        "failed_count": len([result for result in case_results if not result["passed"]]),
        "cases": case_results,
    }
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return report


def _evaluate_case(packet, expected: Dict[str, object]) -> List[str]:
    failures: List[str] = []
    _expect_equal(failures, "status", packet.status, expected["status"])
    _expect_equal(
        failures,
        "approval_status",
        packet.approval_route.status,
        expected["approval_status"],
    )
    _expect_equal(failures, "risk_tier", packet.facts.risk.tier, expected["risk_tier"])
    _expect_equal(
        failures,
        "budget_status",
        packet.facts.budget.status,
        expected["budget_status"],
    )
    _expect_equal(
        failures,
        "duplicate_vendor_matched",
        packet.facts.duplicate_vendor.matched,
        expected["duplicate_vendor_matched"],
    )

    reviewers = packet.approval_route.required_reviewers
    for reviewer in expected.get("required_reviewers_include", []):
        if reviewer not in reviewers:
            failures.append("expected reviewer missing: %s" % reviewer)
    for reviewer in expected.get("required_reviewers_exclude", []):
        if reviewer in reviewers:
            failures.append("unexpected reviewer present: %s" % reviewer)

    missing_text = " | ".join(item.item for item in packet.missing_information)
    for expected_text in expected.get("missing_contains", []):
        if expected_text.lower() not in missing_text.lower():
            failures.append("missing info text not found: %s" % expected_text)

    finding_text = " | ".join(
        "%s %s %s"
        % (finding.trigger, finding.why_it_matters, finding.recommended_action)
        for finding in packet.findings
    )
    for expected_text in expected.get("finding_text_contains", []):
        if expected_text.lower() not in finding_text.lower():
            failures.append("finding text not found: %s" % expected_text)

    evidence_ids = {item.id for item in packet.evidence}
    for finding in packet.findings:
        if not finding.evidence_ids:
            failures.append("finding lacks evidence: %s" % finding.id)
        for evidence_id in finding.evidence_ids:
            if evidence_id not in evidence_ids:
                failures.append("finding has invalid evidence id: %s" % evidence_id)
    for trace_entry in packet.trace:
        if not trace_entry.requirement_ids:
            failures.append("trace entry lacks requirement IDs: %s" % trace_entry.tool_name)
        for evidence_id in trace_entry.evidence_ids:
            if evidence_id not in evidence_ids:
                failures.append("trace has invalid evidence id: %s" % evidence_id)

    if any(action.lower().startswith("approve") for action in packet.approval_route.prohibited_actions) is False:
        failures.append("approval route does not prohibit approving vendor")
    if not all(draft.requires_human_approval for draft in packet.drafts):
        failures.append("one or more drafts do not require human approval")

    return failures


def _expect_equal(failures: List[str], field: str, actual, expected) -> None:
    if actual != expected:
        failures.append("%s expected %r but observed %r" % (field, expected, actual))

