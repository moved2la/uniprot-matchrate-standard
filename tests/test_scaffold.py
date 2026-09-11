"""Smoke test: the repo layout the plan (section 3) promises actually exists."""
import py_compile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

EXPECTED = [
    "config/candidates_step1.ini",
    "docs/00_project_plan.md",
    "docs/conventions.md",
    "docs/decisions.md",
    "docs/handoff_template.md",
    "docs/handoffs/01_accession_list.md",
    "src/muscle_aa/verify_accessions.py",
]


def test_layout_exists():
    missing = [p for p in EXPECTED if not (ROOT / p).exists()]
    assert not missing, f"missing: {missing}"


def test_verify_script_compiles():
    py_compile.compile(str(ROOT / "src/muscle_aa/verify_accessions.py"), doraise=True)
