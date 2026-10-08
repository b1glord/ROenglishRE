#!/usr/bin/env python3
# 📄 Dosya Yolu: /ROenglishRE/TurkuazTR/tools/validate-iteminfo-exact-strings.py
# 📌 Amac: itemInfo exact cevirilerinde Lua string kacisini ve shard guvenligini dogrular
# 📌 Modul - Tool Python
# Version: 1.2.0
# Aciklama: ItemInfo v1.123.0 ve v1.124.0 regex ile exact cevirileri dogrular
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



if __name__ == "__main__":
    unittest.main()
