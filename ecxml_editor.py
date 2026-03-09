#!/usr/bin/env python3
"""
FloTHERM ECXML 参数修改工具
基于 JEDEC JEP181 标准，兼容 FloTHERM 2020.2
用于批量修改 ecxml 文件中的仿真参数
"""

import xml.etree.ElementTree as ET
from xml.dom import minidom
import argparse
import os
import re
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
import json
import csv


@dataclass
class ComponentInfo:
    """器件信息"""
    name: str
    power: float = 0.0
    x: float = 0.0
    y: float = 0.0
    z: float = 0.0
    width: float = 0.0
    height: float = 0.0
    depth: float = 0.0
    material: str = ""
    element: Optional[ET.Element] = None


@dataclass
class BoundaryCondition:
    """边界条件"""
    name: str
    bc_type: str  # "ambient", "inlet", "outlet", "wall", etc.
    temperature: float = 25.0
    flow_rate: float = 0.0
    element: Optional[ET.Element] = None


class ECXMLParser:
    """ECXML 文件解析器 (JEDEC JEP181 兼容)"""

    # JEDEC JEP181 常见命名空间
    KNOWN_NAMESPACES = {
        'ecxml': 'http://www.jedec.org/ecxml',
        'ft': 'http://www.mentor.com/flotherm/ecxml',
        'xsi': 'http://www.w3.org/2001/XMLSchema-instance',
    }

    def __init__(self, filepath: str):
        self.filepath = filepath
        self.tree = ET.parse(filepath)
        self.root = self.tree.getroot()
        self.namespaces = self._detect_namespaces()

    def _detect_namespaces(self) -> Dict[str, str]:
        """自动检测 XML 命名空间"""
        namespaces = {}

        # 从根元素获取命名空间
        if hasattr(self.root, 'attrib'):
            for key, value in self.root.attrib.items():
                if key.startswith('xmlns'):
                    if ':' in key:
                        prefix = key.split(':')[1]
                    else:
                        prefix = ''
                    namespaces[prefix] = value

        # 检查子元素的命名空间
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

    def get_components(self) -> List[ComponentInfo]:
        """获取所有器件信息"""
        components = []

        # 根据实际 ecxml 结构调整路径
        for elem in self.root.iter():
            if 'Component' in elem.tag or 'component' in elem.tag.lower():
                info = self._parse_component(elem)
                if info:
                    components.append(info)

        return components

    def _parse_component(self, elem) -> Optional[ComponentInfo]:
        """解析单个器件"""
        try:
            name = elem.get('name', elem.get('Name', 'Unknown'))

            # 查找功耗 (powerDissipation 是 JEDEC JEP181 标准字段)
            power = 0.0
            power_elem = (elem.find('.//powerDissipation') or
                          elem.find('.//PowerDissipation') or
                          elem.find('.//Power') or
                          elem.find('.//power'))
            if power_elem is not None and power_elem.text:
                power = float(power_elem.text)

            # 查找位置和尺寸
            x = y = z = width = height = depth = 0.0

            # 根据实际结构调整选择器
            for child in elem:
                if 'Position' in child.tag or 'position' in child.tag.lower():
                    x = float(child.get('x', child.get('X', 0)))
                    y = float(child.get('y', child.get('Y', 0)))
                    z = float(child.get('z', child.get('Z', 0)))
                elif 'Size' in child.tag or 'size' in child.tag.lower():
                    width = float(child.get('width', child.get('Width', 0)))
                    height = float(child.get('height', child.get('Height', 0)))
                    depth = float(child.get('depth', child.get('Depth', 0)))

            return ComponentInfo(name, power, x, y, z, width, height, depth)
        except Exception as e:
            print(f"解析器件失败: {e}")
            return None

    def find_element_by_name(self, name: str) -> Optional[ET.Element]:
        """按名称查找元素"""
        for elem in self.root.iter():
            if elem.get('name') == name or elem.get('Name') == name:
                return elem
        return None

    def find_elements_by_pattern(self, pattern: str) -> List[ET.Element]:
        """按正则表达式查找元素"""
        regex = re.compile(pattern, re.IGNORECASE)
        results = []
        for elem in self.root.iter():
            name = elem.get('name', elem.get('Name', ''))
            if regex.search(name):
                results.append(elem)
        return results

    def set_power(self, component_name: str, power: float) -> bool:
        """设置器件功耗"""
        elem = self.find_element_by_name(component_name)
        if elem is None:
            print(f"未找到器件: {component_name}")
            return False

        # 查找并设置功耗元素 (powerDissipation 是 JEDEC JEP181 标准字段)
        # 需要处理命名空间，使用 _strip_ns 匹配
        power_elem = None
        for child in elem.iter():
            tag_name = self._strip_ns(child.tag).lower()
            if tag_name in ['powerdissipation', 'power', 'power_dissipation']:
                power_elem = child
                break

        if power_elem is not None:
            power_elem.text = str(power)
            return True

        # 如果没有找到，可能需要创建（根据实际结构）
        print(f"器件 {component_name} 未找到功耗字段")
        return False

    def set_boundary_condition(self, bc_name: str, temperature: float = None,
                                flow_rate: float = None) -> bool:
        """设置边界条件"""
        elem = self.find_element_by_name(bc_name)
        if elem is None:
            print(f"未找到边界条件: {bc_name}")
            return False

        if temperature is not None:
            # 处理命名空间
            temp_elem = None
            for child in elem.iter():
                tag_name = self._strip_ns(child.tag).lower()
                if tag_name in ['temperature', 'temp']:
                    temp_elem = child
                    break
            if temp_elem is not None:
                temp_elem.text = str(temperature)

        if flow_rate is not None:
            # 处理命名空间
            flow_elem = None
            for child in elem.iter():
                tag_name = self._strip_ns(child.tag).lower()
                if tag_name in ['flowrate', 'flow_rate', 'flow']:
                    flow_elem = child
                    break
            if flow_elem is not None:
                flow_elem.text = str(flow_rate)

        return True

    def batch_set_power(self, power_map: Dict[str, float]) -> int:
        """批量设置功耗"""
        success_count = 0
        for name, power in power_map.items():
            if self.set_power(name, power):
                success_count += 1
        return success_count

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

    def print_structure(self, max_depth: int = 4):
        """打印 XML 结构（用于调试）"""
        print("\n=== ECXML 结构 ===")
        print(f"命名空间: {self.namespaces}")
        print(f"根元素: {self._strip_ns(self.root.tag)}")
        print()

        def print_elem(elem, depth=0):
            if depth > max_depth:
                return
            indent = "  " * depth
            tag_name = self._strip_ns(elem.tag)
            attrs = ' '.join([f'{k}="{v}"' for k, v in list(elem.attrib.items())[:3]])
            if len(elem.attrib) > 3:
                attrs += " ..."
            text_preview = f" = {elem.text[:30]}..." if elem.text and elem.text.strip() else ""
            print(f"{indent}<{tag_name} {attrs}>{text_preview}")
            for child in elem:
                print_elem(child, depth + 1)

        print_elem(self.root)

    def analyze_structure(self) -> Dict[str, Any]:
        """分析 ECXML 文件结构，返回统计信息"""
        stats = {
            "root_tag": self._strip_ns(self.root.tag),
            "namespaces": self.namespaces,
            "element_types": {},
            "attributes": {},
            "power_related": [],
            "temperature_related": [],
        }

        for elem in self.root.iter():
            tag = self._strip_ns(elem.tag)

            # 统计元素类型
            stats["element_types"][tag] = stats["element_types"].get(tag, 0) + 1

            # 收集属性名
            for attr in elem.attrib:
                stats["attributes"][attr] = stats["attributes"].get(attr, 0) + 1

            # 查找功耗相关 (powerDissipation 是 JEDEC JEP181 标准字段)
            if any(kw in tag.lower() for kw in ['power', 'dissipation']):
                stats["power_related"].append({
                    "tag": tag,
                    "name": elem.get('name', elem.get('Name', '')),
                    "text": elem.text[:50] if elem.text and elem.text.strip() else None,
                })

            # 查找温度相关
            if any(kw in tag.lower() for kw in ['temp', 'ambient']):
                stats["temperature_related"].append({
                    "tag": tag,
                    "name": elem.get('name', elem.get('Name', '')),
                    "text": elem.text[:50] if elem.text and elem.text.strip() else None,
                })

        return stats

    def print_analysis(self):
        """打印结构分析结果"""
        stats = self.analyze_structure()

        print("\n" + "="*60)
        print("ECXML 文件结构分析")
        print("="*60)

        print(f"\n根元素: {stats['root_tag']}")
        print(f"\n命名空间:")
        for prefix, ns in stats['namespaces'].items():
            print(f"  {prefix or '(默认)'}: {ns}")

        print(f"\n元素类型统计 (共 {len(stats['element_types'])} 种):")
        for tag, count in sorted(stats['element_types'].items(), key=lambda x: -x[1])[:15]:
            print(f"  {tag}: {count}")

        print(f"\n常见属性:")
        for attr, count in sorted(stats['attributes'].items(), key=lambda x: -x[1])[:10]:
            print(f"  {attr}: {count}")

        if stats['power_related']:
            print(f"\n功耗相关元素 ({len(stats['power_related'])} 个):")
            for item in stats['power_related'][:10]:
                print(f"  <{item['tag']}> name=\"{item['name']}\" text=\"{item['text']}\"")

        if stats['temperature_related']:
            print(f"\n温度相关元素 ({len(stats['temperature_related'])} 个):")
            for item in stats['temperature_related'][:10]:
                print(f"  <{item['tag']}> name=\"{item['name']}\" text=\"{item['text']}\"")

        print("\n" + "="*60)

    def export_components_csv(self, output_path: str):
        """导出器件信息到 CSV"""
        components = self.get_components()
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['Name', 'Power(W)', 'X', 'Y', 'Z', 'Width', 'Height', 'Depth'])
            for c in components:
                writer.writerow([c.name, c.power, c.x, c.y, c.z, c.width, c.height, c.depth])
        print(f"已导出 {len(components)} 个器件到 {output_path}")


def load_power_config(config_path: str) -> Dict[str, float]:
    """从配置文件加载功耗设置"""
    power_map = {}

    if config_path.endswith('.json'):
        with open(config_path, 'r', encoding='utf-8') as f:
            power_map = json.load(f)
    elif config_path.endswith('.csv'):
        with open(config_path, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            next(reader)  # 跳过表头
            for row in reader:
                if len(row) >= 2:
                    power_map[row[0]] = float(row[1])

    return power_map


def main():
    parser = argparse.ArgumentParser(description='FloTHERM ECXML 参数修改工具 (FloTHERM 2020.2 兼容)')
    parser.add_argument('input', help='输入 ECXML 文件路径')
    parser.add_argument('-o', '--output', help='输出文件路径（默认覆盖原文件）')

    # 分析命令
    parser.add_argument('--info', action='store_true', help='显示文件结构信息')
    parser.add_argument('--analyze', action='store_true', help='详细分析文件结构')
    parser.add_argument('--export-csv', help='导出器件信息到 CSV 文件')

    # 修改命令
    parser.add_argument('--set-power', nargs=2, metavar=('NAME', 'POWER'),
                       help='设置单个器件功耗')
    parser.add_argument('--power-config', help='从 JSON/CSV 文件批量加载功耗设置')
    parser.add_argument('--set-temp', nargs=2, metavar=('NAME', 'TEMP'),
                       help='设置边界条件温度')
    parser.add_argument('--pattern', help='使用正则表达式匹配器件名称')

    args = parser.parse_args()

    # 创建解析器
    ecxml = ECXMLParser(args.input)

    # 详细分析
    if args.analyze:
        ecxml.print_analysis()
        return

    # 显示结构信息
    if args.info:
        ecxml.print_structure()
        components = ecxml.get_components()
        print(f"\n找到 {len(components)} 个器件:")
        for c in components:
            print(f"  - {c.name}: {c.power}W")
        return

    # 导出 CSV
    if args.export_csv:
        ecxml.export_components_csv(args.export_csv)
        return

    # 设置单个器件功耗
    if args.set_power:
        name, power = args.set_power
        power = float(power)
        ecxml.set_power(name, power)
        print(f"已设置 {name} 功耗为 {power}W")

    # 设置边界条件温度
    if args.set_temp:
        name, temp = args.set_temp
        temp = float(temp)
        ecxml.set_boundary_condition(name, temperature=temp)
        print(f"已设置 {name} 温度为 {temp}°C")

    # 批量设置功耗
    if args.power_config:
        power_map = load_power_config(args.power_config)
        count = ecxml.batch_set_power(power_map)
        print(f"已批量更新 {count}/{len(power_map)} 个器件功耗")

    # 保存文件
    if args.set_power or args.power_config or args.set_temp:
        ecxml.save(args.output)


if __name__ == '__main__':
    main()
