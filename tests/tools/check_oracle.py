import subprocess
import sys
import tempfile
from pathlib import Path


def run_pytest(path):
    return subprocess.run(
        [sys.executable, "-m", "pytest", "-q", str(path)],
        cwd=path.parent,
        capture_output=True,
        text=True,
    )


def main():
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        passing = root / "test_ok.py"
        passing.write_text("def test_ok():\n    assert True\n")
        failing = root / "test_bad.py"
        failing.write_text("def test_bad():\n    assert False\n")

        good = run_pytest(passing)
        bad = run_pytest(failing)

    if good.returncode != 0:
        print(good.stdout)
        print(good.stderr)
        print("oracle did not pass a passing test")
        return 1
    if bad.returncode == 0:
        print(bad.stdout)
        print(bad.stderr)
        print("oracle did not fail a failing test")
        return 1

    print("oracle ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
