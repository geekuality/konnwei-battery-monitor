"""The Konnwei Battery Monitor integration."""

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_ADDRESS, Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers.update_coordinator import UpdateFailed

from .const import CONF_POLL_INTERVAL, DEFAULT_POLL_INTERVAL, DOMAIN
from .coordinator import KonnweiCoordinator

_LOGGER = logging.getLogger(__name__)

PLATFORMS = [Platform.SENSOR, Platform.BINARY_SENSOR]


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Set up the Konnwei Battery Monitor component."""
    hass.data.setdefault(DOMAIN, {})
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Konnwei Battery Monitor from a config entry.

    Args:
        hass: Home Assistant instance
        entry: Config entry

    Returns:
        True if setup succeeded

    Raises:
        ConfigEntryNotReady: If device is unavailable at setup
    """
    address = entry.data[CONF_ADDRESS]
    poll_interval = entry.options.get(CONF_POLL_INTERVAL, DEFAULT_POLL_INTERVAL)

    coordinator = KonnweiCoordinator(hass, address, poll_interval)

    try:
        await coordinator.async_config_entry_first_refresh()
    except UpdateFailed as err:
        raise ConfigEntryNotReady(f"Device unavailable: {err}") from err

    hass.data[DOMAIN][entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    entry.async_on_unload(entry.add_update_listener(async_update_listener))

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry.

    Args:
        hass: Home Assistant instance
        entry: Config entry

    Returns:
        True if unload succeeded
    """
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok


async def async_update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Handle options update.

    Args:
        hass: Home Assistant instance
        entry: Config entry
    """
    await hass.config_entries.async_reload(entry.entry_id)


async def async_get_config_entry_diagnostics(hass: HomeAssistant, entry: ConfigEntry) -> dict:
    """Return diagnostics for config entry.

    Args:
        hass: Home Assistant instance
        entry: Config entry

    Returns:
        Dict with diagnostic information
    """
    coordinator: KonnweiCoordinator = hass.data[DOMAIN][entry.entry_id]

    return {
        "device_info": coordinator.device_info,
        "last_update_success": coordinator.last_update_success,
        "last_update_time": (
            coordinator.last_update_time.isoformat() if coordinator.last_update_time else None
        ),
        "data": coordinator.data,
        "options": dict(entry.options),
        "config": {
            "address": entry.data.get(CONF_ADDRESS),
            "name": entry.data.get("name"),
        },
    }


async def async_migrate_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Migrate old entry.

    Args:
        hass: Home Assistant instance
        entry: Config entry

    Returns:
        True if migration succeeded
    """
    _LOGGER.debug("Migrating from version %s", entry.version)

    if entry.version == 1:
        return True

    return False
