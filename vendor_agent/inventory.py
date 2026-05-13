"""Case package inventory checks."""

from pathlib import Path
from typing import Dict, List, Tuple


CASE_SUFFIXES = {
    "intake": "intake.xlsx",
    "quote": "quote.csv",
    "contract": "contract.pdf",
    "security_questionnaire": "security_questionnaire.md",
    "vendor_email": "vendor_email.txt",
}

POLICY_FILES = [
    "communication_policy.md",
    "data_handling_policy.md",
    "finance_approval_matrix.md",
    "legal_review_policy.md",
    "procurement_policy.md",
    "security_review_policy.md",
    "vendor_risk_policy.md",
]

TOOL_FILES = ["budget_lookup.csv", "vendor_register.csv"]


def package_root_for_case(case_dir: Path) -> Path:
    return case_dir.parent.parent


def case_id_from_path(case_dir: Path) -> str:
    return case_dir.name


def inventory_case(case_dir: Path) -> Tuple[str, Dict[str, Path], List[str]]:
    case_dir = case_dir.resolve()
    case_id = case_id_from_path(case_dir)
    package_root = package_root_for_case(case_dir)
    files: Dict[str, Path] = {}
    missing: List[str] = []

    for key, suffix in CASE_SUFFIXES.items():
        path = case_dir / f"{case_id}_{suffix}"
        files[key] = path
        if not path.exists():
            missing.append(str(path))

    docs_dir = package_root / "docs"
    for policy_file in POLICY_FILES:
        key = "policy_" + policy_file.replace(".md", "")
        path = docs_dir / policy_file
        files[key] = path
        if not path.exists():
            missing.append(str(path))

    tools_dir = package_root / "tools"
    for tool_file in TOOL_FILES:
        key = "tool_" + tool_file.replace(".csv", "")
        path = tools_dir / tool_file
        files[key] = path
        if not path.exists():
            missing.append(str(path))

    return case_id, files, missing

