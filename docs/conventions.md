# Conventions

Formalized from `00_project_plan.md` §6. Any change here is a logged decision.

## Config format

`.ini` via `configparser` with `optionxform = str` (keys are case-sensitive). One section per entity.
Free-text `note` and `justification` keys allowed anywhere. Comments with `#`.
Biology lives in config, not in code.

## Terminology

- **Paralog** — a different gene (MYH1 vs MYH2). Own accession, own entry in every config.
- **Isoform** — a splice/promoter variant of the *same* gene (Q8WZ42-4). Suffix on the accession.
- Never write "MYH isoforms" for paralogs in project docs; write "MYH paralogs" or "MYH genes".
  Full statement in `docs/methods.md` § Terminology.

## Accession identity

`ACCESSION` = canonical sequence. `ACCESSION-N` = a specific UniProt isoform.
Every entry records `seq_version`, `length`, and the verification date.
Canonical sequences are verified against UniProt's published MD5; isoform sequences record a
locally computed MD5 plus length (UniProt publishes no per-isoform checksum).

## Segment flags (`config/segments.ini`)

Inherited from the collagen pipeline. One or more sections per accession:

    [P68133.chain]
    start              = 3
    end                = 377
    in_master_molecule = true
    note               = mature chain after removal of Met1 and Cys2 (UniProt FT PROPEP)

Coordinates are 1-indexed, inclusive, on the fetched sequence.
`master` segment set = sections with `in_master_molecule = true`; `metabolic` = all sections.
Where no processing occurs, one whole-chain section with an explicit note — the harvest never infers.

## Citation schema (every literature-derived number)

    value     = 0.431
    unit      = mass_fraction_of_tier
    source    = Author et al. YEAR, Journal Vol:pages, DOI
    location  = Supplementary Table S3, column "iBAQ_typeI"
    retrieved = 2026-09-XX
    note      = optional — conversions applied, caveats

## Mass conventions

- `residue_mass` — in-chain residue mass (free AA minus 18.01528 Da). Sums to protein MW.
- `free_aa_mass` — free amino acid mass. Sums to MW + (n−1)·water. USDA / lab AAA convention; Match Rate uses this.
- Both reported. Ground truth is the residue count.

## Tiers

1 = myofibrillar (primary standard). 2 = sarcoplasmic (sensitivity analysis). 3 = ECM/stromal (collagen pipeline, out of scope here).
Mass fractions are normalized within tier.

## Fiber type

`I | IIa | IIx | all`. `all` means expressed in more than one type; level is Layer B's job.

## Naming: stages, not step numbers

Step numbers belong to the project plan (`docs/00_project_plan.md`, `docs/handoffs/`,
`docs/decisions.md`). Nothing the repository ships — config, code, tests, outputs,
methods, README — refers to a step number. Use the stage name:

| plan step | name used in shipped files |
|---|---|
| 1 | protein set (definition / verification) |
| 2 | sequence harvest; composition engine (Layer A) |
| 3 | mass-fraction assignment (Layer B) |
| 4 | aggregation |
| 5 | laboratory validation |
| 6 | Match Rate |

Tool and output names say what they do (`verify_accessions.py`,
`isoform_processing_deltas.py`, `outputs/isoform_processing/`), never which step made them.

## Directories

- `config/` — hand-written, audited.
- `data/` — machine-generated or downloaded verbatim; never hand-edited.
- `outputs/` — derived tables and figures, versioned with the standard.
- `docs/handoffs/` — one per step; "Deferred / raised" and "Handoff to next" filled at close.
