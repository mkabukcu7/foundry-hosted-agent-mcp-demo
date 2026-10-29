"""Stage an allowlisted Foundry code package without a registry or local secrets."""

from pathlib import Path
import shutil


ROOT = Path(__file__).resolve().parents[1]
DESTINATION = ROOT / "deployment" / "contract-assurance" / ".build" / "agent-code"


def stage(destination=DESTINATION):
    destination.mkdir(parents=True, exist_ok=True)
    for package in ("agent", "shared"):
        target = destination / package
        target.mkdir(exist_ok=True)
        for source in (ROOT / package).glob("*.py"):
            shutil.copyfile(source, target / source.name)
    for source in (ROOT / "agent").glob("requirements*.txt"):
        shutil.copyfile(source, destination / "agent" / source.name)
    source = ROOT / "deployment" / "contract-assurance"
    for name in ("main.py", "requirements.txt"):
        shutil.copyfile(source / name, destination / name)
    shutil.copyfile(ROOT / "agent" / ".agentignore", destination / ".agentignore")
    print(f"Staged source-only assurance package at {destination}")
    return destination


if __name__ == "__main__":
    stage()