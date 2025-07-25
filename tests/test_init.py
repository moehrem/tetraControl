import pytest
from unittest.mock import Mock, AsyncMock

from custom_components.tetraconnect import async_setup_entry, async_unload_entry
from custom_components.tetraconnect.const import DOMAIN
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
async def test_async_setup_entry(hass: HomeAssistant, mock_config_entry: ConfigEntry):
    """Test setting up the integration."""
    # Mock the coordinator methods
    with pytest.mock.patch('custom_components.tetraconnect.coordinator.TetraconnectCoordinator') as mock_coordinator_class:
        mock_coordinator = AsyncMock()
        mock_coordinator_class.return_value = mock_coordinator
        
        # Mock the async_forward_entry_setups method
        hass.config_entries.async_forward_entry_setups = AsyncMock(return_value=True)
        
        result = await async_setup_entry(hass, mock_config_entry)
        
        assert result is True
        assert DOMAIN in hass.data
        assert hass.data[DOMAIN] == mock_coordinator
        mock_coordinator.async_start.assert_called_once()
        hass.config_entries.async_forward_entry_setups.assert_called_once()


@pytest.mark.asyncio
async def test_async_unload_entry(hass: HomeAssistant, mock_config_entry: ConfigEntry):
    """Test unloading the integration."""
    # First set up the integration
    with pytest.mock.patch('custom_components.tetraconnect.coordinator.TetraconnectCoordinator') as mock_coordinator_class:
        mock_coordinator = AsyncMock()
        mock_coordinator_class.return_value = mock_coordinator
        
        # Mock the methods
        hass.config_entries.async_forward_entry_setups = AsyncMock(return_value=True)
        hass.config_entries.async_unload_platforms = AsyncMock(return_value=True)
        
        # Set up first
        await async_setup_entry(hass, mock_config_entry)
        
        # Now test unload
        result = await async_unload_entry(hass, mock_config_entry)
        
        assert result is True
        mock_coordinator.async_stop.assert_called_once()
        hass.config_entries.async_unload_platforms.assert_called_once()
