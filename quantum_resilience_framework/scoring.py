"""
Mosca theorem risk scoring engine.

Mosca's theorem: act now if x + y > z, where
  x = years the data must remain confidential (data_sensitivity_years)
  y = years needed to migrate this asset (migration_timeline_years)
  z = years until a cryptographically relevant quantum computer exists (crqc_horizon_years)

This module turns the inequality into a bounded urgency score used for
prioritisation, rather than a binary act/do-not-act flag, since a portfolio
of assets needs relative ranking, not just a threshold.
"""

from .models import CryptoAsset, QuantumVulnerability

# Probability-weighted CRQC horizon estimates, in years from now.
CRQC_ESTIMATES = {
    "conservative": 10.0,
    "moderate": 15.0,
    "pessimistic": 20.0,
}

# Shor's algorithm gives a polynomial-time break of RSA/ECC - a BROKEN asset
# has effectively zero security once a CRQC exists. Grover's algorithm only
# gives a quadratic speed-up against symmetric primitives - a WEAKENED asset
# such as AES-128 still presents a real (if reduced) work factor of 2^64
# rather than an outright compromise. Treating both cases identically under
# the raw Mosca formula overstates the urgency of the weakened case, so its
# score is dampened relative to an equivalent broken asset. 0.5 is a
# deliberately conservative choice - it halves the urgency rather than
# treating it as low-priority, since falling compute costs mean a 2^64 work
# factor is not a permanent margin either. See METHODOLOGY.md for the full
# rationale.
WEAKENED_DAMPENING_FACTOR = 0.5


def mosca_urgency(x_data_sensitivity: float, y_migration_timeline: float, z_crqc_horizon: float) -> int:
    """
    Return an urgency score from 0-10.

    urgency = min(10, round(10 * (x + y) / z))

    A raw score of 10 or more means x + y already meets or exceeds z - the
    Mosca inequality has triggered and migration should have started already.
    Scores are capped at 10 so assets can still be ranked against each other
    once several have already breached the threshold.
    """
    if z_crqc_horizon <= 0:
        raise ValueError("z_crqc_horizon (CRQC estimate) must be positive")

    raw = 10 * (x_data_sensitivity + y_migration_timeline) / z_crqc_horizon
    return min(10, round(raw))


def score_asset(asset: CryptoAsset, crqc_horizon_years: float) -> int:
    """
    Score a single asset.

    - SAFE assets (already PQC) get a fixed urgency of 0 - there is no
      migration required, only routine parameter-set currency checks.
    - WEAKENED assets run through the Mosca formula and then have
      WEAKENED_DAMPENING_FACTOR applied, reflecting that Grover's algorithm
      degrades security rather than eliminating it (see the module-level
      docstring above). A non-zero raw score always rounds to at least 1
      after dampening, so a weakened asset is never reported as fully safe.
    - BROKEN and UNKNOWN assets run through the Mosca formula unmodified.
    """
    if asset.vulnerability == QuantumVulnerability.SAFE:
        return 0

    raw_urgency = mosca_urgency(
        x_data_sensitivity=asset.data_sensitivity_years,
        y_migration_timeline=asset.migration_timeline_years,
        z_crqc_horizon=crqc_horizon_years,
    )

    if asset.vulnerability == QuantumVulnerability.WEAKENED:
        dampened = round(raw_urgency * WEAKENED_DAMPENING_FACTOR)
        return max(1, dampened) if raw_urgency > 0 else 0

    return raw_urgency
