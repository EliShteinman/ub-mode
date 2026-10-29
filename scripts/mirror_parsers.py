"""Build the tree-sitter parser files to upload to an internal mirror.

Usage (on a machine with internet, after install.sh / install.ps1):
    <skill-dir>/.venv/bin/python scripts/mirror_parsers.py <mirror-base-url> [--out DIR] [--platform P ...]

Upload everything in DIR to <mirror-base-url>, then on every machine set
TREE_SITTER_LANGUAGE_PACK_MANIFEST_URL=<mirror-base-url>/manifest.json
"""

import argparse
import hashlib
import json
import shutil
import urllib.request
from importlib.metadata import version
from pathlib import Path

DEFAULT_PLATFORMS: list[str] = ["linux-x86_64", "windows-x86_64"]
UPSTREAM_RELEASES: str = "https://github.com/xberg-io/tree-sitter-language-pack/releases/download"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build an internal tree-sitter parser mirror.")
    parser.add_argument("base_url", help="URL the uploaded files will be served from")
    parser.add_argument("--out", type=Path, default=Path("parser-mirror"))
    parser.add_argument("--platform", action="append", dest="platforms")
    return parser.parse_args()


def upstream_manifest() -> dict:
    url: str = f"{UPSTREAM_RELEASES}/v{version('tree-sitter-language-pack')}/parsers.json"
    print(f"Downloading {url}")
    with urllib.request.urlopen(url) as response:
        return json.load(response)


def fetch_verified(url: str, sha256: str, destination: Path) -> None:
    print(f"Downloading {url}")
    with urllib.request.urlopen(url) as response, destination.open("wb") as file:
        shutil.copyfileobj(response, file)
    actual: str = hashlib.sha256(destination.read_bytes()).hexdigest()
    if actual != sha256:
        destination.unlink()
        raise SystemExit(f"Checksum mismatch for {url}")


def mirror_platform(entry: dict, base_url: str, out: Path) -> dict:
    file_name: str = entry["url"].rsplit("/", 1)[1]
    fetch_verified(entry["url"], entry["sha256"], out / file_name)
    return {**entry, "url": f"{base_url.rstrip('/')}/{file_name}"}


def main() -> None:
    args: argparse.Namespace = parse_args()
    platforms: list[str] = args.platforms or DEFAULT_PLATFORMS
    args.out.mkdir(parents=True, exist_ok=True)
    manifest: dict = upstream_manifest()
    manifest["platforms"] = {
        name: mirror_platform(manifest["platforms"][name], args.base_url, args.out)
        for name in platforms
    }
    (args.out / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"Upload the contents of {args.out} to {args.base_url}")
    print(f"Then set TREE_SITTER_LANGUAGE_PACK_MANIFEST_URL={args.base_url.rstrip('/')}/manifest.json")


if __name__ == "__main__":
    main()
