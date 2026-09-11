#!/usr/bin/env python3
"""
verify_accessions.py — Step 1 accession verification against UniProt REST.

Reads a candidates .ini (gene -> optional seed accession), resolves every
gene against UniProt (reviewed, human) by EXACT GENE NAME, and writes:

  data/uniprot_raw/<GENE>.json            raw search response (provenance)
  data/uniprot_raw/<ACCESSION[-N]>.fasta  every isoform sequence
  data/uniprot_verification.ini           one section per gene
  data/verify_accessions.log              everything printed, incl. flags
  stdout                                  summary table + flags

No biological judgement is made here. The seed accession is only used to
flag disagreement with what UniProt returns. Isoform CHOICE is made by a
human in config/accessions.ini after reading this output.

Usage:
    python verify_accessions.py [--candidates config/candidates_step1.ini]
                                [--outdir data] [--no-isoforms]
                                [--log data/verify_accessions.log]

Stdlib only. Tested against UniProt REST API (rest.uniprot.org).
"""

from __future__ import annotations

import argparse
import configparser
import hashlib
import json
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import date
from pathlib import Path

BASE = "https://rest.uniprot.org/uniprotkb"
UA = "uniprot-matchrate-standard/step1 (verify_accessions.py; stdlib urllib)"
PAUSE = 0.35  # seconds between requests — polite rate

# Return fields requested from the search endpoint.
FIELDS = ",".join([
    "accession", "id", "protein_name", "gene_primary", "gene_names",
    "length", "mass", "sequence", "sequence_version", "version",
    "date_sequence_modified", "cc_alternative_products", "cc_tissue_specificity",
    "ft_init_met", "ft_signal", "ft_propep", "ft_chain", "ft_transit",
    "ft_peptide",
])

PROCESSING_FEATURES = {
    "Initiator methionine", "Signal", "Propeptide", "Chain",
    "Transit peptide", "Peptide",
}


# ----------------------------------------------------------------- HTTP ----
def _get(url: str, retries: int = 4) -> tuple[bytes, dict]:
    """GET with simple backoff on 429/5xx. Returns (body, headers)."""
    last_err: Exception | None = None
    for attempt in range(retries):
        req = urllib.request.Request(url, headers={"User-Agent": UA,
                                                   "Accept": "*/*"})
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                return r.read(), dict(r.headers)
        except urllib.error.HTTPError as e:
            last_err = e
            if e.code in (429, 500, 502, 503, 504):
                time.sleep(2 ** attempt)
                continue
            body = ""
            try:
                body = e.read().decode(errors="replace")[:600]
            except Exception:  # noqa: BLE001
                pass
            raise RuntimeError(f"HTTP {e.code} for {url}\n  server said: {body}") from e
        except urllib.error.URLError as e:
            last_err = e
            time.sleep(2 ** attempt)
    raise RuntimeError(f"GET failed after {retries} attempts: {url}: {last_err}")


def search_gene(gene: str) -> tuple[dict, dict]:
    q = f"gene_exact:{gene} AND organism_id:9606 AND reviewed:true"
    url = (f"{BASE}/search?query={urllib.parse.quote(q)}"
           f"&format=json&fields={FIELDS}&size=25")
    body, headers = _get(url)
    time.sleep(PAUSE)
    return json.loads(body), headers


def fetch_fasta(acc: str) -> str:
    body, _ = _get(f"{BASE}/{acc}.fasta")
    time.sleep(PAUSE)
    lines = body.decode().splitlines()
    return "".join(l.strip() for l in lines if not l.startswith(">"))


def md5(seq: str) -> str:
    return hashlib.md5(seq.upper().encode()).hexdigest().upper()


# ------------------------------------------------------------ parsing ----
def _text(obj, *path, default=""):
    for p in path:
        if obj is None:
            return default
        obj = obj.get(p) if isinstance(obj, dict) else None
    return obj if obj is not None else default


def parse_entry(e: dict) -> dict:
    seq = e.get("sequence", {})
    audit = e.get("entryAudit", {})
    genes = e.get("genes", [])
    out = {
        "accession": e.get("primaryAccession", ""),
        "entry_name": e.get("uniProtkbId", ""),
        "entry_type": e.get("entryType", ""),
        "protein_name": _text(e, "proteinDescription", "recommendedName",
                              "fullName", "value"),
        "gene_primary": _text(genes[0], "geneName", "value") if genes else "",
        "length": seq.get("length", ""),
        "mol_weight_da": seq.get("molWeight", ""),
        "md5_published": (seq.get("md5") or "").upper(),
        "crc64_published": seq.get("crc64", ""),
        "sequence": seq.get("value", ""),
        "seq_version": audit.get("sequenceVersion", ""),
        "entry_version": audit.get("entryVersion", ""),
        "last_seq_update": audit.get("lastSequenceUpdateDate", ""),
        "features": [],
        "isoforms": [],
        "tissue_specificity": "",
    }
    for f in e.get("features", []):
        if f.get("type") in PROCESSING_FEATURES:
            loc = f.get("location", {})
            out["features"].append({
                "type": f["type"],
                "start": _text(loc, "start", "value"),
                "end": _text(loc, "end", "value"),
                "description": f.get("description", ""),
            })
    for c in e.get("comments", []):
        ct = c.get("commentType")
        if ct == "ALTERNATIVE PRODUCTS":
            for iso in c.get("isoforms", []):
                out["isoforms"].append({
                    "ids": iso.get("isoformIds", []),
                    "name": _text(iso, "name", "value"),
                    "synonyms": [s.get("value", "") for s in iso.get("synonyms", [])],
                    "status": iso.get("isoformSequenceStatus", ""),
                    "note": " ".join(t.get("value", "")
                                     for t in _text(iso, "note", "texts", default=[])),
                })
        elif ct == "TISSUE SPECIFICITY":
            out["tissue_specificity"] = " ".join(
                t.get("value", "") for t in c.get("texts", []))
    return out


# ---------------------------------------------------------------- main ----
class _Tee:
    """Write to stdout and a log file at once."""

    def __init__(self, path: Path):
        path.parent.mkdir(parents=True, exist_ok=True)
        self._f = open(path, "w", encoding="utf-8")
        self._out = sys.stdout

    def write(self, s: str) -> None:
        self._out.write(s)
        self._f.write(s)

    def flush(self) -> None:
        self._out.flush()
        self._f.flush()

    def close(self) -> None:
        self._f.close()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--candidates", default="config/candidates_step1.ini")
    ap.add_argument("--outdir", default="data")
    ap.add_argument("--no-isoforms", action="store_true",
                    help="skip per-isoform FASTA fetches")
    ap.add_argument("--log", default=None,
                    help="log file (default: <outdir>/verify_accessions.log)")
    args = ap.parse_args()

    log_path = Path(args.log) if args.log else Path(args.outdir) / "verify_accessions.log"
    tee = _Tee(log_path)
    sys.stdout = tee
    print(f"# verify_accessions.py run {date.today().isoformat()}")
    print(f"# candidates: {args.candidates}   outdir: {args.outdir}   log: {log_path}\n")

    cands = configparser.ConfigParser()
    cands.optionxform = str  # keep key case
    if not cands.read(args.candidates):
        print(f"cannot read {args.candidates}", file=sys.stderr)
        return 2

    outdir = Path(args.outdir)
    raw = outdir / "uniprot_raw"
    raw.mkdir(parents=True, exist_ok=True)

    report = configparser.ConfigParser()
    report.optionxform = str
    today = date.today().isoformat()
    release = ""
    flags: list[str] = []
    rows: list[tuple] = []

    for gene in cands.sections():
        seed = cands[gene].get("candidate", "").strip()
        group = cands[gene].get("group", "").strip()
        print(f"[{gene}] querying ...", flush=True)
        try:
            data, headers = search_gene(gene)
        except Exception as ex:  # noqa: BLE001
            flags.append(f"{gene}: NETWORK/HTTP ERROR {ex}")
            continue
        release = headers.get("X-UniProt-Release", release)
        rel_date = headers.get("X-UniProt-Release-Date", "")
        (raw / f"{gene}.json").write_text(json.dumps(data, indent=1))

        hits = [parse_entry(e) for e in data.get("results", [])]
        # Keep only entries whose PRIMARY gene name is the query; synonyms
        # matched by gene_exact are reported as 'other_hits'.
        primary = [h for h in hits if h["gene_primary"].upper() == gene.upper()]
        others = [h for h in hits if h not in primary]

        sec = f"{gene}"
        report.add_section(sec)
        r = report[sec]
        r["group"] = group
        r["seed_accession"] = seed
        r["retrieved"] = today
        r["uniprot_release"] = f"{release} ({rel_date})" if rel_date else release
        r["reviewed_hits_primary_gene"] = ",".join(h["accession"] for h in primary) or "NONE"
        r["reviewed_hits_synonym_only"] = ",".join(h["accession"] for h in others) or ""

        if not primary:
            flags.append(f"{gene}: NO reviewed human entry with primary gene {gene}")
            rows.append((gene, group, seed, "NONE", "", "", "", "NO-HIT"))
            continue
        if len(primary) > 1:
            flags.append(f"{gene}: {len(primary)} reviewed entries with primary "
                         f"gene {gene}: {[h['accession'] for h in primary]} — decide")

        h = primary[0]
        acc = h["accession"]
        r["accession"] = acc
        r["entry_name"] = h["entry_name"]
        r["entry_type"] = h["entry_type"]
        r["protein_name"] = h["protein_name"]
        r["length"] = str(h["length"])
        r["mol_weight_da"] = str(h["mol_weight_da"])
        r["seq_version"] = str(h["seq_version"])
        r["entry_version"] = str(h["entry_version"])
        r["last_seq_update"] = h["last_seq_update"]
        r["md5_published"] = h["md5_published"]
        local = md5(h["sequence"])
        r["md5_local"] = local
        r["md5_match"] = str(local == h["md5_published"])
        r["seed_match"] = str(seed == "" or seed == acc)
        r["starts_with_met"] = str(h["sequence"][:1] == "M")
        (raw / f"{acc}.fasta").write_text(f">{acc}\n{h['sequence']}\n")

        if seed and seed != acc:
            flags.append(f"{gene}: seed {seed} != UniProt {acc}")
        if local != h["md5_published"]:
            flags.append(f"{gene}: MD5 MISMATCH {acc}")
        if h["sequence"][:1] != "M":
            flags.append(f"{gene}: sequence does not start with Met")

        # Processing features
        if h["features"]:
            for i, f in enumerate(h["features"], 1):
                r[f"feature_{i}"] = (f"{f['type']} | {f['start']}-{f['end']} | "
                                     f"{f['description']}")
        else:
            r["feature_1"] = "NONE — no processing features annotated"
        nontrivial = [f for f in h["features"] if f["type"] != "Chain"]
        r["processing_present"] = str(bool(nontrivial))
        if nontrivial:
            flags.append(f"{gene}: processing features "
                         f"{sorted({f['type'] for f in nontrivial})} — segments.ini")

        r["tissue_specificity"] = h["tissue_specificity"] or "(none annotated)"

        # Isoforms
        r["isoform_count"] = str(len(h["isoforms"]))
        for i, iso in enumerate(h["isoforms"], 1):
            ids = ",".join(iso["ids"])
            r[f"isoform_{i}_ids"] = ids
            r[f"isoform_{i}_name"] = iso["name"]
            r[f"isoform_{i}_synonyms"] = ", ".join(iso["synonyms"])
            r[f"isoform_{i}_status"] = iso["status"]
            r[f"isoform_{i}_note"] = iso["note"]
            if args.no_isoforms or not iso["ids"]:
                continue
            iso_id = iso["ids"][0]
            try:
                s = fetch_fasta(iso_id)
                (raw / f"{iso_id}.fasta").write_text(f">{iso_id}\n{s}\n")
                r[f"isoform_{i}_length"] = str(len(s))
                r[f"isoform_{i}_md5_local"] = md5(s)
                r[f"isoform_{i}_is_canonical"] = str(s == h["sequence"])
            except Exception as ex:  # noqa: BLE001
                r[f"isoform_{i}_length"] = f"FETCH FAILED: {ex}"
        if len(h["isoforms"]) > 1:
            flags.append(f"{gene}: {len(h['isoforms'])} isoforms — choose in accessions.ini")

        rows.append((gene, group, seed, acc, h["length"], h["seq_version"],
                     len(h["isoforms"]),
                     "ok" if r["seed_match"] == "True" else "SEED-MISMATCH"))

    outdir.mkdir(parents=True, exist_ok=True)
    with open(outdir / "uniprot_verification.ini", "w") as fh:
        fh.write(f"# Generated by verify_accessions.py on {today}\n"
                 f"# UniProt release {release}\n"
                 f"# Source: {BASE} — search by gene_exact + organism_id:9606 + reviewed:true\n"
                 f"# NOTHING in this file is a decision. See config/accessions.ini.\n\n")
        report.write(fh)

    # Summary
    print("\n{:<8} {:<10} {:<8} {:<8} {:>7} {:>4} {:>4}  {}".format(
        "gene", "group", "seed", "uniprot", "len", "sv", "iso", "status"))
    for row in rows:
        print("{:<8} {:<10} {:<8} {:<8} {:>7} {:>4} {:>4}  {}".format(*row))
    print(f"\nUniProt release: {release}")
    print(f"Wrote {outdir / 'uniprot_verification.ini'} and raw files under {raw}/")
    if flags:
        print("\nFLAGS (require a human decision or a fix):")
        for f in flags:
            print("  -", f)
    else:
        print("\nNo flags.")
    print(f"Log written to {log_path}")
    tee.flush()
    return 0


if __name__ == "__main__":
    sys.exit(main())