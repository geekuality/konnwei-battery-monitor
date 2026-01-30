"""Pytest configuration for tests."""

import sys
from pathlib import Path

# Add the custom_components directory to Python path
project_root = Path(__file__).parent.parent
custom_components_path = project_root / "custom_components" / "konnwei_battery_monitor"
sys.path.insert(0, str(custom_components_path))
