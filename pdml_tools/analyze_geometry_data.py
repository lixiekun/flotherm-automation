#!/usr/bin/env python3
"""
PDML 几何数据分析器

深入分析 PDML 文件中几何体的位置和尺寸编码。
"""

import struct
import sys
from pathlib import Path


def analyze_geometry(filepath: str):
    """分析几何数据编码"""

    with open(filepath, 'rb') as f:
        data = f.read()

    print("=" * 70)
    print(f"几何数据分析: {filepath}")
    print("=" * 70)

    # 查找几何相关字符串
    geometry_keywords = ['coldplate', 'plate', 'block', 'cuboid', 'assembly', 'heatsink']

    # 使用大端序提取字符串
    strings = {}
    pos = 0
    while pos < len(data) - 10:
        if data[pos:pos+2] == b'\x07\x02':
            if pos + 10 <= len(data):
                length = struct.unpack('>I', data[pos+6:pos+10])[0]
                if 0 < length < 1000 and pos + 10 + length <= len(data):
                    str_data = data[pos+10:pos+10+length]
                    try:
                        value = str_data.decode('utf-8', errors='replace').strip()
                        if value:
                            strings[pos] = value
                    except:
                        pass
        pos += 1

    # 提取所有 double 值 (0x06 + 8B BE)
    doubles = []
    pos = 0
    while pos < len(data) - 9:
        if data[pos] == 0x06:
            try:
                value = struct.unpack('>d', data[pos+1:pos+9])[0]
                if -1e15 < value < 1e15 and abs(value) > 1e-15:
                    doubles.append((pos, value))
            except:
                pass
        pos += 1

    print(f"\n找到 {len(strings)} 个字符串, {len(doubles)} 个浮点数")

    # 查找几何名称
    print("\n[几何相关字符串分析]")
    print("-" * 60)

    for str_pos, str_val in sorted(strings.items()):
        str_lower = str_val.lower()
        if any(kw in str_lower for kw in geometry_keywords):
            print(f"\n字符串: '{str_val}' @ 0x{str_pos:06X}")

            # 分析字符串前后的数据
            start = max(0, str_pos - 200)
            end = min(len(data), str_pos + len(str_val) + 200)

            # 查找附近的浮点数
            nearby_doubles = [(p, v) for p, v in doubles
                             if start <= p <= end]

            if nearby_doubles:
                print(f"  附近的浮点数 ({len(nearby_doubles)} 个):")
                for p, v in nearby_doubles[:20]:
                    rel_pos = p - str_pos
                    print(f"    {rel_pos:+5d}: {v:12.6g}")

            # 分析原始字节
            print(f"  原始字节 (前50字节):")
            raw_start = max(0, str_pos - 50)
            raw_data = data[raw_start:str_pos]
            hex_str = ' '.join(f'{b:02X}' for b in raw_data[-50:])
            print(f"    {hex_str}")

    # 尝试找出坐标和尺寸的模式
    print("\n[坐标/尺寸模式分析]")
    print("-" * 60)

    # 查找可能的坐标组 (6个连续的合理值: x, y, z, dx, dy, dz)
    coord_patterns = []
    for i in range(len(doubles) - 5):
        group = doubles[i:i+6]
        values = [v for p, v in group]

        # 检查是否可能是坐标和尺寸
        # 位置通常在 -1 到 1 之间，尺寸通常在 0.001 到 1 之间
        positions = values[:3]
        sizes = values[3:]

        if all(-1 <= v <= 1 for v in positions) and all(0.001 <= v <= 1 for v in sizes):
            # 检查是否连续 (间隔合理)
            offsets = [p for p, v in group]
            gaps = [offsets[j+1] - offsets[j] for j in range(5)]
            if all(g < 50 for g in gaps):  # 间隔小于 50 字节
                coord_patterns.append((group, offsets, gaps))

    print(f"找到 {len(coord_patterns)} 个可能的坐标组")
    for i, (group, offsets, gaps) in enumerate(coord_patterns[:10]):
        values = [v for p, v in group]
        print(f"\n  坐标组 {i+1} @ 0x{offsets[0]:06X}:")
        print(f"    位置: ({values[0]:.4f}, {values[1]:.4f}, {values[2]:.4f})")
        print(f"    尺寸: ({values[3]:.4f}, {values[4]:.4f}, {values[5]:.4f})")
        print(f"    间隔: {gaps}")

    # 分析 0x0A 0x02 块 (可能包含几何数据)
    print("\n[块结构分析 - 0x0A 0x02]")
    print("-" * 60)

    pos = 0
    count = 0
    while pos < len(data) - 50 and count < 5:
        if data[pos:pos+2] == b'\x0a\x02':
            print(f"\n  块 @ 0x{pos:06X}:")
            # 显示块类型码
            type_code = struct.unpack('<H', data[pos+2:pos+4])[0]
            print(f"    类型码: 0x{type_code:04X}")

            # 显示原始数据
            raw = data[pos:pos+50]
            hex_str = ' '.join(f'{b:02X}' for b in raw)
            print(f"    数据: {hex_str}")

            # 尝试解析可能的坐标
            # 在块内查找 0x06 + double
            for offset in range(4, 50):
                if pos + offset + 9 <= len(data) and data[pos + offset] == 0x06:
                    try:
                        val = struct.unpack('>d', data[pos+offset+1:pos+offset+9])[0]
                        if -1 < val < 1:
                            print(f"    +{offset}: 0x06 + double = {val:.6g}")
                    except:
                        pass

            count += 1
        pos += 1


def find_solution_domain(data: bytes):
    """查找 solution domain 数据"""
    # solution domain 通常有 6 个值: position (x,y,z) + size (dx,dy,dz)

    # 查找 "solution domain" 或 "domain" 字符串
    pass


def main():
    if len(sys.argv) < 2:
        print("用法: python analyze_geometry_data.py <file.pdml>")
        return 1

    analyze_geometry(sys.argv[1])
    return 0


if __name__ == "__main__":
    exit(main())
