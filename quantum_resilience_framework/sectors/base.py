"""
Base class for sector-specific migration modules.

A sector module inspects assets tagged with its sector and adds
deployment-specific blockers - constraints that a generic Mosca score cannot
capture, such as protocol limitations, latency budgets, or hardware refresh
cycles.
"""

from abc import ABC, abstractmethod

from ..models import CryptoAsset


class SectorModule(ABC):
    sector_key: str = "base"

    @abstractmethod
    def apply(self, asset: CryptoAsset) -> None:
        """Mutate asset.blockers in place with sector-specific findings."""
        raise NotImplementedError
