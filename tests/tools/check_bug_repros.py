import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def run(args):
    return subprocess.run(
        [sys.executable, "-m", "pytest", "-q", *args],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )


def main():
    control = run(["-m", "not bug and not integration", "tests"])
    if control.returncode != 0:
        print(control.stdout)
        print(control.stderr)
        print("control tests are not green")
        return 1

    collected = run(["--collect-only", "-m", "bug and not integration", "tests"])
    match = re.search(r"(\d+)(?:/\d+)? tests? collected", collected.stdout)
    if collected.returncode != 0 or match is None:
        print(collected.stdout)
        print(collected.stderr)
        print("could not count bug tests")
        return 1
    expected = int(match.group(1))
    if expected == 0:
        print("no bug tests were collected")
        return 1

    regressions = run(["-m", "bug and not integration", "tests"])
    if regressions.returncode != 0:
        print(regressions.stdout)
        print(regressions.stderr)
        print("bug regression tests are not green")
        return 1

    print(f"bug regressions confirmed ({expected})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
