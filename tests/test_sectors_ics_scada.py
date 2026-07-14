from quantum_resilience_framework.models import AssetRole, CryptoAsset
from quantum_resilience_framework.sectors.ics_scada import ICSSCADAModule


def _asset(location: str) -> CryptoAsset:
    return CryptoAsset(
        asset_id="X", name="AES-128-CBC", role=AssetRole.SYMMETRIC_ENCRYPTION,
        location=location, data_sensitivity_years=5, migration_timeline_years=2,
    )


def test_bare_modbus_is_flagged_unauthenticated():
    asset = _asset("Modbus TCP link, RTU telemetry")
    ICSSCADAModule().apply(asset)
    assert any("no native cryptographic authentication" in b for b in asset.blockers)


def test_bare_dnp3_is_flagged_unauthenticated():
    asset = _asset("DNP3 link, substation telemetry")
    ICSSCADAModule().apply(asset)
    assert any("no native cryptographic authentication" in b for b in asset.blockers)


def test_dnp3_secure_authentication_v5_is_not_flagged_unauthenticated():
    asset = _asset("DNP3 Secure Authentication v5 payload encryption, substation gateway")
    ICSSCADAModule().apply(asset)
    assert not any("no native cryptographic authentication" in b for b in asset.blockers)


def test_real_time_control_loop_keyword_adds_latency_blocker():
    asset = _asset("PLC firmware signing, real-time control loop")
    ICSSCADAModule().apply(asset)
    assert any("latency budget" in b for b in asset.blockers)


def test_unrelated_location_adds_no_blockers():
    asset = _asset("Corporate IT file server backup encryption")
    ICSSCADAModule().apply(asset)
    assert asset.blockers == []
