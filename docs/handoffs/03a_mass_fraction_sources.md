# Handoff — Step 3a: Mass-Fraction Sources (Layer B, literature acquisition)

**Project:** Sequence-Derived Amino Acid Standard for Human Skeletal Muscle
**Plan:** `docs/00_project_plan.md`
**Depends on:** nothing hard. Can run in parallel with Step 1. The *row extraction* (which proteins to pull from each table) waits for `accessions.ini`; the *source acquisition and method decisions* do not.
**Feeds:** Step 3b (table construction), Step 4 (aggregation), Step 5 (validation)

---

## Goal

Identify, obtain, and document every literature dataset that will supply Layer B mass fractions, and settle the quantification-method question (how a proteomics intensity becomes a mass fraction) before any number is transcribed. Output is a `data/literature/` folder with the supplementary tables as downloaded, a provenance README, and a written method for iBAQ/TPA → mass fraction that Step 3b applies mechanically.

## Context you need

- D9: proteomics primary, classical fractionation cross-check. D10: research is done in-thread, not deferred.
- Layer B is the only source of uncertainty in the standard. The paper's credibility rests on this step being reproducible from the cited files.
- Everything below marked **verified** was confirmed against the publisher/PMC record in the planning thread on 2026-09-09. Everything marked **candidate** was not and must be confirmed in this thread before use.

## Correction carried from the planning thread

Deshmukh et al. 2015 (*Mol Cell Proteomics* 14:841) was cited in planning as a human deep muscle proteome. It is **mouse** (C57BL/6 triceps + C2C12). It is not a Layer B source. Logged here so the mistake is not repeated.

## The method question — resolve first

Proteomics papers report intensities in different units, and only some of them are comparable *across* proteins:

- **MaxLFQ / LFQ intensity** — normalized for comparing the *same* protein across samples. Not valid for computing what fraction of total protein a given protein is. Cannot be used directly for mass fractions.
- **iBAQ** (intensity ÷ number of theoretically observable tryptic peptides) — approximately proportional to molar abundance. Mass fraction of protein *i* within a set *S*:
  `w_i = iBAQ_i × MW_i / Σ_{j∈S} (iBAQ_j × MW_j)`
  MW comes from Layer A (`composition.py`), which closes the loop with our own sequences.
- **TPA (total protein approach, Wiśniewski)** — protein intensity ÷ summed intensity, interpreted directly as mass fraction of total protein. No MW needed.

Momenzadeh et al. 2023 (below) show why this matters in muscle specifically: with iBAQ, MYH4 came out at 0.3% of total MYH in human fibers; with MaxLFQ, 10%. The LFQ number is an artifact; the iBAQ number matches the biology (MYH4 is not meaningfully expressed in adult human limb muscle). Use that comparison as the citation for choosing iBAQ/TPA.

**Decision to record:** which of iBAQ×MW or TPA is primary. Recommendation: use whichever the chosen dataset provides natively; if both are computable, compute both and report the difference as part of Layer B uncertainty.

**Normalization scope:** mass fractions are normalized *within tier* (Σ Tier 1 = 1; Σ Tier 2 = 1 separately) so that the primary standard is a pure myofibrillar profile. The Tier 1 : Tier 2 ratio is a separate, separately cited number used only in the sensitivity analysis.

## Sources

### A. Human, fiber-type-resolved (primary Layer B)

| # | Source | Status | What it gives | What to check in-thread |
|---|--------|--------|---------------|-------------------------|
| A1 | Murgia M, Nogara L, Baraldo M, Reggiani C, Mann M, Schiaffino S. *Protein profile of fiber types in human skeletal muscle: a single-fiber proteomics study.* Skeletal Muscle 2021;11:24. DOI 10.1186/s13395-021-00279-0. PMC8561870. | **verified** | Human vastus lateralis, young adult males, single fibers ≥80 % pure for MYH7 / MYH2 / MYH1 → type 1 / 2A / 2X. >3800 proteins. Additional file "Dataset 1". | Whether Dataset 1 contains iBAQ or only LFQ. If LFQ only: locate the PRIDE accession (PXD…) and decide whether to reprocess, or use A3 for the cross-protein weights and A1 for fiber-type ratios. |
| A2 | Murgia M et al. *Single Muscle Fiber Proteomics Reveals Fiber-Type-Specific Features of Human Muscle Aging.* Cell Reports 2017. | **verified (existence)** | 152 fibers, 8 donors, type 1 vs 2A, young and old. Table S6 has fiber-type ratios. | Quant units in supplementary; whether 2X fibers are separated; which donors are young. Older dataset than A1 — likely secondary. |
| A3 | Momenzadeh A et al. *Complete Workflow for High Throughput Human Single Skeletal Muscle Fiber Proteomics.* 2023. PMC9980124 (bioRxiv 10.1101/2023.02.23.529600 → check for journal version). | **verified** | 53 human single fibers; iBAQ implemented explicitly; Table S2 = MYH isoform fractions by iBAQ, Table S3 = by MaxLFQ. | Journal of record and final DOI. Whether full per-protein iBAQ tables are in supplementary or only MYH fractions. Fiber-type assignment method. |
| A4 | Deshmukh AS, Steenberg DE, et al. *Deep muscle-proteomic analysis of freeze-dried human muscle biopsies reveals fiber type-specific adaptations to exercise training.* Nat Commun 2021;12:304. DOI 10.1038/s41467-020-20556-8. | **verified** | Pooled slow vs fast fibers, >4000 proteins, human vastus lateralis. | Quant units. Slow/fast only (no 2A/2X split) — useful as a two-class cross-check on A1. |

### B. Absolute quantification methods and muscle applications

| # | Source | Status | Use |
|---|--------|--------|-----|
| B1 | Wiśniewski JR. *Label-Free and Standard-Free Absolute Quantitative Proteomics Using the "Total Protein" and "Proteomic Ruler" Approaches.* Methods Enzymol 2017;585:49-60. DOI 10.1016/bs.mie.2016.10.002. | **verified** | Method citation for TPA. |
| B2 | Wiśniewski JR, Koepsell H, Gizak A, Rakus D. *Absolute protein quantification allows differentiation of cell-specific metabolic routes and functions.* Proteomics 2015;15:1316-25. | **verified** | TPA applied to tissues incl. red muscle fibers (mouse). Method support, not human data. |
| B3 | Rakus D, Gizak A, Deshmukh A, Wiśniewski JR. *Absolute quantitative profiling of the key metabolic pathways in slow and fast skeletal muscle.* J Proteome Res 2015;14:1400-11. | **verified (existence)** | TPA, slow vs fast muscle. **Species not confirmed — likely rodent.** If rodent, cross-check only. |
| B4 | Schwanhäusser B et al. 2011 (iBAQ origin, Nature 473:337). | candidate | Method citation for iBAQ. |

### C. Classical biochemical fractionation (cross-check)

| # | Source | Status | Use |
|---|--------|--------|-----|
| C1 | Pepe FA. *Macromolecular assembly of myosin* / myofibrillar protein sections, Handbook of Physiology, Skeletal Muscle (Suppl. 27), 1983. DOI 10.1002/cphy.cp100104. | **verified (existence)** | Review-level myofibrillar composition by band. Rabbit-dominated. |
| C2 | Yates LD, Greaser ML. *Quantitative determination of myosin and actin in rabbit skeletal muscle.* J Mol Biol 1983. | candidate | The commonly cited myosin ~43 % / actin ~22 % of myofibrillar protein. Confirm citation and extract the actual table with method. |
| C3 | Ohtsuki I, Maruyama K, Ebashi S. *Regulatory and cytoskeletal proteins of vertebrate skeletal muscle.* Adv Protein Chem 1986. | candidate | Tabulated myofibrillar protein percentages incl. titin, nebulin, tropomyosin, troponin, C-protein, α-actinin. |
| C4 | Elzinga M et al. PNAS 1973;70:2687. | **verified** | Not a mass-fraction source. Cited for actin's single 3-methylhistidine residue (Step 2 open question 3). |

### D. Tier 1 : Tier 2 ratio and fiber-type proportions (needed for Step 4/5, acquire here)

- Myofibrillar vs sarcoplasmic vs stromal protein fractions of whole muscle — candidate sources: classical meat-science / muscle-biochemistry fractionation (e.g., Lawrie; Goll et al.). Must be human or explicitly flagged as non-human.
- Fiber-type proportions for vastus lateralis and soleus — candidate: Johnson MA et al. 1973 (*J Neurol Sci*, autopsy study of 36 muscles) and later biopsy studies. Verify, extract table, note that MYH-based and ATPase-based typing differ.

## Tasks

1. Confirm every **candidate** row above or replace it. Add any better human fiber-type-resolved dataset found in the process (the field moved fast 2021–2025; search for single-fiber DIA studies with >1000 fibers from the Mann/Deshmukh groups and others).
2. For each retained source, download the supplementary file(s) into `data/literature/<firstauthor_year>/`, unchanged. Record in `data/literature/README.md`: citation, DOI, file name as published, download URL, retrieval date, SHA-256 of the file.
3. For each dataset, record: species, muscle, donor characteristics, fiber typing method and purity threshold, quantification units available per column, number of proteins, number of fibers/donors.
4. Write `docs/methods.md` section "Mass fraction derivation": the iBAQ×MW / TPA formulae, the within-tier normalization, the treatment of shared MYH peptides (see open questions), and the LFQ-is-not-cross-protein justification with the Momenzadeh comparison.
5. Decide primary vs cross-check role for each dataset and record in `decisions.md`.
6. Hand to 3b: the list of files, the column to use in each, and the formula.

## Deliverables

- `data/literature/*/` — supplementary tables as downloaded.
- `data/literature/README.md` — provenance per file.
- `docs/methods.md` — "Mass fraction derivation" section.
- `docs/decisions.md` — appended.
- `docs/handoffs/03b_mass_fraction_tables.md` — drafted.

## Acceptance criteria

- [ ] No candidate remains unconfirmed; each is either verified with DOI and file, or dropped with a reason.
- [ ] Every retained file has a SHA-256 and retrieval date in the README.
- [ ] Quant units per dataset are known and recorded; the primary dataset provides (or allows computing) a cross-protein-comparable quantity.
- [ ] The mass-fraction formula and normalization scope are written in methods.md.
- [ ] Species is recorded for every source; any non-human source is marked cross-check only.
- [ ] No mass fraction has been assigned to any protein yet. (That is 3b, after Step 1 closes.)

## Open questions this step must resolve

1. **A1 quant units.** iBAQ present, or LFQ only? Determines whether A3 or a reprocessing step is needed.
2. **Shared peptides among MYH1/MYH2/MYH4 and among MYL/TPM/TNN isoforms.** Razor-peptide assignment in MaxQuant can shift mass between isoforms. Decide: unique-peptide-only quantification for isoform families, or accept the dataset's protein-group assignment and document it.
3. **Giant proteins.** Titin and nebulin have thousands of theoretical peptides; iBAQ is sensitive to incomplete coverage of very large proteins. Check whether A1/A3 iBAQ for TTN and NEB are plausible against the classical ~10 % / ~5 % myofibrillar values (C2/C3). Disagreement here is the most likely place Layer B needs an explicit reconciliation rule.
4. **Which fibers count as "pure."** A1 uses ≥80 % of one MYH. Hybrid fibers are real in vivo; decide whether the per-fiber-type standard is defined on pure fibers (cleaner) with hybrids handled by the fiber-mix step.
5. **TPA vs iBAQ×MW as primary.** See method section.

## Explicitly out of scope

- Transcribing any mass fraction into config (3b).
- Anything about amino acid composition (Layer A).
- Aggregation, plots, Match Rate.

## Deferred / raised

_(fill in during the thread)_

## Handoff to Step 3b

_(fill in at completion)_
