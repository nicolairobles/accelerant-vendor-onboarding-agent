from io import BytesIO
from pathlib import Path
from zipfile import ZipFile

from vendor_agent.pipeline import run_case
from vendor_agent.uploads import UploadedArtifact, missing_role_labels, stage_uploaded_case


CASE_DIR = Path("data/source-package/Candidate_package/cases/case_003")
PACKAGE_ROOT = Path("data/source-package/Candidate_package")


def test_uploaded_files_are_staged_and_run_through_pipeline(tmp_path):
    uploaded_case = stage_uploaded_case(
        [
            artifact("people intake.xlsx", "case_003_intake.xlsx"),
            artifact("vendor-pricing.csv", "case_003_quote.csv"),
            artifact("services agreement.pdf", "case_003_contract.pdf"),
            artifact("security answers.md", "case_003_security_questionnaire.md"),
            artifact("vendor email.txt", "case_003_vendor_email.txt"),
        ],
        tmp_path,
        template_package_root=PACKAGE_ROOT,
    )

    assert uploaded_case.is_ready
    assert not uploaded_case.missing_roles
    assert {match.role for match in uploaded_case.role_matches} == {
        "intake",
        "quote",
        "contract",
        "security_questionnaire",
        "vendor_email",
    }

    packet = run_case(uploaded_case.case_dir)

    assert packet.case_id == "uploaded_case"
    assert packet.facts.vendor_name == "TalentPulse AI"
    assert packet.status == "blocked"
    assert packet.facts.risk.tier == "high"


def test_uploaded_zip_package_is_supported(tmp_path):
    buffer = BytesIO()
    with ZipFile(buffer, "w") as archive:
        for path in CASE_DIR.iterdir():
            archive.writestr("vendor-package/%s" % path.name, path.read_bytes())

    uploaded_case = stage_uploaded_case(
        [UploadedArtifact(name="vendor-package.zip", content=buffer.getvalue())],
        tmp_path,
        template_package_root=PACKAGE_ROOT,
    )

    assert uploaded_case.is_ready
    packet = run_case(uploaded_case.case_dir)
    assert packet.facts.vendor_name == "TalentPulse AI"


def test_uploaded_package_reports_missing_required_files(tmp_path):
    uploaded_case = stage_uploaded_case(
        [
            artifact("intake.xlsx", "case_003_intake.xlsx"),
            artifact("quote.csv", "case_003_quote.csv"),
        ],
        tmp_path,
        template_package_root=PACKAGE_ROOT,
    )

    assert not uploaded_case.is_ready
    assert "contract" in uploaded_case.missing_roles
    assert "security_questionnaire" in uploaded_case.missing_roles
    assert "vendor_email" in uploaded_case.missing_roles
    labels = missing_role_labels(uploaded_case.missing_roles)
    assert "contract PDF (.pdf)" in labels
    assert not uploaded_case.case_dir.exists()


def artifact(uploaded_name: str, fixture_name: str) -> UploadedArtifact:
    return UploadedArtifact(
        name=uploaded_name,
        content=(CASE_DIR / fixture_name).read_bytes(),
    )
