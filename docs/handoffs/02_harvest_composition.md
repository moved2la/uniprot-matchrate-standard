# Handoff — Step 2: Harvest and Composition Engine

**Project:** Sequence-Derived Amino Acid Standard for Human Skeletal Muscle
**Plan:** `docs/00_project_plan.md`
**Depends on:** Step 1 (`config/accessions.ini`, `config/segments.ini`)
**Feeds:** Step 3 (needs molecular weights for iBAQ→mass), Step 4 (needs composition vectors)
**Status:** READY — Step 1 closed 2026-09-10; inputs filled in below.

---

## Goal

Two modules and one data file. `fetch.py` pulls every accession in `accessions.ini` from UniProt REST, verifies the sequence against UniProt's published checksum, captures the feature table, and writes `data/sequences.ini`. `composition.py` reads `sequences.ini` and `segments.ini` and produces, for each protein, the residue count vector (ground truth), the residue-mass vector, the free-amino-acid-mass vector, and the molecular weight — for both the master-molecule and metabolic segment sets. When this step is done, Layer A is complete: every number is either a sequence character count or derived from one by arithmetic against a cited mass table. No biology is decided in this step.

## Context you need

- Layer A is exact (D2). This step must not introduce any estimated quantity. The only external constants are amino acid masses, and those come from a cited table in config, not from code.
- Residue counts are ground truth; both mass conventions are derived (D7). The free-AA convention is what USDA and lab AAA use and what Match Rate will consume.
- The collagen pipeline already has a working fetcher (`fetch_sequences.py`, UniProt REST + MD5 + feature JSON → `.ini`) and a reader for segment flags. Generalize; don't rewrite from scratch.
- The working sandbox may have no network. Development and tests run against fixture sequences in `tests/fixtures/`. The live harvest runs on a machine with network and the resulting `sequences.ini` is committed.

## Decisions already made — do not reopen

- D2, D7, D8, D11.
- Step 1 decisions on isoforms and segment flags: read them from `accessions.ini` / `segments.ini` and `docs/decisions.md`. Do not second-guess an isoform choice here; if a fetch reveals a problem (e.g., isoform ID doesn't resolve), log it in "Deferred / raised" and use what resolves, flagged.

## Inputs

- `config/accessions.ini` — every section has `accession`, `isoform`, `seq_version`, `length`, `tier`, `fiber_type`.
- `config/segments.ini` — one or more `[ACCESSION.segment]` sections per accession with `start`, `end`, `in_master_molecule`.
- Collagen pipeline `fetch_sequences.py` and `collagen_stoich_model_v2.py` (project history) — reference implementations.

### Inputs from Step 1 (fill in at Step 1 close)

- Final accession count, Tier 1: **37** (36 genes; MYL1 carried as MLC1f + MLC3f). Tier 2: **15**. Skip `tier = excluded` (MYH4) and `tier = 3` (DES).
- Accessions using a non-canonical isoform ID: **Q8WZ42-4** (TTN), **P05976-2** (MYL1_MLC3f), **P52179-2** (MYOM1), **P47756-1** (CAPZB).
- `segments.ini` entries with `in_master_molecule = false`: **27** — one `.met1` segment on 26 entries, plus `P68133.cys2` (ACTA1 has three segments: met1, cys2, chain 3-377).
- Anything Step 1 flagged for Step 2: confirm MLC3f (P05976-2) initiator-Met feature from the isoform JSON; `accessions.ini` carries `md5_kind` to tell published vs computed checksums apart; build `fetch.py` from `verify_accessions.py`. See 01 handoff "Deferred / raised".

## Tasks

### A. `src/muscle_aa/fetch.py`

1. Read `config/accessions.ini`. For each entry build the UniProt identifier: `ACCESSION` for canonical, `ACCESSION-N` for a specific isoform.
2. Fetch from `rest.uniprot.org`:
   - Sequence: `/uniprotkb/{id}.fasta` (isoform IDs resolve here).
   - Entry JSON: `/uniprotkb/{accession}.json` — capture `sequence.md5Checksum`, `sequence.length`, `entryAudit.sequenceVersion`, `entryAudit.lastSequenceUpdateDate`, and the `features` array (Initiator methionine, Propeptide, Signal, Chain, Region, Modified residue).
   - Note: the JSON checksum is for the canonical sequence. For isoforms, compute MD5 of the fetched FASTA and record it; cross-check length against the isoform length in the JSON `comments` (ALTERNATIVE PRODUCTS) block.
3. Verify: computed MD5 of the fetched sequence == UniProt's published MD5 (canonical) or recorded isoform length matches (isoform). Verify `length` and `seq_version` match `accessions.ini`. **Any mismatch is a hard failure** — print what differed and exit non-zero. A stale `accessions.ini` is a Step 1 correction, not something the fetcher silently tolerates.
4. Write `data/sequences.ini` (schema below). Include a header with the fetch timestamp and the UniProt release (from the `X-UniProt-Release` response header if present).
5. Retries with backoff; polite rate (UniProt asks for reasonable request rates); `--only ACC` and `--dry-run` flags.
6. Non-standard letters (`B`, `Z`, `X`, `U`, `O`) in a fetched sequence: fail loudly. None are expected in these entries.

### B. `data/sequences.ini` schema

```ini
# Generated by fetch.py — DO NOT EDIT BY HAND
# fetched      = 2026-09-XXTHH:MM:SSZ
# uniprot_release = 2026_0X
# source       = https://rest.uniprot.org/uniprotkb/

[P12883]
gene              = MYH7
isoform_id        = P12883            ; or P12883-2 etc.
sequence          = MGDSEMAVFGAAAPYLRKSEKERLEAQ...
length            = 1935
seq_version       = 5
md5_uniprot       = <from JSON>
md5_computed      = <computed>
md5_match         = true
last_seq_update   = 2003-XX-XX
feature.initiator_methionine = 1-1
feature.chain                = 2-1935 ; Myosin-7
feature.region.0             = ...    ; as many as UniProt lists, description after ';'
```

Features are captured verbatim for audit. `composition.py` does **not** read features — it reads `segments.ini`, which Step 1 wrote by hand from those same features. The feature capture exists so a reviewer can check `segments.ini` against the source without leaving the repo.

### C. `config/aa_masses.ini`

The one biological constant table in Layer A. Average (not monoisotopic) masses, since composition is a bulk-mass quantity.

```ini
# Free amino acid average molecular masses, g/mol.
# source   = <cited — e.g., IUPAC / NIST WebBook / PubChem CID per amino acid>
# retrieved = 2026-09-XX
# residue_mass = free_mass - water ; water = 18.01528 (cite)
[G]
name      = Glycine
free_mass = 75.0666
cid       = 750
...
```

Twenty entries. Every value sourced. Record the water mass and its source. Do not type these from memory — pull each from the cited source in-thread.

### D. `src/muscle_aa/composition.py`

For each accession, for each segment set (`master` = segments with `in_master_molecule = true`; `metabolic` = all segments):

1. Concatenate the flagged segments' residues (slice the sequence string by `start`/`end`, 1-indexed inclusive — same convention as the collagen pipeline).
2. **Residue count vector** — `Counter` over the 20 letters. This is the stored ground truth.
3. **Residue-mass vector** — `count[aa] × residue_mass[aa]`. Sum + one water = protein MW.
4. **Free-AA-mass vector** — `count[aa] × free_mass[aa]`. Sum = MW + (n − 1) × water, where n = residue count. Use this identity as a unit test.
5. **Fractions** — each vector normalized to sum 1, in both conventions. Report as fraction and as g/100 g.
6. **Molecular weight** — from the residue-mass sum. Step 3 needs this for iBAQ→mass.
7. Output: `outputs/composition/<accession>_<master|metabolic>.csv` plus one combined table `outputs/composition/all.csv` with columns `accession, gene, tier, fiber_type, segment_set, n_residues, mw, <20 count columns>, <20 residue_frac columns>, <20 free_frac columns>`.
8. A `--check` mode that prints, per protein, the master vs metabolic difference in each fraction. For muscle proteins this should be tiny; print it anyway so the negligibility claim in the paper is a printed number, not an assertion.

### E. Tests (`tests/`)

- `test_masses.py` — 20 entries present; residue = free − water for every row; sums behave.
- `test_composition.py` — against fixtures:
  - A hand-computable synthetic sequence (e.g., `GGGAAAK`) with expected counts, MW, both vectors.
  - One real small protein (e.g., TNNC2 or MYL2 fixture) with MW cross-checked against ExPASy ProtParam for the same sequence. Record the ProtParam value and date in the test docstring.
  - The `(n − 1) × water` identity for every fixture.
  - Segment slicing: a fixture with a false-flagged N-terminal segment; master count = metabolic count − segment length.
- `test_fetch.py` — parses a saved FASTA and JSON fixture; MD5 verification passes; an altered fixture fails.
- No test touches the network.

### F. Documentation

- `docs/methods.md` — section "Sequence acquisition and composition calculation": endpoints, verification, mass table source, the two conventions with the water identity written out, 3-methylhistidine treatment (below).
- `docs/decisions.md` — append.

## Deliverables

- `src/muscle_aa/fetch.py`
- `src/muscle_aa/composition.py`
- `config/aa_masses.ini` (cited)
- `data/sequences.ini` (committed after a live run; MD5-verified)
- `outputs/composition/*.csv`
- `tests/fixtures/`, `tests/test_*.py`
- `docs/methods.md` section, `docs/decisions.md` appended

## Acceptance criteria

- [ ] `fetch.py` runs against every entry in `accessions.ini` and exits zero only when every MD5/length/version check passes.
- [ ] `data/sequences.ini` is committed, with fetch timestamp and UniProt release in the header.
- [ ] `aa_masses.ini` has 20 sourced entries and a sourced water mass; no value came from memory.
- [ ] `composition.py` produces both vectors, both segment sets, for every accession, and the water identity holds for every one.
- [ ] MW for at least one protein matches ExPASy ProtParam for the identical sequence (record the value).
- [ ] `--check` output committed showing master vs metabolic deltas.
- [ ] All tests pass offline.
- [ ] No mass fractions, tier weights, fiber-type mixes, or aggregated profiles appear anywhere in this step's outputs. Per-protein only.

## Open questions this step must resolve

1. **Mass table source.** One authoritative source for all 20 free masses (preferred) vs. per-CID from PubChem. Decide, cite, record.
2. **Cysteine in the free-AA convention.** Lab AAA typically reports cysteine as cysteine or cystine depending on method; USDA reports "cystine". For the standard, report as cysteine (free mass) and note the convention. Confirm and document — this becomes a Step 6 mapping issue when USDA columns are ingested.
3. **3-methylhistidine.** Actin and myosin heavy chain each carry one post-translationally methylated His. Count as His: dietary His is the precursor and the mass difference is negligible. Confirm and write one sentence in methods.
4. **Isoform checksum.** UniProt's JSON gives an MD5 only for the canonical sequence. Decide how isoform sequences are verified (length + spot-check against the isoform's FASTA header, plus stored computed MD5 for reproducibility) and document.
5. **Tryptophan and other hydrolysis-sensitive residues** — nothing to decide here (the sequence is exact), but note in methods that these are reported at full value, which is where the lab comparison in Step 5 will diverge.

## Explicitly out of scope

- Mass fractions, iBAQ, abundance — Step 3.
- Any aggregation across proteins, fiber types, or muscles — Step 4.
- Plots — Step 4.
- Hydroxylation, glycosylation, or any PTM mass adjustment — not relevant for muscle proteins; collagen tier handles its own.
- USDA ingestion, Match Rate — Step 6.
- Adding or removing proteins from the list — Step 1 correction; log and go back.

## Deferred / raised

_(fill in during the thread)_

## Handoff to Step 3

_(fill in at completion — path to `all.csv`, the MW column Step 3 should use for iBAQ×MW, any accession whose fetched length differed from Step 1's record and how it was resolved)_
