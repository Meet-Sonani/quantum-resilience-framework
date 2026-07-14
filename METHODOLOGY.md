# Methodology

This document explains the reasoning behind quantum-resilience-framework's
scoring model — the *why*, not just the *what*. Anyone auditing the tool's
recommendations should be able to reconstruct these numbers by hand from this
document alone.

---

## 1. Classification: broken, weakened, safe, unknown

Every asset is classified by matching its name against known primitive
patterns:

- **Broken** — primitives relying on integer factorisation or the elliptic
  curve discrete logarithm problem (RSA, ECC, Diffie-Hellman, DSA/ECDSA,
  X25519, and so on). Shor's algorithm solves both problems in polynomial
  time on a sufficiently large fault-tolerant quantum computer. Once a CRQC
  exists, these primitives offer effectively zero security.
- **Weakened** — symmetric primitives (AES, ChaCha20) and hash-based
  constructions (SHA-2, SHA-3, HMAC). Grover's algorithm gives a quadratic
  speed-up against brute-force search, halving the *effective* security
  level (AES-128 behaves like a 64-bit cipher against a quantum adversary).
  This is a real degradation, not a full break — see Section 3 for why the
  scoring model treats it differently from "broken."
- **Safe** — primitives already standardised under FIPS 203/204/205
  (ML-KEM, ML-DSA, SLH-DSA). No known quantum algorithm threatens these.
- **Unknown** — the classifier did not recognise the primitive name, or (as
  with a bare Modbus/DNP3 link) there is no cryptographic primitive at all.
  This is deliberately *not* folded into "broken": telling an engineer their
  cleartext protocol is "broken by Shor's algorithm" would be actively
  misleading about the actual gap, which is architectural rather than
  cryptographic. See Section 4.

---

## 2. The Mosca theorem scoring engine

Mosca's theorem gives the core decision rule for Harvest-Now-Decrypt-Later
(HNDL) risk: act now if

```
x + y > z
```

where `x` is how long the protected data must stay confidential (in years),
`y` is how long migrating this specific asset will realistically take, and
`z` is the estimated number of years until a cryptographically relevant
quantum computer (CRQC) exists.

The framework turns this inequality into a bounded 0–10 urgency score rather
than a binary flag, since a real inventory needs relative ranking across many
assets, not just a yes/no per asset:

```
urgency = min(10, round(10 * (x + y) / z))
```

A raw score of 10 or higher means `x + y` already meets or exceeds `z` — the
Mosca inequality has triggered and migration should have started already.
The score is capped at 10 so that assets which have already breached the
threshold can still be ranked against each other by how far past it they
are, via the underlying raw value before capping.

`z` defaults to 15 years (the "moderate" CRQC estimate) but is configurable
per inventory or via `--crqc-horizon` on the CLI, to a conservative (10),
moderate (15), or pessimistic (20) estimate, or any other value the assessor
judges appropriate.

---

## 3. Why weakened assets are scored differently from broken ones

**This is the most important design decision in the scoring model, and it
was not part of the original specification — it was added after review.**

Running the Mosca formula unmodified on both broken and weakened assets
means an AES-128 key-size bump — a trivial configuration change — scores
identically to a full RSA-to-ML-KEM protocol migration, given the same `x`
and `y`. That conflates two genuinely different situations:

- A broken asset (RSA, ECC) offers **no security at all** once a CRQC
  exists. There is no partial credit — Shor's algorithm does not leave a
  reduced-but-functional security margin.
- A weakened asset (AES-128) still offers a real, if reduced, security
  margin under Grover's algorithm — a 2^64 work factor rather than 2^128.
  This is meaningfully weaker than intended, and worth fixing, but it is not
  equivalent to zero security.

The framework therefore applies a `WEAKENED_DAMPENING_FACTOR` of **0.5** to
the raw Mosca score for weakened assets only:

```
weakened_urgency = max(1, round(mosca_urgency(x, y, z) * 0.5))   # if raw > 0
```

**Why 0.5, and not lower:** a 2^64 work factor is not a permanent margin —
compute costs continue to fall, and treating a weakened asset as low
priority indefinitely would be its own mistake. Halving is a deliberately
conservative choice: it demotes weakened assets *relative to* broken ones
for the same inputs, without implying they can be safely ignored. The score
never dampens all the way to zero when the raw score is positive, for the
same reason — a weakened asset is never reported as fully safe.

**What this changes in practice:** in the healthcare IoT example inventory,
an AES-128-GCM asset with the same data-sensitivity and migration-timeline
values as a broken ECDH-P256 asset scores 5 instead of 10 — correctly
signalling "worth fixing, but not the fire to put out first."

---

## 4. Why "unknown" is not folded into "broken"

The ICS/SCADA example inventory includes an asset representing a bare
Modbus TCP link with no cryptographic layer at all. The classifier correctly
returns `unknown` for this — there is no primitive name to match against any
pattern, because there is no primitive.

An earlier version of the recommendation engine incorrectly reported this
case as *"broken by Shor's algorithm"*, inherited from a shared code path
with genuinely broken primitives. That is factually wrong and would mislead
a reader into thinking the gap is cryptographic (swap the algorithm) rather
than architectural (there is no cryptographic layer to swap — the protocol
itself needs a wrapping layer, a gateway, or a redesign). The recommendation
engine now gives `unknown` its own honest message that names the ambiguity
(no primitive in use, or an unrecognised name) and calls for manual review,
rather than attributing a cause that may not apply.

---

## 5. Sector modules add findings a generic score cannot

The Mosca score is necessarily generic — it has no notion of *why* a
particular migration might be blocked in practice. The sector modules exist
to add that context on top of the score, not to replace it:

- **Healthcare IoT** — flags long-lifecycle devices (implants, firmware with
  5–10 year update cycles) as needing migration scheduled well ahead of the
  CRQC horizon rather than reactively, and flags patient-data sensitivity
  windows of 10+ years as squarely in HNDL scope per NIST IR 8547.
- **ICS/SCADA** — flags legacy protocols with no native authentication
  (bare Modbus, bare DNP3) as needing protocol-level redesign rather than a
  primitive swap, and flags real-time control loops (typically sub-10ms
  latency budgets) as needing measured — not assumed — ML-DSA/ML-KEM timing
  on representative hardware before committing to a parameter set. DNP3
  Secure Authentication v5 is explicitly excluded from the "no native
  authentication" finding, since it is the secure variant of the protocol.
- **Financial services** — flags SWIFT key-exchange assets as needing
  confirmation that the replacement is deployed in ephemeral (not static)
  mode, since forward secrecy is a hard SWIFT requirement, and flags
  cardholder-data-environment assets as in scope for PCI DSS 4.0's
  cryptographic-agility requirement.

These are additive findings appended to `asset.blockers` — they never
override the urgency score itself, since a blocker is about *how* to
migrate, not *whether* the asset needs to.

---

## 6. What the LLM policy agent does and does not do

The classification, scoring, and recommendation engines are entirely
deterministic — the same inventory produces the same numbers every run. The
LLM policy agent (`policy_agent.py`) is a separate layer on top: it receives
the *already-processed* inventory (including the final urgency scores and
recommendations) and is asked to reason about sequencing and practical
trade-offs across the whole portfolio — which assets share a migration
dependency, what a realistic first-quarter plan looks like — rather than to
recompute or second-guess the numbers themselves.

This separation is deliberate. The numbers a compliance team would actually
rely on are never model-generated; only the narrative and sequencing
judgement around them is, and that judgement is always presented alongside
the deterministic figures it is reasoning over, never in place of them.

---

## 7. Known limitations

- `_security_level()` infers a NIST security level (1/3/5) from substrings in
  the primitive's name (e.g. "3072", "p-384"). This is a heuristic, not a
  parse of an authoritative key-size field, and inventories should confirm
  the inferred level matches intent for anything ambiguous.
- The CRQC horizon (`z`) is a single configurable number, not a probability
  distribution. Treating 15 years as a point estimate is a simplification —
  a more complete treatment would carry the conservative/moderate/pessimistic
  estimates through as a range and report a confidence-weighted score.
- Sector module detection is keyword-based on the free-text `location`
  field. This is intentionally simple and auditable, but it means an asset
  described in unexpected wording could miss a sector finding it should
  receive — the sector modules are a floor, not a substitute for expert
  review.
