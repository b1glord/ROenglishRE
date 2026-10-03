#!/usr/bin/env python3
# 📄 Dosya Yolu: /ROenglishRE/Tools/export_ongoingquests_preview.py
# 📌 Amac: Legacy OngoingQuests.lub dosyasini degistirmeden UTF-8 inceleme raporuna donusturur
# 📌 Tool - Python
# Version: 1.1.0
# Aciklama: Her satiri UTF-8, CP949, EUC-KR ve Latin-1 fallback sirasi ile decode ederek karisik encoding icin guvenli onizleme uretir
# Bagimli Oldugu Katman: Tool

from __future__ import annotations

import argparse
import subprocess
import sys
from collections import Counter
from pathlib import Path

DEFAULT_SOURCE_PATH = "Translation/Renewal/SystemEN/OngoingQuests.lub"
DEFAULT_OUTPUT_PATH = "TurkuazTR/OngoingQuests.preview.txt"
DEFAULT_SOURCE_REF = "translation/tr"
DEFAULT_START_LINE = 1
DEFAULT_MAX_LINES = 1200
ENCODINGS = ("utf-8", "cp949", "euc-kr", "latin-1")


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


def decode_line(data: bytes) -> tuple[str, str]:
    for encoding in ENCODINGS:
        try:
            return data.decode(encoding), encoding
        except UnicodeDecodeError:
            continue
    raise AssertionError("latin-1 decode must always succeed")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Export a UTF-8 preview of mixed-encoding OngoingQuests.lub."
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
    raw_lines = raw.splitlines()
    decoded_lines: list[str] = []
    encoding_counts: Counter[str] = Counter()

    for raw_line in raw_lines:
        decoded, encoding = decode_line(raw_line)
        decoded_lines.append(decoded)
        encoding_counts[encoding] += 1

    start_index = max(args.start_line - 1, 0)
    end_index = min(start_index + max(args.max_lines, 0), len(decoded_lines))
    encoding_summary = ",".join(
        f"{name}:{encoding_counts.get(name, 0)}" for name in ENCODINGS
    )

    output_lines = [
        "# 📄 Dosya Yolu: /ROenglishRE/TurkuazTR/OngoingQuests.preview.txt",
        "# 📌 Amac: OngoingQuests.lub legacy kaynak dosyasinin UTF-8 inceleme raporu",
        "# 📌 Generated Report - TXT",
        "# Version: 1.1.0",
        "# Aciklama: Kaynak dosyaya dokunmadan karisik encoding destekli satir numarali onizleme saglar",
        "# Bagimli Oldugu Katman: Tool",
        "",
        f"source_path={args.path}",
        f"source_ref={args.source_ref}",
        f"encoding_summary={encoding_summary}",
        f"source_bytes={len(raw)}",
        f"source_lines={len(decoded_lines)}",
        f"preview_start_line={start_index + 1}",
        f"preview_end_line={end_index}",
        "",
    ]

    for index in range(start_index, end_index):
        output_lines.append(f"{index + 1:07d}: {decoded_lines[index]}")

    target = repo_root / args.output
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("\n".join(output_lines) + "\n", encoding="utf-8")

    print(f"Encoding summary: {encoding_summary}")
    print(f"Source bytes: {len(raw)}")
    print(f"Source lines: {len(decoded_lines)}")
    print(f"Preview lines: {end_index - start_index}")
    print(f"Output: {target.relative_to(repo_root)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
