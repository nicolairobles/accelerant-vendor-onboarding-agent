from streamlit.testing.v1 import AppTest

from app import _markdown_brief
from vendor_agent.pipeline import run_case


def test_streamlit_app_renders_default_case():
    app = AppTest.from_file("app.py")
    app.run(timeout=30)

    assert not app.exception
    assert any("Vendor Onboarding Triage" in item.value for item in app.title)
    assert any("TalentPulse AI" in item.value for item in app.subheader)
    assert any("Required Human Route" in item.value for item in app.subheader)
    assert any("Next Actions" in item.value for item in app.subheader)


def test_streamlit_app_switches_to_low_risk_case():
    app = AppTest.from_file("app.py")
    app.run(timeout=30)
    app.selectbox[0].set_value("case_002")
    app.run(timeout=30)

    assert not app.exception
    assert any("Workspace Depot" in item.value for item in app.markdown)
    assert any("Low" in item.value for item in app.metric)


def test_markdown_brief_contains_review_packet_sections():
    from pathlib import Path

    packet = run_case(Path("data/source-package/Candidate_package/cases/case_003"))
    brief = _markdown_brief(packet)

    assert "# TalentPulse AI Vendor Triage Brief" in brief
    assert "## Missing Information" in brief
    assert "## Required Human Route" in brief
    assert "## Findings" in brief
