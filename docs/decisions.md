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

<!-- Step 3a decisions (D13–D23) were logged in `decisions_step3a_append.md` in the Step 3a thread.
     Append them here verbatim when that file is brought into the repo. Do not renumber. -->
