"""JSON loading for cryptographic asset inventories."""

import json

from .models import AssetRole, CryptoAsset, Inventory


def load_inventory(path: str) -> Inventory:
    """Load and validate a JSON asset inventory file into an Inventory object."""
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    assets = [
        CryptoAsset(
            asset_id=a["asset_id"],
            name=a["name"],
            role=AssetRole(a["role"]),
            location=a["location"],
            data_sensitivity_years=a["data_sensitivity_years"],
            migration_timeline_years=a["migration_timeline_years"],
            sector=a.get("sector"),
            notes=a.get("notes", ""),
        )
        for a in data["assets"]
    ]

    return Inventory(
        system_name=data["system_name"],
        assets=assets,
        crqc_horizon_years=data.get("crqc_horizon_years", 15.0),
    )
