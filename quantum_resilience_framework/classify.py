"""
Classification engine: maps a raw algorithm name to a QuantumVulnerability.

Matching is pattern-based on normalised algorithm names rather than an exact
lookup table, since inventories will contain free-text variants such as
"RSA-2048", "rsa2048", "RSA (2048-bit)". Safe (already-PQC) patterns are
checked first so that names such as "ML-DSA-65" are never mistaken for the
broken "DSA" they replace.
"""

import re

from .models import QuantumVulnerability


def _word(fragment: str) -> str:
    """
    Build a pattern that matches `fragment` as a standalone token, tolerant of
    a trailing key-size digit run (e.g. "rsa4096", "aes256") but not of it
    being embedded inside another word (e.g. "mlrsa" should not match "rsa").
    """
    return rf"(?<![a-zA-Z])({fragment})(?![a-zA-Z])"


_SAFE_PATTERNS = [
    _word("ml-?kem"), _word("ml-?dsa"), _word("slh-?dsa"),
    _word("kyber"), _word("dilithium"), _word(r"sphincs\+?"),
    _word("falcon"), _word("frodo-?kem"),
]

_BROKEN_PATTERNS = [
    _word("rsa"), _word("dsa"), _word("ecdsa"), _word("ecdh"),
    _word("x25519"), _word("x448"), _word("ed25519"), _word("ed448"),
    _word("ecc"), _word(r"elliptic.?curve"), _word(r"diffie.?hellman"), _word("dh"),
    _word("p-?256"), _word("p-?384"), _word("p-?521"),
]

_WEAKENED_PATTERNS = [
    _word("aes"), _word("chacha20"), _word("salsa20"),
    _word("sha-?2"), _word("sha-?3"), _word("sha-?256"), _word("sha-?384"), _word("sha-?512"),
    _word("hmac"), _word("blake2"), _word("blake3"),
]


def classify(name: str) -> QuantumVulnerability:
    """Classify a cryptographic primitive by name into broken/weakened/safe/unknown."""
    normalised = name.strip().lower()

    for pattern in _SAFE_PATTERNS:
        if re.search(pattern, normalised):
            return QuantumVulnerability.SAFE

    for pattern in _BROKEN_PATTERNS:
        if re.search(pattern, normalised):
            return QuantumVulnerability.BROKEN

    for pattern in _WEAKENED_PATTERNS:
        if re.search(pattern, normalised):
            return QuantumVulnerability.WEAKENED

    return QuantumVulnerability.UNKNOWN
