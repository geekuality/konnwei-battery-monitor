"""Binary sensor platform for Konnwei Battery Monitor."""

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import KonnweiCoordinator
from .entity import KonnweiEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up binary sensor platform.

    Args:
        hass: Home Assistant instance
        entry: Config entry
        async_add_entities: Callback to add entities
    """
    coordinator: KonnweiCoordinator = hass.data[DOMAIN][entry.entry_id]

    async_add_entities(
        [
            BatteryStatusSensor(coordinator, entry),
            ChargingSensor(coordinator, entry),
        ]
    )


class BatteryStatusSensor(KonnweiEntity, BinarySensorEntity):
    """Battery status sensor (low/OK)."""

    _attr_device_class = BinarySensorDeviceClass.BATTERY

    def __init__(self, coordinator: KonnweiCoordinator, entry: ConfigEntry) -> None:
        """Initialize battery status sensor."""
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{self._address}_battery_status"
        self._attr_name = "Battery status"

    @property
    def is_on(self) -> bool | None:
        """Return True if battery is low."""
        if not self.coordinator.data:
            return None
        battery_ok = self.coordinator.data.get("battery_ok")
        if battery_ok is None:
            return None
        return not battery_ok


class ChargingSensor(KonnweiEntity, BinarySensorEntity):
    """Charging indicator sensor."""

    _attr_device_class = BinarySensorDeviceClass.BATTERY_CHARGING

    def __init__(self, coordinator: KonnweiCoordinator, entry: ConfigEntry) -> None:
        """Initialize charging sensor."""
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{self._address}_charging"
        self._attr_name = "Charging"

    @property
    def is_on(self) -> bool | None:
        """Return True if charging."""
        if not self.coordinator.data:
            return None
        charging = self.coordinator.data.get("charging")
        if charging is None:
            return None
        return not charging
