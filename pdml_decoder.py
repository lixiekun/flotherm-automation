#!/usr/bin/env python3
"""
PDML 数据解码器

深入分析 PDML 二进制数据编码。
"""

import struct
import sys
from pathlib import Path


def decode_pdml(filepath: str):
    """尝试解码 PDML 文件"""

    with open(filepath, 'rb') as f:
        data = f.read()

    print("=" * 70)
    print(f"PDML 深度解码: {filepath}")
    print("=" * 70)

    # 跳过头部
    header_end = data.find(b'\n') + 1
    pos = header_end

    print(f"\n头部结束位置: 0x{header_end:06X}")
    print(f"魔数: {data[header_end:header_end+4].hex().upper()}")

    # 尝试解析数据结构
    print("\n[1] 逐字节分析前 512 字节")
    print("-" * 40)

    pos = header_end
    indent = 0
    context = []

    while pos < min(header_end + 512, len(data)):
        # 读取标记字节
        marker = data[pos:pos+2]

        if marker == b'\x07\x02':
            # 类型标记 + 长度前缀字符串
            print(f"{'  '*indent}[0x{pos:04X}] STRING_BLOCK (07 02)")
            pos += 2
            # 读取长度和偏移
            if pos + 8 <= len(data):
                str_len = struct.unpack('<I', data[pos:pos+4])[0]
                str_off = struct.unpack('<I', data[pos+4:pos+8])[0]
                print(f"{'  '*indent}        len={str_len}, offset=0x{str_off:04X}")
                pos += 8
                # 读取字符串
                if pos + str_len <= len(data):
                    s = data[pos:pos+str_len]
                    try:
                        decoded = s.decode('utf-8', errors='replace')
                        print(f"{'  '*indent}        value=\"{decoded[:50]}{'...' if len(decoded)>50 else ''}\"")
                    except:
                        print(f"{'  '*indent}        raw={s[:50].hex()}")
                    pos += str_len
            continue

        elif marker == b'\x03\x00':
            # 计数/索引
            print(f"{'  '*indent}[0x{pos:04X}] COUNT (03 00 00 00)")
            pos += 4
            if pos + 4 <= len(data):
                count = struct.unpack('<I', data[pos:pos+4])[0]
                print(f"{'  '*indent}        value={count}")
                pos += 4
            continue

        elif marker == b'\x0a\x01':
            print(f"{'  '*indent}[0x{pos:04X}] BLOCK_START_01 (0A 01)")
            pos += 2
            indent += 1
            continue

        elif marker == b'\x0a\x02':
            print(f"{'  '*indent}[0x{pos:04X}] BLOCK_START_02 (0A 02)")
            pos += 2
            indent += 1
            continue

        elif marker == b'\x01\x00' and indent > 0:
            print(f"{'  '*indent}[0x{pos:04X}] BLOCK_END (01 00 00 00)")
            pos += 4
            indent = max(0, indent - 1)
            continue

        elif data[pos:pos+2] == b'\x0c\x03':
            # 浮点数块
            print(f"{'  '*indent}[0x{pos:04X}] FLOAT_BLOCK (0C 03)")
            pos += 2
            # 尝试读取浮点数
            if pos + 8 <= len(data):
                val = struct.unpack('<d', data[pos:pos+8])[0]
                print(f"{'  '*indent}        double={val}")
                pos += 8
            continue

        else:
            # 显示原始字节
            if pos < len(data):
                preview = data[pos:pos+8]
                print(f"{'  '*indent}[0x{pos:04X}] RAW: {preview.hex().upper()}")
                pos += 1

    # 分析特定字段
    print("\n[2] 定位并解析关键字段")
    print("-" * 40)

    # 查找 gravity
    gravity_pos = data.find(b'gravity')
    if gravity_pos > 0:
        print(f"\nGRAVITY 字段 @ 0x{gravity_pos:06X}")
        # 向前查找结构开始
        start = max(0, gravity_pos - 50)
        print(f"  前置数据: {data[start:gravity_pos].hex().upper()}")
        # 向后查找数值
        end = min(len(data), gravity_pos + 7 + 100)
        print(f"  后置数据: {data[gravity_pos+7:end].hex().upper()}")

        # 尝试解析 gravity 值 (通常是 9.81)
        for offset in range(10, 60, 2):
            test_pos = gravity_pos + 7 + offset
            if test_pos + 8 <= len(data):
                val = struct.unpack('<d', data[test_pos:test_pos+8])[0]
                if 9.0 < val < 10.0:
                    print(f"  找到 gravity 值 @ 0x{test_pos:06X}: {val}")

    # 查找 overall control
    control_pos = data.find(b'overall control')
    if control_pos > 0:
        print(f"\nOVERALL CONTROL 字段 @ 0x{control_pos:06X}")
        start = max(0, control_pos - 30)
        print(f"  前置数据: {data[start:control_pos].hex().upper()}")
        end = min(len(data), control_pos + 16 + 200)
        print(f"  后置数据: {data[control_pos+16:end].hex().upper()}")

        # 尝试解析 outer_iterations (通常是 500)
        for offset in range(10, 100, 4):
            test_pos = control_pos + 16 + offset
            if test_pos + 4 <= len(data):
                val = struct.unpack('<I', data[test_pos:test_pos+4])[0]
                if 100 < val < 2000:
                    print(f"  可能的 outer_iterations @ 0x{test_pos:06X}: {val}")


def find_string_blocks(data: bytes, start: int = 0) -> list:
    """查找所有字符串块"""
    blocks = []
    pos = start

    while pos < len(data) - 10:
        # 查找 08 00 00 00 模式 (长度=8 的字符串)
        if data[pos:pos+4] == b'\x08\x00\x00\x00':
            str_data = data[pos+4:pos+12]
            try:
                s = str_data.decode('ascii')
                if s.isprintable():
                    blocks.append((pos, 8, s))
            except:
                pass

        # 查找 10 00 00 00 模式 (长度=16 的字符串)
        if data[pos:pos+4] == b'\x10\x00\x00\x00':
            str_data = data[pos+4:pos+20]
            try:
                s = str_data.decode('ascii')
                if s.isprintable():
                    blocks.append((pos, 16, s))
            except:
                pass

        pos += 1

    return blocks


def analyze_structure(filepath: str):
    """分析整体结构"""

    with open(filepath, 'rb') as f:
        data = f.read()

    print("\n[3] 结构推断")
    print("-" * 40)

    header_end = data.find(b'\n') + 1

    # 查找所有字符串块
    blocks = find_string_blocks(data, header_end)

    print(f"找到 {len(blocks)} 个字符串块")

    # 按内容分组
    groups = {}
    for pos, length, s in blocks:
        key = s[:10] if len(s) >= 10 else s
        if key not in groups:
            groups[key] = []
        groups[key].append((pos, length, s))

    print("\n字符串块分组:")
    for key, items in sorted(groups.items())[:10]:
        print(f"  '{key}...': {len(items)} 个")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python pdml_decoder.py <file.pdml>")
        sys.exit(1)

    decode_pdml(sys.argv[1])
    analyze_structure(sys.argv[1])
