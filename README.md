
# Toyama Home Assistant Integration

This custom Home Assistant integration allows you to control Toyama devices, such as switches and fans, directly from Home Assistant.

## Features

- **Switch Control:** Manage Toyama TouchArt switches from Home Assistant.
- **Fan Control:** Control Toyama TouchArt Dimmer fans with support for specific speed percentages.
- **Automatic Discovery:** Discover Toyama devices automatically on your local network.
- **Real-Time Updates:** Receive live updates from devices.

## Supported Devices

- **Switches**
- **Fans** (with speed control for specific percentages)

## Installation

### Manual Installation

1. Download the repository and extract the files.
2. Copy the `toyama` directory into your Home Assistant `custom_components` directory:

   ```bash
   custom_components/toyama/
   ```

3. Restart Home Assistant.

## Configuration

### Add Integration

1. Go to **Configuration** > **Devices & Services**.
2. Click on **Add Integration** and search for `Toyama`.
3. Follow the setup instructions.

## Usage

### Switches

After setup, your Toyama switches will be available in Home Assistant. You can control them via the Home Assistant UI and include them in automations.

### Fans

Toyama fans are integrated with support for specific speed percentages. The supported speeds are mapped to UI-friendly values:

- 0% (Off)
- 25% (Mapped to 35%)
- 50% (Mapped to 50%)
- 75% (Mapped to 55%)
- 100% (Full Speed)

