#!/usr/bin/env python3
"""
PDML 几何类型标识符分析

通过对比原始 FloXML 和 PDML，确定几何体类型的编码规则。
"""

import struct
import sys
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass


@dataclass
class GeometryEntry:
    """几何体条目"""
    name: str
    type_code: bytes  # 07 02 后的 2 字节
    floxml_type: str  # 原始 FloXML 中的类型
    offset: int
    size_values: List[float]
    position_values: List[float]


class GeometryTypeAnalyzer:
    """几何类型分析器"""

    # 原始 FloXML 中的几何体信息（名称 -> 类型）
    FLOXML_GEOMETRY_TYPES = {
        # 从 All-Objects-Attributes-Settings-FullModel.xml 提取
        'Fan-1': 'fan',
        'Block': 'cuboid',
        'Prism1': 'prism',
        'Tet22': 'tet',
        'ITET': 'inverted_tet',
        'BAFFLE': 'sloping_block',
        'Source-1': 'source',
        'Flow Resistance': 'resistance',  # geometry 中的 resistance
        'Region': 'region',
        'MP-01': 'monitor_point',
        'Cap': 'cylinder',
        '1206': 'assembly',
        'Chassis': 'enclosure',
        'Fixed Flow': 'fixed_flow',
        'Floor Tile': 'perforated_plate',
        'Block with Holes': 'cuboid',  # cuboid with holes
        'Recirc-01': 'recirc_device',
        'Rack-001': 'rack',
        'Cooler-001': 'cooler',
        'Network Assembly Example': 'network_assembly',
        'Plate Fin Heat Sink': 'heatsink',
        'Pin Fin Heat Sink': 'heatsink',
        'Printed Circuit Board': 'pcb',
        'Die SmartPart': 'die',
        'Cutout Example': 'cutout',
        'Simple Heat Pipe': 'heatpipe',
        'Thermoelectric': 'tec',
        'Diffuser': 'square_diffuser',
        'Controller': 'controller',
    }

    def __init__(self, pdml_path: str, floxml_path: str):
        self.pdml_path = pdml_path
        self.floxml_path = floxml_path

        with open(pdml_path, 'rb') as f:
            self.pdml_data = f.read()

        with open(floxml_path, 'r', encoding='utf-8') as f:
            self.floxml_data = f.read()

        self.entries: List[GeometryEntry] = []

    def analyze(self):
        """执行分析"""
        print("=" * 80)
        print("PDML 几何类型标识符分析")
        print("=" * 80)

        # 1. 在 PDML 中查找所有已知几何体名称
        self._find_geometry_entries()

        # 2. 分析类型编码
        self._analyze_type_codes()

        # 3. 分析数值位置
        self._analyze_value_positions()

        # 4. 生成类型映射表
        self._generate_type_mapping()

    def _find_geometry_entries(self):
        """查找所有几何体条目"""
        print("\n--- 查找几何体条目 ---")

        for name, floxml_type in self.FLOXML_GEOMETRY_TYPES.items():
            # 在 PDML 中搜索名称
            name_bytes = name.encode('utf-8')
            pos = 0
            while True:
                pos = self.pdml_data.find(name_bytes, pos)
                if pos < 0:
                    break

                # 检查是否是有效的字符串块 (前面应该有 07 02)
                if pos >= 10 and self.pdml_data[pos-10:pos-8] == b'\x07\x02':
                    type_code = self.pdml_data[pos-8:pos-6]
                    offset = pos - 10

                    # 提取附近的 double 值
                    size_values, position_values = self._extract_nearby_values(offset)

                    entry = GeometryEntry(
                        name=name,
                        type_code=type_code,
                        floxml_type=floxml_type,
                        offset=offset,
                        size_values=size_values,
                        position_values=position_values,
                    )
                    self.entries.append(entry)

                    print(f"  {name}: type_code={type_code.hex()}, floxml_type={floxml_type}")
                    if size_values:
                        print(f"    size: {size_values[:3]}")
                    if position_values:
                        print(f"    pos:  {position_values[:3]}")

                pos += 1

    def _extract_nearby_values(self, offset: int) -> Tuple[List[float], List[float]]:
        """提取名称附近的数值"""
        # 搜索名称后 200-500 字节范围内的 double
        size_values = []
        position_values = []

        search_start = offset + 200
        search_end = min(offset + 500, len(self.pdml_data) - 9)

        for p in range(search_start, search_end):
            if self.pdml_data[p] == 0x06:
                try:
                    val = struct.unpack('>d', self.pdml_data[p+1:p+9])[0]
                    if -1e10 < val < 1e10 and val == val:  # 不是 NaN
                        rel_offset = p - offset
                        # 根据相对位置判断是 size 还是 position
                        if 250 <= rel_offset <= 350:
                            size_values.append(val)
                        elif 350 <= rel_offset <= 450:
                            position_values.append(val)
                except:
                    pass

        return size_values, position_values

    def _analyze_type_codes(self):
        """分析类型编码"""
        print("\n--- 类型编码分析 ---")

        # 按 type_code 分组
        code_to_entries: Dict[str, List[GeometryEntry]] = {}
        for entry in self.entries:
            code_hex = entry.type_code.hex()
            if code_hex not in code_to_entries:
                code_to_entries[code_hex] = []
            code_to_entries[code_hex].append(entry)

        print("\n按 type_code 分组:")
        for code_hex, entries in sorted(code_to_entries.items()):
            types = set(e.floxml_type for e in entries)
            names = [e.name for e in entries[:3]]
            print(f"  {code_hex}: {types}")
            print(f"    示例: {names}")

    def _analyze_value_positions(self):
        """分析数值位置"""
        print("\n--- 数值位置分析 ---")

        # 对比 Block 的实际值
        # 原始 FloXML: position (1.1, 2.2, 3.3), size (3, 2, 11)
        print("\nBlock 详细分析 (期望: pos=(1.1,2.2,3.3), size=(3,2,11)):")
        for entry in self.entries:
            if entry.name == 'Block':
                print(f"  offset: {entry.offset:#x}")
                print(f"  size_values: {entry.size_values}")
                print(f"  position_values: {entry.position_values}")

                # 详细十六进制分析
                self._hex_dump_around(entry.offset, entry.name)

        # Fan-1 分析
        # 原始 FloXML: position (0,0,0), fan_geometry: outer_diameter=0.15, hub_diameter=0.05, depth=0.01
        print("\nFan-1 详细分析:")
        for entry in self.entries:
            if entry.name == 'Fan-1':
                print(f"  offset: {entry.offset:#x}")
                print(f"  size_values: {entry.size_values}")
                print(f"  position_values: {entry.position_values}")
                self._hex_dump_around(entry.offset, entry.name)

    def _hex_dump_around(self, offset: int, name: str):
        """在指定位置周围进行十六进制转储"""
        print(f"\n  {name} 十六进制转储 (+0 到 +400):")

        for range_start in [0, 100, 200, 300]:
            start = offset + range_start
            end = min(start + 50, offset + 400, len(self.pdml_data))
            if start >= len(self.pdml_data):
                break

            chunk = self.pdml_data[start:end]
            hex_str = ' '.join(f'{b:02x}' for b in chunk)
            ascii_str = ''.join(chr(b) if 32 <= b < 127 else '.' for b in chunk)
            print(f"    +{range_start:#05x}: {hex_str}")
            # print(f"          |{ascii_str}|")

    def _generate_type_mapping(self):
        """生成类型映射表"""
        print("\n" + "=" * 80)
        print("类型映射表 (可用于转换器)")
        print("=" * 80)

        # 创建 type_code -> floxml_type 的映射
        code_to_type: Dict[str, str] = {}
        for entry in self.entries:
            code_hex = entry.type_code.hex()
            if code_hex not in code_to_type:
                code_to_type[code_hex] = entry.floxml_type
            elif code_to_type[code_hex] != entry.floxml_type:
                # 冲突
                print(f"  警告: type_code {code_hex} 映射到多个类型: {code_to_type[code_hex]}, {entry.floxml_type}")

        print("\nGEOMETRY_TYPE_CODES = {")
        for code_hex, geo_type in sorted(code_to_type.items()):
            print(f"    0x{code_hex.upper()}: '{geo_type}',")
        print("}")


def main():
    pdml_path = "all.pdml"
    floxml_path = "All-Objects-Attributes-Settings-FullModel.xml"

    if not Path(pdml_path).exists():
        print(f"错误: 找不到 {pdml_path}")
        return 1

    if not Path(floxml_path).exists():
        print(f"错误: 找不到 {floxml_path}")
        return 1

    analyzer = GeometryTypeAnalyzer(pdml_path, floxml_path)
    analyzer.analyze()
    return 0


if __name__ == "__main__":
    sys.exit(main())
