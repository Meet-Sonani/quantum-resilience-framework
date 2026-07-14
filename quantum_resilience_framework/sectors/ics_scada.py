"""
ICS/SCADA sector module.

Real-time process control loops typically have latency budgets under 10ms.
Some ML-DSA parameter sets have verification times that conflict with this.
Legacy Modbus and pre-SAv5 DNP3 have no native cryptographic authentication
at all - a gap that no PQC primitive substitution alone can fix. DNP3 Secure
Authentication v5 (SAv5) is the exception: it does provide native
authentication, so it must not be flagged the same way as bare DNP3.
"""

from .base import SectorModule
from ..models import CryptoAsset

_UNAUTHENTICATED_PROTOCOLS = ("modbus", "dnp3")
# Location text containing any of these means the asset is on the *secure*
# side of the protocol (e.g. DNP3 SAv5), so the generic "no native
# authentication" blocker for that protocol must not fire.
_AUTHENTICATED_VARIANT_MARKERS = ("secure authentication", "sav5", "sa v5")
_REAL_TIME_KEYWORDS = ("process control", "real-time", "control loop")


class ICSSCADAModule(SectorModule):
    sector_key = "ics_scada"

    def apply(self, asset: CryptoAsset) -> None:
        location = asset.location.lower()
        is_authenticated_variant = any(marker in location for marker in _AUTHENTICATED_VARIANT_MARKERS)

        if not is_authenticated_variant:
            for protocol in _UNAUTHENTICATED_PROTOCOLS:
                if protocol in location:
                    asset.blockers.append(
                        f"{protocol.upper()} has no native cryptographic authentication. "
                        "This is broken with no direct PQC migration path - it requires "
                        "protocol-level redesign (e.g. a wrapping layer or gateway), not "
                        "a primitive swap."
                    )

        if any(keyword in location for keyword in _REAL_TIME_KEYWORDS):
            asset.blockers.append(
                "Real-time control loop: latency budget is typically under 10ms. "
                "Verify the chosen ML-DSA/ML-KEM parameter set against measured "
                "verification/decapsulation time on representative target hardware "
                "before committing to it - published pqm4 benchmarks are a "
                "reasonable starting reference if you have not measured your own."
            )
