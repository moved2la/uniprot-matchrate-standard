"""Smoke test: the repo layout the plan (section 3) promises actually exists,
and the protein-set tools compile."""
import configparser
import py_compile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

EXPECTED = [
    "config/gene_candidates.ini",
    "config/accessions.ini",
    "config/segments.ini",
    "docs/00_project_plan.md",
    "docs/conventions.md",
    "docs/decisions.md",
    "docs/methods.md",
    "docs/handoff_template.md",
    "docs/handoffs/01_accession_list.md",
    "src/muscle_aa/verify_accessions.py",
    "src/muscle_aa/isoform_processing_deltas.py",
]


def test_layout_exists():
    missing = [p for p in EXPECTED if not (ROOT / p).exists()]
    assert not missing, f"missing: {missing}"


def test_tools_compile():
    for f in ("verify_accessions.py", "isoform_processing_deltas.py"):
        py_compile.compile(str(ROOT / "src/muscle_aa" / f), doraise=True)


def _ini(path):
    c = configparser.ConfigParser()
    c.optionxform = str
    c.read(ROOT / path, encoding="utf-8")
    return c


def test_accessions_schema():
    c = _ini("config/accessions.ini")
    required = {"gene", "accession", "isoform", "seq_version", "length", "md5",
                "tier", "compartment", "fiber_type", "role", "justification", "verified"}
    for s in c.sections():
        assert required <= set(c[s]), f"{s} missing {required - set(c[s])}"
        assert c[s]["tier"] in {"1", "2", "3", "excluded"}, s


def test_every_fetched_accession_has_segments():
    acc = _ini("config/accessions.ini")
    seg = _ini("config/segments.ini")
    seg_ids = {s.split(".")[0] for s in seg.sections()}
    for s in acc.sections():
        if acc[s]["tier"] not in {"1", "2"}:
            continue
        ident = acc[s]["accession"] if acc[s]["isoform"] == "canonical" else acc[s]["isoform"]
        assert ident in seg_ids, f"{s}: no segments.ini entry for {ident}"


def test_segments_cover_full_length():
    acc = _ini("config/accessions.ini")
    seg = _ini("config/segments.ini")
    by_id = {}
    for s in seg.sections():
        by_id.setdefault(s.split(".")[0], []).append((int(seg[s]["start"]), int(seg[s]["end"])))
    for s in acc.sections():
        if acc[s]["tier"] not in {"1", "2"}:
            continue
        ident = acc[s]["accession"] if acc[s]["isoform"] == "canonical" else acc[s]["isoform"]
        spans = sorted(by_id[ident])
        covered = sum(e - b + 1 for b, e in spans)
        assert spans[0][0] == 1 and spans[-1][1] == int(acc[s]["length"]), s
        assert covered == int(acc[s]["length"]), f"{s}: segments cover {covered}, length {acc[s]['length']}"
