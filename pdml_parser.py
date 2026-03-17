#!/usr/bin/env python3
"""
FloTHERM PDML 文件解析器

PDML (Project Data Markup Language) 是 FloTHERM 的原生模型格式，
包含完整的模型定义，包括几何、网格、材料、边界条件等。

使用方法:
    python pdml_parser.py model.pdml --info           # 显示基本信息
    python pdml_parser.py model.pdml --structure      # 显示完整结构
    python pdml_parser.py model.pdml --grid           # 显示网格信息
    python pdml_parser.py model.pdml --components     # 显示器件列表
    python pdml_parser.py model.pdml --export-csv     # 导出器件到 CSV
"""

import xml.etree.ElementTree as ET
import argparse
import json
import csv
import re
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field


@dataclass
class GridInfo:
    """网格信息"""
    grid_type: str = ""
    nx: int = 0
    ny: int = 0
    nz: int = 0
    total_cells: int = 0
    min_cell_size: float = 0.0
    max_cell_size: float = 0.0
    settings: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ComponentInfo:
    """器件信息"""
    name: str = ""
    component_type: str = ""
    x: float = 0.0
    y: float = 0.0
    z: float = 0.0
    width: float = 0.0
    height: float = 0.0
    depth: float = 0.0
    power: float = 0.0
    material: str = ""
    attributes: Dict[str, str] = field(default_factory=dict)


@dataclass
class BoundaryCondition:
    """边界条件"""
    name: str = ""
    bc_type: str = ""
    temperature: float = 25.0
    flow_rate: float = 0.0
    settings: Dict[str, Any] = field(default_factory=dict)


@dataclass
class MaterialInfo:
    """材料信息"""
    name: str = ""
    density: float = 0.0
    specific_heat: float = 0.0
    conductivity: float = 0.0
    conductivity_type: str = "isotropic"  # isotropic, orthotropic, anisotropic


class PDMLParser:
    """PDML 文件解析器"""

    # PDML 常见命名空间
    KNOWN_NAMESPACES = {
        'pdml': 'http://www.mentor.com/flotherm/pdml',
        'ft': 'http://www.mentor.com/flotherm',
        'xsi': 'http://www.w3.org/2001/XMLSchema-instance',
    }

    def __init__(self, filepath: str):
        self.filepath = filepath
        self.tree = ET.parse(filepath)
        self.root = self.tree.getroot()
        self.namespaces = self._detect_namespaces()

    def _detect_namespaces(self) -> Dict[str, str]:
        """自动检测命名空间"""
        namespaces = {}

        # 从根元素获取
        if hasattr(self.root, 'attrib'):
            for key, value in self.root.attrib.items():
                if key.startswith('xmlns'):
                    if ':' in key:
                        prefix = key.split(':')[1]
                    else:
                        prefix = ''
                    namespaces[prefix] = value

        # 检查子元素
        for elem in self.root.iter():
            if elem.tag.startswith('{'):
                ns = elem.tag.split('}')[0][1:]
                if ns not in namespaces.values():
                    namespaces[f'ns{len(namespaces)}'] = ns

        return namespaces

    def _strip_ns(self, tag: str) -> str:
        """去除命名空间前缀"""
        if '}' in tag:
            return tag.split('}')[1]
        return tag

    def _get_text(self, elem: ET.Element, *tags) -> Optional[str]:
        """获取子元素的文本内容（支持多个可能的标签名）"""
        for tag in tags:
            # 直接查找
            child = elem.find(tag)
            if child is not None and child.text:
                return child.text.strip()

            # 忽略命名空间查找
            for child in elem:
                if self._strip_ns(child.tag).lower() == tag.lower():
                    if child.text:
                        return child.text.strip()

        return None

    def _get_attr(self, elem: ET.Element, *attrs) -> Optional[str]:
        """获取元素属性（支持多个可能的属性名）"""
        for attr in attrs:
            value = elem.get(attr) or elem.get(attr.lower()) or elem.get(attr.upper())
            if value:
                return value
        return None

    def _get_float(self, elem: ET.Element, *tags) -> float:
        """获取浮点数值"""
        text = self._get_text(elem, *tags)
        if text:
            try:
                return float(text)
            except ValueError:
                pass
        return 0.0

    def _get_int(self, elem: ET.Element, *tags) -> int:
        """获取整数值"""
        text = self._get_text(elem, *tags)
        if text:
            try:
                return int(float(text))
            except ValueError:
                pass
        return 0

    def get_grid_info(self) -> GridInfo:
        """获取网格信息"""
        grid = GridInfo()

        # 常见的网格相关标签
        grid_tags = [
            'AssemblyGrid', 'Grid', 'Mesh', 'MeshSettings',
            'GridSettings', 'LocalisedGrid', 'GridRegion'
        ]

        for elem in self.root.iter():
            tag = self._strip_ns(elem.tag)

            if tag in grid_tags or 'grid' in tag.lower() or 'mesh' in tag.lower():
                grid.grid_type = tag

                # 解析网格尺寸
                grid.nx = self._get_int(elem, 'Nx', 'nx', 'NumCellsX', 'CellsX', 'XCells')
                grid.ny = self._get_int(elem, 'Ny', 'ny', 'NumCellsY', 'CellsY', 'YCells')
                grid.nz = self._get_int(elem, 'Nz', 'nz', 'NumCellsZ', 'CellsZ', 'ZCells')

                # 如果属性中有
                if grid.nx == 0:
                    grid.nx = int(elem.get('nx', elem.get('Nx', 0)) or 0)
                if grid.ny == 0:
                    grid.ny = int(elem.get('ny', elem.get('Ny', 0)) or 0)
                if grid.nz == 0:
                    grid.nz = int(elem.get('nz', elem.get('Nz', 0)) or 0)

                grid.total_cells = grid.nx * grid.ny * grid.nz

                # 网格设置
                for child in elem:
                    child_tag = self._strip_ns(child.tag).lower()
                    if child.text:
                        try:
                            grid.settings[child_tag] = float(child.text)
                        except ValueError:
                            grid.settings[child_tag] = child.text.strip()

                break  # 找到第一个网格定义就返回

        return grid

    def get_components(self) -> List[ComponentInfo]:
        """获取所有器件信息"""
        components = []

        # 常见的器件标签
        component_tags = [
            'Component', 'Block', 'Prism', 'Cuboid', 'Enclosure',
            'Heatsink', 'Fan', 'PCB', 'Chip', 'ThermalModel'
        ]

        for elem in self.root.iter():
            tag = self._strip_ns(elem.tag)

            if tag in component_tags or 'component' in tag.lower():
                comp = ComponentInfo()
                comp.component_type = tag
                comp.name = self._get_attr(elem, 'name', 'Name', 'id', 'Id') or f"Component_{len(components)}"

                # 位置
                for child in elem:
                    child_tag = self._strip_ns(child.tag).lower()

                    if 'position' in child_tag or 'location' in child_tag or 'origin' in child_tag:
                        comp.x = float(child.get('x', child.get('X', 0)) or 0)
                        comp.y = float(child.get('y', child.get('Y', 0)) or 0)
                        comp.z = float(child.get('z', child.get('Z', 0)) or 0)

                    elif 'size' in child_tag or 'dimension' in child_tag:
                        comp.width = float(child.get('width', child.get('Width',
                                     child.get('dx', child.get('Dx', 0))) or 0) or 0)
                        comp.height = float(child.get('height', child.get('Height',
                                      child.get('dy', child.get('Dy', 0))) or 0) or 0)
                        comp.depth = float(child.get('depth', child.get('Depth',
                                     child.get('dz', child.get('Dz', 0))) or 0) or 0)

                    elif 'power' in child_tag or 'heat' in child_tag:
                        if child.text:
                            try:
                                comp.power = float(child.text.strip())
                            except ValueError:
                                pass

                    elif 'material' in child_tag:
                        comp.material = child.get('name', child.get('ref',
                                       child.text or '') or '') or ''
                        if child.text:
                            comp.material = child.text.strip()

                # 收集所有属性
                comp.attributes = dict(elem.attrib)

                components.append(comp)

        return components

    def get_boundary_conditions(self) -> List[BoundaryCondition]:
        """获取边界条件"""
        bcs = []

        bc_tags = ['BoundaryCondition', 'Boundary', 'Ambient', 'Inlet', 'Outlet', 'Wall']

        for elem in self.root.iter():
            tag = self._strip_ns(elem.tag)

            if tag in bc_tags or 'boundary' in tag.lower():
                bc = BoundaryCondition()
                bc.bc_type = tag
                bc.name = self._get_attr(elem, 'name', 'Name') or f"BC_{len(bcs)}"

                # 温度
                for child in elem:
                    child_tag = self._strip_ns(child.tag).lower()
                    if 'temp' in child_tag:
                        if child.text:
                            try:
                                bc.temperature = float(child.text.strip())
                            except ValueError:
                                pass
                    elif 'flow' in child_tag or 'velocity' in child_tag:
                        if child.text:
                            try:
                                bc.flow_rate = float(child.text.strip())
                            except ValueError:
                                pass

                bcs.append(bc)

        return bcs

    def get_materials(self) -> List[MaterialInfo]:
        """获取材料定义"""
        materials = []

        for elem in self.root.iter():
            tag = self._strip_ns(elem.tag)

            if 'material' in tag.lower():
                mat = MaterialInfo()
                mat.name = self._get_attr(elem, 'name', 'Name', 'id') or f"Material_{len(materials)}"

                for child in elem:
                    child_tag = self._strip_ns(child.tag).lower()

                    if 'density' in child_tag and child.text:
                        try:
                            mat.density = float(child.text.strip())
                        except ValueError:
                            pass
                    elif 'heat' in child_tag or 'specific' in child_tag:
                        if child.text:
                            try:
                                mat.specific_heat = float(child.text.strip())
                            except ValueError:
                                pass
                    elif 'conduct' in child_tag:
                        if child.text:
                            try:
                                mat.conductivity = float(child.text.strip())
                            except ValueError:
                                pass
                        # 检查类型
                        mat.conductivity_type = child.get('type', 'isotropic')

                materials.append(mat)

        return materials

    def get_structure(self, max_depth: int = 5) -> Dict:
        """获取文件结构"""
        def parse_elem(elem, depth=0):
            if depth > max_depth:
                return {"...": "truncated"}

            result = {
                "tag": self._strip_ns(elem.tag),
                "attrs": dict(list(elem.attrib.items())[:5]),
                "children_count": len(list(elem))
            }

            if len(elem) > 0 and depth < max_depth:
                result["children"] = []
                for child in elem:
                    result["children"].append(parse_elem(child, depth + 1))

            return result

        return parse_elem(self.root)

    def print_structure(self, max_depth: int = 4):
        """打印文件结构"""
        print("\n" + "="*60)
        print("PDML 文件结构")
        print("="*60)
        print(f"文件: {self.filepath}")
        print(f"根元素: {self._strip_ns(self.root.tag)}")
        print(f"命名空间: {self.namespaces}")
        print()

        def print_elem(elem, depth=0):
            if depth > max_depth:
                return

            indent = "  " * depth
            tag = self._strip_ns(elem.tag)
            attrs = ' '.join([f'{k}="{v}"' for k, v in list(elem.attrib.items())[:3]])
            if len(elem.attrib) > 3:
                attrs += " ..."

            # 显示文本内容预览
            text_preview = ""
            if elem.text and elem.text.strip():
                text_preview = f" = {elem.text[:30]}{'...' if len(elem.text) > 30 else ''}"

            child_count = len(list(elem))
            children_str = f" [{child_count} children]" if child_count > 0 else ""

            print(f"{indent}<{tag} {attrs}>{text_preview}{children_str}")

            for child in elem:
                print_elem(child, depth + 1)

        print_elem(self.root)
        print("="*60)

    def print_grid_info(self):
        """打印网格信息"""
        grid = self.get_grid_info()

        print("\n" + "="*60)
        print("网格信息")
        print("="*60)

        if grid.grid_type:
            print(f"网格类型: {grid.grid_type}")
            print(f"网格尺寸: {grid.nx} x {grid.ny} x {grid.nz}")
            print(f"总网格数: {grid.total_cells:,}")

            if grid.settings:
                print("\n网格设置:")
                for key, value in grid.settings.items():
                    print(f"  {key}: {value}")
        else:
            print("未找到网格信息")

        print("="*60)

    def print_components(self):
        """打印器件列表"""
        components = self.get_components()

        print("\n" + "="*60)
        print(f"器件列表 (共 {len(components)} 个)")
        print("="*60)

        for comp in components:
            print(f"\n[{comp.component_type}] {comp.name}")
            if comp.x or comp.y or comp.z:
                print(f"  位置: ({comp.x}, {comp.y}, {comp.z})")
            if comp.width or comp.height or comp.depth:
                print(f"  尺寸: {comp.width} x {comp.height} x {comp.depth}")
            if comp.power:
                print(f"  功耗: {comp.power} W")
            if comp.material:
                print(f"  材料: {comp.material}")

        print("\n" + "="*60)

    def print_boundary_conditions(self):
        """打印边界条件"""
        bcs = self.get_boundary_conditions()

        print("\n" + "="*60)
        print(f"边界条件 (共 {len(bcs)} 个)")
        print("="*60)

        for bc in bcs:
            print(f"\n[{bc.bc_type}] {bc.name}")
            if bc.temperature != 25.0:
                print(f"  温度: {bc.temperature} °C")
            if bc.flow_rate:
                print(f"  流速: {bc.flow_rate}")

        print("\n" + "="*60)

    def print_summary(self):
        """打印摘要信息"""
        components = self.get_components()
        grid = self.get_grid_info()
        bcs = self.get_boundary_conditions()
        materials = self.get_materials()

        print("\n" + "="*60)
        print("PDML 文件摘要")
        print("="*60)
        print(f"文件: {self.filepath}")
        print(f"根元素: {self._strip_ns(self.root.tag)}")
        print()
        print(f"器件数量: {len(components)}")
        print(f"边界条件: {len(bcs)}")
        print(f"材料定义: {len(materials)}")

        if grid.grid_type:
            print(f"网格: {grid.nx} x {grid.ny} x {grid.nz} = {grid.total_cells:,} cells")

        # 功耗统计
        total_power = sum(c.power for c in components)
        if total_power > 0:
            print(f"总功耗: {total_power:.2f} W")

        print("="*60)

    def export_components_csv(self, output_path: str):
        """导出器件到 CSV"""
        components = self.get_components()

        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['Name', 'Type', 'X', 'Y', 'Z', 'Width', 'Height', 'Depth', 'Power(W)', 'Material'])
            for c in components:
                writer.writerow([c.name, c.component_type, c.x, c.y, c.z,
                               c.width, c.height, c.depth, c.power, c.material])

        print(f"已导出 {len(components)} 个器件到 {output_path}")

    def export_structure_json(self, output_path: str):
        """导出结构到 JSON"""
        structure = {
            "file": self.filepath,
            "root": self._strip_ns(self.root.tag),
            "namespaces": self.namespaces,
            "structure": self.get_structure(),
            "summary": {
                "components": len(self.get_components()),
                "boundary_conditions": len(self.get_boundary_conditions()),
                "materials": len(self.get_materials()),
            }
        }

        # 添加网格信息
        grid = self.get_grid_info()
        if grid.grid_type:
            structure["grid"] = {
                "type": grid.grid_type,
                "nx": grid.nx,
                "ny": grid.ny,
                "nz": grid.nz,
                "total_cells": grid.total_cells,
                "settings": grid.settings
            }

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(structure, f, indent=2, ensure_ascii=False)

        print(f"已导出结构到 {output_path}")

    def find_element_by_name(self, name: str) -> Optional[ET.Element]:
        """
        按名称查找元素

        支持两种格式:
        1. 属性格式: <Component name="CPU">
        2. 子元素格式: <Component><name>CPU</name></Component>
        """
        for elem in self.root.iter():
            # 方式1: 检查 name 属性
            if elem.get('name') == name or elem.get('Name') == name:
                return elem

            # 方式2: 检查 <name> 子元素
            for child in elem:
                tag = self._strip_ns(child.tag).lower()
                if tag == 'name' and child.text and child.text.strip() == name:
                    return elem

        return None

    def set_value_by_path(self, path: str, value: Any) -> bool:
        """
        通过路径设置值，支持类似 XPath 的定位方式

        路径格式:
            - "ElementName"                      → 通过 name 属性/子元素定位
            - "ElementName.child"                → 子元素的文本值
            - "tag[name=xxx].child"              → 通过路径 + name 筛选
            - "tag@attr"                         → 元素的属性
            - "[Material:1]"                     → 名称包含特殊字符

        示例:
            - "CPU"                              → 设置功耗（自动）
            - "CPU.powerDissipation"             → 设置功耗
            - "materials.material[name=Copper].density"  → XPath 风格
            - "Heatsink.Material.density"        → 简化路径
            - "PCB.Size@width"                   → 设置属性

        Args:
            path: 路径字符串
            value: 要设置的值

        Returns:
            是否成功
        """
        # 解析属性
        attr_name = None
        if '@' in path:
            path, attr_name = path.rsplit('@', 1)

        # 解析路径段
        segments = self._parse_path(path)
        if not segments:
            print(f"错误: 路径为空")
            return False

        # 遍历路径段，定位元素
        elem = self.root
        root_tag = self._strip_ns(self.root.tag)

        for i, seg in enumerate(segments):
            tag_name = seg['tag']
            filter_name = seg['filter']

            # 如果第一段是根元素名称，跳过它
            if i == 0 and tag_name.lower() == root_tag.lower():
                continue

            # 判断是简单的名称匹配还是路径遍历
            is_simple_name = (
                i == 0 and
                filter_name is None and
                '.' not in path.replace('/', '.') and
                '[' not in path.replace('[name=', '')
            )

            # 检查是否是 [xxx] 格式的特殊名称
            is_bracketed_name = path.startswith('[') and ']' in path

            if i == 0 and filter_name is None and (is_simple_name or is_bracketed_name):
                # 简单格式或方括号格式：通过 name 属性/子元素定位
                found = self.find_element_by_name(tag_name)
                if found is None:
                    print(f"    ⚠ 未找到元素: {tag_name}")
                    return False
                elem = found
            else:
                # 路径格式：通过标签名查找子元素
                found = self._find_child_by_tag_with_filter(elem, tag_name, filter_name)
                if found is None:
                    if filter_name:
                        print(f"    ⚠ 未找到子元素: {tag_name}[name={filter_name}]")
                    else:
                        print(f"    ⚠ 未找到子元素: {tag_name}")
                    return False
                elem = found

        # 设置值
        if attr_name:
            elem.set(attr_name, str(value))
            print(f"    ✓ 设置属性: {path}@{attr_name} = {value}")
        else:
            elem.text = str(value)
            print(f"    ✓ 设置值: {path} = {value}")

        return True

    def _parse_path(self, path: str) -> List[Dict]:
        """
        解析路径字符串

        支持格式:
        - "CPU" → [{tag: "CPU", filter: None}]
        - "CPU.child" → [{tag: "CPU", filter: None}, {tag: "child", filter: None}]
        - "[Material:1]" → [{tag: "Material:1", filter: None}]
        - "materials.material[name=Copper]" → [{tag: "materials", filter: None}, {tag: "material", filter: "Copper"}]
        """
        segments = []

        # 处理 [xxx] 开头的特殊名称
        if path.startswith('[') and ']' in path:
            close_bracket = path.index(']')
            name = path[1:close_bracket]
            segments.append({'tag': name, 'filter': None})
            remaining = path[close_bracket + 1:]
            if remaining.startswith('.'):
                remaining = remaining[1:]
            if remaining:
                segments.extend(self._parse_path_segments(remaining))
            return segments

        # 普通路径解析
        return self._parse_path_segments(path)

    def _parse_path_segments(self, path: str) -> List[Dict]:
        """解析路径段，支持 tag[name=xxx] 格式"""
        segments = []

        # 统一使用 . 作为分隔符
        path = path.replace('/', '.')

        # 使用正则表达式解析
        # 匹配: tag 或 tag[name=xxx]
        pattern = r'(\w+)(?:\[name=([^\]]+)\])?'

        parts = path.split('.')
        for part in parts:
            part = part.strip()
            if not part:
                continue

            match = re.match(pattern, part)
            if match:
                tag = match.group(1)
                filter_name = match.group(2)
                segments.append({'tag': tag, 'filter': filter_name})
            else:
                segments.append({'tag': part, 'filter': None})

        return segments

    def _find_child_by_tag_with_filter(self, parent: ET.Element, tag: str, filter_name: str = None) -> Optional[ET.Element]:
        """
        通过标签名和可选的 name 筛选查找子元素

        Args:
            parent: 父元素
            tag: 标签名（忽略命名空间）
            filter_name: 可选的 name 属性/子元素筛选值

        Returns:
            找到的元素或 None
        """
        tag_lower = tag.lower()

        for child in parent:
            child_tag = self._strip_ns(child.tag).lower()

            # 标签名匹配（支持单数/复数形式）
            if child_tag != tag_lower and child_tag.rstrip('s') != tag_lower.rstrip('s'):
                continue

            # 如果没有筛选条件，返回第一个匹配的
            if filter_name is None:
                return child

            # 检查 name 属性
            if child.get('name') == filter_name or child.get('Name') == filter_name:
                return child

            # 检查 <name> 子元素
            for subchild in child:
                sub_tag = self._strip_ns(subchild.tag).lower()
                if sub_tag == 'name' and subchild.text and subchild.text.strip() == filter_name:
                    return child

        return None

    def save(self, output_path: str = None):
        """保存修改后的文件"""
        if output_path is None:
            output_path = self.filepath

        # 美化 XML 输出
        self._indent(self.root)
        self.tree.write(output_path, encoding='utf-8', xml_declaration=True)
        print(f"已保存到: {output_path}")

    def _indent(self, elem, level=0):
        """添加缩进，美化输出"""
        indent = "\n" + "  " * level
        if len(elem):
            if not elem.text or not elem.text.strip():
                elem.text = indent + "  "
            if not elem.tail or not elem.tail.strip():
                elem.tail = indent
            for child in elem:
                self._indent(child, level + 1)
            if not child.tail or not child.tail.strip():
                child.tail = indent
        else:
            if level and (not elem.tail or not elem.tail.strip()):
                elem.tail = indent


def main():
    parser = argparse.ArgumentParser(
        description='FloTHERM PDML 文件解析器',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
示例:
  python pdml_parser.py model.pdml --info           # 显示摘要
  python pdml_parser.py model.pdml --structure      # 显示结构
  python pdml_parser.py model.pdml --grid           # 显示网格
  python pdml_parser.py model.pdml --components     # 显示器件
  python pdml_parser.py model.pdml --export-csv     # 导出 CSV
        '''
    )

    parser.add_argument('input', help='PDML 文件路径')
    parser.add_argument('--info', '-i', action='store_true', help='显示摘要信息')
    parser.add_argument('--structure', '-s', action='store_true', help='显示文件结构')
    parser.add_argument('--grid', '-g', action='store_true', help='显示网格信息')
    parser.add_argument('--components', '-c', action='store_true', help='显示器件列表')
    parser.add_argument('--boundaries', '-b', action='store_true', help='显示边界条件')
    parser.add_argument('--export-csv', metavar='FILE', help='导出器件到 CSV')
    parser.add_argument('--export-json', metavar='FILE', help='导出结构到 JSON')
    parser.add_argument('--depth', type=int, default=4, help='结构显示深度')

    args = parser.parse_args()

    try:
        pdml = PDMLParser(args.input)

        # 默认显示摘要
        if not any([args.structure, args.grid, args.components, args.boundaries,
                    args.export_csv, args.export_json]):
            args.info = True

        if args.info:
            pdml.print_summary()

        if args.structure:
            pdml.print_structure(args.depth)

        if args.grid:
            pdml.print_grid_info()

        if args.components:
            pdml.print_components()

        if args.boundaries:
            pdml.print_boundary_conditions()

        if args.export_csv:
            pdml.export_components_csv(args.export_csv)

        if args.export_json:
            pdml.export_structure_json(args.export_json)

    except Exception as e:
        print(f"[ERROR] {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0


if __name__ == '__main__':
    exit(main())
