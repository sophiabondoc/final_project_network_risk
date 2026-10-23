import json
import tempfile
import unittest
from pathlib import Path

from asset_risk import Asset, AssetInventory


class AssetRiskTests(unittest.TestCase):
    def test_assessment_includes_nested_service_breakdown_and_caps_services(self):
        asset = Asset(
            "edge-router",
            "Windows XP",
            ["telnet", "ftp", "rdp", "unknown-daemon"],
            "Overdue",
        )

        assessment = asset.risk_assessment()

        self.assertEqual(85, assessment["score"])
        self.assertEqual("Critical", assessment["level"])
        self.assertEqual(30, assessment["breakdown"]["services"]["total"])
        self.assertEqual(18, assessment["breakdown"]["services"]["items"]["telnet"])

    def test_unknown_service_and_patch_status_add_risk(self):
        asset = Asset("camera-1", "Embedded Linux", ["custom"], "Unknown")

        assessment = asset.risk_assessment()

        self.assertEqual(24, assessment["score"])
        self.assertEqual(4, assessment["breakdown"]["services"]["items"]["custom"])

    def test_asset_validation_normalizes_values_and_deduplicates_services(self):
        asset = Asset("  laptop  ", "  Ubuntu  ", ["ssh", " ssh ", ""], "current")

        self.assertEqual("laptop", asset.name)
        self.assertEqual(["ssh"], asset.services)
        self.assertEqual("Current", asset.patch_status)

    def test_patch_status_update_validates_input(self):
        asset = Asset("laptop", "Ubuntu", [], "Current")

        with self.assertRaisesRegex(ValueError, "Patch status"):
            asset.update_patch_status("not a patch state")

        self.assertEqual("Current", asset.patch_status)

    def test_inventory_save_load_round_trip(self):
        inventory = AssetInventory()
        inventory.add_asset(Asset("Laptop-1", "Windows 11", ["https"], "Current"))
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "assets.json"

            inventory.save(path)
            loaded = AssetInventory.load(path)

        self.assertEqual(
            inventory.get_asset("laptop-1").to_dict(),
            loaded.get_asset("LAPTOP-1").to_dict(),
        )

    def test_duplicate_names_are_case_insensitive(self):
        inventory = AssetInventory()
        inventory.add_asset(Asset("Switch-1", "Linux", [], "Current"))

        with self.assertRaisesRegex(ValueError, "already exists"):
            inventory.add_asset(Asset("switch-1", "Linux", [], "Current"))

    def test_rejects_invalid_inventory_schema(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "assets.json"
            path.write_text(json.dumps({"schema_version": 99, "assets": {}}))

            with self.assertRaisesRegex(ValueError, "Unsupported"):
                AssetInventory.load(path)


if __name__ == "__main__":
    unittest.main()
