"""Reviewer-facing synthesis from validated decision packets."""

import json
import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from .schemas import SynthesisBundle


DEFAULT_OPENAI_SYNTHESIS_MODEL = "gpt-4o-mini-2024-07-18"


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


class SynthesisDraft(BaseModel):
    executive_summary: str = Field(
        description="Concise procurement-owner summary of the validated packet."
    )
    vendor_follow_up_draft: str = Field(
        description=(
            "Draft vendor follow-up. Must state it requires human review before sending "
            "and include each missing_information item exactly."
        )
    )
    internal_note_draft: str = Field(
        description="Draft internal routing note for procurement and reviewers."
    )
    cited_evidence_ids: List[str] = Field(
        default_factory=list,
        description="Evidence IDs from the packet used in the synthesis.",
    )


def build_synthesis_bundle(packet, provider: Optional[str] = None) -> SynthesisBundle:
    """Build a reviewer brief from structured packet fields only.

    This deterministic implementation is the fallback and validation contract for
    a future LLM-backed synthesis call. It intentionally does not read raw source
    documents or alter packet decisions.
    """

    selected_provider = (provider or os.getenv("OPENAI_SYNTHESIS_PROVIDER", "deterministic")).lower()
    if selected_provider == "openai":
        try:
            bundle = build_openai_synthesis_bundle(packet)
            if bundle.validation_status == "passed":
                return bundle
            fallback = build_deterministic_synthesis_bundle(packet)
            return fallback.model_copy(
                update={
                    "synthesis_mode": "deterministic_fallback_after_openai_validation",
                    "model_name": "%s -> deterministic-template-v1" % bundle.model_name,
                    "generated_at": _now_utc(),
                    "validation_status": "passed_with_provider_fallback",
                    "validation_errors": bundle.validation_errors,
                }
            )
        except Exception:
            fallback = build_deterministic_synthesis_bundle(packet)
            return fallback.model_copy(
                update={
                    "synthesis_mode": "deterministic_fallback_after_openai_error",
                    "model_name": "%s -> deterministic-template-v1"
                    % os.getenv("OPENAI_SYNTHESIS_MODEL", DEFAULT_OPENAI_SYNTHESIS_MODEL),
                    "generated_at": _now_utc(),
                    "validation_status": "passed_with_provider_fallback",
                    "validation_errors": [],
                }
            )
    return build_deterministic_synthesis_bundle(packet)


def build_deterministic_synthesis_bundle(packet) -> SynthesisBundle:
    """Build the deterministic reviewer brief fallback."""

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
        generated_at=_now_utc(),
        executive_summary=executive_summary,
        vendor_follow_up_draft=vendor_follow_up_draft,
        internal_note_draft=internal_note_draft,
        cited_evidence_ids=cited_evidence_ids,
        validation_status="failed" if errors else "passed",
        validation_errors=errors,
    )


def build_openai_synthesis_bundle(packet, client=None, model: Optional[str] = None) -> SynthesisBundle:
    """Build a reviewer brief using OpenAI structured outputs."""

    if client is None:
        from openai import OpenAI

        client = OpenAI()
    model_name = model or os.getenv("OPENAI_SYNTHESIS_MODEL", DEFAULT_OPENAI_SYNTHESIS_MODEL)
    response = client.responses.parse(
        model=model_name,
        input=[
            {
                "role": "system",
                "content": (
                    "You draft procurement reviewer synthesis from a validated vendor "
                    "onboarding decision packet. Do not change status, risk, budget, "
                    "missing information, approval route, prohibited actions, or evidence IDs. "
                    "Do not approve vendors, commit spend, accept contract terms, or send messages. "
                    "Every vendor-facing draft must say it requires human review before external use. "
                    "Copy each value in expected_missing_items exactly at least once in the vendor "
                    "follow-up draft. Cite only evidence IDs present in known_evidence_ids."
                ),
            },
            {
                "role": "user",
                "content": json.dumps(build_llm_synthesis_payload(packet), sort_keys=True),
            },
        ],
        text_format=SynthesisDraft,
        temperature=0,
    )
    draft = response.output_parsed
    if draft is None:
        raise ValueError("OpenAI synthesis returned no parsed output")
    errors = _validate_synthesis(
        packet,
        [draft.executive_summary, draft.vendor_follow_up_draft, draft.internal_note_draft],
        draft.cited_evidence_ids,
    )
    return SynthesisBundle(
        case_id=packet.case_id,
        synthesis_mode="openai_responses_structured_output",
        model_name=model_name,
        generated_at=_now_utc(),
        executive_summary=draft.executive_summary,
        vendor_follow_up_draft=draft.vendor_follow_up_draft,
        internal_note_draft=draft.internal_note_draft,
        cited_evidence_ids=draft.cited_evidence_ids,
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
        "expected_missing_items": [item.item for item in packet.missing_information],
        "known_evidence_ids": [item.id for item in packet.evidence],
        "validation_requirements": [
            "Keep packet status, risk tier, budget status, approval route, and prohibited actions unchanged.",
            "Include every expected_missing_items value exactly in vendor_follow_up_draft.",
            "State that vendor_follow_up_draft requires human review before external use.",
            "Use only known_evidence_ids in cited_evidence_ids.",
            "Do not include approval, spend commitment, accepted terms, or external-send language.",
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


def _now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


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
