"""Deterministic tool-like checks used by the triage pipeline."""

import csv
from difflib import SequenceMatcher
from pathlib import Path
from typing import Dict, List

from .parsers import EvidenceStore
from .schemas import (
    BudgetCheck,
    DuplicateVendorCheck,
    RiskClassification,
    TotalContractValue,
)


def lookup_budget(
    budget_csv: Path,
    cost_center: str,
    annual_contract_value: float,
    evidence: EvidenceStore,
) -> BudgetCheck:
    with budget_csv.open(newline="", encoding="utf-8") as handle:
        for row_number, row in enumerate(csv.DictReader(handle), start=2):
            if row["cost_center"] == cost_center:
                budget_remaining = float(row["annual_budget_remaining"])
                delta = budget_remaining - annual_contract_value
                status = "sufficient" if delta >= 0 else "insufficient"
                evidence_id = evidence.add(
                    budget_csv,
                    "csv",
                    "row %s" % row_number,
                    row,
                    "%s budget=%s acv=%s"
                    % (cost_center, budget_remaining, annual_contract_value),
                )
                return BudgetCheck(
                    cost_center=cost_center,
                    department=row["department"],
                    annual_budget_remaining=budget_remaining,
                    annual_contract_value=annual_contract_value,
                    budget_delta=delta,
                    budget_owner=row["budget_owner"],
                    status=status,
                    evidence_id=evidence_id,
                )
    evidence_id = evidence.add(
        budget_csv,
        "csv",
        "lookup",
        "No budget row found for %s" % cost_center,
        "missing",
    )
    return BudgetCheck(
        cost_center=cost_center,
        department="",
        annual_budget_remaining=0.0,
        annual_contract_value=annual_contract_value,
        budget_delta=-annual_contract_value,
        budget_owner="",
        status="missing",
        evidence_id=evidence_id,
    )


def check_existing_vendor(vendor_csv: Path, vendor_name: str) -> DuplicateVendorCheck:
    matches: List[Dict[str, str]] = []
    normalized_vendor = _normalize(vendor_name)
    with vendor_csv.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            normalized_candidate = _normalize(row["vendor_name"])
            ratio = SequenceMatcher(None, normalized_vendor, normalized_candidate).ratio()
            if ratio >= 0.82 or normalized_vendor in normalized_candidate:
                match = dict(row)
                match["similarity"] = "%.2f" % ratio
                matches.append(match)
    return DuplicateVendorCheck(
        vendor_name=vendor_name,
        matched=bool(matches),
        matches=matches,
    )


def calculate_total_contract_value(
    annual_contract_value: float,
    contract_term_months: int,
    one_time_fees: float,
    evidence_ids: List[str],
) -> TotalContractValue:
    recurring_total = annual_contract_value * contract_term_months / 12
    return TotalContractValue(
        annual_contract_value=annual_contract_value,
        contract_term_months=contract_term_months,
        recurring_total=recurring_total,
        one_time_fees=one_time_fees,
        total_contract_value=recurring_total + one_time_fees,
        evidence_ids=evidence_ids,
    )


def classify_data_sensitivity(
    annual_contract_value: float,
    data_access: List[str],
    integrations: List[str],
    subprocessors: List[str],
    ai_functionality: str,
    soc2_type2_provided: bool,
    evidence_ids: List[str],
) -> RiskClassification:
    reasons: List[str] = []
    data_access = _list(data_access)
    integrations = _list(integrations)
    subprocessors = _list(subprocessors)
    data_text = " ".join(data_access).lower()
    integrations_text = " ".join(integrations).lower()
    subprocessors_text = " ".join(subprocessors).lower()
    ai_text = (ai_functionality or "").lower()
    has_data = bool(data_access) and "no customer" not in data_text
    has_integrations = bool(integrations) and "no system" not in integrations_text
    has_ai = ai_text not in {"", "none"} and (
        "ai" in ai_text
        or "model" in ai_text
        or "attrition" in ai_text
        or "prediction" in ai_text
        or "recommendation" in ai_text
        or "segmentation" in ai_text
    )

    if "employee" in data_text or "performance" in data_text or "salary" in data_text:
        reasons.append("Processes sensitive employee data.")
    elif "customer" in data_text or "crm" in data_text or "named users" in data_text:
        reasons.append("Processes customer or user-identifiable data.")
    if "hris" in integrations_text:
        reasons.append("Integrates with HRIS.")
    elif "snowflake" in integrations_text or "salesforce" in integrations_text:
        reasons.append("Integrates with sensitive business systems.")
    elif has_integrations:
        reasons.append("Integrates with internal systems.")
    if has_ai and has_data:
        reasons.append("Uses AI or machine learning on company, customer, or employee data.")
    if "eu" in subprocessors_text or "apac" in subprocessors_text:
        reasons.append("Uses subprocessors outside the United States.")
    if (has_data or has_integrations or has_ai or annual_contract_value > 25000) and not soc2_type2_provided:
        reasons.append("Current SOC 2 Type II report is not provided.")
    if annual_contract_value > 100000:
        reasons.append("Annual contract value exceeds $100,000.")

    high_markers = [
        "sensitive employee",
        "hris",
        "ai or machine learning",
        "outside the united states",
        "soc 2 type ii",
        "exceeds $100,000",
        "sensitive business systems",
    ]
    if any(any(marker in reason.lower() for marker in high_markers) for reason in reasons):
        tier = "high"
    elif reasons or annual_contract_value > 25000:
        tier = "medium"
    else:
        tier = "low"
    return RiskClassification(tier=tier, reasons=reasons, evidence_ids=evidence_ids)


def _list(value: List[str]) -> List[str]:
    if not value:
        return []
    if isinstance(value, list):
        return [item for item in value if item]
    return [str(value)]


def _normalize(value: str) -> str:
    return (
        value.lower()
        .replace(",", "")
        .replace(".", "")
        .replace(" inc", "")
        .replace(" llc", "")
        .strip()
    )
