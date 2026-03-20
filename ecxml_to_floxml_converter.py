#!/usr/bin/env python3
"""
ECXML to FloXML Converter

将 JEDEC JEP181 ECXML 器件热模型转换为 FloTHERM FloXML 项目格式。

ECXML 是器件级热模型交换格式，缺少:
  - 网格设置 (grid)
  - 求解器配置 (solve)
  - 模型设置 (model)
  - 求解域 (solution_domain)

本工具自动补充这些配置，生成完整的 FloXML 项目文件。
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Iterable
import xml.etree.ElementTree as ET


# ============================================================================
# 数据类定义
# ============================================================================

@dataclass
class ComponentData:
    """ECXML 组件数据"""
    name: str
    power: float = 0.0
    x: float = 0.0
    y: float = 0.0
    z: float = 0.0
    width: float = 0.0   # FloXML size/x
    height: float = 0.0  # FloXML size/y
    depth: float = 0.0   # FloXML size/z
    material: str = "Default"


@dataclass
class ConversionConfig:
    """转换配置"""
    padding_ratio: float = 0.1
    minimum_padding: float = 0.01
    ambient_temp: float = 300.0
    ambient_name: str = "Ambient"
    fluid_name: str = "Air"
    outer_iterations: int = 500
    default_material: str = "Default"


# ============================================================================
# ECXML 解析器
# ============================================================================

class ECXMLExtractor:
    """从 ECXML 提取组件数据"""

    KNOWN_NAMESPACES = {
        'ecxml': 'http://www.jedec.org/ecxml',
        'ft': 'http://www.mentor.com/flotherm/ecxml',
    }

    def __init__(self, filepath: str):
        self.filepath = filepath
        self.tree = ET.parse(filepath)
        self.root = self.tree.getroot()
        self.namespaces = self._detect_namespaces()

    def _detect_namespaces(self) -> Dict[str, str]:
        """检测 XML 命名空间"""
        namespaces = {}
        for key, value in self.root.attrib.items():
            if key.startswith('xmlns'):
                prefix = key.split(':')[1] if ':' in key else ''
                namespaces[prefix] = value
        return namespaces

    def _strip_ns(self, tag: str) -> str:
        """去除命名空间前缀"""
        return tag.split('}')[1] if '}' in tag else tag

    def _get_float_attr(self, elem: ET.Element, *attrs: str) -> float:
        """获取浮点属性值"""
        for attr in attrs:
            val = elem.get(attr) or elem.get(attr.lower()) or elem.get(attr.capitalize())
            if val is not None:
                try:
                    return float(val)
                except ValueError:
                    pass
        return 0.0

    def _get_float_text(self, elem: ET.Element, *tags: str) -> float:
        """获取浮点文本值"""
        for tag in tags:
            child = elem.find(tag)
            if child is None:
                child = elem.find(tag.lower())
            if child is None:
                child = elem.find(tag.capitalize())
            if child is not None and child.text:
                try:
                    return float(child.text.strip())
                except ValueError:
                    pass
        return 0.0

    def extract_components(self) -> List[ComponentData]:
        """提取所有组件数据"""
        components = []

        for elem in self.root.iter():
            tag = self._strip_ns(elem.tag).lower()
            if 'component' in tag or 'device' in tag:
                comp = self._parse_component(elem)
                if comp:
                    components.append(comp)

        return components

    def _parse_component(self, elem: ET.Element) -> Optional[ComponentData]:
        """解析单个组件"""
        try:
            # 名称
            name = elem.get('name') or elem.get('Name') or 'Component'

            # 功耗 - 支持多种格式和命名空间
            power = 0.0
            for child in elem:
                child_tag = self._strip_ns(child.tag).lower()
                if 'powerdissipation' in child_tag or child_tag == 'power':
                    if child.text:
                        try:
                            power = float(child.text.strip())
                            break
                        except ValueError:
                            pass

            # 位置和尺寸
            x = y = z = width = height = depth = 0.0
            material = "Default"

            for child in elem:
                child_tag = self._strip_ns(child.tag).lower()

                if 'position' in child_tag:
                    x = self._get_float_attr(child, 'x', 'X')
                    y = self._get_float_attr(child, 'y', 'Y')
                    z = self._get_float_attr(child, 'z', 'Z')
                elif 'geometry' in child_tag:
                    # Geometry 子元素中包含 Size
                    for geo_child in child:
                        geo_tag = self._strip_ns(geo_child.tag).lower()
                        if 'size' in geo_tag:
                            width = self._get_float_attr(geo_child, 'width', 'Width')
                            height = self._get_float_attr(geo_child, 'height', 'Height')
                            depth = self._get_float_attr(geo_child, 'depth', 'Depth')
                elif 'size' in child_tag:
                    width = self._get_float_attr(child, 'width', 'Width')
                    height = self._get_float_attr(child, 'height', 'Height')
                    depth = self._get_float_attr(child, 'depth', 'Depth')
                elif 'material' in child_tag:
                    mat_name = child.get('name') or child.findtext('name')
                    if mat_name:
                        material = mat_name.strip()

            return ComponentData(
                name=name,
                power=power,
                x=x, y=y, z=z,
                width=width, height=height, depth=depth,
                material=material
            )
        except Exception as e:
            print(f"[WARN] 解析组件失败: {e}")
            return None

    def get_project_name(self) -> str:
        """获取项目名称"""
        # 尝试从根元素获取
        name = self.root.get('name') or self.root.get('Name')
        if name:
            return name

        # 尝试从 name 子元素获取
        name_elem = self.root.find('name')
        if name_elem is not None and name_elem.text:
            return name_elem.text.strip()

        # 使用文件名
        return Path(self.filepath).stem


# ============================================================================
# FloXML 构建器
# ============================================================================

class FloXMLBuilder:
    """构建 FloXML 项目文件"""

    def __init__(self, config: ConversionConfig):
        self.config = config

    def _append_text(self, parent: ET.Element, tag: str, text: str) -> ET.Element:
        """添加带文本的子元素"""
        elem = ET.SubElement(parent, tag)
        elem.text = text
        return elem

    def build_project(self, components: List[ComponentData], project_name: str) -> ET.Element:
        """构建完整的 FloXML 项目"""
        root = ET.Element("xml_case")

        # 项目名称
        self._append_text(root, "name", f"{project_name}_Project")

        # 模型设置
        root.append(self._build_model())

        # 求解设置
        root.append(self._build_solve())

        # 计算求解域
        bounds = self._calculate_bounds(components)
        domain_pos, domain_size = self._calculate_domain(bounds)

        # 网格设置
        root.append(self._build_grid(domain_size))

        # 属性
        root.append(self._build_attributes(components))

        # 几何体
        root.append(self._build_geometry(components))

        # 求解域
        root.append(self._build_solution_domain(domain_pos, domain_size))

        return root

    def _build_model(self) -> ET.Element:
        """构建 model 节"""
        model = ET.Element("model")

        # modeling
        modeling = ET.SubElement(model, "modeling")
        for tag, val in (
            ("solution", "flow_heat"),
            ("radiation", "off"),
            ("dimensionality", "3d"),
            ("transient", "false"),
            ("store_mass_flux", "false"),
            ("store_heat_flux", "false"),
            ("store_surface_temp", "false"),
            ("store_grad_t", "false"),
            ("store_bn_sc", "false"),
            ("store_power_density", "false"),
            ("store_mean_radiant_temperature", "false"),
            ("compute_capture_index", "false"),
            ("user_defined_subgroups", "false"),
            ("store_lma", "false"),
        ):
            self._append_text(modeling, tag, val)

        # turbulence
        turbulence = ET.SubElement(model, "turbulence")
        self._append_text(turbulence, "type", "turbulent")
        self._append_text(turbulence, "turbulence_type", "auto_algebraic")

        # gravity
        gravity = ET.SubElement(model, "gravity")
        self._append_text(gravity, "type", "normal")
        self._append_text(gravity, "normal_direction", "neg_y")
        self._append_text(gravity, "value_type", "user")
        self._append_text(gravity, "gravity_value", "9.81")

        # global
        global_settings = ET.SubElement(model, "global")
        for tag, val in (
            ("datum_pressure", "101325"),
            ("radiant_temperature", str(self.config.ambient_temp)),
            ("ambient_temperature", str(self.config.ambient_temp)),
            ("concentration_1", "0"),
            ("concentration_2", "0"),
            ("concentration_3", "0"),
            ("concentration_4", "0"),
            ("concentration_5", "0"),
        ):
            self._append_text(global_settings, tag, val)

        return model

    def _build_solve(self) -> ET.Element:
        """构建 solve 节"""
        solve = ET.Element("solve")
        overall = ET.SubElement(solve, "overall_control")

        for tag, val in (
            ("outer_iterations", str(self.config.outer_iterations)),
            ("fan_relaxation", "1"),
            ("estimated_free_convection_velocity", "0.2"),
            ("solver_option", "multi_grid"),
            ("active_plate_conduction", "false"),
            ("use_double_precision", "false"),
            ("network_assembly_block_correction", "false"),
            ("freeze_flow", "false"),
            ("store_error_field", "false"),
        ):
            self._append_text(overall, tag, val)

        return solve

    def _build_grid(self, domain_size: Tuple[float, float, float]) -> ET.Element:
        """构建 grid 节"""
        x_size, y_size, z_size = domain_size

        grid = ET.Element("grid")
        system_grid = ET.SubElement(grid, "system_grid")

        self._append_text(system_grid, "smoothing", "true")
        self._append_text(system_grid, "smoothing_type", "v3")
        self._append_text(system_grid, "dynamic_update", "true")

        # 计算网格尺寸
        def grid_axis(parent: ET.Element, tag: str, size: float):
            axis = ET.SubElement(parent, tag)
            min_sz = min(max(size / 100.0, 1e-4), 0.001)
            max_sz = max(size / 12.0, 0.001)
            self._append_text(axis, "min_size", f"{min_sz:.6g}")
            self._append_text(axis, "grid_type", "max_size")
            self._append_text(axis, "max_size", f"{max_sz:.6g}")
            self._append_text(axis, "smoothing_value", "12")

        grid_axis(system_grid, "x_grid", x_size)
        grid_axis(system_grid, "y_grid", y_size)
        grid_axis(system_grid, "z_grid", z_size)

        return grid

    def _build_attributes(self, components: List[ComponentData]) -> ET.Element:
        """构建 attributes 节"""
        attributes = ET.Element("attributes")

        # 材料
        materials = ET.SubElement(attributes, "materials")
        used_materials = set(c.material for c in components if c.material)
        used_materials.add(self.config.default_material)

        for mat_name in used_materials:
            mat = ET.SubElement(materials, "isotropic_material_att")
            self._append_text(mat, "name", mat_name)
            self._append_text(mat, "conductivity", "1.0")
            self._append_text(mat, "density", "1.0")
            self._append_text(mat, "specific_heat", "1.0")

        # 热源
        sources = ET.SubElement(attributes, "sources")
        for comp in components:
            if comp.power > 0:
                src = ET.SubElement(sources, "source_att")
                self._append_text(src, "name", f"{comp.name}_Source")
                self._append_text(src, "source_type", "fixed")
                self._append_text(src, "power", f"{comp.power:.6g}")

        # 环境
        ambients = ET.SubElement(attributes, "ambients")
        ambient = ET.SubElement(ambients, "ambient_att")
        self._append_text(ambient, "name", self.config.ambient_name)
        self._append_text(ambient, "pressure", "0")
        self._append_text(ambient, "temperature", str(self.config.ambient_temp))
        self._append_text(ambient, "radiant_temperature", str(self.config.ambient_temp))
        self._append_text(ambient, "heat_transfer_coeff", "0")

        velocity = ET.SubElement(ambient, "velocity")
        for axis in ("x", "y", "z"):
            self._append_text(velocity, axis, "0")

        for tag in ("turbulent_kinetic_energy", "turbulent_dissipation_rate",
                    "concentration_1", "concentration_2", "concentration_3",
                    "concentration_4", "concentration_5"):
            self._append_text(ambient, tag, "0")

        # 流体
        fluids = ET.SubElement(attributes, "fluids")
        fluid = ET.SubElement(fluids, "fluid_att")
        self._append_text(fluid, "name", self.config.fluid_name)
        self._append_text(fluid, "conductivity_type", "constant")
        self._append_text(fluid, "conductivity", "0.0261")
        self._append_text(fluid, "viscosity_type", "constant")
        self._append_text(fluid, "viscosity", "0.0000184")
        self._append_text(fluid, "density_type", "constant")
        self._append_text(fluid, "density", "1.16")
        self._append_text(fluid, "specific_heat", "1008")
        self._append_text(fluid, "expansivity", "0.003")
        self._append_text(fluid, "diffusivity", "0")

        return attributes

    def _build_geometry(self, components: List[ComponentData]) -> ET.Element:
        """构建 geometry 节"""
        geometry = ET.Element("geometry")

        for comp in components:
            cuboid = ET.SubElement(geometry, "cuboid")
            self._append_text(cuboid, "name", comp.name)

            # 位置
            position = ET.SubElement(cuboid, "position")
            self._append_text(position, "x", f"{comp.x:.6g}")
            self._append_text(position, "y", f"{comp.y:.6g}")
            self._append_text(position, "z", f"{comp.z:.6g}")

            # 尺寸 (ECXML width/height/depth -> FloXML x/y/z)
            size = ET.SubElement(cuboid, "size")
            self._append_text(size, "x", f"{comp.width:.6g}")
            self._append_text(size, "y", f"{comp.height:.6g}")
            self._append_text(size, "z", f"{comp.depth:.6g}")

            # 材料
            self._append_text(cuboid, "material", comp.material or self.config.default_material)

            # 热源
            if comp.power > 0:
                self._append_text(cuboid, "source", f"{comp.name}_Source")

        return geometry

    def _build_solution_domain(self, position: Tuple[float, float, float],
                               size: Tuple[float, float, float]) -> ET.Element:
        """构建 solution_domain 节"""
        domain = ET.Element("solution_domain")

        # 位置
        pos = ET.SubElement(domain, "position")
        self._append_text(pos, "x", f"{position[0]:.6g}")
        self._append_text(pos, "y", f"{position[1]:.6g}")
        self._append_text(pos, "z", f"{position[2]:.6g}")

        # 尺寸
        sz = ET.SubElement(domain, "size")
        self._append_text(sz, "x", f"{size[0]:.6g}")
        self._append_text(sz, "y", f"{size[1]:.6g}")
        self._append_text(sz, "z", f"{size[2]:.6g}")

        # 边界条件
        for face in ("x_low_ambient", "x_high_ambient",
                     "y_low_ambient", "y_high_ambient",
                     "z_low_ambient", "z_high_ambient"):
            self._append_text(domain, face, self.config.ambient_name)

        # 流体
        self._append_text(domain, "fluid", self.config.fluid_name)

        return domain

    def _calculate_bounds(self, components: List[ComponentData]) -> Tuple[float, float, float, float, float, float]:
        """计算组件边界框"""
        if not components:
            return (0.0, 0.0, 0.0, 0.1, 0.1, 0.1)

        min_x = min(c.x for c in components)
        min_y = min(c.y for c in components)
        min_z = min(c.z for c in components)
        max_x = max(c.x + c.width for c in components)
        max_y = max(c.y + c.height for c in components)
        max_z = max(c.z + c.depth for c in components)

        return (min_x, min_y, min_z, max_x, max_y, max_z)

    def _calculate_domain(self, bounds: Tuple[float, float, float, float, float, float]) -> Tuple[Tuple[float, float, float], Tuple[float, float, float]]:
        """计算求解域位置和尺寸"""
        min_x, min_y, min_z, max_x, max_y, max_z = bounds

        geom_x = max(max_x - min_x, 0.001)
        geom_y = max(max_y - min_y, 0.001)
        geom_z = max(max_z - min_z, 0.001)

        pad_x = max(geom_x * self.config.padding_ratio, self.config.minimum_padding)
        pad_y = max(geom_y * self.config.padding_ratio, self.config.minimum_padding)
        pad_z = max(geom_z * self.config.padding_ratio, self.config.minimum_padding)

        position = (min_x - pad_x / 2.0, min_y - pad_y / 2.0, min_z - pad_z / 2.0)
        size = (geom_x + pad_x, geom_y + pad_y, geom_z + pad_z)

        return position, size


# ============================================================================
# 转换器
# ============================================================================

class ECXMLToFloXMLConverter:
    """ECXML 到 FloXML 转换器"""

    def __init__(self, config: Optional[ConversionConfig] = None):
        self.config = config or ConversionConfig()

    def convert(self, input_path: Path, output_path: Optional[Path] = None) -> Dict:
        """
        转换单个文件

        Returns:
            结果字典: {success, input, output, components, errors, warnings}
        """
        result = {
            "success": False,
            "input": str(input_path),
            "output": None,
            "components": 0,
            "errors": [],
            "warnings": []
        }

        try:
            # 验证输入
            if not input_path.exists():
                result["errors"].append(f"输入文件不存在: {input_path}")
                return result

            # 解析 ECXML
            extractor = ECXMLExtractor(str(input_path))
            components = extractor.extract_components()

            if not components:
                result["warnings"].append("未找到任何组件")

            # 获取项目名称
            project_name = extractor.get_project_name()

            # 构建 FloXML
            builder = FloXMLBuilder(self.config)
            root = builder.build_project(components, project_name)

            # 确定输出路径
            if output_path is None:
                output_path = input_path.with_name(f"{input_path.stem}_floxml.xml")
            result["output"] = str(output_path)

            # 写入文件
            self._write_floxml(root, output_path)

            result["success"] = True
            result["components"] = len(components)

        except Exception as e:
            result["errors"].append(str(e))

        return result

    def _write_floxml(self, root: ET.Element, output_path: Path) -> None:
        """写入 FloXML 文件"""
        tree = ET.ElementTree(root)
        ET.indent(tree, space="    ")

        xml_bytes = ET.tostring(root, encoding="utf-8")
        text = '<?xml version="1.0" encoding="UTF-8" standalone="no" ?>\n' + xml_bytes.decode("utf-8")

        output_path.write_text(text, encoding="utf-8")

    def convert_batch(self, input_files: List[Path], output_dir: Path) -> List[Dict]:
        """批量转换"""
        results = []

        if not output_dir.exists():
            output_dir.mkdir(parents=True)

        for input_path in input_files:
            output_path = output_dir / f"{input_path.stem}_floxml.xml"
            result = self.convert(input_path, output_path)
            results.append(result)

        return results


# ============================================================================
# CLI 接口
# ============================================================================

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="将 ECXML (JEDEC JEP181) 转换为 FloTHERM FloXML 项目格式",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 单文件转换
  python ecxml_to_floxml_converter.py input.ecxml -o output.xml

  # 批量转换
  python ecxml_to_floxml_converter.py *.ecxml --output-dir ./floxml/

  # 自定义参数
  python ecxml_to_floxml_converter.py input.ecxml -o output.xml \\
      --padding-ratio 0.15 --ambient-temp 308.15
        """
    )

    # 输入输出
    parser.add_argument("input", nargs="+", type=Path,
                        help="输入 ECXML 文件")
    parser.add_argument("-o", "--output", type=Path,
                        help="输出 FloXML 文件 (单文件模式)")
    parser.add_argument("--output-dir", type=Path,
                        help="输出目录 (批量模式)")

    # 转换参数
    parser.add_argument("--padding-ratio", type=float, default=0.1,
                        help="求解域 padding 比例 (默认: 0.1)")
    parser.add_argument("--minimum-padding", type=float, default=0.01,
                        help="最小 padding (米) (默认: 0.01)")
    parser.add_argument("--ambient-temp", type=float, default=300.0,
                        help="环境温度 (K) (默认: 300)")
    parser.add_argument("--outer-iterations", type=int, default=500,
                        help="求解迭代次数 (默认: 500)")

    # 其他选项
    parser.add_argument("-v", "--verbose", action="store_true",
                        help="详细输出")

    return parser


def main(argv: Optional[Iterable[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)

    # 构建配置
    config = ConversionConfig(
        padding_ratio=args.padding_ratio,
        minimum_padding=args.minimum_padding,
        ambient_temp=args.ambient_temp,
        outer_iterations=args.outer_iterations,
    )

    converter = ECXMLToFloXMLConverter(config)

    # 判断模式
    input_files = args.input
    is_batch = len(input_files) > 1 or args.output_dir

    if is_batch:
        # 批量模式
        output_dir = args.output_dir or Path(".")
        results = converter.convert_batch(input_files, output_dir)

        success_count = sum(1 for r in results if r["success"])
        total_count = len(results)

        print("=" * 60)
        print("ECXML to FloXML 批量转换")
        print("=" * 60)
        print(f"输入目录: {input_files[0].parent}")
        print(f"输出目录: {output_dir}")
        print(f"成功: {success_count}/{total_count}")
        print()

        for r in results:
            status = "✓" if r["success"] else "✗"
            print(f"  [{status}] {Path(r['input']).name}")
            if args.verbose and r.get("components"):
                print(f"       组件数: {r['components']}")
            for err in r.get("errors", []):
                print(f"       错误: {err}")
            for warn in r.get("warnings", []):
                print(f"       警告: {warn}")

        return 0 if success_count == total_count else 1

    else:
        # 单文件模式
        output_path = args.output
        result = converter.convert(input_files[0], output_path)

        print("=" * 60)
        print("ECXML to FloXML 转换")
        print("=" * 60)
        print(f"输入: {result['input']}")
        print(f"输出: {result['output']}")

        if result["success"]:
            print(f"组件数: {result['components']}")
            print("[OK] 转换成功")
            return 0
        else:
            for err in result.get("errors", []):
                print(f"[ERROR] {err}")
            return 1


if __name__ == "__main__":
    raise SystemExit(main())
