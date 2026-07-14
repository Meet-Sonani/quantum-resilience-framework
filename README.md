# quantum-resilience-framework

[![Tests](https://github.com/Meet-Sonani/quantum-resilience-framework/actions/workflows/tests.yml/badge.svg)](https://github.com/Meet-Sonani/quantum-resilience-framework/actions)

Assess quantum vulnerability across a real cryptographic asset inventory and
produce a prioritised, explainable post-quantum migration report.

Given a JSON inventory of cryptographic primitives in use across a system —
TLS certificates, firmware signing keys, session encryption, and so on — this
framework classifies each asset by its exposure to a cryptographically
relevant quantum computer (CRQC), scores migration urgency using Mosca's
theorem, recommends the specific NIST FIPS 203/204/205 replacement, and
layers on sector-specific findings (healthcare IoT, ICS/SCADA, financial
services) that a generic score cannot capture on its own. An LLM policy
agent then reasons over the already-scored inventory to produce a
sequencing-aware migration briefing.

See [METHODOLOGY.md](METHODOLOGY.md) for the full reasoning behind every
scoring decision, including two design gaps that were found and fixed during
review (documented there rather than quietly patched, since the reasoning
itself is part of the point of this project).

---

## Why this exists

Harvest-Now-Decrypt-Later (HNDL) means data encrypted today with a
quantum-vulnerable primitive can be recorded now and decrypted later, once a
CRQC exists. Mosca's theorem gives the decision rule — migrate now if the
data's confidentiality window plus the migration timeline exceeds the CRQC
horizon — but applying that rule consistently across a real inventory of
dozens or hundreds of assets, each with different sensitivity, different
migration cost, and different deployment context, is where this becomes a
genuine engineering problem rather than a one-line equation.

---

## Quickstart

```bash
pip install -e .                    # core install
pip install -e ".[llm]"             # + the optional LLM policy agent
pip install -e ".[dev]"             # + pytest/hypothesis, needed to run the test suite
# or, all at once:
pip install -e ".[llm,dev]"

qrf examples/healthcare-iot-inventory.json --output report.md
```

This produces a markdown report ranking every asset by urgency, with its
classification, recommended replacement, and any sector-specific blockers.

To also generate an LLM-written policy briefing (requires `ANTHROPIC_API_KEY`
to be set):

```bash
qrf examples/healthcare-iot-inventory.json --policy-briefing
```

---

## How it works

```
JSON inventory
      │
      ▼
 classify()        → broken / weakened / safe / unknown, per asset
      │
      ▼
 score_asset()     → 0-10 urgency via the Mosca formula
      │                (weakened assets are dampened relative to
      │                 broken ones - see METHODOLOGY.md §3)
      ▼
 recommend()       → specific FIPS 203/204/205 replacement + parameter set
      │
      ▼
 sector module     → additive blockers (healthcare_iot / ics_scada /
      │                financial_services), if the asset is tagged
      ▼
 generate_report()  → prioritised markdown report
      │
      ▼
 policy_agent (optional) → LLM sequencing briefing over the scored inventory
```

The classification → scoring → recommendation → sector pipeline is entirely
deterministic: the same inventory produces the same numbers on every run.
The LLM layer is additive and opt-in — it reasons about sequencing and
trade-offs on top of those numbers, never in place of them.

---

## Example inventories

Three realistic sample inventories are included under `examples/`, each
exercising a different sector module:

- **`healthcare-iot-inventory.json`** — an implantable pacemaker telemetry
  system. Demonstrates long-lifecycle device blockers and HNDL risk from
  20-year data sensitivity windows.
- **`ics-scada-inventory.json`** — a substation automation network.
  Demonstrates the "no native authentication" protocol gap (bare Modbus),
  correctly *not* flagging DNP3 Secure Authentication v5 as unauthenticated,
  and the real-time control loop latency blocker.
- **`financial-services-inventory.json`** — a cross-border payments
  platform. Demonstrates the SWIFT forward-secrecy check, PCI DSS 4.0 scope
  flagging, and an asset (AES-256-GCM) that is already at an adequate key
  size and correctly recommended for no change.

Run any of them through the CLI to see the full pipeline end to end.

---

## Project layout

```
quantum_resilience_framework/
  models.py          CryptoAsset / Inventory dataclasses
  classify.py         broken / weakened / safe / unknown classification
  scoring.py           Mosca urgency engine
  recommendations.py   NIST FIPS 203/204/205 replacement mapping
  sectors/             healthcare_iot, ics_scada, financial_services modules
  policy_agent.py       LLM policy reasoning agent (Anthropic API)
  pipeline.py           wires classify -> score -> recommend -> sector
  report.py             markdown report generation
  cli.py                the `qrf` command
examples/               three sample inventories
tests/                  33 tests covering every module above
METHODOLOGY.md          full scoring rationale and known limitations
```

---

## Testing

Requires the `dev` extra (`pip install -e ".[dev]"`) for pytest and hypothesis.

```bash
pytest tests/ -v
```

33 tests, all passing, covering classification edge cases (including a
regex-boundary bug found and fixed during development), the Mosca formula
and its weakened-asset dampening, every recommendation branch, all three
sector modules, and the LLM policy agent (via an injected fake client — no
network calls in the test suite).

---

## Standalone by design

This project has no dependency on any other repository. It is a complete,
self-contained package: install it, run it, test it, read it, on its own.