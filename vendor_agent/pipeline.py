"""End-to-end deterministic triage pipeline."""

from pathlib import Path
from typing import Dict, List

from .inventory import inventory_case
from .parsers import (
    EvidenceStore,
    load_policy_documents,
    parse_contract_pdf,
    parse_intake_workbook,
    parse_quote_csv,
    parse_security_questionnaire,
    parse_vendor_email,
)
from .policies import (
    build_approval_route,
    build_drafts,
    build_findings,
    build_missing_information,
)
from .schemas import CaseFacts, DecisionPacket
from .tools import (
    calculate_total_contract_value,
    check_existing_vendor,
    classify_data_sensitivity,
    lookup_budget,
)
from .tracing import TraceRecorder


def run_case(case_dir: Path) -> DecisionPacket:
    case_dir = Path(case_dir)
    evidence = EvidenceStore()
    trace = TraceRecorder()

    case_id, files, missing_files = trace.run(
        "parse_case_inventory",
        ["REQ-001"],
        {"case_dir": str(case_dir)},
        lambda: inventory_case(case_dir),
        output_summary=lambda result: {
            "case_id": result[0],
            "file_count": len(result[1]),
            "missing_files": result[2],
        },
    )
    if missing_files:
        raise FileNotFoundError("Missing expected files: %s" % ", ".join(missing_files))

    intake_values, document_checklist = trace.run(
        "parse_intake_workbook",
        ["REQ-002", "REQ-003"],
        {"path": str(files["intake"])},
        lambda: parse_intake_workbook(files["intake"], evidence),
        output_summary=lambda result: {
            "field_count": len(result[0]),
            "checklist_count": len(result[1]),
        },
        evidence_id_extractor=lambda result: _unique(
            [item.evidence_id for item in result[0].values()]
            + [item.evidence_id for item in result[1]]
        ),
    )
    quote = trace.run(
        "parse_quote_csv",
        ["REQ-002", "REQ-003"],
        {"path": str(files["quote"])},
        lambda: parse_quote_csv(files["quote"], evidence),
        output_summary=lambda result: {
            "annual_contract_value": result.annual_contract_value,
            "one_time_fees": result.one_time_fees,
            "line_items": len(result.line_items),
        },
        evidence_id_extractor=lambda result: _unique(
            [item.evidence_id for item in result.line_items]
        ),
    )
    contract = trace.run(
        "parse_contract_pdf",
        ["REQ-002", "REQ-003"],
        {"path": str(files["contract"])},
        lambda: parse_contract_pdf(files["contract"], evidence),
        evidence_ids=[],
        output_summary=lambda result: {
            "term_months": result.initial_term_months,
            "payment_terms": result.payment_terms,
            "annual_fees": result.annual_fees,
        },
        evidence_id_extractor=lambda result: result.evidence_ids,
    )
    security = trace.run(
        "parse_security_questionnaire",
        ["REQ-002", "REQ-003"],
        {"path": str(files["security_questionnaire"])},
        lambda: parse_security_questionnaire(files["security_questionnaire"], evidence),
        output_summary=lambda result: {
            "data_categories": len(result.data_processed),
            "integrations": result.integrations,
            "soc2_type2_provided": result.soc2_type2_provided,
            "gaps": result.gaps,
        },
        evidence_id_extractor=lambda result: result.evidence_ids,
    )
    vendor_email = trace.run(
        "parse_vendor_email",
        ["REQ-002", "REQ-003"],
        {"path": str(files["vendor_email"])},
        lambda: parse_vendor_email(files["vendor_email"], evidence),
        output_summary=lambda result: {"characters": len(str(result.value))},
        evidence_id_extractor=lambda result: [result.evidence_id],
    )
    policy_docs = trace.run(
        "load_policy_documents",
        ["REQ-002", "REQ-006"],
        {"policy_files": _policy_paths(files)},
        lambda: load_policy_documents(Path(path) for path in _policy_paths(files)),
        output_summary=lambda result: {"policy_documents": sorted(result.keys())},
    )

    annual_contract_value = float(_value(intake_values, "annual_contract_value"))
    contract_term_months = int(_value(intake_values, "contract_term_months"))
    payment_terms = str(_value(intake_values, "payment_terms"))
    vendor_name = str(_value(intake_values, "vendor_name"))
    cost_center = str(_value(intake_values, "cost_center"))

    budget = trace.run(
        "lookup_budget",
        ["REQ-005"],
        {
            "cost_center": cost_center,
            "annual_contract_value": annual_contract_value,
            "path": str(files["tool_budget_lookup"]),
        },
        lambda: lookup_budget(
            files["tool_budget_lookup"], cost_center, annual_contract_value, evidence
        ),
        output_summary=lambda result: {
            "status": result.status,
            "budget_delta": result.budget_delta,
            "budget_owner": result.budget_owner,
        },
        evidence_id_extractor=lambda result: [result.evidence_id],
    )
    duplicate_vendor = trace.run(
        "check_existing_vendor",
        ["REQ-005"],
        {"vendor_name": vendor_name, "path": str(files["tool_vendor_register"])},
        lambda: check_existing_vendor(files["tool_vendor_register"], vendor_name),
        output_summary=lambda result: {
            "matched": result.matched,
            "match_count": len(result.matches),
        },
    )
    total_contract_value = trace.run(
        "calculate_total_contract_value",
        ["REQ-005"],
        {
            "annual_contract_value": annual_contract_value,
            "contract_term_months": contract_term_months,
            "one_time_fees": quote.one_time_fees,
        },
        lambda: calculate_total_contract_value(
            annual_contract_value,
            contract_term_months,
            quote.one_time_fees,
            [
                intake_values["annual_contract_value"].evidence_id,
                intake_values["contract_term_months"].evidence_id,
            ],
        ),
        output_summary=lambda result: {
            "recurring_total": result.recurring_total,
            "one_time_fees": result.one_time_fees,
            "total_contract_value": result.total_contract_value,
        },
        evidence_id_extractor=lambda result: result.evidence_ids,
    )
    risk = trace.run(
        "classify_data_sensitivity",
        ["REQ-005", "REQ-006"],
        {
            "annual_contract_value": annual_contract_value,
            "data_access": _list_value(intake_values, "data_access"),
            "integrations": _list_value(intake_values, "system_integrations"),
        },
        lambda: classify_data_sensitivity(
            annual_contract_value,
            _list_value(intake_values, "data_access"),
            _list_value(intake_values, "system_integrations"),
            _list_value(intake_values, "subprocessors_declared"),
            str(_value(intake_values, "ai_functionality")),
            security.soc2_type2_provided,
            [
                intake_values["data_access"].evidence_id,
                intake_values["system_integrations"].evidence_id,
                intake_values["subprocessors_declared"].evidence_id,
                intake_values["ai_functionality"].evidence_id,
            ]
            + security.evidence_ids,
        ),
        output_summary=lambda result: {"tier": result.tier, "reasons": result.reasons},
        evidence_id_extractor=lambda result: result.evidence_ids,
    )

    facts = CaseFacts(
        case_id=case_id,
        vendor_name=vendor_name,
        requesting_team=str(_value(intake_values, "requesting_team")),
        requester_name=str(_value(intake_values, "requester_name")),
        business_owner=str(_value(intake_values, "business_owner")),
        business_owner_email=str(_value(intake_values, "business_owner_email")),
        cost_center=cost_center,
        vendor_category=str(_value(intake_values, "vendor_category")),
        business_use_case=str(_value(intake_values, "use_case")),
        annual_contract_value=annual_contract_value,
        contract_term_months=contract_term_months,
        payment_terms=payment_terms,
        requested_start_date=str(_value(intake_values, "requested_start_date")),
        renewal_or_new_vendor=str(_value(intake_values, "renewal_or_new_vendor")),
        data_access=_list_value(intake_values, "data_access"),
        system_integrations=_list_value(intake_values, "system_integrations"),
        subprocessors_declared=_list_value(intake_values, "subprocessors_declared"),
        ai_functionality=str(_value(intake_values, "ai_functionality")),
        document_checklist=document_checklist,
        quote=quote,
        contract=contract,
        security=security,
        vendor_email=vendor_email,
        budget=budget,
        duplicate_vendor=duplicate_vendor,
        total_contract_value=total_contract_value,
        risk=risk,
    )

    missing = trace.run(
        "detect_missing_information",
        ["REQ-007"],
        {"case_id": case_id},
        lambda: build_missing_information(facts),
        output_summary=lambda result: {"missing_items": [item.item for item in result]},
        evidence_id_extractor=lambda result: _unique(
            [evidence_id for item in result for evidence_id in item.evidence_ids]
        ),
    )
    findings = trace.run(
        "run_policy_checks",
        ["REQ-006", "REQ-007"],
        {"case_id": case_id, "policy_document_count": len(policy_docs)},
        lambda: build_findings(facts),
        output_summary=lambda result: {
            "finding_count": len(result),
            "blockers": len([item for item in result if item.severity == "blocker"]),
        },
        evidence_id_extractor=lambda result: _unique(
            [evidence_id for item in result for evidence_id in item.evidence_ids]
        ),
    )
    approval_route = trace.run(
        "determine_required_approvals",
        ["REQ-008"],
        {"case_id": case_id},
        lambda: build_approval_route(facts, findings),
        evidence_ids=_unique(
            [evidence_id for item in findings for evidence_id in item.evidence_ids]
        ),
        output_summary=lambda result: {
            "status": result.status,
            "required_reviewers": result.required_reviewers,
        },
    )
    drafts = trace.run(
        "draft_human_review_messages",
        ["REQ-004", "REQ-008"],
        {"case_id": case_id, "missing_count": len(missing)},
        lambda: build_drafts(facts, missing),
        evidence_ids=_unique(
            [evidence_id for item in missing for evidence_id in item.evidence_ids]
        ),
        output_summary=lambda result: {
            "draft_count": len(result),
            "audiences": [item.audience for item in result],
        },
    )

    status = _packet_status(findings)
    status_reason = _status_reason(facts, missing, findings)
    summary = _summary(facts, status)

    return DecisionPacket(
        case_id=case_id,
        status=status,
        status_reason=status_reason,
        summary=summary,
        facts=facts,
        missing_information=missing,
        findings=findings,
        approval_route=approval_route,
        drafts=drafts,
        evidence=evidence.items,
        trace=trace.entries,
    )


def _value(values: Dict[str, object], key: str):
    return values[key].value


def _list_value(values: Dict[str, object], key: str) -> List[str]:
    value = _value(values, key)
    if value is None:
        return []
    if isinstance(value, list):
        return [item for item in value if item]
    value = str(value).strip()
    return [value] if value else []


def _policy_paths(files: Dict[str, Path]) -> List[str]:
    return [
        str(path)
        for key, path in sorted(files.items())
        if key.startswith("policy_")
    ]


def _unique(values: List[str]) -> List[str]:
    seen = set()
    unique_values = []
    for value in values:
        if value and value not in seen:
            unique_values.append(value)
            seen.add(value)
    return unique_values


def _join_list(values: List[str]) -> str:
    if not values:
        return "declared systems"
    if len(values) == 1:
        return values[0]
    return ", ".join(values[:-1]) + " and " + values[-1]


def _packet_status(findings) -> str:
    if any(finding.severity == "blocker" for finding in findings):
        return "blocked"
    if any(finding.severity == "review_required" for finding in findings):
        return "review_required"
    return "ready_low_risk"


def _status_reason(facts: CaseFacts, missing, findings) -> str:
    if any(finding.severity == "blocker" for finding in findings):
        missing_text = "; ".join(item.item for item in missing) or "policy review required"
        return "%s has unresolved blockers: %s." % (facts.vendor_name, missing_text)
    if facts.risk.tier == "high":
        return "%s is high risk and requires cross-functional review." % facts.vendor_name
    if facts.risk.tier == "medium":
        return "%s is medium risk and requires targeted review." % facts.vendor_name
    return "%s is low risk once routine setup checks are complete." % facts.vendor_name


def _summary(facts: CaseFacts, status: str) -> str:
    data_phrase = (
        "processes %s" % _join_list(facts.data_access)
        if facts.data_access
        else "does not declare customer, employee, or confidential data processing"
    )
    integration_phrase = (
        "integrates with %s" % _join_list(facts.system_integrations)
        if facts.system_integrations
        else "has no declared system integrations"
    )
    request_type = (
        "renewal" if facts.renewal_or_new_vendor == "renewal" else "new vendor request"
    )
    return (
        "%s is a %s for the %s team: %s. ACV is %s with a %s-month term, "
        "%s one-time fees, and %s payment terms. The vendor %s and %s. "
        "Current triage status is %s with %s risk."
    ) % (
        facts.vendor_name,
        request_type,
        facts.requesting_team,
        facts.business_use_case,
        _money(facts.annual_contract_value),
        facts.contract_term_months,
        _money(facts.quote.one_time_fees),
        facts.payment_terms,
        data_phrase,
        integration_phrase,
        status,
        facts.risk.tier,
    )


def _money(value: float) -> str:
    return "$%s" % format(value, ",.0f")
