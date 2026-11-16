"""Cover controlled through LocalTuya and its raw limit-switch DPs."""
from datetime import timedelta

from homeassistant.components.cover import CoverDeviceClass, CoverEntity, CoverEntityFeature
from homeassistant.core import callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.event import async_call_later


async def async_setup_entry(hass, entry, async_add_entities):
    async_add_entities([GateCover(entry)])


class GateCover(CoverEntity):
    _attr_device_class = CoverDeviceClass.GATE
    _attr_supported_features = CoverEntityFeature.OPEN | CoverEntityFeature.CLOSE | CoverEntityFeature.STOP
    _attr_should_poll = False

    def __init__(self, entry):
        self._entry = entry
        self._attr_unique_id = f"{entry.data['device_id']}_gate"
        self._attr_name = entry.title
        self._status = {}
        self._connected = False
        self._movement = None
        self._cancel_timeout = None
        self._timed_out = False

    @callback
    def _clear_movement(self):
        if self._cancel_timeout is not None:
            self._cancel_timeout()
            self._cancel_timeout = None
        self._movement = None

    async def async_will_remove_from_hass(self):
        self._clear_movement()
        await super().async_will_remove_from_hass()

    @callback
    def _movement_timeout(self, _now):
        self._cancel_timeout = None
        self._movement = None
        self._timed_out = True
        self.async_write_ha_state()

    @callback
    def _start_movement(self, direction):
        self._clear_movement()
        self._timed_out = False
        self._movement = direction
        self._cancel_timeout = async_call_later(self.hass, timedelta(seconds=60), self._movement_timeout)
        self.async_write_ha_state()

    async def async_added_to_hass(self):
        await super().async_added_to_hass()
        device_id = self._entry.data['device_id']
        self.async_on_remove(async_dispatcher_connect(self.hass, f'localtuya_{device_id}', self._status_changed))
        device = self.hass.data.get('localtuya', {}).get('tuya_devices', {}).get(device_id)
        if device and device.connected:
            self._connected = True
            self._status = dict(device._status)

    @callback
    def _status_changed(self, status):
        self._connected = status is not None
        self._status = dict(status) if status is not None else {}
        opened, closed = self._limits()
        if status is None:
            self._clear_movement()
        elif (self._movement == 'opening' and opened is True and closed is False
              or self._movement == 'closing' and closed is True and opened is False):
            self._clear_movement()
            self._timed_out = False
        elif self._timed_out and (opened is True and closed is False or closed is True and opened is False):
            self._timed_out = False
        self.async_write_ha_state()

    def _limits(self):
        reverse = self._entry.data.get('reverse', True)
        opened = self._status.get('106' if reverse else '107')
        closed = self._status.get('107' if reverse else '106')
        return opened, closed

    @property
    def available(self):
        opened, closed = self._limits()
        return (self._connected and type(opened) is bool and type(closed) is bool
                and not (opened and closed)
                and self.hass.services.has_service('localtuya', 'set_dp'))

    @property
    def is_closed(self):
        opened, closed = self._limits()
        if not self.available or self._timed_out or not (opened or closed):
            return None
        return closed

    @property
    def is_opening(self):
        return self._movement == 'opening'

    @property
    def is_closing(self):
        return self._movement == 'closing'

    async def _command(self, dp):
        await self.hass.services.async_call(
            'localtuya', 'set_dp',
            {'device_id': self._entry.data['device_id'], 'dp': dp, 'value': True},
            blocking=True,
        )

    async def async_open_cover(self, **kwargs):
        await self._command(102 if self._entry.data.get('reverse', True) else 101)
        self._start_movement('opening')

    async def async_close_cover(self, **kwargs):
        await self._command(101 if self._entry.data.get('reverse', True) else 102)
        self._start_movement('closing')

    async def async_stop_cover(self, **kwargs):
        await self._command(103)
        self._clear_movement()
        self._timed_out = False
        self.async_write_ha_state()
