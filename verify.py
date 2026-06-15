#!/usr/bin/env python3
"""
ZenFlare ledger verifier — STANDALONE, dependency-free (Python standard library
only). Anyone can run this against the published files to confirm the ZenFlare
track record is internally consistent and matches the latest anchored head:

    python3 verify.py            # verifies ledger.jsonl against heads.log here
    python3 verify.py <dir>      # verify files in another directory

What it does, with zero trust in ZenFlare:
  1. For every record in ledger.jsonl, recompute SHA-256 over the exact
     `canonical` bytes that were hashed, then the chained record hash
     SHA-256(prev_hash || payload_hash).
  2. Confirm each record links to the previous one (a hash chain): altering or
     removing any past record breaks every record after it.
  3. Confirm the recomputed head equals the latest head in heads.log — the value
     that was committed to git and timestamped on the Bitcoin blockchain via
     OpenTimestamps (the .ots proofs). Together those prove the record existed by
     a given date without trusting ZenFlare or GitHub.

Honesty epoch & backfill: records before the honesty epoch (printed below) are
PRE-ENGINE BACKFILL — their content is hashed, but their timestamps were never
anchored in real time and are only as trustworthy as ZenFlare's database.
Independent date-proof applies to records at/after the epoch. See README.md.

This file is a verbatim copy of the verification path in the ZenFlare codebase
(honesty/canonical.py). It imports nothing outside the standard library.
"""
import hashlib
import json
import os
import sys

GENESIS_PREV = "0" * 64


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def record_hash(prev_hash: str, payload_hash: str) -> str:
    return sha256_hex((prev_hash + payload_hash).encode("utf-8"))


def verify_chain(records):
    """records: list of dicts with canonical/prev_hash/record_hash in seq order.
    Returns (ok, head_hash, error)."""
    prev = GENESIS_PREV
    for i, r in enumerate(records):
        if r["prev_hash"] != prev:
            return (False, None, f"linkage break at index {i}: "
                                 f"prev_hash != prior record_hash")
        ph = sha256_hex(r["canonical"].encode("utf-8"))
        expected = record_hash(r["prev_hash"], ph)
        if expected != r["record_hash"]:
            return (False, None, f"hash mismatch at index {i}: "
                                 f"record content altered")
        prev = r["record_hash"]
    return (True, prev, None)


def _latest_head(heads_path):
    """Return (head_hash, raw_line) from the last non-empty heads.log line."""
    with open(heads_path, encoding="utf-8") as f:
        lines = [ln.strip() for ln in f if ln.strip()]
    if not lines:
        return None, None
    last = lines[-1]
    for field in last.split("\t"):
        if field.startswith("head="):
            return field[len("head="):], last
    return None, last


def main(argv):
    d = argv[1] if len(argv) > 1 else os.path.dirname(os.path.abspath(__file__))
    ledger_path = os.path.join(d, "ledger.jsonl")
    heads_path = os.path.join(d, "heads.log")

    try:
        with open(ledger_path, encoding="utf-8") as f:
            records = [json.loads(ln) for ln in f if ln.strip()]
    except (OSError, ValueError) as e:
        print(f"FAIL: cannot read ledger.jsonl: {e}")
        return 2
    records.sort(key=lambda r: r["seq"])

    ok, head, err = verify_chain(records)
    if not ok:
        print(f"FAIL: chain broken — {err}")
        return 1

    # honesty epoch + backfill stats, from the genesis record (first line)
    epoch = "(no genesis record)"
    if records and records[0].get("record_type") == "genesis":
        try:
            epoch = json.loads(records[0]["canonical"]).get("honesty_epoch", "?")
        except ValueError:
            epoch = "?"
    backfill = sum(1 for r in records if r.get("era") == "backfill")
    live = sum(1 for r in records if r.get("era") == "live")

    claimed, raw = _latest_head(heads_path)
    if claimed is None:
        print(f"OK: chain of {len(records)} records is internally consistent.")
        print(f"    recomputed head: {head}")
        print("    WARNING: no heads.log to compare against (unanchored).")
        return 0
    if claimed != head:
        print("FAIL: recomputed head does not match the latest anchored head.")
        print(f"    recomputed: {head}")
        print(f"    heads.log : {claimed}")
        return 1

    print(f"OK: {len(records)} records verified and match the anchored head.")
    print(f"    head           : {head}")
    print(f"    honesty epoch  : {epoch}")
    print(f"    records        : {backfill} pre-engine backfill (DB-trust only), "
          f"{live} live (anchored)")
    print(f"    latest anchor  : {raw}")
    print("    To prove the date independently, verify the matching .ots proof "
          "with OpenTimestamps (`ots verify`).")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
