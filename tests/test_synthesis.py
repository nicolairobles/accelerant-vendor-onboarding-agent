from pathlib import Path
from types import SimpleNamespace

from vendor_agent.pipeline import run_case
from vendor_agent.synthesis import (
    SynthesisDraft,
    build_llm_synthesis_payload,
    build_openai_synthesis_bundle,
    build_synthesis_bundle,
)


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
    assert payload["expected_missing_items"] == [
        item.item for item in packet.missing_information
    ]
    assert set(payload["known_evidence_ids"]) == {item.id for item in packet.evidence}
    assert any(
        "vendor_follow_up_draft" in requirement
        for requirement in payload["validation_requirements"]
    )
    assert "raw_documents" not in payload
    assert "allowed_task" in payload
    assert "Do not change status" in payload["allowed_task"]


def test_openai_synthesis_provider_uses_structured_outputs_without_changing_decisions():
    packet = run_case(CASE_DIR)
    fake_client = FakeOpenAIClient(
        SynthesisDraft(
            executive_summary=(
                "TalentPulse AI is blocked for procurement triage. The request is high risk "
                "with five open requests before routing."
            ),
            vendor_follow_up_draft="\n".join(
                ["Draft for human review before any external send:"]
                + ["- %s" % item.item for item in packet.missing_information]
            ),
            internal_note_draft=(
                "Internal routing note: TalentPulse AI is blocked and requires CFO, Legal, "
                "Security, and Executive sponsor review."
            ),
            cited_evidence_ids=packet.missing_information[0].evidence_ids,
        )
    )

    bundle = build_openai_synthesis_bundle(packet, client=fake_client, model="test-model")

    assert bundle.synthesis_mode == "openai_responses_structured_output"
    assert bundle.model_name == "test-model"
    assert bundle.validation_status == "passed"
    assert fake_client.responses.calls[0]["text_format"] is SynthesisDraft
    payload_text = fake_client.responses.calls[0]["input"][1]["content"]
    assert "raw_documents" not in payload_text
    assert "expected_missing_items" in payload_text


def test_openai_provider_failure_falls_back_to_valid_deterministic_synthesis(monkeypatch):
    packet = run_case(CASE_DIR)

    def fail_provider(_packet):
        raise RuntimeError("provider unavailable")

    monkeypatch.setattr("vendor_agent.synthesis.build_openai_synthesis_bundle", fail_provider)
    bundle = build_synthesis_bundle(packet, provider="openai")

    # Provider errors fail closed to the deterministic packet-grounded synthesis
    # rather than exposing invalid model output.
    assert bundle.synthesis_mode == "deterministic_fallback_after_openai_error"
    assert bundle.validation_status.startswith("passed")


class FakeOpenAIClient:
    def __init__(self, parsed):
        self.responses = FakeResponses(parsed)


class FakeResponses:
    def __init__(self, parsed):
        self.parsed = parsed
        self.calls = []

    def parse(self, **kwargs):
        self.calls.append(kwargs)
        return SimpleNamespace(output_parsed=self.parsed)
