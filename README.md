# Toyama Home Assistant Integration

## Overview
The **Toyama Home Assistant Integration** enables seamless control of **TouchArt Smart Switches and Fans** within the Home Assistant ecosystem. This integration discovers Toyama device gateways automatically on the local network, making setup quick and easy. Once added, users can control all their Toyama smart devices directly from the **Home Assistant dashboard**.

## Features
- **Automatic Discovery**: Uses HomeAssistant (zeroconf) to find Toyama gateways on the local network.
- **Switch Control**: Turn TouchArt Smart Switches **on/off** from Home Assistant.
- **Fan Control**: Adjust **fan speed** directly from the HA dashboard.
- **Seamless Integration**: Works natively within Home Assistant with minimal setup.

## Installation
### Prerequisites
- A working **Home Assistant** installation.
- **Toyama TouchArt Smart Switches and Fans** already configured in Toyama's WizHom application.
- All devices should be on the **same local network**.

### Manual Installation
Since this is not an official Home Assistant integration, it must be installed manually:

1. Download the **Toyama integration** from the GitHub repository: [GitHub - ha-toyama](https://github.com/prasannareddych/ha-toyama).
2. Copy the `toyama` folder from `custom_components/toyama` in the repository to `custom_components/toyama` Home Assistant configuration directory.
3. Restart Home Assistant to apply the changes.
4. Once the Toyama gateway is discovered, follow the integration setup.
5. Done!

## Usage
Once the integration is set up:
- **Switches** will appear as standard Home Assistant **switch entities**.
- **Fans** will support speed control via Home Assistant’s **fan control interface**.
- You can use **Home Assistant Automations** and **Scripts** to control Toyama devices.

## Troubleshooting
- Ensure that the **Toyama gateway** and **Home Assistant** are on the **same network**.
- If devices are not discovered, try **restarting Home Assistant**.
- Check **Home Assistant logs** for any errors related to the integration.

## Contributing
If you'd like to contribute to this integration, feel free to submit an issue or pull request on the [GitHub repository](https://github.com/prasannareddych/ha-toyama).
