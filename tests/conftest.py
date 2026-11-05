"""Fixtures for Furby Connect tests."""
from __future__ import annotations

import pytest

pytest_plugins = "pytest_homeassistant_custom_component"

# A real 0x22 ImHere reply (19 bytes), captured 2026-10 and edited to the Excited mood:
# MAC (LE) | name idx | colour | personality | mood | excited displeased tired fullness wellness | wellness_en | states (BE)
IM_HERE = bytes.fromhex("22" "6c6cc112076b" "0c" "01" "00" "00" "45" "00" "09" "53" "64" "01" "0040")


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    """Enable custom integrations in every test."""
    yield
