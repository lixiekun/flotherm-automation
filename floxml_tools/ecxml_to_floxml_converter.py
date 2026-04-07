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
from typing import Any, Dict, List, Optional, Tuple, Iterable
import xml.etree.ElementTree as ET


# ============================================================================
# 数据类定义
# ============================================================================

@dataclass
class CuboidData:
    """Cuboid 几何体数据"""
    name: str
    x: float = 0.0
    y: float = 0.0
    z: float = 0.0
    width: float = 0.0   # FloXML size/x
    height: float = 0.0  # FloXML size/y
    depth: float = 0.0   # FloXML size/z
    material: str = "Default"
    power: float = 0.0
    active: bool = True


@dataclass
class SourceData:
    """热源数据"""
    name: str
    x: float = 0.0
    y: float = 0.0
    z: float = 0.0
    width: float = 0.0
    height: float = 0.0
    depth: float = 0.0
    power: float = 0.0
    active: bool = True


@dataclass
class MonitorPointData:
    """监控点数据"""
    name: str
    x: float = 0.0
    y: float = 0.0
    z: float = 0.0
    active: bool = True


@dataclass
class AssemblyData:
    """装配件数据（支持嵌套）"""
    name: str
    active: bool = True
    position_x: float = 0.0
    position_y: float = 0.0
    position_z: float = 0.0
    material: str = "Default"
    cuboids: List[CuboidData] = field(default_factory=list)
    sources: List[SourceData] = field(default_factory=list)
    monitor_points: List[MonitorPointData] = field(default_factory=list)
    sub_assemblies: List['AssemblyData'] = field(default_factory=list)
    geometry_items: List[Tuple[str, Any]] = field(default_factory=list)


@dataclass
class MaterialData:
    """材料数据"""
    name: str
    conductivity: float = 1.0
    density: float = 1.0
    specific_heat: float = 1.0
    emissivity: float = 0.9


@dataclass
class SolutionDomainData:
    """求解域数据"""
    x: float = 0.0
    y: float = 0.0
    z: float = 0.0
    width: float = 0.1
    height: float = 0.1
    depth: float = 0.1


@dataclass
class ECXMLData:
    """完整的 ECXML 数据"""
    name: str = "Project"
    producer: str = ""
    materials: List[MaterialData] = field(default_factory=list)
    root_assembly: Optional[AssemblyData] = None
    sources: List[SourceData] = field(default_factory=list)
    monitor_points: List[MonitorPointData] = field(default_factory=list)
    solution_domain: Optional[SolutionDomainData] = None


# 保留旧类名作为别名，保持向后兼容
ComponentData = CuboidData


@dataclass
class ConversionConfig:
    """转换配置"""
    # --- Domain & Environment ---
    padding_ratio: float = 0.1
    minimum_padding: float = 0.01
    ambient_temp: float = 300.0
    ambient_name: str = "Ambient"
    fluid_name: str = "Air"
    outer_iterations: int = 500
    default_material: str = "Default"

    # --- External config sources ---
    grid_config_file: Optional[str] = None  # Excel 网格配置文件路径
    template_file: Optional[str] = None  # FloXML 模板文件路径
    floxml_source: Optional[str] = None  # 源 FloXML/PDML 文件路径（用于提取网格设置）
    config_file: Optional[str] = None  # 统一 JSON 配置文件路径（注入属性/分配）

    # --- Model settings (None = not written, FloTHERM uses internal defaults) ---
    solution: Optional[str] = None
    radiation: Optional[str] = None
    dimensionality: Optional[str] = None
    transient: Optional[bool] = None
    turbulence_type: Optional[str] = None
    turbulence_model: Optional[str] = None
    gravity_direction: Optional[str] = None
    gravity_value: Optional[float] = None
    datum_pressure: Optional[float] = None

    # --- Solve settings ---
    solver_option: Optional[str] = None
    fan_relaxation: Optional[float] = None
    estimated_free_convection_velocity: Optional[float] = None
    use_double_precision: Optional[bool] = None
    freeze_flow: Optional[bool] = None
    active_plate_conduction: Optional[bool] = None
    network_assembly_block_correction: Optional[bool] = None
    store_error_field: Optional[bool] = None

    # --- Fluid properties ---
    fluid_conductivity: Optional[float] = None
    fluid_viscosity: Optional[float] = None
    fluid_density: Optional[float] = None
    fluid_specific_heat: Optional[float] = None
    fluid_expansivity: Optional[float] = None

    # --- Grid defaults ---
    grid_smoothing_type: Optional[str] = None
    grid_smoothing_value: Optional[int] = None
    grid_min_divisor: Optional[float] = None
    grid_max_divisor: Optional[float] = None

    # --- Source defaults ---
    source_applies_to: Optional[str] = None
    source_type: Optional[str] = None
    source_linear_coefficient: Optional[float] = None

    # --- Store flags ---
    store_mass_flux: Optional[bool] = None
    store_heat_flux: Optional[bool] = None
    store_surface_temp: Optional[bool] = None
    store_grad_t: Optional[bool] = None
    store_bn_sc: Optional[bool] = None
    store_power_density: Optional[bool] = None
    store_mean_radiant_temperature: Optional[bool] = None
    compute_capture_index: Optional[bool] = None
    user_defined_subgroups: Optional[bool] = None
    store_lma: Optional[bool] = None

    # FloTHERM defaults — used by apply_defaults() for backward compat
    _DEFAULTS: Dict[str, object] = field(default_factory=lambda: dict(
        solution="flow_heat", radiation="off", dimensionality="3d",
        transient=False, turbulence_type="turbulent", turbulence_model="auto_algebraic",
        gravity_direction="neg_y", gravity_value=9.81, datum_pressure=101325.0,
        solver_option="multi_grid", fan_relaxation=1.0,
        estimated_free_convection_velocity=0.2,
        use_double_precision=False, freeze_flow=False,
        active_plate_conduction=False, network_assembly_block_correction=False,
        store_error_field=False,
        fluid_conductivity=0.0261, fluid_viscosity=0.0000184,
        fluid_density=1.16, fluid_specific_heat=1008.0, fluid_expansivity=0.003,
        grid_smoothing_type="v3", grid_smoothing_value=12,
        grid_min_divisor=100.0, grid_max_divisor=12.0,
        source_applies_to="temperature", source_type="total", source_linear_coefficient=0.0,
        store_mass_flux=False, store_heat_flux=False, store_surface_temp=False,
        store_grad_t=False, store_bn_sc=False, store_power_density=False,
        store_mean_radiant_temperature=False, compute_capture_index=False,
        user_defined_subgroups=False, store_lma=False,
    ))

    def apply_defaults(self) -> None:
        """Fill None fields with FloTHERM defaults. Called when not using --settings."""
        for field_name, default_value in self._DEFAULTS.items():
            if getattr(self, field_name) is None:
                setattr(self, field_name, default_value)

    @classmethod
    def from_template(cls, filepath: str) -> 'ConversionConfig':
        """从模板文件加载配置"""
        from floxml_template import load_template

        template = load_template(filepath)
        # 从模板中提取简单配置
        return cls(
            padding_ratio=template.solution_domain.padding_ratio,
            minimum_padding=template.solution_domain.minimum_padding,
            ambient_temp=template.attributes.ambients[0].temperature if template.attributes.ambients else 300.0,
            ambient_name=template.attributes.ambients[0].name if template.attributes.ambients else "Ambient",
            fluid_name=template.attributes.fluids[0].name if template.attributes.fluids else "Air",
            outer_iterations=template.solve.overall_control.outer_iterations,
            default_material=template.default_references.material,
            grid_config_file=None,
            template_file=filepath
        )

    @classmethod
    def from_json(cls, filepath: str) -> 'ConversionConfig':
        """从 JSON 文件加载配置，只覆盖指定的字段，其余用默认值。

        JSON 示例::

            {
              "radiation": "on",
              "fluid_conductivity": 0.0262,
              "outer_iterations": 1000
            }
        """
        import json
        from dataclasses import fields as dc_fields

        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)

        valid_names = {f.name for f in dc_fields(cls)}
        unknown = set(data.keys()) - valid_names
        if unknown:
            print(f"[WARN] JSON 中有未识别的字段，已忽略: {unknown}")

        return cls(**{k: v for k, v in data.items() if k in valid_names})

    def merge_json(self, filepath: str) -> None:
        """从 JSON 文件合并配置，覆盖已有字段。"""
        import json
        from dataclasses import fields as dc_fields

        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)

        valid_names = {f.name for f in dc_fields(self)}
        unknown = set(data.keys()) - valid_names
        if unknown:
            print(f"[WARN] JSON 中有未识别的字段，已忽略: {unknown}")

        for k, v in data.items():
            if k in valid_names:
                setattr(self, k, v)

    # CLI 参数名 → ConversionConfig 字段名的映射
    _CLI_MAP = {
        "padding_ratio": "padding_ratio",
        "minimum_padding": "minimum_padding",
        "ambient_temp": "ambient_temp",
        "outer_iterations": "outer_iterations",
        "radiation": "radiation",
        "turbulence_model": "turbulence_model",
        "gravity_direction": "gravity_direction",
        "gravity_value": "gravity_value",
        "datum_pressure": "datum_pressure",
        "solver_option": "solver_option",
        "use_double_precision": "use_double_precision",
        "fluid_conductivity": "fluid_conductivity",
        "fluid_viscosity": "fluid_viscosity",
        "fluid_density": "fluid_density",
        "fluid_specific_heat": "fluid_specific_heat",
        "fluid_expansivity": "fluid_expansivity",
    }

    def merge_cli_args(self, args) -> None:
        """从 argparse Namespace 合并，只覆盖用户显式指定的参数。

        通过比较 args 值与 parser 默认值来判断是否显式指定。
        """
        import dataclasses
        defaults = {a.dest: a.default for a in args.__dict__}

        for cli_name, field_name in self._CLI_MAP.items():
            val = getattr(args, cli_name, None)
            default = defaults.get(cli_name)
            # bool store_true 类型：default 是 False，显式传了就是 True
            if isinstance(val, bool):
                if val:
                    setattr(self, field_name, val)
            elif val is not None and val != default:
                setattr(self, field_name, val)


# ============================================================================
# ECXML 解析器
# ============================================================================

class ECXMLExtractor:
    """从 ECXML 提取完整数据结构"""

    def __init__(self, filepath: str):
        self.filepath = filepath
        self.tree = ET.parse(filepath)
        self.root = self.tree.getroot()

    def _strip_ns(self, tag: str) -> str:
        """去除命名空间前缀"""
        return tag.split('}')[1] if '}' in tag else tag

    def _get_tag_lower(self, elem: ET.Element) -> str:
        """获取小写的标签名（去除命名空间）"""
        return self._strip_ns(elem.tag).lower()

    def _find_child(self, elem: ET.Element, *tag_names: str) -> Optional[ET.Element]:
        """按名称查找子元素（忽略命名空间和大小写）"""
        for child in elem:
            tag_lower = self._get_tag_lower(child)
            for name in tag_names:
                if tag_lower == name.lower():
                    return child
        return None

    def _find_children(self, elem: ET.Element, *tag_names: str) -> List[ET.Element]:
        """按名称查找所有匹配的子元素"""
        results = []
        for child in elem:
            tag_lower = self._get_tag_lower(child)
            for name in tag_names:
                if tag_lower == name.lower():
                    results.append(child)
                    break
        return results

    def _get_float_text(self, elem: ET.Element, *tag_names: str) -> float:
        """获取子元素的浮点文本值"""
        child = self._find_child(elem, *tag_names)
        if child is not None and child.text:
            try:
                return float(child.text.strip())
            except (ValueError, AttributeError):
                pass
        return 0.0

    def _get_text(self, elem: ET.Element, *tag_names: str) -> str:
        """获取子元素的文本值"""
        child = self._find_child(elem, *tag_names)
        if child is not None and child.text:
            return child.text.strip()
        return ""

    def _parse_location(self, elem: ET.Element) -> Tuple[float, float, float]:
        """解析 location/position 元素"""
        loc = self._find_child(elem, 'location', 'position')
        if loc is not None:
            x = self._get_float_text(loc, 'x')
            y = self._get_float_text(loc, 'y')
            z = self._get_float_text(loc, 'z')
            return (x, y, z)
        return (0.0, 0.0, 0.0)

    def _parse_size(self, elem: ET.Element) -> Tuple[float, float, float]:
        """解析 size 元素"""
        size = self._find_child(elem, 'size')
        if size is not None:
            x = self._get_float_text(size, 'x', 'width')
            y = self._get_float_text(size, 'y', 'height')
            z = self._get_float_text(size, 'z', 'depth')
            return (x, y, z)
        return (0.0, 0.0, 0.0)

    def _parse_solid3d_block(self, elem: ET.Element) -> CuboidData:
        """解析 solid3dBlock 元素"""
        name = self._get_text(elem, 'name') or "Cuboid"
        active_text = self._get_text(elem, 'active')
        active = active_text.lower() != 'false'
        x, y, z = self._parse_location(elem)
        width, height, depth = self._parse_size(elem)
        material = self._get_text(elem, 'material') or "Default"
        power = self._get_float_text(elem, 'powerdissipation', 'power')

        return CuboidData(
            name=name,
            x=x, y=y, z=z,
            width=width, height=height, depth=depth,
            material=material,
            power=power,
            active=active
        )

    def _parse_assembly(self, elem: ET.Element) -> AssemblyData:
        """递归解析 assembly 元素"""
        name = self._get_text(elem, 'name') or "Assembly"
        active_text = self._get_text(elem, 'active')
        active = active_text.lower() != 'false'
        x, y, z = self._parse_location(elem)
        material = self._get_text(elem, 'material') or "Default"

        assembly = AssemblyData(
            name=name,
            active=active,
            position_x=x,
            position_y=y,
            position_z=z,
            material=material
        )

        # 查找 geometry 子元素
        geo = self._find_child(elem, 'geometry')
        if geo is not None:
            for child in geo:
                tag_lower = self._get_tag_lower(child)
                if tag_lower in {'solid3dblock'}:
                    cuboid = self._parse_solid3d_block(child)
                    assembly.cuboids.append(cuboid)
                    assembly.geometry_items.append(("cuboid", cuboid))
                elif tag_lower in {'source2dblock', 'source3dblock', 'sourceblock'}:
                    source = self._parse_source_block(child)
                    assembly.sources.append(source)
                    assembly.geometry_items.append(("source", source))
                elif tag_lower in {'monitorpoint', 'monitor_point'}:
                    mp = self._parse_monitor_point(child)
                    assembly.monitor_points.append(mp)
                    assembly.geometry_items.append(("monitor_point", mp))
                elif tag_lower == 'assembly':
                    sub_data = self._parse_assembly(child)
                    assembly.sub_assemblies.append(sub_data)
                    assembly.geometry_items.append(("assembly", sub_data))

        return assembly

    def _parse_source_block(self, elem: ET.Element) -> SourceData:
        """解析 sourceBlock 元素"""
        name = self._get_text(elem, 'name') or "Source"
        active_text = self._get_text(elem, 'active')
        active = active_text.lower() != 'false'
        x, y, z = self._parse_location(elem)
        width, height, depth = self._parse_size(elem)
        power = self._get_float_text(elem, 'powerdissipation', 'power')

        return SourceData(
            name=name,
            x=x, y=y, z=z,
            width=width, height=height, depth=depth,
            power=power,
            active=active
        )

    def _parse_monitor_point(self, elem: ET.Element) -> MonitorPointData:
        """解析 monitorPoint 元素"""
        name = self._get_text(elem, 'name') or "MonitorPoint"
        active_text = self._get_text(elem, 'active')
        active = active_text.lower() != 'false'
        x, y, z = self._parse_location(elem)

        return MonitorPointData(
            name=name,
            x=x, y=y, z=z,
            active=active
        )

    def _parse_material(self, elem: ET.Element) -> MaterialData:
        """解析 material 元素"""
        name = self._get_text(elem, 'name') or "Material"
        density = self._get_float_text(elem, 'density')
        specific_heat = self._get_float_text(elem, 'specific_heat')
        emissivity = self._get_float_text(elem, 'surfaceemissivity', 'emissivity')

        # 解析热导率
        conductivity = 1.0
        tc = self._find_child(elem, 'thermalconductivity', 'thermal_conductivity')
        if tc is not None:
            iso = self._find_child(tc, 'isotropic')
            if iso is not None:
                conductivity = self._get_float_text(iso, 'conductivity')

        return MaterialData(
            name=name,
            conductivity=conductivity,
            density=density,
            specific_heat=specific_heat,
            emissivity=emissivity
        )

    def _parse_solution_domain(self, elem: ET.Element) -> SolutionDomainData:
        """解析 solutionDomain 元素"""
        x, y, z = self._parse_location(elem)
        width, height, depth = self._parse_size(elem)

        return SolutionDomainData(
            x=x, y=y, z=z,
            width=width, height=height, depth=depth
        )

    def extract_all(self) -> ECXMLData:
        """提取完整的 ECXML 数据"""
        data = ECXMLData()

        # 项目名称
        data.name = self._get_text(self.root, 'name') or Path(self.filepath).stem

        # 生产者
        data.producer = self._get_text(self.root, 'producer')

        # 解析材料
        materials_elem = self._find_child(self.root, 'materials')
        if materials_elem is not None:
            for mat_elem in self._find_children(materials_elem, 'material'):
                mat = self._parse_material(mat_elem)
                data.materials.append(mat)

        # 解析几何体
        geometry_elem = self._find_child(self.root, 'geometry')
        if geometry_elem is not None:
            # 解析根 assembly
            for assembly_elem in self._find_children(geometry_elem, 'assembly'):
                assembly = self._parse_assembly(assembly_elem)
                if data.root_assembly is None:
                    data.root_assembly = assembly
                # 如果有多个根 assembly，可以作为子 assembly 添加

            # 解析独立热源
            for source_elem in self._find_children(
                geometry_elem,
                'source2dBlock',
                'source3dBlock',
                'sourceBlock',
                'sourceblock',
            ):
                source = self._parse_source_block(source_elem)
                data.sources.append(source)

            # 解析 monitorPoint
            for mp_elem in self._find_children(geometry_elem, 'monitorpoint', 'monitor_point'):
                mp = self._parse_monitor_point(mp_elem)
                data.monitor_points.append(mp)

        # 解析求解域
        sd_elem = self._find_child(self.root, 'solutiondomain', 'solution_domain')
        if sd_elem is not None:
            data.solution_domain = self._parse_solution_domain(sd_elem)

        return data

    def extract_components(self) -> List[CuboidData]:
        """提取所有组件数据（向后兼容方法）"""
        data = self.extract_all()
        components = []

        def collect_cuboids(assembly: AssemblyData):
            components.extend(assembly.cuboids)
            for sub in assembly.sub_assemblies:
                collect_cuboids(sub)

        if data.root_assembly:
            collect_cuboids(data.root_assembly)

        return components

    def get_project_name(self) -> str:
        """获取项目名称"""
        name = self._get_text(self.root, 'name')
        return name or Path(self.filepath).stem


# ============================================================================
# FloXML 构建器
# ============================================================================

class FloXMLBuilder:
    """构建 FloXML 项目文件"""

    def __init__(self, config: ConversionConfig):
        self.config = config
        self._grid_config = None
        self._template: Optional[FloXMLTemplate] = None

        if config.template_file:
            from floxml_template import load_template
            self._template = load_template(config.template_file)
            print(f"[INFO] 已加载模板: {config.template_file}")

        if config.grid_config_file:
            self._load_grid_config(config.grid_config_file)

    def _append_text(self, parent: ET.Element, tag: str, text: str) -> ET.Element:
        """添加带文本的子元素"""
        elem = ET.SubElement(parent, tag)
        elem.text = text
        return elem

    def _write_field(self, parent: ET.Element, tag: str, value) -> None:
        """Write child element; skip entirely when value is None."""
        if value is None:
            return
        if isinstance(value, bool):
            self._append_text(parent, tag, str(value).lower())
        elif isinstance(value, float):
            self._append_text(parent, tag, f"{value:.6g}")
        else:
            self._append_text(parent, tag, str(value))

    def build_project(self, ecxml_data: ECXMLData) -> ET.Element:
        """构建完整的 FloXML 项目"""
        # 使用模板（如果可用）
        if self._template:
            builder = FloXMLTemplateBuilder(self._template)
            return builder.build_project(
                ecxml_data.name,
                self._collect_all_cuboids(ecxml_data),
                ecxml_data.materials,
                ecxml_data.sources
            )

        root = ET.Element("xml_case")
        self._append_text(root, "name", ecxml_data.name)

        root.append(self._build_model())
        root.append(self._build_solve())

        if ecxml_data.solution_domain:
            sd = ecxml_data.solution_domain
            domain_pos = (sd.x, sd.y, sd.z)
            domain_size = (sd.width, sd.height, sd.depth)
        else:
            components = self._collect_all_cuboids(ecxml_data)
            bounds = self._calculate_bounds(components)
            domain_pos, domain_size = self._calculate_domain(bounds)

        root.append(self._build_grid(domain_size))
        root.append(self._build_attributes(ecxml_data))
        root.append(self._build_geometry(ecxml_data))
        root.append(self._build_solution_domain(domain_pos, domain_size))

        return root

    def _collect_all_cuboids(self, ecxml_data: ECXMLData) -> List[CuboidData]:
        """收集所有 cuboid 数据"""
        components = []

        def collect_from_assembly(assembly: AssemblyData):
            components.extend(assembly.cuboids)
            for sub in assembly.sub_assemblies:
                collect_from_assembly(sub)

        if ecxml_data.root_assembly:
            collect_from_assembly(ecxml_data.root_assembly)

        return components

    def _collect_all_sources(self, ecxml_data: ECXMLData) -> List[SourceData]:
        """收集所有 source 数据，包括 assembly 内的 source。"""
        sources = list(ecxml_data.sources)

        def collect_from_assembly(assembly: AssemblyData):
            sources.extend(assembly.sources)
            for sub in assembly.sub_assemblies:
                collect_from_assembly(sub)

        if ecxml_data.root_assembly:
            collect_from_assembly(ecxml_data.root_assembly)

        return sources

    def build_project_legacy(self, components: List[ComponentData], project_name: str) -> ET.Element:
        """构建完整的 FloXML 项目（向后兼容）"""
        ecxml_data = ECXMLData(name=f"{project_name}_Project")
        ecxml_data.root_assembly = AssemblyData(name=f"{project_name}_Assembly")
        ecxml_data.root_assembly.cuboids = components
        ecxml_data.root_assembly.geometry_items = [("cuboid", comp) for comp in components]
        return self.build_project(ecxml_data)

    def _build_attributes(self, ecxml_data: ECXMLData) -> ET.Element:
        """构建 attributes 节"""
        attributes = ET.Element("attributes")
        components = self._collect_all_cuboids(ecxml_data)

        used_material_names = set()
        for c in components:
            if c.material:
                used_material_names.add(c.material)
        if ecxml_data.root_assembly and ecxml_data.root_assembly.material:
            used_material_names.add(ecxml_data.root_assembly.material)

        materials = ET.SubElement(attributes, "materials")
        materials_dict = {m.name: m for m in ecxml_data.materials}

        for mat_name in used_material_names:
            mat_elem = ET.SubElement(materials, "isotropic_material_att")
            self._append_text(mat_elem, "name", mat_name)

            if mat_name in materials_dict:
                mat_data = materials_dict[mat_name]
                self._append_text(mat_elem, "conductivity", f"{mat_data.conductivity:.6g}")
                self._append_text(mat_elem, "density", f"{mat_data.density:.6g}")
                self._append_text(mat_elem, "specific_heat", f"{mat_data.specific_heat:.6g}")
            else:
                self._append_text(mat_elem, "conductivity", "1.0")
                self._append_text(mat_elem, "density", "1.0")
                self._append_text(mat_elem, "specific_heat", "1.0")

        all_sources = self._collect_all_sources(ecxml_data)

        sources = ET.SubElement(attributes, "sources")
        for comp in components:
            if comp.power > 0:
                self._build_source_att(sources, f"{comp.name}_Source", comp.power)
        for source in all_sources:
            if source.power > 0:
                self._build_source_att(sources, f"{source.name}_Source", source.power)

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

        for tag in (
            "turbulent_kinetic_energy",
            "turbulent_dissipation_rate",
            "concentration_1",
            "concentration_2",
            "concentration_3",
            "concentration_4",
            "concentration_5",
        ):
            self._append_text(ambient, tag, "0")

        fluids = ET.SubElement(attributes, "fluids")
        fluid = ET.SubElement(fluids, "fluid_att")
        self._append_text(fluid, "name", self.config.fluid_name)
        cfg = self.config
        if cfg.fluid_conductivity is not None:
            self._append_text(fluid, "conductivity_type", "constant")
            self._write_field(fluid, "conductivity", cfg.fluid_conductivity)
        if cfg.fluid_viscosity is not None:
            self._append_text(fluid, "viscosity_type", "constant")
            self._write_field(fluid, "viscosity", cfg.fluid_viscosity)
        if cfg.fluid_density is not None:
            self._append_text(fluid, "density_type", "constant")
            self._write_field(fluid, "density", cfg.fluid_density)
        self._write_field(fluid, "specific_heat", cfg.fluid_specific_heat)
        self._write_field(fluid, "expansivity", cfg.fluid_expansivity)
        self._append_text(fluid, "diffusivity", "0")

        if self._grid_config and self._grid_config.constraints:
            from .grid_config import GridBuilder
            builder = GridBuilder()
            attributes.append(builder.build_constraints_attributes(self._grid_config.constraints))

        return attributes

    def _build_source_att(self, parent: ET.Element, name: str, power: float) -> None:
        """构建 source_att 元素"""
        src = ET.SubElement(parent, "source_att")
        self._append_text(src, "name", name)
        source_options = ET.SubElement(src, "source_options")
        option = ET.SubElement(source_options, "option")
        self._write_field(option, "applies_to", self.config.source_applies_to)
        self._write_field(option, "type", self.config.source_type)
        self._append_text(option, "value", "0")
        self._append_text(option, "power", f"{power:.6g}")
        self._write_field(option, "linear_coefficient", self.config.source_linear_coefficient)

    def _build_geometry(self, ecxml_data: ECXMLData) -> ET.Element:
        """构建 geometry 节"""
        geometry = ET.Element("geometry")

        # 构建根 assembly 及其子元素
        if ecxml_data.root_assembly:
            self._build_assembly_element(geometry, ecxml_data.root_assembly)

        # 构建独立的热源
        for source in ecxml_data.sources:
            self._build_source_element(geometry, source)

        # 构建监控点
        for mp in ecxml_data.monitor_points:
            self._build_monitor_point_element(geometry, mp)

        return geometry

    def _build_assembly_element(self, parent: ET.Element, assembly: AssemblyData) -> ET.Element:
        """递归构建 assembly 元素"""
        assembly_elem = ET.SubElement(parent, "assembly")
        self._append_text(assembly_elem, "name", assembly.name)
        self._append_text(assembly_elem, "active", "true" if assembly.active else "false")
        self._append_text(assembly_elem, "ignore", "false")

        position = ET.SubElement(assembly_elem, "position")
        self._append_text(position, "x", f"{assembly.position_x:.6g}")
        self._append_text(position, "y", f"{assembly.position_y:.6g}")
        self._append_text(position, "z", f"{assembly.position_z:.6g}")

        self._build_identity_orientation(assembly_elem)
        self._append_text(assembly_elem, "material", assembly.material or self.config.default_material)
        self._append_text(assembly_elem, "localized_grid", "false")
        self._apply_grid_constraints(assembly_elem, assembly.name)

        if assembly.cuboids or assembly.sources or assembly.monitor_points or assembly.sub_assemblies:
            geometry_elem = ET.SubElement(assembly_elem, "geometry")
            if assembly.geometry_items:
                for item_type, item in assembly.geometry_items:
                    if item_type == "cuboid":
                        self._build_cuboid_element(geometry_elem, item)
                    elif item_type == "source":
                        self._build_source_element(geometry_elem, item)
                    elif item_type == "monitor_point":
                        self._build_monitor_point_element(geometry_elem, item)
                    elif item_type == "assembly":
                        self._build_assembly_element(geometry_elem, item)
            else:
                for cuboid in assembly.cuboids:
                    self._build_cuboid_element(geometry_elem, cuboid)
                for source in assembly.sources:
                    self._build_source_element(geometry_elem, source)
                for mp in assembly.monitor_points:
                    self._build_monitor_point_element(geometry_elem, mp)
                for sub_assembly in assembly.sub_assemblies:
                    self._build_assembly_element(geometry_elem, sub_assembly)

        return assembly_elem

    def _build_cuboid_element(self, parent: ET.Element, cuboid: CuboidData) -> ET.Element:
        """构建 cuboid 元素"""
        cuboid_elem = ET.SubElement(parent, "cuboid")
        self._append_text(cuboid_elem, "name", cuboid.name)
        self._append_text(cuboid_elem, "active", "true" if cuboid.active else "false")

        position = ET.SubElement(cuboid_elem, "position")
        self._append_text(position, "x", f"{cuboid.x:.6g}")
        self._append_text(position, "y", f"{cuboid.y:.6g}")
        self._append_text(position, "z", f"{cuboid.z:.6g}")

        size = ET.SubElement(cuboid_elem, "size")
        self._append_text(size, "x", f"{cuboid.width:.6g}")
        self._append_text(size, "y", f"{cuboid.height:.6g}")
        self._append_text(size, "z", f"{cuboid.depth:.6g}")

        self._build_identity_orientation(cuboid_elem)
        self._append_text(cuboid_elem, "localized_grid", "false")

        if cuboid.material:
            self._append_text(cuboid_elem, "material", cuboid.material)

        if cuboid.power > 0:
            self._append_text(cuboid_elem, "source", f"{cuboid.name}_Source")

        return cuboid_elem

    def _build_source_element(self, parent: ET.Element, source: SourceData) -> ET.Element:
        """构建 source 元素"""
        source_elem = ET.SubElement(parent, "source")
        self._append_text(source_elem, "name", source.name)
        self._append_text(source_elem, "active", "true" if source.active else "false")

        position = ET.SubElement(source_elem, "position")
        self._append_text(position, "x", f"{source.x:.6g}")
        self._append_text(position, "y", f"{source.y:.6g}")
        self._append_text(position, "z", f"{source.z:.6g}")

        size = ET.SubElement(source_elem, "size")
        self._append_text(size, "x", f"{source.width:.6g}")
        self._append_text(size, "y", f"{source.height:.6g}")
        self._append_text(size, "z", f"{source.depth:.6g}")

        self._build_identity_orientation(source_elem)

        if source.power > 0:
            self._append_text(source_elem, "source", f"{source.name}_Source")
        self._append_text(source_elem, "localized_grid", "false")

        return source_elem

    def _build_monitor_point_element(self, parent: ET.Element, mp: MonitorPointData) -> ET.Element:
        """构建 monitor_point 元素"""
        mp_elem = ET.SubElement(parent, "monitor_point")
        self._append_text(mp_elem, "name", mp.name)
        self._append_text(mp_elem, "active", "true" if mp.active else "false")

        # 位置
        position = ET.SubElement(mp_elem, "position")
        self._append_text(position, "x", f"{mp.x:.6g}")
        self._append_text(position, "y", f"{mp.y:.6g}")
        self._append_text(position, "z", f"{mp.z:.6g}")

        return mp_elem

    def _build_solution_domain(self, position: Tuple[float, float, float],
                               size: Tuple[float, float, float]) -> ET.Element:
        """构建 solution_domain 节"""
        domain = ET.Element("solution_domain")

        pos = ET.SubElement(domain, "position")
        self._append_text(pos, "x", f"{position[0]:.6g}")
        self._append_text(pos, "y", f"{position[1]:.6g}")
        self._append_text(pos, "z", f"{position[2]:.6g}")

        sz = ET.SubElement(domain, "size")
        self._append_text(sz, "x", f"{size[0]:.6g}")
        self._append_text(sz, "y", f"{size[1]:.6g}")
        self._append_text(sz, "z", f"{size[2]:.6g}")

        for face in (
            "x_low_ambient",
            "x_high_ambient",
            "y_low_ambient",
            "y_high_ambient",
            "z_low_ambient",
            "z_high_ambient",
        ):
            self._append_text(domain, face, self.config.ambient_name)

        self._append_text(domain, "fluid", self.config.fluid_name)

        return domain

    def _build_model(self) -> ET.Element:
        """构建 model 节"""
        model = ET.Element("model")
        cfg = self.config

        # modeling — only write fields that are not None
        modeling = ET.SubElement(model, "modeling")
        for tag, val in (
            ("solution", cfg.solution),
            ("radiation", cfg.radiation),
            ("dimensionality", cfg.dimensionality),
            ("transient", cfg.transient),
            ("store_mass_flux", cfg.store_mass_flux),
            ("store_heat_flux", cfg.store_heat_flux),
            ("store_surface_temp", cfg.store_surface_temp),
            ("store_grad_t", cfg.store_grad_t),
            ("store_bn_sc", cfg.store_bn_sc),
            ("store_power_density", cfg.store_power_density),
            ("store_mean_radiant_temperature", cfg.store_mean_radiant_temperature),
            ("compute_capture_index", cfg.compute_capture_index),
            ("user_defined_subgroups", cfg.user_defined_subgroups),
            ("store_lma", cfg.store_lma),
        ):
            self._write_field(modeling, tag, val)

        # turbulence
        if cfg.turbulence_type is not None or cfg.turbulence_model is not None:
            turbulence = ET.SubElement(model, "turbulence")
            self._write_field(turbulence, "type", cfg.turbulence_type)
            self._write_field(turbulence, "turbulence_type", cfg.turbulence_model)

        # gravity
        if cfg.gravity_direction is not None or cfg.gravity_value is not None:
            gravity = ET.SubElement(model, "gravity")
            self._write_field(gravity, "type", "normal")
            self._write_field(gravity, "normal_direction", cfg.gravity_direction)
            self._write_field(gravity, "value_type", "user")
            self._write_field(gravity, "gravity_value", cfg.gravity_value)

        # global
        if any(v is not None for v in (
            cfg.datum_pressure, cfg.ambient_temp,
        )):
            global_settings = ET.SubElement(model, "global")
            self._write_field(global_settings, "datum_pressure", cfg.datum_pressure)
            if cfg.ambient_temp is not None:
                self._append_text(global_settings, "radiant_temperature", str(cfg.ambient_temp))
                self._append_text(global_settings, "ambient_temperature", str(cfg.ambient_temp))

        return model

    def _build_solve(self) -> ET.Element:
        """构建 solve 节"""
        solve = ET.Element("solve")
        overall = ET.SubElement(solve, "overall_control")
        cfg = self.config

        for tag, val in (
            ("outer_iterations", cfg.outer_iterations),
            ("fan_relaxation", cfg.fan_relaxation),
            ("estimated_free_convection_velocity", cfg.estimated_free_convection_velocity),
            ("solver_option", cfg.solver_option),
            ("active_plate_conduction", cfg.active_plate_conduction),
            ("use_double_precision", cfg.use_double_precision),
            ("network_assembly_block_correction", cfg.network_assembly_block_correction),
            ("freeze_flow", cfg.freeze_flow),
            ("store_error_field", cfg.store_error_field),
        ):
            self._write_field(overall, tag, val)

        return solve

    def _build_grid(self, domain_size: Tuple[float, float, float]) -> ET.Element:
        """构建 grid 节"""
        if self._grid_config:
            return self._build_grid_from_config()
        return self._build_grid_auto(domain_size)

    def _load_grid_config(self, filepath: str) -> None:
        """加载网格配置文件"""
        try:
            from .grid_config import GridExcelReader, GridConfig
            reader = GridExcelReader(filepath)
            self._grid_config = reader.read_config()
            print(f"[INFO] 已加载网格配置: {filepath}")
        except ImportError:
            print(f"[WARN] 无法加载网格配置: 需要 openpyxl 或 pandas")
        except Exception as e:
            print(f"[WARN] 加载网格配置失败: {e}")

    def _build_grid_from_config(self) -> ET.Element:
        """从配置构建 grid"""
        from .grid_config import GridBuilder
        builder = GridBuilder()
        return builder.build_grid(self._grid_config)

    def _build_grid_auto(self, domain_size: Tuple[float, float, float]) -> ET.Element:
        """自动计算并构建 grid"""
        x_size, y_size, z_size = domain_size
        cfg = self.config

        grid = ET.Element("grid")
        system_grid = ET.SubElement(grid, "system_grid")

        self._append_text(system_grid, "smoothing", "true")
        self._write_field(system_grid, "smoothing_type", cfg.grid_smoothing_type)
        self._append_text(system_grid, "dynamic_update", "true")

        # Grid axis divisors default to None — fall back only when building axis
        min_div = cfg.grid_min_divisor if cfg.grid_min_divisor is not None else 100.0
        max_div = cfg.grid_max_divisor if cfg.grid_max_divisor is not None else 12.0

        def grid_axis(parent: ET.Element, tag: str, size: float):
            axis = ET.SubElement(parent, tag)
            min_sz = min(max(size / min_div, 1e-4), 0.001)
            max_sz = max(size / max_div, 0.001)
            self._append_text(axis, "min_size", f"{min_sz:.6g}")
            self._append_text(axis, "grid_type", "max_size")
            self._append_text(axis, "max_size", f"{max_sz:.6g}")
            self._write_field(axis, "smoothing_value", cfg.grid_smoothing_value)

        grid_axis(system_grid, "x_grid", x_size)
        grid_axis(system_grid, "y_grid", y_size)
        grid_axis(system_grid, "z_grid", z_size)

        return grid

    def _build_identity_orientation(self, parent: ET.Element) -> ET.Element:
        """构建单位方向矩阵。"""
        orientation = ET.SubElement(parent, "orientation")
        local_x = ET.SubElement(orientation, "local_x")
        self._append_text(local_x, "i", "1")
        self._append_text(local_x, "j", "0")
        self._append_text(local_x, "k", "0")
        local_y = ET.SubElement(orientation, "local_y")
        self._append_text(local_y, "i", "0")
        self._append_text(local_y, "j", "1")
        self._append_text(local_y, "k", "0")
        local_z = ET.SubElement(orientation, "local_z")
        self._append_text(local_z, "i", "0")
        self._append_text(local_z, "j", "0")
        self._append_text(local_z, "k", "1")
        return orientation

    def _apply_grid_constraints(self, elem: ET.Element, assembly_name: str) -> None:
        """根据配置应用网格约束到元素"""
        if not self._grid_config or not self._grid_config.assembly_constraints:
            return

        import fnmatch

        for mapping in self._grid_config.assembly_constraints:
            if fnmatch.fnmatch(assembly_name, mapping.assembly_name):
                if mapping.all_constraint:
                    self._append_text(elem, "all_grid_constraint", mapping.all_constraint)
                else:
                    if mapping.x_constraint:
                        self._append_text(elem, "x_grid_constraint", mapping.x_constraint)
                    if mapping.y_constraint:
                        self._append_text(elem, "y_grid_constraint", mapping.y_constraint)
                    if mapping.z_constraint:
                        self._append_text(elem, "z_grid_constraint", mapping.z_constraint)
                break

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

            # 解析 ECXML（使用新的完整提取方法）
            extractor = ECXMLExtractor(str(input_path))
            ecxml_data = extractor.extract_all()

            # 收集所有组件用于统计
            components = extractor.extract_components()
            if not components:
                result["warnings"].append("未找到任何组件")

            # 构建 FloXML
            builder = FloXMLBuilder(self.config)
            root = builder.build_project(ecxml_data)

            # 注入 JSON 配置（surface、radiation、fan、thermal 等）
            if self.config.config_file:
                from .config_injector import ConfigInjector
                injector = ConfigInjector(self.config.config_file)
                injector.inject(root)

            # 如果提供了源 FloXML，注入网格设置
            if self.config.floxml_source:
                self._inject_grid_from_floxml(root, self.config.floxml_source)

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

    def _inject_grid_from_floxml(self, root: ET.Element, source_path: str) -> None:
        """从源 PDML/FloXML 提取网格设置并注入到目标 root

        支持三种格式：
        1. XML 格式的 FloXML/PDML（直接解析）
        2. 二进制 PDML（#FFFB 头，尝试从 .pack/ZIP 中提取 FloXML）
        3. .pack ZIP 压缩包（提取内部 XML）
        """
        from copy import deepcopy
        import zipfile
        import tempfile

        src_root = self._parse_pdml_source(source_path)
        if src_root is None:
            print("[WARN] 无法解析源文件，跳过网格注入")
            return

        def _find_child(parent, tag):
            child = parent.find(tag)
            if child is not None:
                return child
            for c in parent:
                if c.tag.split('}')[1] if '}' in c.tag else c.tag == tag:
                    return c
            return None

        def _strip_ns(tag):
            return tag.split('}')[1] if '}' in tag else tag

        def _remove_child(parent, tag):
            child = _find_child(parent, tag)
            if child is not None:
                parent.remove(child)

        # 注入 <grid>（system_grid + patches）
        src_grid = _find_child(src_root, 'grid')
        if src_grid is not None:
            _remove_child(root, 'grid')
            root.insert(0, deepcopy(src_grid))
            print(f"[OK] 已注入 <grid> (system_grid + patches)")
        else:
            print("[WARN] 源 FloXML 中未找到 <grid>")

        # 注入 <grid_constraints>
        src_gc = _find_child(src_root, 'grid_constraints')
        if src_gc is None:
            src_attrs = _find_child(src_root, 'attributes')
            if src_attrs is not None:
                src_gc = _find_child(src_attrs, 'grid_constraints')
        if src_gc is not None:
            tgt_attrs = _find_child(root, 'attributes')
            if tgt_attrs is not None:
                _remove_child(tgt_attrs, 'grid_constraints')
                tgt_attrs.append(deepcopy(src_gc))
            else:
                _remove_child(root, 'grid_constraints')
                root.append(deepcopy(src_gc))
            count = sum(1 for c in src_gc if _strip_ns(c.tag) == 'grid_constraint_att')
            print(f"[OK] 已注入 <grid_constraints> ({count} 个约束)")
        else:
            print("[WARN] 源 FloXML 中未找到 <grid_constraints>")

        # 注入 region（网格区域定义，引用 grid_constraint）
        # 递归收集源中所有 region（可能嵌套在 assembly/geometry 内）
        src_geo = _find_child(src_root, 'geometry')
        tgt_geo = _find_child(root, 'geometry')
        if src_geo is not None and tgt_geo is not None:
            src_regions = list(src_geo.iter('region'))
            if src_regions:
                # 按层级注入：顶层的 region 放到目标顶层，嵌套的按 assembly name 匹配
                injected = 0
                for src_reg in src_regions:
                    reg_copy = deepcopy(src_reg)
                    name_el = reg_copy.find('name')
                    reg_name = name_el.text if name_el is not None else ''

                    # 判断是否在顶层 geometry 下
                    parent = None
                    for p in src_geo.iter():
                        if src_reg in list(p):
                            parent = p
                            break
                    is_top_level = (parent is src_geo)

                    if is_top_level:
                        # 注入到目标顶层 geometry
                        for c in list(tgt_geo):
                            if c.tag == 'region':
                                n2 = c.find('name')
                                if n2 is not None and n2.text == reg_name:
                                    tgt_geo.remove(c)
                                    break
                        tgt_geo.append(reg_copy)
                        injected += 1
                    else:
                        # 嵌套 region：找到源中所属的 assembly name，在目标中找同名 assembly 注入
                        # 向上找父 assembly
                        asm_name = None
                        for p in src_geo.iter():
                            if p.tag == 'assembly' and src_reg in list(p.iter()):
                                if p is not src_reg:
                                    pn = p.find('name')
                                    if pn is not None:
                                        asm_name = pn.text
                                        break
                        if asm_name:
                            # 在目标中找同名 assembly
                            for tgt_asm in tgt_geo.iter('assembly'):
                                tn = tgt_asm.find('name')
                                if tn is not None and tn.text == asm_name:
                                    tgt_asm_geo = tgt_asm.find('geometry')
                                    if tgt_asm_geo is None:
                                        tgt_asm_geo = ET.SubElement(tgt_asm, 'geometry')
                                    # 移除同名旧 region
                                    for c in list(tgt_asm_geo):
                                        if c.tag == 'region':
                                            n2 = c.find('name')
                                            if n2 is not None and n2.text == reg_name:
                                                tgt_asm_geo.remove(c)
                                                break
                                    tgt_asm_geo.append(reg_copy)
                                    injected += 1
                                    break
                print(f"[OK] 已注入 {injected} 个 <region>")
            else:
                print("[WARN] 源 FloXML <geometry> 中未找到 <region>")
        else:
            if src_geo is None:
                print("[WARN] 源 FloXML 中未找到 <geometry>")
            if tgt_geo is None:
                print("[WARN] 目标 FloXML 中未找到 <geometry>")

    def _parse_pdml_source(self, source_path: str) -> Optional[ET.Element]:
        """解析源 PDML/FloXML 文件，返回 root Element

        支持格式：
        1. XML 文本（FloXML / XML 格式的 PDML）→ 直接解析
        2. 二进制 PDML（#FFFB 头）→ 尝试 ZIP 提取内部 XML
        3. .pack 文件（ZIP）→ 提取内部 XML
        """
        import zipfile
        import tempfile

        # 1) 尝试直接作为 XML 解析
        try:
            tree = ET.parse(source_path)
            print(f"[OK] 已解析源文件 (XML): {source_path}")
            return tree.getroot()
        except ET.ParseError:
            pass

        # 2) 非 XML，尝试作为 ZIP（.pack 或 ZIP 格式的 PDML）
        try:
            with zipfile.ZipFile(source_path, 'r') as zf:
                # 查找 PDProject 下的 group 文件，判断是否为 .pack
                names = zf.namelist()
                is_pack = any('PDProject/group' in n for n in names)

                if is_pack:
                    print(f"[ERROR] .pack 文件中的项目定义是二进制 PDML 格式，无法提取网格设置")
                    print(f"  请在 FloTHERM 中打开项目后导出 FloXML，再用 --pdml 指定导出的文件")
                    return None

                # 其他 ZIP：查找内部的 XML 文件
                xml_candidates = [
                    n for n in names
                    if n.endswith(('.xml', '.pdml', '.floxml'))
                ]
                if not xml_candidates:
                    print(f"[WARN] ZIP 中未找到 XML 文件: {source_path}")
                    return None

                xml_candidates.sort(key=lambda n: zf.getinfo(n).file_size, reverse=True)
                with zf.open(xml_candidates[0]) as xf:
                    tree = ET.parse(xf)
                print(f"[OK] 已从 ZIP 中提取: {xml_candidates[0]}")
                return tree.getroot()
        except zipfile.BadZipFile:
            pass

        # 3) 二进制 PDML（#FFFB 头），使用 PDML 解析器
        with open(source_path, 'rb') as f:
            header = f.read(64)

        if header[:5] == b'#FFFB':
            print(f"[INFO] 检测到二进制 PDML 文件，使用 PDML 解析器提取网格...")
            try:
                import importlib
                import sys
                _parent = str(Path(__file__).resolve().parent.parent)
                if _parent not in sys.path:
                    sys.path.insert(0, _parent)
                _pdml_mod = importlib.import_module('pdml_tools.pdml_to_floxml_converter')
                _PDMLReader = _pdml_mod.PDMLBinaryReader
                _PDMLFloXMLBuilder = _pdml_mod.FloXMLBuilder
                reader = _PDMLReader(source_path)
                pdml_data = reader.read()
                builder = _PDMLFloXMLBuilder()
                pdml_root = builder.build(pdml_data)
                print(f"[OK] 已从二进制 PDML 提取网格设置")
                return pdml_root
            except Exception as e:
                print(f"[ERROR] PDML 解析失败: {e}")
                return None
        else:
            print(f"[ERROR] 无法识别文件格式: {source_path}")

        return None

    def _write_floxml(self, root: ET.Element, output_path: Path) -> None:
        """写入 FloXML 文件"""
        tree = ET.ElementTree(root)
        self._indent_xml(tree.getroot())

        xml_bytes = ET.tostring(root, encoding="utf-8")
        text = '<?xml version="1.0" encoding="UTF-8" standalone="no" ?>\n' + xml_bytes.decode("utf-8")

        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(text, encoding="utf-8")

    def _indent_xml(self, elem: ET.Element, level: int = 0, space: str = "    ") -> None:
        """兼容 Python 3.8 的 XML 缩进。"""
        try:
            ET.indent(elem, space=space, level=level)
            return
        except AttributeError:
            pass

        indent = "\n" + level * space
        child_indent = "\n" + (level + 1) * space
        children = list(elem)

        if children:
            if not elem.text or not elem.text.strip():
                elem.text = child_indent
            for child in children:
                self._indent_xml(child, level + 1, space)
                if not child.tail or not child.tail.strip():
                    child.tail = child_indent
            if not children[-1].tail or not children[-1].tail.strip():
                children[-1].tail = indent
        elif level and (not elem.tail or not elem.tail.strip()):
            elem.tail = indent

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

    # 模型设置
    model_group = parser.add_argument_group("model", "模型设置")
    model_group.add_argument("--radiation", choices=["off", "on"], default=None,
                             help="辐射模型")
    model_group.add_argument("--turbulence-model",
                             choices=["auto_algebraic", "k_epsilon", "zero_equation", "laminar"],
                             default=None,
                             help="湍流模型")
    model_group.add_argument("--gravity-direction",
                             choices=["neg_y", "pos_y", "neg_z", "pos_z", "neg_x", "pos_x"],
                             default=None,
                             help="重力方向")
    model_group.add_argument("--gravity-value", type=float, default=None,
                             help="重力加速度 m/s²")
    model_group.add_argument("--datum-pressure", type=float, default=None,
                             help="大气压 Pa")

    # 求解器设置
    solve_group = parser.add_argument_group("solve", "求解器设置")
    solve_group.add_argument("--solver-option",
                             choices=["multi_grid", "simple", "conjugate_gradient"],
                             default=None,
                             help="求解器选项")
    solve_group.add_argument("--use-double-precision", action="store_true", default=None,
                             help="使用双精度求解")

    # 流体属性
    fluid_group = parser.add_argument_group("fluid", "流体属性")
    fluid_group.add_argument("--fluid-conductivity", type=float, default=None,
                             help="流体热导率 W/(m·K)")
    fluid_group.add_argument("--fluid-viscosity", type=float, default=None,
                             help="流体动力粘度 Pa·s")
    fluid_group.add_argument("--fluid-density", type=float, default=None,
                             help="流体密度 kg/m³")
    fluid_group.add_argument("--fluid-specific-heat", type=float, default=None,
                             help="流体比热 J/(kg·K)")
    fluid_group.add_argument("--fluid-expansivity", type=float, default=None,
                             help="流体膨胀系数 1/K")

    # 网格配置
    parser.add_argument("--grid-config", type=str,
                        help="Excel 网格配置文件路径")

    # JSON 设置（覆盖 ConversionConfig 字段）
    parser.add_argument("--settings", type=str,
                        help="JSON 设置文件路径，覆盖模型/求解/流体等参数")

    # 统一 JSON 配置（注入 surface/radiation/fan/thermal/resistance 等）
    parser.add_argument("--config", type=str,
                        help="统一 JSON 配置文件路径（注入属性定义和分配）")

    # 源 PDML/FloXML（提取网格）
    parser.add_argument("--pdml", type=str,
                        help="源 PDML 或 FloXML 文件路径，用于提取网格设置")

    # 模板配置
    parser.add_argument("--template", type=str,
                        help="FloXML 模板 JSON 文件路径")

    # 其他选项
    parser.add_argument("-v", "--verbose", action="store_true",
                        help="详细输出")

    return parser


def main(argv: Optional[Iterable[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)

    # 构建配置：--settings JSON → CLI args 覆盖 → apply_defaults 兜底
    if args.template:
        config = ConversionConfig.from_template(args.template)
        if args.verbose:
            print(f"[INFO] 使用模板: {args.template}")
    elif args.settings:
        config = ConversionConfig.from_json(args.settings)
        if args.verbose:
            print(f"[INFO] 使用设置文件: {args.settings} (仅输出 JSON 中指定的字段)")
        # CLI 参数可覆盖 JSON
        config.merge_cli_args(args)
    else:
        # 无 JSON / 无 template — 用 CLI 参数构建，缺省填 FloTHERM 默认值
        config = ConversionConfig(
            padding_ratio=args.padding_ratio,
            minimum_padding=args.minimum_padding,
            ambient_temp=args.ambient_temp,
            outer_iterations=args.outer_iterations,
        )
        config.apply_defaults()
        # CLI 显式指定的参数覆盖 defaults
        config.merge_cli_args(args)

    # 确保 external config sources 始终从 CLI 传入
    if args.grid_config:
        config.grid_config_file = args.grid_config
    if args.pdml:
        config.floxml_source = args.pdml
    if args.config:
        config.config_file = args.config

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
