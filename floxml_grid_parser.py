#!/usr/bin/env python3
"""
FloTHERM FloXML 网格解析器
用于解析和修改 FloXML 文件中的网格设置

FloXML 结构:
- 根元素: xml_case
- 网格路径: xml_case.grid.system_grid
- 网格方向: x_grid, y_grid, z_grid
- 网格属性: min_size, grid_type, min_number, smoothing_value
"""

import xml.etree.ElementTree as ET
from xml.dom import minidom
import argparse
import os
import json
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field


@dataclass
class GridAxis:
    """单个方向的网格设置"""
    name: str  # x_grid, y_grid, z_grid
    min_size: float = 0.0
    grid_type: str = ""  # 网格类型
    min_number: int = 0  # 最小网格数
    smoothing_value: float = 0.0  # 平滑值
    element: Optional[ET.Element] = None

    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            "name": self.name,
            "min_size": self.min_size,
            "grid_type": self.grid_type,
            "min_number": self.min_number,
            "smoothing_value": self.smoothing_value
        }


@dataclass
class SystemGrid:
    """系统网格设置"""
    x_grid: Optional[GridAxis] = None
    y_grid: Optional[GridAxis] = None
    z_grid: Optional[GridAxis] = None
    element: Optional[ET.Element] = None

    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            "x_grid": self.x_grid.to_dict() if self.x_grid else None,
            "y_grid": self.y_grid.to_dict() if self.y_grid else None,
            "z_grid": self.z_grid.to_dict() if self.z_grid else None
        }

    def get_summary(self) -> str:
        """获取网格摘要信息"""
        lines = ["=== System Grid Summary ==="]

        for axis_name, axis in [("X", self.x_grid), ("Y", self.y_grid), ("Z", self.z_grid)]:
            if axis:
                lines.append(f"\n{axis_name}_Grid:")
                lines.append(f"  min_size: {axis.min_size}")
                lines.append(f"  grid_type: {axis.grid_type}")
                lines.append(f"  min_number: {axis.min_number}")
                lines.append(f"  smoothing_value: {axis.smoothing_value}")
            else:
                lines.append(f"\n{axis_name}_Grid: Not defined")

        return "\n".join(lines)


@dataclass
class GridInfo:
    """完整网格信息"""
    system_grid: Optional[SystemGrid] = None
    # 后续可扩展: localized_grids, grid_constraints 等

    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            "system_grid": self.system_grid.to_dict() if self.system_grid else None
        }


class FloXMLGridParser:
    """FloXML 网格解析器"""

    def __init__(self, filepath: str):
        self.filepath = filepath
        self.tree = ET.parse(filepath)
        self.root = self.tree.getroot()
        self.grid_info: Optional[GridInfo] = None

    def _find_element(self, *path) -> Optional[ET.Element]:
        """
        查找元素，支持多种路径格式
        例如: _find_element("grid", "system_grid")
        """
        current = self.root

        for tag in path:
            # 尝试直接查找
            found = current.find(tag)
            if found is not None:
                current = found
                continue

            # 尝试忽略命名空间查找
            for child in current:
                if self._strip_ns(child.tag) == tag:
                    current = child
                    break
            else:
                return None

        return current

    def _strip_ns(self, tag: str) -> str:
        """去除命名空间前缀"""
        if '}' in tag:
            return tag.split('}')[1]
        return tag

    def _get_text(self, element: ET.Element, attr: str, default: str = "") -> str:
        """获取元素属性或子元素文本"""
        # 先尝试属性
        if attr in element.attrib:
            return element.attrib[attr]

        # 再尝试子元素
        child = element.find(attr)
        if child is not None and child.text:
            return child.text.strip()

        return default

    def _get_float(self, element: ET.Element, attr: str, default: float = 0.0) -> float:
        """获取浮点值"""
        text = self._get_text(element, attr, str(default))
        try:
            return float(text)
        except ValueError:
            return default

    def _get_int(self, element: ET.Element, attr: str, default: int = 0) -> int:
        """获取整数值"""
        text = self._get_text(element, attr, str(default))
        try:
            return int(float(text))  # 处理 "10.0" 这种格式
        except ValueError:
            return default

    def parse_grid_axis(self, element: ET.Element, name: str) -> GridAxis:
        """解析单个方向的网格设置"""
        axis = GridAxis(
            name=name,
            element=element
        )

        # 解析属性
        axis.min_size = self._get_float(element, "min_size")
        axis.grid_type = self._get_text(element, "grid_type")
        axis.min_number = self._get_int(element, "min_number")
        axis.smoothing_value = self._get_float(element, "smoothing_value")

        return axis

    def parse_system_grid(self) -> SystemGrid:
        """解析系统网格设置"""
        system_grid = SystemGrid()

        # 查找 system_grid 元素
        sg_element = self._find_element("grid", "system_grid")
        if sg_element is None:
            print("Warning: system_grid element not found")
            return system_grid

        system_grid.element = sg_element

        # 解析三个方向的网格
        for axis_tag in ["x_grid", "y_grid", "z_grid"]:
            axis_element = sg_element.find(axis_tag)
            if axis_element is None:
                # 尝试忽略命名空间
                for child in sg_element:
                    if self._strip_ns(child.tag) == axis_tag:
                        axis_element = child
                        break

            if axis_element is not None:
                axis = self.parse_grid_axis(axis_element, axis_tag)
                setattr(system_grid, axis_tag, axis)

        return system_grid

    def parse(self) -> GridInfo:
        """解析完整的网格信息"""
        self.grid_info = GridInfo()
        self.grid_info.system_grid = self.parse_system_grid()
        return self.grid_info

    def print_grid_info(self):
        """打印网格信息"""
        if self.grid_info is None:
            self.parse()

        if self.grid_info and self.grid_info.system_grid:
            print(self.grid_info.system_grid.get_summary())
        else:
            print("No grid information found")

    def export_to_json(self, output_path: str):
        """导出网格信息到 JSON"""
        if self.grid_info is None:
            self.parse()

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(self.grid_info.to_dict(), f, indent=2, ensure_ascii=False)
        print(f"Grid info exported to: {output_path}")

    def set_grid_axis(self, axis_name: str, **kwargs):
        """
        设置指定方向的网格参数

        Args:
            axis_name: "x_grid", "y_grid", 或 "z_grid"
            **kwargs: min_size, grid_type, min_number, smoothing_value
        """
        if self.grid_info is None:
            self.parse()

        if not self.grid_info or not self.grid_info.system_grid:
            print("Error: No grid info available")
            return False

        axis: Optional[GridAxis] = getattr(self.grid_info.system_grid, axis_name, None)
        if axis is None or axis.element is None:
            print(f"Error: {axis_name} not found")
            return False

        # 更新属性
        for key, value in kwargs.items():
            if hasattr(axis, key):
                setattr(axis, key, value)

                # 更新 XML 元素
                if key in axis.element.attrib:
                    axis.element.attrib[key] = str(value)
                else:
                    # 查找或创建子元素
                    child = axis.element.find(key)
                    if child is not None:
                        child.text = str(value)
                    else:
                        ET.SubElement(axis.element, key).text = str(value)

                print(f"Set {axis_name}.{key} = {value}")
            else:
                print(f"Warning: Unknown attribute '{key}'")

        return True

    def set_system_grid(self,
                        x_min_size: Optional[float] = None,
                        y_min_size: Optional[float] = None,
                        z_min_size: Optional[float] = None,
                        x_min_number: Optional[int] = None,
                        y_min_number: Optional[int] = None,
                        z_min_number: Optional[int] = None,
                        smoothing: Optional[float] = None):
        """
        批量设置系统网格参数

        Args:
            x_min_size, y_min_size, z_min_size: 各方向最小网格尺寸
            x_min_number, y_min_number, z_min_number: 各方向最小网格数
            smoothing: 平滑值 (应用到所有方向)
        """
        if self.grid_info is None:
            self.parse()

        # X 方向
        x_kwargs = {}
        if x_min_size is not None:
            x_kwargs['min_size'] = x_min_size
        if x_min_number is not None:
            x_kwargs['min_number'] = x_min_number
        if smoothing is not None:
            x_kwargs['smoothing_value'] = smoothing
        if x_kwargs:
            self.set_grid_axis("x_grid", **x_kwargs)

        # Y 方向
        y_kwargs = {}
        if y_min_size is not None:
            y_kwargs['min_size'] = y_min_size
        if y_min_number is not None:
            y_kwargs['min_number'] = y_min_number
        if smoothing is not None:
            y_kwargs['smoothing_value'] = smoothing
        if y_kwargs:
            self.set_grid_axis("y_grid", **y_kwargs)

        # Z 方向
        z_kwargs = {}
        if z_min_size is not None:
            z_kwargs['min_size'] = z_min_size
        if z_min_number is not None:
            z_kwargs['min_number'] = z_min_number
        if smoothing is not None:
            z_kwargs['smoothing_value'] = smoothing
        if z_kwargs:
            self.set_grid_axis("z_grid", **z_kwargs)

    def save(self, output_path: str, pretty: bool = True):
        """
        保存修改后的 XML 文件

        Args:
            output_path: 输出文件路径
            pretty: 是否格式化输出
        """
        if pretty:
            # 使用 minidom 格式化
            rough_string = ET.tostring(self.root, encoding='unicode')
            reparsed = minidom.parseString(rough_string)
            pretty_xml = reparsed.toprettyxml(indent="  ")

            # 移除多余空行
            lines = [line for line in pretty_xml.split('\n') if line.strip()]
            pretty_xml = '\n'.join(lines)

            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(pretty_xml)
        else:
            self.tree.write(output_path, encoding='utf-8', xml_declaration=True)

        print(f"Saved to: {output_path}")


def main():
    parser = argparse.ArgumentParser(
        description="FloTHERM FloXML 网格解析和修改工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 查看网格信息
  python floxml_grid_parser.py model.floxml --info

  # 导出网格信息到 JSON
  python floxml_grid_parser.py model.floxml --export-json grid_info.json

  # 修改网格参数
  python floxml_grid_parser.py model.floxml -o modified.floxml \\
      --set-x-min-size 0.001 \\
      --set-y-min-size 0.001 \\
      --set-z-min-size 0.001 \\
      --set-smoothing 0.5
        """
    )

    parser.add_argument("floxml_file", help="FloXML 文件路径")
    parser.add_argument("-o", "--output", help="输出文件路径")
    parser.add_argument("--info", action="store_true", help="显示网格信息")
    parser.add_argument("--export-json", metavar="FILE", help="导出网格信息到 JSON")

    # 网格修改参数
    parser.add_argument("--set-x-min-size", type=float, help="设置 X 方向最小网格尺寸")
    parser.add_argument("--set-y-min-size", type=float, help="设置 Y 方向最小网格尺寸")
    parser.add_argument("--set-z-min-size", type=float, help="设置 Z 方向最小网格尺寸")
    parser.add_argument("--set-x-min-number", type=int, help="设置 X 方向最小网格数")
    parser.add_argument("--set-y-min-number", type=int, help="设置 Y 方向最小网格数")
    parser.add_argument("--set-z-min-number", type=int, help="设置 Z 方向最小网格数")
    parser.add_argument("--set-smoothing", type=float, help="设置平滑值 (所有方向)")

    args = parser.parse_args()

    # 检查文件是否存在
    if not os.path.exists(args.floxml_file):
        print(f"Error: File not found: {args.floxml_file}")
        return 1

    # 解析文件
    try:
        floxml = FloXMLGridParser(args.floxml_file)
        floxml.parse()
    except Exception as e:
        print(f"Error parsing file: {e}")
        return 1

    # 显示信息
    if args.info or not any([args.output, args.export_json]):
        floxml.print_grid_info()

    # 导出 JSON
    if args.export_json:
        floxml.export_to_json(args.export_json)

    # 修改参数
    has_modifications = any([
        args.set_x_min_size, args.set_y_min_size, args.set_z_min_size,
        args.set_x_min_number, args.set_y_min_number, args.set_z_min_number,
        args.set_smoothing
    ])

    if has_modifications:
        floxml.set_system_grid(
            x_min_size=args.set_x_min_size,
            y_min_size=args.set_y_min_size,
            z_min_size=args.set_z_min_size,
            x_min_number=args.set_x_min_number,
            y_min_number=args.set_y_min_number,
            z_min_number=args.set_z_min_number,
            smoothing=args.set_smoothing
        )

        # 保存文件
        if args.output:
            floxml.save(args.output)
        else:
            # 生成默认输出文件名
            base, ext = os.path.splitext(args.floxml_file)
            output_path = f"{base}_modified{ext}"
            floxml.save(output_path)

    return 0


if __name__ == "__main__":
    exit(main())
