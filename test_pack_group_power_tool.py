#!/usr/bin/env python3
import csv
import json
import struct
import tempfile
import unittest
import zipfile
from pathlib import Path

from pack_group_power_tool import (
    ENTRY_GROUP,
    ENTRY_GROUP_BAK,
    calibrate_pack,
    inspect_pack,
    load_rule,
    patch_pack,
    run_batch,
    save_rule,
)


ROOT = "SyntheticProject.1234567890ABCDEF1234567800000001"


def member_name(suffix: str) -> str:
    return f"{ROOT}/{suffix}"


def make_group(component_name: str, power: float, timestamp: str, label: str) -> bytes:
    payload = bytearray()
    payload.extend(b"#FFFB V2504 Simcenter Flotherm 2504\n")
    payload.extend(f"component:{component_name}\n".encode("ascii"))
    payload.extend(f"timestamp:{timestamp}\n".encode("ascii"))
    payload.extend(f"label:{label}\n".encode("ascii"))
    payload.extend(b"power_le64:")
    payload.extend(struct.pack("<d", power))
    payload.extend(b"\n")
    payload.extend(b"sentinel:unchanged\n")
    return bytes(payload)


def make_pack(path: Path, group_power: float, group_bak_power: float, timestamp: str) -> None:
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr(member_name(ENTRY_GROUP), make_group("R100", group_power, timestamp, "primary"))
        archive.writestr(member_name(ENTRY_GROUP_BAK), make_group("R100", group_bak_power, timestamp, "backup"))
        archive.writestr(
            member_name("PDProject/results_state_file.xml"),
            '<?xml version="1.0" encoding="UTF-8"?><results_state_file/>',
        )
        archive.writestr(member_name("DataSets/BaseSolution/grid"), b"grid-cache")


class PackGroupPowerToolTests(unittest.TestCase):
    def test_calibrate_patch_and_batch(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            base_pack = tmp_path / "base.pack"
            calibrated_pack = tmp_path / "calibrated.pack"
            output_pack = tmp_path / "patched.pack"
            rule_path = tmp_path / "rule.json"
            cases_path = tmp_path / "cases.csv"
            batch_dir = tmp_path / "batch"

            make_pack(base_pack, group_power=10.0, group_bak_power=10.0, timestamp="2026-03-19 00:45")
            make_pack(calibrated_pack, group_power=12.5, group_bak_power=12.5, timestamp="2026-03-19 01:02")

            rule = calibrate_pack(
                baseline_pack=base_pack,
                calibrated_pack=calibrated_pack,
                component_name="R100",
                baseline_power_text="10.0",
                calibrated_power_text="12.5",
            )
            self.assertEqual(rule.component_name, "R100")
            self.assertEqual({entry.entry_suffix for entry in rule.entries}, {ENTRY_GROUP, ENTRY_GROUP_BAK})

            save_rule(rule, rule_path)
            loaded_rule = load_rule(rule_path)

            patch_pack(base_pack, loaded_rule, 15.0, output_pack)
            with zipfile.ZipFile(output_pack, "r") as archive:
                group = archive.read(member_name(ENTRY_GROUP))
                group_bak = archive.read(member_name(ENTRY_GROUP_BAK))
                results_xml = archive.read(member_name("PDProject/results_state_file.xml"))

            self.assertIn(struct.pack("<d", 15.0), group)
            self.assertIn(struct.pack("<d", 15.0), group_bak)
            self.assertEqual(results_xml, b'<?xml version="1.0" encoding="UTF-8"?><results_state_file/>')

            with cases_path.open("w", encoding="utf-8", newline="") as handle:
                writer = csv.DictWriter(handle, fieldnames=["case_id", "component_name", "power"])
                writer.writeheader()
                writer.writerow({"case_id": "caseA", "component_name": "R100", "power": "18.0"})

            manifest = run_batch(base_pack, loaded_rule, cases_path, batch_dir)
            self.assertEqual(len(manifest["cases"]), 1)
            batch_pack = batch_dir / "caseA" / "caseA.pack"
            self.assertTrue(batch_pack.exists())

            with zipfile.ZipFile(batch_pack, "r") as archive:
                batch_group = archive.read(member_name(ENTRY_GROUP))
            self.assertIn(struct.pack("<d", 18.0), batch_group)

        # TemporaryDirectory cleanup proves we do not need repo fixtures on disk.

    def test_inspect_reports_real_entries(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            pack_path = tmp_path / "inspect.pack"
            make_pack(pack_path, group_power=5.0, group_bak_power=5.0, timestamp="2026-03-19 00:45")

            info = inspect_pack(pack_path, include_strings=True, max_strings=20)
            self.assertIn(ENTRY_GROUP, info["entries"])
            self.assertEqual(info["flotherm_version"], "#FFFB V2504 Simcenter Flotherm 2504")
            strings = info["group_strings"]
            self.assertTrue(any("component:R100" in value for value in strings))


if __name__ == "__main__":
    unittest.main()
