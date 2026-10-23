"""Local asset inventory and transparent, rule-based risk scoring."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


SCHEMA_VERSION = 1
PATCH_STATUSES = ("Current", "Behind", "Unknown", "Overdue")

SERVICE_RISK: dict[str, int] = {
    "telnet": 18,
    "ftp": 12,
    "rdp": 12,
    "smb": 12,
    "mysql": 10,
    "postgres": 10,
    "ssh": 4,
    "http": 3,
    "https": 1,
}

OS_RISK_CUES: dict[str, int] = {
    "windows xp": 25,
    "windows vista": 25,
    "windows 7": 25,
    "windows 8": 20,
    "windows server 2003": 25,
    "windows server 2008": 25,
    "unsupported": 25,
    "end of life": 25,
    "legacy": 15,
}


def _normalize_patch_status(status: str) -> str:
    if not isinstance(status, str):
        raise ValueError("Patch status must be text.")
    normalized = status.strip().casefold()
    for valid_status in PATCH_STATUSES:
        if normalized == valid_status.casefold():
            return valid_status
    raise ValueError(f"Patch status must be one of: {', '.join(PATCH_STATUSES)}.")


@dataclass
class Asset:
    """A device and the user-supplied facts used to assess its risk."""

    name: str
    operating_system: str
    services: list[str]
    patch_status: str

    def __post_init__(self) -> None:
        if not isinstance(self.name, str):
            raise ValueError("Device name must be text.")
        if not isinstance(self.operating_system, str):
            raise ValueError("Operating system must be text.")
        self.name = self.name.strip()
        self.operating_system = self.operating_system.strip()
        if not self.name:
            raise ValueError("Device name cannot be empty.")
        if not self.operating_system:
            raise ValueError("Operating system cannot be empty.")
        if not isinstance(self.services, list) or not all(
            isinstance(service, str) for service in self.services
        ):
            raise ValueError("Services must be a list of service names.")
        self.services = list(
            dict.fromkeys(service.strip() for service in self.services if service.strip())
        )
        self.patch_status = _normalize_patch_status(self.patch_status)

    def update_patch_status(self, status: str) -> None:
        self.patch_status = _normalize_patch_status(status)

    def risk_assessment(self) -> dict[str, Any]:
        """Return a reproducible score and a category-by-category explanation."""
        operating_system_risk = 0
        os_name = self.operating_system.casefold()
        for cue, points in OS_RISK_CUES.items():
            if cue in os_name:
                operating_system_risk = max(operating_system_risk, points)

        service_risks = {
            service: SERVICE_RISK.get(service.casefold(), 4)
            for service in self.services
        }
        service_risk = min(sum(service_risks.values()), 30)
        patch_risk = {
            "Current": 0,
            "Behind": 15,
            "Unknown": 20,
            "Overdue": 30,
        }[self.patch_status]
        score = min(100, operating_system_risk + service_risk + patch_risk)

        if score >= 75:
            level = "Critical"
        elif score >= 50:
            level = "High"
        elif score >= 25:
            level = "Medium"
        else:
            level = "Low"

        return {
            "score": score,
            "level": level,
            "breakdown": {
                "operating_system": operating_system_risk,
                "services": {"items": service_risks, "total": service_risk},
                "patch_status": {"status": self.patch_status, "points": patch_risk},
            },
        }

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "operating_system": self.operating_system,
            "services": self.services,
            "patch_status": self.patch_status,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Asset:
        required = {"name", "operating_system", "services", "patch_status"}
        if not isinstance(data, dict) or not required.issubset(data):
            raise ValueError("Asset record is missing one or more required fields.")
        if not isinstance(data["name"], str) or not isinstance(
            data["operating_system"], str
        ):
            raise ValueError("Asset name and operating system must be text.")
        return cls(
            name=data["name"],
            operating_system=data["operating_system"],
            services=data["services"],
            patch_status=data["patch_status"],
        )


class AssetInventory:
    """Manage assets indexed by a case-insensitive device name."""

    def __init__(self) -> None:
        self.assets: dict[str, Asset] = {}

    @staticmethod
    def _key(name: str) -> str:
        return name.strip().casefold()

    def add_asset(self, asset: Asset) -> None:
        key = self._key(asset.name)
        if key in self.assets:
            raise ValueError(f"An asset named {asset.name!r} already exists.")
        self.assets[key] = asset

    def get_asset(self, name: str) -> Asset:
        try:
            return self.assets[self._key(name)]
        except KeyError as error:
            raise KeyError(f"No asset named {name!r} exists.") from error

    def remove_asset(self, name: str) -> Asset:
        try:
            return self.assets.pop(self._key(name))
        except KeyError as error:
            raise KeyError(f"No asset named {name!r} exists.") from error

    def all_assets(self) -> list[Asset]:
        return sorted(self.assets.values(), key=lambda asset: asset.name.casefold())

    def save(self, path: str | Path) -> None:
        target = Path(path)
        data = {
            "schema_version": SCHEMA_VERSION,
            "assets": {key: asset.to_dict() for key, asset in self.assets.items()},
        }
        target.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")

    @classmethod
    def load(cls, path: str | Path) -> AssetInventory:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        if not isinstance(data, dict) or data.get("schema_version") != SCHEMA_VERSION:
            raise ValueError(
                f"Unsupported or invalid inventory file (expected schema {SCHEMA_VERSION})."
            )
        records = data.get("assets")
        if not isinstance(records, dict):
            raise ValueError("Inventory file must contain an assets object.")

        inventory = cls()
        for key, record in records.items():
            asset = Asset.from_dict(record)
            if key != inventory._key(asset.name):
                raise ValueError(f"Asset key does not match device name {asset.name!r}.")
            inventory.add_asset(asset)
        return inventory
