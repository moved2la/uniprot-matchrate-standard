# Project Plan — Sequence-Derived Amino Acid Standard for Human Skeletal Muscle

**Status:** Planning complete, Step 1 ready to open
**Planning thread:** this document is the output of the planning thread. Each step below is executed in its own thread using its handoff doc in `docs/handoffs/`.
**Last updated:** 2026-09-09

---

## 1. Purpose

Replace the laboratory-sampled amino acid profile currently used as the NutriMatch™ "standard" with a **public, auditable, sequence-derived standard** computed from UniProt protein sequences and literature-derived tissue mass fractions.

The current standard has three problems:

1. It is a black box — quasi-public, not reproducible by a third party.
2. It carries laboratory error: acid hydrolysis destroys tryptophan, deamidates Asn→Asp and Gln→Glu, partially degrades Cys/Met/Ser/Thr; sampling variance between donors and muscles is unquantified.
3. It includes non-protein nitrogen (carnosine, anserine, taurine, creatine, free amino acid pool) that is not part of muscle protein.

The sequence-derived standard is exact at the protein level and carries uncertainty only in the tissue weighting, which is explicit, sourced, and propagated.

End goal: a published methods paper plus an open repository. The standard against which Match Rate is measured should not be a black box.

---

## 2. Design Principles

- **Primary sources only.** Sequences from UniProt REST with MD5 verification. Mass fractions from peer-reviewed supplementary data. No AI-estimated biological constants anywhere in the pipeline.
- **Every literature number carries a citation.** Source, table/figure, and page or supplementary file, on the same row as the number.
- **Human-editable, auditable config.** `.ini` files that a reviewer can open and check line by line. Biology lives in config, not in code.
- **Exactness is layered, and the layers are named.**
  - **Layer A** — per-protein residue composition from sequence. Exact. Zero uncertainty.
  - **Layer B** — mass fraction of each protein in the tissue, by fiber type. Literature-derived. Uncertainty is quantified and propagated.
- **Scope is tiered, and tiers are justified in writing** rather than by convention.
- **Corrections are welcome.** Anything found wrong gets fixed and logged in the decisions log (§8).

---

## 3. Architecture

```
UniProt REST ──► fetch ──► sequence store (.ini, MD5-verified)
                                    │
accessions.ini ─────────────────────┤  Layer A
segments.ini (processing flags) ────┤
                                    ▼
                          composition engine
                    (residue counts → mass vectors,
                     residue-mass AND free-AA-mass conventions)
                                    │
mass_fractions_<fiber>.ini ─────────┤  Layer B (cited per row)
fiber_mixes.ini ────────────────────┤
                                    ▼
                          aggregation + Monte Carlo
                    (per fiber type, per muscle, ranges, plots)
                                    │
                                    ▼
                          STANDARD (versioned, published)
                                    │
USDA food table ────────────────────┤
match formula ──────────────────────┤
                                    ▼
                          Match Rate for any food
```

### Repository layout (target)

```
uniprot-matchrate-standard/
├── README.md
├── pyproject.toml
├── config/
│   ├── accessions.ini            # Step 1 — what proteins, which isoform, which tier
│   ├── segments.ini              # Step 1/2 — processing flags per accession
│   ├── mass_fractions/           # Step 3 — one file per fiber type, cited per row
│   └── fiber_mixes.ini           # Step 3/4 — fiber-type proportions per muscle
├── data/
│   ├── sequences.ini             # Step 2 — auto-generated, MD5-verified
│   ├── literature/               # Step 3 — supplementary tables as downloaded, with provenance
│   └── usda/                     # Step 6
├── src/muscle_aa/
│   ├── fetch.py                  # Step 2
│   ├── composition.py            # Step 2
│   ├── aggregate.py              # Step 4
│   ├── uncertainty.py            # Step 4
│   ├── validate.py               # Step 5
│   ├── match.py                  # Step 6
│   └── plots.py                  # Step 4/5
├── tests/
├── outputs/                      # standard tables, figures — versioned
└── docs/
    ├── 00_project_plan.md        # this file
    ├── handoff_template.md
    ├── handoffs/                 # one per step
    ├── decisions.md              # running log, see §8
    └── methods.md                # written incrementally, becomes the paper's Methods
```

---

## 4. Decisions Already Made (planning thread)

| # | Decision | Rationale |
|---|----------|-----------|
| D1 | Standard is built first; Match Rate module comes after (Step 6). | The standard is the input to the match calculation; must exist before the calculation is formalized in code. |
| D2 | Two-layer model (Layer A exact / Layer B cited). | UniProt gives composition, not abundance. Naming the layers makes the uncertainty honest and publishable. |
| D3 | **Tier 1 = myofibrillar proteins** is the primary standard. | Original scoping concept was muscle fiber; MPS literature measures myofibrillar synthesis separately; resistance training primarily drives the myofibrillar fraction. |
| D4 | **Tier 2 = sarcoplasmic proteins** is computed and reported as a sensitivity analysis, not folded into the primary standard. | Needed to compare against whole-tissue lab standards and to justify the scope with a number ("including sarcoplasmic changes the profile by X") rather than by assertion. Whether it is EAA-heavy is unknown until computed — no guessing. |
| D5 | Myosin light chains, MYBPC, and α-actinin are in Tier 1 from the first run. | Light chains are ~15% of myosin mass with a different composition; omitting them was a defect in the starting table. |
| D6 | Fiber-type-specific accessions are used, not proxies. | MYH1 (IIx), slow troponins, TPM3 etc. are all in UniProt. Proxying IIx with MYH2 was unnecessary and prevents per-fiber-type profiles. |
| D7 | Residue counts are the stored ground truth; both mass conventions are derived. | Residue-in-chain mass ≠ free amino acid mass (one H₂O). USDA food tables and lab AAA report free-AA g/100 g. Match Rate must use the free-AA convention to be consistent with the food data. |
| D8 | Keep the `in_master_molecule` / `in_triple_helix`-style segment-flag architecture from the collagen pipeline. | Mature vs precursor is a small effect for cytosolic muscle proteins (initiator Met, actin N-terminal processing, isoform choice) but the architecture is already proven and the collagen tier reuses it. |
| D9 | Layer B primary source = quantitative human proteomics (single-fiber, by fiber type; whole-muscle deep proteome). Classical biochemical fractionation values are the cross-check. | Proteomics gives human, fiber-type-resolved abundance. Classical fractionation gives direct mass measurement of the major structural proteins. Agreement between the two is itself a validation result. |
| D10 | Literature is researched in-thread (Step 3), not deferred as "verify later". | Public scrutiny standard. |
| D11 | Accession list (Step 1) is settled before mass fractions (Step 3). | Can't weight what hasn't been enumerated. |
| D12 | The starting 9-protein table is treated as unverified and is not an input to anything. | Provenance unknown; resembles a renormalized classical myofibrillar fractionation but cannot be reconstructed. |

---

## 5. Steps

Each step = one thread + one handoff doc. A step is done when its acceptance criteria are met and its outputs are committed.

### Step 0 — Repo scaffold and conventions
- **Goal:** Package skeleton, config schemas, citation schema, doc templates.
- **Deliverables:** Directory layout above; `.ini` schema documented in `docs/conventions.md`; `pyproject.toml`; empty test harness; `decisions.md` seeded from §4.
- **Size:** Small. Can be folded into the start of Step 1 or 2 if preferred.

### Step 1 — Accession list, Pass 1 (myofibrillar)
- **Goal:** The definitive, justified list of Tier 1 proteins with fiber-type isoforms, plus the drafted (unweighted) Tier 2 sarcoplasmic list.
- **Deliverables:** `config/accessions.ini` with per-entry justification; `config/segments.ini` processing decisions; isoform decisions (titin, MYH, troponin, tropomyosin families) documented.
- **Handoff:** `docs/handoffs/01_accession_list.md`

### Step 2 — Harvest and composition engine
- **Goal:** Generalized fetcher and the composition module.
- **Deliverables:** `fetch.py` (UniProt REST, MD5 verification, isoform support, feature table capture); `data/sequences.ini`; `composition.py` producing residue counts, residue-mass vector, free-AA-mass vector, molecular weight; unit tests against hand-verified proteins.
- **Note:** Live fetches run on a machine with network access. Offline development uses fixture sequences.

### Step 3 — Mass fractions (Layer B)
- **Goal:** Cited mass fraction of every Tier 1 (and Tier 2) protein, per fiber type (I, IIa, IIx).
- **Deliverables:** Downloaded supplementary tables in `data/literature/` with provenance notes; `config/mass_fractions/*.ini` with a citation per row; documented iBAQ→mass conversion (iBAQ × MW, normalized within tier); classical fractionation cross-check table; `config/fiber_mixes.ini` for named muscles (e.g., vastus lateralis, soleus).
- **Note:** Longest step. May split into 3a (literature acquisition and extraction) and 3b (table construction and reconciliation).

### Step 4 — Aggregation and uncertainty
- **Goal:** The standard itself, with ranges.
- **Deliverables:** `aggregate.py` (mass-fraction-weighted sum of composition vectors per fiber type and per muscle); `uncertainty.py` (Monte Carlo over Layer B fractions and fiber mixes); output tables in both mass conventions; distribution plots per amino acid; EAA subset tables.

### Step 5 — Validation against laboratory data
- **Goal:** Show where and why the sequence-derived standard differs from lab-sampled human muscle.
- **Deliverables:** Compiled lab AAA values for human skeletal muscle (cited); predicted-vs-measured figure; per-amino-acid attribution of deviations (Trp destruction, Asn/Gln deamidation, Cys/Met/Ser/Thr loss, non-protein nitrogen contributions to His etc.); Tier 1 vs Tier 1+2 comparison.

### Step 6 — Match Rate
- **Goal:** Formalize the Match Rate calculation in code against the new standard.
- **Deliverables:** Formula written out in `docs/methods.md`; `match.py`; USDA ingestion in the free-AA convention; Match Rate for every food in the database; re-scored reference foods (whey, pea, egg, steak, current blend) under old vs new standard.
- **Input needed from Anthony:** the current spreadsheet formula.

### Step 7 — Paper
- **Goal:** Methods paper.
- **Deliverables:** `docs/methods.md` assembled from per-step docs; figures from Steps 4/5; supplementary data = the config files themselves.

---

## 6. Conventions (to be formalized in Step 0)

**Config format:** `.ini` via `configparser`. One section per entity. Free-text `note` and `justification` keys allowed. Comments with `#`.

**Citation schema** (every literature-derived number):
```
value     = 0.431
unit      = mass_fraction_of_tier
source    = Author et al. YEAR, Journal Vol:pages, DOI
location  = Supplementary Table S3, column "iBAQ_typeI"
retrieved = 2026-09-XX
note      = optional — conversions applied, caveats
```

**Mass conventions:**
- `residue_mass` — in-chain residue mass (free AA minus 18.015 Da). Sums to protein MW.
- `free_aa_mass` — free amino acid mass. Sums to > protein MW. This is the USDA / lab AAA convention and the one Match Rate uses.
- Both reported. Ground truth is residue count.

**Accession identity:** `ACCESSION` or `ACCESSION-N` for a specific isoform. Sequence version recorded. MD5 recorded and checked against UniProt's published checksum.

---

## 7. Open Questions (carried forward, owned by the step that resolves them)

| Question | Resolved in |
|----------|-------------|
| Titin isoform: canonical Q8WZ42 vs skeletal N2A. | Step 1 |
| MYH4 (IIb): include? Human limb muscle does not express IIb at protein level in meaningful quantity. | Step 1 |
| Desmin, myomesins, obscurin, nebulin-related, other Z-disc/M-band proteins: Tier 1 or Tier 2? Need a written criterion for "myofibrillar". | Step 1 |
| Initiator Met and actin N-terminal processing — segment flags or ignore as negligible with a stated bound? | Step 1 → confirmed Step 2 |
| 3-methylhistidine: count as His (dietary precursor). Confirm and document. | Step 2 |
| Which proteomics datasets, and how to reconcile iBAQ with classical fractionation when they disagree. | Step 3 |
| Fiber-type proportions for named muscles — which source(s). | Step 3 |
| Which lab AAA datasets of human muscle to validate against. | Step 5 |
| Match Rate formula — EAA-only or all AA; normalization; basis. | Step 6 |

---

## 8. Decisions Log

Maintained in `docs/decisions.md`. Seeded from §4. Every subsequent decision made in a step thread is appended there with date, step, and rationale.

---

## 9. Thread Protocol

1. Open a new thread named for the step (e.g., "Step 1 — Accession list").
2. Paste the handoff doc as the first message.
3. Work only that step. Anything out of scope goes into the handoff's "Deferred / raised" section, not into the work.
4. On completion: update `decisions.md`, write the next step's handoff (or update the draft), commit.
5. Return to the planning thread only to re-plan, not to do work.
