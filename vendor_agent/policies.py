"""Deterministic policy checks for vendor onboarding triage."""

from typing import List

from .schemas import (
    ApprovalRoute,
    CaseFacts,
    DraftMessage,
    MissingInfoItem,
    PolicyFinding,
)


def build_missing_information(facts: CaseFacts) -> List[MissingInfoItem]:
    missing: List[MissingInfoItem] = []
    checklist = {item.document_key: item for item in facts.document_checklist}
    has_sensitive_data = _has_sensitive_data(facts)
    needs_security_materials = facts.risk.tier in {"medium", "high"}
    ai_data_use_needs_confirmation = _has_ai_data_use_concern(facts)

    def add_from_checklist(
        key: str,
        label: str,
        owner: str,
        why_needed: str,
    ) -> None:
        item = checklist.get(key)
        if item and not item.provided:
            missing.append(
                MissingInfoItem(
                    item=label,
                    owner=owner,
                    why_needed=why_needed,
                    evidence_ids=[item.evidence_id],
                )
            )

    if needs_security_materials:
        add_from_checklist(
            "soc2_type2",
            "SOC 2 Type II report or equivalent security attestation",
            "Vendor / Security",
            "Medium-risk and high-risk vendors must provide a current SOC 2 Type II report or equivalent.",
        )

    if has_sensitive_data:
        add_from_checklist(
            "data_processing_agreement",
            "Data Processing Agreement",
            "Vendor / Legal",
            "The vendor processes personal, customer, employee, or confidential data and needs data protection terms.",
        )

    if ai_data_use_needs_confirmation:
        item = checklist.get("ai_training_opt_out")
        evidence_ids = [item.evidence_id] if item else _ai_evidence_ids(facts)
        label = (
            "AI training opt-out confirmation or Enterprise Control package"
            if item
            else "Data-use opt-out or service-improvement disablement confirmation"
        )
        missing.append(
            MissingInfoItem(
                item=label,
                owner="Vendor / Legal / Security",
                why_needed="Company, customer, or employee data cannot be used for model training, benchmarking, or product improvement without explicit approval.",
                evidence_ids=evidence_ids,
            )
        )

    add_from_checklist(
        "tax_form",
        "Updated tax form",
        "Vendor / Procurement",
        "Low-risk operational vendors still need tax documentation before vendor setup is complete.",
    )
    add_from_checklist(
        "vendor_setup_form",
        "Updated vendor setup form",
        "Vendor / Procurement",
        "Procurement needs current setup details before completing vendor setup or renewal routing.",
    )

    if facts.security.scim_provisioning.upper() == "TBD":
        missing.append(
            MissingInfoItem(
                item="SCIM provisioning answer",
                owner="Vendor / Security",
                why_needed="Provisioning controls are incomplete for a vendor integrating with %s."
                % _join_list(facts.system_integrations),
                evidence_ids=facts.security.evidence_ids,
            )
        )

    if facts.risk.tier == "high" and not facts.security.incident_response:
        missing.append(
            MissingInfoItem(
                item="Incident response and breach notification summary",
                owner="Vendor / Security",
                why_needed="High-risk vendors should provide incident response and breach notification information.",
                evidence_ids=facts.security.evidence_ids,
            )
        )

    return _dedupe_missing(missing)


def build_findings(facts: CaseFacts) -> List[PolicyFinding]:
    findings: List[PolicyFinding] = []
    next_id = 1
    doc_evidence = {item.document_key: item.evidence_id for item in facts.document_checklist}
    missing_docs = [item for item in facts.document_checklist if not item.provided]
    has_sensitive_data = _has_sensitive_data(facts)
    payment_days = _payment_days(facts.payment_terms)

    def add(
        function: str,
        severity: str,
        trigger: str,
        why: str,
        owner: str,
        action: str,
        evidence_ids: List[str],
        policy_refs: List[str],
    ) -> None:
        nonlocal next_id
        cleaned_evidence_ids = _clean_evidence_ids(evidence_ids)
        if not cleaned_evidence_ids:
            return
        findings.append(
            PolicyFinding(
                id="F%03d" % next_id,
                function=function,
                severity=severity,
                trigger=trigger,
                why_it_matters=why,
                required_owner=owner,
                recommended_action=action,
                evidence_ids=cleaned_evidence_ids,
                policy_refs=policy_refs,
            )
        )
        next_id += 1

    if missing_docs:
        add(
            "Procurement",
            "blocker",
            "Required onboarding materials are missing.",
            "A request cannot be marked ready while required information is missing.",
            "Procurement owner",
            "Request missing materials before routing for approval.",
            [item.evidence_id for item in missing_docs],
            ["Procurement Policy: Approval routing", "Procurement Policy: Document requirements by category"],
        )

    if facts.duplicate_vendor.matched:
        severity = "review_required" if facts.renewal_or_new_vendor == "new_vendor" else "informational"
        action = (
            "Review likely duplicate before creating a new vendor record."
            if severity == "review_required"
            else "Confirm renewal is linked to the existing active vendor record."
        )
        add(
            "Procurement",
            severity,
            "Vendor register has a likely existing-vendor match.",
            "Procurement should check whether a vendor already exists before creating or updating records.",
            "Procurement owner",
            action,
            [facts.vendor_email.evidence_id],
            ["Vendor Risk Policy: Duplicate vendor check"],
        )

    if facts.budget.status != "sufficient":
        add(
            "Finance",
            "blocker",
            "Annual contract value exceeds remaining budget.",
            "Available %s budget is %s while ACV is %s."
            % (
                facts.cost_center,
                _money(facts.budget.annual_budget_remaining),
                _money(facts.annual_contract_value),
            ),
            "Finance / FP&A",
            "Confirm incremental budget or reduce scope before approval routing.",
            [facts.budget.evidence_id],
            ["Finance Approval Matrix: Budget status"],
        )

    finance_owner = _finance_threshold_owner(facts.annual_contract_value)
    if finance_owner != "Business owner":
        add(
            "Finance",
            "review_required",
            "ACV requires %s approval." % finance_owner,
            "Annual contract value is %s." % _money(facts.annual_contract_value),
            finance_owner,
            "Route to the required Finance approver after blockers are resolved.",
            [facts.quote.line_items[0].evidence_id],
            ["Finance Approval Matrix: Spend approval thresholds"],
        )

    if facts.contract_term_months > 24:
        add(
            "Finance",
            "review_required",
            "Contract term exceeds 24 months.",
            "Longer commitments require Finance review.",
            "Finance",
            "Review multi-year spend commitment and total contract value.",
            facts.contract.evidence_ids,
            ["Finance Approval Matrix: Contract term"],
        )

    if payment_days == 60:
        add(
            "Finance",
            "review_required",
            "Payment terms are Net 60.",
            "Net 60 requires VP Finance review.",
            "VP Finance",
            "Review payment terms.",
            facts.contract.evidence_ids,
            ["Finance Approval Matrix: Payment terms"],
        )
    elif payment_days > 60:
        add(
            "Finance",
            "review_required",
            "Payment terms are %s." % facts.payment_terms,
            "Payment terms longer than Net 60 require VP Finance and Legal review.",
            "VP Finance",
            "Review and negotiate payment terms.",
            facts.contract.evidence_ids,
            ["Finance Approval Matrix: Payment terms"],
        )

    if facts.risk.tier in {"medium", "high"}:
        add(
            "Security",
            "review_required",
            "Security review is required for this vendor.",
            "The vendor risk tier is %s because %s"
            % (facts.risk.tier, "; ".join(facts.risk.reasons)),
            "Security",
            "Complete security review before marking the request ready.",
            facts.risk.evidence_ids,
            ["Security Review Policy: When Security review is required", "Vendor Risk Policy: Risk tiering"],
        )

    if facts.risk.tier in {"medium", "high"} and not facts.security.soc2_type2_provided:
        add(
            "Security",
            "blocker",
            "Current SOC 2 Type II or equivalent is not provided.",
            "Medium-risk and high-risk vendors need a current security attestation before approval readiness.",
            "Security",
            "Request SOC 2 Type II or equivalent security attestation.",
            facts.security.evidence_ids + [doc_evidence.get("soc2_type2", "")],
            ["Security Review Policy: Required security materials"],
        )

    if _has_ai_data_use_concern(facts):
        add(
            "Security",
            "blocker",
            "Vendor may use company, customer, or employee data for model or service improvement.",
            "Company, customer, and employee data may not be used for model training, benchmarking, or product improvement without explicit approval.",
            "Security / Legal / Executive sponsor",
            "Require opt-out, disablement confirmation, or explicit approved exception.",
            _ai_evidence_ids(facts),
            ["Security Review Policy: Blocking issues", "Data Handling Policy: AI and model training"],
        )

    if _has_non_us_subprocessors(facts):
        add(
            "Security",
            "review_required",
            "Subprocessors include non-US regions.",
            "Cross-border processing of personal or confidential data requires Legal and Security review.",
            "Security",
            "Review subprocessors, regions, and data-transfer terms.",
            facts.security.evidence_ids,
            ["Security Review Policy: High risk", "Data Handling Policy: Cross-border processing"],
        )

    if has_sensitive_data:
        add(
            "Legal",
            "review_required",
            "Vendor processes personal, customer, employee, or confidential data.",
            "Legal must confirm data protection terms, retention, deletion, and subprocessor obligations.",
            "Legal",
            "Review DPA, data use, breach, retention, deletion, and subprocessor language.",
            facts.contract.evidence_ids + facts.security.evidence_ids,
            ["Legal Review Policy: Data protection terms"],
        )

    if doc_evidence.get("data_processing_agreement") and not _doc_provided(facts, "data_processing_agreement"):
        add(
            "Legal",
            "blocker",
            "Data Processing Agreement is not provided.",
            "The vendor processes protected data and data protection terms must be confirmed.",
            "Legal",
            "Request DPA and confirm breach, retention, deletion, and subprocessor terms.",
            [doc_evidence.get("data_processing_agreement", "")],
            ["Legal Review Policy: Data protection terms"],
        )

    if facts.annual_contract_value > 50000:
        add(
            "Legal",
            "review_required",
            "Annual contract value exceeds $50,000.",
            "Legal review is required when annual contract value exceeds $50,000.",
            "Legal",
            "Review contract terms before approval.",
            [facts.quote.line_items[0].evidence_id],
            ["Legal Review Policy: When Legal review is required"],
        )

    if facts.total_contract_value.total_contract_value > 100000:
        add(
            "Legal",
            "review_required",
            "Total contract value exceeds $100,000.",
            "Legal review is required when total contract value exceeds $100,000.",
            "Legal",
            "Review total contract commitment and terms.",
            facts.total_contract_value.evidence_ids,
            ["Legal Review Policy: When Legal review is required"],
        )

    if facts.contract_term_months > 12:
        add(
            "Legal",
            "review_required",
            "Contract term exceeds 12 months.",
            "Legal review is required for contract terms longer than 12 months.",
            "Legal",
            "Review renewal, termination, and commitment terms.",
            facts.contract.evidence_ids,
            ["Legal Review Policy: When Legal review is required"],
        )

    if payment_days > 60:
        add(
            "Legal",
            "review_required",
            "Payment terms exceed Net 60.",
            "Legal review is required when payment terms exceed Net 60.",
            "Legal",
            "Review payment terms with Finance.",
            facts.contract.evidence_ids,
            ["Legal Review Policy: When Legal review is required"],
        )

    if _liability_below_12_months(facts.contract.limitation_of_liability):
        add(
            "Legal",
            "review_required",
            "Limitation of liability is below 12 months of fees.",
            "The contract states liability is limited to %s." % facts.contract.limitation_of_liability,
            "Legal",
            "Review and negotiate liability language.",
            facts.contract.evidence_ids,
            ["Legal Review Policy: Non-standard clauses"],
        )

    if facts.risk.tier == "high":
        add(
            "Vendor Risk",
            "review_required",
            "Preliminary risk tier is high.",
            "The vendor triggered high-risk conditions: %s" % "; ".join(facts.risk.reasons),
            "Procurement owner",
            "Route as high-risk vendor and do not mark ready until blockers are resolved.",
            facts.risk.evidence_ids,
            ["Vendor Risk Policy: High risk", "Vendor Risk Policy: Executive approval"],
        )
    elif facts.risk.tier == "low":
        add(
            "Vendor Risk",
            "informational",
            "Preliminary risk tier is low.",
            "The vendor has low spend, no system access, and no protected data processing.",
            "Procurement owner",
            "Proceed through low-risk vendor setup once required setup documents are complete.",
            [facts.vendor_email.evidence_id],
            ["Vendor Risk Policy: Low risk"],
        )

    return findings


def build_approval_route(facts: CaseFacts, findings: List[PolicyFinding]) -> ApprovalRoute:
    reviewers: List[str] = ["Business owner", "Procurement manager"]
    rationale: List[str] = []
    finance_owner = _finance_threshold_owner(facts.annual_contract_value)

    if finance_owner == "VP Finance":
        _append_once(reviewers, "VP Finance")
        rationale.append("ACV is %s, requiring VP Finance approval." % _money(facts.annual_contract_value))
    elif finance_owner == "CFO":
        _append_once(reviewers, "VP Finance")
        _append_once(reviewers, "CFO")
        rationale.append("ACV is %s, requiring CFO approval." % _money(facts.annual_contract_value))
    elif finance_owner == "Executive sponsor":
        _append_once(reviewers, "CFO")
        _append_once(reviewers, "Executive sponsor")
        rationale.append("ACV is %s, requiring executive approval." % _money(facts.annual_contract_value))
    else:
        rationale.append("ACV is %s, within business-owner approval threshold." % _money(facts.annual_contract_value))

    if facts.budget.status != "sufficient":
        _append_once(reviewers, "VP Finance")
        rationale.append("Available budget is below annual contract value.")

    payment_days = _payment_days(facts.payment_terms)
    if payment_days >= 60:
        _append_once(reviewers, "VP Finance")
        rationale.append("Payment terms are %s." % facts.payment_terms)

    if any(finding.function == "Legal" for finding in findings):
        _append_once(reviewers, "Legal")
        rationale.append("Legal policy triggers are present.")
    if any(finding.function == "Security" for finding in findings):
        _append_once(reviewers, "Security")
        rationale.append("Security policy triggers are present.")
    if any("Executive sponsor" in finding.required_owner for finding in findings):
        _append_once(reviewers, "Executive sponsor")
        rationale.append("AI data-use or high-risk vendor conditions require executive review.")

    if any(finding.severity == "blocker" for finding in findings):
        status = "blocked_pending_missing_information"
    elif any(finding.severity == "review_required" for finding in findings):
        status = "ready_for_cross_functional_review"
    else:
        status = "low_risk_setup_review"

    return ApprovalRoute(
        status=status,
        required_reviewers=reviewers,
        prohibited_actions=[
            "Approve vendor",
            "Commit spend",
            "Accept contract terms",
            "Send external communications",
            "Bypass Legal, Security, Finance, Procurement, or executive approval",
        ],
        rationale=rationale,
    )


def build_drafts(facts: CaseFacts, missing: List[MissingInfoItem]) -> List[DraftMessage]:
    if missing:
        missing_lines = "\n".join("- %s" % item.item for item in missing)
        vendor_body = (
            "Draft - requires human approval before sending.\n\n"
            "Hi,\n\n"
            "Thank you for the %s materials. To continue procurement review, "
            "could you please provide or confirm the following?\n\n"
            "%s\n\n"
            "Best,\nProcurement"
        ) % (facts.vendor_name, missing_lines)
    else:
        vendor_body = (
            "Draft - requires human approval before sending.\n\n"
            "Hi,\n\n"
            "Thank you for the %s materials. We do not have additional document requests at this stage.\n\n"
            "Best,\nProcurement"
        ) % facts.vendor_name

    internal_body = (
        "Draft internal note - requires human review.\n\n"
        "%s triage status: %s risk, %s ACV, %s budget status. "
        "Review required approvers and blockers before taking action."
    ) % (
        facts.vendor_name,
        facts.risk.tier,
        _money(facts.annual_contract_value),
        facts.budget.status,
    )

    return [
        DraftMessage(
            audience="vendor",
            subject="%s procurement follow-up" % facts.vendor_name,
            body=vendor_body,
        ),
        DraftMessage(
            audience="internal",
            subject="%s triage packet ready for review" % facts.vendor_name,
            body=internal_body,
        ),
    ]


def _has_sensitive_data(facts: CaseFacts) -> bool:
    text = " ".join(facts.data_access + facts.security.data_processed).lower()
    return bool(text) and "no customer" not in text and any(
        token in text
        for token in [
            "customer",
            "employee",
            "confidential",
            "crm",
            "usage analytics",
            "performance",
            "salary",
            "personal",
        ]
    )


def _has_non_us_subprocessors(facts: CaseFacts) -> bool:
    text = " ".join(facts.subprocessors_declared + facts.security.subprocessors).lower()
    return "eu" in text or "apac" in text


def _has_ai_data_use_concern(facts: CaseFacts) -> bool:
    if not _has_sensitive_data(facts):
        return False
    text = " ".join(
        [
            facts.ai_functionality,
            facts.contract.data_use,
            facts.security.ai_model_training,
            str(facts.vendor_email.value),
        ]
    ).lower()
    concern_terms = [
        "model enhancement",
        "service improvement",
        "improve",
        "benchmark",
        "recommendation tuning",
        "unless disabled",
        "unless opted out",
        "opt-out",
        "train",
    ]
    return any(term in text for term in concern_terms)


def _ai_evidence_ids(facts: CaseFacts) -> List[str]:
    return _clean_evidence_ids(
        facts.contract.evidence_ids
        + facts.security.evidence_ids
        + facts.risk.evidence_ids
        + [facts.vendor_email.evidence_id]
    )


def _doc_provided(facts: CaseFacts, key: str) -> bool:
    return any(item.document_key == key and item.provided for item in facts.document_checklist)


def _finance_threshold_owner(acv: float) -> str:
    if acv > 250000:
        return "Executive sponsor"
    if acv > 100000:
        return "CFO"
    if acv > 50000:
        return "VP Finance"
    if acv > 25000:
        return "Procurement manager"
    return "Business owner"


def _payment_days(payment_terms: str) -> int:
    digits = "".join(char for char in payment_terms if char.isdigit())
    return int(digits) if digits else 0


def _liability_below_12_months(value: str) -> bool:
    text = (value or "").lower()
    return "prior 6" in text or "6 months" in text or "below 12" in text


def _dedupe_missing(items: List[MissingInfoItem]) -> List[MissingInfoItem]:
    seen = set()
    unique_items = []
    for item in items:
        if item.item in seen:
            continue
        unique_items.append(item)
        seen.add(item.item)
    return unique_items


def _append_once(values: List[str], value: str) -> None:
    if value not in values:
        values.append(value)


def _clean_evidence_ids(values: List[str]) -> List[str]:
    return [value for value in values if value]


def _money(value: float) -> str:
    return "$%s" % format(value, ",.0f")


def _join_list(values: List[str]) -> str:
    if not values:
        return "the declared systems"
    if len(values) == 1:
        return values[0]
    return ", ".join(values[:-1]) + " and " + values[-1]
