import pytest

from quantum_resilience_framework.models import AssetRole, CryptoAsset, QuantumVulnerability
from quantum_resilience_framework.scoring import WEAKENED_DAMPENING_FACTOR, mosca_urgency, score_asset


def test_mosca_urgency_below_threshold():
    # x=2, y=2, z=15 -> 10 * 4 / 15 = 2.67 -> rounds to 3
    assert mosca_urgency(2, 2, 15) == 3


def test_mosca_urgency_at_threshold():
    # x=10, y=5, z=15 -> exactly at the Mosca inequality boundary
    assert mosca_urgency(10, 5, 15) == 10


def test_mosca_urgency_caps_at_ten():
    # x=20, y=10, z=10 -> raw score of 30, capped at 10
    assert mosca_urgency(20, 10, 10) == 10


def test_mosca_urgency_rejects_non_positive_horizon():
    with pytest.raises(ValueError):
        mosca_urgency(5, 5, 0)


def test_safe_asset_scores_zero_regardless_of_inputs():
    asset = CryptoAsset(
        asset_id="A1", name="ML-KEM-768", role=AssetRole.KEY_EXCHANGE,
        location="test", data_sensitivity_years=25, migration_timeline_years=10,
    )
    asset.vulnerability = QuantumVulnerability.SAFE
    assert score_asset(asset, crqc_horizon_years=15) == 0


def test_broken_asset_uses_mosca_formula_unmodified():
    asset = CryptoAsset(
        asset_id="A2", name="RSA-2048", role=AssetRole.KEY_EXCHANGE,
        location="test", data_sensitivity_years=10, migration_timeline_years=5,
    )
    asset.vulnerability = QuantumVulnerability.BROKEN
    assert score_asset(asset, crqc_horizon_years=15) == 10


def test_weakened_asset_is_dampened_relative_to_an_equivalent_broken_asset():
    # Same x/y/z as the broken test above, but classified WEAKENED instead.
    weakened = CryptoAsset(
        asset_id="A3", name="AES-128-GCM", role=AssetRole.SYMMETRIC_ENCRYPTION,
        location="test", data_sensitivity_years=10, migration_timeline_years=5,
    )
    weakened.vulnerability = QuantumVulnerability.WEAKENED
    broken_equivalent_score = 10  # from test_broken_asset_uses_mosca_formula_unmodified

    weakened_score = score_asset(weakened, crqc_horizon_years=15)
    assert weakened_score == round(broken_equivalent_score * WEAKENED_DAMPENING_FACTOR)
    assert weakened_score < broken_equivalent_score


def test_weakened_asset_with_low_raw_urgency_never_dampens_to_zero():
    # A small but non-zero raw urgency should still surface as urgency 1,
    # not disappear entirely - a weakened asset is never fully "safe".
    weakened = CryptoAsset(
        asset_id="A4", name="SHA-256", role=AssetRole.HASH,
        location="test", data_sensitivity_years=1, migration_timeline_years=1,
    )
    weakened.vulnerability = QuantumVulnerability.WEAKENED
    assert score_asset(weakened, crqc_horizon_years=15) >= 1

