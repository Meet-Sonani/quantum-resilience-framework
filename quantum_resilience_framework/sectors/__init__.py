"""Registry mapping an inventory's sector string to its module instance."""

from .financial import FinancialServicesModule
from .healthcare import HealthcareIoTModule
from .ics_scada import ICSSCADAModule

SECTOR_MODULES = {
    "healthcare_iot": HealthcareIoTModule(),
    "ics_scada": ICSSCADAModule(),
    "financial_services": FinancialServicesModule(),
}

__all__ = ["SECTOR_MODULES", "HealthcareIoTModule", "ICSSCADAModule", "FinancialServicesModule"]
