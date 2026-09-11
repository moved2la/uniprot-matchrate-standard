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

## Building the protein set (Layer A inputs)

    python src/muscle_aa/verify_accessions.py          # UniProt -> data/   (needs network)
    python src/muscle_aa/build_protein_set.py          # decisions + data -> config/accessions.ini, segments.ini
    python src/muscle_aa/isoform_processing_deltas.py  # decision-support numbers -> outputs/isoform_processing/
    pytest                                             # checks config is exactly what the build produces

The only hand-written input is `config/protein_set_decisions.ini` (which gene, which
isoform, which tier, and why). Everything mechanical — accessions, lengths, versions,
checksums, processing coordinates — is derived from UniProt by the scripts.
