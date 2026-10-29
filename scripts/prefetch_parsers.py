"""Load the tree-sitter grammars into the user cache from vendor/parsers, offline.

Called by install.sh / install.ps1 with the skill's .venv Python.
A platform with no vendored bundle falls back to the upstream download.
"""

import json
import os
import tempfile
from pathlib import Path

ROOT: Path = Path(__file__).resolve().parents[1]
PARSERS_DIR: Path = ROOT / "vendor" / "parsers"
LANGUAGES_FILE: Path = ROOT / "parser-languages.txt"


def local_entry(entry: dict) -> dict:
    bundle: Path = PARSERS_DIR / entry["url"].rsplit("/", 1)[1]
    return {**entry, "url": bundle.as_uri()} if bundle.is_file() else entry


def write_local_manifest(directory: Path) -> Path:
    manifest: dict = json.loads((PARSERS_DIR / "parsers.json").read_text(encoding="utf-8"))
    manifest["platforms"] = {name: local_entry(entry) for name, entry in manifest["platforms"].items()}
    target: Path = directory / "manifest.json"
    target.write_text(json.dumps(manifest), encoding="utf-8")
    return target


def main() -> None:
    with tempfile.TemporaryDirectory() as directory:
        if "TREE_SITTER_LANGUAGE_PACK_MANIFEST_URL" not in os.environ:
            os.environ["TREE_SITTER_LANGUAGE_PACK_MANIFEST_URL"] = write_local_manifest(Path(directory)).as_uri()
        from tree_sitter_language_pack import download

        download(LANGUAGES_FILE.read_text(encoding="utf-8").split())


if __name__ == "__main__":
    main()
