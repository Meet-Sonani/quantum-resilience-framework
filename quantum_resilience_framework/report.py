"""Markdown report generation from a processed inventory."""

from .models import Inventory


def generate_report(inventory: Inventory) -> str:
    """Render a processed inventory as a prioritised markdown migration report."""
    lines = [
        f"# Quantum Resilience Assessment - {inventory.system_name}",
        "",
        f"CRQC horizon used: {inventory.crqc_horizon_years} years",
        "",
        "| Asset | Role | Status | Urgency | Recommendation |",
        "|---|---|---|---|---|",
    ]

    ranked = sorted(inventory.assets, key=lambda a: a.urgency_score or 0, reverse=True)

    for asset in ranked:
        lines.append(
            f"| {asset.name} | {asset.role.value} | {asset.vulnerability.value} "
            f"| {asset.urgency_score} | {asset.recommendation} |"
        )

    blockers_present = [a for a in inventory.assets if a.blockers]
    if blockers_present:
        lines += ["", "## Sector-specific blockers", ""]
        for asset in blockers_present:
            lines.append(f"**{asset.name}** ({asset.location})")
            for blocker in asset.blockers:
                lines.append(f"- {blocker}")
            lines.append("")

    return "\n".join(lines)
