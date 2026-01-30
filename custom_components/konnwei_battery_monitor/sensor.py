"""Sensor platform for Konnwei Battery Monitor."""

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import PERCENTAGE, UnitOfElectricPotential
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import CONF_VOLTAGE_MAX, CONF_VOLTAGE_MIN, DOMAIN
from .coordinator import KonnweiCoordinator
from .entity import KonnweiEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up sensor platform.

    Args:
        hass: Home Assistant instance
        entry: Config entry
        async_add_entities: Callback to add entities
    """
    coordinator: KonnweiCoordinator = hass.data[DOMAIN][entry.entry_id]

    async_add_entities(
        [
            VoltageSensor(coordinator, entry),
            BatterySoCSensor(coordinator, entry),
            ModelSensor(coordinator, entry),
            FirmwareSensor(coordinator, entry),
        ]
    )


class VoltageSensor(KonnweiEntity, SensorEntity):
    """Voltage sensor."""

    _attr_device_class = SensorDeviceClass.VOLTAGE
    _attr_native_unit_of_measurement = UnitOfElectricPotential.VOLT
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_suggested_display_precision = 2

    def __init__(self, coordinator: KonnweiCoordinator, entry: ConfigEntry) -> None:
        """Initialize voltage sensor."""
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{self._address}_voltage"
        self._attr_name = "Voltage"

    @property
    def native_value(self) -> float | None:
        """Return voltage value."""
        if not self.coordinator.data:
            return None
        return self.coordinator.data.get("voltage")


class BatterySoCSensor(KonnweiEntity, SensorEntity):
    """Battery State of Charge sensor."""

    _attr_device_class = SensorDeviceClass.BATTERY
    _attr_native_unit_of_measurement = PERCENTAGE
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_suggested_display_precision = 0

    def __init__(self, coordinator: KonnweiCoordinator, entry: ConfigEntry) -> None:
        """Initialize SoC sensor."""
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{self._address}_battery_soc"
        self._attr_name = "Battery"

    @property
    def native_value(self) -> int | None:
        """Return battery SoC percentage."""
        if not self.coordinator.data:
            return None

        voltage = self.coordinator.data.get("voltage")
        if voltage is None:
            return None

        voltage_min = self._entry.options.get(CONF_VOLTAGE_MIN)
        voltage_max = self._entry.options.get(CONF_VOLTAGE_MAX)

        if voltage_min is None or voltage_max is None:
            return None

        if voltage_max <= voltage_min:
            return None

        soc = ((voltage - voltage_min) / (voltage_max - voltage_min)) * 100
        return max(0, min(100, int(soc)))


class ModelSensor(KonnweiEntity, SensorEntity):
    """Device model sensor."""

    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, coordinator: KonnweiCoordinator, entry: ConfigEntry) -> None:
        """Initialize model sensor."""
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{self._address}_model"
        self._attr_name = "Model"

    @property
    def native_value(self) -> str | None:
        """Return device model."""
        return self.coordinator.device_info.get("model")


class FirmwareSensor(KonnweiEntity, SensorEntity):
    """Firmware version sensor."""

    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, coordinator: KonnweiCoordinator, entry: ConfigEntry) -> None:
        """Initialize firmware sensor."""
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{self._address}_firmware"
        self._attr_name = "Firmware"

    @property
    def native_value(self) -> str | None:
        """Return firmware version."""
        return self.coordinator.device_info.get("fw_version")
