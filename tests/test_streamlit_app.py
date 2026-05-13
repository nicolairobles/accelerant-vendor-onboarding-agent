from streamlit.testing.v1 import AppTest

from openpyxl import load_workbook

from app import _markdown_brief, _triage_workbook_bytes
from vendor_agent.pipeline import run_case


def test_streamlit_app_renders_dashboard_homepage():
    app = AppTest.from_file("app.py")
    app.run(timeout=30)

    assert not app.exception
    assert any("Vendor Onboarding Triage" in item.value for item in app.title)
    assert any("Vendor Case Queue" in item.value for item in app.subheader)
    assert any("Queue Priorities" in item.value for item in app.subheader)
    assert any("Open Requests" in item.label for item in app.metric)


def test_streamlit_app_switches_to_low_risk_case():
    app = AppTest.from_file("app.py")
    app.run(timeout=30)
    app.radio[0].set_value("Review sample case")
    app.run(timeout=30)
    app.selectbox[0].set_value("case_002 - Workspace Depot")
    app.run(timeout=30)

    assert not app.exception
    assert any("Workspace Depot" in item.value for item in app.markdown)
    assert any("Low" in item.value for item in app.metric)
    assert any("Required Follow-up" in item.value for item in app.subheader)
    assert any("Human Review Route" in item.value for item in app.subheader)
    assert any("Triage Workflow" in item.value for item in app.subheader)
    assert any("Reviewer Brief" in item.value for item in app.subheader)
    assert not any("Updated tax form" in checkbox.label for checkbox in app.checkbox)


def test_markdown_brief_contains_review_packet_sections():
    from pathlib import Path

    packet = run_case(Path("data/source-package/Candidate_package/cases/case_003"))
    brief = _markdown_brief(packet)

    assert "# TalentPulse AI Vendor Triage Brief" in brief
    assert "## Reviewer Brief" in brief
    assert "## Missing Information" in brief
    assert "## Required Human Route" in brief
    assert "## Findings" in brief


def test_triage_workbook_export_contains_packet_sheets():
    from io import BytesIO
    from pathlib import Path

    packet = run_case(Path("data/source-package/Candidate_package/cases/case_003"))
    workbook_bytes = _triage_workbook_bytes(packet)
    wb = load_workbook(BytesIO(workbook_bytes), read_only=True)

    assert {"Summary", "Missing Info", "Findings", "Approval Route", "Trace", "Synthesis"} <= set(wb.sheetnames)
    assert wb["Summary"]["B2"].value == "TalentPulse AI"
    assert wb["Synthesis"]["B3"].value == "passed"
