# Network Asset Risk Inventory

A small, local-only Python command-line tool for recording devices, their
operating systems, open services, and patch status. It assigns each device a
transparent, rule-based risk score and saves inventory data as JSON.

## Two-week project milestones

### Week 1 — Inventory foundation

- Added `Asset` and `AssetInventory` classes.
- Captured device names, operating systems, open services, and patch status.
- Built a case-insensitive asset dictionary and nested service-risk breakdown.
- Implemented JSON save/load with a versioned file format.

### Week 2 — Risk scoring and usable CLI

- Added a documented scoring rubric and Low/Medium/High/Critical bands.
- Added an interactive menu for adding, listing, inspecting, updating, removing,
  saving, and loading devices.
- Added automated tests for scoring, validation, duplicate names, and persistence.

## Requirements and run

- Python 3.10 or newer; no third-party packages required.
- From the project directory, run:

```powershell
python main.py
```

The program reads and writes `assets.json` in the current directory. Use menu
option `0` to save and quit, or `6` and `7` to save/load at any time.

Run the tests with:

```powershell
python -m unittest discover -s tests -v
```

## Scoring rubric

The total is the sum of the following user-visible factors, capped at 100:

- **Operating system:** 25 points for explicitly unsupported/end-of-life
  systems in the built-in cue list; 15 for systems described as legacy; 0
  otherwise.
- **Open services:** weighted points by service (for example, Telnet 18,
  FTP/RDP/SMB 12, SSH 4, HTTP 3, HTTPS 1); unlisted services add 4 each.
  Service points are capped at 30.
- **Patch status:** Current 0, Behind 15, Unknown 20, Overdue 30.
- **Bands:** Low 0–24, Medium 25–49, High 50–74, Critical 75–100.

These are simple prioritization heuristics, not vulnerability findings. The
tool does not scan, connect to, or probe devices, and its OS cue list is not a
comprehensive support-lifecycle database. Confirm asset facts and validate
priorities with your organization's security process. Inventory data is stored
locally as plain JSON; protect the file according to your organization's
requirements.
