#!/usr/bin/env python3
"""
PDML 二进制格式分析器

逆向工程 FloTHERM PDML 文件格式。
"""

import struct
import sys
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Tuple
from collections import defaultdict


@dataclass
class PDMLBlock:
    """PDML 数据块"""
    offset: int
    block_type: bytes
    data: bytes
    children: List['PDMLBlock'] = field(default_factory=list)


@dataclass
class PDMLString:
    """PDML 字符串"""
    offset: int
    length: int
    value: str


class PDMLAnalyzer:
    """PDML 二进制分析器"""

    def __init__(self, filepath: str):
        self.filepath = filepath
        with open(filepath, 'rb') as f:
            self.data = f.read()
        self.pos = 0
        self.strings: List[PDMLString] = []
        self.blocks: List[Tuple[int, bytes, int]] = []  # (offset, marker, length)

    def analyze(self):
        """完整分析"""
        print("=" * 70)
        print(f"PDML 分析: {self.filepath}")
        print("=" * 70)

        # 1. 检查头部
        self._analyze_header()

        # 2. 提取所有字符串
        self._extract_strings()

        # 3. 识别数据块标记
        self._identify_block_markers()

        # 4. 分析结构
        self._analyze_structure()

        # 5. 尝试解析已知字段
        self._parse_known_fields()

    def _analyze_header(self):
        """分析文件头部"""
        print("\n[1] 文件头部")
        print("-" * 40)

        # 检查魔数
        if self.data[:5] == b'#FFFB':
            print("  格式: PDML (FloTHERM 二进制)")
            # 找到换行符
            newline_pos = self.data.find(b'\n')
            if newline_pos > 0:
                header_line = self.data[:newline_pos].decode('ascii', errors='replace')
                print(f"  头部: {header_line}")

                # 解析版本
                parts = header_line.split()
                if len(parts) >= 4:
                    print(f"  版本: {parts[1]}")
                    print(f"  产品: {' '.join(parts[2:])}")

                # 检查二进制魔数
                if len(self.data) > newline_pos + 1:
                    magic = self.data[newline_pos + 1:newline_pos + 3]
                    print(f"  二进制魔数: {magic.hex().upper()}")

    def _extract_strings(self):
        """提取所有可读字符串"""
        print("\n[2] 字符串提取")
        print("-" * 40)

        i = 0
        while i < len(self.data):
            # 查找可打印 ASCII 序列 (长度 >= 4)
            if self.data[i:i+1].isascii() and 32 <= self.data[i] < 127:
                start = i
                while i < len(self.data) and self.data[i:i+1].isascii() and 32 <= self.data[i] < 127:
                    i += 1

                length = i - start
                if length >= 4:
                    try:
                        value = self.data[start:i].decode('ascii')
                        self.strings.append(PDMLString(start, length, value))
                    except:
                        pass
            else:
                i += 1

        # 分类字符串
        categories = {
            'keywords': [],
            'names': [],
            'guids': [],
            'dates': [],
            'numbers': [],
            'other': []
        }

        for s in self.strings:
            if any(kw in s.value.lower() for kw in
                   ['gravity', 'model', 'control', 'grid', 'geometry', 'solve',
                    'material', 'ambient', 'source', 'fluid', 'boundary']):
                categories['keywords'].append(s)
            elif s.value.count('-') == 4 and s.value.count(':') == 1:  # 日期格式
                categories['dates'].append(s)
            elif len(s.value) == 32 and all(c in '0123456789ABCDEF' for c in s.value.upper()):
                categories['guids'].append(s)
            elif s.value[0].isupper() or '[' in s.value:
                categories['names'].append(s)
            else:
                categories['other'].append(s)

        for cat, strings in categories.items():
            if strings:
                print(f"\n  {cat.upper()} ({len(strings)} 个):")
                for s in strings[:10]:  # 只显示前10个
                    print(f"    0x{s.offset:06X} [{s.length:3d}] {s.value[:60]}{'...' if len(s.value) > 60 else ''}")
                if len(strings) > 10:
                    print(f"    ... 还有 {len(strings) - 10} 个")

    def _identify_block_markers(self):
        """识别数据块标记"""
        print("\n[3] 数据块标记分析")
        print("-" * 40)

        # 统计字节模式
        patterns = defaultdict(int)

        # 查找常见的块标记模式
        for i in range(len(self.data) - 4):
            # 检查 0x0A 0x01 0x00 模式 (可能是块开始)
            if self.data[i:i+2] == b'\x0a\x01':
                patterns['0x0A01'] += 1
            if self.data[i:i+2] == b'\x0a\x02':
                patterns['0x0A02'] += 1
            if self.data[i:i+2] == b'\x07\x02':
                patterns['0x0702'] += 1
            if self.data[i:i+2] == b'\x0c\x03':
                patterns['0x0C03'] += 1

        print("  常见模式统计:")
        for pattern, count in sorted(patterns.items(), key=lambda x: -x[1]):
            print(f"    {pattern}: {count} 次")

        # 分析块结构
        print("\n  块结构示例:")
        self._analyze_block_patterns()

    def _analyze_block_patterns(self):
        """分析块结构模式"""
        # 查找 0x0A 后跟 0x01 或 0x02 的模式
        i = 0
        count = 0
        while i < len(self.data) - 20 and count < 5:
            if self.data[i] == 0x0a:
                block_type = self.data[i+1]
                if block_type in (0x01, 0x02):
                    print(f"\n    块 @ 0x{i:06X}:")
                    print(f"      标记: 0x{self.data[i]:02X} 0x{self.data[i+1]:02X}")
                    # 显示接下来的字节
                    preview = self.data[i:i+30]
                    hex_str = ' '.join(f'{b:02X}' for b in preview)
                    print(f"      数据: {hex_str}")

                    # 尝试解析长度
                    if self.data[i+2:i+4] == b'\x00\x10':
                        print("      -> 可能是 0x1000 (4096) 长度标记")
                    elif self.data[i+2:i+4] == b'\x10\x00':
                        length = struct.unpack('<H', self.data[i+2:i+4])[0]
                        print(f"      -> 长度字段: {length}")

                    count += 1
                    i += 10
            i += 1

    def _analyze_structure(self):
        """分析整体结构"""
        print("\n[4] 整体结构分析")
        print("-" * 40)

        # 查找可能的节 (section) 边界
        # 基于字符串位置推断

        # 按偏移排序字符串
        sorted_strings = sorted(self.strings, key=lambda s: s.offset)

        # 计算字符串间距
        gaps = []
        for i in range(1, len(sorted_strings)):
            prev = sorted_strings[i-1]
            curr = sorted_strings[i]
            gap = curr.offset - (prev.offset + prev.length)
            if gap > 100:  # 大于 100 字节的间隙可能是节边界
                gaps.append((prev.offset + prev.length, gap, curr.offset))

        if gaps:
            print("  可能的节边界 (大间隙):")
            for start, gap, end in gaps[:10]:
                print(f"    0x{start:06X} --[{gap:6d} bytes]--> 0x{end:06X}")

    def _parse_known_fields(self):
        """尝试解析已知字段"""
        print("\n[5] 已知字段解析")
        print("-" * 40)

        # 查找 gravity 相关数据
        for s in self.strings:
            if 'gravity' in s.value.lower():
                print(f"\n  GRAVITY 字段 @ 0x{s.offset:06X}")
                self._parse_float_field(s.offset + s.length, 5)

        # 查找 overall control
        for s in self.strings:
            if 'overall control' in s.value.lower() or 'overall_control' in s.value.lower():
                print(f"\n  OVERALL CONTROL 字段 @ 0x{s.offset:06X}")
                self._parse_control_block(s.offset + s.length)

    def _parse_float_field(self, start: int, count: int):
        """尝试解析浮点数字段"""
        print(f"    尝试在偏移 0x{start:06X} 解析浮点数:")

        for i in range(count):
            offset = start + i * 8
            if offset + 8 <= len(self.data):
                # 尝试 little-endian double
                try:
                    val = struct.unpack('<d', self.data[offset:offset+8])[0]
                    if -1e10 < val < 1e10 and val != 0:
                        print(f"      +{i*8}: {val:.6g} (double LE)")
                except:
                    pass

                # 尝试 big-endian double
                try:
                    val = struct.unpack('>d', self.data[offset:offset+8])[0]
                    if -1e10 < val < 1e10 and val != 0:
                        print(f"      +{i*8}: {val:.6g} (double BE)")
                except:
                    pass

    def _parse_control_block(self, start: int):
        """尝试解析控制块"""
        print(f"    控制块数据预览:")
        preview = self.data[start:start+100]
        hex_str = ' '.join(f'{b:02X}' for b in preview[:50])
        print(f"      {hex_str}")

        # 查找附近的整数
        for i in range(0, 50, 4):
            if start + i + 4 <= len(self.data):
                val = struct.unpack('<I', self.data[start+i:start+i+4])[0]
                if 0 < val < 10000:
                    print(f"      +{i}: {val} (可能是迭代次数等)")


def main():
    if len(sys.argv) < 2:
        print("用法: python pdml_analyzer.py <file.pdml>")
        return 1

    analyzer = PDMLAnalyzer(sys.argv[1])
    analyzer.analyze()
    return 0


if __name__ == "__main__":
    exit(main())
