"""Config flow: Bluetooth discovery or manual pick."""
from __future__ import annotations

from typing import Any

import voluptuous as vol
from homeassistant.components.bluetooth import BluetoothServiceInfoBleak, async_discovered_service_info
from homeassistant.config_entries import ConfigFlow, ConfigFlowResult, OptionsFlow
from homeassistant.const import CONF_ADDRESS
from homeassistant.core import callback

from .const import CONF_POLL_MINUTES, DEFAULT_POLL_MINUTES, DOMAIN, MIN_POLL_MINUTES


def _is_furby(info: BluetoothServiceInfoBleak) -> bool:
    return (info.name or "").lower().startswith("furby")


class FurbyConfigFlow(ConfigFlow, domain=DOMAIN):
    VERSION = 1

    def __init__(self) -> None:
        self._info: BluetoothServiceInfoBleak | None = None
        self._found: dict[str, str] = {}

    async def async_step_bluetooth(self, info: BluetoothServiceInfoBleak) -> ConfigFlowResult:
        await self.async_set_unique_id(info.address)
        self._abort_if_unique_id_configured()
        self._info = info
        self.context["title_placeholders"] = {"name": f"Furby {info.address[-5:]}"}
        return await self.async_step_confirm()

    async def async_step_confirm(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        assert self._info
        title = f"Furby {self._info.address[-5:]}"
        if user_input is not None:
            return self.async_create_entry(title=title, data={CONF_ADDRESS: self._info.address})
        self._set_confirm_only()
        return self.async_show_form(step_id="confirm", description_placeholders={"name": title})

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        if user_input is not None:
            addr = user_input[CONF_ADDRESS]
            await self.async_set_unique_id(addr, raise_on_progress=False)
            self._abort_if_unique_id_configured()
            return self.async_create_entry(title=f"Furby {addr[-5:]}", data={CONF_ADDRESS: addr})
        current = self._async_current_ids()
        for info in async_discovered_service_info(self.hass, connectable=True):
            if _is_furby(info) and info.address not in current:
                self._found[info.address] = f"{info.name} ({info.address}, {info.rssi} dBm)"
        if not self._found:
            return self.async_abort(reason="no_devices_found")
        return self.async_show_form(step_id="user",
            data_schema=vol.Schema({vol.Required(CONF_ADDRESS): vol.In(self._found)}))

    @staticmethod
    @callback
    def async_get_options_flow(entry) -> OptionsFlow:
        return FurbyOptionsFlow()


class FurbyOptionsFlow(OptionsFlow):
    async def async_step_init(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        if user_input is not None:
            return self.async_create_entry(data=user_input)
        cur = self.config_entry.options.get(CONF_POLL_MINUTES, DEFAULT_POLL_MINUTES)
        return self.async_show_form(step_id="init", data_schema=vol.Schema({
            vol.Required(CONF_POLL_MINUTES, default=cur): vol.All(vol.Coerce(int), vol.Range(min=MIN_POLL_MINUTES, max=240))}))
