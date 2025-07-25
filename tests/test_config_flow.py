"""Test the config flow module."""

import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from pathlib import Path
import asyncio
import serial

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.exceptions import ConfigEntryNotReady

from custom_components.tetraconnect.config_flow import (
    TetraconnectConfigFlow,
    TetraconnectConfigEntry,
)
from custom_components.tetraconnect.const import DOMAIN, MANUFACTURERS_LIST


@pytest.fixture
def mock_hass():
    """Return a mock HomeAssistant instance."""
    hass = Mock(spec=HomeAssistant)
    hass.async_add_executor_job = AsyncMock()
    return hass


class TestTetraconnectConfigEntry:
    """Test the TetraconnectConfigEntry dataclass."""

    def test_config_entry_defaults(self):
        """Test default values of TetraconnectConfigEntry."""
        entry = TetraconnectConfigEntry()
        
        assert entry.manufacturer == "unknown"
        assert entry.serial_port == ""
        assert entry.baudrate == 0
        assert entry.device_id == "unknown"
        assert entry.model == "unknown"
        assert entry.revision == "unknown"

    def test_config_entry_custom_values(self):
        """Test TetraconnectConfigEntry with custom values."""
        entry = TetraconnectConfigEntry(
            manufacturer="Motorola",
            serial_port="/dev/ttyUSB0",
            baudrate=38400,
            device_id="M83AAA1BB2CC",
            model="M83AAA1BB2CC",
            revision="1.0"
        )
        
        assert entry.manufacturer == "Motorola"
        assert entry.serial_port == "/dev/ttyUSB0"
        assert entry.baudrate == 38400
        assert entry.device_id == "M83AAA1BB2CC"
        assert entry.model == "M83AAA1BB2CC"
        assert entry.revision == "R11.222.3333"


class TestTetraconnectConfigFlow:
    """Test the TetraconnectConfigFlow class."""

    def test_config_flow_initialization(self):
        """Test config flow initialization."""
        flow = TetraconnectConfigFlow()
        
        assert isinstance(flow.config_entry, TetraconnectConfigEntry)
        assert flow.errors == {}
        assert flow.VERSION == "0"
        assert hasattr(flow, 'MINOR_VERSION')
        assert hasattr(flow, 'PATCH_VERSION')

    @pytest.mark.asyncio
    async def test_async_step_user_no_input(self, mock_hass):
        """Test async_step_user with no user input."""
        flow = TetraconnectConfigFlow()
        flow.hass = mock_hass
        
        # Mock _get_serial_ports
        with patch.object(flow, '_get_serial_ports', return_value=['/dev/ttyUSB0', '/dev/ttyUSB1']):
            mock_hass.async_add_executor_job.return_value = ['/dev/ttyUSB0', '/dev/ttyUSB1']
            
            result = await flow.async_step_user()
            
            assert result["type"] == FlowResultType.FORM
            assert result["step_id"] == "user"
            assert "manufacturer" in result["data_schema"].schema
            assert "serial_port" in result["data_schema"].schema
            assert "baudrate" in result["data_schema"].schema

    @pytest.mark.asyncio
    async def test_async_step_user_successful_setup(self, mock_hass):
        """Test successful configuration setup."""
        flow = TetraconnectConfigFlow()
        flow.hass = mock_hass
        
        user_input = {
            "manufacturer": "Motorola",
            "serial_port": "/dev/ttyUSB0",
            "baudrate": 38400,
        }
        
        # Mock _request_device_data to succeed
        with patch.object(flow, '_request_device_data', new_callable=AsyncMock) as mock_request:
            # Set up mock device data
            flow.config_entry.device_id = "M83AAA1BB2CC"
            flow.config_entry.manufacturer = "Motorola"
            
            result = await flow.async_step_user(user_input)
            
            assert result["type"] == FlowResultType.CREATE_ENTRY
            assert result["title"] == "Motorola M83AAA1BB2CC"
            assert result["data"]["manufacturer"] == "Motorola"
            assert result["data"]["serial_port"] == "/dev/ttyUSB0"
            assert result["data"]["baudrate"] == 38400
            mock_request.assert_called_once()

    @pytest.mark.asyncio
    async def test_async_step_user_timeout_error(self, mock_hass):
        """Test timeout error during device communication."""
        flow = TetraconnectConfigFlow()
        flow.hass = mock_hass
        
        user_input = {
            "manufacturer": "Motorola",
            "serial_port": "/dev/ttyUSB0",
            "baudrate": 38400,
        }
        
        # Mock _request_device_data to raise TimeoutError
        with patch.object(flow, '_request_device_data', side_effect=TimeoutError):
            with patch.object(flow, '_async_show_form_user', new_callable=AsyncMock) as mock_form:
                mock_form.return_value = {"type": FlowResultType.FORM}
                
                result = await flow.async_step_user(user_input)
                
                assert flow.errors["base"] == "timeout_error"
                mock_form.assert_called_once()

    @pytest.mark.asyncio
    async def test_async_step_user_serial_error(self, mock_hass):
        """Test serial error during device communication."""
        flow = TetraconnectConfigFlow()
        flow.hass = mock_hass
        
        user_input = {
            "manufacturer": "Motorola",
            "serial_port": "/dev/ttyUSB0",
            "baudrate": 38400,
        }
        
        # Mock _request_device_data to raise SerialException
        with patch.object(flow, '_request_device_data', side_effect=serial.SerialException("Port error")):
            with patch.object(flow, '_async_show_form_user', new_callable=AsyncMock) as mock_form:
                mock_form.return_value = {"type": FlowResultType.FORM}
                
                result = await flow.async_step_user(user_input)
                
                assert flow.errors["base"] == "serial_error"
                mock_form.assert_called_once()

    @pytest.mark.asyncio
    async def test_async_step_user_manufacturer_mismatch(self, mock_hass):
        """Test manufacturer mismatch error."""
        flow = TetraconnectConfigFlow()
        flow.hass = mock_hass
        
        user_input = {
            "manufacturer": "Motorola",
            "serial_port": "/dev/ttyUSB0",
            "baudrate": 38400,
        }
        
        # Mock _request_device_data to raise ValueError
        with patch.object(flow, '_request_device_data', side_effect=ValueError("Manufacturer mismatch")):
            with patch.object(flow, '_async_show_form_user', new_callable=AsyncMock) as mock_form:
                mock_form.return_value = {"type": FlowResultType.FORM}
                
                result = await flow.async_step_user(user_input)
                
                assert flow.errors["base"] == "manufacturer_mismatch"
                mock_form.assert_called_once()

    def test_get_serial_ports(self):
        """Test _get_serial_ports method."""
        flow = TetraconnectConfigFlow()
        
        with patch('pathlib.Path.glob') as mock_glob, \
             patch('pathlib.Path.exists') as mock_exists, \
             patch('os.access') as mock_access:
            
            # Mock different serial port types
            mock_glob.side_effect = [
                [Path('/dev/ttyUSB0'), Path('/dev/ttyUSB1')],  # ttyUSB*
                [Path('/dev/ttyACM0')],  # ttyACM*
                [],  # ttyS*
                [],  # ttyAMA*
                [],  # serial/by-id/*
                [Path('/dev/pts/1')],  # pts/*
            ]
            
            mock_exists.return_value = True
            mock_access.return_value = True
            
            result = flow._get_serial_ports()
            
            expected = ['/dev/pts/1', '/dev/ttyACM0', '/dev/ttyUSB0', '/dev/ttyUSB1']
            assert result == expected

    def test_get_serial_ports_filtered(self):
        """Test _get_serial_ports with filtered results."""
        flow = TetraconnectConfigFlow()
        
        with patch('pathlib.Path.glob') as mock_glob, \
             patch('pathlib.Path.exists') as mock_exists, \
             patch('os.access') as mock_access:
            
            mock_glob.side_effect = [
                [Path('/dev/ttyUSB0'), Path('/dev/ttyUSB1')],
                [], [], [], [], []
            ]
            
            # Mock that only ttyUSB0 exists and is accessible
            def exists_side_effect(path):
                return str(path) == '/dev/ttyUSB0'
            
            def access_side_effect(path, mode):
                return str(path) == '/dev/ttyUSB0'
            
            mock_exists.side_effect = exists_side_effect
            mock_access.side_effect = access_side_effect
            
            result = flow._get_serial_ports()
            
            assert result == ['/dev/ttyUSB0']

    @pytest.mark.asyncio
    async def test_request_device_data_success(self):
        """Test successful device data request."""
        flow = TetraconnectConfigFlow()
        config_entry = TetraconnectConfigEntry(
            serial_port="/dev/ttyUSB0",
            baudrate=38400
        )
        
        # Mock serial connection
        mock_reader = AsyncMock()
        mock_writer = AsyncMock()
        mock_response = b"\r\n+GMI: Motorola\r\n\r\n+GMM: 54009,M83AAA1BB2CC,91.2.0.0\r\n\r\n+GMR: R11.222.3333\r\n\r\nOK\r\n"
        mock_reader.read.return_value = mock_response
        
        with patch('serial_asyncio.open_serial_connection') as mock_serial, \
             patch('asyncio.wait_for') as mock_wait_for:
            
            mock_wait_for.side_effect = [
                (mock_reader, mock_writer),  # First call for connection
                mock_response,  # Second call for reading response
            ]
            
            await flow._request_device_data(config_entry)
            
            # Verify the parsed data
            assert config_entry.model == "M83AAA1BB2CC"
            assert config_entry.device_id == "M83AAA1BB2CC"
            mock_writer.write.assert_called()
            mock_writer.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_request_device_data_connection_failure(self):
        """Test device data request with connection failure."""
        flow = TetraconnectConfigFlow()
        config_entry = TetraconnectConfigEntry(
            serial_port="/dev/ttyUSB0",
            baudrate=38400
        )
        
        with patch('asyncio.wait_for', side_effect=serial.SerialException("Connection failed")):
            with pytest.raises(ConfigEntryNotReady):
                await flow._request_device_data(config_entry)

    def test_parse_init_data_complete(self):
        """Test parsing of complete initialization data."""
        flow = TetraconnectConfigFlow()
        response = b"\r\n+GMI: Motorola\r\n\r\n+GMM: 54009,M83AAA1BB2CC,91.2.0.0\r\n\r\n+GMR: R11.222.3333\r\n\r\nOK\r\n"
        
        flow._parse_init_data(response)
        
        assert flow.config_entry.model == "M83AAA1BB2CC"
        assert flow.config_entry.device_id == "M83AAA1BB2CC"
        assert flow.config_entry.revision == "R11.222.3333"

    def test_parse_init_data_partial(self):
        """Test parsing of partial initialization data."""
        flow = TetraconnectConfigFlow()
        response = b"\r\n+GMM: 54009,M83AAA1BB2CC,91.2.0.0\r\n"
        
        flow._parse_init_data(response)
        
        assert flow.config_entry.model == "Unknown"
        assert flow.config_entry.device_id == "Unknown"
        assert flow.config_entry.revision == "R11.222.3333"

    def test_check_manufacturer_match(self):
        """Test manufacturer check with matching manufacturer."""
        flow = TetraconnectConfigFlow()
        flow.config_entry.manufacturer = "Motorola"
        
        # Should not raise any exception
        flow._check_manufacturer("Motorola")

    def test_check_manufacturer_case_insensitive(self):
        """Test manufacturer check is case insensitive."""
        flow = TetraconnectConfigFlow()
        flow.config_entry.manufacturer = "motorola"
        
        # Should not raise any exception
        flow._check_manufacturer("MOTOROLA")

    def test_check_manufacturer_mismatch(self):
        """Test manufacturer check with mismatched manufacturer."""
        flow = TetraconnectConfigFlow()
        flow.config_entry.manufacturer = "Motorola"
        
        with pytest.raises(ValueError, match="Manufacturer mismatch"):
            flow._check_manufacturer("Nokia")

    def test_check_manufacturer_whitespace_handling(self):
        """Test manufacturer check handles whitespace correctly."""
        flow = TetraconnectConfigFlow()
        flow.config_entry.manufacturer = " Motorola "
        
        # Should not raise any exception
        flow._check_manufacturer("  Motorola  ")
