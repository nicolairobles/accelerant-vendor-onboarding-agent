"""Reviewer-facing synthesis from validated decision packets."""

from typing import Any, Dict, List

from .schemas import SynthesisBundle


PROHIBITED_PHRASES = [
    "vendor is approved",
    "approved to proceed",
    "we approve",
    "approved for purchase",
    "terms are accepted",
    "accept the terms",
    "commit spend",
    "send this to the vendor",
    "blockers are resolved",
]


def build_synthesis_bundle(packet) -> SynthesisBundle:
    """Build a reviewer brief from structured packet fields only.

    This deterministic implementation is the fallback and validation contract for
    a future LLM-backed synthesis call. It intentionally does not read raw source
    documents or alter packet decisions.
    """

    cited_evidence_ids = _cited_evidence_ids(packet)
    executive_summary = _executive_summary(packet)
    vendor_follow_up_draft = _vendor_follow_up_draft(packet)
    internal_note_draft = _internal_note_draft(packet)
    errors = _validate_synthesis(
        packet,
        [executive_summary, vendor_follow_up_draft, internal_note_draft],
        cited_evidence_ids,
    )
    return SynthesisBundle(
        case_id=packet.case_id,
        synthesis_mode="deterministic_packet_synthesis",
        model_name="deterministic-template-v1",
        executive_summary=executive_summary,
        vendor_follow_up_draft=vendor_follow_up_draft,
        internal_note_draft=internal_note_draft,
        cited_evidence_ids=cited_evidence_ids,
        validation_status="failed" if errors else "passed",
        validation_errors=errors,
    )


def build_llm_synthesis_payload(packet) -> Dict[str, Any]:
    """Return the compact packet view that an LLM may receive later."""

    return {
        "case_id": packet.case_id,
        "status": packet.status,
        "status_reason": packet.status_reason,
        "vendor": packet.facts.vendor_name,
        "business_use_case": packet.facts.business_use_case,
        "annual_contract_value": packet.facts.annual_contract_value,
        "total_contract_value": packet.facts.total_contract_value.total_contract_value,
        "budget_status": packet.facts.budget.status,
        "risk_tier": packet.facts.risk.tier,
        "risk_reasons": packet.facts.risk.reasons,
        "missing_information": [
            {
                "item": item.item,
                "owner": item.owner,
                "why_needed": item.why_needed,
                "evidence_ids": item.evidence_ids,
            }
            for item in packet.missing_information
        ],
        "required_reviewers": packet.approval_route.required_reviewers,
        "prohibited_actions": packet.approval_route.prohibited_actions,
        "findings": [
            {
                "function": finding.function,
                "severity": finding.severity,
                "trigger": finding.trigger,
                "required_owner": finding.required_owner,
                "recommended_action": finding.recommended_action,
                "evidence_ids": finding.evidence_ids,
            }
            for finding in packet.findings
        ],
        "allowed_task": (
            "Rewrite a concise reviewer summary and draft follow-up text. "
            "Do not change status, risk, budget, missing information, approval route, "
            "or prohibited actions."
        ),
    }


def _executive_summary(packet) -> str:
    facts = packet.facts
    missing_count = len(packet.missing_information)
    reviewer_route = _join(packet.approval_route.required_reviewers)
    budget_note = "budget is %s" % facts.budget.status
    return (
        "%s is %s for procurement triage. The request is %s risk, ACV is %s, "
        "TCV is %s, and %s. There are %s open request(s) before the packet can "
        "move through the required human route: %s."
    ) % (
        facts.vendor_name,
        packet.status.replace("_", " "),
        facts.risk.tier,
        _money(facts.annual_contract_value),
        _money(facts.total_contract_value.total_contract_value),
        budget_note,
        missing_count,
        reviewer_route,
    )


def _vendor_follow_up_draft(packet) -> str:
    if not packet.missing_information:
        return (
            "Draft for human review: No vendor follow-up is currently required based on "
            "the structured packet."
        )
    lines = [
        "Draft for human review before any external send:",
        "",
        "To continue procurement triage for %s, please provide:" % packet.facts.vendor_name,
    ]
    for item in packet.missing_information:
        lines.append("- %s: %s" % (item.item, item.why_needed))
    return "\n".join(lines)


def _internal_note_draft(packet) -> str:
    blocker_count = len([finding for finding in packet.findings if finding.severity == "blocker"])
    review_count = len([finding for finding in packet.findings if finding.severity == "review_required"])
    lines = [
        "Internal routing note:",
        "%s is %s with %s blocker(s), %s review-required finding(s), and %s open request(s)."
        % (
            packet.facts.vendor_name,
            packet.status.replace("_", " "),
            blocker_count,
            review_count,
            len(packet.missing_information),
        ),
        "Required human route: %s." % _join(packet.approval_route.required_reviewers),
    ]
    top_findings = packet.findings[:3]
    if top_findings:
        lines.append("Top policy issues:")
        for finding in top_findings:
            lines.append("- %s: %s" % (finding.function, finding.trigger))
    return "\n".join(lines)


def _validate_synthesis(packet, texts: List[str], cited_evidence_ids: List[str]) -> List[str]:
    errors: List[str] = []
    evidence_ids = {item.id for item in packet.evidence}
    for evidence_id in cited_evidence_ids:
        if evidence_id not in evidence_ids:
            errors.append("unknown evidence id: %s" % evidence_id)
    combined = "\n".join(texts).lower()
    for phrase in PROHIBITED_PHRASES:
        if phrase in combined:
            errors.append("prohibited language: %s" % phrase)
    for item in packet.missing_information:
        if item.item.lower() not in combined:
            errors.append("missing item omitted from synthesis: %s" % item.item)
    status_text = packet.status.replace("_", " ")
    if packet.status not in combined and status_text not in combined:
        errors.append("packet status omitted from synthesis: %s" % packet.status)
    return errors


def _cited_evidence_ids(packet) -> List[str]:
    values: List[str] = []
    for item in packet.missing_information:
        values.extend(item.evidence_ids)
    for finding in packet.findings[:5]:
        values.extend(finding.evidence_ids)
    return _unique(values)


def _unique(values: List[str]) -> List[str]:
    seen = set()
    unique_values = []
    for value in values:
        if value and value not in seen:
            unique_values.append(value)
            seen.add(value)
    return unique_values


def _join(values: List[str]) -> str:
    if not values:
        return "Procurement owner"
    if len(values) == 1:
        return values[0]
    return ", ".join(values[:-1]) + " and " + values[-1]


def _money(value: float) -> str:
    return "$%s" % format(value, ",.0f")
