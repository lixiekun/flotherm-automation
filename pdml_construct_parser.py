#!/usr/bin/env python3
"""
PDML Construct Parser

使用 construct 库声明式解析 PDML 二进制格式。
这是 pdml_to_floxml_converter.py 的重构版本，结构更清晰。
"""

from construct import *
from construct.lib import *
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from pathlib import Path
import xml.etree.ElementTree as ET


# ============================================================================
# PDML 二进制结构定义
# ============================================================================

# PDML 类型码映射
GEOMETRY_TYPE_CODES = {
    0x0010: 'pcb',
    0x01D0: 'resistance',
    0x0250: 'cuboid',
    0x0260: 'cutout',
    0x0270: 'monitor_point',
    0x0280: 'prism',
    0x0290: 'region',
    0x02A0: 'resistance',
    0x02B0: 'fan',
    0x02C0: 'source',
    0x02D0: 'heatsink',
    0x02E0: 'assembly',
    0x02F0: 'cuboid',  # Alternate cuboid type code
    0x0300: 'cylinder',
    0x0310: 'enclosure',
    0x0320: 'fan',  # Alternate fan type code
    0x0330: 'fixed_flow',
    0x0340: 'heatsink',  # Alternate heatsink type code
    0x0350: 'pcb',  # Alternate pcb type code
    0x0370: 'perforated_plate',
    0x0380: 'sloping_block',
    0x0390: 'cooler',
    0x0530: 'square_diffuser',
    0x05d0: 'perforated_plate',  # Alternate perforated_plate type code
    0x0731: 'tet',
    0x0732: 'inverted_tet',
    0x0740: 'network_assembly',
    0x0770: 'heatpipe',
    0x0800: 'tec',
    0x0810: 'die',
    0x0840: 'cooler',
    0x0870: 'rack',
}

# 内部几何体名称（跳过）
INTERNAL_GEOMETRY_NAMES = {
    'System',
    'Root Assembly',
    'Printed Circuit Board-1',
    'Printed Circuit Board Comp-2',
    'Junction Temperature',
    'Wall', 'Side Wall', 'Top Wall', 'Bottom Wall',
    'Wall (Low X)', 'Wall (High X)',
    'Wall (Low Y)', 'Wall (High Y)',
    'Wall (Low Z)', 'Wall (High Z)',
    'Inlet', 'Outlet', 'Opening', 'Recirculation Opening',
}


# ============================================================================
# Construct 结构定义
# ============================================================================

# PDML 字符串记录结构
PdmlStringRecord = Struct(
    "marker" / Const(b"\x07\x02"),           # 2 bytes: 固定标记
    "type_code" / Int16ub,                    # 2 bytes: 类型码 (大端)
    "reserved" / Int16ub,                     # 2 bytes: 保留字段
    "length" / Int32ub,                       # 4 bytes: 字符串长度 (大端)
    "value" / Bytes(this.length),             # N bytes: 字符串内容
    Probe(lookahead=0),  # 调试用，显示当前状态
)

# 简化版：跳过 Probe，用于生产
PdmlStringRecordQuiet = Struct(
    "marker" / Const(b"\x07\x02"),
    "type_code" / Int16ub,
    "reserved" / Int16ub,
    "length" / Int32ub,
    "value" / Bytes(this.length),
)


# ============================================================================
# 数据类定义
# ============================================================================

@dataclass
class PdmlGeometryNode:
    """几何体节点"""
    node_type: str
    name: str
    position: Tuple[float, float, float] = (0.0, 0.0, 0.0)
    size: Tuple[float, float, float] = (0.0, 0.0, 0.0)
    material: Optional[str] = None
    source: Optional[str] = None
    children: List['PdmlGeometryNode'] = field(default_factory=list)
    level: int = 2
    orientation: Optional[Tuple[Tuple[float, float, float], ...]] = None
    active: bool = True
    hidden: bool = False
    ignore: bool = False


@dataclass
class PdmlData:
    """PDML 解析结果"""
    name: str = ""
    version: str = ""
    product: str = ""
    geometry: Optional[PdmlGeometryNode] = None


# ============================================================================
# 解析器类
# ============================================================================

class PdmlConstructParser:
    """使用 construct 库的 PDML 解析器"""

    FEATURE_RICH_LAYOUT = "feature_rich_layout"
    COMPACT_FORCED_FLOW_LAYOUT = "compact_forced_flow_layout"

    def __init__(self, filepath: str):
        self.filepath = filepath
        with open(filepath, 'rb') as f:
            self.data = f.read()

        self.strings: Dict[int, str] = {}
        self.tagged_strings: List[Dict[str, Any]] = []
        self.profile = self.FEATURE_RICH_LAYOUT

    def parse(self) -> PdmlData:
        """解析 PDML 文件"""
        result = PdmlData()

        # 1. 解析头部
        header = self._parse_header()
        result.version = header.get('version', '')
        result.product = header.get('product', '')

        # 2. 提取所有字符串记录
        self._extract_all_strings()

        # 3. 获取项目名称
        result.name = self._extract_project_name()

        # 4. 检测 profile
        self.profile = self._detect_profile(result.name)

        # 5. 构建几何体层级
        result.geometry = self._build_geometry()

        return result

    def _detect_profile(self, project_name: str) -> str:
        """检测项目类型"""
        compact_names = ['Heatsink', 'Compact Forced Flow']
        for name in compact_names:
            if name.lower() in project_name.lower():
                return self.COMPACT_FORCED_FLOW_LAYOUT
        return self.FEATURE_RICH_LAYOUT

    def _parse_header(self) -> Dict[str, str]:
        """解析文件头部（第一行文本）"""
        newline_pos = self.data.find(b'\n')
        if newline_pos < 0:
            return {}

        header_line = self.data[:newline_pos].decode('ascii', errors='replace')
        parts = header_line.split()

        return {
            'format': parts[0] if len(parts) > 0 else '',
            'version': parts[1] if len(parts) > 1 else '',
            'product': ' '.join(parts[2:]) if len(parts) > 2 else ''
        }

    def _extract_all_strings(self):
        """提取所有字符串记录"""
        pos = 0
        while pos < len(self.data) - 10:
            # 检查是否是字符串标记
            if self.data[pos:pos+2] == b'\x07\x02':
                try:
                    # 使用 construct 解析
                    record = PdmlStringRecordQuiet.parse(self.data[pos:pos+10+4096])

                    # 验证长度合理性
                    if 0 < record.length < 4096 and pos + 10 + record.length <= len(self.data):
                        try:
                            value = record.value.decode('utf-8', errors='replace')
                            if value.strip():
                                self.strings[pos] = value.strip()
                                self.tagged_strings.append({
                                    'offset': pos,
                                    'type_code': record.type_code,
                                    'reserved': record.reserved,
                                    'value': value.strip(),
                                })
                        except:
                            pass
                except:
                    pass
            pos += 1

    def _extract_project_name(self) -> str:
        """提取项目名称（通常是第一个有效字符串）"""
        for record in self.tagged_strings[:10]:
            value = record['value']
            if len(value) > 1 and len(value) < 128:
                # 跳过 UUID 格式
                if len(value) == 32 and all(c in '0123456789ABCDEFabcdef' for c in value):
                    continue
                return value
        return "Unknown"

    def _find_geometry_records(self) -> List[Dict[str, Any]]:
        """查找所有几何体记录"""
        import struct
        records: List[Dict[str, Any]] = []
        seen_offsets: set = set()

        for record in self.tagged_strings:
            type_code = record['type_code']
            name = record['value']

            # 只处理几何体类型
            if type_code not in GEOMETRY_TYPE_CODES:
                continue

            # 跳过内部名称
            if name in INTERNAL_GEOMETRY_NAMES or name.startswith('Wall ('):
                continue

            offset = record['offset']

            # 提取层级信息
            level = 2
            if offset >= 4:
                level_bytes = struct.unpack('>I', self.data[offset-4:offset])[0]
                if 2 <= level_bytes <= 20:
                    level = level_bytes

            # 去重
            if offset in seen_offsets:
                continue
            seen_offsets.add(offset)

            records.append({
                'offset': offset,
                'type_code': type_code,
                'node_type': GEOMETRY_TYPE_CODES[type_code],
                'name': name,
                'level': level,
            })

        return sorted(records, key=lambda x: x['offset'])

    def _build_geometry(self) -> PdmlGeometryNode:
        """构建几何体层级结构"""
        # 创建根节点
        root = PdmlGeometryNode(
            node_type='assembly',
            name=self._extract_project_name(),
        )

        # 获取所有几何记录
        records = self._find_geometry_records()

        # 转换为节点
        nodes = []
        for rec in records:
            node = PdmlGeometryNode(
                node_type=rec['node_type'],
                name=rec['name'],
                level=rec['level'],
            )
            nodes.append(node)

        # 根据 profile 选择附加方式
        if self.profile == self.COMPACT_FORCED_FLOW_LAYOUT:
            root.children = self._attach_heatsink_children(nodes)
        else:
            root.children = self._attach_by_level(nodes)

        return root

    def _attach_heatsink_children(self, nodes: List[PdmlGeometryNode]) -> List[PdmlGeometryNode]:
        """Heatsink 项目的特殊层级处理"""
        # 查找 Heat Sink Geometry 装配体
        heat_sink = next(
            (n for n in nodes if n.name == 'Heat Sink Geometry' and n.node_type == 'assembly'),
            None
        )
        if heat_sink is None:
            return self._attach_by_level(nodes)

        top_level: List[PdmlGeometryNode] = []
        current_fin: Optional[PdmlGeometryNode] = None
        in_heat_sink_scope = False

        for node in nodes:
            if node is heat_sink:
                top_level.append(node)
                in_heat_sink_scope = True
                current_fin = None
                continue

            if not in_heat_sink_scope:
                top_level.append(node)
                continue

            if node.node_type == 'assembly' and node.name.startswith('Fin '):
                heat_sink.children.append(node)
                current_fin = node
                continue

            if node.node_type == 'cuboid':
                if node.name == 'Base':
                    heat_sink.children.append(node)
                    current_fin = None
                    continue
                if current_fin is not None:
                    current_fin.children.append(node)
                    continue

            # 其他节点放到顶层
            top_level.append(node)

        return top_level

    def _attach_by_level(self, nodes: List[PdmlGeometryNode]) -> List[PdmlGeometryNode]:
        """根据 level 信息构建层级关系

        PDML level 编码规则：
        - L3: 新子组的第一个元素（开始嵌套）
        - L2: 同组的后续兄弟元素
        """
        top_level: List[PdmlGeometryNode] = []
        parent_stack: List[PdmlGeometryNode] = []
        last_assembly: Optional[PdmlGeometryNode] = None

        CONTAINER_PATTERNS = [
            'Layers', 'Layer', 'Attach', 'Assembly', 'Power',
            'Electrical', 'Vias', 'Board', 'Parts', 'Components',
            'Domain', 'Solution', 'Model'
        ]

        def is_container(name: str) -> bool:
            return any(p.lower() in name.lower() for p in CONTAINER_PATTERNS)

        def get_current_parent() -> Optional[PdmlGeometryNode]:
            return parent_stack[-1] if parent_stack else None

        for node in nodes:
            level = node.level
            current_parent = get_current_parent()

            if node.node_type == 'assembly':
                if level == 3:
                    # L3 装配体：作为当前父级的子节点
                    if current_parent:
                        current_parent.children.append(node)
                    else:
                        top_level.append(node)
                    parent_stack.append(node)
                    last_assembly = node

                elif level == 2:
                    if is_container(node.name) and not parent_stack:
                        top_level.append(node)
                        parent_stack = [node]
                        last_assembly = node
                    elif last_assembly and parent_stack:
                        if len(parent_stack) > 1:
                            parent_stack.pop()
                        sibling_parent = get_current_parent()
                        if sibling_parent:
                            sibling_parent.children.append(node)
                        else:
                            top_level.append(node)
                        parent_stack.append(node)
                        last_assembly = node
                    else:
                        top_level.append(node)
                        parent_stack = [node]
                        last_assembly = node
            else:
                # 非装配体节点
                if current_parent:
                    current_parent.children.append(node)
                else:
                    top_level.append(node)

        return top_level


# ============================================================================
# 调试工具
# ============================================================================

def debug_string_records(filepath: str, limit: int = 20):
    """调试：显示字符串记录"""
    parser = PdmlConstructParser(filepath)
    parser._extract_all_strings()

    print(f"=== 字符串记录分析: {filepath} ===")
    print(f"总数: {len(parser.tagged_strings)}")
    print()
    print("序号 | offset | type_code | reserved | value")
    print("-" * 70)

    for i, rec in enumerate(parser.tagged_strings[:limit]):
        type_name = GEOMETRY_TYPE_CODES.get(rec['type_code'], '?')
        print(f"{i:3d}  | {rec['offset']:8d} | 0x{rec['type_code']:04x} | {rec['reserved']:8d} | {rec['value'][:40]}")


def debug_geometry_hierarchy(filepath: str, max_depth: int = 5):
    """调试：显示几何体层级"""
    parser = PdmlConstructParser(filepath)
    data = parser.parse()

    def print_tree(node: PdmlGeometryNode, depth: int = 0):
        if depth > max_depth:
            return
        indent = "  " * depth
        level = getattr(node, 'level', '?')
        print(f"{indent}[L{level}] {node.node_type}: {node.name[:30]} ({len(node.children)} children)")
        for child in node.children:
            print_tree(child, depth + 1)

    print(f"=== 几何体层级: {filepath} ===")
    print_tree(data.geometry)


# ============================================================================
# 主程序
# ============================================================================

if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("用法:")
        print("  python pdml_construct_parser.py <file.pdml>          # 显示层级")
        print("  python pdml_construct_parser.py <file.pdml> --strings # 显示字符串记录")
        sys.exit(1)

    filepath = sys.argv[1]

    if '--strings' in sys.argv:
        debug_string_records(filepath)
    else:
        debug_geometry_hierarchy(filepath)
