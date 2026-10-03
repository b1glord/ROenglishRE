#!/usr/bin/env python3
# Dosya Yolu: /ROenglishRE/Tools/validate_questid2display_translation.py
# Amac: questid2display.txt cevirisinin byte ve kayit yapisini dogrular
# Modul: Tool - Python
# Version: 1.2.0
# Aciklama: Legacy encoding'i decode etmeden ID/header/# yapisini ve degisen satirlarin ASCII olmasini kontrol eder
# Bagimli Oldugu Katman: Tool

from __future__ import annotations

import argparse
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


def structural_line(line: bytes) -> bytes:
    match = HEADER_RE.match(line)
    if match:
        quest_id, _title, icon, image = match.groups()
        return quest_id + b"##" + icon + b"#" + image + b"#"

    if line == b"":
        return b""

    if line.endswith(b"#"):
        return b"#"

    return line


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate questid2display localization structure."
    )
    parser.add_argument("--repo-root", default=None)
    parser.add_argument(
        "--path",
        default="Translation/Renewal/data/questid2display.txt",
    )
    parser.add_argument(
        "--upstream-ref",
        default="refs/remotes/origin/upstream/latest",
    )
    parser.add_argument("--translation-ref", default="HEAD")
    parser.add_argument(
        "--working-tree",
        action="store_true",
        help="Validate the current working-tree file instead of git show translation-ref.",
    )
    args = parser.parse_args()

    script_path = Path(__file__).resolve()
    repo_root = (
        Path(args.repo_root).resolve()
        if args.repo_root
        else script_path.parent.parent
    )

    upstream = git_show(repo_root, args.upstream_ref, args.path).split(b"\n")
    if args.working_tree:
        translated_raw = (repo_root / args.path).read_bytes()
    else:
        translated_raw = git_show(repo_root, args.translation_ref, args.path)
    translated = translated_raw.split(b"\n")

    if len(upstream) != len(translated):
        print(
            f"Satir sayisi farkli: upstream={len(upstream)}, "
            f"translation={len(translated)}",
            file=sys.stderr,
        )
        return 1

    changed_lines = 0
    changed_non_ascii: list[tuple[int, bytes]] = []

    for index, (source, target) in enumerate(
        zip(upstream, translated), start=1
    ):
        if structural_line(source) != structural_line(target):
            print(
                f"Quest yapisi degisti, satir {index}:\n"
                f"  upstream: {source!r}\n"
                f"  turkce:   {target!r}",
                file=sys.stderr,
            )
            return 1

        if source != target:
            changed_lines += 1
            if any(byte >= 0x80 for byte in target):
                changed_non_ascii.append((index, target))

    if changed_non_ascii:
        print(
            "Degistirilen quest satirlarinda ASCII disi byte bulundu:",
            file=sys.stderr,
        )
        for index, line in changed_non_ascii[:20]:
            print(f"  {index}: {line!r}", file=sys.stderr)
        return 1

    upstream_headers = sum(
        1 for line in upstream if HEADER_RE.match(line)
    )
    translated_headers = sum(
        1 for line in translated if HEADER_RE.match(line)
    )
    if upstream_headers != translated_headers:
        print(
            f"Quest header sayisi farkli: upstream={upstream_headers}, "
            f"translation={translated_headers}",
            file=sys.stderr,
        )
        return 1

    print("questid2display byte structure: OK")
    print(f"Quest record count: {translated_headers}")
    print(f"Changed lines: {changed_lines}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
