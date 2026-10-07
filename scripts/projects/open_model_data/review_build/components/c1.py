"""Closed-registry C1 sentence correction component."""

from . import c1_ua_gec
from .ua_gec_component import UaGecComponent

COMPONENT = UaGecComponent(c1_ua_gec)
