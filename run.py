#!/usr/bin/env python3
"""
run.py — the one entry point. Runs a stage of the pipeline in the right order,
writes everything to its place, and ends with a summary of what changed.

    python run.py protein-set             verify (UniProt) -> build config -> deltas -> tests
    python run.py protein-set --offline   same, but skip the UniProt fetch (reuse data/)
    python run.py test                    just the tests

Later stages (harvest, mass-fractions, aggregate, ...) get added here as they exist.
All logs go to outputs/logs/<tool>_<stamp>.log.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
TOOLS = ROOT / "src" / "muscle_aa"
PY = sys.executable


def step(title: str, cmd: list[str]) -> None:
    print(f"\n=== {title} ===")
    r = subprocess.run(cmd, cwd=ROOT)
    if r.returncode != 0:
        print(f"\n!! {title} failed (exit {r.returncode}). Stopping.")
        sys.exit(r.returncode)


def newest(pattern: str) -> str:
    files = sorted((ROOT / "outputs" / "logs").glob(pattern))
    return str(files[-1].relative_to(ROOT)) if files else "(none)"


def protein_set(offline: bool) -> None:
    if not offline:
        step("1/4 verify accessions against UniProt", [PY, str(TOOLS / "verify_accessions.py")])
    else:
        print("\n=== 1/4 verify — skipped (--offline), using existing data/ ===")
    step("2/4 build config from decisions + data", [PY, str(TOOLS / "build_protein_set.py")])
    step("3/4 isoform / processing deltas", [PY, str(TOOLS / "isoform_processing_deltas.py")])
    step("4/4 tests", [PY, "-m", "pytest", "-q"])
    print(f"""
=== done: protein set ===
  hand-written input   config/protein_set_decisions.ini
  UniProt record       data/uniprot_verification.ini  (+ data/uniprot_raw/)
  generated config     config/accessions.ini, config/segments.ini
  decision numbers     outputs/isoform_processing/*.csv, isoform_notes.txt
  logs                 {newest('verify_accessions_*.log')}
                       {newest('build_protein_set_*.log')}
                       {newest('isoform_processing_deltas_*.log')}
                       {newest('pytest_*.log')}
""")


def main() -> None:
    args = sys.argv[1:]
    if not args or args[0] in ("-h", "--help"):
        print(__doc__)
        return
    if args[0] == "protein-set":
        protein_set(offline="--offline" in args)
    elif args[0] == "test":
        step("tests", [PY, "-m", "pytest", "-q"])
    else:
        print(f"unknown stage {args[0]!r}\n{__doc__}")
        sys.exit(2)


if __name__ == "__main__":
    main()
