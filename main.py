"""Interactive command-line interface for the local asset risk tool."""

from __future__ import annotations

from pathlib import Path

from asset_risk import Asset, AssetInventory, PATCH_STATUSES


DEFAULT_FILE = Path("assets.json")


def show_assets(inventory: AssetInventory) -> None:
    assets = inventory.all_assets()
    if not assets:
        print("No devices in the inventory yet.")
        return
    print(f"\n{'Device':<22} {'Operating system':<24} {'Patch':<10} {'Risk':<12}")
    print("-" * 72)
    for asset in assets:
        assessment = asset.risk_assessment()
        print(
            f"{asset.name[:21]:<22} {asset.operating_system[:23]:<24} "
            f"{asset.patch_status:<10} "
            f"{assessment['score']:>3}/100 {assessment['level']}"
        )


def add_asset(inventory: AssetInventory) -> None:
    name = input("Device name: ").strip()
    operating_system = input("Operating system: ").strip()
    services_input = input("Open services (comma-separated, or blank): ")
    services = [service.strip() for service in services_input.split(",")]
    patch_status = input(
        f"Patch status ({'/'.join(PATCH_STATUSES)}): "
    ).strip()
    inventory.add_asset(Asset(name, operating_system, services, patch_status))
    print(f"Added {name}.")


def show_assessment(inventory: AssetInventory) -> None:
    asset = inventory.get_asset(input("Device name: "))
    assessment = asset.risk_assessment()
    breakdown = assessment["breakdown"]
    print(f"\n{asset.name}: {assessment['score']}/100 ({assessment['level']})")
    print(f"  Operating system: {breakdown['operating_system']} points")
    print(
        f"  Open services: {breakdown['services']['total']} points "
        f"(cap 30; {breakdown['services']['items']})"
    )
    print(
        f"  Patching ({breakdown['patch_status']['status']}): "
        f"{breakdown['patch_status']['points']} points"
    )


def update_patch_status(inventory: AssetInventory) -> None:
    asset = inventory.get_asset(input("Device name: "))
    status = input(f"New patch status ({'/'.join(PATCH_STATUSES)}): ")
    asset.update_patch_status(status)
    print(f"Updated patch status for {asset.name}.")


def run() -> None:
    inventory = AssetInventory()
    if DEFAULT_FILE.exists():
        inventory = AssetInventory.load(DEFAULT_FILE)
        print(f"Loaded {len(inventory.assets)} device(s) from {DEFAULT_FILE}.")

    actions = {
        "1": ("Add device", lambda: add_asset(inventory)),
        "2": ("List devices and scores", lambda: show_assets(inventory)),
        "3": ("Show risk breakdown", lambda: show_assessment(inventory)),
        "4": ("Update patch status", lambda: update_patch_status(inventory)),
        "5": (
            "Remove device",
            lambda: inventory.remove_asset(input("Device name: ")),
        ),
        "6": ("Save inventory", lambda: inventory.save(DEFAULT_FILE)),
        "7": (
            "Load inventory",
            lambda: replace_inventory(inventory, DEFAULT_FILE),
        ),
    }

    while True:
        print(
            "\nNetwork Asset Risk Inventory\n"
            "1) Add device   2) List devices   3) Risk breakdown\n"
            "4) Update patch status   5) Remove device\n"
            "6) Save   7) Load   0) Save and quit"
        )
        choice = input("Choose an action: ").strip()
        if choice == "0":
            inventory.save(DEFAULT_FILE)
            print(f"Saved inventory to {DEFAULT_FILE}. Goodbye.")
            return
        action = actions.get(choice)
        if action is None:
            print("Choose one of the listed options.")
            continue
        try:
            action[1]()
            if choice == "6":
                print(f"Saved inventory to {DEFAULT_FILE}.")
            elif choice == "7":
                print(f"Loaded inventory from {DEFAULT_FILE}.")
            elif choice == "5":
                print("Device removed.")
        except (ValueError, KeyError, OSError) as error:
            print(f"Could not complete that action: {error}")


def replace_inventory(inventory: AssetInventory, path: Path) -> None:
    loaded = AssetInventory.load(path)
    inventory.assets.clear()
    inventory.assets.update(loaded.assets)


if __name__ == "__main__":
    run()
