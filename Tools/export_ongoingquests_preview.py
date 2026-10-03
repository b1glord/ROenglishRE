#!/usr/bin/env python3
# 📄 Dosya Yolu: /ROenglishRE/Tools/export_ongoingquests_preview.py
# 📌 Amac: Legacy OngoingQuests.lub dosyasini degistirmeden UTF-8 inceleme raporuna donusturur
# 📌 Tool - Python
# Version: 1.0.0
# Aciklama: Kaynak blobu byte olarak okur, CP949/EUC-KR fallback ile decode eder ve numarali satir onizlemesi uretir
# Bagimli Oldugu Katman: Tool

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

DEFAULT_SOURCE_PATH = "Translation/Renewal/SystemEN/OngoingQuests.lub"
DEFAULT_OUTPUT_PATH = "TurkuazTR/OngoingQuests.preview.txt"
DEFAULT_SOURCE_REF = "translation/tr"
DEFAULT_START_LINE = 1
DEFAULT_MAX_LINES = 1200
ENCODINGS = ("cp949", "euc-kr", "utf-8")


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


def decode_legacy(data: bytes) -> tuple[str, str]:
    for encoding in ENCODINGS:
        try:
            return data.decode(encoding), encoding
        except UnicodeDecodeError:
            continue
    return data.decode("latin-1"), "latin-1"


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Export a UTF-8 preview of legacy OngoingQuests.lub."
    )
    parser.add_argument("--repo-root", default=None)
    parser.add_argument("--path", default=DEFAULT_SOURCE_PATH)
    parser.add_argument("--source-ref", default=DEFAULT_SOURCE_REF)
    parser.add_argument("--output", default=DEFAULT_OUTPUT_PATH)
    parser.add_argument("--start-line", type=int, default=DEFAULT_START_LINE)
    parser.add_argument("--max-lines", type=int, default=DEFAULT_MAX_LINES)
    args = parser.parse_args()

    script_path = Path(__file__).resolve()
    repo_root = Path(args.repo_root).resolve() if args.repo_root else script_path.parent.parent

    raw = git_show(repo_root, args.source_ref, args.path)
    text, encoding = decode_legacy(raw)
    lines = text.splitlines()

    start_index = max(args.start_line - 1, 0)
    end_index = min(start_index + max(args.max_lines, 0), len(lines))

    output_lines = [
        "# 📄 Dosya Yolu: /ROenglishRE/TurkuazTR/OngoingQuests.preview.txt",
        "# 📌 Amac: OngoingQuests.lub legacy kaynak dosyasinin UTF-8 inceleme raporu",
        "# 📌 Generated Report - TXT",
        "# Version: 1.0.0",
        "# Aciklama: Kaynak dosyaya dokunmadan satir numarali onizleme saglar",
        "# Bagimli Oldugu Katman: Tool",
        "",
        f"source_path={args.path}",
        f"source_ref={args.source_ref}",
        f"detected_encoding={encoding}",
        f"source_bytes={len(raw)}",
        f"source_lines={len(lines)}",
        f"preview_start_line={start_index + 1}",
        f"preview_end_line={end_index}",
        "",
    ]

    for index in range(start_index, end_index):
        output_lines.append(f"{index + 1:07d}: {lines[index]}")

    target = repo_root / args.output
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("\n".join(output_lines) + "\n", encoding="utf-8")

    print(f"Detected encoding: {encoding}")
    print(f"Source bytes: {len(raw)}")
    print(f"Source lines: {len(lines)}")
    print(f"Preview lines: {end_index - start_index}")
    print(f"Output: {target.relative_to(repo_root)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
