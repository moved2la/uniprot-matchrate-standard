# Methods

Written incrementally, one section per step. Becomes the paper's Methods.

## Protein set definition
_(Step 1 — criterion and isoform rationale to be inserted at step close)_

### Terminology: isoform versus paralog

The word "isoform" is used in two incompatible senses in the muscle literature, and this
work keeps them separate.

**Paralogs** are distinct genes encoding homologous proteins. MYH7, MYH2, MYH1 and MYH4
are four genes with four UniProt accessions (P12883, Q9UKX2, P12882, Q9Y623). The
literature calls these "myosin heavy chain isoforms"; here each is treated as a separate
protein with its own accession, sequence, and Layer B mass fraction (Decision D6).

**Splice isoforms** are distinct protein products of one gene, produced by alternative
splicing, alternative promoters, or alternative initiation. UniProt records them under a
single accession with a numeric suffix (Q8WZ42-1 … Q8WZ42-13 for titin). They share most
of their sequence and differ by inserted, skipped, or exchanged segments. The "canonical"
(Displayed) isoform is UniProt's curatorial choice for the entry — often the longest or
first characterized — and is not necessarily the form expressed in adult skeletal muscle;
titin's canonical is a meta-transcript containing every exon, which no fiber expresses.

Every Layer A entry therefore specifies both an accession (which gene) and an isoform
suffix (which splice product), and the isoform choice is a documented decision, not a
default. Where a single gene yields two proteins that both occupy the sarcomere
stoichiometrically — MYL1 producing MLC1f and MLC3f from alternative promoters — both are
carried as separate entries. Isoform differences are exact at Layer A (sequence) and
propagate to Layer B through molecular weight in the intensity-to-mass conversion.

## Sequence acquisition and composition calculation
_(Step 2)_

## Mass fraction derivation
_(Step 3)_

## Aggregation and uncertainty
_(Step 4)_

## Validation against laboratory data
_(Step 5)_

## Match Rate
_(Step 6)_
