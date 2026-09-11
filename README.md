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

## Running it

    python run.py protein-set        # the whole protein-set stage, in order, with a summary at the end
    python run.py protein-set --offline   # skip the UniProt fetch, reuse data/
    python run.py test               # just the tests

`run.py` is the only command you need to remember. It calls the tools in
`src/muscle_aa/` in the right order and prints where everything went.

## Where things live

| folder | meaning | who writes it |
|---|---|---|
| `config/` | what we decided — `protein_set_decisions.ini` is hand-written; `accessions.ini` and `segments.ini` are generated from it | you (decisions), `build_protein_set.py` (generated) |
| `data/` | what UniProt said — verification record and raw responses | `verify_accessions.py` |
| `outputs/` | everything computed, and **every log** in `outputs/logs/` | the tools |
| `docs/` | plan, conventions, decisions log, methods | hand-written |

The only hand-written input is `config/protein_set_decisions.ini` (which gene, which
isoform, which tier, and why). Everything mechanical — accessions, lengths, versions,
checksums, processing coordinates — is derived from UniProt by the scripts.
