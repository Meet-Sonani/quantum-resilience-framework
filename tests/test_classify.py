from quantum_resilience_framework.classify import classify
from quantum_resilience_framework.models import QuantumVulnerability


def test_rsa_variants_are_broken():
    for name in ["RSA-2048", "rsa4096", "RSA (3072-bit)"]:
        assert classify(name) == QuantumVulnerability.BROKEN


def test_ecc_variants_are_broken():
    for name in ["ECDSA-P256", "ECDH-P384", "X25519", "Ed25519"]:
        assert classify(name) == QuantumVulnerability.BROKEN


def test_symmetric_and_hash_are_weakened():
    for name in ["AES-128-GCM", "AES-256", "SHA-256", "HMAC-SHA256", "ChaCha20-Poly1305"]:
        assert classify(name) == QuantumVulnerability.WEAKENED


def test_pqc_primitives_are_safe():
    for name in ["ML-KEM-768", "ML-DSA-65", "SLH-DSA-SHA2-128s"]:
        assert classify(name) == QuantumVulnerability.SAFE


def test_ml_dsa_is_not_misclassified_as_broken_dsa():
    # "dsa" is a substring of "ml-dsa" - safe patterns must win the ordering check
    assert classify("ML-DSA-44") == QuantumVulnerability.SAFE


def test_unrecognised_primitive_is_unknown():
    assert classify("FrobnicateCipher-9000") == QuantumVulnerability.UNKNOWN
