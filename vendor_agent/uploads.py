"""Upload staging for ad hoc vendor packages."""

import re
import shutil
import zipfile
from dataclasses import dataclass
from io import BytesIO
from pathlib import Path
from typing import Dict, Iterable, List, Tuple

from .inventory import CASE_SUFFIXES


DEFAULT_PACKAGE_ROOT = Path("data/source-package/Candidate_package")

ROLE_LABELS = {
    "intake": "intake workbook (.xlsx)",
    "quote": "quote CSV (.csv)",
    "contract": "contract PDF (.pdf)",
    "security_questionnaire": "security questionnaire (.md)",
    "vendor_email": "vendor email (.txt)",
}


@dataclass(frozen=True)
class UploadedArtifact:
    name: str
    content: bytes


@dataclass(frozen=True)
class UploadRoleMatch:
    role: str
    uploaded_name: str
    staged_name: str


@dataclass(frozen=True)
class UploadedCase:
    case_dir: Path
    role_matches: List[UploadRoleMatch]
    missing_roles: List[str]
    unmatched_files: List[str]
    warnings: List[str]

    @property
    def is_ready(self) -> bool:
        return not self.missing_roles


def stage_uploaded_case(
    artifacts: Iterable[UploadedArtifact],
    work_root: Path,
    template_package_root: Path = DEFAULT_PACKAGE_ROOT,
    case_id: str = "uploaded_case",
) -> UploadedCase:
    """Create a canonical case folder from uploaded files.

    The downstream pipeline expects stable file names, so upload handling is
    deliberately isolated here. Policy docs and mock internal tools still come
    from the bundled candidate package.
    """

    expanded = _expand_archives(list(artifacts))
    selected, unmatched_files, warnings = _select_role_matches(expanded)
    missing_roles = [role for role in CASE_SUFFIXES if role not in selected]

    case_dir = Path(work_root) / "Candidate_package" / "cases" / case_id
    role_matches: List[UploadRoleMatch] = []
    if missing_roles:
        return UploadedCase(
            case_dir=case_dir,
            role_matches=[],
            missing_roles=missing_roles,
            unmatched_files=unmatched_files,
            warnings=warnings,
        )

    package_root = case_dir.parent.parent
    _reset_directory(package_root)
    case_dir.mkdir(parents=True, exist_ok=True)
    _copy_supporting_package_files(template_package_root, package_root)

    for role, artifact in selected.items():
        staged_name = "%s_%s" % (case_id, CASE_SUFFIXES[role])
        staged_path = case_dir / staged_name
        staged_path.write_bytes(artifact.content)
        role_matches.append(
            UploadRoleMatch(
                role=role,
                uploaded_name=artifact.name,
                staged_name=staged_name,
            )
        )

    return UploadedCase(
        case_dir=case_dir,
        role_matches=sorted(role_matches, key=lambda item: item.role),
        missing_roles=[],
        unmatched_files=unmatched_files,
        warnings=warnings,
    )


def missing_role_labels(roles: Iterable[str]) -> List[str]:
    return [ROLE_LABELS.get(role, role) for role in roles]


def _expand_archives(artifacts: List[UploadedArtifact]) -> List[UploadedArtifact]:
    expanded: List[UploadedArtifact] = []
    for artifact in artifacts:
        if artifact.name.lower().endswith(".zip"):
            expanded.extend(_zip_members(artifact))
        else:
            expanded.append(artifact)
    return expanded


def _zip_members(artifact: UploadedArtifact) -> List[UploadedArtifact]:
    members: List[UploadedArtifact] = []
    with zipfile.ZipFile(BytesIO(artifact.content)) as archive:
        for member in archive.infolist():
            if member.is_dir() or member.filename.startswith("__MACOSX/"):
                continue
            name = member.filename.replace("\\", "/")
            if name.startswith("/") or ".." in Path(name).parts:
                continue
            members.append(
                UploadedArtifact(
                    name="%s:%s" % (artifact.name, name),
                    content=archive.read(member),
                )
            )
    return members


def _select_role_matches(
    artifacts: List[UploadedArtifact],
) -> Tuple[Dict[str, UploadedArtifact], List[str], List[str]]:
    candidates: Dict[str, List[Tuple[int, UploadedArtifact]]] = {
        role: [] for role in CASE_SUFFIXES
    }
    unmatched: List[str] = []
    warnings: List[str] = []

    for artifact in artifacts:
        scores = {
            role: _score_artifact(artifact, role)
            for role in CASE_SUFFIXES
        }
        best_score = max(scores.values()) if scores else 0
        if best_score <= 0:
            unmatched.append(artifact.name)
            continue
        for role, score in scores.items():
            if score == best_score:
                candidates[role].append((score, artifact))
                break

    selected: Dict[str, UploadedArtifact] = {}
    selected_names = set()
    for role, role_candidates in candidates.items():
        if not role_candidates:
            continue
        ordered = sorted(
            role_candidates,
            key=lambda item: (item[0], _specificity(item[1].name, role)),
            reverse=True,
        )
        selected[role] = ordered[0][1]
        selected_names.add(ordered[0][1].name)
        if len(ordered) > 1:
            warnings.append(
                "Multiple files looked like %s; using %s."
                % (ROLE_LABELS[role], ordered[0][1].name)
            )

    for artifact in artifacts:
        if artifact.name not in selected_names and artifact.name not in unmatched:
            unmatched.append(artifact.name)

    return selected, sorted(unmatched), warnings


def _score_artifact(artifact: UploadedArtifact, role: str) -> int:
    name = artifact.name.lower()
    suffix = CASE_SUFFIXES[role].rsplit(".", 1)[1]
    if not name.endswith("." + suffix):
        return 0

    text = _text_head(artifact.content)
    score = 10
    role_tokens = {
        "intake": ["intake", "request", "form"],
        "quote": ["quote", "pricing", "order"],
        "contract": ["contract", "agreement", "msa"],
        "security_questionnaire": ["security_questionnaire", "security", "questionnaire"],
        "vendor_email": ["vendor_email", "vendor", "email"],
    }[role]
    score += 8 * sum(1 for token in role_tokens if token in name)

    if role == "quote" and {"line_item", "annual_amount", "one_time_amount"} <= set(_csv_headers(text)):
        score += 40
    elif role == "security_questionnaire":
        if "## security controls" in text or "## soc 2" in text:
            score += 40
    elif role == "vendor_email":
        if "subject:" in text or "from:" in text:
            score += 30
    elif role == "contract":
        if artifact.content.startswith(b"%PDF"):
            score += 20
    elif role == "intake":
        if "intake" in name:
            score += 20

    return score


def _specificity(name: str, role: str) -> int:
    normalized = name.lower().replace("-", "_").replace(" ", "_")
    expected = CASE_SUFFIXES[role].replace(".", "_")
    return len(re.findall(re.escape(role), normalized)) + (1 if expected in normalized else 0)


def _csv_headers(text: str) -> List[str]:
    first_line = text.splitlines()[0] if text.splitlines() else ""
    return [item.strip().lower() for item in first_line.split(",")]


def _text_head(content: bytes) -> str:
    return content[:8192].decode("utf-8", errors="ignore").lower()


def _copy_supporting_package_files(template_package_root: Path, package_root: Path) -> None:
    template_package_root = Path(template_package_root)
    for folder_name in ["docs", "tools"]:
        source = template_package_root / folder_name
        destination = package_root / folder_name
        if not source.exists():
            raise FileNotFoundError("Missing supporting package folder: %s" % source)
        shutil.copytree(source, destination)


def _reset_directory(path: Path) -> None:
    if path.exists():
        shutil.rmtree(path)
    path.mkdir(parents=True, exist_ok=True)
