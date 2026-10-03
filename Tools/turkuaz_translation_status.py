#!/usr/bin/env python3
# Dosya Yolu: /ROenglishRE/Tools/turkuaz_translation_status.py
# Amac: Turkce ceviri dosyalarinin upstream karsisindaki durumunu raporlar
# Modul: Tool - Python
# Version: 1.0.0
# Aciklama: Pinned upstream, guncel upstream ve Turkce dal iceriklerini karsilastirir
# Bagimli Oldugu Katman: Tool

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path


def run_git(repo_root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-C", str(repo_root), *args],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )


def read_git_file(repo_root: Path, ref_name: str, file_path: str) -> str | None:
    result = run_git(repo_root, "show", f"{ref_name}:{file_path}")
    if result.returncode != 0:
        return None
    return result.stdout


def content_hash(content: str | None) -> str:
    if content is None:
        return "-"
    return hashlib.sha256(content.encode("utf-8")).hexdigest()[:12]


def resolve_status(
    base_content: str | None,
    upstream_content: str | None,
    translation_content: str | None,
) -> str:
    if base_content is None or upstream_content is None or translation_content is None:
        return "missing"

    if translation_content == upstream_content:
        return "untranslated"

    if upstream_content == base_content:
        return "translated-current"

    if translation_content == base_content:
        return "upstream-changed-untranslated"

    return "needs-review"


def main() -> int:
    parser = argparse.ArgumentParser(
        description="TurkuazTR translation status reporter."
    )
    parser.add_argument(
        "--repo-root",
        default=None,
        help="Repository root. Defaults to the parent of the Tools directory.",
    )
    parser.add_argument("--upstream-ref", default=None)
    parser.add_argument("--translation-ref", default=None)
    args = parser.parse_args()

    script_path = Path(__file__).resolve()
    repo_root = (
        Path(args.repo_root).resolve()
        if args.repo_root
        else script_path.parent.parent
    )

    config_path = repo_root / "TurkuazTR" / "tracking.json"
    if not config_path.is_file():
        print(f"Config bulunamadi: {config_path}", file=sys.stderr)
        return 2

    config = json.loads(config_path.read_text(encoding="utf-8"))
    base_ref = config["sync_base_sha"]
    upstream_ref = args.upstream_ref or config["default_upstream_ref"]
    translation_ref = args.translation_ref or config["default_translation_ref"]

    print(
        "name".ljust(20),
        "status".ljust(30),
        "base".ljust(14),
        "upstream".ljust(14),
        "translation".ljust(14),
    )
    print("-" * 96)

    missing_count = 0
    review_count = 0

    for item in config["files"]:
        path = item["path"]
        base_content = read_git_file(repo_root, base_ref, path)
        upstream_content = read_git_file(repo_root, upstream_ref, path)
        translation_content = read_git_file(repo_root, translation_ref, path)

        status = resolve_status(
            base_content,
            upstream_content,
            translation_content,
        )

        if status == "missing":
            missing_count += 1
        if status in {"needs-review", "upstream-changed-untranslated"}:
            review_count += 1

        print(
            item["name"].ljust(20),
            status.ljust(30),
            content_hash(base_content).ljust(14),
            content_hash(upstream_content).ljust(14),
            content_hash(translation_content).ljust(14),
        )

    print()
    print(f"Review gereken dosya: {review_count}")
    print(f"Eksik dosya/ref: {missing_count}")

    return 1 if missing_count else 0


if __name__ == "__main__":
    raise SystemExit(main())
