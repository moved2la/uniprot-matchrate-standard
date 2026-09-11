# Handoff — Step 1: Accession List, Pass 1 (Myofibrillar)

**Project:** Sequence-Derived Amino Acid Standard for Human Skeletal Muscle
**Plan:** `docs/00_project_plan.md`
**Depends on:** Step 0 (scaffold) — may be done at the start of this thread if not already
**Feeds:** Step 2 (harvest), Step 3 (mass fractions)

---

## Goal

Produce the definitive, per-entry-justified list of Tier 1 (myofibrillar) human skeletal muscle proteins, with fiber-type-specific isoforms, each mapped to a verified UniProt accession and a chosen sequence isoform. Draft the Tier 2 (sarcoplasmic) list without weighting it. Record the processing decisions (mature vs precursor) per protein. When this step is done, Step 2 can fetch every sequence without making a single biological judgement call, and Step 3 knows exactly which proteins it needs mass fractions for.

## Context you need

- We are building a two-layer standard (plan §3). This step defines the *set* of proteins in Layer A. It does not assign abundances — that is Step 3.
- Tier 1 = myofibrillar = the primary standard (D3). Tier 2 = sarcoplasmic = sensitivity analysis (D4). Tier 3 (collagen/ECM) already exists in the collagen pipeline and is out of scope here.
- The standard is reported per fiber type (I, IIa, IIx) and then mixed per muscle. That is only possible if fiber-type-specific isoforms are enumerated separately (D6).
- The 9-protein starting table from the planning thread is not an input (D12).
- Every accession in this document is a **candidate from memory** and must be verified against UniProt in-thread before it goes into `accessions.ini`. Verification = search UniProt by gene name + organism 9606, confirm reviewed (Swiss-Prot) entry, confirm the accession, record sequence version and length.

## Decisions already made — do not reopen

- D3, D4: Tier 1 primary / Tier 2 sensitivity.
- D5: MYL1, MYL2, MYL3, MYLPF, MYBPC1, MYBPC2, ACTN2, ACTN3 are in Tier 1.
- D6: fiber-type-specific accessions, no proxies.
- D8: segment-flag architecture retained from the collagen pipeline.
- D11: accessions before mass fractions. Do not start pulling abundance data in this thread.

## Inputs

- Collagen pipeline `segments.ini` format (in project history) — reuse its section/key style.
- UniProt REST (`rest.uniprot.org`) for verification. If the working machine has no network, verification is done manually on uniprot.org and recorded.

## Tasks

1. **Write the inclusion criterion for "myofibrillar."** One paragraph. Suggested basis: proteins that are structural components of the sarcomere (thick filament, thin filament, Z-disc, M-band, titin/nebulin scaffold), recovered in the myofibrillar fraction under standard differential extraction. This criterion decides the borderline cases in Task 4 and goes into `docs/methods.md` verbatim.
2. **Verify each Tier 1 candidate** (table below) against UniProt. Record accession, reviewed status, sequence length, sequence version, and the date checked.
3. **Choose the isoform for each entry** where UniProt lists more than one. Document why. Specific cases:
   - **TTN** — canonical Q8WZ42 is the full-length entry (~34,350 aa). Adult skeletal muscle expresses the N2A isoform. Decide: canonical, or the specific isoform ID (`Q8WZ42-N`). Record the choice and the length difference.
   - **NEB** — check for isoform variation; nebulin is alternatively spliced.
   - **TPM1/TPM2/TPM3** — skeletal (striated) isoforms specifically; several TPM entries have non-muscle splice variants.
   - **MYBPC1/2** — slow vs fast skeletal; confirm isoforms.
4. **Resolve the borderline entries** using the criterion from Task 1. For each: in Tier 1, in Tier 2, or excluded, with one line of justification.
5. **Decide fiber-type assignment** for every Tier 1 entry: `I`, `IIa`, `IIx`, or `all`. Where a protein is expressed in more than one fiber type but at different levels, assign `all` and leave the level to Step 3.
6. **Draft the Tier 2 sarcoplasmic candidate list.** Gene names and verified accessions only. No weights. Suggested starting set: CKM, ALDOA, GAPDH, PKM, ENO3, PGAM2, TPI1, PGK1, GPI, LDHA, MB, PVALB, CA3, PYGM, AK1. Confirm against a deep human muscle proteome abundance ranking in Step 3, not here.
7. **Record processing decisions** per Tier 1 protein in `config/segments.ini`:
   - Initiator methionine: removed or retained in the mature protein (UniProt "Initiator methionine" feature).
   - ACTA1: N-terminal processing (UniProt propeptide feature at the N-terminus). Flag the removed residues.
   - Any signal peptide or propeptide (expected: none for cytosolic proteins — confirm rather than assume).
   - Where processing is absent, say so explicitly with `in_master_molecule = true` for the whole chain, so Step 2 never has to infer.
8. **Write `config/accessions.ini`** in the schema below.
9. **Update `docs/decisions.md`** with every decision from Tasks 1, 3, 4, 5.
10. **Fill in the Handoff to Step 2** section at the bottom.

## Tier 1 candidate table (VERIFY EVERY ROW)

| Gene | Protein | Fiber type | Candidate accession | Notes / decision required |
|------|---------|-----------|---------------------|---------------------------|
| MYH7 | Myosin heavy chain, slow / type I | I | P12883 | — |
| MYH2 | Myosin heavy chain IIa | IIa | Q9UKX2 | — |
| MYH1 | Myosin heavy chain IIx | IIx | P12882 | Replaces the IIa-as-proxy approach. |
| MYH4 | Myosin heavy chain IIb | — | Q9Y623 | Decide: exclude. Not expressed at protein level in adult human limb muscle in meaningful quantity. Record justification with a source. |
| MYL1 | Myosin light chain 1/3, fast (MLC1f/MLC3f) | IIa, IIx | P05976 | Two isoforms (MLC1f, MLC3f) from one gene — decide whether to carry both. |
| MYLPF | Myosin regulatory light chain 2, fast | IIa, IIx | Q96A32 | — |
| MYL3 | Myosin light chain 3, slow (MLC1sa/b) | I | P08590 | — |
| MYL2 | Myosin regulatory light chain 2, slow/ventricular | I | P10916 | Shared with cardiac; confirm it is the slow skeletal RLC. |
| ACTA1 | Actin, alpha skeletal | all | P68133 | N-terminal processing — Task 7. |
| TTN | Titin | all | Q8WZ42 | Isoform decision — Task 3. |
| NEB | Nebulin | all | P20929 | Isoform check — Task 3. |
| TPM1 | Tropomyosin alpha-1 (fast) | IIa, IIx | P09493 | Skeletal isoform — Task 3. |
| TPM2 | Tropomyosin beta | all | P07951 | Expressed in both; level differs by fiber type. |
| TPM3 | Tropomyosin alpha-3 (slow) | I | P06753 | Skeletal isoform — Task 3. |
| TNNT1 | Troponin T, slow skeletal | I | P13805 | — |
| TNNT3 | Troponin T, fast skeletal | IIa, IIx | P45378 | — |
| TNNI1 | Troponin I, slow skeletal | I | P19237 | — |
| TNNI2 | Troponin I, fast skeletal | IIa, IIx | P48788 | — |
| TNNC1 | Troponin C, slow/cardiac | I | P63316 | — |
| TNNC2 | Troponin C, fast skeletal | IIa, IIx | P02585 | — |
| MYBPC1 | Myosin-binding protein C, slow | I | Q00872 | Isoform check — Task 3. |
| MYBPC2 | Myosin-binding protein C, fast | IIa, IIx | Q14324 | — |
| ACTN2 | Alpha-actinin-2 | all | P35609 | — |
| ACTN3 | Alpha-actinin-3 | IIa, IIx | Q08043 | Fast-fiber specific. Note common null allele (R577X) — population-level caveat for the paper, not a modelling decision. |

## Borderline candidates (resolve with the Task 1 criterion)

| Gene | Protein | Candidate accession | Question |
|------|---------|---------------------|----------|
| MYOM1 | Myomesin-1 | P52179 | M-band structural. Likely Tier 1. |
| MYOM2 | Myomesin-2 | P54296 | M-band, fast. Likely Tier 1. |
| DES | Desmin | P17661 | Intermediate filament linking Z-discs. Cytoskeletal, not sarcomeric. Tier 1 or 2? |
| OBSCN | Obscurin | Q5VST9 | Giant, low abundance. Probably negligible mass; decide on principle. |
| MYOT | Myotilin | Q9UBF9 | Z-disc. Low abundance. |
| LDB3 | ZASP/Cypher | O75112 | Z-disc. Low abundance. |
| CSRP3 | Muscle LIM protein | P50461 | Z-disc. Low abundance. |
| MYOZ1/2 | Myozenins | Q9NP98 / Q9NPC6 | Z-disc. Low abundance. |
| TMOD1/4 | Tropomodulins | P28289 / Q9NZR1 | Thin filament capping. Low abundance. |
| CAPZA/CAPZB | CapZ | — | Z-disc capping. Low abundance. |

A defensible position: include everything meeting the criterion regardless of abundance, and let Step 3 assign mass fractions that may round to ~0. That keeps the list principled rather than pre-truncated. Alternatively, set an explicit mass-fraction floor in Step 3 and note excluded proteins. Decide and record.

## Deliverables

- `config/accessions.ini` — schema:

```ini
# ============================================================
#  accessions.ini — Tier 1 / Tier 2 protein set
#  Every accession verified against UniProt on the date shown.
#  Fiber type: I | IIa | IIx | all
#  Tier: 1 = myofibrillar (primary standard)
#        2 = sarcoplasmic (sensitivity analysis)
# ============================================================

[MYH7]
accession     = P12883
isoform       = canonical
seq_version   = <from UniProt>
length        = <aa>
reviewed      = true
tier          = 1
compartment   = thick_filament
fiber_type    = I
role          = Myosin heavy chain, slow / type I
justification = Defining isoform of type I fibers; sarcomeric thick filament.
verified      = 2026-09-XX
```

- `config/segments.ini` — one section per accession, collagen-pipeline style, with `in_master_molecule` flags. For unprocessed proteins a single whole-chain section with `note = no processing; initiator Met <retained|removed> per UniProt`.
- `docs/decisions.md` — appended.
- `docs/methods.md` — section "Protein set definition" containing the Task 1 criterion and the isoform rationale.

## Acceptance criteria

- [ ] Every Tier 1 entry has a UniProt-verified reviewed accession, isoform choice, sequence version, length, and verification date.
- [ ] Every Tier 1 entry has a fiber-type assignment and a one-line justification.
- [ ] The myofibrillar inclusion criterion is written and every borderline candidate is resolved against it.
- [ ] MYH4 decision recorded with a source.
- [ ] Titin and nebulin isoform decisions recorded with length and rationale.
- [ ] `segments.ini` exists for every Tier 1 accession, including explicit "no processing" entries.
- [ ] Tier 2 candidates listed with verified accessions, no weights.
- [ ] No abundance or mass-fraction numbers appear anywhere in this step's outputs.
- [ ] `decisions.md` updated.

## Open questions this step must resolve

1. Myofibrillar inclusion criterion (Task 1).
2. Titin isoform: canonical vs N2A.
3. MYL1: carry MLC1f and MLC3f as separate entries, or one?
4. Borderline Z-disc / M-band proteins: include on principle, or apply an abundance floor later?
5. Initiator Met / ACTA1 N-terminus: model via segment flags (recommended — cost is nil) or state a negligibility bound.

## Explicitly out of scope

- Any mass fraction, iBAQ, or abundance data. (Step 3.)
- Fetching sequences. (Step 2.)
- Composition calculations of any kind, including "just checking" whether sarcoplasmic proteins are EAA-heavy. (Step 2 → Step 4.)
- Collagen / ECM tier.
- Match Rate formula.

## Deferred / raised

_(fill in during the thread)_

## Handoff to Step 2

_(fill in at completion — list the final accession count per tier, any accession where the canonical sequence should NOT be used, and any segments.ini entries Step 2 must handle specially)_
