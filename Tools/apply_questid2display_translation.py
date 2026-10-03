#!/usr/bin/env python3
# Dosya Yolu: /ROenglishRE/Tools/apply_questid2display_translation.py
# Amac: questid2display.txt Turkce patchlerini legacy encoding byte'larini koruyarak uygular
# Modul: Tool - Python
# Version: 1.0.0
# Aciklama: Upstream dosyayi byte olarak okur; sadece hedef questlerin ASCII title/description/goal satirlarini degistirir
# Bagimli Oldugu Katman: Tool

from __future__ import annotations

import argparse
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


def ascii_field(value: str, quest_id: str, field: str) -> bytes:
    if "#" in value:
        raise ValueError(f"{quest_id}.{field}: '#' ayiraci kullanilamaz")
    try:
        return value.encode("ascii")
    except UnicodeEncodeError as exc:
        raise ValueError(
            f"{quest_id}.{field}: ASCII disi karakter var"
        ) from exc


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Apply byte-safe Turkish questid2display patches."
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
    repo_root = (
        Path(args.repo_root).resolve()
        if args.repo_root
        else script_path.parent.parent
    )

    patch_path = repo_root / args.patch
    config = json.loads(patch_path.read_text(encoding="utf-8"))
    patches = config["patches"]

    source = git_show(repo_root, args.source_ref, args.path)
    source_lines = source.split(b"\n")
    output_lines = list(source_lines)
    applied: set[str] = set()

    for index, line in enumerate(source_lines):
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
        description = ascii_field(
            patch.get("description", ""), quest_id, "description"
        )
        goal = ascii_field(patch.get("goal", ""), quest_id, "goal")

        output_lines[index] = (
            match.group(1)
            + b"#"
            + title
            + b"#"
            + match.group(3)
            + b"#"
            + match.group(4)
            + b"#"
        )
        output_lines[index + 1] = description + b"#"
        output_lines[index + 2] = goal + b"#"
        applied.add(quest_id)

    missing = sorted(set(patches) - applied, key=int)
    if missing:
        print(
            "Upstream dosyada bulunamayan patch quest ID'leri: "
            + ", ".join(missing),
            file=sys.stderr,
        )
        return 1

    output = b"\n".join(output_lines)

    # Byte safety: only explicitly patched 3-line quest records may differ.
    allowed_indexes: set[int] = set()
    for index, line in enumerate(source_lines):
        match = HEADER_RE.match(line)
        if match and match.group(1).decode("ascii") in patches:
            allowed_indexes.update({index, index + 1, index + 2})

    output_check = output.split(b"\n")
    if len(output_check) != len(source_lines):
        print("Satir sayisi degisti.", file=sys.stderr)
        return 1

    for index, (before, after) in enumerate(
        zip(source_lines, output_check)
    ):
        if index not in allowed_indexes and before != after:
            print(
                f"Patch disi byte degisikligi bulundu: satir {index + 1}",
                file=sys.stderr,
            )
            return 1

    target = repo_root / args.path
    target.write_bytes(output)

    print(f"Applied quest patches: {len(applied)}")
    print(f"Source bytes: {len(source)}")
    print(f"Output bytes: {len(output)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
