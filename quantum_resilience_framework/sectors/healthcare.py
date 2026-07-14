"""
Healthcare IoT sector module.

Implantable and other long-lifecycle medical devices have firmware update
cycles of 5-10 years, which is itself a genuine Harvest-Now-Decrypt-Later
risk factor independent of which cryptographic primitive is in use.
"""

from .base import SectorModule
from ..models import CryptoAsset

_LONG_LIFECYCLE_KEYWORDS = ("implant", "pacemaker", "insulin", "firmware")


class HealthcareIoTModule(SectorModule):
    sector_key = "healthcare_iot"

    def apply(self, asset: CryptoAsset) -> None:
        location = asset.location.lower()

        if any(keyword in location for keyword in _LONG_LIFECYCLE_KEYWORDS):
            asset.blockers.append(
                "Long-lifecycle device: firmware update cycles of 5-10 years mean "
                "migration must be scheduled well ahead of the CRQC horizon rather "
                "than reactively - treat migration_timeline_years for this asset as "
                "a floor, not a target."
            )

        if asset.data_sensitivity_years >= 10:
            asset.blockers.append(
                "Patient data sensitivity window is 10 years or more - falls "
                "squarely in scope for Harvest-Now-Decrypt-Later per NIST IR 8547 "
                "guidance."
            )
