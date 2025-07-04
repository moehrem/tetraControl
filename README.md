# tetraControl Home Assistant Integration

The **tetraControl** integration allows you to connect and monitor TETRA radios (e.g., Motorola devices) via serial interface in [Home Assistant](https://www.home-assistant.io/). It provides real-time sensor data such as device status, location, and error messages.

## Features

- Automatic detection and configuration of supported TETRA radios
- Real-time status, location, and error reporting via Home Assistant sensors
- Robust serial connection management with automatic reconnection
- Support for Motorola radios (extendable for other manufacturers)

## Installation

### HACS (recommended)
tetraCotnrol is not (yet) availbale via HACS directly, but you may install it manually:
1. [Install HACS](https://www.hacs.xyz/docs/use/), if not done already
2. [![Add to HACS](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=moehrem&repository=tetracontrol&category=Integration)
3. **Installation:** Click "Download" in the bottom-right corner.

### Manual installation
1. Copy the `custom_components/tetracontrol` directory into your Home Assistant `custom_components` folder.
2. Restart Home Assistant.

## Configuration

### Via Home Assistant UI

1. Go to **Settings** > **Devices & Services** > **Add Integration**.
2. Search for **tetraControl** and follow the setup wizard:
    - Select your device manufacturer.
    - Choose the serial port and baudrate.
    - The integration will auto-detect your device and complete setup.

### Configuration Options

- **Manufacturer**: Supported manufacturers (e.g., Motorola)
- **Serial Port**: Path to the serial device (e.g., `/dev/ttyUSB0`)
- **Baudrate**: Communication speed (default: 38400)

## Sensors

The integration creates sensors for:

- **Connection Status**: Shows if the radio is connected/disconnected.
- **Device Info**: Manufacturer, model, revision.
- **Location Reports**: Latitude, longitude, velocity, direction, position error.
- **Status Messages**: TETRA status codes.
- **Error Reports**: Extended error information.

## Troubleshooting

- Ensure your Home Assistant instance has permission to access the serial port.
- Check the Home Assistant logs for serial connection errors.
- Only one process can access a serial port at a time.