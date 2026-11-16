# Nord Ice NI600Z for Home Assistant

A custom Home Assistant integration for controlling a **Nord Ice NI600Z sliding gate operator** through [LocalTuya](https://github.com/xZetsubou/hass-localtuya).

The integration sends gate commands through the `localtuya.set_dp` service and reads the open/closed limit switches directly from the device's LocalTuya DP status. Separate binary sensor entities are not required.

## Features

- Open, close, and stop controls
- Direct and reversed installation directions
- Automatic selection of devices already configured in LocalTuya
- Manual Tuya Device ID entry as a fallback
- Open and closed states obtained directly from DP 106 and DP 107
- Temporary `opening` and `closing` states after commands
- Automatic transition to `unknown` when no final limit state is received within 60 seconds
- No separate IP address or local key storage

## Requirements

- Home Assistant
- [LocalTuya](https://github.com/xZetsubou/hass-localtuya) installed and configured
- A Nord Ice NI600Z device already added to LocalTuya

The device IP address, Tuya Device ID, and local key are managed by LocalTuya. This integration does not establish a separate Tuya connection and does not store the local key.

## Installation

### Manual installation

1. Download the repository or release archive.
2. Copy `custom_components/nord_ice_gate` to:

   ```text
   /config/custom_components/nord_ice_gate
   ```

3. Restart Home Assistant.
4. Open **Settings → Devices & services**.
5. Click **Add integration**.
6. Search for **Nord Ice Sliding Gate**.

### HACS custom repository

This repository can be added manually to HACS as an **Integration** custom repository if it has been published on GitHub:

1. Open HACS.
2. Open the three-dot menu and select **Custom repositories**.
3. Enter the GitHub repository URL.
4. Select **Integration** as the category.
5. Install the integration and restart Home Assistant.

This does not imply inclusion in the default HACS repository list.

## Configuration

During setup:

1. Select a device already configured in LocalTuya, or select manual entry and provide its Tuya Device ID.
2. Enable **Reverse direction** when the gate uses the reversed DP mapping.
3. Test all commands while physically present at the gate and with the movement area clear.

To change the direction or device after initial setup, remove the integration entry and add it again.

## DP mapping

### Direct direction

| Function | DP |
|---|---:|
| Open command | 101 |
| Close command | 102 |
| Stop command | 103 |
| Open limit | 107 |
| Closed limit | 106 |

### Reverse direction

| Function | DP |
|---|---:|
| Open command | 102 |
| Close command | 101 |
| Stop command | 103 |
| Open limit | 106 |
| Closed limit | 107 |

Command DPs are written with the boolean value `true`. For limit DPs, `true` means that the corresponding limit switch is active.

## State handling

- After a successful open command, the cover reports `opening`.
- After a successful close command, the cover reports `closing`.
- When the expected limit DP becomes active, the cover reports `open` or `closed`.
- If the expected final state is not received within 60 seconds, the cover reports `unknown`.
- A stop command immediately clears the movement state.
- If both limit DPs are `false`, the physical position is unknown.
- If both limit DPs are `true`, either DP is missing, or LocalTuya reports the device as disconnected, the entity is unavailable.

The movement state is inferred from commands sent through this entity. Commands issued by another remote, wall button, or integration may not produce an `opening` or `closing` state.

## Updating

For a manual installation:

1. Replace `/config/custom_components/nord_ice_gate` with the new version.
2. Restart Home Assistant.

The existing configuration entry should remain intact unless a release explicitly documents a breaking configuration change.

## Limitations

- This integration currently uses LocalTuya's internal status dispatcher to receive raw DP updates. A future LocalTuya release may change that internal interface.
- It does not reset command DPs after writing `true`.
- It cannot determine the exact gate position between the two limit switches.
- It cannot reliably detect movement initiated outside this Home Assistant entity.
- Device behavior may differ between firmware revisions or Tuya configurations.

## Safety

Home Assistant is not a safety controller. The operator's obstacle detection, photocells, emergency stop, and other built-in safety systems must work independently of Home Assistant.

Always test the integration while physically present and keep the gate movement area clear.

