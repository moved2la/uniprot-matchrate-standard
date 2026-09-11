# uniprot-matchrate-standard

Public, auditable, sequence-derived amino acid standard for human skeletal muscle.

- **Layer A** — per-protein residue composition from UniProt sequences. Exact.
- **Layer B** — mass fraction of each protein in the tissue, by fiber type. Literature-derived, cited per row, uncertainty propagated.

Plan: `docs/00_project_plan.md`. Conventions: `docs/conventions.md`. Decisions: `docs/decisions.md`.
Each step runs in its own thread from its handoff in `docs/handoffs/`.

## Quick start

    python -m venv .venv
    .venv\Scripts\activate          # Windows   (source .venv/bin/activate on macOS/Linux)
    pip install -r requirements.txt
    pytest

The tools themselves need only the standard library; `requirements.txt` is just pytest.
`pyproject.toml` describes the package for anyone who wants to `pip install` the repo;
you don't need it for day-to-day work.

Verify the protein set against UniProt (needs network):

    python src/muscle_aa/verify_accessions.py --candidates config/gene_candidates.ini --outdir data
