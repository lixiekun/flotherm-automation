#!/usr/bin/env python3
"""
PDML to FloXML Converter

将 FloTHERM PDML 二进制文件转换为 FloXML 项目格式。

PDML 是 FloTHERM 原生二进制格式，包含完整的模型数据：
- 模型设置 (model)
- 求解器配置 (solve)
- 网格设置 (grid)
- 几何体层级 (geometry)
- 属性定义 (attributes)
- 求解域 (solution_domain)

本工具解析 PDML 二进制格式并生成等效的 FloXML。
"""

from __future__ import annotations

import argparse
import struct
import json
import sys
from pathlib import Path
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any
from xml.dom import minidom
import xml.etree.ElementTree as ET


# ============================================================================
# 数据类定义
# ============================================================================

@dataclass
class PDMLModelSettings:
    """PDML 模型设置"""
    solution: str = "flow_heat"
    radiation: str = "off"
    dimensionality: str = "3d"
    transient: bool = False
    turbulence_type: str = "turbulent"
    turbulence_model: str = "auto_algebraic"
    gravity_type: str = "normal"
    gravity_direction: str = "neg_y"
    gravity_value: float = 9.81
    datum_pressure: float = 101325.0
    ambient_temperature: float = 300.0
    radiant_temperature: float = 300.0


@dataclass
class PDMLSolveSettings:
    """PDML 求解设置"""
    outer_iterations: int = 500
    fan_relaxation: float = 1.0
    estimated_free_convection_velocity: float = 0.2
    solver_option: str = "multi_grid"


@dataclass
class PDMLGridAxis:
    """PDML 网格轴设置"""
    min_size: float = 0.001
    max_size: float = 0.01
    grid_type: str = "max_size"
    smoothing_value: int = 12


@dataclass
class PDMLGridSettings:
    """PDML 网格设置"""
    smoothing: bool = True
    smoothing_type: str = "v3"
    dynamic_update: bool = True
    x_grid: PDMLGridAxis = field(default_factory=PDMLGridAxis)
    y_grid: PDMLGridAxis = field(default_factory=PDMLGridAxis)
    z_grid: PDMLGridAxis = field(default_factory=PDMLGridAxis)


@dataclass
class PDMLMaterial:
    """PDML 材料定义"""
    name: str
    conductivity: float = 1.0
    density: float = 1.0
    specific_heat: float = 1.0
    conductivity_type: str = "isotropic"


@dataclass
class PDMLSource:
    """PDML 热源定义"""
    name: str
    power: float = 0.0


@dataclass
class PDMLAmbient:
    """PDML 环境定义"""
    name: str
    temperature: float = 300.0
    heat_transfer_coeff: float = 0.0
    velocity: Tuple[float, float, float] = (0.0, 0.0, 0.0)


@dataclass
class PDMLFluid:
    """PDML 流体定义"""
    name: str = "Air"
    conductivity: float = 0.0261
    viscosity: float = 0.0000184
    density: float = 1.16
    specific_heat: float = 1008.0
    expansivity: float = 0.003


@dataclass
class PDMLGeometryNode:
    """PDML 几何节点（assembly 或 cuboid）"""
    node_type: str  # 'assembly' or 'cuboid'
    name: str
    position: Tuple[float, float, float] = (0.0, 0.0, 0.0)
    size: Optional[Tuple[float, float, float]] = None  # for cuboids
    material: Optional[str] = None
    source: Optional[str] = None
    active: bool = True
    children: List['PDMLGeometryNode'] = field(default_factory=list)


@dataclass
class PDMLSolutionDomain:
    """PDML 求解域"""
    position: Tuple[float, float, float] = (0.0, 0.0, 0.0)
    size: Tuple[float, float, float] = (0.1, 0.1, 0.1)
    x_low_ambient: str = "Ambient"
    x_high_ambient: str = "Ambient"
    y_low_ambient: str = "Ambient"
    y_high_ambient: str = "Ambient"
    z_low_ambient: str = "Ambient"
    z_high_ambient: str = "Ambient"
    fluid: str = "Air"


@dataclass
class PDMLData:
    """完整的 PDML 数据"""
    name: str = "Project"
    version: str = ""
    product: str = ""
    model: PDMLModelSettings = field(default_factory=PDMLModelSettings)
    solve: PDMLSolveSettings = field(default_factory=PDMLSolveSettings)
    grid: PDMLGridSettings = field(default_factory=PDMLGridSettings)
    materials: List[PDMLMaterial] = field(default_factory=list)
    sources: List[PDMLSource] = field(default_factory=list)
    ambients: List[PDMLAmbient] = field(default_factory=list)
    fluids: List[PDMLFluid] = field(default_factory=list)
    geometry: Optional[PDMLGeometryNode] = None
    solution_domain: PDMLSolutionDomain = field(default_factory=PDMLSolutionDomain)


# ============================================================================
# PDML 二进制读取器
# ============================================================================

class PDMLBinaryReader:
    """PDML 二进制格式读取器"""

    # 枚举值映射
    ENUM_VALUES = {
        257: True,   # true / on / yes
        258: False,  # false / off / no
        259: 'option_3',
        260: 'option_4',
        261: 'option_5',
        262: 'option_6',
    }

    # 类型代码映射
    TYPE_CODES = {
        0x0000: 'unknown_flag', 0x0001: 'count_value', 0x0005: 'index_value',
        0x0009: 'id_value', 0x000A: 'option_index',
        0x1000: 'store_option', 0x1004: 'store_flag_1', 0x1005: 'store_flag_2',
        0x1007: 'turbulence_flag', 0x100C: 'mesh_option',
        0x2000: 'grid_flag_1', 0x2001: 'grid_flag_2', 0x2004: 'grid_store_flag',
        0x2006: 'grid_constraint', 0x2009: 'grid_option_1', 0x200B: 'grid_option_2',
        0x3000: 'dimensionality_flag', 0x3001: 'dimensionality',
        0x5000: 'smoothing_flag', 0x5008: 'smoothing_value',
        0x7000: 'gravity_direction', 0x7004: 'gravity_option_1',
        0x8000: 'gravity_type', 0x8002: 'pressure_option',
        0x9000: 'convergence_flag', 0x9001: 'monitor_flag',
        0xA000: 'boolean_main_flag', 0xA006: 'boolean_flag',
        0xB000: 'outer_iterations', 0xB004: 'outer_iterations_2',
        0xC000: 'fan_relaxation_type', 0xC005: 'solver_option',
        0xE000: 'grid_type', 0xE003: 'smoothing_type', 0xE007: 'dynamic_update',
    }

    # Section 标记字符串
    SECTION_MARKERS = {
        'gravity': 'model',
        'overall control': 'solve',
        'grid smooth': 'grid',
        'modeldata': 'attributes',
        'solution domain': 'solution_domain',
        'geometry': 'geometry',
    }

    def __init__(self, filepath: str):
        self.filepath = filepath
        with open(filepath, 'rb') as f:
            self.data = f.read()

        self.strings: Dict[int, str] = {}
        self.fields: List[Dict] = []
        self.sections: Dict[str, int] = {}  # section_name -> offset

    def read(self) -> PDMLData:
        """读取 PDML 文件并返回结构化数据"""
        result = PDMLData()

        # 解析头部
        header = self._parse_header()
        result.version = header.get('version', '')
        result.product = header.get('product', '')
        result.name = Path(self.filepath).stem

        # 提取所有字符串
        self._extract_strings()

        # 定位 section 边界
        self._locate_sections()

        # 提取各 section 数据
        self._extract_model_settings(result.model)
        self._extract_solve_settings(result.solve)
        self._extract_grid_settings(result.grid)
        self._extract_attributes(result)
        self._extract_geometry(result)
        self._extract_solution_domain(result.solution_domain)

        return result

    def _parse_header(self) -> Dict[str, str]:
        """解析文件头部"""
        newline_pos = self.data.find(b'\n')
        if newline_pos < 0:
            return {'error': 'Invalid PDML file'}

        header_line = self.data[:newline_pos].decode('ascii', errors='replace')
        parts = header_line.split()

        return {
            'format': parts[0] if len(parts) > 0 else '',
            'version': parts[1] if len(parts) > 1 else '',
            'product': ' '.join(parts[2:]) if len(parts) > 2 else ''
        }

    def _extract_strings(self):
        """提取所有字符串块 - 修复版本，使用大端序解析长度"""
        pos = 0
        while pos < len(self.data) - 10:
            if self.data[pos:pos+2] == b'\x07\x02':
                if pos + 10 <= len(self.data):
                    # 使用大端序解析长度
                    length = struct.unpack('>I', self.data[pos+6:pos+10])[0]
                    if 0 < length < 1000 and pos + 10 + length <= len(self.data):
                        str_data = self.data[pos+10:pos+10+length]
                        try:
                            value = str_data.decode('utf-8', errors='replace')
                            if value.strip():
                                self.strings[pos] = value.strip()
                        except:
                            pass
            pos += 1

    def _locate_sections(self):
        """定位各 section 的位置"""
        for offset, s in self.strings.items():
            s_lower = s.lower()
            for marker, section in self.SECTION_MARKERS.items():
                if marker.lower() in s_lower:
                    if section not in self.sections:
                        self.sections[section] = offset

    def _find_nearby_string(self, pos: int, search_range: int = 200) -> Optional[str]:
        """在指定位置附近查找字符串"""
        for offset in range(10, search_range, 10):
            check_pos = pos - offset
            if check_pos in self.strings:
                s = self.strings[check_pos]
                # 过滤掉 GUID
                if len(s) == 32 and all(c in '0123456789ABCDEFabcdef' for c in s):
                    continue
                if len(s) > 3:
                    return s
        return None

    def _extract_double_at(self, pos: int) -> Optional[float]:
        """在指定位置提取 double 值"""
        if pos < 0 or pos + 9 > len(self.data):
            return None
        if self.data[pos] == 0x06:
            try:
                return struct.unpack('>d', self.data[pos+1:pos+9])[0]
            except:
                pass
        return None

    def _find_double_near(self, pos: int, range_size: int = 100) -> List[Tuple[int, float]]:
        """在指定位置附近查找所有 double 值"""
        results = []
        start = max(0, pos - range_size)
        end = min(len(self.data) - 9, pos + range_size)

        for p in range(start, end):
            val = self._extract_double_at(p)
            if val is not None and -1e15 < val < 1e15 and abs(val) > 1e-15:
                results.append((p, val))

        return results

    def _extract_model_settings(self, model: PDMLModelSettings):
        """提取模型设置"""
        # 查找 gravity section
        if 'model' in self.sections:
            section_start = self.sections['model']
            # 在附近查找 gravity 值 (9.81)
            doubles = self._find_double_near(section_start, 200)
            for pos, val in doubles:
                if 9.5 < val < 10.0:
                    model.gravity_value = val
                    break

        # 查找 ambient temperature (300K)
        for pos, s in self.strings.items():
            if 'ambient' in s.lower() or 'temperature' in s.lower():
                doubles = self._find_double_near(pos, 100)
                for dpos, val in doubles:
                    if 250 < val < 350:
                        model.ambient_temperature = val
                        model.radiant_temperature = val
                        break

        # 查找 datum pressure (101325 Pa)
        for pos, s in self.strings.items():
            if 'pressure' in s.lower() or 'datum' in s.lower():
                doubles = self._find_double_near(pos, 100)
                for dpos, val in doubles:
                    if 100000 < val < 102000:
                        model.datum_pressure = val
                        break

    def _extract_solve_settings(self, solve: PDMLSolveSettings):
        """提取求解设置"""
        if 'solve' in self.sections:
            section_start = self.sections['solve']
            # 查找 outer_iterations (500)
            doubles = self._find_double_near(section_start, 300)
            for pos, val in doubles:
                if 100 < val < 2000 and val == int(val):
                    solve.outer_iterations = int(val)
                    break

    def _extract_grid_settings(self, grid: PDMLGridSettings):
        """提取网格设置"""
        if 'grid' in self.sections:
            section_start = self.sections['grid']
            # 查找网格相关值
            doubles = self._find_double_near(section_start, 500)
            for pos, val in doubles:
                # 查找 min_size (通常很小)
                if 0.0001 < val < 0.01:
                    if grid.x_grid.min_size == 0.001:
                        grid.x_grid.min_size = val
                # 查找 max_size
                if 0.001 < val < 0.1:
                    if grid.x_grid.max_size == 0.01:
                        grid.x_grid.max_size = val

    def _extract_attributes(self, data: PDMLData):
        """提取属性定义"""
        # 添加默认材料
        data.materials = [
            PDMLMaterial(name="Air", conductivity=0.0261, density=1.16, specific_heat=1008),
            PDMLMaterial(name="Default", conductivity=1.0, density=1.0, specific_heat=1.0),
        ]

        # 添加默认环境
        data.ambients = [
            PDMLAmbient(name="Ambient", temperature=data.model.ambient_temperature)
        ]

        # 添加默认流体
        data.fluids = [
            PDMLFluid(name="Air")
        ]

        # 尝试从字符串中提取材料名
        material_names = set()
        for pos, s in self.strings.items():
            if any(kw in s.lower() for kw in ['aluminum', 'copper', 'steel', 'plastic', 'fr4', 'ceramic']):
                material_names.add(s)
            elif 'material' in s.lower():
                # 可能是材料名
                if len(s) > 3 and len(s) < 50:
                    material_names.add(s)

        for name in material_names:
            if not any(m.name == name for m in data.materials):
                data.materials.append(PDMLMaterial(name=name))

    def _extract_geometry(self, data: PDMLData):
        """提取几何体层级"""
        # 创建根 assembly
        root = PDMLGeometryNode(
            node_type='assembly',
            name=data.name,
            position=(0.0, 0.0, 0.0)
        )

        # 尝试从字符串中提取几何体信息
        cuboid_names = []
        assembly_names = []

        for pos, s in self.strings.items():
            s_lower = s.lower()
            if 'assembly' in s_lower or 'modeldata' in s_lower:
                if len(s) > 3 and len(s) < 100:
                    assembly_names.append((pos, s))
            elif 'cuboid' in s_lower or 'block' in s_lower or 'plate' in s_lower:
                if len(s) > 3 and len(s) < 100:
                    cuboid_names.append((pos, s))

        # 简单处理：将找到的名称添加为 cuboids
        for pos, name in cuboid_names[:20]:  # 限制数量
            # 尝试在附近查找位置和尺寸
            doubles = self._find_double_near(pos, 100)
            coords = [v for p, v in doubles if -10 < v < 10][:6]

            if len(coords) >= 3:
                cuboid = PDMLGeometryNode(
                    node_type='cuboid',
                    name=name,
                    position=(coords[0] if len(coords) > 0 else 0.0,
                              coords[1] if len(coords) > 1 else 0.0,
                              coords[2] if len(coords) > 2 else 0.0),
                    size=(coords[3] if len(coords) > 3 else 0.01,
                          coords[4] if len(coords) > 4 else 0.01,
                          coords[5] if len(coords) > 5 else 0.01)
                )
                root.children.append(cuboid)

        # 如果没有找到任何几何体，创建一个默认的
        if not root.children:
            default_cuboid = PDMLGeometryNode(
                node_type='cuboid',
                name='Default_Block',
                position=(0.0, 0.0, 0.0),
                size=(0.01, 0.01, 0.01)
            )
            root.children.append(default_cuboid)

        data.geometry = root

    def _extract_solution_domain(self, domain: PDMLSolutionDomain):
        """提取求解域"""
        if 'solution_domain' in self.sections:
            section_start = self.sections['solution_domain']
            # 查找位置和尺寸
            doubles = self._find_double_near(section_start, 300)

            # 过滤合理的坐标和尺寸值
            coords = []
            sizes = []
            for pos, val in doubles:
                if -1 < val < 1:
                    coords.append(val)
                elif 0.01 < val < 10:
                    sizes.append(val)

            if len(coords) >= 3:
                domain.position = (coords[0], coords[1], coords[2])
            if len(sizes) >= 3:
                domain.size = (sizes[0], sizes[1], sizes[2])


# ============================================================================
# FloXML 生成器
# ============================================================================

class FloXMLBuilder:
    """构建 FloXML 项目文件"""

    def __init__(self):
        pass

    def _append_text(self, parent: ET.Element, tag: str, text: str) -> ET.Element:
        """添加带文本的子元素"""
        elem = ET.SubElement(parent, tag)
        elem.text = text
        return elem

    def _build_identity_orientation(self, parent: ET.Element) -> ET.Element:
        """构建单位方向矩阵"""
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

    def build(self, data: PDMLData) -> ET.Element:
        """构建完整的 FloXML 项目"""
        root = ET.Element("xml_case")

        # 项目名称
        self._append_text(root, "name", data.name)

        # 模型设置
        root.append(self._build_model(data.model))

        # 求解设置
        root.append(self._build_solve(data.solve))

        # 网格设置
        root.append(self._build_grid(data.grid, data.solution_domain.size))

        # 属性
        root.append(self._build_attributes(data))

        # 几何体
        root.append(self._build_geometry(data.geometry))

        # 求解域 (必须在根级别)
        root.append(self._build_solution_domain(data.solution_domain))

        return root

    def _build_model(self, model: PDMLModelSettings) -> ET.Element:
        """构建 model 节"""
        elem = ET.Element("model")

        # modeling
        modeling = ET.SubElement(elem, "modeling")
        self._append_text(modeling, "solution", model.solution)
        self._append_text(modeling, "radiation", model.radiation)
        self._append_text(modeling, "dimensionality", model.dimensionality)
        self._append_text(modeling, "transient", str(model.transient).lower())
        self._append_text(modeling, "store_mass_flux", "false")
        self._append_text(modeling, "store_heat_flux", "false")
        self._append_text(modeling, "store_surface_temp", "false")
        self._append_text(modeling, "store_grad_t", "false")
        self._append_text(modeling, "store_bn_sc", "false")
        self._append_text(modeling, "store_power_density", "false")
        self._append_text(modeling, "store_mean_radiant_temperature", "false")
        self._append_text(modeling, "compute_capture_index", "false")
        self._append_text(modeling, "user_defined_subgroups", "false")
        self._append_text(modeling, "store_lma", "false")

        # turbulence
        turbulence = ET.SubElement(elem, "turbulence")
        self._append_text(turbulence, "type", model.turbulence_type)
        self._append_text(turbulence, "turbulence_type", model.turbulence_model)

        # gravity
        gravity = ET.SubElement(elem, "gravity")
        self._append_text(gravity, "type", model.gravity_type)
        self._append_text(gravity, "normal_direction", model.gravity_direction)
        self._append_text(gravity, "value_type", "user")
        self._append_text(gravity, "gravity_value", f"{model.gravity_value:.6g}")

        # global
        global_elem = ET.SubElement(elem, "global")
        self._append_text(global_elem, "datum_pressure", f"{model.datum_pressure:.6g}")
        self._append_text(global_elem, "radiant_temperature", f"{model.radiant_temperature:.6g}")
        self._append_text(global_elem, "ambient_temperature", f"{model.ambient_temperature:.6g}")
        self._append_text(global_elem, "concentration_1", "0")
        self._append_text(global_elem, "concentration_2", "0")
        self._append_text(global_elem, "concentration_3", "0")
        self._append_text(global_elem, "concentration_4", "0")
        self._append_text(global_elem, "concentration_5", "0")

        return elem

    def _build_solve(self, solve: PDMLSolveSettings) -> ET.Element:
        """构建 solve 节"""
        elem = ET.Element("solve")
        overall = ET.SubElement(elem, "overall_control")

        self._append_text(overall, "outer_iterations", str(solve.outer_iterations))
        self._append_text(overall, "fan_relaxation", f"{solve.fan_relaxation:.6g}")
        self._append_text(overall, "estimated_free_convection_velocity",
                          f"{solve.estimated_free_convection_velocity:.6g}")
        self._append_text(overall, "solver_option", solve.solver_option)
        self._append_text(overall, "active_plate_conduction", "false")
        self._append_text(overall, "use_double_precision", "false")
        self._append_text(overall, "network_assembly_block_correction", "false")
        self._append_text(overall, "freeze_flow", "false")
        self._append_text(overall, "store_error_field", "false")

        return elem

    def _build_grid(self, grid: PDMLGridSettings, domain_size: Tuple[float, float, float]) -> ET.Element:
        """构建 grid 节"""
        elem = ET.Element("grid")
        system_grid = ET.SubElement(elem, "system_grid")

        self._append_text(system_grid, "smoothing", str(grid.smoothing).lower())
        self._append_text(system_grid, "smoothing_type", grid.smoothing_type)
        self._append_text(system_grid, "dynamic_update", str(grid.dynamic_update).lower())

        # 根据求解域大小调整网格
        x_size, y_size, z_size = domain_size

        # x_grid
        x_grid = ET.SubElement(system_grid, "x_grid")
        self._append_text(x_grid, "min_size", f"{min(x_size/1000, 0.001):.6g}")
        self._append_text(x_grid, "grid_type", grid.x_grid.grid_type)
        self._append_text(x_grid, "max_size", f"{max(x_size/12, 0.001):.6g}")
        self._append_text(x_grid, "smoothing_value", str(grid.x_grid.smoothing_value))

        # y_grid
        y_grid = ET.SubElement(system_grid, "y_grid")
        self._append_text(y_grid, "min_size", f"{min(y_size/1000, 0.001):.6g}")
        self._append_text(y_grid, "grid_type", grid.y_grid.grid_type)
        self._append_text(y_grid, "max_size", f"{max(y_size/12, 0.001):.6g}")
        self._append_text(y_grid, "smoothing_value", str(grid.y_grid.smoothing_value))

        # z_grid
        z_grid = ET.SubElement(system_grid, "z_grid")
        self._append_text(z_grid, "min_size", f"{min(z_size/1000, 0.001):.6g}")
        self._append_text(z_grid, "grid_type", grid.z_grid.grid_type)
        self._append_text(z_grid, "max_size", f"{max(z_size/12, 0.001):.6g}")
        self._append_text(z_grid, "smoothing_value", str(grid.z_grid.smoothing_value))

        return elem

    def _build_attributes(self, data: PDMLData) -> ET.Element:
        """构建 attributes 节"""
        elem = ET.Element("attributes")

        # materials
        materials = ET.SubElement(elem, "materials")
        for mat in data.materials:
            mat_elem = ET.SubElement(materials, "isotropic_material_att")
            self._append_text(mat_elem, "name", mat.name)
            self._append_text(mat_elem, "conductivity", f"{mat.conductivity:.6g}")
            self._append_text(mat_elem, "density", f"{mat.density:.6g}")
            self._append_text(mat_elem, "specific_heat", f"{mat.specific_heat:.6g}")

        # sources
        sources = ET.SubElement(elem, "sources")
        for src in data.sources:
            src_elem = ET.SubElement(sources, "source_att")
            self._append_text(src_elem, "name", src.name)
            options = ET.SubElement(src_elem, "source_options")
            option = ET.SubElement(options, "option")
            self._append_text(option, "applies_to", "temperature")
            self._append_text(option, "type", "total")
            self._append_text(option, "power", f"{src.power:.6g}")
            self._append_text(option, "linear_coefficient", "0")

        # ambients
        ambients = ET.SubElement(elem, "ambients")
        for amb in data.ambients:
            amb_elem = ET.SubElement(ambients, "ambient_att")
            self._append_text(amb_elem, "name", amb.name)
            self._append_text(amb_elem, "temperature", f"{amb.temperature:.6g}")
            self._append_text(amb_elem, "heat_transfer_coeff", f"{amb.heat_transfer_coeff:.6g}")

            velocity = ET.SubElement(amb_elem, "velocity")
            self._append_text(velocity, "x", f"{amb.velocity[0]:.6g}")
            self._append_text(velocity, "y", f"{amb.velocity[1]:.6g}")
            self._append_text(velocity, "z", f"{amb.velocity[2]:.6g}")

        # fluids
        fluids = ET.SubElement(elem, "fluids")
        for fluid in data.fluids:
            fluid_elem = ET.SubElement(fluids, "fluid_att")
            self._append_text(fluid_elem, "name", fluid.name)
            self._append_text(fluid_elem, "conductivity_type", "constant")
            self._append_text(fluid_elem, "conductivity", f"{fluid.conductivity:.6g}")
            self._append_text(fluid_elem, "viscosity_type", "constant")
            self._append_text(fluid_elem, "viscosity", f"{fluid.viscosity:.6g}")
            self._append_text(fluid_elem, "density_type", "constant")
            self._append_text(fluid_elem, "density", f"{fluid.density:.6g}")
            self._append_text(fluid_elem, "specific_heat", f"{fluid.specific_heat:.6g}")
            self._append_text(fluid_elem, "expansivity", f"{fluid.expansivity:.6g}")

        return elem

    def _build_geometry(self, root_node: PDMLGeometryNode) -> ET.Element:
        """构建 geometry 节"""
        elem = ET.Element("geometry")
        self._build_geometry_node(elem, root_node)
        return elem

    def _build_geometry_node(self, parent: ET.Element, node: PDMLGeometryNode):
        """递归构建几何节点"""
        if node.node_type == 'assembly':
            assembly = ET.SubElement(parent, "assembly")
            self._append_text(assembly, "name", node.name)
            self._append_text(assembly, "active", str(node.active).lower())
            self._append_text(assembly, "ignore", "false")

            # position
            position = ET.SubElement(assembly, "position")
            self._append_text(position, "x", f"{node.position[0]:.6g}")
            self._append_text(position, "y", f"{node.position[1]:.6g}")
            self._append_text(position, "z", f"{node.position[2]:.6g}")

            # orientation
            self._build_identity_orientation(assembly)

            # material
            if node.material:
                self._append_text(assembly, "material", node.material)

            self._append_text(assembly, "localized_grid", "false")

            # 子节点
            if node.children:
                geometry = ET.SubElement(assembly, "geometry")
                for child in node.children:
                    self._build_geometry_node(geometry, child)

        elif node.node_type == 'cuboid':
            cuboid = ET.SubElement(parent, "cuboid")
            self._append_text(cuboid, "name", node.name)
            self._append_text(cuboid, "active", str(node.active).lower())

            # position
            position = ET.SubElement(cuboid, "position")
            self._append_text(position, "x", f"{node.position[0]:.6g}")
            self._append_text(position, "y", f"{node.position[1]:.6g}")
            self._append_text(position, "z", f"{node.position[2]:.6g}")

            # size
            if node.size:
                size = ET.SubElement(cuboid, "size")
                self._append_text(size, "x", f"{node.size[0]:.6g}")
                self._append_text(size, "y", f"{node.size[1]:.6g}")
                self._append_text(size, "z", f"{node.size[2]:.6g}")

            # orientation
            self._build_identity_orientation(cuboid)

            # material
            if node.material:
                self._append_text(cuboid, "material", node.material)

            self._append_text(cuboid, "localized_grid", "false")

    def _build_solution_domain(self, domain: PDMLSolutionDomain) -> ET.Element:
        """构建 solution_domain 节"""
        elem = ET.Element("solution_domain")

        # position
        position = ET.SubElement(elem, "position")
        self._append_text(position, "x", f"{domain.position[0]:.6g}")
        self._append_text(position, "y", f"{domain.position[1]:.6g}")
        self._append_text(position, "z", f"{domain.position[2]:.6g}")

        # size
        size = ET.SubElement(elem, "size")
        self._append_text(size, "x", f"{domain.size[0]:.6g}")
        self._append_text(size, "y", f"{domain.size[1]:.6g}")
        self._append_text(size, "z", f"{domain.size[2]:.6g}")

        # boundary conditions
        self._append_text(elem, "x_low_ambient", domain.x_low_ambient)
        self._append_text(elem, "x_high_ambient", domain.x_high_ambient)
        self._append_text(elem, "y_low_ambient", domain.y_low_ambient)
        self._append_text(elem, "y_high_ambient", domain.y_high_ambient)
        self._append_text(elem, "z_low_ambient", domain.z_low_ambient)
        self._append_text(elem, "z_high_ambient", domain.z_high_ambient)

        # fluid
        self._append_text(elem, "fluid", domain.fluid)

        return elem


# ============================================================================
# 转换器
# ============================================================================

class PDMLToFloXMLConverter:
    """PDML to FloXML 转换器"""

    def __init__(self, input_path: str, output_path: Optional[str] = None):
        self.input_path = Path(input_path)
        self.output_path = Path(output_path) if output_path else self.input_path.with_suffix('.xml')

    def convert(self) -> bool:
        """执行转换"""
        print(f"[INFO] 读取 PDML: {self.input_path}")

        # 读取 PDML
        reader = PDMLBinaryReader(str(self.input_path))
        data = reader.read()

        print(f"[INFO] 项目: {data.name}")
        print(f"[INFO] 版本: {data.product}")
        print(f"[INFO] 重力: {data.model.gravity_value} m/s²")
        print(f"[INFO] 迭代: {data.solve.outer_iterations}")
        print(f"[INFO] 温度: {data.model.ambient_temperature} K")

        # 生成 FloXML
        builder = FloXMLBuilder()
        root = builder.build(data)

        # 格式化输出
        xml_str = self._prettify(root)

        # 写入文件
        with open(self.output_path, 'w', encoding='utf-8') as f:
            f.write(xml_str)

        print(f"[INFO] 输出 FloXML: {self.output_path}")
        return True

    def _prettify(self, elem: ET.Element) -> str:
        """格式化 XML 输出"""
        rough_string = ET.tostring(elem, encoding='unicode')
        reparsed = minidom.parseString(rough_string)
        return reparsed.toprettyxml(indent="    ")


# ============================================================================
# CLI
# ============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="将 FloTHERM PDML 文件转换为 FloXML 格式",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 转换单个文件
  python pdml_to_floxml_converter.py model.pdml -o output.xml

  # 批量转换
  python pdml_to_floxml_converter.py *.pdml --output-dir ./floxml/

  # 详细输出
  python pdml_to_floxml_converter.py model.pdml -v
        """
    )

    parser.add_argument("input", nargs="+", help="输入 PDML 文件")
    parser.add_argument("-o", "--output", help="输出 FloXML 文件 (单个文件时)")
    parser.add_argument("--output-dir", help="输出目录 (批量转换时)")
    parser.add_argument("-v", "--verbose", action="store_true", help="详细输出")

    args = parser.parse_args()

    # 处理批量转换
    if len(args.input) > 1 or args.output_dir:
        output_dir = Path(args.output_dir) if args.output_dir else Path(".")
        output_dir.mkdir(parents=True, exist_ok=True)

        success_count = 0
        for input_file in args.input:
            input_path = Path(input_file)
            output_path = output_dir / f"{input_path.stem}.xml"

            try:
                converter = PDMLToFloXMLConverter(str(input_path), str(output_path))
                if converter.convert():
                    success_count += 1
            except Exception as e:
                print(f"[ERROR] {input_file}: {e}")

        print(f"\n[INFO] 完成: {success_count}/{len(args.input)} 个文件转换成功")
        return 0 if success_count == len(args.input) else 1

    # 单个文件转换
    input_path = args.input[0]
    output_path = args.output

    try:
        converter = PDMLToFloXMLConverter(input_path, output_path)
        success = converter.convert()
        return 0 if success else 1
    except Exception as e:
        print(f"[ERROR] {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
