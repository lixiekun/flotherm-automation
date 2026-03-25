#!/usr/bin/env python3
"""
PDML vs FloXML 几何编码对比分析
"""

import struct
import sys
import xml.etree.ElementTree as ET
from pathlib import Path


def parse_floxml_geometries(filepath: str):
    """解析 FloXML 几何数据"""
    tree = ET.parse(filepath)
    root = tree.getroot()

    geometries = []

    def parse_node(node):
        geo_type = node.tag
        if geo_type not in ['cuboid', 'assembly', 'fan', 'prism', 'source',
                            'resistance', 'region', 'monitor_point', 'cylinder',
                            'enclosure', 'heatsink', 'pcb', 'die']:
            return

        name_elem = node.find('name')
        name = name_elem.text if name_elem is not None else f"Unnamed_{geo_type}"

        # 位置
        pos_elem = node.find('position')
        position = (0.0, 0.0, 0.0)
        if pos_elem is not None:
            x = float(pos_elem.findtext('x', '0'))
            y = float(pos_elem.findtext('y', '0'))
            z = float(pos_elem.findtext('z', '0'))
            position = (x, y, z)

        # 尺寸
        size_elem = node.find('size')
        size = None
        if size_elem is not None:
            x = float(size_elem.findtext('x', '0'))
            y = float(size_elem.findtext('y', '0'))
            z = float(size_elem.findtext('z', '0'))
            size = (x, y, z)

        # heatsink 特殊处理
        if geo_type == 'heatsink':
            base_elem = node.find('heat_sink_base')
            if base_elem is not None:
                x = float(base_elem.findtext('x', '0'))
                y = float(base_elem.findtext('y', '0'))
                z = float(base_elem.findtext('z', '0'))
                size = (x, y, z)

        geometries.append({
            'type': geo_type,
            'name': name,
            'position': position,
            'size': size
        })

        # 递归
        geometry_elem = node.find('geometry')
        if geometry_elem is not None:
            for child in geometry_elem:
                parse_node(child)

    geometry_root = root.find('geometry')
    if geometry_root is not None:
        for node in geometry_root:
            parse_node(node)

    return geometries


def extract_pdml_strings(data: bytes):
    """提取 PDML 字符串 (大端序)"""
    strings = {}
    pos = 0
    while pos < len(data) - 10:
        if data[pos:pos+2] == b'\x07\x02':
            if pos + 10 <= len(data):
                length = struct.unpack('>I', data[pos+6:pos+10])[0]
                if 0 < length < 500 and pos + 10 + length <= len(data):
                    try:
                        value = data[pos+10:pos+10+length].decode('utf-8', errors='replace').strip()
                        if value:
                            strings[pos] = value
                    except:
                        pass
        pos += 1
    return strings


def extract_pdml_doubles(data: bytes):
    """提取 PDML 浮点数 (0x06 + 8B BE)"""
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
    return doubles


def find_string_offset(strings: dict, name: str):
    """查找字符串偏移"""
    for pos, s in strings.items():
        if s == name:
            return pos
    return None


def analyze_geometry(name: str, floxml_geo: dict, pdml_data: bytes,
                     strings: dict, doubles: list):
    """分析单个几何体的编码"""
    print(f"\n{'='*70}")
    print(f"分析: {floxml_geo['type']} '{name}'")
    print(f"{'='*70}")

    # FloXML 数据
    pos = floxml_geo['position']
    size = floxml_geo['size']
    print(f"\nFloXML 数据:")
    print(f"  位置: ({pos[0]}, {pos[1]}, {pos[2]})")
    if size:
        print(f"  尺寸: ({size[0]}, {size[1]}, {size[2]})")

    # 在 PDML 中查找
    str_offset = find_string_offset(strings, name)
    if str_offset is None:
        print(f"\nPDML: 未找到字符串 '{name}'")
        return

    print(f"\nPDML 字符串偏移: 0x{str_offset:06X}")

    # 查找附近的浮点数
    search_range = 600
    nearby_doubles = []

    for dpos, dval in doubles:
        rel = dpos - str_offset
        if -search_range <= rel <= search_range:
            nearby_doubles.append((rel, dpos, dval))

    # 按相对位置排序
    nearby_doubles.sort(key=lambda x: x[0])

    print(f"\n附近的浮点数 (相对偏移, 值):")

    for rel, dpos, dval in nearby_doubles[:30]:
        # 检查匹配
        match = ""
        if abs(dval - pos[0]) < 0.0001:
            match = " <-- pos.x!"
        elif abs(dval - pos[1]) < 0.0001:
            match = " <-- pos.y!"
        elif abs(dval - pos[2]) < 0.0001:
            match = " <-- pos.z!"
        elif size:
            if abs(dval - size[0]) < 0.0001:
                match = " <-- size.x!"
            elif abs(dval - size[1]) < 0.0001:
                match = " <-- size.y!"
            elif abs(dval - size[2]) < 0.0001:
                match = " <-- size.z!"

        print(f"  {rel:+5d}: {dval:16.8g}{match}")

    # 尝试识别编码模式
    print(f"\n编码模式分析:")

    # 查找匹配的位置
    pos_matches = [[], [], []]
    size_matches = [[], [], []]

    for i, (rel, dpos, dval) in enumerate(nearby_doubles):
        if abs(dval - pos[0]) < 0.0001:
            pos_matches[0].append(i)
        if abs(dval - pos[1]) < 0.0001:
            pos_matches[1].append(i)
        if abs(dval - pos[2]) < 0.0001:
            pos_matches[2].append(i)
        if size:
            if abs(dval - size[0]) < 0.0001:
                size_matches[0].append(i)
            if abs(dval - size[1]) < 0.0001:
                size_matches[1].append(i)
            if abs(dval - size[2]) < 0.0001:
                size_matches[2].append(i)

    if any(pos_matches):
        print(f"  位置索引: x={pos_matches[0]}, y={pos_matches[1]}, z={pos_matches[2]}")
    if size and any(size_matches):
        print(f"  尺寸索引: x={size_matches[0]}, y={size_matches[1]}, z={size_matches[2]}")


def main():
    if len(sys.argv) < 3:
        print("用法: python compare_geo_encoding.py <floxml> <pdml>")
        return 1

    floxml_path = sys.argv[1]
    pdml_path = sys.argv[2]

    print("=" * 70)
    print("PDML vs FloXML 几何编码对比分析")
    print("=" * 70)

    # 解析 FloXML
    print(f"\n[1] 解析 FloXML: {floxml_path}")
    floxml_geos = parse_floxml_geometries(floxml_path)
    print(f"    找到 {len(floxml_geos)} 个几何体")

    # 读取 PDML
    print(f"\n[2] 读取 PDML: {pdml_path}")
    with open(pdml_path, 'rb') as f:
        pdml_data = f.read()

    strings = extract_pdml_strings(pdml_data)
    doubles = extract_pdml_doubles(pdml_data)
    print(f"    {len(strings)} 字符串, {len(doubles)} 浮点数")

    # 分析每个几何体
    print(f"\n[3] 逐个分析几何体")

    for geo in floxml_geos[:12]:
        analyze_geometry(geo['name'], geo, pdml_data, strings, doubles)

    return 0


if __name__ == "__main__":
    exit(main())
