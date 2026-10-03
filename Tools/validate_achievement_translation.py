#!/usr/bin/env python3
# Dosya Yolu: /ROenglishRE/Tools/validate_achievement_translation.py
# Amac: achievements.lub cevirisinin Lua yapisini degistirmedigini dogrular
# Modul: Tool - Python
# Version: 1.0.1
# Aciklama: Upstream ve Turkce dosyada quoted string iceriklerini maskeleyip kalan yapinin birebir ayni oldugunu kontrol eder
# Bagimli Oldugu Katman: Tool

from __future__ import annotations

import argparse
import difflib
import re
import subprocess
import sys
from pathlib import Path

STRING_RE = re.compile(rb'"(?:\\.|[^"\\])*"')


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
    return result.stdout.replace(b"\r\n", b"\n")


def mask_strings(content: bytes) -> bytes:
    masked = STRING_RE.sub(b'""', content)
    return b"\n".join(line.rstrip() for line in masked.split(b"\n"))


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate that achievement localization changes string contents only."
    )
    parser.add_argument("--repo-root", default=None)
    parser.add_argument(
        "--path",
        default="Translation/Renewal/SystemEN/achievements.lub",
    )
    parser.add_argument(
        "--upstream-ref",
        default="refs/remotes/origin/upstream/latest",
    )
    parser.add_argument("--translation-ref", default="HEAD")
    args = parser.parse_args()

    script_path = Path(__file__).resolve()
    repo_root = (
        Path(args.repo_root).resolve()
        if args.repo_root
        else script_path.parent.parent
    )

    upstream = git_show(repo_root, args.upstream_ref, args.path)
    translated = git_show(repo_root, args.translation_ref, args.path)

    try:
        translated.decode("ascii")
    except UnicodeDecodeError as exc:
        print(
            f"Achievement cevirisinde ASCII disi byte bulundu: offset={exc.start}",
            file=sys.stderr,
        )
        return 1

    upstream_structure = mask_strings(upstream)
    translated_structure = mask_strings(translated)

    if upstream_structure != translated_structure:
        upstream_lines = upstream_structure.decode("latin-1").splitlines()
        translated_lines = translated_structure.decode("latin-1").splitlines()
        diff = difflib.unified_diff(
            upstream_lines,
            translated_lines,
            fromfile="upstream-structure",
            tofile="translation-structure",
            lineterm="",
            n=2,
        )
        print(
            "Achievement Lua yapisi upstream ile ayni degil. "
            "Ceviri yalnizca quoted string icerigini degistirebilir.",
            file=sys.stderr,
        )
        for index, line in enumerate(diff):
            if index >= 80:
                print("... diff kisaltildi ...", file=sys.stderr)
                break
            print(line, file=sys.stderr)
        return 1

    upstream_strings = len(STRING_RE.findall(upstream))
    translated_strings = len(STRING_RE.findall(translated))
    if upstream_strings != translated_strings:
        print(
            f"Quoted string sayisi farkli: upstream={upstream_strings}, "
            f"translation={translated_strings}",
            file=sys.stderr,
        )
        return 1

    print("Achievement localization structure: OK")
    print(f"Quoted string count: {translated_strings}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
