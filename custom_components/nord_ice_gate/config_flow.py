"""Configuration flow for a LocalTuya gate."""
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.helpers import selector

DOMAIN = "nord_ice_gate"


def devices(hass):
    result = {}
    for entry in hass.config_entries.async_entries("localtuya"):
        for device_id, device in entry.data.get("devices", {}).items():
            result[device_id] = f"{device.get('friendly_name') or device.get('name') or device_id} ({device_id})"
    return result


class GateFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None):
        found = devices(self.hass)
        choices = [selector.SelectOptionDict(value=k, label=v) for k, v in found.items()]
        choices.append(selector.SelectOptionDict(value="__manual__", label="Ввести Tuya Device ID вручную"))
        if user_input is not None:
            self._device = user_input["device"]
            return await self.async_step_settings()
        return self.async_show_form(step_id="user", data_schema=vol.Schema({
            vol.Required("device", default=next(iter(found), "__manual__")):
                selector.SelectSelector(selector.SelectSelectorConfig(options=choices)),
        }))

    async def async_step_settings(self, user_input=None):
        errors = {}
        if user_input is not None:
            device_id = user_input.pop("device_id", "").strip() if self._device == "__manual__" else self._device
            if not device_id:
                errors["base"] = "missing_device"
            else:
                await self.async_set_unique_id(device_id)
                self._abort_if_unique_id_configured()
                return self.async_create_entry(title=user_input.pop("name"), data={**user_input, "device_id": device_id})
        fields = {vol.Required("name", default="Nord Ice NI600Z"): str}
        if self._device == "__manual__":
            fields[vol.Required("device_id")] = str
        fields.update({
            vol.Required("reverse", default=False): bool,
        })
        return self.async_show_form(step_id="settings", data_schema=vol.Schema(fields), errors=errors)
