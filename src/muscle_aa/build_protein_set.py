#!/usr/bin/env python3
"""
build_protein_set.py — generate config/accessions.ini and config/segments.ini.

Inputs
  config/protein_set_decisions.ini   HAND-WRITTEN. One section per entry: which
                                     gene, which isoform, which tier, compartment,
                                     fiber type, role, justification. Nothing else.
  data/uniprot_verification.ini      output of verify_accessions.py
  data/uniprot_raw/*.fasta           output of verify_accessions.py

Outputs (GENERATED — do not edit by hand; edit the decisions file and rebuild)
  config/accessions.ini              decisions + accession, length, versions, MD5
  config/segments.ini                processing flags derived from UniProt features
  outputs/protein_set/build_<stamp>.log

Every mechanical value (accession, length, sequence/entry version, MD5,
segment coordinates) comes from the UniProt data. No value is typed in.

Segment rule (mirrors docs/conventions.md):
  canonical entry:
    master range = the LAST "Chain" feature (UniProt lists intermediate forms
    first, e.g. ACTA1 chain 2-377 then 3-377). Residues outside it are
    in_master_molecule = false, one segment per contiguous span.
    No Chain feature -> whole sequence is master.
  isoform entry:
    UniProt gives features in canonical coordinates only. The isoform inherits
    the canonical's N-terminal removal iff its sequence is identical to the
    canonical over that removed span (checked from the two FASTAs). Otherwise
    the whole isoform is master. `processing = none` in the decisions file
    forces no processing; `processing = master:<start>-<end>` sets it explicitly.

Usage: python src/muscle_aa/build_protein_set.py [--check]
  --check   rebuild in memory and exit 1 if config/ differs from disk (used by tests)
"""

from __future__ import annotations

import argparse
import configparser
import io
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DECISIONS = ROOT / "config" / "protein_set_decisions.ini"
VERIFICATION = ROOT / "data" / "uniprot_verification.ini"
RAW = ROOT / "data" / "uniprot_raw"
OUT_ACC = ROOT / "config" / "accessions.ini"
OUT_SEG = ROOT / "config" / "segments.ini"
LOG_DIR = ROOT / "outputs" / "protein_set"

FETCHED_TIERS = {"1", "2"}


# ------------------------------------------------------------ helpers ----
def read_ini(path: Path) -> configparser.ConfigParser:
    c = configparser.ConfigParser(interpolation=None)
    c.optionxform = str
    raw = path.read_bytes()
    try:
        c.read_string(raw.decode("utf-8"))
    except UnicodeDecodeError:
        c.read_string(raw.decode("cp1252"))
    return c


def read_fasta(path: Path) -> str:
    return "".join(l.strip() for l in path.read_text(encoding="utf-8").splitlines()
                   if not l.startswith(">"))


def parse_features(sec) -> list[tuple[str, int, int, str]]:
    out = []
    for k, v in sec.items():
        if not k.startswith("feature_"):
            continue
        parts = [p.strip() for p in v.split("|")]
        if len(parts) < 3 or "-" not in parts[1]:
            continue
        a, b = parts[1].split("-")
        out.append((parts[0], int(a), int(b), parts[2]))
    return out


def isoform_record(sec, iso_id: str) -> tuple[int, str]:
    n = int(sec.get("isoform_count", "0"))
    for i in range(1, n + 1):
        if iso_id in sec.get(f"isoform_{i}_ids", "").split(","):
            return int(sec[f"isoform_{i}_length"]), sec[f"isoform_{i}_md5_local"]
    raise KeyError(f"isoform {iso_id} not in verification data")


def identical_prefix(a: str, b: str) -> int:
    n = 0
    while n < min(len(a), len(b)) and a[n] == b[n]:
        n += 1
    return n


# ------------------------------------------------------------ segments ----
def segments_for(ident: str, length: int, master: tuple[int, int] | None,
                 removed_notes: dict[tuple[int, int], str], note_all: str) -> list[dict]:
    """Return segment dicts tiling 1..length. master=None -> whole chain."""
    if master is None:
        return [{"name": f"{ident}.chain", "start": 1, "end": length, "master": True, "note": note_all}]
    ms, me = master
    segs = []
    if ms > 1:
        # split the N-terminal removed region into the spans UniProt names
        spans = sorted(s for s in removed_notes if s[1] < ms) or [(1, ms - 1)]
        cur = 1
        for (a, b) in spans:
            if a > cur:  # unnamed gap
                segs.append({"name": f"{ident}.nterm_{cur}_{a-1}", "start": cur, "end": a - 1, "master": False,
                             "note": "removed: outside the mature chain per UniProt FT CHAIN; no named feature"})
            segs.append({"name": f"{ident}." + ("met1" if (a, b) == (1, 1) else f"nterm_{a}_{b}"),
                         "start": a, "end": b, "master": False, "note": removed_notes.get((a, b), "removed")})
            cur = b + 1
        if cur < ms:
            segs.append({"name": f"{ident}.nterm_{cur}_{ms-1}", "start": cur, "end": ms - 1, "master": False,
                         "note": "removed: between named N-terminal feature and mature chain start per UniProt FT CHAIN"})
    segs.append({"name": f"{ident}.chain", "start": ms, "end": me, "master": True,
                 "note": f"Mature chain (UniProt FT CHAIN {ms}-{me})"})
    if me < length:
        segs.append({"name": f"{ident}.cterm_{me+1}_{length}", "start": me + 1, "end": length, "master": False,
                     "note": "removed: C-terminal to the mature chain per UniProt FT CHAIN"})
    return segs


def canonical_processing(feats):
    chains = [f for f in feats if f[0] == "Chain"]
    master = (chains[-1][1], chains[-1][2]) if chains else None
    removed = {}
    for typ, a, b, desc in feats:
        if typ == "Initiator methionine":
            removed[(a, b)] = f"Initiator methionine, {desc.lower() or 'removed'} (UniProt FT INIT_MET {a})"
        elif typ in ("Propeptide", "Signal", "Transit peptide"):
            removed[(a, b)] = f"{typ} {a}-{b}: {desc} (UniProt feature)"
    return master, removed


# ---------------------------------------------------------------- build ----
def build(dec: configparser.ConfigParser, ver: configparser.ConfigParser, raw: Path,
          stamp: str, log: list[str]):
    release = next((ver[g]["uniprot_release"] for g in ver.sections() if "uniprot_release" in ver[g]), "?")
    verified = next((ver[g]["retrieved"] for g in ver.sections() if "retrieved" in ver[g]), "?")

    acc_lines = [f"""# ============================================================
#  accessions.ini — Layer A protein set        *** GENERATED FILE ***
#  Built {stamp} by src/muscle_aa/build_protein_set.py from
#     config/protein_set_decisions.ini   (hand-written decisions)
#     data/uniprot_verification.ini      (UniProt release {release}, retrieved {verified})
#  Do not edit. Change the decisions file and rebuild.
#
#  tier:        1 myofibrillar (primary) | 2 sarcoplasmic (sensitivity)
#               3 ECM/stromal (recorded, not fetched) | excluded (recorded, reason given)
#  isoform:     canonical | <UniProt isoform id>
#  seq_version: UniProt sequence version of the ENTRY (isoforms carry none)
#  md5_kind:    uniprot_published (canonical, verified match) |
#               computed_from_isoform_fasta
# ============================================================
"""]
    seg_lines = [f"""# ============================================================
#  segments.ini — processing flags               *** GENERATED FILE ***
#  Built {stamp} by src/muscle_aa/build_protein_set.py from UniProt
#  feature annotations in data/uniprot_verification.ini (release {release}).
#  Do not edit. Rule: see build_protein_set.py docstring / docs/conventions.md.
#  Coordinates 1-indexed inclusive on the fetched sequence for the isoform
#  named in accessions.ini. master set = in_master_molecule true; metabolic = all.
# ============================================================
"""]
    tier_headers = {"1": "Tier 1: myofibrillar", "2": "Tier 2: sarcoplasmic (draft; no weights)",
                    "3": "Tier 3: recorded, not fetched", "excluded": "Excluded: recorded, not fetched"}
    last_tier = None
    n_false = 0

    for name in dec.sections():
        d = dec[name]
        gene = d["gene"]
        iso = d.get("isoform", "canonical").strip()
        tier = d["tier"].strip()
        if gene not in ver or not ver[gene].get("accession"):
            raise SystemExit(f"[{name}] gene {gene} not resolved in verification data — run verify_accessions.py")
        v = ver[gene]
        acc = v["accession"]
        if iso == "canonical":
            ident, length, md5, md5_kind = acc, int(v["length"]), v["md5_published"], "uniprot_published"
        else:
            if not iso.startswith(acc + "-"):
                raise SystemExit(f"[{name}] isoform {iso} does not belong to {acc}")
            length, md5 = isoform_record(v, iso)
            ident, md5_kind = iso, "computed_from_isoform_fasta"

        if tier != last_tier:
            acc_lines.append(f"# ---------------- {tier_headers.get(tier, tier)} ----------------\n")
            if tier in FETCHED_TIERS:
                seg_lines.append(f"# ---------------- {tier_headers[tier]} ----------------\n")
            last_tier = tier

        acc_lines.append("\n".join([
            f"[{name}]",
            f"gene          = {gene}",
            f"accession     = {acc}",
            f"isoform       = {iso}",
            f"seq_version   = {v['seq_version']}",
            f"entry_version = {v['entry_version']}",
            f"length        = {length}",
            f"md5           = {md5}",
            f"md5_kind      = {md5_kind}",
            f"reviewed      = {'true' if 'reviewed' in v['entry_type'] else 'false'}",
            f"tier          = {tier}",
            f"compartment   = {d['compartment']}",
            f"fiber_type    = {d['fiber_type']}",
            f"role          = {d['role']}",
            f"justification = {d['justification']}",
            f"verified      = {v['retrieved']}",
            "",
        ]))

        if tier not in FETCHED_TIERS:
            continue

        # ---- segments ----
        feats = parse_features(v)
        master, removed = canonical_processing(feats)
        override = d.get("processing", "").strip()
        if iso == "canonical":
            segs = segments_for(ident, length, master, removed,
                                "no processing; no INIT_MET/PROPEP/SIGNAL/CHAIN feature annotated; Met1 retained per UniProt")
        else:
            can_seq = read_fasta(raw / f"{acc}.fasta")
            iso_seq = read_fasta(raw / f"{iso}.fasta")
            if len(iso_seq) != length:
                raise SystemExit(f"[{name}] {iso}.fasta length {len(iso_seq)} != verified {length}")
            if override == "none" or master is None:
                segs = segments_for(ident, length, None, {},
                                    f"no processing on {acc}; whole isoform {iso} is master")
            elif override.startswith("master:"):
                a, b = (int(x) for x in override.split(":")[1].split("-"))
                segs = segments_for(ident, length, (a, b), {}, "")
                for s in segs:
                    if not s["master"]:
                        s["note"] = f"removed per explicit `processing` override in protein_set_decisions.ini"
            else:
                pre = identical_prefix(can_seq, iso_seq)
                removed_end = master[0] - 1
                if removed_end > 0 and pre >= removed_end:
                    segs = segments_for(ident, length, (master[0], length), removed,
                                        "")
                    for s in segs:
                        if not s["master"]:
                            s["note"] += (f"; inherited from canonical {acc}: isoform identical over "
                                          f"residues 1-{pre} (removed span 1-{removed_end})")
                    log.append(f"  {name}: {iso} inherits canonical N-terminal processing 1-{removed_end} "
                               f"(identical prefix {pre} aa)")
                else:
                    segs = segments_for(ident, length, None, {},
                                        f"no inherited processing: isoform identical to canonical only over 1-{pre}, "
                                        f"removed span is 1-{removed_end}")
                    log.append(f"  {name}: {iso} — whole chain master (prefix {pre}, removed span 1-{removed_end})")

        # tiling check
        segs.sort(key=lambda s: s["start"])
        assert segs[0]["start"] == 1 and segs[-1]["end"] == length, (name, segs)
        for a_, b_ in zip(segs, segs[1:]):
            assert b_["start"] == a_["end"] + 1, (name, a_, b_)

        seg_lines.append(f"# {name} — {d['role']}")
        for s in segs:
            if not s["master"]:
                n_false += 1
            seg_lines.append("\n".join([
                f"[{s['name']}]",
                f"start              = {s['start']}",
                f"end                = {s['end']}",
                f"in_master_molecule = {'true' if s['master'] else 'false'}",
                f"note               = {s['note']}",
                "",
            ]))
        seg_lines.append("")

    log.append(f"  entries: {len(dec.sections())}; segments flagged false: {n_false}")
    return "\n".join(acc_lines), "\n".join(seg_lines)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="compare rebuild with files on disk; exit 1 if different")
    args = ap.parse_args()

    for p in (DECISIONS, VERIFICATION):
        if not p.exists():
            print(f"missing {p}", file=sys.stderr)
            return 2
    dec, ver = read_ini(DECISIONS), read_ini(VERIFICATION)
    stamp = datetime.now().strftime("%Y-%m-%dT%H%M")
    log: list[str] = [f"# build_protein_set.py run {stamp}"]
    acc_txt, seg_txt = build(dec, ver, RAW, stamp, log)

    if args.check:
        def body(t: str) -> str:  # ignore the build timestamp line when comparing
            return "\n".join(l for l in t.splitlines() if not l.startswith("#  Built "))
        same = (OUT_ACC.exists() and body(OUT_ACC.read_text(encoding="utf-8")) == body(acc_txt)
                and OUT_SEG.exists() and body(OUT_SEG.read_text(encoding="utf-8")) == body(seg_txt))
        print("config is current" if same else "config is STALE — run build_protein_set.py")
        return 0 if same else 1

    OUT_ACC.write_text(acc_txt, encoding="utf-8")
    OUT_SEG.write_text(seg_txt, encoding="utf-8")
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    log.append(f"  wrote {OUT_ACC}\n  wrote {OUT_SEG}")
    (LOG_DIR / f"build_{stamp}.log").write_text("\n".join(log) + "\n", encoding="utf-8")
    print("\n".join(log))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
