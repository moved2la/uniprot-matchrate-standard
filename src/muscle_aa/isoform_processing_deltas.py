#!/usr/bin/env python3
"""
isoform_processing_deltas.py — Decision support for isoform and processing choices in the protein set. Reads what verify_accessions.py
wrote (data/uniprot_raw/*.json, *.fasta, data/uniprot_verification.ini) and
prints three things a human needs to close the isoform and processing
decisions:

  1. ISOFORM NOTES — UniProt's own text on each isoform (from the raw JSON),
     for genes where the choice isn't obvious from the name alone.
  2. ISOFORM DELTAS — residue-fraction (mol %) difference between two
     isoforms of the same gene, per amino acid. Exact, from sequence.
  3. PROCESSING DELTAS — for every entry with a removed Met / propeptide,
     mature chain vs full translation, per amino acid.

Residue FRACTIONS (count / total) only — no masses. Masses belong to the composition engine.
This script makes no decisions and writes nothing to config/.

Outputs (all under --outdir, default outputs/isoform_processing/):
  isoform_processing_deltas_<stamp>.txt     everything printed, one file per run
  isoform_deltas.csv           per-AA mol % for every compared isoform pair
  processing_deltas.csv        per-AA mol % full vs mature for every processed entry
  isoform_notes.txt            the verbatim UniProt isoform notes

Usage:  python src/muscle_aa/isoform_processing_deltas.py [--datadir data] [--outdir outputs/isoform_processing]
"""

from __future__ import annotations

import argparse
import configparser
import csv
import json
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path

AA = "ACDEFGHIKLMNPQRSTVWY"

# Genes whose isoform notes we want to read verbatim.
NOTE_GENES = ["TTN", "NEB", "MYL1", "TNNT3", "MYBPC1", "MYOM1", "CAPZB",
              "OBSCN", "LDB3", "TPM1", "TPM2", "TPM3"]

# (gene, isoform A, isoform B) pairs to compare. A = canonical/reference.
PAIRS = [
    ("TTN",   "Q8WZ42-1", "Q8WZ42-4"),   # canonical meta vs soleus/N2A
    ("NEB",   "P20929-2", "P20929-1"),   # displayed 8525 vs 6669 form
    ("MYL1",  "P05976-1", "P05976-2"),   # MLC1f vs MLC3f
    ("TNNT3", "P45378-1", "P45378-2"),   # Tnt1 vs Tnt3
    ("MYOM1", "P52179-1", "P52179-2"),
    ("CAPZB", "P47756-2", "P47756-1"),
    ("MYBPC1", "Q00872-1", "Q00872-4"),  # shortest-vs-longest span check
]


def read_fasta(p: Path) -> str:
    return "".join(l.strip() for l in p.read_text().splitlines()
                   if not l.startswith(">"))


def frac(seq: str) -> dict[str, float]:
    c = Counter(seq)
    n = len(seq)
    return {a: 100.0 * c.get(a, 0) / n for a in AA}


def diff_locus(a: str, b: str) -> str:
    """Common prefix/suffix lengths and the differing core, alignment-free."""
    pre = 0
    while pre < min(len(a), len(b)) and a[pre] == b[pre]:
        pre += 1
    suf = 0
    while (suf < min(len(a), len(b)) - pre) and a[-1 - suf] == b[-1 - suf]:
        suf += 1
    core_a, core_b = a[pre:len(a) - suf], b[pre:len(b) - suf]
    return (f"identical prefix {pre} aa, identical suffix {suf} aa; "
            f"A differs at {pre + 1}-{len(a) - suf} ({len(core_a)} aa), "
            f"B differs at {pre + 1}-{len(b) - suf} ({len(core_b)} aa)\n"
            f"      A core: {core_a[:60]}{'…' if len(core_a) > 60 else ''}\n"
            f"      B core: {core_b[:60]}{'…' if len(core_b) > 60 else ''}")


def print_delta(label_a: str, seq_a: str, label_b: str, seq_b: str) -> dict:
    print("    locus:", diff_locus(seq_a, seq_b))
    fa, fb = frac(seq_a), frac(seq_b)
    print(f"    {'aa':>3} {label_a[:14]:>14} {label_b[:14]:>14} {'delta(pp)':>10}")
    worst = ("", 0.0)
    for a in AA:
        d = fb[a] - fa[a]
        if abs(d) > abs(worst[1]):
            worst = (a, d)
        print(f"    {a:>3} {fa[a]:14.3f} {fb[a]:14.3f} {d:+10.3f}")
    print(f"    lengths {len(seq_a)} -> {len(seq_b)}  "
          f"(dlen {len(seq_b) - len(seq_a):+d}, {100 * (len(seq_b) - len(seq_a)) / len(seq_a):+.2f} %)"
          f"   largest per-AA shift: {worst[0]} {worst[1]:+.3f} pp\n")
    return {"a": fa, "b": fb, "len_a": len(seq_a), "len_b": len(seq_b)}


NOTES_BUF: list[str] = []


def _n(line: str) -> None:
    print(line)
    NOTES_BUF.append(line)


def isoform_notes(raw: Path, gene: str) -> None:
    p = raw / f"{gene}.json"
    if not p.exists():
        _n(f"  ({gene}: no raw json)")
        return
    data = json.loads(p.read_text(encoding="utf-8"))
    for e in data.get("results", []):
        if e.get("genes") and e["genes"][0].get("geneName", {}).get("value", "").upper() != gene.upper():
            continue
        for c in e.get("comments", []):
            if c.get("commentType") != "ALTERNATIVE PRODUCTS":
                continue
            ev = c.get("events", [])
            _n(f"  [{gene}] {e['primaryAccession']}  events={ev}")
            for t in c.get("note", {}).get("texts", []):
                _n(f"    comment-level note: {t.get('value')}")
            for iso in c.get("isoforms", []):
                ids = ",".join(iso.get("isoformIds", []))
                name = iso.get("name", {}).get("value", "")
                syn = ", ".join(s.get("value", "") for s in iso.get("synonyms", []))
                status = iso.get("isoformSequenceStatus", "")
                vsp = ",".join(iso.get("sequenceIds", []))
                _n(f"    {ids:<22} name={name!r:<8} syn={syn!r:<40} status={status:<14} VSP={vsp}")
                for t in iso.get("note", {}).get("texts", []):
                    _n(f"        note: {t.get('value')}")


class _Tee:
    def __init__(self, path: Path):
        path.parent.mkdir(parents=True, exist_ok=True)
        self._f = open(path, "w", encoding="utf-8")
        self._out = sys.stdout

    def write(self, t: str) -> None:
        self._out.write(t)
        self._f.write(t)

    def flush(self) -> None:
        self._out.flush()
        self._f.flush()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--datadir", default="data")
    ap.add_argument("--outdir", default="outputs/isoform_processing")
    args = ap.parse_args()
    data = Path(args.datadir)
    raw = data / "uniprot_raw"
    out = Path(args.outdir)
    out.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y-%m-%dT%H%M")
    sys.stdout = _Tee(out / f"isoform_processing_deltas_{stamp}.txt")
    print(f"# isoform_processing_deltas.py run {stamp}   datadir={data}   outdir={out}\n")

    ini = configparser.ConfigParser()
    ini.optionxform = str
    txt = (data / "uniprot_verification.ini").read_bytes()
    try:
        ini.read_string(txt.decode("utf-8"))
    except UnicodeDecodeError:
        ini.read_string(txt.decode("cp1252"))

    print("=" * 78)
    print("1. ISOFORM NOTES (verbatim from UniProt JSON)")
    print("=" * 78)
    for g in NOTE_GENES:
        isoform_notes(raw, g)
        if g in ini:
            for k, v in ini[g].items():
                if k.startswith("var_seq_"):
                    _n(f"    {v}")
        _n("")
    (out / "isoform_notes.txt").write_text("\n".join(NOTES_BUF) + "\n", encoding="utf-8")

    print("=" * 78)
    print("2. ISOFORM DELTAS (residue mol %, B minus A)")
    print("=" * 78)
    iso_rows = []
    for gene, a, b in PAIRS:
        pa, pb = raw / f"{a}.fasta", raw / f"{b}.fasta"
        if not pa.exists() or not pb.exists():
            print(f"  {gene}: missing {a if not pa.exists() else b}.fasta — skipped\n")
            continue
        print(f"  {gene}: {a} vs {b}")
        r = print_delta(a, read_fasta(pa), b, read_fasta(pb))
        for lab, key, n in ((a, "a", r["len_a"]), (b, "b", r["len_b"])):
            iso_rows.append([gene, lab, n] + [f"{r[key][x]:.4f}" for x in AA])
    with open(out / "isoform_deltas.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["gene", "isoform_id", "length"] + [f"{x}_molpct" for x in AA])
        w.writerows(iso_rows)

    print("=" * 78)
    print("3. PROCESSING DELTAS (mature chain vs full translation, mol %)")
    print("=" * 78)
    rows = []
    for gene in ini.sections():
        s = ini[gene]
        acc = s.get("accession", "")
        if not acc or s.get("processing_present", "False") != "True":
            continue
        feats = [v for k, v in s.items() if k.startswith("feature_")]
        # mature chain = the LAST Chain feature (UniProt lists intermediate
        # forms before the final one, e.g. ACTA1 2-377 then 3-377)
        chains = [f for f in feats if f.startswith("Chain")]
        if not chains:
            continue
        loc = chains[-1].split("|")[1].strip()
        start, end = (int(x) for x in loc.split("-"))
        full = read_fasta(raw / f"{acc}.fasta")
        mature = full[start - 1:end]
        ff, fm = frac(full), frac(mature)
        worst = max(AA, key=lambda a: abs(fm[a] - ff[a]))
        removed = full[:start - 1] + full[end:]
        rows.append((gene, acc, len(full), f"{start}-{end}", removed,
                     worst, fm[worst] - ff[worst], ff, fm))
    print(f"  {'gene':<8} {'acc':<8} {'len':>6} {'mature':>12} {'removed':<8} {'largest shift':>16}")
    for gene, acc, n, mat, rem, w, d, _, _ in sorted(rows, key=lambda r: -abs(r[6])):
        print(f"  {gene:<8} {acc:<8} {n:>6} {mat:>12} {rem:<8} {w} {d:+.3f} pp")
    with open(out / "processing_deltas.csv", "w", newline="", encoding="utf-8") as fh:
        wr = csv.writer(fh)
        wr.writerow(["gene", "accession", "segment_set", "length", "mature_range",
                     "removed_residues"] + [f"{x}_molpct" for x in AA])
        for gene, acc, n, mat, rem, _, _, ff, fm in rows:
            wr.writerow([gene, acc, "metabolic", n, mat, rem] + [f"{ff[x]:.4f}" for x in AA])
            wr.writerow([gene, acc, "master", n, mat, rem] + [f"{fm[x]:.4f}" for x in AA])
    print("\n  (pp = percentage points of residue mol fraction within that protein;"
          "\n   tier-level effect needs Layer B and is reported at aggregation)")
    print(f"\nWrote {out}/isoform_processing_deltas_{stamp}.txt, isoform_notes.txt, "
          f"isoform_deltas.csv, processing_deltas.csv")
    sys.stdout.flush()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
