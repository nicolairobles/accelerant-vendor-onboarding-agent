import json
import html
import shutil
import tempfile
from pathlib import Path

import pandas as pd
import streamlit as st

from vendor_agent.pipeline import run_case
from vendor_agent.uploads import UploadedArtifact, missing_role_labels, stage_uploaded_case


PACKAGE_ROOT = Path("data/source-package/Candidate_package")
CASES_ROOT = Path("data/source-package/Candidate_package/cases")
CASE_OPTIONS = ["case_001", "case_002", "case_003"]


st.set_page_config(
    page_title="Vendor Onboarding Triage",
    page_icon="",
    layout="wide",
)


def main() -> None:
    st.title("Vendor Onboarding Triage")
    st.caption("Evidence-backed procurement review packet")

    with st.sidebar:
        input_mode = st.radio("Input mode", ["Sample case", "Upload package"])
        selected_case = None
        uploaded_files = []
        if input_mode == "Sample case":
            selected_case = st.selectbox("Case", CASE_OPTIONS, index=2)
            run_clicked = st.button("Run triage", type="primary", use_container_width=True)
        else:
            uploaded_files = st.file_uploader(
                "Vendor package files",
                type=["xlsx", "csv", "pdf", "md", "txt", "zip"],
                accept_multiple_files=True,
                help=(
                    "Upload intake workbook, quote CSV, contract PDF, security "
                    "questionnaire, and vendor email. A zip containing those files is also supported."
                ),
            )
            st.caption("Required: intake workbook, quote CSV, contract PDF, security questionnaire, vendor email.")
            st.caption("Uploaded files are staged in temporary storage for this session only.")
            run_clicked = st.button("Run uploaded package", type="primary", use_container_width=True)
        st.divider()
        st.caption("Mode")
        st.write("Deterministic policy workflow")
        st.caption("Human gate")
        st.write("No approvals, sends, spend commitments, or legal acceptance.")

    if input_mode == "Sample case":
        _run_sample_case(selected_case, run_clicked)
    else:
        _run_uploaded_case(uploaded_files, run_clicked)

    packet = st.session_state.get("packet")
    if packet and st.session_state.get("input_mode") == input_mode:
        render_packet(packet)
        if input_mode == "Upload package":
            render_upload_details(st.session_state.get("uploaded_case"))
    elif input_mode == "Upload package":
        render_upload_feedback()
        st.info("Upload a vendor package and run triage to produce a decision packet.")


def _run_sample_case(selected_case: str, run_clicked: bool) -> None:
    context_key = "sample:%s" % selected_case
    if run_clicked or st.session_state.get("packet_context") != context_key:
        with st.status("Running triage", expanded=False) as status:
            packet = run_case(CASES_ROOT / selected_case)
            st.session_state["packet"] = packet
            st.session_state["packet_context"] = context_key
            st.session_state["input_mode"] = "Sample case"
            st.session_state["uploaded_case"] = None
            st.session_state["upload_feedback"] = None
            status.update(label="Triage complete", state="complete")


def _run_uploaded_case(uploaded_files, run_clicked: bool) -> None:
    if not run_clicked:
        return
    if not uploaded_files:
        st.error("Upload the required vendor package files before running triage.")
        return

    _clear_upload_workspace()
    upload_workspace = Path(tempfile.mkdtemp(prefix="accelerant_vendor_upload_"))
    st.session_state["upload_workspace"] = str(upload_workspace)

    with st.status("Preparing uploaded package", expanded=False) as status:
        try:
            uploaded_case = stage_uploaded_case(
                _uploaded_artifacts(uploaded_files),
                upload_workspace,
                template_package_root=PACKAGE_ROOT,
            )
        except Exception as exc:
            st.session_state["packet"] = None
            st.session_state["packet_context"] = "upload:error"
            st.session_state["input_mode"] = "Upload package"
            st.session_state["upload_feedback"] = {
                "error": "Upload package could not be prepared: %s" % exc,
                "warnings": [],
            }
            status.update(label="Upload package could not be prepared", state="error")
            return
        if not uploaded_case.is_ready:
            st.session_state["packet"] = None
            st.session_state["uploaded_case"] = uploaded_case
            st.session_state["packet_context"] = "upload:incomplete"
            st.session_state["input_mode"] = "Upload package"
            st.session_state["upload_feedback"] = {
                "error": "Missing required files: %s."
                % ", ".join(missing_role_labels(uploaded_case.missing_roles)),
                "warnings": (
                    ["Unmatched files: %s." % ", ".join(uploaded_case.unmatched_files)]
                    if uploaded_case.unmatched_files
                    else []
                ),
            }
            status.update(label="Upload package incomplete", state="error")
            return
        status.update(label="Running triage", state="running")
        packet = run_case(uploaded_case.case_dir)
        st.session_state["packet"] = packet
        st.session_state["uploaded_case"] = uploaded_case
        st.session_state["packet_context"] = "upload:%s" % packet.case_id
        st.session_state["input_mode"] = "Upload package"
        st.session_state["upload_feedback"] = None
        status.update(label="Triage complete", state="complete")


def render_packet(packet) -> None:
    status_label = _status_label(packet)
    if packet.status == "blocked":
        st.error("%s - %s" % (status_label, packet.status_reason))
    elif packet.status == "review_required":
        st.warning("%s - %s" % (status_label, packet.status_reason))
    else:
        st.success("%s - %s" % (status_label, packet.status_reason))

    st.caption("Vendor")
    st.subheader(packet.facts.vendor_name)

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("ACV", _money(packet.facts.annual_contract_value))
    col2.metric("TCV", _money(packet.facts.total_contract_value.total_contract_value))
    col3.metric("Budget", packet.facts.budget.status.title())
    col4.metric("Risk", packet.facts.risk.tier.title())

    action_col, route_col = st.columns([1.2, 1])
    with action_col:
        st.subheader("Next Actions")
        actions = _next_actions(packet)
        if actions:
            for action in actions:
                st.checkbox(action, value=False, key="action_%s_%s" % (packet.case_id, action))
        else:
            st.write("No blockers detected.")

    with route_col:
        st.subheader("Required Human Route")
        for index, reviewer in enumerate(packet.approval_route.required_reviewers, start=1):
            st.write("%s. %s" % (index, reviewer))

    st.download_button(
        "Download JSON packet",
        data=json.dumps(packet.model_dump(mode="json"), indent=2, sort_keys=True),
        file_name="%s_decision_packet.json" % packet.case_id,
        mime="application/json",
    )
    st.download_button(
        "Download trace",
        data=json.dumps([entry.model_dump(mode="json") for entry in packet.trace], indent=2, sort_keys=True),
        file_name="%s_trace.json" % packet.case_id,
        mime="application/json",
    )
    st.download_button(
        "Download Markdown brief",
        data=_markdown_brief(packet),
        file_name="%s_brief.md" % packet.case_id,
        mime="text/markdown",
    )

    overview_tab, findings_tab, evidence_tab, drafts_tab, trace_tab = st.tabs(
        ["Overview", "Findings", "Evidence", "Drafts", "Trace"]
    )
    with overview_tab:
        render_overview(packet)
    with findings_tab:
        render_findings(packet)
    with evidence_tab:
        render_evidence(packet)
    with drafts_tab:
        render_drafts(packet)
    with trace_tab:
        render_trace(packet)


def render_upload_details(uploaded_case) -> None:
    if not uploaded_case:
        return
    with st.expander("Uploaded package mapping"):
        if uploaded_case.role_matches:
            rows = [
                {
                    "Role": match.role.replace("_", " ").title(),
                    "Uploaded file": match.uploaded_name,
                    "Staged file": match.staged_name,
                }
                for match in uploaded_case.role_matches
            ]
            st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
        if uploaded_case.warnings:
            for warning in uploaded_case.warnings:
                st.warning(warning)
        if uploaded_case.unmatched_files:
            st.caption("Ignored files: %s" % ", ".join(uploaded_case.unmatched_files))


def render_upload_feedback() -> None:
    feedback = st.session_state.get("upload_feedback")
    if not feedback:
        return
    st.error(feedback["error"])
    for warning in feedback.get("warnings", []):
        st.warning(warning)


def render_overview(packet) -> None:
    st.markdown(_summary_html(packet.summary), unsafe_allow_html=True)

    left, right = st.columns(2)
    with left:
        st.subheader("Commercial")
        commercial = {
            "Requesting team": packet.facts.requesting_team,
            "Business owner": packet.facts.business_owner,
            "Cost center": packet.facts.cost_center,
            "Request type": packet.facts.renewal_or_new_vendor,
            "Term": "%s months" % packet.facts.contract_term_months,
            "Payment terms": packet.facts.payment_terms,
            "One-time fees": _money(packet.facts.quote.one_time_fees),
        }
        st.table(pd.DataFrame(commercial.items(), columns=["Field", "Value"]))

    with right:
        st.subheader("Risk Drivers")
        if packet.facts.risk.reasons:
            for reason in packet.facts.risk.reasons:
                st.write("- %s" % reason)
        else:
            st.write("No elevated risk drivers detected.")

    st.subheader("Missing Information")
    if packet.missing_information:
        st.dataframe(_missing_rows(packet), use_container_width=True, hide_index=True)
    else:
        st.write("No missing information detected.")


def render_findings(packet) -> None:
    rows = [
        {
            "Function": finding.function,
            "Severity": finding.severity,
            "Trigger": finding.trigger,
            "Owner": finding.required_owner,
            "Recommended action": finding.recommended_action,
            "Evidence": len(finding.evidence_ids),
        }
        for finding in packet.findings
    ]
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

    for function in sorted({finding.function for finding in packet.findings}):
        with st.expander(function):
            for finding in [item for item in packet.findings if item.function == function]:
                st.markdown("**%s**" % finding.trigger)
                st.write(finding.why_it_matters)
                st.caption("Owner: %s | Severity: %s" % (finding.required_owner, finding.severity))
                st.caption("Policy: %s" % "; ".join(finding.policy_refs))


def render_evidence(packet) -> None:
    rows = [
        {
            "ID": item.id,
            "Source type": item.source_type,
            "Source file": Path(item.source_file).name,
            "Location": item.location,
            "Parsed value": item.parsed_value or "",
            "Snippet": item.snippet,
        }
        for item in packet.evidence
    ]
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)


def render_drafts(packet) -> None:
    acknowledged = st.checkbox(
        "I understand these are drafts and require human approval before use.",
        value=False,
    )
    for draft in packet.drafts:
        st.subheader("%s draft" % draft.audience.title())
        st.text_input(
            "Subject",
            value=draft.subject,
            key="subject_%s_%s" % (packet.case_id, draft.audience),
        )
        st.text_area(
            "Body",
            value=draft.body,
            height=220,
            key="body_%s_%s" % (packet.case_id, draft.audience),
            disabled=not acknowledged,
        )


def render_trace(packet) -> None:
    rows = [
        {
            "Step": index,
            "Tool": entry.tool_name,
            "Status": entry.status,
            "Duration ms": entry.duration_ms,
            "Requirements": ", ".join(entry.requirement_ids),
            "Evidence IDs": ", ".join(entry.evidence_ids),
        }
        for index, entry in enumerate(packet.trace, start=1)
    ]
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

    with st.expander("Raw trace JSON"):
        st.json([entry.model_dump(mode="json") for entry in packet.trace])


def _status_label(packet) -> str:
    if packet.status == "blocked" and packet.facts.risk.tier == "low":
        return "LOW-RISK SETUP DOCS MISSING"
    if packet.status == "blocked":
        return "BLOCKED"
    if packet.status == "review_required":
        return "READY FOR REVIEW"
    return "READY"


def _next_actions(packet) -> list:
    actions = [item.item for item in packet.missing_information]
    if packet.status != "ready_low_risk":
        actions.extend(
            [
                "Review approval route",
                "Inspect blocker evidence",
            ]
        )
    return actions[:8]


def _missing_rows(packet) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "Item": item.item,
                "Owner": item.owner,
                "Why needed": item.why_needed,
                "Evidence IDs": ", ".join(item.evidence_ids),
            }
            for item in packet.missing_information
        ]
    )


def _money(value: float) -> str:
    return "$%s" % format(value, ",.0f")


def _markdown_brief(packet) -> str:
    missing = "\n".join("- %s (%s)" % (item.item, item.owner) for item in packet.missing_information)
    findings = "\n".join(
        "- [%s] %s: %s" % (finding.severity, finding.function, finding.trigger)
        for finding in packet.findings
    )
    route = "\n".join(
        "%s. %s" % (index, reviewer)
        for index, reviewer in enumerate(packet.approval_route.required_reviewers, start=1)
    )
    return (
        "# %s Vendor Triage Brief\n\n"
        "Status: %s\n\n"
        "Risk: %s\n\n"
        "ACV: %s\n\n"
        "TCV: %s\n\n"
        "## Summary\n\n%s\n\n"
        "## Missing Information\n\n%s\n\n"
        "## Required Human Route\n\n%s\n\n"
        "## Findings\n\n%s\n"
    ) % (
        packet.facts.vendor_name,
        packet.status,
        packet.facts.risk.tier,
        _money(packet.facts.annual_contract_value),
        _money(packet.facts.total_contract_value.total_contract_value),
        packet.summary,
        missing or "None",
        route,
        findings or "None",
    )


def _summary_html(value: str) -> str:
    escaped = html.escape(value).replace("$", "&#36;")
    return '<p class="summary-text">%s</p>' % escaped


def _uploaded_artifacts(uploaded_files) -> list:
    return [
        UploadedArtifact(name=uploaded_file.name, content=uploaded_file.getvalue())
        for uploaded_file in uploaded_files
    ]


def _clear_upload_workspace() -> None:
    workspace = st.session_state.get("upload_workspace")
    if workspace and Path(workspace).exists():
        shutil.rmtree(workspace, ignore_errors=True)


st.markdown(
    """
    <style>
    .summary-text {
        font-size: 1rem;
        line-height: 1.55;
        margin-bottom: 1.25rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


if __name__ == "__main__":
    main()
