# Decisions Log

Seeded 2026-09-10 from `00_project_plan.md` §4. Every subsequent decision is appended with date, step, and rationale. Nothing is deleted; reversals are new entries that reference the original.

| # | Date | Step | Decision | Rationale |
|---|------|------|----------|-----------|
| D1 | 2026-09-09 | plan | Standard is built first; Match Rate module comes after (Step 6). | The standard is the input to the match calculation; must exist before the calculation is formalized in code. |
| D2 | 2026-09-09 | plan | Two-layer model (Layer A exact / Layer B cited). | UniProt gives composition, not abundance. Naming the layers makes the uncertainty honest and publishable. |
| D3 | 2026-09-09 | plan | Tier 1 = myofibrillar proteins is the primary standard. | Original scoping concept was muscle fiber; MPS literature measures myofibrillar synthesis separately; resistance training primarily drives the myofibrillar fraction. |
| D4 | 2026-09-09 | plan | Tier 2 = sarcoplasmic proteins is computed and reported as a sensitivity analysis, not folded into the primary standard. | Needed to compare against whole-tissue lab standards and to justify scope with a number. Whether it is EAA-heavy is unknown until computed. |
| D5 | 2026-09-09 | plan | Myosin light chains, MYBPC, and α-actinin are in Tier 1 from the first run. | Light chains are ~15% of myosin mass with a different composition; omitting them was a defect in the starting table. |
| D6 | 2026-09-09 | plan | Fiber-type-specific accessions are used, not proxies. | MYH1, slow troponins, TPM3 etc. are all in UniProt. Proxying prevents per-fiber-type profiles. |
| D7 | 2026-09-09 | plan | Residue counts are the stored ground truth; both mass conventions are derived. | Residue-in-chain mass ≠ free AA mass. USDA and lab AAA report free-AA g/100 g; Match Rate must use that convention. |
| D8 | 2026-09-09 | plan | Keep the `in_master_molecule` segment-flag architecture from the collagen pipeline. | Small effect for muscle proteins, but the architecture is proven and the collagen tier reuses it. |
| D9 | 2026-09-09 | plan | Layer B primary source = quantitative human proteomics; classical biochemical fractionation is the cross-check. | Proteomics gives human, fiber-type-resolved abundance. Fractionation gives direct mass measurement of major structural proteins. Agreement is itself a validation result. |
| D10 | 2026-09-09 | plan | Literature is researched in-thread (Step 3), not deferred as "verify later". | Public scrutiny standard. |
| D11 | 2026-09-09 | plan | Accession list (Step 1) is settled before mass fractions (Step 3). | Can't weight what hasn't been enumerated. |
| D12 | 2026-09-09 | plan | The starting 9-protein table is treated as unverified and is not an input to anything. | Provenance unknown; resembles a renormalized classical fractionation but cannot be reconstructed. |

| D24 | 2026-09-10 | 1 | Myofibrillar inclusion criterion adopted as written in methods.md § Protein set definition. Abundance is not a criterion. | Keeps the list principled rather than pre-truncated; Layer B decides contribution, which may round to zero. |
| D25 | 2026-09-10 | 1 | Accessions are resolved by UniProt gene-name query (reviewed, human), never by a remembered accession. Seed accessions are used only to flag mismatch. | Caught one wrong seed (TMOD4) and one renamed symbol (MYLPF→MYL11) in the first run. |
| D26 | 2026-09-10 | 1 | Isoform selection rule: retain UniProt canonical unless UniProt isoform names, tissue annotation, VSP features, or cited primary literature identify a different adult-skeletal-muscle form. | Canonical is a curatorial choice, not a tissue claim; titin's canonical is a meta-transcript. |
| D27 | 2026-09-10 | 1 | Titin = Q8WZ42-4 (isoform 4, 'Soleus', N2A; 33,445 aa). | UniProt tissue annotation. Composition Δ ≤0.10 pp vs canonical; length Δ −905 aa affects MW in Layer B. |
| D28 | 2026-09-10 | 1 | MYL1 carried as two entries: MLC1f (P05976-1) and MLC3f (P05976-2). | Distinct proteins from alternative promoters, both stoichiometric on fast myosin; composition Δ up to 4.7 pp (Ala, Pro). Step 3 assigns separate fractions; shared-peptide caveat raised. |
| D29 | 2026-09-10 | 1 | Myomesin-1 = P52179-2 (1589 aa). | Canonical contains the 96-aa EH exon (836–931, VSP_035663), embryonic-heart specific (Agarkova et al. JBC 2000;275:10256). |
| D30 | 2026-09-10 | 1 | CapZ β = P47756-1 (277 aa, β1). | β1 is the Z-disc muscle isoform; β1/β2 differ only in the C-terminal tail (Schafer et al. JCB 1994;127:453; Hart et al. JCB 1999;147:1287). UniProt's displayed 272-aa canonical is β2. |
| D31 | 2026-09-10 | 1 | Nebulin, TPM1/2/3, TNNT1, TNNT3, TNNI2, MYBPC1, ACTN2, MYH2, OBSCN, MYOT, LDB3, CSRP3, TMOD1/4, CAPZA2: canonical isoform. | Alternates are fragments, same-length variants, non-muscle forms, fetal forms, or unnamed variants unresolvable by proteomic protein groups; composition Δ <1 pp in every case checked. |
| D32 | 2026-09-10 | 1 | MYH4 excluded; recorded in accessions.ini with tier = excluded. | 0.3 % of total MYH by iBAQ in human single fibers (Momenzadeh et al. 2023, Table S2). |
| D33 | 2026-09-10 | 1 | All 13 borderline sarcomeric candidates (MYOM1/2, OBSCN, MYOT, LDB3, CSRP3, MYOZ1/2, TMOD1/4, CAPZA1/2, CAPZB) → Tier 1. DES → Tier 3 (raised, not modelled). | Per D24 criterion: each is a sarcomeric lattice constituent; desmin is not. |
| D34 | 2026-09-10 | 1 | N-terminal processing follows UniProt feature annotation exactly; no N-end-rule inference. Modelled via segment flags; primary standard = mature (master) set; metabolic set reported; tier-level delta printed in Step 4. | Flags cost nothing (D8). Largest within-protein shift is −0.59 pp Met (TNNC2); actin Cys2 −0.26 pp. Excluding by assumption would replace a number with an assertion. |
| D35 | 2026-09-10 | 1 | Fiber-type assignment uses UniProt tissue annotation where present, defining isoform relationships otherwise, and 'all' where a protein is present in more than one type at differing levels. | Level differences are Layer B's job. |
| D36 | 2026-09-10 | 1 | Tier 2 drafted with canonical isoforms, provisional; isoform choice (esp. PKM M1/M2) and membership confirmed in Step 3 against abundance ranking. | Tier 2 is a sensitivity analysis; no weights assigned in Step 1 per handoff scope. |

| D37 | 2026-09-10 | 1 | `accessions.ini` and `segments.ini` are generated by `build_protein_set.py` from `protein_set_decisions.ini` (hand-written: gene, isoform, tier, compartment, fiber type, justification only) plus the UniProt verification data. Hand edits to the generated files are forbidden; `pytest` enforces it. | A transcription error (MYL11 given MYL1's length and MD5) was caught only by cross-checking; removing the transcription step removes the error class. The human layer is the decision, not the number. |

<!-- Step 3a decisions (D13–D23) were logged in `decisions_step3a_append.md` in the Step 3a thread.
     Append them here verbatim when that file is brought into the repo. Do not renumber. -->
