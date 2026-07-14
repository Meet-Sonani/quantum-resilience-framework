from quantum_resilience_framework.models import AssetRole, QuantumVulnerability
from quantum_resilience_framework.recommendations import recommend


def test_broken_key_exchange_recommends_ml_kem():
    text = recommend("RSA-2048", AssetRole.KEY_EXCHANGE, QuantumVulnerability.BROKEN)
    assert "ML-KEM-512" in text
    assert "FIPS 203" in text


def test_broken_high_security_key_exchange_recommends_ml_kem_1024():
    text = recommend("ECDH-P521", AssetRole.KEY_EXCHANGE, QuantumVulnerability.BROKEN)
    assert "ML-KEM-1024" in text


def test_broken_signature_recommends_ml_dsa_and_slh_dsa_backup():
    text = recommend("ECDSA-P256", AssetRole.SIGNATURE, QuantumVulnerability.BROKEN)
    assert "ML-DSA-44" in text
    assert "SLH-DSA-SHA2-128s" in text
    assert "FIPS 204" in text


def test_weakened_symmetric_recommends_key_size_increase():
    text = recommend("AES-128-GCM", AssetRole.SYMMETRIC_ENCRYPTION, QuantumVulnerability.WEAKENED)
    assert "AES-256" in text


def test_weakened_symmetric_already_at_256_needs_no_change():
    text = recommend("AES-256-GCM", AssetRole.SYMMETRIC_ENCRYPTION, QuantumVulnerability.WEAKENED)
    assert "no key-size change is needed" in text


def test_unknown_classification_does_not_blame_shor():
    text = recommend("None - cleartext Modbus TCP", AssetRole.OTHER, QuantumVulnerability.UNKNOWN)
    assert "Shor" not in text
    assert "not recognised" in text


def test_safe_primitive_needs_no_migration():
    text = recommend("ML-KEM-768", AssetRole.KEY_EXCHANGE, QuantumVulnerability.SAFE)
    assert "No migration required" in text
