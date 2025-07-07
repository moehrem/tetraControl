# tetraControl Home Assistant Integration

The **tetraControl** integration allows you to connect and monitor TETRA radios (e.g., Motorola devices) via serial interface in [Home Assistant](https://www.home-assistant.io/). It provides real-time sensor data such as device status, location, and error messages.

> This integration is NOT able to decode encrypted TETRA radio messages. You need to have legal access to any source of decrypted data via a suitable hardware device.

ATTENTION: The integration is in an early stage of development. Its neither feature complete nor polished or even fully tested. Thus please be aware of bugs. If you find one, I would be happy to receive an [issue](https://github.com/moehrem/tetraControl/issues). Many thanks!


## Features
- Automatic detection and configuration of supported TETRA radios
- Real-time status, location, and error reporting via Home Assistant sensors
- Robust serial connection management with automatic reconnection
- Based on ETSI EN 300 392‑5 V2.7.1 (April 2020)

## Supported manufacturers
According to ETSI-Standard each manufacturer is free to offer own data structures within specific limits. Thus data handling within the integration is specific to each manufacturer.
As of now the following manufacturers are supportes:
- Motorola

We plan to support in the future:
- Sepura

If you know how to handle data from other manufacturers or you are able to supply documentation, please contact us. Many thanks!

## Installation

### HACS (recommended)
tetraControl is not (yet) availbale via HACS directly, but you may install it manually:
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
- **Error Reports**: Extended error information.

Furthermore it will create sensors per sender per message type. These will be updated, if a new message of the same type from the same sender arrives.

## Troubleshooting
- Ensure your Home Assistant instance has permission to access the serial port.
- Check the Home Assistant logs for serial connection errors.
- Only one process can access a serial port at a time.