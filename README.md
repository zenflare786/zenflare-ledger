# ZenFlare Ledger — a track record you don't have to trust us about

This repository is the public, tamper-evident record of every trading **signal**
and **resolved outcome** produced by [ZenFlare](https://zenflare.digital). Its
whole purpose is to let an outsider verify — without trusting ZenFlare, and
without trusting GitHub — that we made an exact prediction (strategy, direction,
stop, target, reasoning, timestamp) at a certain time, recorded what actually
happened, and never altered either after the fact.

If you have ever been shown a trading "track record" that could have been edited
after the results were known, this repository is the opposite of that.

## How to verify it yourself

You need only Python 3 (standard library — no installs):

```
python3 verify.py
```

It recomputes the entire hash chain from `ledger.jsonl` and confirms the result
matches the latest anchored head in `heads.log`. If it prints `OK`, the record is
internally consistent and matches what we publicly committed. If anyone had
changed, inserted, or deleted a past record, the chain would break and you would
see `FAIL`.

`verify.py` is a verbatim copy of the verification code ZenFlare runs internally,
and it imports nothing outside the Python standard library — read it; it's short.

## How it works

- **Each record is hashed** (SHA-256) over its exact content, and every record's
  hash includes the previous record's hash — a **hash chain**. Changing any past
  record changes every record after it, and the final "head" hash no longer
  matches what we published.
- **The head is anchored two ways, daily and right after each candidate trade
  resolves:**
  1. **git** — the head is committed here, so GitHub records when it was pushed.
  2. **OpenTimestamps** — the head is timestamped on the **Bitcoin blockchain**
     (the `.ots` proof files). This is *trustless*: anyone can verify the date
     against Bitcoin with `ots verify`, without trusting ZenFlare **or** GitHub.

Together, the git history and the Bitcoin timestamp prove a record existed by a
given date.

## The honesty epoch — read this

**Honesty epoch: `2026-06-15` (exact: `2026-06-15T21:08:00.383494+00:00`).**

Real-time anchoring — and therefore independent, trustless date-proof — begins at
the honesty epoch. Everything before it is backfill, and we say so plainly:

> **Records before the honesty epoch are PRE-ENGINE BACKFILL. Their content is
> hashed, but their timestamps were never anchored in real time and are only as
> trustworthy as the ZenFlare database. Independent, trustless date-proof begins
> at the honesty epoch and applies to every signal and outcome recorded after
> it.**

We will never claim we anchored history we didn't. `verify.py` prints how many
records are pre-engine backfill versus live (anchored), so you can see the line
for yourself.

## What this does *not* claim

- It does **not** prove the backfilled (pre-epoch) records were created at their
  stated times — only that they existed by the time we first anchored.
- It does **not** prove we recorded *every* prediction we could have. It proves
  that what we recorded has not been altered, deleted, or back-dated since it was
  anchored. The promotion-relevant stream (the gold candidate's signals and
  outcomes) is hashed in real time and anchored within minutes of each
  resolution, leaving no useful window to cherry-pick after the fact.
- It is **not** a claim that the strategy is good. Whether the strategy earns its
  promotion is decided separately, against criteria frozen before the results
  existed. This repository only makes the record **honest**.

## Files

| File | What it is |
|---|---|
| `ledger.jsonl` | One record per line, including the exact `canonical` bytes that were hashed. The source of truth you recompute over. |
| `heads.log` | Append-only. One line per anchoring run: timestamp, chain head hash, record count, and the OpenTimestamps proof path. |
| `*.ots` | OpenTimestamps proofs (Bitcoin-anchored) for the published heads. Verify with `ots verify`. |
| `verify.py` | The standalone, stdlib-only verifier. |

## Nothing here is financial advice

ZenFlare is research and education. No signals are provided or sold. This
repository is evidence of what was predicted and what happened — not a
recommendation to trade anything. Past results are not a promise of future
results.
