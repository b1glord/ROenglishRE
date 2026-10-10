#!/usr/bin/env python3
# 📄 Dosya Yolu: /ROenglishRE/TurkuazTR/tools/validate-iteminfo-exact-strings.py
# 📌 Amac: itemInfo exact cevirilerinde Lua string kacisini ve shard guvenligini dogrular
# 📌 Modul - Tool Python
# Version: 1.14.0
# Aciklama: v1.162 Harici kanitli eksik yuzde onarimi ve regresyon testleri
# Bagimli Oldugu Katman: Tool

from __future__ import annotations

import importlib.util
import json
import re
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
BUILDER_PATH = REPO_ROOT / "TurkuazTR/tools/build-iteminfo-profile.py"
spec = importlib.util.spec_from_file_location("iteminfo_builder", BUILDER_PATH)
if spec is None or spec.loader is None:
    raise RuntimeError("itemInfo builder yuklenemedi")
builder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(builder)


class ExactLuaStringTests(unittest.TestCase):
    def test_v1154_triage_is_complete_and_source_safe(self) -> None:
        import importlib.util

        audit_path = REPO_ROOT / "TurkuazTR/tools/audit-iteminfo-visible.py"
        audit_spec = importlib.util.spec_from_file_location("iteminfo_audit_triage", audit_path)
        self.assertIsNotNone(audit_spec)
        self.assertIsNotNone(audit_spec.loader)
        audit = importlib.util.module_from_spec(audit_spec)
        audit_spec.loader.exec_module(audit)

        ledger = json.loads(
            (REPO_ROOT / "TurkuazTR/config/iteminfo-v1154-triage.json").read_text(
                encoding="utf-8"
            )
        )
        shard = json.loads(
            (REPO_ROOT / "TurkuazTR/config/iteminfo-exact-v1154.tr.json").read_text(
                encoding="utf-8"
            )
        )["translations"]
        recovery = json.loads(
            (REPO_ROOT / "TurkuazTR/iteminfo-lore.source-recovery.json").read_text(
                encoding="utf-8"
            )
        )["candidates"]
        # Historical v1.154 triage remains immutable: later evidence-backed
        # recoveries can graduate from the quarantine into newer exact shards.
        v1155 = json.loads(
            (REPO_ROOT / "TurkuazTR/config/iteminfo-recovery-evidence-v1155.json").read_text(
                encoding="utf-8"
            )
        )["entries"]
        v1157 = json.loads(
            (REPO_ROOT / "TurkuazTR/config/iteminfo-recovery-evidence-v1157.json").read_text(
                encoding="utf-8"
            )
        )["entries"]
        v1158 = json.loads(
            (REPO_ROOT / "TurkuazTR/config/iteminfo-recovery-evidence-v1158.json").read_text(
                encoding="utf-8"
            )
        )["entries"]
        v1160 = json.loads(
            (REPO_ROOT / "TurkuazTR/config/iteminfo-recovery-evidence-v1160.json").read_text(
                encoding="utf-8"
            )
        )["entries"]
        v1161 = json.loads(
            (REPO_ROOT / "TurkuazTR/config/iteminfo-recovery-evidence-v1161.json").read_text(
                encoding="utf-8"
            )
        )["entries"]
        v1162 = json.loads(
            (REPO_ROOT / "TurkuazTR/config/iteminfo-recovery-evidence-v1162.json").read_text(
                encoding="utf-8"
            )
        )["entries"]
        resolved_later = {entry["source"] for entry in [*v1155, *v1157, *v1158, *v1160, *v1161, *v1162]}
        statuses = {
            "translated": 0,
            "canonical_proper_name": 0,
            "upstream_source_recovery": 0,
        }
        unique_sources = set()
        for entry in ledger["entries"]:
            source, decision = entry["source"], entry["decision"]
            self.assertNotIn(source, unique_sources)
            unique_sources.add(source)
            self.assertIn(decision, statuses)
            statuses[decision] += 1
            if decision == "translated":
                target = shard[source]
                target.encode("ascii")
                self.assertNotEqual(source, target)
                self.assertEqual(
                    sorted(re.findall(r"\d+(?:\.\d+)?", source)),
                    sorted(re.findall(r"\d+(?:\.\d+)?", target)),
                )
                self.assertEqual(
                    re.findall(r"\^[0-9a-fA-F]{6}", source),
                    re.findall(r"\^[0-9a-fA-F]{6}", target),
                )
                safe = builder.escape_lua_quoted_content(target.encode("ascii"))
                self.assertIsNotNone(builder.STRING_RE.fullmatch(b'"' + safe + b'"'))
            elif decision == "canonical_proper_name":
                self.assertTrue(audit.canonical_name_list(audit.COLOR_RE.sub("", source).strip()))
                self.assertFalse(audit.lore_candidate(source))
                self.assertNotIn(source, recovery)
            else:
                self.assertTrue(
                    source in recovery or source in resolved_later,
                    "Deferred source must remain quarantined or have newer provenance",
                )
                self.assertTrue(entry.get("reason"))
        self.assertEqual(len(unique_sources), 32)
        self.assertEqual(
            statuses,
            {"translated": 2, "canonical_proper_name": 16, "upstream_source_recovery": 14},
        )
        self.assertEqual(set(shard), {
            e["source"] for e in ledger["entries"] if e["decision"] == "translated"
        })
        self.assertEqual(len(recovery), len(set(recovery)))

    def test_v1154_does_not_hide_meaningful_item_lore(self) -> None:
        import importlib.util
        audit_path = REPO_ROOT / "TurkuazTR/tools/audit-iteminfo-visible.py"
        spec = importlib.util.spec_from_file_location("iteminfo_audit_v1154", audit_path)
        audit = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(audit)
        self.assertFalse(audit.canonical_name_list(
            "Increases damage inflicted and Decreases damage taken by 5%."
        ))
        self.assertFalse(audit.canonical_name_list(
            "A Mystery Box, which increases Attack Speed, has been added."
        ))
        self.assertFalse(audit.canonical_name_list(
            "Safe to 9 Weapon Certificate, Safe to 9 Armor Certificate and other items can be found."
        ))
        self.assertFalse(audit.canonical_name_list(
            "Powerful ATK, increases MaxHP and MATK."
        ))

    def test_v1155_source_context_provenance(self) -> None:
        from collections import Counter

        provenance = json.loads(
            (REPO_ROOT / "TurkuazTR/config/iteminfo-recovery-evidence-v1155.json").read_text(
                encoding="utf-8"
            )
        )
        records = provenance["entries"]
        mapping = json.loads(
            (REPO_ROOT / "TurkuazTR/config/iteminfo-exact-v1155.tr.json").read_text(
                encoding="utf-8"
            )
        )["translations"]
        source = (REPO_ROOT / provenance["source_path"]).read_text(
            encoding="utf-8", errors="surrogateescape"
        )
        recovery = json.loads(
            (REPO_ROOT / "TurkuazTR/iteminfo-lore.source-recovery.json").read_text(
                encoding="utf-8"
            )
        )["candidates"]
        self.assertEqual(provenance["resolved_count"], len(records))
        self.assertEqual(set(mapping), {e["source"] for e in records})
        self.assertEqual(len(recovery), len(set(recovery)))
        entries = re.split(r"(?m)^\s*\[(\d+)\]\s*=\s*\{", source)
        item_blocks = dict(zip(entries[1::2], entries[2::2]))
        for e in records:
            with self.subTest(item=e["item_id"], source=e["source"][:70]):
                self.assertNotIn(e["source"], recovery)
                item_block = item_blocks[str(e["item_id"])]
                self.assertIn(e["source"], item_block)
                self.assertIn('identifiedDisplayName = "' + e["item_name"] + '"', item_block)
                lines = item_block.splitlines()
                self.assertTrue(any(
                    i > 0 and i + 1 < len(lines)
                    and lines[i - 1] == e["previous_source_line"]
                    and lines[i] == e["exact_source_line"]
                    and lines[i + 1] == e["next_source_line"]
                    for i in range(len(lines))
                ), "source line and adjacent lines must be from the same item")
                self.assertEqual(mapping[e["source"]], e["translation"])
                self.assertEqual(
                    Counter(re.findall(r"\d+(?:\.\d+)?", e["source"])),
                    Counter(re.findall(r"\d+(?:\.\d+)?", e["translation"])),
                )
                self.assertEqual(
                    re.findall(r"\^[0-9A-Fa-f]{6}", e["source"]),
                    re.findall(r"\^[0-9A-Fa-f]{6}", e["translation"]),
                )
                e["translation"].encode("ascii")
                escaped = builder.escape_lua_quoted_content(e["translation"].encode("ascii"))
                self.assertIsNotNone(builder.STRING_RE.fullmatch(b'"' + escaped + b'"'))
                self.assertEqual(e["upstream_source_blob_sha"], provenance["upstream_source_blob_sha"])

    def test_v1157_source_context_provenance(self) -> None:
        from collections import Counter

        provenance = json.loads(
            (REPO_ROOT / "TurkuazTR/config/iteminfo-recovery-evidence-v1157.json").read_text(
                encoding="utf-8"
            )
        )
        records = provenance["entries"]
        mapping = json.loads(
            (REPO_ROOT / "TurkuazTR/config/iteminfo-exact-v1157.tr.json").read_text(
                encoding="utf-8"
            )
        )["translations"]
        source = (REPO_ROOT / provenance["source_path"]).read_text(
            encoding="utf-8", errors="surrogateescape"
        )
        quarantine = json.loads(
            (REPO_ROOT / "TurkuazTR/iteminfo-lore.source-recovery.json").read_text(
                encoding="utf-8"
            )
        )["candidates"]
        self.assertEqual(len(records), provenance["resolved_count"])
        self.assertEqual(set(mapping), {entry["source"] for entry in records})
        blocks = re.split(r"(?m)^\s*\[(\d+)\]\s*=\s*\{", source)
        by_id = dict(zip(blocks[1::2], blocks[2::2]))
        for entry in records:
            with self.subTest(item=entry["item_id"], source=entry["source"][:80]):
                self.assertNotIn(entry["source"], quarantine)
                self.assertIn(entry["source"], by_id[str(entry["item_id"])])
                self.assertEqual(mapping[entry["source"]], entry["translation"])
                self.assertEqual(
                    Counter(re.findall(r"\d+(?:\.\d+)?", entry["source"])),
                    Counter(re.findall(r"\d+(?:\.\d+)?", entry["translation"])),
                )
                self.assertEqual(
                    re.findall(r"\^[0-9A-Fa-f]{6}", entry["source"]),
                    re.findall(r"\^[0-9A-Fa-f]{6}", entry["translation"]),
                )
                entry["translation"].encode("ascii")
                result = builder.escape_lua_quoted_content(entry["translation"].encode("ascii"))
                self.assertIsNotNone(builder.STRING_RE.fullmatch(bytes([34]) + result + bytes([34])))
                self.assertEqual(entry["upstream_source_blob_sha"], provenance["upstream_source_blob_sha"])

    def test_v1158_source_context_provenance(self) -> None:
        from collections import Counter

        evidence = json.loads(
            (REPO_ROOT / "TurkuazTR/config/iteminfo-recovery-evidence-v1158.json").read_text(
                encoding="utf-8"
            )
        )
        shard = json.loads(
            (REPO_ROOT / "TurkuazTR/config/iteminfo-exact-v1158.tr.json").read_text(
                encoding="utf-8"
            )
        )["translations"]
        recovery = json.loads(
            (REPO_ROOT / "TurkuazTR/iteminfo-lore.source-recovery.json").read_text(
                encoding="utf-8"
            )
        )["candidates"]
        source = (REPO_ROOT / evidence["source_path"]).read_text(
            encoding="utf-8", errors="surrogateescape"
        )
        chunks = re.split(r"(?m)^\s*\[(\d+)\]\s*=\s*\{", source)
        by_id = dict(zip(chunks[1::2], chunks[2::2]))
        entries = evidence["entries"]
        self.assertEqual(len(entries), evidence["resolved_count"])
        self.assertEqual(len(entries), 23)
        self.assertEqual(set(shard), {e["source"] for e in entries})
        for entry in entries:
            with self.subTest(item=entry["item_id"], source=entry["source"][:80]):
                self.assertNotIn(entry["source"], recovery)
                self.assertIn(entry["source"], by_id[str(entry["item_id"])])
                self.assertEqual(shard[entry["source"]], entry["translation"])
                self.assertEqual(
                    Counter(re.findall(r"\d+(?:\.\d+)?", entry["source"])),
                    Counter(re.findall(r"\d+(?:\.\d+)?", entry["translation"])),
                )
                self.assertEqual(
                    re.findall(r"\^[0-9A-Fa-f]{6}", entry["source"]),
                    re.findall(r"\^[0-9A-Fa-f]{6}", entry["translation"]),
                )
                entry["translation"].encode("ascii")
                escaped = builder.escape_lua_quoted_content(entry["translation"].encode("ascii"))
                self.assertIsNotNone(builder.STRING_RE.fullmatch(bytes([34]) + escaped + bytes([34])))
                self.assertEqual(entry["upstream_source_blob_sha"], evidence["upstream_source_blob_sha"])

    def test_v1160_paired_lore_source_provenance(self) -> None:
        from collections import Counter

        evidence = json.loads(
            (REPO_ROOT / "TurkuazTR/config/iteminfo-recovery-evidence-v1160.json").read_text(
                encoding="utf-8"
            )
        )
        shard = json.loads(
            (REPO_ROOT / "TurkuazTR/config/iteminfo-exact-v1160.tr.json").read_text(
                encoding="utf-8"
            )
        )["translations"]
        recovery = set(json.loads(
            (REPO_ROOT / "TurkuazTR/iteminfo-lore.source-recovery.json").read_text(
                encoding="utf-8"
            )
        )["candidates"])
        raw = (REPO_ROOT / evidence["source_path"]).read_text(
            encoding="utf-8", errors="surrogateescape"
        )
        parts = re.split(r"(?m)^\s*\[(\d+)\]\s*=\s*\{", raw)
        by_id = dict(zip(parts[1::2], parts[2::2]))
        self.assertEqual(evidence["resolved_count"], 3)
        self.assertEqual(evidence["adjacent_translation_count"], 0)
        self.assertEqual(evidence["reused_existing_adjacent_count"], 2)
        self.assertEqual(evidence["total_translations"], 3)
        self.assertEqual(len(shard), 3)
        keys = set()
        for entry in evidence["entries"]:
            with self.subTest(item_id=entry["item_id"]):
                self.assertIn(str(entry["item_id"]), by_id)
                self.assertIn(entry["source"], by_id[str(entry["item_id"])])
                self.assertNotIn(entry["source"], recovery)
                self.assertEqual(shard[entry["source"]], entry["translation"])
                keys.add(entry["source"])
                if "adjacent_source" in entry:
                    neighbor = entry["adjacent_source"]
                    self.assertNotIn(neighbor, shard)
                    prior_path = REPO_ROOT / entry["adjacent_translation_path"]
                    prior_mapping = json.loads(prior_path.read_text(encoding="utf-8"))["translations"]
                    self.assertEqual(prior_mapping[neighbor], entry["adjacent_translation"])
                    # Every use of the opening fragment must be followed by
                    # its proven continuation in the SAME item, not another item.
                    pair_count = 0
                    for block in by_id.values():
                        lines = [line.strip() for line in block.splitlines()]
                        first = '"' + entry["source"] + '",'
                        second = '"' + neighbor + '",'
                        for index in range(len(lines) - 1):
                            if lines[index] == first:
                                self.assertEqual(lines[index + 1], second)
                                pair_count += 1
                    self.assertGreaterEqual(pair_count, entry["expected_contexts"])
                for key in (entry["source"], entry.get("adjacent_source")):
                    if key is None:
                        continue
                    target = shard[key] if key in shard else entry["adjacent_translation"]
                    self.assertEqual(
                        Counter(re.findall(r"\d+(?:\.\d+)?", key)),
                        Counter(re.findall(r"\d+(?:\.\d+)?", target)),
                    )
                    self.assertEqual(
                        re.findall(r"\^[0-9A-Fa-f]{6}", key),
                        re.findall(r"\^[0-9A-Fa-f]{6}", target),
                    )
                    target.encode("ascii")
                    escaped = builder.escape_lua_quoted_content(target.encode("ascii"))
                    self.assertIsNotNone(
                        builder.STRING_RE.fullmatch(bytes([34]) + escaped + bytes([34]))
                    )
        self.assertEqual(keys, set(shard))

    def test_v1161_integrity_triage_and_safe_box_list(self) -> None:
        from collections import Counter

        path = REPO_ROOT / "TurkuazTR/tools/audit-iteminfo-recovery-context.py"
        triage_spec = importlib.util.spec_from_file_location("iteminfo_source_integrity", path)
        self.assertIsNotNone(triage_spec)
        self.assertIsNotNone(triage_spec.loader)
        triage = importlib.util.module_from_spec(triage_spec)
        triage_spec.loader.exec_module(triage)

        fixtures = {
            "bad" + chr(0xdc81) + " byte": "invalid_source_bytes",
            "Decreases by ^009900^000000 0.5 seconds": "empty_color_span",
            "Increases Damage taken by%.": "missing_percent_value",
            "Level 1 ^00990Decrease AGI^000000": "suspected_color_marker_text_overlap",
            "^0000FF+ or higher^000000": "missing_refine_threshold",
        }
        for raw, expected in fixtures.items():
            with self.subTest(flag=expected):
                self.assertIn(expected, triage.source_integrity_flags(raw))
        evidence = json.loads(
            (REPO_ROOT / "TurkuazTR/config/iteminfo-recovery-evidence-v1161.json").read_text(
                encoding="utf-8"
            )
        )
        shard = json.loads(
            (REPO_ROOT / "TurkuazTR/config/iteminfo-exact-v1161.tr.json").read_text(
                encoding="utf-8"
            )
        )["translations"]
        recovery = json.loads(
            (REPO_ROOT / "TurkuazTR/iteminfo-lore.source-recovery.json").read_text(
                encoding="utf-8"
            )
        )["candidates"]
        self.assertEqual(evidence["resolved_count"], 1)
        self.assertEqual(evidence["expected_source_occurrences"], 2)
        self.assertEqual(len(shard), 1)
        entry = evidence["entries"][0]
        self.assertEqual(set(shard), {entry["source"]})
        self.assertEqual(shard[entry["source"]], entry["translation"])
        self.assertNotIn(entry["source"], recovery)
        self.assertEqual(triage.source_integrity_flags(entry["source"]), [])
        entry["translation"].encode("ascii")
        self.assertEqual(
            Counter(re.findall(r"\d+(?:\.\d+)?", entry["source"])),
            Counter(re.findall(r"\d+(?:\.\d+)?", entry["translation"])),
        )
        self.assertEqual(
            re.findall(r"\^[0-9a-fA-F]{6}", entry["source"]),
            re.findall(r"\^[0-9a-fA-F]{6}", entry["translation"]),
        )
        source_text = (REPO_ROOT / evidence["source_path"]).read_text(
            encoding="utf-8", errors="surrogateescape"
        )
        sections = re.split(r"(?m)^\s*\[(\d+)\]\s*=\s*\{", source_text)
        by_id = dict(zip(sections[1::2], sections[2::2]))
        self.assertEqual(len(entry["matching_item_ids"]), 2)
        for item_id in entry["matching_item_ids"]:
            with self.subTest(item_id=item_id):
                self.assertIn(entry["source"], by_id[str(item_id)])
        self.assertEqual(
            source_text.count('"' + entry["source"] + '",'),
            evidence["expected_source_occurrences"],
        )
        escaped = builder.escape_lua_quoted_content(entry["translation"].encode("ascii"))
        self.assertIsNotNone(
            builder.STRING_RE.fullmatch(bytes([34]) + escaped + bytes([34]))
        )

    def test_v1162_herosria_verified_missing_percent(self) -> None:
        """Only the independently evidenced percent may bridge broken source numbers."""
        evidence = json.loads(
            (REPO_ROOT / "TurkuazTR/config/iteminfo-recovery-evidence-v1162.json").read_text(
                encoding="utf-8"
            )
        )
        shard = json.loads(
            (REPO_ROOT / "TurkuazTR/config/iteminfo-exact-v1162.tr.json").read_text(
                encoding="utf-8"
            )
        )["translations"]
        quarantine = json.loads(
            (REPO_ROOT / "TurkuazTR/iteminfo-lore.source-recovery.json").read_text(
                encoding="utf-8"
            )
        )["candidates"]
        entry = evidence["entries"][0]
        self.assertEqual(evidence["resolved_count"], len(evidence["entries"]))
        self.assertEqual(evidence["expected_source_occurrences"], 1)
        self.assertEqual(entry["item_id"], 400338)
        self.assertEqual(entry["verified_missing_percent"], 5)
        self.assertEqual(entry["source_integrity_flag"], "missing_percent_value")
        self.assertEqual(len(entry["reference_urls"]), 2)
        self.assertEqual(set(shard), {entry["source"]})
        self.assertEqual(shard[entry["source"]], entry["translation"])
        self.assertNotIn(entry["source"], quarantine)
        self.assertIn("by%.", entry["source"])
        self.assertIn("%" + str(entry["verified_missing_percent"]), entry["translation"])
        self.assertEqual(re.findall(r"\d+(?:\.\d+)?", entry["source"]), [])
        self.assertEqual(
            re.findall(r"\d+(?:\.\d+)?", entry["translation"]),
            [str(entry["verified_missing_percent"])],
        )
        self.assertEqual(
            re.findall(r"\^[0-9a-fA-F]{6}", entry["source"]),
            re.findall(r"\^[0-9a-fA-F]{6}", entry["translation"]),
        )
        original = (REPO_ROOT / evidence["source_path"]).read_text(
            encoding="utf-8", errors="surrogateescape"
        )
        blocks = re.split(r"(?m)^\s*\[(\d+)\]\s*=\s*\{", original)
        by_id = dict(zip(blocks[1::2], blocks[2::2]))
        item_lines = [line.strip() for line in by_id[str(entry["item_id"])].splitlines()]
        needle = '"' + entry["source"] + '",'
        self.assertEqual(item_lines.count(needle), 1)
        index = item_lines.index(needle)
        self.assertEqual(item_lines[index - 1], entry["previous_source_line"])
        self.assertEqual(item_lines[index + 1], entry["next_source_line"])
        self.assertEqual(original.count(needle), evidence["expected_source_occurrences"])
        self.assertEqual(
            evidence["upstream_source_blob_sha"], entry["upstream_source_blob_sha"]
        )
        escaped = builder.escape_lua_quoted_content(entry["translation"].encode("ascii"))
        self.assertIsNotNone(
            builder.STRING_RE.fullmatch(bytes([34]) + escaped + bytes([34]))
        )

    def test_unescaped_double_quote_becomes_lua_escape(self) -> None:
        self.assertEqual(
            builder.escape_lua_quoted_content(b'Valkyrie "Frist" adi.'),
            b'Valkyrie \\"Frist\\" adi.',
        )

    def test_existing_escape_remains_unchanged(self) -> None:
        value = b'Valkyrie \\"Frist\\" adi.'
        self.assertEqual(builder.escape_lua_quoted_content(value), value)

    def test_dangling_backslash_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "dangling"):
            builder.escape_lua_quoted_content(b"Bad " + bytes([0x5C]))

    def test_exact_substitution_is_single_lua_string(self) -> None:
        source = r'A sword named after Valkyrie \"Frist\".'
        prepared = builder.prepare_exact_translations(
            {"translations": {source: 'Valkyrie "Frist" adi.'}}
        )
        line = ('identifiedDescriptionName = { "' + source + '", }').encode("ascii")
        counts = {}
        output = builder.apply_exact_translations(line, prepared, counts)
        self.assertEqual(counts["exact_translation"], 1)
        self.assertEqual(
            output,
            b'identifiedDescriptionName = { "Valkyrie \\"Frist\\" adi.", }',
        )

    def test_all_canonical_exact_shards_have_safe_targets(self) -> None:
        config = json.loads(
            (REPO_ROOT / "TurkuazTR/config/iteminfo-rules.json").read_text(encoding="utf-8")
        )
        shards = json.loads(
            (REPO_ROOT / "TurkuazTR/config/iteminfo-exact-shards.json").read_text(
                encoding="utf-8"
            )
        )
        paths = [config["exact_translation_path"], *shards.get("paths", [])]
        combined: dict[bytes, bytes] = {}
        for path in paths:
            records = json.loads((REPO_ROOT / path).read_text(encoding="utf-8"))
            translated = builder.prepare_exact_translations(records)
            for source, target in translated.items():
                self.assertIsNotNone(
                    builder.STRING_RE.fullmatch(b'"' + target + b'"'),
                    msg=f"Invalid Lua literal: {source!r}",
                )
                self.assertNotIn(source, combined, msg=f"Duplicate exact key: {source!r}")
                combined[source] = target
        self.assertGreater(len(combined), 10000)


    def test_v1123_rules_keep_numbers_color_tags_and_boundaries(self) -> None:
        config = json.loads(
            (REPO_ROOT / "TurkuazTR/config/iteminfo-rules.json").read_text(
                encoding="utf-8"
            )
        )
        rules = {
            rule["id"]: rule
            for rule in config["rules"]
            if rule["id"].startswith("lore_v1123_")
        }
        samples = {
            "lore_v1123_experience_race":
                "Increases experience gained from ^FF0000Angel^000000 race monsters by 15%.",
            "lore_v1123_magic_damage_size":
                "Increases Magical Damage against monsters of ^FF0000Large^000000 size by 10%.",
            "lore_v1123_magic_damage_size_extra":
                "Increases Magical Damage against monsters of ^FF0000Large^000000 size by additional 3%.",
            "lore_v1123_refine_restricted_items":
                "It can only be used on Dim Glacier weapons with refine level between +9 and +11.",
            "lore_v1123_level_restricted_items":
                "It can only be used from Level 150 to Level 169.",
            "lore_v1123_autocast_chance_percent":
                "Increases the chance to auto-cast ^009900Psychic Wave^000000 by 2%.",
            "lore_v1123_autocast_chance_generic":
                "Increases the chance to auto-cast ^009900Judex^000000.",
            "lore_v1123_bonus_contains":
                "It also contains Kagerou, Oboro, Rebellion and Doram Stone(Garment).",
        }
        self.assertEqual(set(rules), set(samples))
        for rule_id, source in samples.items():
            with self.subTest(rule=rule_id):
                prepared = builder.prepare_rules([rules[rule_id]])
                original = ('"' + source + '"').encode("ascii")
                counts: dict[str, int] = {}
                actual = builder.apply_rules(original, prepared, counts)
                self.assertNotEqual(actual, original)
                self.assertEqual(counts.get(rule_id), 1)
                self.assertEqual(
                    sorted(re.findall(rb"[0-9]+", original)),
                    sorted(re.findall(rb"[0-9]+", actual)),
                )
                self.assertEqual(
                    sorted(re.findall(rb"\^[0-9A-Fa-f]{6}", original)),
                    sorted(re.findall(rb"\^[0-9A-Fa-f]{6}", actual)),
                )
                self.assertIsNotNone(builder.STRING_RE.fullmatch(actual))



    def test_v1124_combat_rules_preserve_numeric_color_contract(self) -> None:
        data = json.loads(
            (REPO_ROOT / "TurkuazTR/config/iteminfo-rules.json").read_text(
                encoding="utf-8"
            )
        )
        rules = {
            rule["id"]: rule
            for rule in data["rules"]
            if rule["id"].startswith("lore_v1124_")
        }
        samples = {
            "lore_v1124_physical_enemies_extra":
                "Increases Physical Damage against enemies of ^FF0000Demon^000000 race by additional 10%.",
            "lore_v1124_physical_enemies":
                "Increases Physical Damage against enemies of Angel monsters by 5%.",
            "lore_v1124_physical_monsters":
                "Increases Physical Damage against monsters of ^777777Holy^000000 and ^777777Neutral^000000 element by 25%.",
            "lore_v1124_magical_enemies_extra":
                "Increases Magical Damage against enemies of ^FF0000Boss^000000 class by additional 15%.",
            "lore_v1124_magical_enemies":
                "Increases Magical Damage against enemies of ^777777Holy^000000 element by 3%.",
            "lore_v1124_damage_enemies":
                "Increases Damage against enemies of Niflheim monsters by 20%.",
            "lore_v1124_damage_monsters":
                "Increases Damage against monsters of ^777777Holy^000000 by 10%.",
            "lore_v1124_magical_monsters":
                "Increases Magical Damage against monsters of ^FF0000Insect^000000 and ^FF0000Demi-Human^000000 race, except ^FF0000Players^000000, by 10%.",
            "lore_v1124_received_healing":
                "Increases received ^009900Healing^000000 amount by 15%.",
            "lore_v1124_status_resistance":
                "Increases resistance against ^663399Poison^000000 by 30%.",
            "lore_v1124_refine_item":
                "Increases the refine level of a +10 Geoborg armor by +1.",
            "lore_v1124_autocast_additional_chance":
                "Increases the chance to auto-cast ^009900Ignition Break^000000 by additional 1%.",
            "lore_v1124_inflict_status_chance":
                "Increases the chance of inflicting ^663399Critical Wound^000000 by 5%.",
        }
        self.assertEqual(set(rules), set(samples))
        for rule_id, source in samples.items():
            with self.subTest(rule=rule_id):
                prepared = builder.prepare_rules([rules[rule_id]])
                before = ('"' + source + '"').encode("ascii")
                counts: dict[str, int] = {}
                after = builder.apply_rules(before, prepared, counts)
                self.assertNotEqual(before, after)
                self.assertEqual(counts.get(rule_id), 1)
                self.assertEqual(
                    sorted(re.findall(rb"[0-9]+", before)),
                    sorted(re.findall(rb"[0-9]+", after)),
                )
                self.assertEqual(
                    sorted(re.findall(rb"\^[0-9A-Fa-f]{6}", before)),
                    sorted(re.findall(rb"\^[0-9A-Fa-f]{6}", after)),
                )
                self.assertIsNotNone(builder.STRING_RE.fullmatch(after))



    def test_v1125_recipe_rules_keep_numeric_contract(self) -> None:
        data = json.loads(
            (REPO_ROOT / "TurkuazTR/config/iteminfo-rules.json").read_text(
                encoding="utf-8"
            )
        )
        rules = {
            r["id"]: r
            for r in data["rules"] if r["id"].startswith("lore_v1125_")
        }
        samples = {
            "lore_v1125_weapon_difficulty":
                "It is more difficult to handle than the existing Relapse Axe.",
            "lore_v1125_shadow_combine_random_can":
                "If you combine 2 of any of the following Shadow Equipments which are refined to +7 or higher, you can obtain one of these randomly:",
            "lore_v1125_shadow_combine_random":
                "If you combine 2 of any of the following Shadow Equipments which are refined to +7 or higher, you obtain one of these randomly.",
            "lore_v1125_shadow_combine_experience":
                "If you combine five +7 or higher refined of any of the following Shadow Equipments, you can obtain one Experience Shadow Shield:",
        }
        self.assertEqual(set(rules), set(samples))
        for key, source in samples.items():
            with self.subTest(rule=key):
                before = ('"' + source + '"').encode("ascii")
                counts: dict[str, int] = {}
                after = builder.apply_rules(
                    before, builder.prepare_rules([rules[key]]), counts
                )
                self.assertNotEqual(before, after)
                self.assertEqual(counts.get(key), 1)
                self.assertEqual(
                    sorted(re.findall(rb"[0-9]+", before)),
                    sorted(re.findall(rb"[0-9]+", after)),
                )
                self.assertEqual(
                    sorted(re.findall(rb"\^[0-9A-Fa-f]{6}", before)),
                    sorted(re.findall(rb"\^[0-9A-Fa-f]{6}", after)),
                )
                self.assertIsNotNone(builder.STRING_RE.fullmatch(after))



    def test_v1126_lore_rules_preserve_lua_and_color_tags(self) -> None:
        config = json.loads(
            (REPO_ROOT / "TurkuazTR/config/iteminfo-rules.json").read_text(
                encoding="utf-8"
            )
        )
        rules = {
            r["id"]: r
            for r in config["rules"] if r["id"].startswith("lore_v1126_")
        }
        samples = {
            "lore_v1126_must_equip_tag":
                "It must be equipped with ^990099Flush Metal Detector Mk47^000000.",
            "lore_v1126_small_power_protection":
                "It is said that the protection of crabs can be obtained by collecting the small power.",
            "lore_v1126_recover_original_power":
                "It is said that the original performance can be demonstrated by regaining the power of ^0000CCEarth^000000.",
            "lore_v1126_old_magic_resonance":
                "It looks old but has hidden magic, it resonates with Ancient Hero's Boots.",
            "lore_v1126_specialized_combat_power":
                "It is said to be imbued with power specialized for magical combat.",
        }
        self.assertEqual(set(rules), set(samples))
        for rule_id, src in samples.items():
            with self.subTest(rule=rule_id):
                before = ('"' + src + '"').encode("ascii")
                counts: dict[str, int] = {}
                after = builder.apply_rules(
                    before, builder.prepare_rules([rules[rule_id]]), counts
                )
                self.assertNotEqual(before, after)
                self.assertEqual(counts.get(rule_id), 1)
                self.assertEqual(
                    sorted(re.findall(rb"[0-9]+", before)),
                    sorted(re.findall(rb"[0-9]+", after)),
                )
                self.assertEqual(
                    sorted(re.findall(rb"\^[0-9A-Fa-f]{6}", before)),
                    sorted(re.findall(rb"\^[0-9A-Fa-f]{6}", after)),
                )
                self.assertIsNotNone(builder.STRING_RE.fullmatch(after))



    def test_v1127_exact_batch_keeps_source_numbers_and_colors(self) -> None:
        shard = json.loads(
            (REPO_ROOT / "TurkuazTR/config/iteminfo-exact-v1127.tr.json").read_text(
                encoding="utf-8"
            )
        )
        translations = shard["translations"]
        self.assertGreaterEqual(len(translations), 330)
        for source, target in translations.items():
            with self.subTest(source=source[:90]):
                self.assertNotEqual(source, target)
                target.encode("ascii")
                self.assertEqual(
                    sorted(re.findall(r"[0-9]+(?:[.,][0-9]+)?", source)),
                    sorted(re.findall(r"[0-9]+(?:[.,][0-9]+)?", target)),
                )
                self.assertEqual(
                    sorted(re.findall(r"\^[0-9A-Fa-f]{6}", source)),
                    sorted(re.findall(r"\^[0-9A-Fa-f]{6}", target)),
                )
                self.assertIsNotNone(
                    builder.STRING_RE.fullmatch(
                        b'"' + builder.escape_lua_quoted_content(target.encode("ascii")) + b'"'
                    )
                )

    def test_v1127_combat_patterns_keep_numbers_and_color_tags(self) -> None:
        data = json.loads(
            (REPO_ROOT / "TurkuazTR/config/iteminfo-rules.json").read_text(
                encoding="utf-8"
            )
        )
        rules = {
            r["id"]: r
            for r in data["rules"] if r["id"].startswith("lore_v1127_")
        }
        samples = {
            "lore_v1127_damage_thanatos":
                "Increases damage agaist Thanatos monsters by 10%.",
            "lore_v1127_damage_element_monsters":
                "Increases damage against monsters of ^0000BBWater^000000 element by 5%.",
            "lore_v1127_damage_special_dungeon":
                "Increases damage against monsters in ^0033CCLarge Bath Meditathio^000000 by 10% for 15 minutes.",
            "lore_v1127_magical_every_race_extra":
                "Increases Magical Damage against monsters of every race by additional 10%.",
            "lore_v1127_magical_every_element_extra":
                "Increases Magical Damage against monsters of every element by additional 25%",
            "lore_v1127_magical_every_size_extra":
                "Increases Magical Damage against monsters of every size by additional 15%.",
            "lore_v1127_physical_every_element_extra":
                "Increases Physical Damage against monsters of every element by additional 10%.",
            "lore_v1127_elemental_spell_damage":
                "Increases Magical Damage with every element by 15% for 15 minutes.",
            "lore_v1127_skill_damage_simple":
                "Increases ^009900Round Trip^000000 damage by 1%.",
            "lore_v1127_skill_damage_simple_extra":
                "Increases ^009900Axe Tornado^000000 damage by additional 50%.",
            "lore_v1127_physical_from_races":
                "Increases Physical Damage taken from ^FF0000Demon^000000 race monsters by 20%.",
            "lore_v1127_ranged_additional":
                "Increases Ranged Physical Damage by an additional 4%.",
            "lore_v1127_natural_hp_recovery":
                "Increases Natural HP Recovery Rate by 100%.",
            "lore_v1127_bow_damage":
                "Increases ^990099Bow^000000 class weapon damage by 5%.",
        }
        self.assertEqual(set(rules), set(samples))
        for name, phrase in samples.items():
            with self.subTest(rule=name):
                before = ('"' + phrase + '"').encode("ascii")
                counts: dict[str, int] = {}
                after = builder.apply_rules(
                    before, builder.prepare_rules([rules[name]]), counts
                )
                self.assertNotEqual(before, after)
                self.assertEqual(counts.get(name), 1)
                self.assertEqual(
                    sorted(re.findall(rb"[0-9]+", before)),
                    sorted(re.findall(rb"[0-9]+", after)),
                )
                self.assertEqual(
                    sorted(re.findall(rb"\^[0-9A-Fa-f]{6}", before)),
                    sorted(re.findall(rb"\^[0-9A-Fa-f]{6}", after)),
                )
                self.assertIsNotNone(builder.STRING_RE.fullmatch(after))



    def test_v1128_exact_lore_retains_numbers_colors_and_lua_safety(self) -> None:
        shard = json.loads(
            (REPO_ROOT / "TurkuazTR/config/iteminfo-exact-v1128.tr.json").read_text(
                encoding="utf-8"
            )
        )
        translations = shard["translations"]
        self.assertGreaterEqual(len(translations), 300)
        for source, target in translations.items():
            with self.subTest(source=source[:65]):
                self.assertNotEqual(source, target)
                target.encode("ascii")
                self.assertEqual(
                    sorted(re.findall(r"[0-9]+(?:[.,][0-9]+)?", source)),
                    sorted(re.findall(r"[0-9]+(?:[.,][0-9]+)?", target)),
                )
                self.assertEqual(
                    sorted(re.findall(r"\^[0-9A-Fa-f]{6}", source)),
                    sorted(re.findall(r"\^[0-9A-Fa-f]{6}", target)),
                )
                escaped = builder.escape_lua_quoted_content(
                    target.encode("ascii")
                )
                self.assertIsNotNone(
                    builder.STRING_RE.fullmatch(b'"' + escaped + b'"')
                )

    def test_v1128_lore_rules_preserve_numbers_colors_and_quotes(self) -> None:
        config = json.loads(
            (REPO_ROOT / "TurkuazTR/config/iteminfo-rules.json").read_text(
                encoding="utf-8"
            )
        )
        rules = {
            r["id"]: r
            for r in config["rules"]
            if r["id"].startswith("lore_v1128_")
        }
        cases = {
            "lore_v1128_kafra_buff":
                "Kafra Buff that increases experience and item drop rate for 7 days.",
            "lore_v1128_magic_written_element":
                "It's written about the ^0000BBWater^000000 element magic, ^0000FFJack Frost^000000.",
            "lore_v1128_fortified_improved":
                "It supplemented the shortcomings of the existing Fortified Book.",
            "lore_v1128_bomb_ingredient_list":
                "List of ingredients required to make an Apple bomb.",
            "lore_v1128_herb_hair_dye":
                "Made of Blue Herb, can be used to dye the fabric or hair Blue.",
            "lore_v1128_charm_element":
                "It is said that the force of Earth dwelling inside this charm.",
            "lore_v1128_magic_armor_scroll":
                "Magic scroll that contains Cold Armor. Those who use it will wear water armor.",
            "lore_v1128_magic_attacks_int":
                "Magical attacks have a 3% chance of increasing INT by 120 for 10 seconds.",
            "lore_v1128_magic_attacks_matk":
                "Magical attacks have a 3% chance of increasing MATK by 35% for 10 seconds.",
            "lore_v1128_damage_skill_simple":
                "Increases Damage of ^009900Bash^000000 by 10%.",
            "lore_v1128_damage_skill_extra":
                "Increases Damage of ^009900Bash^000000 by additional 15%.",
            "lore_v1128_magic_attack_restore_sp":
                "Magical attacks have a 1% chance to restore 120 SP per 0.4 seconds for 23 times.",
        }
        self.assertEqual(set(rules), set(cases))
        for name, phrase in cases.items():
            with self.subTest(rule=name):
                before = ('"' + phrase + '"').encode("ascii")
                counts: dict[str, int] = {}
                after = builder.apply_rules(
                    before, builder.prepare_rules([rules[name]]), counts
                )
                self.assertNotEqual(before, after)
                self.assertEqual(counts.get(name), 1)
                self.assertEqual(
                    sorted(re.findall(rb"[0-9]+(?:[.,][0-9]+)?", before)),
                    sorted(re.findall(rb"[0-9]+(?:[.,][0-9]+)?", after)),
                )
                self.assertEqual(
                    sorted(re.findall(rb"\^[0-9A-Fa-f]{6}", before)),
                    sorted(re.findall(rb"\^[0-9A-Fa-f]{6}", after)),
                )
                self.assertIsNotNone(builder.STRING_RE.fullmatch(after))



    def test_v1129_exact_batch_preserves_numbers_colors_and_lua(self) -> None:
        shard = json.loads(
            (REPO_ROOT / "TurkuazTR/config/iteminfo-exact-v1129.tr.json").read_text(
                encoding="utf-8"
            )
        )
        translations = shard["translations"]
        self.assertEqual(len(translations), 305)
        for source, target in translations.items():
            with self.subTest(source=source[:90]):
                self.assertNotEqual(source, target)
                target.encode("ascii")
                self.assertEqual(
                    sorted(re.findall(r"[0-9]+(?:[.,][0-9]+)?", source)),
                    sorted(re.findall(r"[0-9]+(?:[.,][0-9]+)?", target)),
                )
                self.assertEqual(
                    sorted(re.findall(r"\^[0-9A-Fa-f]{6}", source)),
                    sorted(re.findall(r"\^[0-9A-Fa-f]{6}", target)),
                )
                escaped = builder.escape_lua_quoted_content(target.encode("ascii"))
                self.assertIsNotNone(
                    builder.STRING_RE.fullmatch(b'"' + escaped + b'"')
                )

    def test_v1129_lore_rules_preserve_numbers_colors_and_lua(self) -> None:
        config = json.loads(
            (REPO_ROOT / "TurkuazTR/config/iteminfo-rules.json").read_text(
                encoding="utf-8"
            )
        )
        rules = {
            r["id"]: r for r in config["rules"]
            if r["id"].startswith("lore_v1129_")
        }
        samples = {
            "lore_v1129_mystical_dragon_crystal":
                "Mystical crystal with the power of the blue dragon.",
            "lore_v1129_unknown_mysterious_item":
                "Not much is known about the mysterious Golden Axe...",
            "lore_v1129_magic_certain_hp_sp_recovery":
                "Magical attacks have a certain chance to recover 150 SP per second for 4 seconds.",
            "lore_v1129_magic_random_int_increase":
                "Magical attacks have a random chance to increase INT by 175 for 10 seconds.",
            "lore_v1129_shadow_combine_refined":
                "If you combine 2 of either Athena Shadow Shield/Earring and Immune Shadow Armor which are refined to +7 or higher, you can obtain 1 Immune Athena Shadow Shield.",
        }
        self.assertEqual(set(rules), set(samples))
        for rule_id, source in samples.items():
            with self.subTest(rule=rule_id):
                before = ('"' + source + '"').encode("ascii")
                counts: dict[str, int] = {}
                after = builder.apply_rules(
                    before, builder.prepare_rules([rules[rule_id]]), counts
                )
                self.assertNotEqual(before, after)
                self.assertEqual(counts.get(rule_id), 1)
                self.assertEqual(
                    sorted(re.findall(rb"[0-9]+(?:[.,][0-9]+)?", before)),
                    sorted(re.findall(rb"[0-9]+(?:[.,][0-9]+)?", after)),
                )
                self.assertEqual(
                    sorted(re.findall(rb"\^[0-9A-Fa-f]{6}", before)),
                    sorted(re.findall(rb"\^[0-9A-Fa-f]{6}", after)),
                )
                self.assertIsNotNone(builder.STRING_RE.fullmatch(after))



if __name__ == "__main__":
    unittest.main()
