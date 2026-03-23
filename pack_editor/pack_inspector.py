#!/usr/bin/env python3
"""
Pack Inspector - Pack 文件检查器

提供 Pack 文件结构的检查和分析功能。
"""

from __future__ import annotations

import json
import re
import struct
import zipfile
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from .data.pack_structure import PackEntry, PackStructure


class PackInspector:
    """
    Pack 文件检查器

    提供详细的 Pack 文件结构分析。

    Usage:
        inspector = PackInspector("model.pack")
        inspector.print_info()
        strings = inspector.extract_strings()
    """

    def __init__(self, pack_path: Union[str, Path]):
        """
        初始化检查器

        Args:
            pack_path: Pack 文件路径
        """
        self.pack_path = Path(pack_path)
        self._structure: Optional[PackStructure] = None
        self._group_blob: Optional[bytes] = None

    @property
    def structure(self) -> PackStructure:
        """获取 Pack 结构"""
        if self._structure is None:
            self._analyze()
        return self._structure

    def _analyze(self) -> None:
        """分析 Pack 文件"""
        if not self.pack_path.exists():
            raise FileNotFoundError(f"Pack file not found: {self.pack_path}")

        if not zipfile.is_zipfile(self.pack_path):
            raise ValueError(f"Not a valid pack file: {self.pack_path}")

        self._structure = PackStructure()

        with zipfile.ZipFile(self.pack_path, "r") as zf:
            names = zf.namelist()

            # 获取根目录前缀
            if names:
                first_name = names[0]
                if "/" in first_name:
                    self._structure.root_prefix = first_name.split("/")[0]

                # 解析项目名称和 GUID
                root = self._structure.root_prefix
                if "." in root:
                    # 查找最后一个点后面是32字符GUID的情况
                    match = re.match(r"(.+)\.([A-F0-9]{32})$", root)
                    if match:
                        self._structure.project_name = match.group(1)
                        self._structure.project_guid = match.group(2)
                    else:
                        self._structure.project_name = root

            # 分析所有条目
            for info in zf.infolist():
                if info.is_dir():
                    continue

                # 计算相对名称
                full_path = info.filename
                name = full_path.split("/", 1)[1] if "/" in full_path else full_path

                entry = PackEntry(
                    name=name,
                    full_path=full_path,
                    size=info.file_size,
                    compressed_size=info.compress_size,
                )

                self._structure.entries[name] = entry

                # 链接特殊条目
                self._link_entry(entry)

            # 提取版本
            self._extract_version(zf)

    def _link_entry(self, entry: PackEntry) -> None:
        """链接特殊条目"""
        name = entry.name.lower()

        special_map = {
            "pdproject/group": "group",
            "pdproject/group.bak": "group_bak",
            "pdproject/results_state_file.xml": "results_state_file",
            "datasets/solution.cat": "solution_cat",
            "datasets/basesolution/grid": "base_solution_grid",
            "datasets/basesolution/connectivity": "base_solution_connectivity",
        }

        if name in special_map:
            setattr(self._structure, special_map[name], entry)

    def _extract_version(self, zf: zipfile.ZipFile) -> None:
        """提取 FloTHERM 版本"""
        if not self._structure.group:
            return

        try:
            content = zf.read(self._structure.group.full_path)
            first_line = content.split(b"\n")[0]
            self._structure.flotherm_version = first_line.decode(
                "latin-1", errors="ignore"
            ).strip()
        except Exception:
            pass

    # ==================== 信息输出 ====================

    def get_info(self) -> Dict[str, Any]:
        """获取 Pack 信息字典"""
        s = self.structure

        return {
            "pack_path": str(self.pack_path),
            "pack_size": self.pack_path.stat().st_size,
            "root_prefix": s.root_prefix,
            "project_name": s.project_name,
            "project_guid": s.project_guid,
            "flotherm_version": s.flotherm_version,
            "total_entries": len(s.entries),
            "has_group": s.group is not None,
            "has_solution": s.base_solution_grid is not None,
            "entries": [
                {
                    "name": e.name,
                    "size": e.size,
                    "compressed_size": e.compressed_size,
                }
                for e in s.entries.values()
            ],
        }

    def print_info(self) -> None:
        """打印 Pack 信息"""
        info = self.get_info()

        print("=" * 60)
        print("Pack File Information")
        print("=" * 60)
        print(f"Path: {info['pack_path']}")
        print(f"Size: {info['pack_size']:,} bytes")
        print()
        print(f"Project: {info['project_name'] or 'N/A'}")
        print(f"GUID: {info['project_guid'] or 'N/A'}")
        print(f"Version: {info['flotherm_version'] or 'N/A'}")
        print()
        print(f"Total entries: {info['total_entries']}")
        print(f"Has group: {info['has_group']}")
        print(f"Has solution: {info['has_solution']}")
        print()
        print("Entries:")
        for entry in info["entries"]:
            size_str = f"{entry['size']:,}"
            if entry['compressed_size'] != entry['size']:
                size_str += f" (compressed: {entry['compressed_size']:,})"
            print(f"  {entry['name']}: {size_str} bytes")

    def print_summary(self) -> None:
        """打印 Pack 摘要 (alias for print_info)"""
        self.print_info()

    def print_tree(self, show_size: bool = False) -> None:
        """打印目录树结构"""
        s = self.structure
        print(f"{s.root_prefix}/")

        # 按目录分组
        dirs: Dict[str, List[PackEntry]] = {}
        for entry in s.entries.values():
            parts = entry.name.split("/")
            if len(parts) > 1:
                dir_name = "/".join(parts[:-1])
            else:
                dir_name = ""
            if dir_name not in dirs:
                dirs[dir_name] = []
            dirs[dir_name].append(entry)

        for dir_name in sorted(dirs.keys()):
            if dir_name:
                print(f"  {dir_name}/")
            entries = dirs[dir_name]
            for entry in sorted(entries, key=lambda e: e.name):
                name = entry.name.split("/")[-1]
                if show_size:
                    print(f"    {name} ({entry.size:,} bytes)")
                else:
                    print(f"    {name}")

    def print_entries(self, pattern: str = "*") -> None:
        """打印匹配的条目"""
        from fnmatch import fnmatch

        s = self.structure
        matches = [e for e in s.entries.values() if fnmatch(e.name, pattern)]

        if not matches:
            print(f"No entries matching: {pattern}")
            return

        print(f"Entries matching '{pattern}':")
        for entry in sorted(matches, key=lambda e: e.name):
            print(f"  {entry.name}: {entry.size:,} bytes")

    # ==================== Group 二进制分析 ====================

    def load_group(self) -> bytes:
        """加载 group 文件内容"""
        if self._group_blob is not None:
            return self._group_blob

        if not self.structure.group:
            raise ValueError("No group file in pack")

        with zipfile.ZipFile(self.pack_path, "r") as zf:
            self._group_blob = zf.read(self.structure.group.full_path)

        return self._group_blob

    def extract_strings(self, min_length: int = 4) -> List[Dict[str, Any]]:
        """
        提取 group 文件中的可读字符串

        Args:
            min_length: 最小字符串长度

        Returns:
            字符串列表 [{offset, string}, ...]
        """
        blob = self.load_group()
        strings = []

        current_start = None
        current_chars = []

        for i, b in enumerate(blob):
            if 32 <= b < 127:
                if current_start is None:
                    current_start = i
                current_chars.append(chr(b))
            else:
                if len(current_chars) >= min_length:
                    strings.append({
                        "offset": current_start,
                        "string": "".join(current_chars),
                    })
                current_start = None
                current_chars = []

        # 处理末尾
        if len(current_chars) >= min_length:
            strings.append({
                "offset": current_start,
                "string": "".join(current_chars),
            })

        return strings

    def find_float_values(self, min_val: float = 1e-10,
                          max_val: float = 1e6) -> List[Dict[str, Any]]:
        """
        查找 group 文件中的浮点数值

        Args:
            min_val: 最小值
            max_val: 最大值

        Returns:
            浮点数列表 [{offset, value, encoding}, ...]
        """
        blob = self.load_group()
        floats = []

        # 只检查 float64 little-endian (FloTHERM 默认)
        for i in range(0, len(blob) - 8):
            try:
                val = struct.unpack("<d", blob[i:i+8])[0]

                # 检查有效性
                if val != val or abs(val) == float("inf"):
                    continue

                if min_val <= abs(val) <= max_val:
                    floats.append({
                        "offset": i,
                        "value": val,
                        "encoding": "float64_le",
                        "hex": blob[i:i+8].hex(),
                    })
            except struct.error:
                continue

        return floats

    def find_object_ids(self) -> List[Dict[str, Any]]:
        """
        查找 group 文件中的对象 ID

        Returns:
            对象 ID 列表 [{offset, guid, context}, ...]
        """
        blob = self.load_group()
        ids = []

        # FloTHERM GUID 格式: 32 字符十六进制
        pattern = rb"([A-F0-9]{32})"

        for m in re.finditer(pattern, blob):
            offset = m.start()
            guid = m.group(1).decode("ascii")

            # 获取上下文 (前面的字符串)
            context_start = max(0, offset - 50)
            context = blob[context_start:offset]

            # 提取可读字符
            context_str = "".join(
                chr(b) if 32 <= b < 127 else "."
                for b in context
            )

            ids.append({
                "offset": offset,
                "guid": guid,
                "context": context_str,
            })

        return ids

    def print_group_analysis(self) -> None:
        """打印 group 文件分析"""
        print("=" * 60)
        print("Group File Analysis")
        print("=" * 60)

        blob = self.load_group()
        print(f"Size: {len(blob):,} bytes")
        print()

        # 提取版本
        first_line = blob.split(b"\n")[0].decode("latin-1", errors="ignore")
        print(f"Header: {first_line}")
        print()

        # 字符串统计
        strings = self.extract_strings()
        print(f"Readable strings (len >= 4): {len(strings)}")
        print("Sample strings:")
        for s in strings[:20]:
            print(f"  0x{s['offset']:04x}: {s['string'][:50]}")
        print()

        # 对象 ID
        ids = self.find_object_ids()
        print(f"Object IDs: {len(ids)}")
        for obj in ids[:10]:
            print(f"  0x{obj['offset']:04x}: {obj['guid']}")


def inspect_pack(pack_path: Union[str, Path],
                 include_strings: bool = False,
                 include_floats: bool = False) -> Dict[str, Any]:
    """
    检查 Pack 文件并返回信息

    Args:
        pack_path: Pack 文件路径
        include_strings: 是否包含 group 中的字符串
        include_floats: 是否包含 group 中的浮点数

    Returns:
        Pack 信息字典
    """
    inspector = PackInspector(pack_path)
    info = inspector.get_info()

    if include_strings:
        info["group_strings"] = inspector.extract_strings()

    if include_floats:
        info["group_floats"] = inspector.find_float_values()

    return info
