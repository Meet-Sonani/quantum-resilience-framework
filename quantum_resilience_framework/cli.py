"""Command-line interface for the quantum-resilience-framework."""

import json

import click

from .io import load_inventory
from .pipeline import process_inventory
from .report import generate_report


@click.command()
@click.argument("inventory_path", type=click.Path(exists=True))
@click.option(
    "--crqc-horizon", default=None, type=float,
    help="Override the CRQC horizon in years (default: value in the inventory file, or 15.0)",
)
@click.option("--output", default="report.md", help="Output markdown report path")
@click.option(
    "--policy-briefing", is_flag=True, default=False,
    help="Also generate an LLM-written policy briefing (requires ANTHROPIC_API_KEY).",
)
def assess(inventory_path, crqc_horizon, output, policy_briefing):
    """Assess a cryptographic asset inventory and write a prioritised migration report."""
    inventory = load_inventory(inventory_path)

    if crqc_horizon is not None:
        inventory.crqc_horizon_years = crqc_horizon

    process_inventory(inventory)
    report = generate_report(inventory)

    with open(output, "w", encoding="utf-8") as f:
        f.write(report)

    click.echo(f"Assessed {len(inventory.assets)} assets. Report written to {output}")

    if policy_briefing:
        # imported lazily so `anthropic` is only required when this flag is used
        import anthropic

        from .policy_agent import PolicyBriefingError, generate_policy_briefing

        client = anthropic.Anthropic()
        briefing_path = output.rsplit(".", 1)[0] + "-policy-briefing.json"

        try:
            briefing = generate_policy_briefing(inventory, client)
        except PolicyBriefingError as exc:
            click.echo(f"Policy briefing failed: {exc}", err=True)
            raise SystemExit(1)

        with open(briefing_path, "w", encoding="utf-8") as f:
            json.dump(briefing, f, indent=2)

        click.echo(f"Policy briefing written to {briefing_path}")


if __name__ == "__main__":
    assess()