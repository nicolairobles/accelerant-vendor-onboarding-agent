import json
import subprocess
import sys
from pathlib import Path

from pydantic import TypeAdapter

from vendor_agent.inventory import CASE_SUFFIXES, POLICY_FILES, TOOL_FILES, inventory_case
from vendor_agent.pipeline import run_case
from vendor_agent.schemas import DecisionPacket


CASE_DIR = "data/source-package/Candidate_package/cases/case_003"


def test_case003_inventory_has_all_expected_files():
    case_id, files, missing = inventory_case_path()

    assert case_id == "case_003"
    assert not missing
    assert files["intake"].name == "case_003_intake.xlsx"
    assert files["quote"].name == "case_003_quote.csv"
    assert files["contract"].name == "case_003_contract.pdf"
    assert files["security_questionnaire"].name == "case_003_security_questionnaire.md"
    assert files["tool_budget_lookup"].name == "budget_lookup.csv"


def test_case003_decision_packet_blocks_high_risk_vendor():
    packet = run_case_path()

    assert packet.status == "blocked"
    assert packet.facts.vendor_name == "TalentPulse AI"
    assert packet.facts.risk.tier == "high"
    assert packet.facts.budget.status == "insufficient"
    assert packet.facts.total_contract_value.total_contract_value == 380000
    assert packet.facts.duplicate_vendor.matched is False
    assert packet.facts.vendor_email.key == "vendor_email"
    assert "TalentPulse can connect to your HRIS" in packet.facts.vendor_email.value
    assert packet.approval_route.status == "blocked_pending_missing_information"
    assert "CFO" in packet.approval_route.required_reviewers
    assert "Executive sponsor" in packet.approval_route.required_reviewers
    assert "Approve vendor" in packet.approval_route.prohibited_actions


def test_case003_missing_info_and_findings_match_expected_blockers():
    packet = run_case_path()
    missing = {item.item for item in packet.missing_information}
    finding_text = " ".join(
        [finding.trigger + " " + finding.why_it_matters for finding in packet.findings]
    )

    assert "SOC 2 Type II report or equivalent security attestation" in missing
    assert "Data Processing Agreement" in missing
    assert "AI training opt-out confirmation or Enterprise Control package" in missing
    assert "SCIM provisioning answer" in missing
    assert "budget" in finding_text.lower()
    assert "Net 90" in finding_text
    assert "employee data" in finding_text
    assert "model or service improvement" in finding_text
    assert "SOC 2 Type II" in finding_text
    assert "prior 6 months" in finding_text


def test_case003_evidence_and_trace_are_populated():
    packet = run_case_path()
    evidence_ids = {item.id for item in packet.evidence}
    trace_tools = {entry.tool_name for entry in packet.trace}

    assert len(packet.evidence) >= 20
    assert all(finding.evidence_ids for finding in packet.findings)
    assert all(evidence_id in evidence_ids for finding in packet.findings for evidence_id in finding.evidence_ids)
    assert packet.facts.vendor_email.evidence_id in evidence_ids
    assert "parse_intake_workbook" in trace_tools
    assert "lookup_budget" in trace_tools
    assert "check_existing_vendor" in trace_tools
    assert "calculate_total_contract_value" in trace_tools
    assert "classify_data_sensitivity" in trace_tools
    assert "run_policy_checks" in trace_tools
    assert "determine_required_approvals" in trace_tools
    assert all(entry.requirement_ids for entry in packet.trace)
    assert all(entry.duration_ms >= 0 for entry in packet.trace)
    evidence_backed_tools = {
        "parse_intake_workbook",
        "parse_quote_csv",
        "parse_contract_pdf",
        "parse_security_questionnaire",
        "parse_vendor_email",
        "lookup_budget",
        "calculate_total_contract_value",
        "classify_data_sensitivity",
        "detect_missing_information",
        "run_policy_checks",
        "determine_required_approvals",
        "draft_human_review_messages",
    }
    for entry in packet.trace:
        if entry.tool_name in evidence_backed_tools:
            assert entry.evidence_ids, entry.tool_name
            assert all(evidence_id in evidence_ids for evidence_id in entry.evidence_ids)


def test_case003_drafts_and_route_preserve_human_gate():
    packet = run_case_path()

    assert packet.status != "approved"
    assert all(draft.requires_human_approval for draft in packet.drafts)
    assert all("requires human" in draft.body.lower() for draft in packet.drafts)
    assert "Approve vendor" in packet.approval_route.prohibited_actions
    assert "Commit spend" in packet.approval_route.prohibited_actions
    assert "Accept contract terms" in packet.approval_route.prohibited_actions
    assert "Send external communications" in packet.approval_route.prohibited_actions


def test_inventory_reports_missing_case_files(tmp_path):
    package = tmp_path / "Candidate_package"
    copied = package / "cases" / "case_003"
    docs = package / "docs"
    tools = package / "tools"
    copied.mkdir(parents=True)
    docs.mkdir()
    tools.mkdir()
    for key, suffix in CASE_SUFFIXES.items():
        if key != "quote":
            (copied / ("case_003_%s" % suffix)).touch()
    for policy_file in POLICY_FILES:
        (docs / policy_file).touch()
    for tool_file in TOOL_FILES:
        (tools / tool_file).touch()

    case_id, files, missing = inventory_case(copied)

    assert case_id == "case_003"
    assert files["quote"].name == "case_003_quote.csv"
    assert any(path.endswith("case_003_quote.csv") for path in missing)


def test_cli_writes_decision_packet_and_trace(tmp_path):
    out = tmp_path / "case_003.json"
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "vendor_agent.cli",
            "run",
            "--case",
            CASE_DIR,
            "--out",
            str(out),
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    assert "Status: blocked" in result.stdout
    assert out.exists()
    assert out.with_name("case_003.trace.json").exists()
    payload = json.loads(out.read_text(encoding="utf-8"))
    TypeAdapter(DecisionPacket).validate_python(payload)
    assert payload["case_id"] == "case_003"
    assert payload["status"] == "blocked"


def inventory_case_path():
    return inventory_case(Path(CASE_DIR))


def run_case_path():
    return run_case(Path(CASE_DIR))
