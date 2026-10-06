"""Closed-registry C6a calque-only sentence correction component."""

from . import c6a_calque
from .ua_gec_component import UaGecComponent

COMPONENT = UaGecComponent(c6a_calque)
