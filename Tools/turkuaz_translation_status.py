#!/usr/bin/env python3
# Dosya Yolu: /ROenglishRE/Tools/turkuaz_translation_status.py
# Amac: Turkce ceviri dosyalarinin upstream karsisindaki durumunu raporlar
# Modul: Tool - Python
# Version: 2.0.0
# Aciklama: Dosya senkronuna ek olarak canonical overlay patch, source blob ve generated profil durumunu raporlar
# Bagimli Oldugu Katman: Tool

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path


def run_git(repo_root: Path, *args: str) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(
        ["git", "-C", str(repo_root), *args],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )


def read_git_file(repo_root: Path, ref_name: str, file_path: str) -> bytes | None:
    result = run_git(repo_root, "show", f"{ref_name}:{file_path}")
    if result.returncode != 0:
        return None
    return result.stdout


def git_blob_sha(repo_root: Path, ref_name: str, file_path: str) -> str | None:
    result = run_git(repo_root, "rev-parse", f"{ref_name}:{file_path}")
    if result.returncode != 0:
        return None
    return result.stdout.decode("ascii", errors="ignore").strip()


def content_hash(content: bytes | None) -> str:
    if content is None:
        return "-"
    return hashlib.sha256(content).hexdigest()[:12]


def resolve_status(
    base_content: bytes | None,
    upstream_content: bytes | None,
    translation_content: bytes | None,
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


def overlay_status(
    repo_root: Path,
    upstream_ref: str,
    item: dict,
) -> tuple[str, int | str, int]:
    patch_path = item.get("patch_path")
    if not patch_path:
        return "-", "-", 0

    absolute_patch = repo_root / patch_path
    if not absolute_patch.is_file():
        return "patch-missing", "-", len(item.get("generated_profiles", []))

    patch = json.loads(absolute_patch.read_text(encoding="utf-8"))
    patch_count = patch.get("patch_count")
    if patch_count is None and isinstance(patch.get("patches"), dict):
        patch_count = len(patch["patches"])
    if patch_count is None:
        patch_count = "whole"

    expected_blob = patch.get("source_blob_sha")
    if expected_blob:
        actual_blob = git_blob_sha(repo_root, upstream_ref, item["path"])
        status = "overlay-current" if actual_blob == expected_blob else "overlay-source-changed"
    elif item.get("overlay_type") == "record":
        status = "record-overlay"
    else:
        status = "overlay-unpinned"

    return status, patch_count, len(item.get("generated_profiles", []))


def audit_msgstringtable(
    upstream_content: bytes,
    translation_content: bytes,
    intentional_lines: set[bytes],
) -> tuple[int, int, int, int]:
    upstream_lines = upstream_content.replace(b"\r\n", b"\n").split(b"\n")
    translation_lines = translation_content.replace(b"\r\n", b"\n").split(b"\n")

    translated = 0
    intentional = 0
    review = 0
    comparable = min(len(upstream_lines), len(translation_lines))

    for upstream_line, translation_line in zip(upstream_lines, translation_lines):
        if upstream_line != translation_line:
            translated += 1
            continue

        if not re.search(rb"[A-Za-z]{4,}", upstream_line):
            continue

        if (
            upstream_line.startswith(b"MSI_")
            or upstream_line.startswith(b"http://")
            or upstream_line.startswith(b"https://")
            or upstream_line.startswith(b"ftp://")
            or re.match(rb"^/[A-Za-z0-9]", upstream_line)
        ):
            intentional += 1
            continue

        if upstream_line in intentional_lines:
            intentional += 1
        else:
            review += 1

    return comparable, translated, intentional, review


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
    intentional_path = repo_root / "TurkuazTR" / "intentional-english.json"

    if not config_path.is_file():
        print(f"Config bulunamadi: {config_path}", file=sys.stderr)
        return 2
    if not intentional_path.is_file():
        print(f"Intentional English config bulunamadi: {intentional_path}", file=sys.stderr)
        return 2

    config = json.loads(config_path.read_text(encoding="utf-8"))
    intentional_config = json.loads(intentional_path.read_text(encoding="utf-8"))
    intentional_lines = {
        line.encode("utf-8") for line in intentional_config.get("exact_lines", [])
    }

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
    msg_audit = None

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

        if (
            item["name"] == "msgstringtable"
            and upstream_content is not None
            and translation_content is not None
        ):
            msg_audit = audit_msgstringtable(
                upstream_content,
                translation_content,
                intentional_lines,
            )

    print()
    print(f"Review gereken dosya: {review_count}")
    print(f"Eksik dosya/ref: {missing_count}")

    print()
    print("Canonical overlay durumu:")
    print(
        "name".ljust(20),
        "overlay".ljust(26),
        "patch".ljust(10),
        "profiles".ljust(10),
    )
    print("-" * 70)

    overlay_error_count = 0
    for item in config["files"]:
        status, patch_count, profile_count = overlay_status(
            repo_root,
            upstream_ref,
            item,
        )
        if status == "-":
            continue
        if status in {"patch-missing", "overlay-source-changed", "overlay-unpinned"}:
            overlay_error_count += 1
        print(
            item["name"].ljust(20),
            status.ljust(26),
            str(patch_count).ljust(10),
            str(profile_count).ljust(10),
        )

    print()
    print(f"Overlay source/patch hatasi: {overlay_error_count}")

    if msg_audit is not None:
        comparable, translated, intentional, review = msg_audit
        print()
        print("msgstringtable satir denetimi:")
        print(f"  Karsilastirilabilir satir: {comparable}")
        print(f"  Turkcelestirilmis/uyarlanmis: {translated}")
        print(f"  Bilincli Ingilizce/teknik: {intentional}")
        print(f"  Gercek ceviri incelemesi gereken: {review}")

    return 1 if (missing_count or overlay_error_count) else 0


if __name__ == "__main__":
    raise SystemExit(main())
