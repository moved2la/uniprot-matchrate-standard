# uniprot-matchrate-standard

Public, auditable, sequence-derived amino acid standard for human skeletal muscle.

- **Layer A** — per-protein residue composition from UniProt sequences. Exact.
- **Layer B** — mass fraction of each protein in the tissue, by fiber type. Literature-derived, cited per row, uncertainty propagated.

Plan: `docs/00_project_plan.md`. Conventions: `docs/conventions.md`. Decisions: `docs/decisions.md`.
Each step runs in its own thread from its handoff in `docs/handoffs/`.

## Quick start

    python -m venv .venv && source .venv/bin/activate
    pip install -e ".[dev]"
    pytest

Step 1 verification run (needs network):

    python src/muscle_aa/verify_accessions.py --candidates config/candidates_step1.ini --outdir data
