import pytest

from custom_components.tetraconnect import async_setup_entry, async_unload_entry
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry


@pytest.fixture
def mock_config_entry() -> ConfigEntry:
    """Return a mock ConfigEntry for tetraconnect."""
    return ConfigEntry(
        version=1,
        minor_version=0,
        domain="tetraconnect",
        title="Test tetraconnect",
        data={
            "manufacturer": "Motorola",
            "serial_port": "/dev/ttyUSB0",
            "baudrate": 38400,
        },
        options={},
        entry_id="1234",
        unique_id="test-unique-id",
        source="user",
        discovery_keys={},
        subentries_data={},
    )


@pytest.mark.asyncio
async def test_async_setup_entry(hass: HomeAssistant, config_entry: ConfigEntry):
    result = await async_setup_entry(hass, config_entry)
    assert result is True
    assert "tetraconnect" in hass.data


@pytest.mark.asyncio
async def test_async_unload_entry(hass: HomeAssistant, config_entry: ConfigEntry):
    await async_setup_entry(hass, config_entry)
    result = await async_unload_entry(hass, config_entry)
    assert result is True
