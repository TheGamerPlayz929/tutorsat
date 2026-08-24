import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "web"
DST = ROOT / "site"

PRESERVE = {"config.js"}


def main():
    if not DST.exists():
        DST.mkdir(parents=True)
    copied = []
    for item in SRC.iterdir():
        if item.name in PRESERVE:
            continue
        target = DST / item.name
        if item.is_file():
            shutil.copy2(item, target)
        else:
            shutil.copytree(item, target, dirs_exist_ok=True)
        copied.append(item.name)
    print("synced:", ", ".join(sorted(copied)))
    preserved = [p.name for p in DST.iterdir()
                 if p.name in PRESERVE and p.exists()]
    print("preserved:", ", ".join(sorted(preserved)) or "(none)")
    if len(sys.argv) > 1 and sys.argv[1] == "--deploy":
        import subprocess
        subprocess.run(["firebase.cmd", "deploy", "--only", "hosting"],
                       cwd=str(ROOT), check=True)


if __name__ == "__main__":
    main()
