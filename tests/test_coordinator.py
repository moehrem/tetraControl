"""Test the coordinator module."""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.exceptions import ConfigEntryNotReady

from custom_components.tetraconnect.coordinator import TetraconnectCoordinator
from custom_components.tetraconnect.const import DOMAIN


@pytest.fixture
def mock_config_entry() -> ConfigEntry:
    """Return a mock ConfigEntry for tetraconnect."""
    return ConfigEntry(
        version=1,
        minor_version=0,
        domain=DOMAIN,
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


@pytest.fixture
def mock_hass():
    """Return a mock HomeAssistant instance."""
    return Mock(spec=HomeAssistant)


class TestTetraconnectCoordinator:
    """Test the TetraconnectCoordinator class."""

    def test_coordinator_initialization(self, mock_hass, mock_config_entry):
        """Test coordinator initialization."""
        with patch('custom_components.tetraconnect.coordinator.COMManager') as mock_com_manager:
            coordinator = TetraconnectCoordinator(mock_hass, mock_config_entry)
            
            # Check that properties are set correctly
            assert coordinator.manufacturer == "Motorola"
            assert coordinator.serial_port == "/dev/ttyUSB0"
            assert coordinator.baudrate == 38400
            
            # Check that COMManager was initialized with correct parameters
            mock_com_manager.assert_called_once_with(
                coordinator, "/dev/ttyUSB0", 38400
            )

    @pytest.mark.asyncio
    async def test_async_start_success(self, mock_hass, mock_config_entry):
        """Test successful coordinator start."""
        with patch('custom_components.tetraconnect.coordinator.COMManager') as mock_com_manager_class:
            mock_com_manager = AsyncMock()
            mock_com_manager_class.return_value = mock_com_manager
            
            coordinator = TetraconnectCoordinator(mock_hass, mock_config_entry)
            
            # Test successful start
            await coordinator.async_start()
            
            # Verify that COM manager methods were called
            mock_com_manager.serial_initialize.assert_called_once_with(mock_hass)
            mock_com_manager.tetra_initialize.assert_called_once()

    @pytest.mark.asyncio
    async def test_async_start_serial_initialize_failure(self, mock_hass, mock_config_entry):
        """Test coordinator start with serial initialization failure."""
        with patch('custom_components.tetraconnect.coordinator.COMManager') as mock_com_manager_class:
            mock_com_manager = AsyncMock()
            mock_com_manager_class.return_value = mock_com_manager
            mock_com_manager.serial_initialize.side_effect = Exception("Serial port error")
            
            coordinator = TetraconnectCoordinator(mock_hass, mock_config_entry)
            
            # Test that ConfigEntryNotReady is raised
            with pytest.raises(ConfigEntryNotReady):
                await coordinator.async_start()
            
            # Verify that serial_initialize was called
            mock_com_manager.serial_initialize.assert_called_once_with(mock_hass)
            # tetra_initialize should not be called if serial_initialize fails
            mock_com_manager.tetra_initialize.assert_not_called()

    @pytest.mark.asyncio
    async def test_async_start_tetra_initialize_failure(self, mock_hass, mock_config_entry):
        """Test coordinator start with tetra initialization failure."""
        with patch('custom_components.tetraconnect.coordinator.COMManager') as mock_com_manager_class:
            mock_com_manager = AsyncMock()
            mock_com_manager_class.return_value = mock_com_manager
            mock_com_manager.tetra_initialize.side_effect = Exception("Tetra initialization error")
            
            coordinator = TetraconnectCoordinator(mock_hass, mock_config_entry)
            
            # Test that ConfigEntryNotReady is raised
            with pytest.raises(ConfigEntryNotReady):
                await coordinator.async_start()
            
            # Verify that both methods were called
            mock_com_manager.serial_initialize.assert_called_once_with(mock_hass)
            mock_com_manager.tetra_initialize.assert_called_once()

    @pytest.mark.asyncio
    async def test_async_stop(self, mock_hass, mock_config_entry):
        """Test coordinator stop."""
        with patch('custom_components.tetraconnect.coordinator.COMManager') as mock_com_manager_class:
            mock_com_manager = AsyncMock()
            mock_com_manager_class.return_value = mock_com_manager
            
            coordinator = TetraconnectCoordinator(mock_hass, mock_config_entry)
            
            # Test stop
            await coordinator.async_stop()
            
            # Verify that serial_stop was called
            mock_com_manager.serial_stop.assert_called_once()

    def test_coordinator_properties_from_config(self, mock_hass, mock_config_entry):
        """Test that coordinator correctly extracts properties from config entry."""
        # Modify config entry data
        mock_config_entry.data = {
            "manufacturer": "TestManufacturer",
            "serial_port": "/dev/ttyUSB1",
            "baudrate": 9600,
        }
        
        with patch('custom_components.tetraconnect.coordinator.COMManager'):
            coordinator = TetraconnectCoordinator(mock_hass, mock_config_entry)
            
            assert coordinator.manufacturer == "TestManufacturer"
            assert coordinator.serial_port == "/dev/ttyUSB1"
            assert coordinator.baudrate == 9600

    def test_coordinator_inheritance(self, mock_hass, mock_config_entry):
        """Test that coordinator properly inherits from DataUpdateCoordinator."""
        from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
        
        with patch('custom_components.tetraconnect.coordinator.COMManager'):
            coordinator = TetraconnectCoordinator(mock_hass, mock_config_entry)
            
            # Check inheritance
            assert isinstance(coordinator, DataUpdateCoordinator)
            
            # Check that DataUpdateCoordinator was initialized with correct parameters
            assert coordinator.name == f"{DOMAIN} Coordinator"
            assert coordinator.update_interval is None
