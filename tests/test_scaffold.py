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
    "src/muscle_aa/build_protein_set.py",
    "run.py",
    "config/protein_set_decisions.ini",
]


def test_layout_exists():
    missing = [p for p in EXPECTED if not (ROOT / p).exists()]
    assert not missing, f"missing: {missing}"


def test_tools_compile():
    for f in ("verify_accessions.py", "isoform_processing_deltas.py", "build_protein_set.py"):
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


def test_accessions_match_uniprot_verification():
    """When data/uniprot_verification.ini exists (output of verify_accessions.py),
    every accessions.ini entry must agree with it on accession, length, sequence
    version, and MD5. Catches copy errors between the verification data and config."""
    vpath = ROOT / "data" / "uniprot_verification.ini"
    if not vpath.exists():
        import pytest
        pytest.skip("data/uniprot_verification.ini not present; run verify_accessions.py")
    v = _ini("data/uniprot_verification.ini")
    a = _ini("config/accessions.ini")
    problems = []
    for s in a.sections():
        g, acc, iso = a[s]["gene"], a[s]["accession"], a[s]["isoform"]
        if g not in v or v[g].get("accession") != acc:
            problems.append(f"{s}: accession {acc} not verified for gene {g}")
            continue
        if iso == "canonical":
            ok = (v[g]["length"] == a[s]["length"] and v[g]["seq_version"] == a[s]["seq_version"]
                  and v[g]["md5_published"] == a[s]["md5"])
        else:
            ok = False
            for i in range(1, int(v[g].get("isoform_count", "0")) + 1):
                if iso in v[g].get(f"isoform_{i}_ids", "").split(","):
                    ok = (v[g][f"isoform_{i}_length"] == a[s]["length"]
                          and v[g][f"isoform_{i}_md5_local"] == a[s]["md5"])
        if not ok:
            problems.append(f"{s}: length/version/md5 differ from verification data")
    assert not problems, "\n".join(problems)


def test_config_is_built_from_data():
    """accessions.ini and segments.ini must be exactly what build_protein_set.py
    produces from protein_set_decisions.ini + the UniProt verification data.
    A hand edit, a stale build, or a transcription error all fail here."""
    if not (ROOT / "data" / "uniprot_verification.ini").exists():
        import pytest
        pytest.skip("data/uniprot_verification.ini not present; run verify_accessions.py")
    import subprocess
    import sys
    r = subprocess.run([sys.executable, str(ROOT / "src/muscle_aa/build_protein_set.py"), "--check"],
                       capture_output=True, text=True)
    assert r.returncode == 0, r.stdout + r.stderr
