"""Config flow for Konnwei Battery Monitor."""

import logging
from typing import Any

import voluptuous as vol

from homeassistant.components import bluetooth
from homeassistant.components.bluetooth import BluetoothServiceInfoBleak
from homeassistant.config_entries import ConfigEntry, ConfigFlow, ConfigFlowResult, OptionsFlow
from homeassistant.const import CONF_ADDRESS, CONF_NAME
from homeassistant.core import callback

from .const import (
    BATTERY_PRESETS,
    CONF_BATTERY_TYPE,
    CONF_POLL_INTERVAL,
    CONF_VOLTAGE_MAX,
    CONF_VOLTAGE_MIN,
    DEFAULT_POLL_INTERVAL,
    DOMAIN,
    MAC_PREFIX,
    MAX_POLL_INTERVAL,
    MAX_VOLTAGE_LIMIT,
    MIN_POLL_INTERVAL,
    MIN_VOLTAGE_LIMIT,
)

_LOGGER = logging.getLogger(__name__)


class KonnweiConfigFlow(ConfigFlow, domain=DOMAIN):
    """Config flow for Konnwei Battery Monitor."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize config flow."""
        self._discovery_info: BluetoothServiceInfoBleak | None = None
        self._discovered_devices: dict[str, BluetoothServiceInfoBleak] = {}

    async def async_step_bluetooth(
        self, discovery_info: BluetoothServiceInfoBleak
    ) -> ConfigFlowResult:
        """Handle bluetooth discovery.

        Args:
            discovery_info: Bluetooth discovery data
        """
        address = discovery_info.address

        # Only accept devices with Konnwei MAC prefix
        if not address.upper().startswith(MAC_PREFIX):
            return self.async_abort(reason="not_supported")

        await self.async_set_unique_id(address)
        self._abort_if_unique_id_configured()

        self._discovery_info = discovery_info
        self.context["title_placeholders"] = {
            "name": discovery_info.name or address,
        }

        return await self.async_step_confirm()

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        """Handle user-initiated setup."""
        if user_input is not None:
            address = user_input[CONF_ADDRESS]
            await self.async_set_unique_id(address)
            self._abort_if_unique_id_configured()

            return await self.async_step_confirm()

        current_addresses = self._async_current_ids()
        discovered = await bluetooth.async_get_scanner(
            self.hass
        ).async_discovered_devices_and_advertisement_data()

        for service_info, _ in discovered:
            address = service_info.address
            if address in current_addresses:
                continue
            if not address.upper().startswith(MAC_PREFIX):
                continue
            self._discovered_devices[address] = service_info

        if not self._discovered_devices:
            return self.async_abort(reason="no_devices_found")

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_ADDRESS): vol.In(
                        {
                            address: f"{info.name or 'Unknown'} ({address})"
                            for address, info in self._discovered_devices.items()
                        }
                    ),
                }
            ),
        )

    async def async_step_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Confirm setup and configure battery settings."""
        errors = {}

        if user_input is not None:
            battery_type = user_input[CONF_BATTERY_TYPE]

            if battery_type == "custom":
                voltage_min = user_input.get(CONF_VOLTAGE_MIN)
                voltage_max = user_input.get(CONF_VOLTAGE_MAX)

                if voltage_min is None or voltage_max is None:
                    errors["base"] = "custom_voltage_required"
                elif voltage_min >= voltage_max:
                    errors["base"] = "invalid_voltage_range"
                elif voltage_max > MAX_VOLTAGE_LIMIT or voltage_min < MIN_VOLTAGE_LIMIT:
                    errors["base"] = "voltage_out_of_range"
            else:
                preset = BATTERY_PRESETS[battery_type]
                voltage_min = preset["min"]
                voltage_max = preset["max"]

            if not errors:
                poll_interval = user_input.get(CONF_POLL_INTERVAL, DEFAULT_POLL_INTERVAL)

                address = self.unique_id
                name = (
                    self._discovery_info.name
                    if self._discovery_info
                    else f"Battery Monitor {address}"
                )

                return self.async_create_entry(
                    title=name,
                    data={
                        CONF_ADDRESS: address,
                        CONF_NAME: name,
                    },
                    options={
                        CONF_BATTERY_TYPE: battery_type,
                        CONF_VOLTAGE_MIN: voltage_min,
                        CONF_VOLTAGE_MAX: voltage_max,
                        CONF_POLL_INTERVAL: poll_interval,
                    },
                )

        address = self.unique_id
        name = self._discovery_info.name if self._discovery_info else f"Battery Monitor {address}"

        schema = vol.Schema(
            {
                vol.Required(CONF_BATTERY_TYPE, default="12v_lead_acid"): vol.In(
                    {k: v["name"] for k, v in BATTERY_PRESETS.items()}
                ),
                vol.Optional(CONF_VOLTAGE_MIN): vol.Coerce(float),
                vol.Optional(CONF_VOLTAGE_MAX): vol.Coerce(float),
                vol.Optional(CONF_POLL_INTERVAL, default=DEFAULT_POLL_INTERVAL): vol.All(
                    vol.Coerce(int),
                    vol.Range(min=MIN_POLL_INTERVAL, max=MAX_POLL_INTERVAL),
                ),
            }
        )

        return self.async_show_form(
            step_id="confirm",
            data_schema=schema,
            errors=errors,
            description_placeholders={"name": name},
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> OptionsFlow:
        """Get options flow handler."""
        return KonnweiOptionsFlow(config_entry)


class KonnweiOptionsFlow(OptionsFlow):
    """Options flow for Konnwei Battery Monitor."""

    def __init__(self, config_entry) -> None:
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        """Manage options."""
        errors = {}

        if user_input is not None:
            battery_type = user_input[CONF_BATTERY_TYPE]

            if battery_type == "custom":
                voltage_min = user_input.get(CONF_VOLTAGE_MIN)
                voltage_max = user_input.get(CONF_VOLTAGE_MAX)

                if voltage_min is None or voltage_max is None:
                    errors["base"] = "custom_voltage_required"
                elif voltage_min >= voltage_max:
                    errors["base"] = "invalid_voltage_range"
                elif voltage_max > MAX_VOLTAGE_LIMIT or voltage_min < MIN_VOLTAGE_LIMIT:
                    errors["base"] = "voltage_out_of_range"
            else:
                preset = BATTERY_PRESETS[battery_type]
                voltage_min = preset["min"]
                voltage_max = preset["max"]

            if not errors:
                return self.async_create_entry(
                    title="",
                    data={
                        CONF_BATTERY_TYPE: battery_type,
                        CONF_VOLTAGE_MIN: voltage_min,
                        CONF_VOLTAGE_MAX: voltage_max,
                        CONF_POLL_INTERVAL: user_input[CONF_POLL_INTERVAL],
                    },
                )

        current_battery_type = self.config_entry.options.get(CONF_BATTERY_TYPE, "12v_lead_acid")
        current_voltage_min = self.config_entry.options.get(CONF_VOLTAGE_MIN)
        current_voltage_max = self.config_entry.options.get(CONF_VOLTAGE_MAX)
        current_poll_interval = self.config_entry.options.get(
            CONF_POLL_INTERVAL, DEFAULT_POLL_INTERVAL
        )

        schema = vol.Schema(
            {
                vol.Required(CONF_BATTERY_TYPE, default=current_battery_type): vol.In(
                    {k: v["name"] for k, v in BATTERY_PRESETS.items()}
                ),
                vol.Optional(CONF_VOLTAGE_MIN, default=current_voltage_min): vol.Coerce(float),
                vol.Optional(CONF_VOLTAGE_MAX, default=current_voltage_max): vol.Coerce(float),
                vol.Required(CONF_POLL_INTERVAL, default=current_poll_interval): vol.All(
                    vol.Coerce(int),
                    vol.Range(min=MIN_POLL_INTERVAL, max=MAX_POLL_INTERVAL),
                ),
            }
        )

        return self.async_show_form(
            step_id="init",
            data_schema=schema,
            errors=errors,
        )
