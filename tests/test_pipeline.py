import os

from quantum_resilience_framework.io import load_inventory
from quantum_resilience_framework.models import QuantumVulnerability
from quantum_resilience_framework.pipeline import process_inventory

EXAMPLES_DIR = os.path.join(os.path.dirname(__file__), "..", "examples")


def test_healthcare_inventory_end_to_end():
    inventory = load_inventory(os.path.join(EXAMPLES_DIR, "healthcare-iot-inventory.json"))
    process_inventory(inventory)

    assert len(inventory.assets) == 4

    ecdh_asset = next(a for a in inventory.assets if a.asset_id == "CL-01")
    assert ecdh_asset.vulnerability == QuantumVulnerability.BROKEN
    assert ecdh_asset.urgency_score == 10  # (20 + 6) / 15 * 10, capped at 10
    assert any("firmware update cycles" in b for b in ecdh_asset.blockers)

    aes_asset = next(a for a in inventory.assets if a.asset_id == "CL-03")
    assert aes_asset.vulnerability == QuantumVulnerability.WEAKENED
    assert aes_asset.urgency_score == 5  # dampened: raw 10, halved for WEAKENED
    assert "AES-256" in aes_asset.recommendation


def test_ics_scada_inventory_end_to_end():
    inventory = load_inventory(os.path.join(EXAMPLES_DIR, "ics-scada-inventory.json"))
    process_inventory(inventory)

    assert len(inventory.assets) == 4

    modbus_asset = next(a for a in inventory.assets if a.asset_id == "SS-01")
    assert modbus_asset.vulnerability == QuantumVulnerability.UNKNOWN
    assert any("no native cryptographic authentication" in b for b in modbus_asset.blockers)
    assert "Shor" not in modbus_asset.recommendation

    dnp3_sav5_asset = next(a for a in inventory.assets if a.asset_id == "SS-02")
    # DNP3 Secure Authentication v5 DOES provide native authentication - it
    # must not receive the generic "no native authentication" blocker.
    assert not any("no native cryptographic authentication" in b for b in dnp3_sav5_asset.blockers)

    plc_asset = next(a for a in inventory.assets if a.asset_id == "SS-03")
    assert any("Real-time control loop" in b for b in plc_asset.blockers)
    assert "ML-DSA" in plc_asset.recommendation


def test_financial_services_inventory_end_to_end():
    inventory = load_inventory(os.path.join(EXAMPLES_DIR, "financial-services-inventory.json"))
    process_inventory(inventory)

    assert len(inventory.assets) == 4

    swift_kex_asset = next(a for a in inventory.assets if a.asset_id == "FS-01")
    assert swift_kex_asset.vulnerability == QuantumVulnerability.BROKEN
    assert any("forward secrecy" in b for b in swift_kex_asset.blockers)

    pci_asset = next(a for a in inventory.assets if a.asset_id == "FS-03")
    assert any("PCI DSS 4.0" in b for b in pci_asset.blockers)

    already_adequate_asset = next(a for a in inventory.assets if a.asset_id == "FS-04")
    assert already_adequate_asset.vulnerability == QuantumVulnerability.WEAKENED
    assert "no key-size change is needed" in already_adequate_asset.recommendation
