#!/usr/bin/env python3
"""
Group Binary Handler - 二进制 group 文件处理器

封装 pack_group_power_tool 的功能，提供统一的 API。

Usage:
    from pack_editor import PackManager
    from pack_editor.group_binary import GroupBinaryHandler

    # 校准模式
    handler = GroupBinaryHandler()
    rule = handler.calibrate(
        baseline_pack="baseline.pack",
        calibrated_pack="calibrated.pack",
        component_name="CPU",
        baseline_power=10.0,
        calibrated_power=20.0
    )
    rule.save("rule.json")

    # 应用模式
    handler.apply_rule("baseline.pack", "rule.json", 15.0, "output.pack")
"""

from __future__ import annotations

import hashlib
import json
import struct
import zipfile
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union


class GroupBinaryError(Exception):
    """二进制处理错误"""
    pass


@dataclass
class RuleOffset:
    """规则偏移信息"""
    offset: int
    encoding: str
    baseline_hex: str
    calibrated_hex: str
    calibration_diff_region: Tuple[int, int] = (0, 0)


@dataclass
class EntryRule:
    """条目规则"""
    entry_suffix: str
    size: int
    sha256: str
    offsets: List[RuleOffset]
    anchor_hits: List[int] = field(default_factory=list)
    diff_regions: List[Tuple[int, int]] = field(default_factory=list)


@dataclass
class CalibrationRule:
    """校准规则"""
    tool: str = "pack_editor.group_binary"
    version: int = 1
    flotherm_version: str = ""
    component_name: str = ""
    baseline_power: float = 0.0
    calibrated_power: float = 0.0
    pack_family_prefix: str = ""
    entries: List[EntryRule] = field(default_factory=list)

    def save(self, path: Union[str, Path]) -> None:
        """保存规则到 JSON 文件"""
        path = Path(path)
        path.write_text(json.dumps(asdict(self), indent=2), encoding="utf-8")

    @classmethod
    def load(cls, path: Union[str, Path]) -> "CalibrationRule":
        """从 JSON 文件加载规则"""
        path = Path(path)
        payload = json.loads(path.read_text(encoding="utf-8"))

        return cls(
            tool=payload.get("tool", "pack_editor.group_binary"),
            version=payload.get("version", 1),
            flotherm_version=payload.get("flotherm_version", ""),
            component_name=payload.get("component_name", ""),
            baseline_power=float(payload.get("baseline_power", 0)),
            calibrated_power=float(payload.get("calibrated_power", 0)),
            pack_family_prefix=payload.get("pack_family_prefix", ""),
            entries=[
                EntryRule(
                    entry_suffix=entry.get("entry_suffix", ""),
                    size=entry.get("size", 0),
                    sha256=entry.get("sha256", ""),
                    offsets=[
                        RuleOffset(
                            offset=offset.get("offset", 0),
                            encoding=offset.get("encoding", ""),
                            baseline_hex=offset.get("baseline_hex", ""),
                            calibrated_hex=offset.get("calibrated_hex", ""),
                            calibration_diff_region=tuple(offset.get("calibration_diff_region", (0, 0))),
                        )
                        for offset in entry.get("offsets", [])
                    ],
                    anchor_hits=entry.get("anchor_hits", []),
                    diff_regions=[tuple(r) for r in entry.get("diff_regions", [])],
                )
                for entry in payload.get("entries", [])
            ],
        )


class GroupBinaryHandler:
    """
    二进制 group 文件处理器

    提供校准和应用功能，用于修改 Pack 文件中的功耗值。
    """

    ENTRY_GROUP = "PDProject/group"
    ENTRY_GROUP_BAK = "PDProject/group.bak"

    def __init__(self):
        pass

    # ==================== 校准功能 ====================

    def calibrate(
        self,
        baseline_pack: Union[str, Path],
        calibrated_pack: Union[str, Path],
        component_name: str,
        baseline_power: float,
        calibrated_power: float,
    ) -> CalibrationRule:
        """
        创建校准规则

        通过比较两个 Pack 文件（只有功耗不同）来确定功耗值的存储位置。

        Args:
            baseline_pack: 基准 Pack 文件路径
            calibrated_pack: 校准 Pack 文件路径（功耗已修改）
            component_name: 组件名称
            baseline_power: 基准功耗值
            calibrated_power: 校准功耗值

        Returns:
            CalibrationRule: 校准规则
        """
        baseline_pack = Path(baseline_pack)
        calibrated_pack = Path(calibrated_pack)

        base_entries = self._read_pack_entries(baseline_pack)
        cal_entries = self._read_pack_entries(calibrated_pack)

        if base_entries["_root_prefix"] != cal_entries["_root_prefix"]:
            raise GroupBinaryError("Baseline and calibrated packs do not belong to the same project family")

        entries: List[EntryRule] = []
        flotherm_version = self._extract_version(base_entries[self.ENTRY_GROUP])

        for suffix in (self.ENTRY_GROUP, self.ENTRY_GROUP_BAK):
            base_blob = base_entries.get(suffix)
            cal_blob = cal_entries.get(suffix)
            if base_blob is None or cal_blob is None:
                continue

            entry_rule = self._locate_offsets(
                baseline_blob=base_blob,
                calibrated_blob=cal_blob,
                component_name=component_name,
                baseline_power=baseline_power,
                calibrated_power=calibrated_power,
            )
            entry_rule.entry_suffix = suffix
            entries.append(entry_rule)

        if not entries:
            raise GroupBinaryError("Could not calibrate any group entries")

        return CalibrationRule(
            flotherm_version=flotherm_version,
            component_name=component_name,
            baseline_power=baseline_power,
            calibrated_power=calibrated_power,
            pack_family_prefix=base_entries["_root_prefix"].decode("utf-8"),
            entries=entries,
        )

    def _read_pack_entries(self, pack_path: Path) -> Dict[str, bytes]:
        """读取 Pack 文件中的 group 条目"""
        if not pack_path.exists():
            raise FileNotFoundError(f"Pack file not found: {pack_path}")
        if not zipfile.is_zipfile(pack_path):
            raise GroupBinaryError(f"Not a valid pack file: {pack_path}")

        with zipfile.ZipFile(pack_path, "r") as archive:
            names = archive.namelist()
            entries: Dict[str, bytes] = {}

            for suffix in (self.ENTRY_GROUP, self.ENTRY_GROUP_BAK):
                for name in names:
                    if self._normalize_suffix(name) == suffix:
                        entries[suffix] = archive.read(name)
                        break

            # 获取根前缀
            for name in names:
                if self._normalize_suffix(name) == self.ENTRY_GROUP:
                    entries["_root_prefix"] = name.rsplit("/", 2)[0].encode("utf-8")
                    break

            return entries

    def _normalize_suffix(self, member_name: str) -> str:
        """获取成员的相对路径"""
        if "/" not in member_name:
            return member_name
        return member_name.split("/", 1)[1]

    def _extract_version(self, group_blob: bytes) -> str:
        """提取 FloTHERM 版本"""
        first_line = group_blob.splitlines()[0].decode("latin-1", errors="ignore").strip()
        return first_line or "unknown"

    def _locate_offsets(
        self,
        baseline_blob: bytes,
        calibrated_blob: bytes,
        component_name: str,
        baseline_power: float,
        calibrated_power: float,
    ) -> EntryRule:
        """定位功耗值的偏移位置"""
        diff_regions = self._compute_diff_regions(baseline_blob, calibrated_blob)
        if not diff_regions:
            raise GroupBinaryError("No differences found between baseline and calibrated blobs")

        anchor_hits = self._find_anchor_hits(baseline_blob, component_name)
        specs = self._candidate_encodings(baseline_power, calibrated_power)

        matches_by_spec: Dict[str, List[RuleOffset]] = {}
        scores_by_spec: Dict[str, Tuple[int, int, int, int]] = {}

        for spec in specs:
            hits: List[RuleOffset] = []
            start = 0

            while True:
                idx = baseline_blob.find(spec["baseline_bytes"], start)
                if idx == -1:
                    break

                region = self._region_for_offset(diff_regions, idx, len(spec["baseline_bytes"]))
                if region and calibrated_blob[idx:idx + len(spec["calibrated_bytes"])] == spec["calibrated_bytes"]:
                    hits.append(RuleOffset(
                        offset=idx,
                        encoding=spec["name"],
                        baseline_hex=spec["baseline_bytes"].hex(),
                        calibrated_hex=spec["calibrated_bytes"].hex(),
                        calibration_diff_region=region,
                    ))
                start = idx + 1

            if hits:
                matches_by_spec[spec["name"]] = hits
                spec_scores = [
                    self._score_candidate(hit.offset, len(spec["baseline_bytes"]),
                                          hit.calibration_diff_region, anchor_hits, spec["name"])
                    for hit in hits
                ]
                scores_by_spec[spec["name"]] = max(spec_scores)

        if not matches_by_spec:
            raise GroupBinaryError("Could not locate power value offsets")

        # 选择最佳匹配
        ranked_specs = sorted(
            matches_by_spec.keys(),
            key=lambda name: (scores_by_spec[name], -len(matches_by_spec[name]), name),
            reverse=True,
        )

        winner = ranked_specs[0]
        return EntryRule(
            entry_suffix="",
            size=len(baseline_blob),
            sha256=hashlib.sha256(baseline_blob).hexdigest(),
            offsets=matches_by_spec[winner],
            anchor_hits=anchor_hits,
            diff_regions=diff_regions,
        )

    def _compute_diff_regions(self, left: bytes, right: bytes) -> List[Tuple[int, int]]:
        """计算差异区域"""
        if len(left) != len(right):
            raise GroupBinaryError("Entry sizes must match for calibration")

        regions: List[Tuple[int, int]] = []
        start: Optional[int] = None

        for idx, (a, b) in enumerate(zip(left, right)):
            if a != b and start is None:
                start = idx
            elif a == b and start is not None:
                regions.append((start, idx))
                start = None

        if start is not None:
            regions.append((start, len(left)))

        return regions

    def _find_anchor_hits(self, blob: bytes, component_name: str) -> List[int]:
        """查找组件名称位置"""
        needle = component_name.encode("utf-8", errors="ignore")
        if not needle:
            return []

        hits: List[int] = []
        start = 0
        while True:
            idx = blob.find(needle, start)
            if idx == -1:
                break
            hits.append(idx)
            start = idx + 1
        return hits

    def _candidate_encodings(self, baseline_power: float, calibrated_power: float) -> List[Dict]:
        """生成候选编码"""
        specs = []

        # 二进制编码
        binary_specs = [
            ("float64_le", "<d", 64),
            ("float64_be", ">d", 64),
            ("float32_le", "<f", 32),
            ("float32_be", ">f", 32),
        ]

        for name, fmt, precision in binary_specs:
            try:
                specs.append({
                    "name": name,
                    "baseline_bytes": struct.pack(fmt, baseline_power),
                    "calibrated_bytes": struct.pack(fmt, calibrated_power),
                    "precision": precision,
                })
            except struct.error:
                pass

        # ASCII 编码
        for base_var in [str(baseline_power), f"{baseline_power:g}", f"{baseline_power:.6f}"]:
            for cal_var in [str(calibrated_power), f"{calibrated_power:g}", f"{calibrated_power:.6f}"]:
                if base_var != cal_var:
                    specs.append({
                        "name": f"ascii:{base_var}->{cal_var}",
                        "baseline_bytes": base_var.encode("ascii"),
                        "calibrated_bytes": cal_var.encode("ascii"),
                        "precision": len(base_var),
                    })

        return specs

    def _region_for_offset(self, regions: List[Tuple[int, int]], offset: int, size: int) -> Optional[Tuple[int, int]]:
        """查找偏移所在的差异区域"""
        end = offset + size
        for region_start, region_end in regions:
            if offset < region_end and end > region_start:
                return (region_start, region_end)
        return None

    def _score_candidate(
        self, offset: int, size: int, region: Tuple[int, int],
        anchor_hits: List[int], spec_name: str
    ) -> Tuple[int, int, int, int]:
        """评分候选匹配"""
        anchor_score = 0
        if anchor_hits:
            anchor_distance = min(abs(offset - hit) for hit in anchor_hits)
            if anchor_distance <= 256:
                anchor_score = 3
            elif anchor_distance <= 1024:
                anchor_score = 2
            elif anchor_distance <= 4096:
                anchor_score = 1

        exact_region = 1 if (region[1] - region[0]) == size else 0
        binary_priority = 1 if spec_name.startswith("float64_le") else 0
        compactness = -(region[1] - region[0])

        return (anchor_score, exact_region, binary_priority, compactness)

    # ==================== 应用功能 ====================

    def apply_rule(
        self,
        input_pack: Union[str, Path],
        rule: CalibrationRule,
        new_power: float,
        output_pack: Union[str, Path],
    ) -> Path:
        """
        应用校准规则修改功耗

        Args:
            input_pack: 输入 Pack 文件
            rule: 校准规则
            new_power: 新的功耗值
            output_pack: 输出 Pack 文件

        Returns:
            Path: 输出文件路径
        """
        input_pack = Path(input_pack)
        output_pack = Path(output_pack)

        if input_pack.resolve() == output_pack.resolve():
            raise GroupBinaryError("Refusing to overwrite input pack")

        member_map = self._pack_member_map(input_pack)
        missing = [e.entry_suffix for e in rule.entries if e.entry_suffix not in member_map]
        if missing:
            raise GroupBinaryError(f"Missing entries: {missing}")

        output_pack.parent.mkdir(parents=True, exist_ok=True)

        with zipfile.ZipFile(input_pack, "r") as source, \
             zipfile.ZipFile(output_pack, "w") as target:
            for info in source.infolist():
                data = source.read(info.filename)
                suffix = self._normalize_suffix(info.filename)

                entry_rule = next((e for e in rule.entries if e.entry_suffix == suffix), None)
                if entry_rule:
                    data = self._apply_rule_to_blob(data, entry_rule, new_power)

                # 复制 ZIP 条目属性
                cloned = zipfile.ZipInfo(info.filename, date_time=info.date_time)
                cloned.compress_type = info.compress_type
                cloned.comment = info.comment
                cloned.extra = info.extra
                cloned.internal_attr = info.internal_attr
                cloned.external_attr = info.external_attr
                cloned.create_system = info.create_system
                cloned.flag_bits = info.flag_bits
                target.writestr(cloned, data)

        return output_pack

    def _pack_member_map(self, pack_path: Path) -> Dict[str, str]:
        """获取 Pack 成员映射"""
        with zipfile.ZipFile(pack_path, "r") as archive:
            return {self._normalize_suffix(name): name for name in archive.namelist()}

    def _apply_rule_to_blob(self, blob: bytes, entry_rule: EntryRule, new_power: float) -> bytes:
        """应用规则到二进制数据"""
        patched = bytearray(blob)

        expected_sha256 = hashlib.sha256(blob).hexdigest()
        if expected_sha256 != entry_rule.sha256:
            raise GroupBinaryError("Entry does not match calibrated baseline")

        for offset_rule in entry_rule.offsets:
            old_bytes = bytes.fromhex(offset_rule.baseline_hex)
            new_bytes = self._encoding_bytes(offset_rule.encoding, new_power)

            current = bytes(patched[offset_rule.offset:offset_rule.offset + len(old_bytes)])
            if current != old_bytes:
                raise GroupBinaryError(f"Offset {offset_rule.offset} no longer matches baseline")

            if len(new_bytes) != len(old_bytes):
                raise GroupBinaryError(f"Encoding width changed for value {new_power}")

            patched[offset_rule.offset:offset_rule.offset + len(new_bytes)] = new_bytes

        return bytes(patched)

    def _encoding_bytes(self, encoding_name: str, value: float) -> bytes:
        """将值编码为字节"""
        if encoding_name == "float64_le":
            return struct.pack("<d", value)
        if encoding_name == "float64_be":
            return struct.pack(">d", value)
        if encoding_name == "float32_le":
            return struct.pack("<f", value)
        if encoding_name == "float32_be":
            return struct.pack(">f", value)
        if encoding_name == "int32_le":
            return struct.pack("<i", int(value))
        if encoding_name == "int32_be":
            return struct.pack(">i", int(value))
        if encoding_name == "int64_le":
            return struct.pack("<q", int(value))
        if encoding_name == "int64_be":
            return struct.pack(">q", int(value))
        if encoding_name.startswith("ascii:"):
            _, mapping = encoding_name.split(":", 1)
            _, calibrated = mapping.split("->", 1)
            return calibrated.encode("ascii")

        raise GroupBinaryError(f"Unsupported encoding: {encoding_name}")


# 便捷函数
def calibrate_pack(
    baseline_pack: Union[str, Path],
    calibrated_pack: Union[str, Path],
    component_name: str,
    baseline_power: float,
    calibrated_power: float,
    output_rule: Optional[Union[str, Path]] = None,
) -> CalibrationRule:
    """
    校准 Pack 文件并生成规则

    Args:
        baseline_pack: 基准 Pack 文件
        calibrated_pack: 校准 Pack 文件
        component_name: 组件名称
        baseline_power: 基准功耗
        calibrated_power: 校准功耗
        output_rule: 输出规则文件路径 (可选)

    Returns:
        CalibrationRule: 校准规则
    """
    handler = GroupBinaryHandler()
    rule = handler.calibrate(
        baseline_pack=baseline_pack,
        calibrated_pack=calibrated_pack,
        component_name=component_name,
        baseline_power=baseline_power,
        calibrated_power=calibrated_power,
    )

    if output_rule:
        rule.save(output_rule)

    return rule


def apply_calibration(
    input_pack: Union[str, Path],
    rule_or_path: Union[CalibrationRule, str, Path],
    new_power: float,
    output_pack: Union[str, Path],
) -> Path:
    """
    应用校准规则修改 Pack 文件

    Args:
        input_pack: 输入 Pack 文件
        rule_or_path: 校准规则或规则文件路径
        new_power: 新功耗值
        output_pack: 输出 Pack 文件

    Returns:
        Path: 输出文件路径
    """
    handler = GroupBinaryHandler()

    if isinstance(rule_or_path, (str, Path)):
        rule = CalibrationRule.load(rule_or_path)
    else:
        rule = rule_or_path

    return handler.apply_rule(input_pack, rule, new_power, output_pack)
