from pathlib import Path

from vendor_agent.pipeline import run_case
from vendor_agent.synthesis import build_llm_synthesis_payload


CASE_DIR = Path("data/source-package/Candidate_package/cases/case_003")


def test_reviewer_synthesis_is_packet_grounded_and_validated():
    packet = run_case(CASE_DIR)

    assert packet.synthesis is not None
    assert packet.synthesis.validation_status == "passed"
    assert packet.synthesis.synthesis_mode == "deterministic_packet_synthesis"
    assert packet.status in packet.synthesis.executive_summary
    assert packet.facts.risk.tier in packet.synthesis.executive_summary
    assert "approved to proceed" not in packet.synthesis.executive_summary.lower()
    assert "commit spend" not in packet.synthesis.internal_note_draft.lower()

    evidence_ids = {item.id for item in packet.evidence}
    assert packet.synthesis.cited_evidence_ids
    assert set(packet.synthesis.cited_evidence_ids) <= evidence_ids
    for item in packet.missing_information:
        assert item.item in packet.synthesis.vendor_follow_up_draft


def test_llm_synthesis_payload_uses_structured_packet_not_raw_documents():
    packet = run_case(CASE_DIR)
    payload = build_llm_synthesis_payload(packet)

    assert payload["case_id"] == "case_003"
    assert payload["status"] == packet.status
    assert payload["risk_tier"] == packet.facts.risk.tier
    assert payload["required_reviewers"] == packet.approval_route.required_reviewers
    assert "raw_documents" not in payload
    assert "allowed_task" in payload
    assert "Do not change status" in payload["allowed_task"]
