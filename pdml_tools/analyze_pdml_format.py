#!/usr/bin/env python3
"""
PDML 二进制格式深度分析工具

分析 PDML 文件的结构模式，包括：
1. Section 边界和结构
2. 几何体类型编码
3. 属性编码
4. 数值存储位置
"""

import struct
import sys
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Set
from dataclasses import dataclass, field


@dataclass
class StringInfo:
    """字符串信息"""
    offset: int
    length: int
    value: str


@dataclass
class DoubleInfo:
    """Double 值信息"""
    offset: int
    value: float


@dataclass
class SectionInfo:
    """Section 信息"""
    name: str
    start_offset: int
    end_offset: int = 0
    strings: List[StringInfo] = field(default_factory=list)
    doubles: List[DoubleInfo] = field(default_factory=list)


class PDMLFormatAnalyzer:
    """PDML 格式分析器"""

    # 已知的 section 标记
    SECTION_MARKERS = [
        'gravity',
        'overall control',
        'grid smooth',
        'modeldata',
        'solution domain',
        'geometry',
        'turbulence',
    ]

    # 已知的几何类型名称（从原始 FloXML 中提取）
    GEOMETRY_TYPES = [
        'fan', 'cuboid', 'prism', 'tet', 'inverted_tet', 'sloping_block',
        'source', 'resistance', 'region', 'monitor_point', 'cylinder',
        'assembly', 'enclosure', 'fixed_flow', 'perforated_plate',
        'recirc_device', 'rack', 'cooler', 'network_assembly', 'heatsink',
        'pcb', 'die', 'cutout', 'heatpipe', 'tec', 'square_diffuser',
        'controller',
    ]

    # 已知的几何体名称（从原始 FloXML 中提取）
    KNOWN_GEOMETRY_NAMES = [
        'Fan-1', 'Block', 'Prism1', 'Tet22', 'ITET', 'BAFFLE', 'Source-1',
        'Flow Resistance', 'Region', 'MP-01', 'Cap', '1206', 'Chassis',
        'Fixed Flow', 'Floor Tile', 'Block with Holes', 'Recirc-01',
        'Rack-001', 'Cooler-001', 'Network Assembly Example',
        'Plate Fin Heat Sink', 'Pin Fin Heat Sink', 'Printed Circuit Board',
        'Die SmartPart', 'Cutout Example', 'Simple Heat Pipe',
        'Thermoelectric', 'Diffuser', 'Controller',
    ]

    def __init__(self, filepath: str):
        self.filepath = filepath
        with open(filepath, 'rb') as f:
            self.data = f.read()

        self.strings: Dict[int, StringInfo] = {}
        self.doubles: Dict[int, DoubleInfo] = {}
        self.sections: Dict[str, SectionInfo] = {}
        self.geometry_markers: List[Tuple[int, str]] = []

    def analyze(self):
        """执行完整分析"""
        print("=" * 80)
        print(f"PDML 格式分析: {self.filepath}")
        print("=" * 80)
        print(f"文件大小: {len(self.data):,} 字节")
        print()

        # 1. 解析头部
        self._analyze_header()

        # 2. 提取所有字符串
        self._extract_all_strings()
        print(f"\n找到 {len(self.strings)} 个字符串")

        # 3. 提取所有 double 值
        self._extract_all_doubles()
        print(f"找到 {len(self.doubles)} 个 double 值")

        # 4. 定位 section 边界
        self._locate_sections()
        print(f"\n找到 {len(self.sections)} 个 section:")
        for name, info in self.sections.items():
            print(f"  - {name}: offset {info.start_offset:#x}")

        # 5. 分析几何体编码
        self._analyze_geometry_encoding()

        # 6. 分析 modeldata section
        self._analyze_modeldata()

        # 7. 分析 solution_domain
        self._analyze_solution_domain()

        # 8. 生成对比报告
        self._generate_comparison_report()

    def _analyze_header(self):
        """分析文件头部"""
        print("\n--- 文件头部 ---")
        newline_pos = self.data.find(b'\n')
        if newline_pos > 0:
            header = self.data[:newline_pos].decode('ascii', errors='replace')
            print(f"头部: {header}")

            # 解析版本信息
            parts = header.split()
            if len(parts) >= 3:
                print(f"  格式: {parts[0]}")
                print(f"  版本: {parts[1]}")
                print(f"  产品: {' '.join(parts[2:])}")

    def _extract_all_strings(self):
        """提取所有字符串 - 使用大端序解析长度"""
        pos = 0
        while pos < len(self.data) - 10:
            # 查找字符串标记 0x07 0x02
            if self.data[pos:pos+2] == b'\x07\x02':
                if pos + 10 <= len(self.data):
                    # 大端序解析长度
                    length = struct.unpack('>I', self.data[pos+6:pos+10])[0]
                    if 0 < length < 1000 and pos + 10 + length <= len(self.data):
                        str_data = self.data[pos+10:pos+10+length]
                        try:
                            value = str_data.decode('utf-8', errors='replace').strip('\x00')
                            if value and len(value) >= 1:
                                self.strings[pos] = StringInfo(pos, length, value)
                        except:
                            pass
            pos += 1

    def _extract_all_doubles(self):
        """提取所有 double 值（大端序，标记字节 0x06）"""
        pos = 0
        while pos < len(self.data) - 9:
            if self.data[pos] == 0x06:
                try:
                    value = struct.unpack('>d', self.data[pos+1:pos+9])[0]
                    # 过滤合理的数值范围
                    if -1e15 < value < 1e15 and (abs(value) > 1e-20 or value == 0):
                        # 检查是否不是 NaN 或 Inf
                        if value == value and value != float('inf') and value != float('-inf'):
                            self.doubles[pos] = DoubleInfo(pos, value)
                except:
                    pass
            pos += 1

    def _locate_sections(self):
        """定位各 section 的位置"""
        # 首先找到所有 section 标记
        section_positions = []
        for offset, sinfo in self.strings.items():
            s_lower = sinfo.value.lower()
            for marker in self.SECTION_MARKERS:
                if marker.lower() in s_lower:
                    section_positions.append((offset, marker, sinfo.value))
                    break

        # 按偏移量排序
        section_positions.sort(key=lambda x: x[0])

        # 创建 section 信息
        for i, (offset, marker, full_name) in enumerate(section_positions):
            # 确定 section 结束位置（下一个 section 开始或文件末尾）
            end_offset = section_positions[i+1][0] if i+1 < len(section_positions) else len(self.data)

            info = SectionInfo(marker, offset, end_offset)

            # 收集该 section 内的字符串和 double
            for s_offset, s in self.strings.items():
                if offset <= s_offset < end_offset:
                    info.strings.append(s)

            for d_offset, d in self.doubles.items():
                if offset <= d_offset < end_offset:
                    info.doubles.append(d)

            self.sections[marker] = info

    def _analyze_geometry_encoding(self):
        """分析几何体编码"""
        print("\n--- 几何体编码分析 ---")

        # 查找所有已知的几何体名称
        geometry_offsets = []
        for offset, sinfo in self.strings.items():
            name = sinfo.value
            # 检查是否是几何体名称
            for known_name in self.KNOWN_GEOMETRY_NAMES:
                if known_name.lower() == name.lower():
                    geometry_offsets.append((offset, name))
                    break

        print(f"\n找到 {len(geometry_offsets)} 个已知几何体名称:")
        for offset, name in geometry_offsets[:30]:
            print(f"  {offset:#010x}: {name}")

        # 分析每个几何体名称后的数据模式
        print("\n--- 几何体数据模式分析 ---")

        for str_offset, name in geometry_offsets[:10]:  # 分析前10个
            print(f"\n[{name}] @ {str_offset:#010x}")

            # 查找名称后 500 字节内的数据
            search_range = 600
            end_pos = min(str_offset + search_range, len(self.data))

            # 提取附近的字符串
            nearby_strings = []
            for s_offset, s in self.strings.items():
                if str_offset < s_offset < end_pos:
                    nearby_strings.append((s_offset - str_offset, s.value))

            # 提取附近的 double
            nearby_doubles = []
            for d_offset, d in self.doubles.items():
                if str_offset < d_offset < end_pos:
                    nearby_doubles.append((d_offset - str_offset, d.value))

            if nearby_strings:
                print(f"  附近字符串 (相对偏移):")
                for rel, s in nearby_strings[:5]:
                    print(f"    +{rel:#06x}: '{s}'")

            if nearby_doubles:
                print(f"  附近 double (相对偏移):")
                for rel, v in nearby_doubles[:15]:
                    print(f"    +{rel:#06x}: {v}")

            # 分析十六进制模式
            print(f"  十六进制模式 (名称后 0-100 字节):")
            hex_start = str_offset
            hex_end = min(str_offset + 100, len(self.data))
            hex_data = self.data[hex_start:hex_end]

            # 显示每 20 字节
            for i in range(0, len(hex_data), 20):
                chunk = hex_data[i:i+20]
                hex_str = ' '.join(f'{b:02x}' for b in chunk)
                ascii_str = ''.join(chr(b) if 32 <= b < 127 else '.' for b in chunk)
                print(f"    +{i:#06x}: {hex_str}  |{ascii_str}|")

    def _analyze_modeldata(self):
        """分析 modeldata section"""
        print("\n--- Modeldata Section 分析 ---")

        if 'modeldata' not in self.sections:
            print("未找到 modeldata section")
            return

        section = self.sections['modeldata']
        print(f"范围: {section.start_offset:#x} - {section.end_offset:#x}")

        # 查找属性名称
        attribute_names = [
            'Aluminum', 'FR4', 'Copper', 'Air', 'Paint', 'Outside World',
            'Heat', 'Grid Constraint 1', 'Sub-Divided1', 'Temp And X-Vel',
            'Flow Resistance', 'Transient1', 'Functions-Example', 'Fan Curve 1',
            'VolumeHT', 'Surface', 'People', 'Control:0',
        ]

        found_attributes = []
        for sinfo in section.strings:
            for attr in attribute_names:
                if attr.lower() in sinfo.value.lower():
                    found_attributes.append((sinfo.offset, sinfo.value))
                    break

        print(f"\n找到的属性名称:")
        for offset, name in found_attributes[:20]:
            print(f"  {offset:#010x}: {name}")

            # 显示附近的 double 值
            nearby_doubles = [(d_offset, d.value) for d_offset, d in self.doubles.items()
                             if offset < d_offset < offset + 200]
            if nearby_doubles:
                print(f"    附近数值: {[v for _, v in nearby_doubles[:5]]}")

    def _analyze_solution_domain(self):
        """分析 solution_domain section"""
        print("\n--- Solution Domain 分析 ---")

        if 'solution domain' not in self.sections:
            print("未找到 solution domain section")
            return

        section = self.sections['solution domain']
        print(f"范围: {section.start_offset:#x} - {section.end_offset:#x}")

        print(f"\n该 section 内的 double 值:")
        for d in section.doubles[:20]:
            print(f"  {d.offset:#010x}: {d.value}")

        print(f"\n该 section 内的字符串:")
        for s in section.strings[:10]:
            print(f"  {s.offset:#010x}: '{s.value}'")

    def _generate_comparison_report(self):
        """生成与原始 FloXML 的对比报告"""
        print("\n" + "=" * 80)
        print("对比报告：PDML 数据 vs 原始 FloXML")
        print("=" * 80)

        # 原始 FloXML 中的关键值
        expected_values = {
            'project_name': 'My Model',
            'radiation': 'on',
            'transient': 'true',
            'gravity_direction': 'neg_z',
            'gravity_value': 12.0,
            'outer_iterations': 1500,
            'ambient_temperature': 300.0,
            'datum_pressure': 101325.0,
            'solution_domain_size': (0.05, 0.05, 0.05),
        }

        # 在 PDML 中搜索这些值
        print("\n关键值搜索:")

        # 搜索项目名称
        for offset, s in self.strings.items():
            if 'My Model' in s.value:
                print(f"  项目名称 'My Model' 找到于 {offset:#x}")
                break

        # 搜索 gravity value = 12.0
        for offset, d in self.doubles.items():
            if abs(d.value - 12.0) < 0.001:
                print(f"  Gravity value 12.0 找到于 {offset:#x}")
                # 检查附近的字符串
                for s_offset, s in self.strings.items():
                    if offset - 200 < s_offset < offset + 200:
                        if 'gravity' in s.value.lower():
                            print(f"    (附近有字符串: '{s.value}')")
                        break

        # 搜索 outer_iterations = 1500
        for offset, d in self.doubles.items():
            if abs(d.value - 1500) < 0.1:
                print(f"  Outer iterations 1500 找到于 {offset:#x}")

        # 搜索 solution_domain size = 0.05
        for offset, d in self.doubles.items():
            if abs(d.value - 0.05) < 0.001:
                print(f"  Solution domain size 0.05 找到于 {offset:#x}")

        # 分析几何体类型编码
        print("\n--- 几何体类型编码分析 ---")

        # 查找几何体名称，分析其前后的模式
        geometry_patterns = {}
        for offset, sinfo in self.strings.items():
            name = sinfo.value
            for geo_type in self.GEOMETRY_TYPES:
                if geo_type.lower() == name.lower():
                    # 分析名称前 50 字节的模式
                    pre_start = max(0, offset - 50)
                    pre_data = self.data[pre_start:offset]
                    pattern_key = pre_data[-10:].hex() if len(pre_data) >= 10 else pre_data.hex()

                    if geo_type not in geometry_patterns:
                        geometry_patterns[geo_type] = []
                    geometry_patterns[geo_type].append((offset, pattern_key))
                    break

        print("\n几何体类型模式:")
        for geo_type, patterns in geometry_patterns.items():
            print(f"\n  {geo_type}:")
            for offset, pattern in patterns[:3]:
                print(f"    {offset:#x}: 前导模式 = {pattern}")


def main():
    if len(sys.argv) < 2:
        print("用法: python analyze_pdml_format.py <pdml_file>")
        print("示例: python analyze_pdml_format.py all.pdml")
        return 1

    filepath = sys.argv[1]
    if not Path(filepath).exists():
        print(f"错误: 文件不存在: {filepath}")
        return 1

    analyzer = PDMLFormatAnalyzer(filepath)
    analyzer.analyze()
    return 0


if __name__ == "__main__":
    sys.exit(main())
