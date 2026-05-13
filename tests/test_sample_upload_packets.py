from pathlib import Path

from vendor_agent.pipeline import run_case
from vendor_agent.uploads import UploadedArtifact, stage_uploaded_case


PACKET_ROOT = Path("data/sample-upload-packets")
ZIP_ROOT = PACKET_ROOT / "zips"
PACKAGE_ROOT = Path("data/source-package/Candidate_package")


def test_sample_low_risk_packet_runs_as_ready_low_risk(tmp_path):
    uploaded_case = stage_zip("valid_low_risk_ops_complete.zip", tmp_path)

    assert uploaded_case.is_ready
    assert {match.role for match in uploaded_case.optional_matches} >= {
        "tax_form",
        "vendor_setup_form",
    }

    packet = run_case(uploaded_case.case_dir)

    assert packet.facts.vendor_name == "Workspace Depot"
    assert packet.status == "ready_low_risk"
    assert not packet.missing_information


def test_sample_high_risk_support_packet_resolves_document_requests(tmp_path):
    uploaded_case = stage_zip("high_risk_ai_with_support_artifacts.zip", tmp_path)

    assert uploaded_case.is_ready
    assert {match.role for match in uploaded_case.optional_matches} >= {
        "data_processing_agreement",
        "soc2_type2",
        "ai_training_opt_out",
        "incident_response_summary",
    }

    packet = run_case(uploaded_case.case_dir)
    missing = {item.item for item in packet.missing_information}

    assert packet.facts.vendor_name == "TalentPulse AI"
    assert packet.status == "blocked"
    assert "SOC 2 Type II report or equivalent security attestation" not in missing
    assert "Data Processing Agreement" not in missing
    assert "AI training opt-out confirmation or Enterprise Control package" not in missing
    assert "Incident response and breach notification summary" not in missing
    assert packet.facts.budget.status == "insufficient"


def test_sample_prompt_injection_packet_preserves_human_gate(tmp_path):
    uploaded_case = stage_zip("guardrail_prompt_injection_email.zip", tmp_path)

    assert uploaded_case.is_ready
    packet = run_case(uploaded_case.case_dir)

    assert packet.status == "blocked"
    assert "Approve vendor" in packet.approval_route.prohibited_actions
    assert all(draft.requires_human_approval for draft in packet.drafts)


def test_sample_policy_doc_decoy_packet_is_incomplete(tmp_path):
    uploaded_case = stage_zip("guardrail_policy_doc_decoy_incomplete.zip", tmp_path)

    assert not uploaded_case.is_ready
    assert "security_questionnaire" in uploaded_case.missing_roles
    assert any("data_handling_policy.md" in name for name in uploaded_case.unmatched_files)


def test_sample_mixed_vendor_packet_is_blocked(tmp_path):
    uploaded_case = stage_zip("invalid_mixed_vendor_case_prefixes.zip", tmp_path)

    assert not uploaded_case.is_ready
    assert uploaded_case.blocking_errors
    assert "multiple vendor cases" in uploaded_case.blocking_errors[0]


def test_sample_bad_quote_packet_is_incomplete(tmp_path):
    uploaded_case = stage_zip("invalid_bad_quote_schema.zip", tmp_path)

    assert not uploaded_case.is_ready
    assert "quote" in uploaded_case.missing_roles


def stage_zip(zip_name: str, tmp_path):
    return stage_uploaded_case(
        [UploadedArtifact(name=zip_name, content=(ZIP_ROOT / zip_name).read_bytes())],
        tmp_path,
        template_package_root=PACKAGE_ROOT,
    )
