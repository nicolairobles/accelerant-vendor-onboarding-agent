"""Typed contracts for vendor onboarding triage outputs."""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class SourceEvidence(BaseModel):
    id: str
    source_file: str
    source_type: str
    location: str
    snippet: str
    parsed_value: Optional[str] = None
    policy_reference: Optional[str] = None


class ExtractedValue(BaseModel):
    key: str
    value: Any
    evidence_id: str


class DocumentChecklistItem(BaseModel):
    document_key: str
    provided: bool
    expected_artifact: str
    note: str
    evidence_id: str


class QuoteLineItem(BaseModel):
    line_item: str
    billing_type: str
    quantity: float
    unit_price: float
    annual_amount: float
    one_time_amount: float
    notes: str
    evidence_id: str


class QuoteSummary(BaseModel):
    annual_contract_value: float
    one_time_fees: float
    line_items: List[QuoteLineItem]


class ContractTerms(BaseModel):
    vendor_name: str
    effective_date: str
    initial_term_months: int
    annual_fees: float
    payment_terms: str
    limitation_of_liability: str
    auto_renewal: str
    data_use: str
    deletion_terms: str
    subprocessors: str
    evidence_ids: List[str]


class SecurityFacts(BaseModel):
    data_processed: List[str]
    integrations: List[str]
    encryption_in_transit: str
    encryption_at_rest: str
    sso_saml: str
    scim_provisioning: str
    audit_logs: str
    soc2_type: str
    soc2_type2_provided: bool
    incident_response: str
    subprocessors: List[str]
    data_retention: str
    ai_model_training: str
    gaps: List[str]
    evidence_ids: List[str]


class BudgetCheck(BaseModel):
    cost_center: str
    department: str
    annual_budget_remaining: float
    annual_contract_value: float
    budget_delta: float
    budget_owner: str
    status: str
    evidence_id: str


class DuplicateVendorCheck(BaseModel):
    vendor_name: str
    matched: bool
    matches: List[Dict[str, str]]


class TotalContractValue(BaseModel):
    annual_contract_value: float
    contract_term_months: int
    recurring_total: float
    one_time_fees: float
    total_contract_value: float
    evidence_ids: List[str]


class RiskClassification(BaseModel):
    tier: str
    reasons: List[str]
    evidence_ids: List[str]


class CaseFacts(BaseModel):
    case_id: str
    vendor_name: str
    requesting_team: str
    requester_name: str
    business_owner: str
    business_owner_email: str
    cost_center: str
    vendor_category: str
    business_use_case: str
    annual_contract_value: float
    contract_term_months: int
    payment_terms: str
    requested_start_date: str
    renewal_or_new_vendor: str
    data_access: List[str]
    system_integrations: List[str]
    subprocessors_declared: List[str]
    ai_functionality: str
    document_checklist: List[DocumentChecklistItem]
    quote: QuoteSummary
    contract: ContractTerms
    security: SecurityFacts
    vendor_email: ExtractedValue
    budget: BudgetCheck
    duplicate_vendor: DuplicateVendorCheck
    total_contract_value: TotalContractValue
    risk: RiskClassification


class MissingInfoItem(BaseModel):
    item: str
    owner: str
    why_needed: str
    evidence_ids: List[str] = Field(default_factory=list)


class PolicyFinding(BaseModel):
    id: str
    function: str
    severity: str
    trigger: str
    why_it_matters: str
    required_owner: str
    recommended_action: str
    evidence_ids: List[str] = Field(default_factory=list)
    policy_refs: List[str] = Field(default_factory=list)


class ApprovalRoute(BaseModel):
    status: str
    required_reviewers: List[str]
    prohibited_actions: List[str]
    rationale: List[str]


class DraftMessage(BaseModel):
    audience: str
    subject: str
    body: str
    requires_human_approval: bool = True


class SynthesisBundle(BaseModel):
    case_id: str
    synthesis_mode: str
    model_name: str
    generated_at: Optional[str] = None
    executive_summary: str
    vendor_follow_up_draft: str
    internal_note_draft: str
    cited_evidence_ids: List[str] = Field(default_factory=list)
    validation_status: str
    validation_errors: List[str] = Field(default_factory=list)


class ToolTraceEntry(BaseModel):
    tool_name: str
    status: str
    inputs: Dict[str, Any]
    outputs: Dict[str, Any]
    duration_ms: float
    requirement_ids: List[str]
    evidence_ids: List[str] = Field(default_factory=list)


class DecisionPacket(BaseModel):
    case_id: str
    status: str
    status_reason: str
    summary: str
    facts: CaseFacts
    missing_information: List[MissingInfoItem]
    findings: List[PolicyFinding]
    approval_route: ApprovalRoute
    drafts: List[DraftMessage]
    synthesis: Optional[SynthesisBundle] = None
    evidence: List[SourceEvidence]
    trace: List[ToolTraceEntry]
