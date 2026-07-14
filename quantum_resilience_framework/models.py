"""
Data models for the quantum-resilience-framework asset inventory.

An inventory is a JSON document listing every cryptographic primitive in use
across a system. Each asset carries enough context (data sensitivity window,
migration timeline, deployment sector) for the scoring engine to reason about
urgency without external lookups.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class QuantumVulnerability(str, Enum):
    """Classification of a primitive's exposure to a cryptographically relevant quantum computer (CRQC)."""
    BROKEN = "broken"       # fully broken by Shor's algorithm (RSA, ECC, DH, DSA)
    WEAKENED = "weakened"   # security level halved by Grover's algorithm (AES, SHA, HMAC)
    SAFE = "safe"           # already a NIST PQC standard (ML-KEM, ML-DSA, SLH-DSA)
    UNKNOWN = "unknown"     # primitive not recognised - flagged for manual review


class AssetRole(str, Enum):
    KEY_EXCHANGE = "key_exchange"
    SIGNATURE = "signature"
    SYMMETRIC_ENCRYPTION = "symmetric_encryption"
    HASH = "hash"
    MAC = "mac"
    OTHER = "other"


@dataclass
class CryptoAsset:
    """A single cryptographic primitive in use somewhere in the system."""
    asset_id: str
    name: str                       # e.g. "RSA-2048", "AES-128-GCM", "ECDSA-P256"
    role: AssetRole
    location: str                   # where it is used, e.g. "TLS handshake, API gateway"
    data_sensitivity_years: float    # x: how long the protected data must stay secret
    migration_timeline_years: float  # y: realistic years needed to migrate this asset
    sector: Optional[str] = None    # "healthcare_iot" | "ics_scada" | "financial_services" | None
    notes: str = ""

    # populated by the pipeline, not supplied in the input JSON
    vulnerability: Optional[QuantumVulnerability] = field(default=None, compare=False)
    urgency_score: Optional[int] = field(default=None, compare=False)
    recommendation: Optional[str] = field(default=None, compare=False)
    blockers: list[str] = field(default_factory=list, compare=False)


@dataclass
class Inventory:
    """A named collection of assets, e.g. one system or organisation."""
    system_name: str
    assets: list[CryptoAsset]
    crqc_horizon_years: float = 15.0  # z: default to the moderate estimate
