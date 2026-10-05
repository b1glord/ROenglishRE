#!/usr/bin/env python3
# 📄 Dosya Yolu: /ROenglishRE/Tools/apply_questid2display_translation.py
# 📌 Amac: questid2display.txt Turkce patchlerini kaynak byte yapisini ve satir sonlarini koruyarak uygular
# 📌 Tool - Python
# Version: 2.1.0
# Aciklama: Upstream blobu byte olarak okur; yalnizca hedef quest alanlarini ASCII byte ile degistirir ve diger byte'lari birebir korur
# Bagimli Oldugu Katman: Tool

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

HEADER_RE = re.compile(rb"^(\d+)#([^#]*)#([^#]*)#([^#]*)#$")


def git_show(repo_root: Path, ref_name: str, path: str) -> bytes:
    result = subprocess.run(
        ["git", "-C", str(repo_root), "show", f"{ref_name}:{path}"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if result.returncode != 0:
        sys.stderr.buffer.write(result.stderr)
        raise SystemExit(2)
    return result.stdout


def split_content_and_eol(line: bytes) -> tuple[bytes, bytes]:
    if line.endswith(b"\r\n"):
        return line[:-2], b"\r\n"
    if line.endswith(b"\n"):
        return line[:-1], b"\n"
    if line.endswith(b"\r"):
        return line[:-1], b"\r"
    return line, b""


def ascii_field(value: str, quest_id: str, field: str) -> bytes:
    if "#" in value:
        raise ValueError(f"{quest_id}.{field}: '#' ayiraci kullanilamaz")
    try:
        return value.encode("ascii")
    except UnicodeEncodeError as exc:
        raise ValueError(f"{quest_id}.{field}: ASCII disi karakter var") from exc


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Apply encoding-safe Turkish questid2display patches."
    )
    parser.add_argument("--repo-root", default=None)
    parser.add_argument(
        "--path",
        default="Translation/Renewal/data/questid2display.txt",
    )
    parser.add_argument(
        "--patch",
        default="TurkuazTR/questid2display.tr.json",
    )
    parser.add_argument(
        "--source-ref",
        default="refs/remotes/origin/upstream/latest",
    )
    args = parser.parse_args()

    script_path = Path(__file__).resolve()
    repo_root = Path(args.repo_root).resolve() if args.repo_root else script_path.parent.parent
    patch_path = repo_root / args.patch
    config = json.loads(patch_path.read_text(encoding="utf-8"))
    patches = config["patches"]

    source = git_show(repo_root, args.source_ref, args.path)
    source_lines = source.splitlines(keepends=True)
    output_lines = list(source_lines)
    applied: set[str] = set()
    allowed_indexes: set[int] = set()

    for index, raw_line in enumerate(source_lines):
        line, eol = split_content_and_eol(raw_line)
        match = HEADER_RE.match(line)
        if not match:
            continue

        quest_id = match.group(1).decode("ascii")
        patch = patches.get(quest_id)
        if patch is None:
            continue

        if index + 2 >= len(source_lines):
            raise ValueError(f"{quest_id}: eksik quest kayit satiri")

        title = ascii_field(patch["title"], quest_id, "title")
        description = ascii_field(patch.get("description", ""), quest_id, "description")
        goal = ascii_field(patch.get("goal", ""), quest_id, "goal")

        _, desc_eol = split_content_and_eol(source_lines[index + 1])
        _, goal_eol = split_content_and_eol(source_lines[index + 2])

        output_lines[index] = (
            match.group(1)
            + b"#"
            + title
            + b"#"
            + match.group(3)
            + b"#"
            + match.group(4)
            + b"#"
            + eol
        )
        output_lines[index + 1] = description + b"#" + desc_eol
        output_lines[index + 2] = goal + b"#" + goal_eol
        allowed_indexes.update({index, index + 1, index + 2})
        applied.add(quest_id)

    missing = sorted(set(patches) - applied, key=int)
    if missing:
        print(
            "Upstream dosyada bulunamayan patch quest ID'leri: " + ", ".join(missing),
            file=sys.stderr,
        )
        return 1

    if len(output_lines) != len(source_lines):
        print("Satir sayisi degisti.", file=sys.stderr)
        return 1

    for index, (before, after) in enumerate(zip(source_lines, output_lines)):
        if index not in allowed_indexes and before != after:
            print(
                f"Patch disi byte degisikligi bulundu: satir {index + 1}",
                file=sys.stderr,
            )
            return 1

        before_body, before_eol = split_content_and_eol(before)
        after_body, after_eol = split_content_and_eol(after)
        if before_eol != after_eol:
            print(
                f"Satir sonu degisti: satir {index + 1}",
                file=sys.stderr,
            )
            return 1

    output = b"".join(output_lines)
    target = Path(args.output_path).resolve() if args.output_path else (repo_root / args.path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(output)

    print(f"Applied quest patches: {len(applied)}")
    print(f"Source bytes: {len(source)}")
    print(f"Output bytes: {len(output)}")
    print(f"Source SHA256: {sha256(source)}")
    print(f"Output SHA256: {sha256(output)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
