"""
Financial services sector module.

PCI DSS 4.0 references cryptographic agility as a requirement, and SWIFT
messaging in particular depends on forward secrecy - a property that maps
onto the key-exchange side of a migration (ML-KEM in ephemeral mode), not
the signature side.
"""

from .base import SectorModule
from ..models import AssetRole, CryptoAsset


class FinancialServicesModule(SectorModule):
    sector_key = "financial_services"

    def apply(self, asset: CryptoAsset) -> None:
        location = asset.location.lower()

        if "swift" in location and asset.role == AssetRole.KEY_EXCHANGE:
            asset.blockers.append(
                "SWIFT messaging requires forward secrecy. Confirm the replacement "
                "is used in an ephemeral (not static) key-exchange mode - a static "
                "ML-KEM deployment would silently drop this property."
            )

        if "pci" in location or "cardholder" in location:
            asset.blockers.append(
                "In scope for PCI DSS 4.0 cryptographic agility requirements - "
                "document the migration plan for the assessor, not just the code."
            )
