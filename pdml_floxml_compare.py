#!/usr/bin/env python3
"""
PDML vs FloXML 对比分析器

通过对比从 FloXML 导入后导出的 PDML，找出几何编码规律。
"""

import struct
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass


@dataclass
class GeometryData:
    """几何数据"""
    name: str
    geo_type: str
    position: Tuple[float, float, float]
    size: Optional[Tuple[float, float, float]] = None
    pdml_offset: int = 0
    pdml_doubles_before: List[Tuple[int, float]] = None
    pdml_doubles_after: List[Tuple[int, float]] = None

    def __post_init__(self):
        if self.pdml_doubles_before is None:
            self.pdml_doubles_before = []
        if self.pdml_doubles_after is None:
            self.pdml_doubles_after = []


def parse_floxml_geometry(filepath: str) -> List[GeometryData]:
    """解析 FloXML 中的几何数据"""
    geometries = []

    tree = ET.parse(filepath)
    root = tree.getroot()

    # 查找所有几何节点
    geo_types = ['cuboid', 'assembly', 'fan', 'prism', 'tet', 'inverted_tet',
                 'sloping_block', 'source', 'resistance', 'region', 'monitor_point',
                 'cylinder', 'enclosure', 'fixed_flow', 'perforated_plate',
                 'recirc_device', 'rack', 'cooler', 'network_assembly', 'heatsink',
                 'pcb', 'die', 'cutout', 'heatpipe', 'tec', 'square_diffuser', 'controller']

    def parse_node(node, parent_name=""):
        geo_type = node.tag
        if geo_type not in geo_types:
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

        # 特殊处理 heatsink
        if geo_type == 'heatsink':
            base_elem = node.find('heat_sink_base')
            if base_elem is not None:
                x = float(base_elem.findtext('x', '0'))
                y = float(base_elem.findtext('y', '0'))
                z = float(base_elem.findtext('z', '0'))
                size = (x, y, z)

        geometries.append(GeometryData(
            name=name,
            geo_type=geo_type,
            position=position,
            size=size
        ))

        # 递归处理子节点
        geometry_elem = node.find('geometry')
        if geometry_elem is not None:
            for child in geometry_elem:
                parse_node(child, name)

    # 查找 geometry 节点
    geometry_root = root.find('geometry')
    if geometry_root is not None:
        for node in geometry_root:
            parse_node(node)

    return geometries


def extract_pdml_strings(data: bytes) -> Dict[int, str]:
    """提取 PDML 字符串"""
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
    return strings


def extract_pdml_doubles(data: bytes) -> List[Tuple[int, float]]:
    """提取 PDML 浮点数"""
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


def find_pdml_geometry_context(name: str, strings: Dict[int, str],
                                doubles: List[Tuple[int, float]]) -> Optional[GeometryData]:
    """在 PDML 中查找几何名称的上下文"""
    # 查找字符串位置
    str_pos = None
    for pos, s in strings.items():
        if s == name:
            str_pos = pos
            break

    if str_pos is None:
        return None

    # 查找附近的浮点数
    search_range = 500
    doubles_before = [(p - str_pos, v) for p, v in doubles
                      if str_pos - search_range <= p < str_pos]
    doubles_after = [(p - str_pos, v) for p, v in doubles
                     if str_pos < p <= str_pos + search_range]

    return GeometryData(
        name=name,
        geo_type='unknown',
        position=(0, 0, 0),
        pdml_offset=str_pos,
        pdml_doubles_before=doubles_before,
        pdml_doubles_after=doubles_after
    )


def analyze_geometry_encoding(floxml_path: str, pdml_path: str):
    """分析几何编码规律"""

    print("=" * 70)
    print("PDML vs FloXML 几何编码对比分析")
    print("=" * 70)

    # 解析 FloXML
    print(f"\n[1] 解析 FloXML: {floxml_path}")
    floxml_geos = parse_floxml_geometry(floxml_path)
    print(f"    找到 {len(floxml_geos)} 个几何体")

    # 读取 PDML
    print(f"\n[2] 读取 PDML: {pdml_path}")
    with open(pdml_path, 'rb') as f:
        pdml_data = f.read()

    pdml_strings = extract_pdml_strings(pdml_data)
    pdml_doubles = extract_pdml_doubles(pdml_data)
    print(f"    {len(pdml_strings)} 字符串, {len(pdml_doubles)} 浮点数")

    # 对比分析
    print(f"\n[3] 对比分析")
    print("=" * 70)

    for flo_geo in floxml_geos[:15]:  # 限制数量
        print(f"\n--- {flo_geo.geo_type}: '{flo_geo.name}' ---")
        print(f"FloXML 位置: ({flo_geo.position[0]}, {flo_geo.position[1]}, {flo_geo.position[2]})")
        if flo_geo.size:
            print(f"FloXML 尺寸: ({flo_geo.size[0]}, {flo_geo.size[1]}, {flo_geo.size[2]})")

        # 在 PDML 中查找
        pdml_geo = find_pdml_geometry_context(pdml_data, flo_geo.name, pdml_strings, pdml_doubles)

        if pdml_geo is None:
            print("PDML: 未找到")
            continue

        print(f"PDML 偏移: 0x{pdml_geo.pdml_offset:06X}")

        # 分析附近的浮点数
        print(f"\nPDML 字符串后的浮点数 (前 15 个):")
        for rel, val in pdml_geo.pdml_doubles_after[:15]:
            # 检查是否匹配 FloXML 数据
            match = ""
            if flo_geo.size:
                if abs(val - flo_geo.size[0]) < 0.0001:
                    match = " <-- size.x"
                elif abs(val - flo_geo.size[1]) < 0.0001:
                    match = " <-- size.y"
                elif abs(val - flo_geo.size[2]) < 0.0001:
                    match = " <-- size.z"
            if abs(val - flo_geo.position[0]) < 0.0001:
                match = " <-- pos.x"
            elif abs(val - flo_geo.position[1]) < 0.0001:
                match = " <-- pos.y"
            elif abs(val - flo_geo.position[2]) < 0.0001:
                match = " <-- pos.z"

            print(f"  {rel:+5d}: {val:16.8g}{match}")

        # 尝试找出规律
        print(f"\n编码规律分析:")
        after_values = [v for _, v in pdml_geo.pdml_doubles_after[:20]]

        # 查找 position 和 size 的位置
        pos_found = [False, False, False]
        size_found = [False, False, False]

        for i, val in enumerate(after_values):
            if not pos_found[0] and abs(val - flo_geo.position[0]) < 0.0001:
                pos_found[0] = True
                print(f"  pos.x 在第 {i+1} 个浮点数")
            if not pos_found[1] and abs(val - flo_geo.position[1]) < 0.0001:
                pos_found[1] = True
                print(f"  pos.y 在第 {i+1} 个浮点数")
            if not pos_found[2] and abs(val - flo_geo.position[2]) < 0.0001:
                pos_found[2] = True
                print(f"  pos.z 在第 {i+1} 个浮点数")

            if flo_geo.size:
                if not size_found[0] and abs(val - flo_geo.size[0]) < 0.0001:
                    size_found[0] = True
                    print(f"  size.x 在第 {i+1} 个浮点数")
                if not size_found[1] and abs(val - flo_geo.size[1]) < 0.0001:
                    size_found[1] = True
                    print(f"  size.y 在第 {i+1} 个浮点数")
                if not size_found[2] and abs(val - flo_geo.size[2]) < 0.0001:
                    size_found[2] = True
                    print(f"  size.z 在第 {i+1} 个浮点数")


def main():
    if len(sys.argv) < 3:
        print("用法: python pdml_floxml_compare.py <floxml> <pdml>")
        return 1

    analyze_geometry_encoding(sys.argv[1], sys.argv[2])
    return 0


if __name__ == "__main__":
    exit(main())
