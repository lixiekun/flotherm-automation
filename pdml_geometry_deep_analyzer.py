#!/usr/bin/env python3
"""
PDML 几何数据深度分析器

通过对比分析找出几何位置和尺寸的编码规律。
"""

import struct
import sys
from pathlib import Path
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass


@dataclass
class StringInfo:
    offset: int
    length: int
    value: str


@dataclass
class DoubleInfo:
    offset: int
    value: float


@dataclass
class BlockInfo:
    offset: int
    block_type: int
    type_code: int
    raw_data: bytes


class PDMLGeometryAnalyzer:
    """PDML 几何数据深度分析器"""

    # 已知的几何关键词
    GEOMETRY_KEYWORDS = [
        'coldplate', 'plate', 'block', 'cuboid', 'assembly',
        'heatsink', 'fan', 'pcb', 'enclosure', 'chassis',
        'source', 'ambient'
    ]

    def __init__(self, filepath: str):
        self.filepath = filepath
        with open(filepath, 'rb') as f:
            self.data = f.read()

        self.strings: List[StringInfo] = []
        self.doubles: List[DoubleInfo] = []
        self.blocks: List[BlockInfo] = []

    def analyze(self):
        """执行完整分析"""
        print("=" * 70)
        print(f"PDML 几何深度分析: {Path(self.filepath).name}")
        print("=" * 70)

        # 1. 提取基础数据
        self._extract_strings_big_endian()
        self._extract_doubles()
        self._extract_blocks()

        print(f"\n统计: {len(self.strings)} 字符串, {len(self.doubles)} 浮点数, {len(self.blocks)} 块")

        # 2. 查找几何相关字符串
        geo_strings = self._find_geometry_strings()
        print(f"\n找到 {len(geo_strings)} 个几何相关字符串")

        # 3. 分析每个几何字符串周围的数据结构
        for s in geo_strings[:10]:
            self._analyze_geometry_context(s)

        # 4. 尝试找出坐标/尺寸的编码模式
        self._find_coordinate_patterns()

        # 5. 分析块结构中的几何数据
        self._analyze_block_geometry()

    def _extract_strings_big_endian(self):
        """使用大端序提取字符串"""
        pos = 0
        while pos < len(self.data) - 10:
            if self.data[pos:pos+2] == b'\x07\x02':
                if pos + 10 <= len(self.data):
                    # 格式: 07 02 + offset(4B BE) + length(4B BE) + string
                    str_offset = struct.unpack('>I', self.data[pos+2:pos+6])[0]
                    length = struct.unpack('>I', self.data[pos+6:pos+10])[0]
                    if 0 < length < 1000 and pos + 10 + length <= len(self.data):
                        str_data = self.data[pos+10:pos+10+length]
                        try:
                            value = str_data.decode('utf-8', errors='replace').strip()
                            if value:
                                self.strings.append(StringInfo(pos, length, value))
                        except:
                            pass
            pos += 1

    def _extract_doubles(self):
        """提取所有 double 值 (0x06 + 8B BE)"""
        pos = 0
        while pos < len(self.data) - 9:
            if self.data[pos] == 0x06:
                try:
                    value = struct.unpack('>d', self.data[pos+1:pos+9])[0]
                    if -1e15 < value < 1e15 and abs(value) > 1e-15:
                        self.doubles.append(DoubleInfo(pos, value))
                except:
                    pass
            pos += 1

    def _extract_blocks(self):
        """提取 0x0A 0x02 块"""
        pos = 0
        while pos < len(self.data) - 10:
            if self.data[pos:pos+2] == b'\x0a\x02':
                type_code = struct.unpack('<H', self.data[pos+2:pos+4])[0]
                raw_data = self.data[pos:pos+30]
                self.blocks.append(BlockInfo(pos, 0x0A02, type_code, raw_data))
            elif self.data[pos:pos+2] == b'\x0a\x01':
                raw_data = self.data[pos:pos+30]
                self.blocks.append(BlockInfo(pos, 0x0A01, 0, raw_data))
            pos += 1

    def _find_geometry_strings(self) -> List[StringInfo]:
        """查找几何相关字符串"""
        result = []
        for s in self.strings:
            s_lower = s.value.lower()
            # 过滤 GUID
            if len(s.value) == 32 and all(c in '0123456789ABCDEFabcdef' for c in s.value):
                continue
            # 检查关键词
            if any(kw in s_lower for kw in self.GEOMETRY_KEYWORDS):
                result.append(s)
        return result

    def _analyze_geometry_context(self, geo_str: StringInfo):
        """分析几何字符串周围的数据"""
        print(f"\n{'='*60}")
        print(f"分析: '{geo_str.value}' @ 0x{geo_str.offset:06X}")
        print(f"{'='*60}")

        # 查找前后 500 字节范围内的浮点数
        start = geo_str.offset - 500
        end = geo_str.offset + len(geo_str.value) + 500

        nearby_doubles = [(d.offset, d.value) for d in self.doubles
                         if start <= d.offset <= end]

        if nearby_doubles:
            print(f"\n附近的浮点数 ({len(nearby_doubles)} 个):")

            # 按相对位置分组
            before = [(o, v) for o, v in nearby_doubles if o < geo_str.offset]
            after = [(o, v) for o, v in nearby_doubles if o >= geo_str.offset]

            if before:
                print(f"  字符串之前 ({len(before)} 个):")
                for o, v in sorted(before, reverse=True)[:10]:
                    rel = o - geo_str.offset
                    print(f"    {rel:+5d}: {v:16.8g}")

            if after:
                print(f"  字符串之后 ({len(after)} 个):")
                for o, v in sorted(after)[:10]:
                    rel = o - geo_str.offset
                    print(f"    {rel:+5d}: {v:16.8g}")

        # 分析原始字节
        print(f"\n原始字节分析:")

        # 向前查找块标记
        for b in reversed(self.blocks):
            if b.offset < geo_str.offset and geo_str.offset - b.offset < 200:
                print(f"  前面的块 @ 0x{b.offset:06X} ({geo_str.offset - b.offset} 字节前):")
                if b.block_type == 0x0A02:
                    print(f"    类型: 0x0A02, 代码: 0x{b.type_code:04X}")
                else:
                    print(f"    类型: 0x0A01")
                hex_str = ' '.join(f'{b:02X}' for b in b.raw_data[:20])
                print(f"    数据: {hex_str}")
                break

    def _find_coordinate_patterns(self):
        """查找坐标模式 - 6个连续的浮点数可能是位置+尺寸"""
        print(f"\n{'='*60}")
        print("坐标模式分析")
        print(f"{'='*60}")

        patterns = []

        # 查找 6 个连续的浮点数 (间隔小于 20 字节)
        for i in range(len(self.doubles) - 5):
            group = self.doubles[i:i+6]
            offsets = [d.offset for d in group]
            values = [d.value for d in group]

            # 检查间隔
            gaps = [offsets[j+1] - offsets[j] for j in range(5)]
            if all(g <= 20 for g in gaps):
                # 检查值是否合理
                # 位置: -1 到 1, 尺寸: 0.001 到 1
                positions = values[:3]
                sizes = values[3:]

                pos_valid = all(-1 <= v <= 1 for v in positions)
                size_valid = all(0.0001 <= v <= 1 for v in sizes)

                if pos_valid and size_valid:
                    # 查找最近的几何字符串
                    nearest_str = None
                    min_dist = float('inf')
                    for s in self.strings:
                        dist = abs(s.offset - offsets[0])
                        if dist < min_dist and dist < 1000:
                            min_dist = dist
                            nearest_str = s

                    patterns.append({
                        'offset': offsets[0],
                        'values': values,
                        'gaps': gaps,
                        'nearest_str': nearest_str
                    })

        print(f"找到 {len(patterns)} 个可能的坐标组")

        for i, p in enumerate(patterns[:15]):
            v = p['values']
            print(f"\n  模式 {i+1} @ 0x{p['offset']:06X}:")
            print(f"    位置: ({v[0]:.6f}, {v[1]:.6f}, {v[2]:.6f})")
            print(f"    尺寸: ({v[3]:.6f}, {v[4]:.6f}, {v[5]:.6f})")
            if p['nearest_str']:
                dist = p['offset'] - p['nearest_str'].offset
                print(f"    最近字符串: '{p['nearest_str'].value}' ({dist:+d} 字节)")

    def _analyze_block_geometry(self):
        """分析块结构中的几何数据"""
        print(f"\n{'='*60}")
        print("块结构几何分析")
        print(f"{'='*60}")

        # 统计块类型
        type_counts = {}
        for b in self.blocks:
            if b.block_type == 0x0A02:
                key = f"0x0A02:0x{b.type_code:04X}"
            else:
                key = "0x0A01"
            type_counts[key] = type_counts.get(key, 0) + 1

        print("\n块类型统计:")
        for k, v in sorted(type_counts.items(), key=lambda x: -x[1]):
            print(f"  {k}: {v}")

        # 分析特定类型代码的块
        # 根据分析，0x01C0 可能与坐标相关
        print("\n分析可能包含坐标的块:")

        for b in self.blocks:
            if b.block_type == 0x0A02:
                # 检查类型代码
                if b.type_code in [0x01C0, 0x02B0, 0x0210, 0x01A0]:
                    print(f"\n  块 @ 0x{b.offset:06X}, 类型: 0x{b.type_code:04X}")

                    # 在块内查找浮点数
                    for d in self.doubles:
                        if b.offset < d.offset < b.offset + 100:
                            rel = d.offset - b.offset
                            print(f"    +{rel}: {d.value:.6g}")


def main():
    if len(sys.argv) < 2:
        print("用法: python pdml_geometry_deep_analyzer.py <file.pdml>")
        return 1

    analyzer = PDMLGeometryAnalyzer(sys.argv[1])
    analyzer.analyze()
    return 0


if __name__ == "__main__":
    exit(main())
