"""Base entity for Konnwei Battery Monitor."""

from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import KonnweiCoordinator


class KonnweiEntity(CoordinatorEntity[KonnweiCoordinator]):
    """Base entity for Konnwei Battery Monitor."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: KonnweiCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the entity.

        Args:
            coordinator: Data update coordinator
            entry: Config entry
        """
        super().__init__(coordinator)
        self._entry = entry
        self._address = entry.data["address"]
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, self._address)},
            name=entry.data.get("name", f"Battery Monitor {self._address}"),
            manufacturer="Konnwei",
            model=coordinator.device_info.get("model"),
            sw_version=coordinator.device_info.get("fw_version"),
        )
