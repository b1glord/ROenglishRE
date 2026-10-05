#!/usr/bin/env python3
# PATH: /ROenglishRE/TurkuazTR/tools/build-quest-profile.py
# PURPOSE: Quest display ve OngoingQuests ciktilarini ortak localization profiline gore uretir.
# MODULE-FILETYPE: Tool - Python
# VERSION: 1.0.0
# DESCRIPTION: English profilde upstream byte kaynagini korur; diger profillerde mevcut byte-safe quest patch araclarini generated cikisa uygular.
# DEPENDENCY-LAYER: Tool

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
PROFILE_FILE = REPO_ROOT / "TurkuazTR/localization-profiles.json"
QUEST_PATH = "Translation/Renewal/data/questid2display.txt"
ONGOING_PATH = "Translation/Renewal/SystemEN/OngoingQuests.lub"
DEFAULT_SOURCE_REF = "refs/remotes/origin/upstream/latest"


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def git_show(ref_name: str, path: str) -> bytes:
    result = subprocess.run(
        ["git", "-C", str(REPO_ROOT), "show", f"{ref_name}:{path}"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if result.returncode != 0:
        sys.stderr.buffer.write(result.stderr)
        raise SystemExit(2)
    return result.stdout


def run_tool(script: str, source_ref: str, output_path: Path) -> None:
    result = subprocess.run(
        [
            sys.executable,
            str(REPO_ROOT / script),
            "--repo-root",
            str(REPO_ROOT),
            "--source-ref",
            source_ref,
            "--output-path",
            str(output_path),
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
        text=True,
    )
    if result.stdout:
        sys.stdout.write(result.stdout)
    if result.returncode != 0:
        if result.stderr:
            sys.stderr.write(result.stderr)
        raise SystemExit(result.returncode)


def main() -> int:
    profiles = load_json(PROFILE_FILE)
    profile_rows = profiles.get("profiles", {})

    parser = argparse.ArgumentParser()
    parser.add_argument("--profile", choices=tuple(profile_rows), required=True)
    parser.add_argument("--source-ref", default=DEFAULT_SOURCE_REF)
    parser.add_argument("--output-root", type=Path)
    args = parser.parse_args()

    profile = profile_rows[args.profile]
    quest_mode = profile.get("quest_display", "original")
    ongoing_mode = profile.get("ongoing_quests", "original")
    if quest_mode not in {"original", "tr"}:
        raise SystemExit(f"Bilinmeyen quest_display modu: {quest_mode}")
    if ongoing_mode not in {"original", "tr"}:
        raise SystemExit(f"Bilinmeyen ongoing_quests modu: {ongoing_mode}")

    output_root = args.output_root or (REPO_ROOT / "TurkuazTR/generated" / args.profile)
    quest_output = output_root / "data/questid2display.txt"
    ongoing_output = output_root / "SystemEN/OngoingQuests.lub"
    quest_output.parent.mkdir(parents=True, exist_ok=True)
    ongoing_output.parent.mkdir(parents=True, exist_ok=True)

    if quest_mode == "original":
        quest_output.write_bytes(git_show(args.source_ref, QUEST_PATH))
    else:
        run_tool(
            "Tools/apply_questid2display_translation.py",
            args.source_ref,
            quest_output,
        )

    if ongoing_mode == "original":
        ongoing_output.write_bytes(git_show(args.source_ref, ONGOING_PATH))
    else:
        run_tool(
            "Tools/apply_ongoingquests_translation.py",
            args.source_ref,
            ongoing_output,
        )

    report = {
        "profile": args.profile,
        "quest_display_mode": quest_mode,
        "ongoing_quests_mode": ongoing_mode,
        "source_ref": args.source_ref,
        "quest_output_path": "data/questid2display.txt",
        "ongoing_output_path": "SystemEN/OngoingQuests.lub",
        "quest_output_size": quest_output.stat().st_size,
        "ongoing_output_size": ongoing_output.stat().st_size,
    }
    (output_root / "quest-build-report.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=True) + "\n",
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
