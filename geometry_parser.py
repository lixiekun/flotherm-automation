#!/usr/bin/env python3
"""
PDML 几何层级解析器

解析 PDML 二进制格式中的几何结构，提取装配体和立方体的嵌套层级、位置、尺寸信息。
"""

import struct
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any


@dataclass
class GeometrySize:
    """几何尺寸"""
    min_size: float
    max_size: float


@dataclass
class GeometryNode:
    """几何节点（装配体或立方体)"""
    node_type: str  # 'assembly' or 'cuboid'
    name: str
    position: Tuple[float, float, float] = (0.0, 0.0, 0.0)
    size: Optional[GeometrySize] = None
    material: str = "Default"
    active: bool = True
    children: List['GeometryNode'] = field(default_factory=list)


@dataclass
class ParseResult:
    """解析结果"""
    geometry_names: List[str] = field(default_factory=list)
    sizes: Dict[str, GeometrySize] = field(default_factory=dict)
    root: Optional[GeometryNode] = None


class PDMLGeometryParser:
    """PDML 几何层级解析器"""

    def __init__(self, data: bytes):
        self.data = data
        self.strings: Dict[int, str] = {}
        self.floats: List[Tuple[int, float]] = []

    def parse(self) -> ParseResult:
        """解析 PDML 文件并返回几何层级"""
        self._extract_strings()
        self._extract_floats()

        result = ParseResult()
        result.geometry_names = self._find_geometry_names()
        result.sizes = self._find_sizes(result.geometry_names)
        result.root = self._build_geometry_hierarchy(result.geometry_names, result.sizes)

        return result

    def _extract_strings(self):
        """提取所有字符串 - 修复版本，使用大端序解析长度"""
        pos = 0
        while pos < len(self.data) - 10:
            if self.data[pos:pos+2] == b'\x07\x02':
                if pos + 10 <= len(self.data):
                    # 格式: 07 02 + 4 bytes offset + length(4B BE) + string
                    # 注意: length 使用大端序
                    length = struct.unpack('>I', self.data[pos+6:pos+10])[0]
                    if 0 < length < 1000 and pos + 10 + length <= len(self.data):
                        str_data = self.data[pos+10:pos+10+length]
                        try:
                            value = str_data.decode('utf-8', errors='replace').strip()
                            if value:
                                self.strings[pos] = value
                        except:
                            pass
            pos += 1

    def _extract_floats(self):
        """提取所有浮点数 (0x06 + 8B BE)"""
        pos = 0
        while pos < len(self.data) - 9:
            if self.data[pos] == 0x06:
                try:
                    value = struct.unpack('>d', self.data[pos+1:pos+9])[0]
                    if -1e15 < value < 1e15 and abs(value) > 1e-15:
                        self.floats.append((pos, value))
                except:
                    pass
            pos += 1

    def _find_geometry_names(self) -> List[str]:
        """查找几何名称字符串"""
        geometry_keywords = [
            'coldplate', 'plate', 'block', 'cuboid', 'assembly',
            'heatsink', 'fan', 'pcb', 'enclosure', 'chassis',
            'source', 'ambient'
        ]
        names = []
        for pos, s in self.strings.items():
            s_lower = s.lower()
            # 过滤 GUID
            if len(s) == 32 and all(c in '0123456789ABCDEFabcdef' for c in s):
                continue
            # 过滤日期
            if len(s) == 16 and '-' in s and ':' in s:
                continue
            # 检查是否包含几何关键词
            if any(kw in s_lower for kw in geometry_keywords):
                if len(s) > 3 and len(s) < 100:
                    names.append(s)
        return names

    def _find_sizes(self, geometry_names: List[str]) -> Dict[str, GeometrySize]:
        """从几何名称字符串附近查找尺寸"""
        sizes = {}
        for name in geometry_names:
            # 在字符串列表中查找该名称
            for pos, s in self.strings.items():
                if s == name:
                    # 在字符串后查找浮点数
                    nearby_floats = self._find_floats_near(pos, 100)
                    if len(nearby_floats) >= 2:
                        # 取前两个可能的尺寸值
                        valid_sizes = [v for p, v in nearby_floats if 0.001 < v < 1]
                        if len(valid_sizes) >= 2:
                            sizes[name] = GeometrySize(
                                min_size=min(valid_sizes),
                                max_size=max(valid_sizes)
                            )
                            break
        return sizes

    def _find_floats_near(self, pos: int, search_range: int) -> List[Tuple[int, float]]:
        """在位置附近查找浮点数"""
        nearby = []
        for fpos, val in self.floats:
            if pos < fpos < pos + search_range:
                nearby.append((fpos, val))
        return nearby

    def _build_geometry_hierarchy(self, names: List[str], sizes: Dict[str, GeometrySize]) -> GeometryNode:
        """构建几何层级"""
        # 创建根装配体
        root = GeometryNode(
            node_type='assembly',
            name='Root Assembly',
            position=(0.0, 0.0, 0.0)
        )

        # 添加几何节点
        for name in names:
            if name in sizes:
                size = sizes[name]
                cuboid = GeometryNode(
                    node_type='cuboid',
                    name=name,
                    position=(0.0, 0.0, 0.0),
                    size=size
                )
                root.children.append(cuboid)

        # 如果没有找到几何名称， 使用默认值
        if not root.children:
            default_cuboid = GeometryNode(
                node_type='cuboid',
                name='Default_Block',
                position=(0.0, 0.0, 0.0),
                size=GeometrySize(min_size=0.01, max_size=0.01)
            )
            root.children.append(default_cuboid)

        return root


def main():
    """测试解析器"""
    import sys

    if len(sys.argv) < 2:
        print("Usage: python geometry_parser.py <file.pdml>")
        return 1

    filepath = sys.argv[1]
    with open(filepath, 'rb') as f:
        data = f.read()

    parser = PDMLGeometryParser(data)
    result = parser.parse()

    print(f"找到 {len(result.geometry_names)} 个几何名称")
    for name in result.geometry_names[:10]:
        print(f"  {name}")

    print(f"\n找到 {len(result.sizes)} 个尺寸")
    for name, size in result.sizes.items():
        print(f"  {name}: min={size.min_size:.6g}, max={size.max_size:.6g}")

    return 0


if __name__ == "__main__":
    exit(main())
