#!/usr/bin/env python3
# 📄 Dosya Yolu: /ROenglishRE/TurkuazTR/tools/build-test-package.py
# 📌 Amac: Generated localization profilini client klasorune acilabilir test ZIP paketine donusturur ve checksum/rapor uretir
# 📌 Tool - Python
# Version: 1.0.1
# Aciklama: English profilinde canonical upstream itemInfo fallback'i kullanir; tum profilleri smoke-test kontrollu test paketleri olarak paketler
# Bagimli Oldugu Katman: Tool

from __future__ import annotations

import argparse
import hashlib
import json
import zipfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
GENERATED_ROOT = REPO_ROOT / "TurkuazTR/generated"
ENGLISH_ITEMINFO_SOURCE = (
    REPO_ROOT / "Translation/Renewal/SystemEN/LuaFiles514/itemInfo.lua"
)
SUPPORTED_PROFILES = ("english", "hybrid", "full_tr", "bilingual")
REQUIRED_FILES = (
    "SystemEN/LuaFiles514/itemInfo.lua",
    "SystemEN/Navi_Data.lub",
    "SystemEN/OngoingQuests.lub",
    "data/msgstringtable.txt",
    "data/luafiles514/lua files/skillinfoz/skillinfolist.lub",
    "data/luafiles514/lua files/skillinfoz/skilldescript.lub",
)
PAYLOAD_ROOTS = ("SystemEN", "data")
OPTIONAL_ROOT_FILES = ("tipoftheday.txt",)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def collect_payload_files(profile_root: Path) -> list[tuple[Path, str]]:
    files: list[tuple[Path, str]] = []
    for root_name in PAYLOAD_ROOTS:
        root = profile_root / root_name
        if not root.is_dir():
            raise FileNotFoundError(f"Missing generated directory: {root}")
        for path in sorted(root.rglob("*")):
            if path.is_file():
                files.append((path, path.relative_to(profile_root).as_posix()))

    for file_name in OPTIONAL_ROOT_FILES:
        path = profile_root / file_name
        if path.is_file():
            files.append((path, file_name))

    item_info_target = "SystemEN/LuaFiles514/itemInfo.lua"
    if (
        profile_root.name == "english"
        and not (profile_root / item_info_target).is_file()
    ):
        if not ENGLISH_ITEMINFO_SOURCE.is_file():
            raise FileNotFoundError(
                f"Missing canonical English itemInfo: {ENGLISH_ITEMINFO_SOURCE}"
            )
        files.append((ENGLISH_ITEMINFO_SOURCE, item_info_target))

    return files


def validate_required_files(profile_root: Path) -> None:
    missing: list[str] = []
    for relative in REQUIRED_FILES:
        if (profile_root / relative).is_file():
            continue
        if (
            profile_root.name == "english"
            and relative == "SystemEN/LuaFiles514/itemInfo.lua"
            and ENGLISH_ITEMINFO_SOURCE.is_file()
        ):
            continue
        missing.append(relative)
    if missing:
        raise FileNotFoundError(
            "Missing required generated files: " + ", ".join(missing)
        )


def package_profile(
    profile: str,
    version: str,
    commit: str,
    output_dir: Path,
) -> dict[str, object]:
    if profile not in SUPPORTED_PROFILES:
        raise ValueError(f"Unsupported profile: {profile}")

    profile_root = GENERATED_ROOT / profile
    validate_required_files(profile_root)
    payload_files = collect_payload_files(profile_root)
    if not payload_files:
        raise RuntimeError(f"No payload files found for profile: {profile}")

    output_dir.mkdir(parents=True, exist_ok=True)
    base_name = f"TurkuazTR-{profile}-{version}"
    zip_path = output_dir / f"{base_name}.zip"

    readme = (
        "TurkuazTR TEST SURUMU\n"
        f"Profil: {profile}\n"
        f"Surum: {version}\n"
        f"Commit: {commit}\n"
        "\n"
        "Kurulum:\n"
        "1. Mevcut client dosyalarinizi yedekleyin.\n"
        "2. Bu ZIP icindeki SystemEN ve data klasorlerini client localization kokune kopyalayin.\n"
        "3. Varsa tipoftheday.txt dosyasini ayni localization kokune kopyalayin.\n"
        "4. Test bittikten sonra yedekten geri donun veya farkli profil paketini uygulayin.\n"
        "\n"
        "Not: itemInfo serbest lore migration'i test surumunde tamamlanmis sayilmaz.\n"
        "Eslesmeyen guvenli olmayan metinler Ingilizce fallback olarak korunur.\n"
    )

    with zipfile.ZipFile(
        zip_path,
        "w",
        compression=zipfile.ZIP_DEFLATED,
        compresslevel=9,
    ) as archive:
        for source, archive_name in payload_files:
            archive.write(source, archive_name)
        archive.writestr("TEST-README.txt", readme)

    with zipfile.ZipFile(zip_path, "r") as archive:
        bad_member = archive.testzip()
        if bad_member is not None:
            raise RuntimeError(f"Corrupt ZIP member: {bad_member}")
        names = set(archive.namelist())
        for required in REQUIRED_FILES:
            if required not in names:
                raise RuntimeError(
                    f"Required file missing from ZIP: {required}"
                )
        if any(name.endswith("-build-report.json") for name in names):
            raise RuntimeError("Build report leaked into client payload")

    checksum = sha256_file(zip_path)
    checksum_path = output_dir / f"{base_name}.sha256"
    checksum_path.write_text(
        f"{checksum}  {zip_path.name}\n",
        encoding="ascii",
    )

    report = {
        "_file_header": {
            "path": f"dist/{base_name}.json",
            "purpose": "TurkuazTR test paketinin build ve smoke-test sonucunu raporlar",
            "module": "Generated Report - JSON",
            "version": "1.0.0",
            "description": "Paket profili, kaynak commit, dosya sayisi, boyut ve SHA-256 degerini kaydeder",
            "dependency_layer": "Tool",
        },
        "profile": profile,
        "release_version": version,
        "source_commit": commit,
        "payload_file_count": len(payload_files),
        "zip_bytes": zip_path.stat().st_size,
        "sha256": checksum,
        "required_files": list(REQUIRED_FILES),
        "smoke_test": "pass",
    }
    report_path = output_dir / f"{base_name}.json"
    report_path.write_text(
        json.dumps(report, ensure_ascii=True, indent=2) + "\n",
        encoding="ascii",
    )
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--profile", required=True, choices=SUPPORTED_PROFILES)
    parser.add_argument("--version", required=True)
    parser.add_argument("--commit", required=True)
    parser.add_argument("--output-dir", default="dist")
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    if not output_dir.is_absolute():
        output_dir = REPO_ROOT / output_dir

    report = package_profile(
        profile=args.profile,
        version=args.version,
        commit=args.commit,
        output_dir=output_dir,
    )
    print(json.dumps(report, ensure_ascii=True, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
