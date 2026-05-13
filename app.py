import html
import importlib
import json
import shutil
import tempfile
from io import BytesIO
from pathlib import Path

import pandas as pd
import streamlit as st
from openpyxl import Workbook

import vendor_agent.pipeline as pipeline_module
import vendor_agent.policies as policies_module
import vendor_agent.uploads as uploads_module


# Streamlit Community Cloud can hot-reload app.py while keeping previously
# imported project modules alive. Refresh the internal modules so deployed
# upload behavior always matches the checked-out source revision.
policies_module = importlib.reload(policies_module)
uploads_module = importlib.reload(uploads_module)
pipeline_module = importlib.reload(pipeline_module)

run_case = pipeline_module.run_case
UploadedArtifact = uploads_module.UploadedArtifact
missing_role_labels = uploads_module.missing_role_labels
stage_uploaded_case = uploads_module.stage_uploaded_case


PACKAGE_ROOT = Path("data/source-package/Candidate_package")
CASES_ROOT = Path("data/source-package/Candidate_package/cases")
CASE_OPTIONS = ["case_001", "case_002", "case_003"]
CASE_DISPLAY_NAMES = {
    "case_001": "case_001 - Northstar Analytics",
    "case_002": "case_002 - Workspace Depot",
    "case_003": "case_003 - TalentPulse AI",
}


st.set_page_config(
    page_title="Vendor Onboarding Triage",
    page_icon="",
    layout="wide",
)


def main() -> None:
    st.title("Vendor Onboarding Triage")
    st.caption("Procurement case queue and evidence-backed review packets")

    with st.sidebar:
        workspace = st.radio(
            "Workspace",
            ["Dashboard", "Review sample case", "Upload package"],
        )

    if workspace == "Dashboard":
        st.session_state["input_mode"] = "Dashboard"
        render_dashboard()
    elif workspace == "Review sample case":
        selected_label = st.sidebar.selectbox(
            "Case",
            [CASE_DISPLAY_NAMES[case_id] for case_id in CASE_OPTIONS],
            index=2,
        )
        selected_case = selected_label.split(" - ", 1)[0]
        refresh_clicked = st.sidebar.button("Refresh triage", type="primary", use_container_width=True)
        _run_sample_case(selected_case, refresh_clicked)
        packet = st.session_state.get("packet")
        if packet and st.session_state.get("input_mode") == workspace:
            render_packet(packet)
    else:
        uploaded_files = st.sidebar.file_uploader(
            "Vendor package files",
            type=["xlsx", "csv", "pdf", "md", "txt", "zip"],
            accept_multiple_files=True,
            help=(
                "Upload intake workbook, quote CSV, contract PDF, security "
                "questionnaire, vendor email, and optional support artifacts."
            ),
        )
        st.sidebar.caption("Required: intake workbook, quote CSV, contract PDF, security questionnaire, vendor email.")
        st.sidebar.caption("Optional: DPA, SOC 2, subprocessors, tax form, vendor setup form, AI opt-out confirmation.")
        run_clicked = st.sidebar.button("Run uploaded package", type="primary", use_container_width=True)
        _run_uploaded_case(uploaded_files, run_clicked)
        packet = st.session_state.get("packet")
        if packet and st.session_state.get("input_mode") == workspace:
            render_packet(packet)
            render_upload_details(st.session_state.get("uploaded_case"))
        else:
            render_upload_feedback()
            render_upload_landing()


@st.cache_data(show_spinner=False)
def _run_sample_case_cached(case_id: str):
    return run_case(CASES_ROOT / case_id)


@st.cache_data(show_spinner=False)
def _sample_packets():
    return {case_id: run_case(CASES_ROOT / case_id) for case_id in CASE_OPTIONS}


def render_dashboard() -> None:
    packets = _sample_packets()
    rows = [_case_queue_row(case_id, packet) for case_id, packet in packets.items()]
    blocked_count = len([packet for packet in packets.values() if packet.status == "blocked"])
    high_risk_count = len([packet for packet in packets.values() if packet.facts.risk.tier == "high"])
    missing_count = sum(len(packet.missing_information) for packet in packets.values())

    st.subheader("Vendor Case Queue")
    metric_cols = st.columns(4)
    metric_cols[0].metric("Cases", len(packets))
    metric_cols[1].metric("Blocked", blocked_count)
    metric_cols[2].metric("High Risk", high_risk_count)
    metric_cols[3].metric("Open Requests", missing_count)
    st.caption("Open Requests is queue-wide across all sample cases, not an additional case count.")

    st.dataframe(
        pd.DataFrame(rows),
        use_container_width=True,
        hide_index=True,
        column_config={
            "ACV": st.column_config.NumberColumn("ACV", format="$%d"),
            "TCV": st.column_config.NumberColumn("TCV", format="$%d"),
            "Missing": st.column_config.NumberColumn("Missing", format="%d"),
            "Blockers": st.column_config.NumberColumn("Blockers", format="%d"),
        },
    )

    st.subheader("Queue Priorities")
    for packet in sorted(
        packets.values(),
        key=lambda item: (
            item.status != "blocked",
            item.facts.risk.tier != "high",
            -len(item.missing_information),
        ),
    ):
        top_action = _primary_next_action(packet)
        st.write(
            "**%s**: %s. Next: %s."
            % (packet.facts.vendor_name, _status_label(packet), top_action)
        )


def _run_sample_case(selected_case: str, run_clicked: bool) -> None:
    context_key = "sample:%s" % selected_case
    if run_clicked or st.session_state.get("packet_context") != context_key:
        with st.status("Running triage", expanded=False) as status:
            packet = _run_sample_case_cached(selected_case)
            st.session_state["packet"] = packet
            st.session_state["packet_context"] = context_key
            st.session_state["input_mode"] = "Review sample case"
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
            errors = list(uploaded_case.blocking_errors)
            if uploaded_case.missing_roles:
                errors.append(
                    "Missing required files: %s."
                    % ", ".join(missing_role_labels(uploaded_case.missing_roles))
                )
            st.session_state["upload_feedback"] = {
                "error": " ".join(errors) or "Upload package is not complete enough for triage.",
                "warnings": (
                    ["Unmatched files: %s." % ", ".join(uploaded_case.unmatched_files)]
                    if uploaded_case.unmatched_files
                    else []
                )
                + uploaded_case.warnings,
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
        render_required_follow_up(packet)

    with route_col:
        render_human_route(packet)

    render_workflow_progress(packet)
    render_exports(packet)

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


def render_workflow_progress(packet) -> None:
    trace_tools = {entry.tool_name for entry in packet.trace}
    rows = [
        _workflow_row(
            "Parse and extract inputs",
            [
                "parse_intake_workbook",
                "parse_vendor_email",
                "parse_quote_csv",
                "parse_security_questionnaire",
                "parse_contract_pdf",
            ],
            trace_tools,
            "Required source files parsed into evidence-backed facts.",
        ),
        _workflow_row(
            "Validate package",
            ["parse_case_inventory", "detect_missing_information"],
            trace_tools,
            _package_validation_note(packet),
        ),
        _workflow_row(
            "Normalize case facts",
            ["classify_data_sensitivity"],
            trace_tools,
            "%s, %s ACV, %s risk."
            % (packet.facts.vendor_name, _money(packet.facts.annual_contract_value), packet.facts.risk.tier),
        ),
        _workflow_row(
            "Run deterministic helper tools",
            ["lookup_budget", "check_existing_vendor", "calculate_total_contract_value"],
            trace_tools,
            "Budget, duplicate vendor, and total contract value checks completed.",
        ),
        _workflow_row(
            "Determine approvals and risk tier",
            ["run_policy_checks", "determine_required_approvals"],
            trace_tools,
            "%s reviewer route." % len(packet.approval_route.required_reviewers),
        ),
        _workflow_row(
            "Prepare outputs",
            ["draft_human_review_messages", "prepare_reviewer_synthesis"],
            trace_tools,
            "Decision packet, reviewer brief, drafts, trace, and workbook exports are available.",
        ),
        {
            "Stage": "Human approval gate",
            "Status": "Required",
            "Function calls": "human_review",
            "Result": "Procurement owner reviews, edits, approves, or rejects.",
        },
    ]
    workflow_df = pd.DataFrame(rows)
    st.subheader("Triage Workflow")
    st.dataframe(
        workflow_df[["Stage", "Status", "Result"]],
        use_container_width=True,
        hide_index=True,
    )
    with st.expander("Function calls captured in trace"):
        st.dataframe(
            workflow_df[["Stage", "Function calls"]],
            use_container_width=True,
            hide_index=True,
        )


def render_required_follow_up(packet) -> None:
    st.subheader("Required Follow-up")
    rows = _review_action_rows(packet)
    if not rows:
        st.success("No missing information or blocking follow-up detected.")
        return
    for index, row in enumerate(rows, start=1):
        st.markdown("**%s. %s**" % (index, row["Action"]))
        st.caption("Owner: %s | Evidence: %s" % (row["Owner"], row["Evidence"] or "n/a"))
        st.write(row["Why"])


def render_human_route(packet) -> None:
    st.subheader("Human Review Route")
    st.caption("Routing recommendation only. No approval, spend commitment, or external send has occurred.")
    for index, reviewer in enumerate(packet.approval_route.required_reviewers, start=1):
        st.write("%s. %s" % (index, reviewer))
    with st.expander("Guardrails enforced"):
        for action in packet.approval_route.prohibited_actions:
            st.write("- %s" % action)


def render_exports(packet) -> None:
    with st.expander("Export decision packet"):
        cols = st.columns(4)
        cols[0].download_button(
            "JSON packet",
            data=json.dumps(packet.model_dump(mode="json"), indent=2, sort_keys=True),
            file_name="%s_decision_packet.json" % packet.case_id,
            mime="application/json",
            use_container_width=True,
        )
        cols[1].download_button(
            "Trace",
            data=json.dumps([entry.model_dump(mode="json") for entry in packet.trace], indent=2, sort_keys=True),
            file_name="%s_trace.json" % packet.case_id,
            mime="application/json",
            use_container_width=True,
        )
        cols[2].download_button(
            "Markdown brief",
            data=_markdown_brief(packet),
            file_name="%s_brief.md" % packet.case_id,
            mime="text/markdown",
            use_container_width=True,
        )
        cols[3].download_button(
            "Workbook",
            data=_triage_workbook_bytes(packet),
            file_name="%s_triage_workbook.xlsx" % packet.case_id,
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
        )


def render_upload_details(uploaded_case) -> None:
    if not uploaded_case:
        return
    with st.expander("Uploaded package mapping"):
        role_matches = getattr(uploaded_case, "role_matches", [])
        optional_matches = getattr(uploaded_case, "optional_matches", [])
        warnings = getattr(uploaded_case, "warnings", [])
        unmatched_files = getattr(uploaded_case, "unmatched_files", [])
        if role_matches:
            rows = [
                {
                    "Role": match.role.replace("_", " ").title(),
                    "Uploaded file": match.uploaded_name,
                    "Staged file": match.staged_name,
                }
                for match in role_matches
            ]
            st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
        if optional_matches:
            st.caption("Support artifacts")
            support_rows = [
                {
                    "Artifact": _artifact_label(match.role),
                    "Uploaded file": match.uploaded_name,
                    "Staged file": match.staged_name,
                }
                for match in optional_matches
            ]
            st.dataframe(pd.DataFrame(support_rows), use_container_width=True, hide_index=True)
        if warnings:
            for warning in warnings:
                st.warning(warning)
        if unmatched_files:
            st.caption("Ignored files: %s" % ", ".join(unmatched_files))


def render_upload_feedback() -> None:
    feedback = st.session_state.get("upload_feedback")
    if not feedback:
        return
    st.error(feedback["error"])
    for warning in feedback.get("warnings", []):
        st.warning(warning)


def render_upload_landing() -> None:
    st.subheader("New Vendor Package")
    st.info("Upload a vendor package and run triage to produce a decision packet.")
    expected = pd.DataFrame(
        [
            {"Role": "Intake", "Required": True, "Accepted": ".xlsx"},
            {"Role": "Quote or order form", "Required": True, "Accepted": ".csv"},
            {"Role": "Contract excerpt", "Required": True, "Accepted": ".pdf"},
            {"Role": "Security questionnaire", "Required": True, "Accepted": ".md"},
            {"Role": "Vendor email", "Required": True, "Accepted": ".txt"},
            {"Role": "Support artifacts", "Required": False, "Accepted": ".pdf, .md, .txt"},
        ]
    )
    st.dataframe(expected, use_container_width=True, hide_index=True)


def render_overview(packet) -> None:
    render_reviewer_brief(packet)

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


def render_reviewer_brief(packet) -> None:
    st.subheader("Reviewer Brief")
    synthesis = getattr(packet, "synthesis", None)
    if not synthesis:
        st.markdown(_summary_html(packet.summary), unsafe_allow_html=True)
        return
    st.markdown(_summary_html(synthesis.executive_summary), unsafe_allow_html=True)
    st.caption(
        "Built from the validated decision packet. Policy status, risk, budget, and routing remain deterministic."
    )
    st.caption("Synthesis source: %s" % synthesis.model_name)
    with st.expander("Synthesis validation"):
        st.write("Status: %s" % synthesis.validation_status)
        st.write("Source: structured decision packet only")
        st.write("Evidence cited: %s" % (", ".join(synthesis.cited_evidence_ids) or "n/a"))
        if synthesis.validation_errors:
            for error in synthesis.validation_errors:
                st.warning(error)


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
    findings_df = pd.DataFrame(rows)
    blocker_rows = findings_df[findings_df["Severity"] == "blocker"] if not findings_df.empty else findings_df
    if not blocker_rows.empty:
        st.subheader("Blocking Issues")
        st.dataframe(
            blocker_rows[["Function", "Trigger", "Owner", "Recommended action", "Evidence"]],
            use_container_width=True,
            hide_index=True,
        )

    st.subheader("All Findings")
    st.dataframe(findings_df, use_container_width=True, hide_index=True)

    with st.expander("Detailed policy rationale"):
        for function in sorted({finding.function for finding in packet.findings}):
            st.markdown("**%s**" % function)
            for finding in [item for item in packet.findings if item.function == function]:
                st.markdown("- **%s**" % finding.trigger)
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
            disabled=not acknowledged,
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


def _case_queue_row(case_id: str, packet) -> dict:
    blockers = len([finding for finding in packet.findings if finding.severity == "blocker"])
    return {
        "Case": case_id,
        "Vendor": packet.facts.vendor_name,
        "Status": _status_label(packet),
        "Risk": packet.facts.risk.tier.title(),
        "ACV": packet.facts.annual_contract_value,
        "TCV": packet.facts.total_contract_value.total_contract_value,
        "Budget": packet.facts.budget.status.title(),
        "Missing": len(packet.missing_information),
        "Blockers": blockers,
        "Next owner": _next_owner(packet),
    }


def _next_owner(packet) -> str:
    if packet.missing_information:
        return packet.missing_information[0].owner
    if packet.approval_route.required_reviewers:
        return packet.approval_route.required_reviewers[-1]
    return "Procurement owner"


def _workflow_row(stage: str, tools: list, trace_tools: set, outcome: str) -> dict:
    completed = [tool for tool in tools if tool in trace_tools]
    status = "Complete" if len(completed) == len(tools) else "Pending"
    return {
        "Stage": stage,
        "Status": status,
        "Function calls": ", ".join(tools),
        "Result": outcome,
    }


def _package_validation_note(packet) -> str:
    if packet.missing_information:
        return "%s open request(s); not complete enough for approval readiness." % len(packet.missing_information)
    return "Complete enough for triage."


def _artifact_label(key: str) -> str:
    labels = {
        "soc2_type2": "SOC 2 Type II",
        "data_processing_agreement": "Data Processing Agreement",
        "subprocessor_list": "Subprocessor list",
        "tax_form": "Tax form",
        "vendor_setup_form": "Vendor setup form",
        "ai_training_opt_out": "AI training opt-out",
        "incident_response_summary": "Incident response summary",
        "statement_of_work": "Statement of work",
    }
    return labels.get(key, key.replace("_", " ").title())


def _triage_workbook_bytes(packet) -> bytes:
    wb = Workbook()
    summary = wb.active
    summary.title = "Summary"
    _append_rows(
        summary,
        [
            ("Case ID", packet.case_id),
            ("Vendor", packet.facts.vendor_name),
            ("Status", packet.status),
            ("Status reason", packet.status_reason),
            ("Risk", packet.facts.risk.tier),
            ("ACV", packet.facts.annual_contract_value),
            ("TCV", packet.facts.total_contract_value.total_contract_value),
            ("Budget", packet.facts.budget.status),
            ("Structured summary", packet.summary),
            ("Reviewer brief", _reviewer_summary(packet)),
        ],
    )

    missing = wb.create_sheet("Missing Info")
    missing.append(["Item", "Owner", "Why needed", "Evidence IDs"])
    for item in packet.missing_information:
        missing.append([item.item, item.owner, item.why_needed, ", ".join(item.evidence_ids)])

    findings = wb.create_sheet("Findings")
    findings.append(["ID", "Function", "Severity", "Trigger", "Owner", "Action", "Evidence IDs", "Policy refs"])
    for finding in packet.findings:
        findings.append(
            [
                finding.id,
                finding.function,
                finding.severity,
                finding.trigger,
                finding.required_owner,
                finding.recommended_action,
                ", ".join(finding.evidence_ids),
                "; ".join(finding.policy_refs),
            ]
        )

    route = wb.create_sheet("Approval Route")
    route.append(["Order", "Reviewer"])
    for index, reviewer in enumerate(packet.approval_route.required_reviewers, start=1):
        route.append([index, reviewer])
    route.append([])
    route.append(["Prohibited action"])
    for action in packet.approval_route.prohibited_actions:
        route.append([action])

    trace = wb.create_sheet("Trace")
    trace.append(["Step", "Tool", "Status", "Duration ms", "Requirements", "Evidence IDs"])
    for index, entry in enumerate(packet.trace, start=1):
        trace.append(
            [
                index,
                entry.tool_name,
                entry.status,
                entry.duration_ms,
                ", ".join(entry.requirement_ids),
                ", ".join(entry.evidence_ids),
            ]
        )

    if getattr(packet, "synthesis", None):
        synthesis = wb.create_sheet("Synthesis")
        _append_rows(
            synthesis,
            [
                ("Mode", packet.synthesis.synthesis_mode),
                ("Model", packet.synthesis.model_name),
                ("Validation", packet.synthesis.validation_status),
                ("Executive summary", packet.synthesis.executive_summary),
                ("Vendor follow-up draft", packet.synthesis.vendor_follow_up_draft),
                ("Internal note draft", packet.synthesis.internal_note_draft),
                ("Evidence IDs", ", ".join(packet.synthesis.cited_evidence_ids)),
                ("Validation errors", "; ".join(packet.synthesis.validation_errors)),
            ],
        )

    for ws in wb.worksheets:
        for column_cells in ws.columns:
            width = min(max(len(str(cell.value or "")) for cell in column_cells) + 2, 60)
            ws.column_dimensions[column_cells[0].column_letter].width = width

    buffer = BytesIO()
    wb.save(buffer)
    return buffer.getvalue()


def _append_rows(sheet, rows) -> None:
    for label, value in rows:
        sheet.append([label, value])


def _status_label(packet) -> str:
    if packet.status == "blocked" and packet.facts.risk.tier == "low":
        return "LOW-RISK SETUP DOCS MISSING"
    if packet.status == "blocked":
        return "BLOCKED"
    if packet.status == "review_required":
        return "READY FOR REVIEW"
    return "READY"


def _primary_next_action(packet) -> str:
    rows = _review_action_rows(packet)
    if rows:
        return rows[0]["Action"]
    return "Route decision packet to required reviewers"


def _review_action_rows(packet) -> list:
    rows = []
    seen = set()

    for item in packet.missing_information:
        key = ("missing", item.item, item.owner)
        if key in seen:
            continue
        seen.add(key)
        rows.append(
            {
                "Action": item.item,
                "Owner": item.owner,
                "Why": item.why_needed,
                "Evidence": ", ".join(item.evidence_ids),
            }
        )

    for finding in packet.findings:
        if finding.severity not in {"blocker", "review_required"}:
            continue
        if packet.missing_information and finding.trigger == "Required onboarding materials are missing.":
            continue
        key = ("finding", finding.recommended_action, finding.required_owner)
        if key in seen:
            continue
        seen.add(key)
        rows.append(
            {
                "Action": finding.recommended_action,
                "Owner": finding.required_owner,
                "Why": finding.trigger,
                "Evidence": ", ".join(finding.evidence_ids),
            }
        )

    return rows[:8]


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
        "## Reviewer Brief\n\n%s\n\n"
        "## Structured Summary\n\n%s\n\n"
        "## Missing Information\n\n%s\n\n"
        "## Required Human Route\n\n%s\n\n"
        "## Findings\n\n%s\n"
    ) % (
        packet.facts.vendor_name,
        packet.status,
        packet.facts.risk.tier,
        _money(packet.facts.annual_contract_value),
        _money(packet.facts.total_contract_value.total_contract_value),
        _reviewer_summary(packet),
        packet.summary,
        missing or "None",
        route,
        findings or "None",
    )


def _reviewer_summary(packet) -> str:
    synthesis = getattr(packet, "synthesis", None)
    if synthesis and synthesis.validation_status.startswith("passed"):
        return synthesis.executive_summary
    return packet.summary


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
