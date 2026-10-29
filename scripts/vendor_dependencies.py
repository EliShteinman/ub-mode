"""Download every wheel and parser bundle into vendor/ so installs need no network.

Maintainer use only, on a machine with internet, after changing requirements.lock:
    <skill-dir>/.venv/bin/python scripts/vendor_dependencies.py [--platform P ...]
"""

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
import urllib.request
from importlib.metadata import version
from pathlib import Path

ROOT: Path = Path(__file__).resolve().parents[1]
WHEELS_DIR: Path = ROOT / "vendor" / "wheels"
PARSERS_DIR: Path = ROOT / "vendor" / "parsers"
LOCK_FILE: Path = ROOT / "requirements.lock"
PYTHON_VERSIONS: list[str] = ["3.11", "3.12", "3.13", "3.14"]
DEFAULT_PLATFORMS: list[str] = ["linux-x86_64", "windows-x86_64"]
WHEEL_TAGS: dict[str, list[str]] = {
    "linux-x86_64": ["manylinux_2_17_x86_64", "manylinux2014_x86_64", "manylinux_2_28_x86_64", "manylinux_2_34_x86_64"],
    "linux-aarch64": ["manylinux_2_17_aarch64", "manylinux2014_aarch64", "manylinux_2_28_aarch64", "manylinux_2_34_aarch64"],
    "windows-x86_64": ["win_amd64"],
    "macos-arm64": ["macosx_11_0_arm64", "macosx_14_0_arm64"],
}
UPSTREAM_RELEASES: str = "https://github.com/xberg-io/tree-sitter-language-pack/releases/download"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Vendor wheels and parser bundles.")
    parser.add_argument("--platform", action="append", dest="platforms", choices=sorted(WHEEL_TAGS))
    return parser.parse_args()


def requirements_without_markers() -> Path:
    lines: list[str] = LOCK_FILE.read_text(encoding="utf-8").splitlines()
    pinned: list[str] = [line.split(";")[0].strip() for line in lines if line.strip()]
    target: Path = WHEELS_DIR / "requirements.txt"
    target.write_text("\n".join(pinned) + "\n", encoding="utf-8")
    return target


def download_wheels(platform: str, python_version: str, requirements: Path) -> None:
    tags: list[str] = [arg for tag in WHEEL_TAGS[platform] for arg in ("--platform", tag)]
    print(f"Wheels for {platform}, Python {python_version}")
    subprocess.run(
        [sys.executable, "-m", "pip", "download", "--quiet", "--only-binary=:all:",
         "--implementation", "cp", "--python-version", python_version, *tags,
         "-r", str(requirements), "-d", str(WHEELS_DIR)],
        check=True,
    )


def upstream_manifest() -> dict:
    url: str = f"{UPSTREAM_RELEASES}/v{version('tree-sitter-language-pack')}/parsers.json"
    with urllib.request.urlopen(url) as response:
        return json.load(response)


def download_bundle(entry: dict) -> None:
    destination: Path = PARSERS_DIR / entry["url"].rsplit("/", 1)[1]
    print(f"Parsers {destination.name}")
    with urllib.request.urlopen(entry["url"]) as response, destination.open("wb") as file:
        shutil.copyfileobj(response, file)
    if hashlib.sha256(destination.read_bytes()).hexdigest() != entry["sha256"]:
        destination.unlink()
        raise SystemExit(f"Checksum mismatch for {entry['url']}")


def main() -> None:
    platforms: list[str] = parse_args().platforms or DEFAULT_PLATFORMS
    for directory in (WHEELS_DIR, PARSERS_DIR):
        shutil.rmtree(directory, ignore_errors=True)
        directory.mkdir(parents=True)
    requirements: Path = requirements_without_markers()
    for platform in platforms:
        for python_version in PYTHON_VERSIONS:
            download_wheels(platform, python_version, requirements)
    requirements.unlink()
    manifest: dict = upstream_manifest()
    (PARSERS_DIR / "parsers.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    for platform in platforms:
        download_bundle(manifest["platforms"][platform])


if __name__ == "__main__":
    main()
