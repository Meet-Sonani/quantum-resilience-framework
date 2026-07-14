"""
End-to-end pipeline: classify, score, and recommend for every asset in an
inventory, then apply sector-specific blockers.
"""

from .classify import classify
from .models import Inventory
from .recommendations import recommend
from .scoring import score_asset
from .sectors import SECTOR_MODULES


def process_inventory(inventory: Inventory) -> Inventory:
    """Run the full assessment pipeline over every asset in the inventory, in place."""
    for asset in inventory.assets:
        asset.vulnerability = classify(asset.name)
        asset.urgency_score = score_asset(asset, inventory.crqc_horizon_years)
        asset.recommendation = recommend(asset.name, asset.role, asset.vulnerability)

        if asset.sector and asset.sector in SECTOR_MODULES:
            SECTOR_MODULES[asset.sector].apply(asset)

    return inventory
