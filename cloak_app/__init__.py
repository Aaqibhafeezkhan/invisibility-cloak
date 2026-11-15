"""Core computer-vision components for Invisibility Cloak."""

from .config import COLOUR_PRESETS, DEFAULT_SETTINGS
from .state import CloakState
from .vision import apply_cloak, build_mask, encode_png

__all__ = [
    "COLOUR_PRESETS",
    "DEFAULT_SETTINGS",
    "CloakState",
    "apply_cloak",
    "build_mask",
    "encode_png",
]
