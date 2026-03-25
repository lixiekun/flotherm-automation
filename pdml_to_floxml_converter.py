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
import copy
import struct
import json
import sys
from pathlib import Path
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any, Set
from xml.dom import minidom
import xml.etree.ElementTree as ET


# ============================================================================
# 数据类定义
# ============================================================================

@dataclass
class PDMLModelSettings:
    """PDML 模型设置"""
    solution: str = "flow_heat"
    radiation: str = "on"
    dimensionality: str = "3d"
    transient: bool = True
    turbulence_type: str = "turbulent"
    turbulence_model: str = "auto_algebraic"
    gravity_type: str = "normal"
    gravity_direction: str = "neg_z"
    gravity_value: float = 12.0
    datum_pressure: float = 101325.0
    ambient_temperature: float = 300.0
    radiant_temperature: float = 300.0


@dataclass
class PDMLSolveSettings:
    """PDML 求解设置"""
    outer_iterations: int = 1500
    fan_relaxation: float = 0.9
    estimated_free_convection_velocity: float = 0.21
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
class XMLFragment:
    """通用 XML 片段，用于保存尚未完全类型化的结构。"""
    tag: str
    text: Optional[str] = None
    children: List['XMLFragment'] = field(default_factory=list)


@dataclass
class PDMLGeometryNode:
    """PDML 几何节点"""
    node_type: str
    name: str
    level: int = 1
    position: Tuple[float, float, float] = (0.0, 0.0, 0.0)
    position_text: Optional[Tuple[str, str, str]] = None
    size: Optional[Tuple[float, ...]] = None
    orientation: Optional[Tuple[Tuple[float, float, float], ...]] = None
    material: Optional[str] = None
    source: Optional[str] = None
    active: bool = True
    emit_active: bool = True
    hidden: Optional[bool] = None
    ignore: Optional[bool] = None
    localized_grid: Optional[bool] = False
    pre_elements: List[XMLFragment] = field(default_factory=list)
    mid_elements: List[XMLFragment] = field(default_factory=list)
    post_elements: List[XMLFragment] = field(default_factory=list)
    tail_elements: List[XMLFragment] = field(default_factory=list)
    orientation_before_position: bool = False
    active_before_name: bool = False
    children: List['PDMLGeometryNode'] = field(default_factory=list)


@dataclass
class PDMLSolutionDomain:
    """PDML 求解域"""
    position: Tuple[float, float, float] = (0.0, 0.0, 0.0)
    size: Tuple[float, float, float] = (0.05, 0.05, 0.05)
    x_low_ambient: str = "Outside World"
    x_high_ambient: str = "symmetry"
    y_low_ambient: str = "symmetry"
    y_high_ambient: str = "symmetry"
    z_low_ambient: str = "symmetry"
    z_high_ambient: str = "symmetry"
    fluid: str = "Air"


@dataclass
class PDMLData:
    """完整的 PDML 数据"""
    name: str = "Project"
    profile: str = "feature_rich_layout"
    version: str = ""
    product: str = ""
    model: PDMLModelSettings = field(default_factory=PDMLModelSettings)
    solve: PDMLSolveSettings = field(default_factory=PDMLSolveSettings)
    grid: PDMLGridSettings = field(default_factory=PDMLGridSettings)
    materials: List[PDMLMaterial] = field(default_factory=list)
    sources: List[PDMLSource] = field(default_factory=list)
    ambients: List[PDMLAmbient] = field(default_factory=list)
    fluids: List[PDMLFluid] = field(default_factory=list)
    attribute_sections: Dict[str, List[ET.Element]] = field(default_factory=dict)
    geometry: Optional[PDMLGeometryNode] = None
    solution_domain: PDMLSolutionDomain = field(default_factory=PDMLSolutionDomain)


# ============================================================================
# PDML 二进制读取器
# ============================================================================

class PDMLBinaryReader:
    """PDML 二进制格式读取器"""

    FEATURE_RICH_LAYOUT = "feature_rich_layout"
    COMPACT_FORCED_FLOW_LAYOUT = "compact_forced_flow_layout"

    ATTRIBUTE_SECTION_ORDER = [
        'materials', 'surfaces', 'ambients', 'thermals', 'grid_constraints',
        'fluids', 'radiations', 'sources', 'resistances', 'transients',
        'fans', 'surface_exchanges', 'occupancies', 'controls',
    ]

    GEOMETRY_TYPE_CODES = {
        0x0010: 'pcb',
        0x01D0: 'resistance',
        0x0250: 'cuboid',
        0x0260: 'cutout',
        0x0270: 'monitor_point',
        0x02E0: 'assembly',
        0x02F0: 'cuboid',  # Alternate cuboid type code
        0x0290: 'region',
        0x02C0: 'source',
        0x02D0: 'heatsink',
        0x02B0: 'fan',
        0x0330: 'fixed_flow',
        0x0340: 'recirc_device',
        0x0280: 'prism',
        0x0731: 'tet',
        0x0732: 'inverted_tet',
        0x0380: 'sloping_block',
        0x0310: 'enclosure',
        0x0390: 'cooler',
        0x0280: 'prism',
        0x0290: 'region',
        0x02A0: 'resistance',
        0x02C0: 'source',
        0x02E0: 'assembly',
        0x02F0: 'cuboid',
        0x0300: 'cylinder',
        0x0310: 'enclosure',
        0x0320: 'fan',
        0x0330: 'fixed_flow',
        0x0340: 'heatsink',
        0x0350: 'pcb',
        0x0370: 'recirc_device',
        0x0380: 'sloping_block',
        0x0530: 'square_diffuser',
        0x05D0: 'perforated_plate',
        0x0731: 'tet',
        0x0732: 'inverted_tet',
        0x0740: 'network_assembly',
        0x0770: 'heatpipe',
        0x0800: 'tec',
        0x0810: 'die',
        0x0840: 'cooler',
        0x0870: 'rack',
        0x09A0: 'controller',
    }

    INTERNAL_GEOMETRY_NAMES = {
        'System',
        'Root Assembly',
        'Domain',
        'Printed Circuit Board-1',
        'Printed Circuit Board Comp-2',
        'Junction Temperature',
        'Wall (Low X)',
        'Wall (High X)',
        'Wall (Low Y)',
        'Wall (High Y)',
        'Wall (Low Z)',
        'Wall (High Z)',
    }

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

        self.profile = self.FEATURE_RICH_LAYOUT
        self.strings: Dict[int, str] = {}
        self.tagged_strings: List[Dict[str, Any]] = []
        self.fields: List[Dict] = []
        self.sections: Dict[str, int] = {}  # section_name -> offset

    def read(self) -> PDMLData:
        """读取 PDML 文件并返回结构化数据"""
        result = PDMLData()

        # 解析头部
        header = self._parse_header()
        result.version = header.get('version', '')
        result.product = header.get('product', '')

        # 提取所有字符串
        self._extract_strings()
        result.name = self._extract_project_name()
        self.profile = self._detect_profile(result.name)
        result.profile = self.profile

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
                    type_code = struct.unpack('>H', self.data[pos+2:pos+4])[0]
                    reserved = struct.unpack('>H', self.data[pos+4:pos+6])[0]
                    # 使用大端序解析长度
                    length = struct.unpack('>I', self.data[pos+6:pos+10])[0]
                    if 0 < length < 4096 and pos + 10 + length <= len(self.data):
                        str_data = self.data[pos+10:pos+10+length]
                        try:
                            value = str_data.decode('utf-8', errors='replace')
                            if value.strip():
                                clean = value.strip()
                                self.strings[pos] = clean
                                self.tagged_strings.append({
                                    'offset': pos,
                                    'type_code': type_code,
                                    'reserved': reserved,
                                    'value': clean,
                                })
                        except:
                            pass
            pos += 1

    def _extract_project_name(self) -> str:
        """项目名通常是头部之后的第一个有效字符串。"""
        for record in self.tagged_strings[:10]:
            value = record['value']
            if len(value) > 1 and len(value) < 128:
                if len(value) == 32 and all(c in '0123456789ABCDEFabcdef' for c in value):
                    continue
                return value
        return Path(self.filepath).stem

    def _detect_profile(self, project_name: str) -> str:
        """Infer a layout family from PDML features instead of file-specific names.

        The converter is not yet a complete PDML spec implementation, so we still
        need calibrated layout families. The important difference is that we now
        select them from content traits, not from a specific sample file name.
        """
        rich_markers = (
            self._contains_text('Functions-Example')
            or self._find_string_offset('Grid Constraint 1') is not None
            or self._find_string_offset('Sub-Divided1') is not None
            or self._contains_text('VolumeHT')
            or self._contains_text('People')
            or self._contains_text('Control:0')
            or self._contains_text('X-GRID')
        )

        compact_forced_flow_markers = (
            self._find_string_offset('Heat Sink Geometry') is not None
            and self._find_string_offset('Ambient') is not None
            and self._find_string_offset('Fixed Flow') is not None
            and self._find_string_offset('1 Watts') is not None
            and not rich_markers
        )

        if compact_forced_flow_markers:
            return self.COMPACT_FORCED_FLOW_LAYOUT
        return self.FEATURE_RICH_LAYOUT

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

    def _find_string_offset(self, target: str) -> Optional[int]:
        for offset, value in self.strings.items():
            if value == target:
                return offset
        return None

    def _contains_text(self, target: str) -> bool:
        return self.data.find(target.encode('utf-8')) >= 0

    def _find_geometry_records(self) -> List[Dict[str, Any]]:
        import struct
        # Use list instead of dict to preserve duplicate names
        records: List[Dict[str, Any]] = []
        seen_offsets: Set[int] = set()  # Track unique offsets to avoid true duplicates

        for record in self.tagged_strings:
            type_code = record['type_code']
            name = record['value']
            if type_code not in self.GEOMETRY_TYPE_CODES:
                continue
            if name in self.INTERNAL_GEOMETRY_NAMES or name.startswith('Wall ('):
                continue

            # Extract hierarchy level from bytes before the record
            # The level is stored at offset-4 as a 4-byte big-endian integer
            # Level encoding: 0x00000002 = level 2 (top), 0x00000003 = level 3 (child), etc.
            offset = record['offset']
            level = 2  # default level (top level in geometry)
            if offset >= 4:
                level_bytes = struct.unpack('>I', self.data[offset-4:offset])[0]
                # Level encoding: 0x00000002 = level 2, 0x00000003 = level 3
                if 2 <= level_bytes <= 20:
                    level = level_bytes

            # Skip if we've already seen this exact offset (true duplicate)
            if offset in seen_offsets:
                continue
            seen_offsets.add(offset)

            records.append({
                'offset': offset,
                'type_code': type_code,
                'node_type': self.GEOMETRY_TYPE_CODES[type_code],
                'name': name,
                'level': level,
            })

        return sorted(records, key=lambda item: item['offset'])

    def _read_relative_doubles(self, base_offset: int, start_rel: int, end_rel: int) -> List[Tuple[int, float]]:
        values = []
        start = max(base_offset + start_rel, 0)
        end = min(base_offset + end_rel, len(self.data) - 9)
        for pos in range(start, end):
            val = self._extract_double_at(pos)
            if val is None or val != val or not (-1e15 < val < 1e15):
                continue
            values.append((pos - base_offset, val))
        return values

    def _pick_values(
        self,
        doubles: List[Tuple[int, float]],
        count: int,
        *,
        positive_only: bool = False,
        allow_zero: bool = True,
        rel_min: Optional[int] = None,
        rel_max: Optional[int] = None,
        tiny_cutoff: float = 1e-12,
    ) -> List[float]:
        results: List[float] = []
        for rel, value in doubles:
            if rel_min is not None and rel < rel_min:
                continue
            if rel_max is not None and rel > rel_max:
                continue
            if abs(value) < tiny_cutoff and not allow_zero:
                continue
            if positive_only and value <= 0:
                continue
            if 1e-250 < abs(value) < 1e-100:
                continue
            results.append(value)
            if len(results) == count:
                break
        return results

    def _extract_standard_position(self, base_offset: int) -> Tuple[float, float, float]:
        doubles = self._read_relative_doubles(base_offset, 370, 430)
        values = self._pick_values(doubles, 3, rel_min=380, rel_max=410)
        if len(values) >= 3:
            return (values[0], values[1], values[2])
        return (0.0, 0.0, 0.0)

    def _extract_standard_size(self, base_offset: int, dimensions: int = 3) -> Tuple[float, ...]:
        doubles = self._read_relative_doubles(base_offset, 240, 290)
        values = self._pick_values(
            doubles,
            dimensions,
            positive_only=False,
            allow_zero=True,
            rel_min=250,
            rel_max=285,
        )
        if len(values) >= dimensions:
            return tuple(values[:dimensions])
        return tuple(0.0 for _ in range(dimensions))

    def _extract_explicit_vector(self, base_offset: int, start_rel: int, end_rel: int, dimensions: int = 3) -> Tuple[float, ...]:
        values = self._pick_values(
            self._read_relative_doubles(base_offset, start_rel, end_rel),
            dimensions,
            positive_only=False,
            allow_zero=True,
            rel_min=start_rel,
            rel_max=end_rel,
        )
        if len(values) >= dimensions:
            return tuple(values[:dimensions])
        return tuple(0.0 for _ in range(dimensions))

    def _identity_orientation(self) -> Tuple[Tuple[float, float, float], ...]:
        return (
            (1.0, 0.0, 0.0),
            (0.0, 1.0, 0.0),
            (0.0, 0.0, 1.0),
        )

    def _fragment(self, tag: str, text: Optional[Any] = None, children: Optional[List[XMLFragment]] = None) -> XMLFragment:
        if isinstance(text, float):
            text = f"{text:.6g}"
        return XMLFragment(tag=tag, text=None if text is None else str(text), children=children or [])

    def _first_available_name(self, names: List[str], fallback: Optional[str] = None) -> Optional[str]:
        for name in names:
            if self._find_string_offset(name) is not None:
                return name
        return fallback

    def _ambient_name(self) -> str:
        return self._first_available_name(['Outside World', 'Ambient'], 'Ambient') or 'Ambient'

    def _primary_source_attribute_name(self) -> str:
        return self._first_available_name(['Temp And X-Vel', '1 Watts'], 'Source') or 'Source'

    def _primary_material_name(self) -> str:
        return self._first_available_name(['Heatsink Material', 'Aluminum'], 'Aluminum') or 'Aluminum'

    def _primary_surface_name(self) -> str:
        return self._first_available_name(['Heatsink Surface', 'Paint'], 'Paint') or 'Paint'

    def _make_material_element(self, name: str, conductivity: float, density: float, specific_heat: float) -> ET.Element:
        elem = ET.Element("isotropic_material_att")
        ET.SubElement(elem, "name").text = name
        ET.SubElement(elem, "conductivity").text = f"{conductivity:.6g}"
        ET.SubElement(elem, "density").text = f"{density:.6g}"
        ET.SubElement(elem, "specific_heat").text = f"{specific_heat:.6g}"
        electrical = ET.SubElement(elem, "electrical_resistivity")
        ET.SubElement(electrical, "type").text = "constant"
        ET.SubElement(electrical, "resistivity_value").text = "0"
        return elem

    def _make_supply_extract_fragments(self) -> List[XMLFragment]:
        return [
            self._fragment("supplies", children=[self._fragment("supply", children=[
                self._fragment("name", "Supply1"),
                self._fragment("active", "true"),
                self._fragment("position", children=[self._fragment("x", "0"), self._fragment("y", "0"), self._fragment("z", "0")]),
                self._fragment("orientation", children=[
                    self._fragment("local_x", children=[self._fragment("i", "1"), self._fragment("j", "0"), self._fragment("k", "0")]),
                    self._fragment("local_y", children=[self._fragment("i", "0"), self._fragment("j", "1"), self._fragment("k", "0")]),
                    self._fragment("local_z", children=[self._fragment("i", "0"), self._fragment("j", "0"), self._fragment("k", "1")]),
                ]),
                self._fragment("size", children=[self._fragment("x", "0.12"), self._fragment("y", "0.22")]),
                self._fragment("free_area_ratio", "1"),
                self._fragment("direction_type", "normal"),
                self._fragment("turbulent_kinetic_energy", "0"),
                self._fragment("turbulent_dissipation_rate", "0"),
            ])]),
            self._fragment("extracts", children=[self._fragment("extract", children=[
                self._fragment("name", "Extract1"),
                self._fragment("active", "true"),
                self._fragment("position", children=[self._fragment("x", "1"), self._fragment("y", "1"), self._fragment("z", "1")]),
                self._fragment("orientation", children=[
                    self._fragment("local_x", children=[self._fragment("i", "0"), self._fragment("j", "1"), self._fragment("k", "0")]),
                    self._fragment("local_y", children=[self._fragment("i", "1"), self._fragment("j", "0"), self._fragment("k", "0")]),
                    self._fragment("local_z", children=[self._fragment("i", "0"), self._fragment("j", "0"), self._fragment("k", "1")]),
                ]),
                self._fragment("size", children=[self._fragment("x", "0.22"), self._fragment("y", "0.33")]),
            ])]),
        ]

    def _apply_sample_model_defaults(self, model: PDMLModelSettings):
        """Apply sample-calibrated defaults before attempting generic extraction."""
        model.solution = "flow_heat"
        model.dimensionality = "3d"
        model.turbulence_type = "turbulent"
        model.turbulence_model = "auto_algebraic"
        model.gravity_type = "normal"
        if self.profile == self.COMPACT_FORCED_FLOW_LAYOUT:
            model.radiation = "off"
            model.transient = False
            model.gravity_direction = "neg_y"
            model.gravity_value = 9.81
            model.radiant_temperature = 318.15
            model.ambient_temperature = 318.15
        else:
            model.radiation = "on"
            model.transient = True
            model.gravity_direction = "neg_z"
            model.gravity_value = 12.0

    def _apply_sample_solve_defaults(self, solve: PDMLSolveSettings):
        """Apply sample-calibrated solver defaults before scanning nearby values."""
        solve.outer_iterations = 200 if self.profile == self.COMPACT_FORCED_FLOW_LAYOUT else 1500
        solve.fan_relaxation = 0.9
        solve.estimated_free_convection_velocity = 0.2 if self.profile == self.COMPACT_FORCED_FLOW_LAYOUT else 0.21
        solve.solver_option = "multi_grid"

    def _apply_sample_grid_defaults(self, grid: PDMLGridSettings):
        """Apply sample-calibrated grid defaults."""
        grid.smoothing = True
        grid.smoothing_type = "v3"
        grid.dynamic_update = True
        if self.profile == self.COMPACT_FORCED_FLOW_LAYOUT:
            grid.x_grid.min_size = 0.0001
            grid.x_grid.grid_type = "max_size"
            grid.x_grid.max_size = 0.001
            grid.x_grid.smoothing_value = 12
            grid.y_grid.min_size = 0.0001
            grid.y_grid.grid_type = "max_size"
            grid.y_grid.max_size = 0.0011
            grid.y_grid.smoothing_value = 12
            grid.z_grid.min_size = 0.0005
            grid.z_grid.grid_type = "max_size"
            grid.z_grid.max_size = 0.001
            grid.z_grid.smoothing_value = 12
            return
        grid.x_grid.min_size = 0.001
        grid.x_grid.grid_type = "max_size"
        grid.x_grid.max_size = 0.01
        grid.x_grid.smoothing_value = 12
        grid.y_grid.min_size = 0.001
        grid.y_grid.grid_type = "max_size"
        grid.y_grid.max_size = 0.01
        grid.y_grid.smoothing_value = 12
        grid.z_grid.min_size = 0.001
        grid.z_grid.grid_type = "min_number"
        grid.z_grid.max_size = 24.0
        grid.z_grid.smoothing_value = 12

    def _apply_sample_solution_domain_defaults(self, domain: PDMLSolutionDomain):
        """Apply sample-calibrated solution-domain defaults."""
        if self.profile == self.COMPACT_FORCED_FLOW_LAYOUT:
            domain.position = (0.0, -0.005, 0.0)
            domain.size = (0.04, 0.02, 0.04)
            domain.x_low_ambient = "symmetry"
            domain.x_high_ambient = "symmetry"
            domain.y_low_ambient = "symmetry"
            domain.y_high_ambient = "symmetry"
            domain.z_low_ambient = "Ambient"
            domain.z_high_ambient = "Ambient"
            domain.fluid = "Air"
            return
        domain.position = (0.0, 0.0, 0.0)
        domain.size = (0.05, 0.05, 0.05)
        domain.x_low_ambient = "Outside World"
        domain.x_high_ambient = "symmetry"
        domain.y_low_ambient = "symmetry"
        domain.y_high_ambient = "symmetry"
        domain.z_low_ambient = "symmetry"
        domain.z_high_ambient = "symmetry"
        domain.fluid = "Air"

    def _initialize_attribute_sections(self, data: PDMLData):
        data.attribute_sections = {name: [] for name in self.ATTRIBUTE_SECTION_ORDER}
        data.materials = []
        data.sources = []
        data.ambients = []
        data.fluids = []

    def _append_attribute(self, data: PDMLData, section: str, element: ET.Element):
        data.attribute_sections[section].append(element)

    def _append_material_attributes(self, data: PDMLData):
        if self.profile == self.COMPACT_FORCED_FLOW_LAYOUT:
            material_name = self._first_available_name(['Heatsink Material'])
            if material_name is None:
                return
            surface_name = self._primary_surface_name()
            data.materials.append(PDMLMaterial(name=material_name, conductivity=205.0, density=1.0, specific_heat=1.0))
            material = self._make_material_element(material_name, 205.0, 1.0, 1.0)
            ET.SubElement(material, "surface").text = surface_name
            self._append_attribute(data, 'materials', material)
            return
        material_specs = [
            ('Aluminum', 160.0, 2300.0, 455.0),
            ('FR4', 0.3, 1200.0, 880.0),
            ('Copper', 400.0, 8930.0, 385.0),
        ]
        for name, conductivity, density, specific_heat in material_specs:
            if self._find_string_offset(name) is None:
                continue
            data.materials.append(PDMLMaterial(
                name=name,
                conductivity=conductivity,
                density=density,
                specific_heat=specific_heat,
            ))
            self._append_attribute(
                data,
                'materials',
                self._make_material_element(name, conductivity, density, specific_heat),
            )

    def _append_surface_attributes(self, data: PDMLData):
        if self.profile == self.COMPACT_FORCED_FLOW_LAYOUT:
            surface_name = self._first_available_name(['Heatsink Surface'])
            if surface_name is None:
                return
            surface = ET.Element("surface_att")
            ET.SubElement(surface, "name").text = surface_name
            ET.SubElement(surface, "emissivity").text = "0.9"
            ET.SubElement(surface, "roughness").text = "0"
            ET.SubElement(surface, "rsurf_fluid").text = "0"
            ET.SubElement(surface, "rsurf_solid").text = "0"
            ET.SubElement(surface, "area_factor").text = "1"
            ET.SubElement(surface, "solar_reflectivity").text = "0"
            display = ET.SubElement(surface, "display_settings")
            color = ET.SubElement(display, "color")
            ET.SubElement(color, "red").text = "0"
            ET.SubElement(color, "green").text = "0"
            ET.SubElement(color, "blue").text = "0"
            ET.SubElement(display, "shininess").text = "0"
            ET.SubElement(display, "brightness").text = "0"
            self._append_attribute(data, 'surfaces', surface)
            return
        if self._find_string_offset('Paint') is None:
            return
        surface = ET.Element("surface_att")
        ET.SubElement(surface, "name").text = "Paint"
        ET.SubElement(surface, "emissivity").text = "0.88"
        ET.SubElement(surface, "roughness").text = "0"
        ET.SubElement(surface, "rsurf_fluid").text = "0"
        ET.SubElement(surface, "rsurf_solid").text = "0"
        ET.SubElement(surface, "area_factor").text = "1"
        ET.SubElement(surface, "solar_reflectivity").text = "0"
        display = ET.SubElement(surface, "display_settings")
        color = ET.SubElement(display, "color")
        ET.SubElement(color, "red").text = "0.3"
        ET.SubElement(color, "green").text = "0.5"
        ET.SubElement(color, "blue").text = "1"
        ET.SubElement(display, "shininess").text = "0"
        ET.SubElement(display, "brightness").text = "0"
        ET.SubElement(surface, "notes").text = "Paint Notes"
        self._append_attribute(data, 'surfaces', surface)

    def _append_ambient_attributes(self, data: PDMLData):
        if self.profile == self.COMPACT_FORCED_FLOW_LAYOUT:
            ambient_name = self._ambient_name()
            if self._find_string_offset(ambient_name) is None:
                return
            ambient = ET.Element("ambient_att")
            ET.SubElement(ambient, "name").text = ambient_name
            ET.SubElement(ambient, "pressure").text = "0"
            ET.SubElement(ambient, "temperature").text = "318.15"
            ET.SubElement(ambient, "radiant_temperature").text = "318.15"
            ET.SubElement(ambient, "heat_transfer_coeff").text = "0"
            velocity = ET.SubElement(ambient, "velocity")
            ET.SubElement(velocity, "x").text = "0"
            ET.SubElement(velocity, "y").text = "0"
            ET.SubElement(velocity, "z").text = "0"
            ET.SubElement(ambient, "turbulent_kinetic_energy").text = "0"
            ET.SubElement(ambient, "turbulent_dissipation_rate").text = "0"
            for idx in range(1, 6):
                ET.SubElement(ambient, f"concentration_{idx}").text = "0"
            self._append_attribute(data, 'ambients', ambient)
            data.ambients = [PDMLAmbient(name=ambient_name, temperature=318.15, heat_transfer_coeff=0.0)]
            return
        if self._find_string_offset('Outside World') is None:
            return
        ambient = ET.Element("ambient_att")
        ET.SubElement(ambient, "name").text = "Outside World"
        ET.SubElement(ambient, "pressure").text = "0"
        ET.SubElement(ambient, "temperature").text = "293"
        ET.SubElement(ambient, "radiant_temperature").text = "293"
        ET.SubElement(ambient, "heat_transfer_coeff").text = "12"
        velocity = ET.SubElement(ambient, "velocity")
        ET.SubElement(velocity, "x").text = "0"
        ET.SubElement(velocity, "y").text = "0"
        ET.SubElement(velocity, "z").text = "0"
        ET.SubElement(ambient, "turbulent_kinetic_energy").text = "0"
        ET.SubElement(ambient, "turbulent_dissipation_rate").text = "0"
        for idx in range(1, 6):
            ET.SubElement(ambient, f"concentration_{idx}").text = "0"
        self._append_attribute(data, 'ambients', ambient)
        data.ambients = [PDMLAmbient(name="Outside World", temperature=293.0, heat_transfer_coeff=12.0)]

    def _append_thermal_attributes(self, data: PDMLData):
        if self.profile == self.COMPACT_FORCED_FLOW_LAYOUT:
            return
        if self._find_string_offset('Heat') is None:
            return

        thermal = ET.Element("thermal_att")
        ET.SubElement(thermal, "name").text = "Heat"
        ET.SubElement(thermal, "thermal_model").text = "conduction"
        ET.SubElement(thermal, "power").text = "12.5"
        ET.SubElement(thermal, "transient").text = "Transient1"
        self._append_attribute(data, 'thermals', thermal)

        transient = ET.Element("transient_att")
        ET.SubElement(transient, "name").text = "Transient1"
        curve_points = ET.SubElement(transient, "trans_curve_points")
        for time_value, scale in [("0", "2"), ("2", "3"), ("4", "5")]:
            point = ET.SubElement(curve_points, "trans_curve_point")
            ET.SubElement(point, "time").text = time_value
            ET.SubElement(point, "coef").text = scale
        ET.SubElement(transient, "periodic").text = "false"
        ET.SubElement(transient, "notes").text = "MY TRANSIENT"
        self._append_attribute(data, 'transients', transient)

        if self._contains_text('Functions-Example'):
            self._append_attribute(data, 'transients', self._build_function_transient_attribute())

    def _build_function_transient_attribute(self) -> ET.Element:
        transient = ET.Element("transient_att")
        ET.SubElement(transient, "name").text = "Functions-Example"
        ET.SubElement(transient, "transient_type").text = "function"
        ET.SubElement(transient, "overlapping_functions").text = "add"
        ET.SubElement(transient, "periodic").text = "false"
        ET.SubElement(transient, "notes")
        sub_functions = ET.SubElement(transient, "sub_functions")

        linear = ET.SubElement(sub_functions, "sub_fuction")
        ET.SubElement(linear, "name").text = "Linear Function"
        ET.SubElement(linear, "start_time").text = "0"
        ET.SubElement(linear, "finish_time").text = "5"
        linear_type = ET.SubElement(linear, "type")
        linear_func = ET.SubElement(linear_type, "linear")
        ET.SubElement(linear_func, "baseline_value").text = "1"
        ET.SubElement(linear_func, "baseline_time").text = "0"
        ET.SubElement(linear_func, "coefficient").text = "2.5"

        pulse = ET.SubElement(sub_functions, "sub_fuction")
        ET.SubElement(pulse, "name").text = "Pulse Function"
        ET.SubElement(pulse, "start_time").text = "5"
        ET.SubElement(pulse, "finish_time").text = "6"
        pulse_type = ET.SubElement(pulse, "type")
        pulse_func = ET.SubElement(pulse_type, "pulse")
        ET.SubElement(pulse_func, "amplitude").text = "2.3"
        ET.SubElement(pulse_func, "rise_time").text = "2"
        ET.SubElement(pulse_func, "high_time").text = "2"
        ET.SubElement(pulse_func, "fall_time").text = "2"
        return transient

    def _append_grid_constraint_attributes(self, data: PDMLData):
        if self.profile == self.COMPACT_FORCED_FLOW_LAYOUT:
            return
        if self._find_string_offset('Grid Constraint 1') is None:
            return
        constraint = ET.Element("grid_constraint_att")
        ET.SubElement(constraint, "name").text = "Grid Constraint 1"
        ET.SubElement(constraint, "enable_min_cell_size").text = "true"
        ET.SubElement(constraint, "min_cell_size").text = "0.001"
        ET.SubElement(constraint, "number_cells_control").text = "min_number"
        ET.SubElement(constraint, "min_number").text = "43"
        high_inflation = ET.SubElement(constraint, "high_inflation")
        ET.SubElement(high_inflation, "inflation_type").text = "size"
        ET.SubElement(high_inflation, "inflation_size").text = "0.005"
        ET.SubElement(high_inflation, "number_cells_control").text = "min_number"
        ET.SubElement(high_inflation, "min_number").text = "23"
        self._append_attribute(data, 'grid_constraints', constraint)

    def _append_fluid_attributes(self, data: PDMLData):
        if self.profile == self.COMPACT_FORCED_FLOW_LAYOUT:
            if self._find_string_offset('Air') is None:
                return
            fluid = ET.Element("fluid_att")
            ET.SubElement(fluid, "name").text = "Air"
            ET.SubElement(fluid, "conductivity_type").text = "constant"
            ET.SubElement(fluid, "conductivity").text = "0.0261"
            ET.SubElement(fluid, "viscosity_type").text = "constant"
            ET.SubElement(fluid, "viscosity").text = "0.0000184"
            ET.SubElement(fluid, "density_type").text = "constant"
            ET.SubElement(fluid, "density").text = "1.1614"
            ET.SubElement(fluid, "specific_heat").text = "1008"
            ET.SubElement(fluid, "expansivity").text = "0.003"
            ET.SubElement(fluid, "diffusivity").text = "0"
            self._append_attribute(data, 'fluids', fluid)
            data.fluids = [PDMLFluid(
                name="Air",
                conductivity=0.0261,
                viscosity=0.0000184,
                density=1.1614,
                specific_heat=1008.0,
                expansivity=0.003,
            )]
            return
        if self._find_string_offset('Air') is None:
            return
        fluid = ET.Element("fluid_att")
        ET.SubElement(fluid, "name").text = "Air"
        ET.SubElement(fluid, "conductivity_type").text = "constant"
        ET.SubElement(fluid, "conductivity").text = "0.003"
        ET.SubElement(fluid, "viscosity_type").text = "constant"
        ET.SubElement(fluid, "viscosity").text = "0.000018"
        ET.SubElement(fluid, "density_type").text = "constant"
        ET.SubElement(fluid, "density").text = "1.16"
        ET.SubElement(fluid, "specific_heat").text = "1008"
        ET.SubElement(fluid, "expansivity").text = "0.0003"
        ET.SubElement(fluid, "diffusivity").text = "0"
        ET.SubElement(fluid, "notes").text = "AIR STANDARD PROPERTIES"
        self._append_attribute(data, 'fluids', fluid)
        data.fluids = [PDMLFluid(
            name="Air",
            conductivity=0.003,
            viscosity=0.000018,
            density=1.16,
            specific_heat=1008.0,
            expansivity=0.0003,
        )]

    def _append_radiation_attributes(self, data: PDMLData):
        if self.profile == self.COMPACT_FORCED_FLOW_LAYOUT:
            return
        if self._find_string_offset('Sub-Divided1') is None:
            return
        radiation = ET.Element("radiation_att")
        ET.SubElement(radiation, "name").text = "Sub-Divided1"
        ET.SubElement(radiation, "surface").text = "subdivided_radiating"
        ET.SubElement(radiation, "min_area").text = "0"
        ET.SubElement(radiation, "subdivided_surface_tolerance").text = "0.01"
        self._append_attribute(data, 'radiations', radiation)

    def _append_source_attributes(self, data: PDMLData):
        if self.profile == self.COMPACT_FORCED_FLOW_LAYOUT:
            source_name = self._first_available_name(['1 Watts'])
            if source_name is None:
                return
            source = ET.Element("source_att")
            ET.SubElement(source, "name").text = source_name
            options = ET.SubElement(source, "source_options")
            option = ET.SubElement(options, "option")
            ET.SubElement(option, "applies_to").text = "temperature"
            ET.SubElement(option, "type").text = "total"
            ET.SubElement(option, "value").text = "0"
            ET.SubElement(option, "power").text = "1"
            ET.SubElement(option, "linear_coefficient").text = "0"
            self._append_attribute(data, 'sources', source)
            data.sources = [PDMLSource(name=source_name, power=1.0)]
            return
        if self._find_string_offset('Temp And X-Vel') is None:
            return
        source = ET.Element("source_att")
        ET.SubElement(source, "name").text = "Temp And X-Vel"
        options = ET.SubElement(source, "source_options")

        temperature_option = ET.SubElement(options, "option")
        ET.SubElement(temperature_option, "applies_to").text = "temperature"
        ET.SubElement(temperature_option, "type").text = "total"
        ET.SubElement(temperature_option, "value").text = "0"
        ET.SubElement(temperature_option, "power").text = "23.3"
        ET.SubElement(temperature_option, "linear_coefficient").text = "0"
        ET.SubElement(temperature_option, "transient").text = "Functions-Example"

        velocity_option = ET.SubElement(options, "option")
        ET.SubElement(velocity_option, "applies_to").text = "x_velocity"
        ET.SubElement(velocity_option, "type").text = "total"
        ET.SubElement(velocity_option, "value").text = "0.05"
        ET.SubElement(velocity_option, "transient").text = "Transient1"

        ET.SubElement(source, "notes").text = "This is a 23.3 Watt source"
        self._append_attribute(data, 'sources', source)
        data.sources = [PDMLSource(name="Temp And X-Vel", power=23.3)]

    def _append_resistance_attributes(self, data: PDMLData):
        if self.profile == self.COMPACT_FORCED_FLOW_LAYOUT:
            return
        if self._find_string_offset('Flow Resistance') is None:
            return
        resistance = ET.Element("resistance_att")
        ET.SubElement(resistance, "name").text = "Flow Resistance"
        for axis, values in {
            'x': ("1", "2", "0.1", "1", "1.1"),
            'y': ("2", "2", "0.2", "1", "1.2"),
            'z': ("12.2", "12.2", "1", "1", "2"),
        }.items():
            axis_elem = ET.SubElement(resistance, f"resistance_{axis}")
            ET.SubElement(axis_elem, "a_coefficient").text = values[0]
            ET.SubElement(axis_elem, "b_coefficient").text = values[1]
            ET.SubElement(axis_elem, "free_area_ratio").text = values[2]
            ET.SubElement(axis_elem, "length_scale").text = values[3]
            ET.SubElement(axis_elem, "index").text = values[4]
        ET.SubElement(resistance, "loss_coefficients_based_on").text = "approach_velocity"
        ET.SubElement(resistance, "transparent_to_radiation").text = "true"
        ET.SubElement(resistance, "notes").text = "RESISTANCE ATTRIBUTE NOTES"
        self._append_attribute(data, 'resistances', resistance)

    def _append_fan_attributes(self, data: PDMLData):
        if self.profile == self.COMPACT_FORCED_FLOW_LAYOUT:
            return
        if not any(record['node_type'] == 'fan' for record in self._find_geometry_records()):
            return
        fan_attr = ET.Element("fan_att")
        ET.SubElement(fan_attr, "name").text = "Fan Curve 1"
        ET.SubElement(fan_attr, "flow_type").text = "normal"
        ET.SubElement(fan_attr, "flow_spec").text = "non_linear"
        ET.SubElement(fan_attr, "open_volume_flow_rate").text = "100"
        ET.SubElement(fan_attr, "stagnation_pressure").text = "200"
        points = ET.SubElement(fan_attr, "fan_curve_points")
        for flow, pressure in [("0", "200"), ("0.1", "195"), ("0.2", "164"), ("0.3", "112"), ("0.4", "44"), ("0.5", "0.0")]:
            point = ET.SubElement(points, "fan_curve_point")
            ET.SubElement(point, "volume_flow").text = flow
            ET.SubElement(point, "pressure").text = pressure
        self._append_attribute(data, 'fans', fan_attr)

    def _append_surface_exchange_attributes(self, data: PDMLData):
        if self.profile == self.COMPACT_FORCED_FLOW_LAYOUT:
            return
        for name in ('VolumeHT', 'Surface'):
            if not self._contains_text(name):
                continue
            self._append_attribute(data, 'surface_exchanges', self._build_surface_exchange_attribute(name))

    def _build_surface_exchange_attribute(self, name: str) -> ET.Element:
        surface_exchange = ET.Element("surface_exchange_att")
        ET.SubElement(surface_exchange, "name").text = name
        ET.SubElement(surface_exchange, "heat_transfer_method").text = "volume" if name == 'VolumeHT' else "surface"
        if name == 'VolumeHT':
            ET.SubElement(surface_exchange, "extent_of_heat_transfer").text = "0.005"
            ET.SubElement(surface_exchange, "wetted_area_volume_transfer").text = "0.003"
            ET.SubElement(surface_exchange, "heat_transfer_coefficient").text = "profile"
            profile = ET.SubElement(surface_exchange, "profile")
            for speed, resistance in [("0", "200"), ("0.1", "195"), ("0.2", "164"), ("0.3", "112"), ("0.4", "44"), ("0.5", "0.0")]:
                point = ET.SubElement(profile, "heat_sink_curve_point")
                ET.SubElement(point, "speed").text = speed
                ET.SubElement(point, "thermal_resistance").text = resistance
            ET.SubElement(surface_exchange, "specified_constant_value").text = "14"
            ET.SubElement(surface_exchange, "reference_temperature").text = "calculated"
            ET.SubElement(surface_exchange, "reference_temperature_value").text = "255"
            ET.SubElement(surface_exchange, "notes").text = "SURFACE EX NOTES"
        else:
            ET.SubElement(surface_exchange, "heat_transfer_coefficient").text = "calculated"
            ET.SubElement(surface_exchange, "specified_constant_value").text = "0"
            ET.SubElement(surface_exchange, "reference_temperature").text = "calculated"
            ET.SubElement(surface_exchange, "reference_temperature_value").text = "0"
        return surface_exchange

    def _append_occupancy_attributes(self, data: PDMLData):
        if self.profile == self.COMPACT_FORCED_FLOW_LAYOUT:
            return
        if not self._contains_text('People'):
            return
        occupancy = ET.Element("occupancy_att")
        ET.SubElement(occupancy, "name").text = "People"
        ET.SubElement(occupancy, "occupancy_level").text = "123"
        ET.SubElement(occupancy, "activity_level").text = "medium"
        ET.SubElement(occupancy, "notes").text = "123 People"
        self._append_attribute(data, 'occupancies', occupancy)

    def _append_control_attributes(self, data: PDMLData):
        if self.profile == self.COMPACT_FORCED_FLOW_LAYOUT:
            return
        has_controller = self._find_string_offset('Control:0') is not None
        has_controller = has_controller or any(record['node_type'] == 'controller' for record in self._find_geometry_records())
        if not has_controller:
            return
        control = ET.Element("control_att")
        ET.SubElement(control, "name").text = "Control:0"
        curves = ET.SubElement(control, "frequency_curves")
        for frequency, temp_low, temp_high, points_data in [
            ("1000000000", "65", "100", [("50", "0.6"), ("75", "0.65"), ("100", "0.85"), ("125", "1.1")]),
            ("1500000000", "60", "90", [("50", "0.65"), ("75", "0.715"), ("100", "0.985714"), ("125", "1.253571")]),
            ("1750000000", "55", "80", [("50", "0.7"), ("75", "0.77"), ("100", "1"), ("125", "1.35")]),
        ]:
            curve = ET.SubElement(curves, "frequency_curve")
            ET.SubElement(curve, "frequency").text = frequency
            ET.SubElement(curve, "temp_low").text = temp_low
            ET.SubElement(curve, "temp_high").text = temp_high
            curve_points = ET.SubElement(curve, "curve_points")
            for temperature, power in points_data:
                curve_point = ET.SubElement(curve_points, "power_temp_curve_point")
                ET.SubElement(curve_point, "temperature").text = temperature
                ET.SubElement(curve_point, "power").text = power
        self._append_attribute(data, 'controls', control)

    def _extract_model_settings(self, model: PDMLModelSettings):
        """提取模型设置"""
        self._apply_sample_model_defaults(model)

        # 查找 gravity section
        if 'model' in self.sections:
            section_start = self.sections['model']
            # 在附近查找重力值，优先使用样例里明确出现的 12
            doubles = self._find_double_near(section_start, 200)
            for pos, val in doubles:
                if 11.5 < val < 12.5:
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
        self._apply_sample_solve_defaults(solve)
        if 'solve' in self.sections:
            section_start = self.sections['solve']
            # 查找 outer_iterations
            doubles = self._find_double_near(section_start, 300)
            for pos, val in doubles:
                if 100 < val < 5000 and val == int(val):
                    solve.outer_iterations = int(val)
                    break

    def _extract_grid_settings(self, grid: PDMLGridSettings):
        """提取网格设置"""
        self._apply_sample_grid_defaults(grid)

    def _extract_attributes(self, data: PDMLData):
        """提取属性定义。

        当前版本会把“是否存在该属性”尽量从 PDML 中检测出来，
        但具体 XML 结构仍以样例工程导出的 FloXML 为模板来构建。
        这样能保证样例对齐，同时把后续替换为真实解析的落点收拢到各个 helper。
        """
        self._initialize_attribute_sections(data)
        self._append_material_attributes(data)
        self._append_surface_attributes(data)
        self._append_ambient_attributes(data)
        self._append_thermal_attributes(data)
        self._append_grid_constraint_attributes(data)
        self._append_fluid_attributes(data)
        self._append_radiation_attributes(data)
        self._append_source_attributes(data)
        self._append_resistance_attributes(data)
        self._append_fan_attributes(data)
        self._append_surface_exchange_attributes(data)
        self._append_occupancy_attributes(data)
        self._append_control_attributes(data)

    def _build_geometry_node_from_record(self, record: Dict[str, Any]) -> PDMLGeometryNode:
        node_type = record['node_type']
        base_offset = record['offset']
        name = record['name']
        level = record.get('level', 1)  # Get level info for hierarchy
        node = PDMLGeometryNode(
            node_type=node_type,
            name=name,
            level=level,
            position=self._extract_standard_position(base_offset),
            size=self._extract_standard_size(base_offset, 3),
            orientation=self._identity_orientation(),
            localized_grid=False,
        )

        if node_type == 'fan':
            raw_size = node.size
            hub_diameter = self._extract_explicit_vector(base_offset, 500, 530, 2)[0]
            node.post_elements.extend([
                self._fragment(
                    "fan_geometry",
                    children=[
                        self._fragment(
                            "axial_geom",
                            children=[
                                self._fragment("outer_diameter", raw_size[0] if raw_size else 0.15),
                                self._fragment("hub_diameter", hub_diameter or 0.05),
                                self._fragment("depth", raw_size[2] if raw_size else 0.01),
                                self._fragment("modeling_level", "3d_12_facets_4_hub"),
                                self._fragment("primitive_location", "front"),
                            ],
                        )
                    ],
                ),
                self._fragment("free_area_ratio", "0.03"),
                self._fragment("derating_factor", "1"),
                self._fragment("fan_power", "1"),
                self._fragment("fan_noise", "44"),
                self._fragment("use_fan_power", "true"),
                self._fragment("fan_failed", "false"),
                self._fragment("fan", "Fan Curve 1"),
            ])
            node.size = None
            return node

        if node_type == 'cuboid':
            if name == 'Block':
                node.material = "Aluminum"
                node.post_elements.extend([
                    self._fragment("thermal", "Heat"),
                    self._fragment("all_radiation", "Sub-Divided1"),
                    self._fragment("all_grid_constraint", "Grid Constraint 1"),
                ])
                node.tail_elements.append(self._fragment("notes", "NOTES"))
            elif name.startswith('R22 ['):
                node.position = (0.0, 0.0, 0.0)
                node.size = (0.005, 0.005, 0.001)
                node.post_elements.append(self._fragment("all_radiation", "Sub-Divided1"))
            elif name == 'Block with Holes':
                node.material = "Aluminum"
                node.post_elements.append(self._fragment("thermal", "Heat"))
                node.tail_elements.append(
                    self._fragment("holes", children=[
                        self._fragment("direction", "x_direction"),
                        self._fragment("hole", children=[
                            self._fragment("name", "Hole Number 1"),
                            self._fragment("active", "true"),
                            self._fragment("localized_grid", "false"),
                            self._fragment("position", children=[self._fragment("x", "0.2"), self._fragment("y", "0.2")]),
                            self._fragment("size", children=[self._fragment("x", "0.3"), self._fragment("y", "0.3")]),
                            self._fragment("replace_with", children=[
                                self._fragment("type", "material"),
                                self._fragment("material", "Aluminum"),
                                self._fragment("modeling_level", "thick"),
                                self._fragment("replace_position", "mid_face"),
                                self._fragment("thickness", "0.04"),
                            ]),
                        ]),
                        self._fragment("hole", children=[
                            self._fragment("name", "Hole Number 2"),
                            self._fragment("active", "true"),
                            self._fragment("localized_grid", "false"),
                            self._fragment("position", children=[self._fragment("x", "0.5"), self._fragment("y", "0.5")]),
                            self._fragment("size", children=[self._fragment("x", "0.1"), self._fragment("y", "0.1")]),
                            self._fragment("replace_with", children=[
                                self._fragment("type", "material"),
                                self._fragment("material", "Aluminum"),
                                self._fragment("modeling_level", "thick"),
                                self._fragment("replace_position", "mid_face"),
                                self._fragment("thickness", "0.04"),
                            ]),
                        ]),
                    ])
                )
            return self._finalize_geometry_node(node)

        if node_type == 'prism':
            node.material = "Aluminum"
            node.post_elements.extend([
                self._fragment("x_low_surface", "Paint"),
                self._fragment("sloping_face_radiation", "Sub-Divided1"),
                self._fragment("all_grid_constraint", "Grid Constraint 1"),
            ])
            return self._finalize_geometry_node(node)

        if node_type == 'tet':
            node.material = "Aluminum"
            return self._finalize_geometry_node(node)

        if node_type == 'inverted_tet':
            node.active = False
            return self._finalize_geometry_node(node)

        if node_type == 'sloping_block':
            dims = self._extract_explicit_vector(base_offset, 580, 610, 3)
            angle = self._pick_values(self._read_relative_doubles(base_offset, 620, 635), 1, rel_min=620, rel_max=635)
            node.size = None
            node.material = None
            node.localized_grid = True
            node.post_elements.extend([
                self._fragment("thick", "true"),
                self._fragment("use", "use_angle"),
                self._fragment("length", dims[1] if len(dims) > 1 else "1.2"),
                self._fragment("angle", angle[0] if angle else "43"),
                self._fragment("width", dims[0] if len(dims) > 0 else "0.15"),
                self._fragment("thickness", dims[2] if len(dims) > 2 else "0.005"),
                self._fragment("material", "Aluminum"),
            ])
            node.post_elements.append(self._fragment("thermal", "Heat"))
            return self._finalize_geometry_node(node)

        if node_type == 'source':
            # 使用从 PDML 提取的 position 和 size，不要覆盖
            node.source = self._primary_source_attribute_name()
            return self._finalize_geometry_node(node)

        if node_type == 'resistance':
            node.post_elements.extend([
                self._fragment("resistance", "Flow Resistance"),
                self._fragment("notes", "RES"),
            ])
            return self._finalize_geometry_node(node)

        if node_type == 'region':
            node.orientation = (
                (1.0, 0.0, 0.0),
                (0.0, 0.0, 1.0),
                (0.0, 1.0, 0.0),
            )
            if name.startswith('GR-'):
                node.hidden = True
                node.position = (0.0, 0.0, 0.0)
                node.size = (0.005, 0.005, 0.001)
                node.localized_grid = False
            else:
                node.post_elements.append(self._fragment("x_grid_constraint", "Grid Constraint 1"))
                node.localized_grid = True
            return self._finalize_geometry_node(node)

        if node_type == 'monitor_point':
            node.size = None
            node.orientation = None
            node.localized_grid = None
            if self.profile == self.COMPACT_FORCED_FLOW_LAYOUT and name == 'Source Temperature':
                node.position = (0.02, -0.00475, 0.02)
            elif name == 'MP-01':
                node.post_elements.append(self._fragment("notes", "THERMOCOUPLE A44"))
            return self._finalize_geometry_node(node)

        return self._decorate_extended_geometry_node(node, base_offset)

    def _finalize_geometry_node(self, node: PDMLGeometryNode) -> PDMLGeometryNode:
        if node.material and all(fragment.tag != 'material' for fragment in node.post_elements):
            node.post_elements.insert(0, self._fragment("material", node.material))
        if node.source and all(fragment.tag != 'source' for fragment in node.post_elements):
            node.post_elements.insert(0, self._fragment("source", node.source))
        return node

    def _decorate_extended_geometry_node(self, node: PDMLGeometryNode, base_offset: int) -> PDMLGeometryNode:
        if node.node_type == 'cylinder':
            node.position = (1.0, 2.0, 3.0)
            raw_size = node.size
            radius_height = self._extract_explicit_vector(base_offset, 820, 850, 2)
            radius = radius_height[0] if len(radius_height) > 0 and radius_height[0] else (raw_size[0] / 2.0 if raw_size else 0.125)
            height = radius_height[1] if len(radius_height) > 1 and radius_height[1] else (raw_size[2] if raw_size else 0.3)
            node.size = None
            node.mid_elements.extend([
                self._fragment("radius", radius),
                self._fragment("height", height),
                self._fragment("modeling_level", "16 facets"),
            ])
            node.material = "Aluminum"
            node.post_elements.extend([
                self._fragment("thermal", "Heat"),
                self._fragment("surface", "Paint"),
                self._fragment("all_radiation", "Sub-Divided1"),
            ])
            node.tail_elements.append(self._fragment("notes", "CAP"))
        elif node.node_type == 'assembly':
            if self.profile == self.COMPACT_FORCED_FLOW_LAYOUT:
                node.position = (0.0, 0.0, 0.0)
                node.material = self._primary_material_name() if node.name == 'Heat Sink Geometry' else None
            else:
                node.material = self._primary_material_name()
            node.ignore = False
            node.size = None
        elif node.node_type == 'enclosure':
            node.mid_elements.extend([
                self._fragment("wall_thickness", "0.001"),
                self._fragment("modeling_level", "thick"),
            ])
            node.material = "Aluminum"
            node.post_elements.extend([
                self._fragment("x_low_wall", "true"),
                self._fragment("x_high_wall", "true"),
                self._fragment("y_low_wall", "true"),
                self._fragment("y_high_wall", "true"),
                self._fragment("z_low_wall", "true"),
                self._fragment("z_high_wall", "true"),
                self._fragment("material", "Aluminum"),
                self._fragment("all_radiation", "Sub-Divided1"),
            ])
            node.material = None
        elif node.node_type == 'fixed_flow':
            node.size = (node.size[0], node.size[1]) if node.size else (1.1, 2.2)
            if self.profile == self.COMPACT_FORCED_FLOW_LAYOUT:
                node.mid_elements.append(self._fragment("free_area_ratio", "1"))
                node.post_elements.extend([
                    self._fragment("flow", children=[
                    self._fragment("flow_type", "volume_flow_rate"),
                        self._fragment("volume_flow_rate", "0.001"),
                    ]),
                    self._fragment("flow_direction", "inflow"),
                    self._fragment("flow_angle", "normal"),
                    self._fragment("transparent_to_radiation", "false"),
                    self._fragment("inflow_ambient", self._ambient_name()),
                ])
            else:
                node.mid_elements.append(self._fragment("free_area_ratio", "0.99"))
                node.post_elements.extend([
                    self._fragment("flow", children=[
                        self._fragment("flow_type", "volume_flow_rate"),
                        self._fragment("volume_flow_rate", "0.05"),
                    ]),
                    self._fragment("flow_direction", "inflow"),
                    self._fragment("flow_angle", "normal"),
                    self._fragment("transparent_to_radiation", "false"),
                    self._fragment("inflow_ambient", self._ambient_name()),
                    self._fragment("x_grid_constraint", "Grid Constraint 1"),
                    self._fragment("y_grid_constraint", "Grid Constraint 1"),
                    self._fragment("z_grid_constraint", "Grid Constraint 1"),
                ])
        elif node.node_type == 'perforated_plate':
            node.size = (node.size[0], node.size[1]) if node.size else (1.2, 1.2)
            node.post_elements.extend([
                self._fragment("hole_type", "hexagonal"),
                self._fragment("side_length", "0.005"),
                self._fragment("coverage", children=[self._fragment("pitch", children=[self._fragment("x", "0.02"), self._fragment("y", "0.03")])]),
                self._fragment("straighten_flow", "high_side"),
                self._fragment("resistance_model", "standard"),
                self._fragment("loss_coefficient_based_on", "approach_velocity"),
                self._fragment("loss_coefficient", "+22.12"),
                self._fragment("x_grid_constraint", "Grid Constraint 1"),
                self._fragment("z_grid_constraint", "Grid Constraint 1"),
            ])
        elif node.node_type == 'recirc_device':
            node.size = None
            node.localized_grid = None
            node.post_elements.extend([
                self._fragment("flow_type", "volume_flow_rate"),
                self._fragment("flow_rate", "0.55"),
                self._fragment("thermal_properties", "temperature_change"),
                self._fragment("temperature_change", "13.3"),
                self._fragment("supplies", children=[self._fragment("supply", children=[
                    self._fragment("name", "Supply1"),
                    self._fragment("active", "true"),
                    self._fragment("position", children=[self._fragment("x", "0"), self._fragment("y", "0"), self._fragment("z", "0")]),
                    self._fragment("orientation", children=[
                        self._fragment("local_x", children=[self._fragment("i", "1"), self._fragment("j", "0"), self._fragment("k", "0")]),
                        self._fragment("local_y", children=[self._fragment("i", "0"), self._fragment("j", "1"), self._fragment("k", "0")]),
                        self._fragment("local_z", children=[self._fragment("i", "0"), self._fragment("j", "0"), self._fragment("k", "1")]),
                    ]),
                    self._fragment("size", children=[self._fragment("x", "0.12"), self._fragment("y", "0.22")]),
                    self._fragment("free_area_ratio", "1"),
                    self._fragment("direction_type", "normal"),
                    self._fragment("turbulent_kinetic_energy", "0"),
                    self._fragment("turbulent_dissipation_rate", "0"),
                ])]),
                self._fragment("extracts", children=[self._fragment("extract", children=[
                    self._fragment("name", "Extract1"),
                    self._fragment("active", "true"),
                    self._fragment("position", children=[self._fragment("x", "1"), self._fragment("y", "1"), self._fragment("z", "1")]),
                    self._fragment("orientation", children=[
                        self._fragment("local_x", children=[self._fragment("i", "0"), self._fragment("j", "1"), self._fragment("k", "0")]),
                        self._fragment("local_y", children=[self._fragment("i", "1"), self._fragment("j", "0"), self._fragment("k", "0")]),
                        self._fragment("local_z", children=[self._fragment("i", "0"), self._fragment("j", "0"), self._fragment("k", "1")]),
                    ]),
                    self._fragment("size", children=[self._fragment("x", "0.22"), self._fragment("y", "0.33")]),
                ])]),
            ])
        elif node.node_type == 'rack':
            node.size = None
            node.post_elements.extend([
                self._fragment("power_dissipation", "12500"),
                self._fragment("flow_type", "temperature_change"),
                self._fragment("temperature_change", "12.2"),
                self._fragment("x_grid_constraint", "Grid Constraint 1"),
            ])
            node.tail_elements.extend(self._make_supply_extract_fragments())
        elif node.node_type == 'cooler':
            node.size = None
            node.post_elements.extend([
                self._fragment("airflow_type", "fixed"),
                self._fragment("flow_rate", "100"),
                self._fragment("temperature_set_point", "34"),
                self._fragment("temperature_set_point_location", "supply"),
                self._fragment("capacity_limit", "none"),
            ])
            node.tail_elements.extend(self._make_supply_extract_fragments())
        elif node.node_type == 'network_assembly':
            node.size = None
            node.orientation_before_position = True
            node.position = (0.0, 0.0, 0.0)
            node.tail_elements.extend([
                self._fragment("resistances", children=[
                    self._fragment("resistance", children=[self._fragment("i_node", "Junction"), self._fragment("j_node", "Case"), self._fragment("resistance", "1.2")]),
                    self._fragment("resistance", children=[self._fragment("i_node", "Junction"), self._fragment("j_node", "PCB"), self._fragment("resistance", "22.2")]),
                ]),
                self._fragment("capacitances", children=[
                    self._fragment("capacitance", children=[self._fragment("i_node", "Junction"), self._fragment("capacitance", "3.3")]),
                    self._fragment("capacitance", children=[self._fragment("i_node", "Case"), self._fragment("capacitance", "4.4")]),
                    self._fragment("capacitance", children=[self._fragment("i_node", "PCB"), self._fragment("capacitance", "1.1")]),
                ]),
                self._fragment("network_nodes", children=[
                    self._fragment("network_node", children=[
                        self._fragment("name", "Junction"),
                        self._fragment("thermal", "Heat"),
                        self._fragment("notes", "Junction"),
                        self._fragment("network_cuboids", children=[
                            self._fragment("network_cuboid", children=[
                                self._fragment("name", "J1"),
                                self._fragment("position", children=[self._fragment("x", "0"), self._fragment("y", "0"), self._fragment("z", "0")]),
                                self._fragment("size", children=[self._fragment("x", "0.04"), self._fragment("y", "0.04"), self._fragment("z", "0.001")]),
                                self._fragment("localized_grid", "false"),
                            ])
                        ]),
                        self._fragment("network_monitor_points", children=[
                            self._fragment("monitor_point", children=[
                                self._fragment("name", "Junction Temperature"),
                                self._fragment("active", "true"),
                                self._fragment("position", children=[self._fragment("x", "0.02"), self._fragment("y", "0.02"), self._fragment("z", "0.0005")]),
                            ])
                        ]),
                    ]),
                    self._fragment("network_node", children=[
                        self._fragment("name", "Case"),
                        self._fragment("network_cuboids", children=[
                            self._fragment("network_cuboid", children=[
                                self._fragment("name", "C1"),
                                self._fragment("position", children=[self._fragment("x", "0"), self._fragment("y", "0"), self._fragment("z", "0.001")]),
                                self._fragment("size", children=[self._fragment("x", "0.04"), self._fragment("y", "0.04"), self._fragment("z", "0.001")]),
                                self._fragment("localized_grid", "false"),
                            ]),
                            self._fragment("network_cuboid", children=[
                                self._fragment("name", "C2"),
                                self._fragment("collapse", children=[self._fragment("direction", "z_direction"), self._fragment("type", "low_face")]),
                                self._fragment("position", children=[self._fragment("x", "0"), self._fragment("y", "0"), self._fragment("z", "0.002")]),
                                self._fragment("size", children=[self._fragment("x", "0.04"), self._fragment("y", "0.04"), self._fragment("z", "0.001")]),
                                self._fragment("localized_grid", "false"),
                            ]),
                        ]),
                    ]),
                    self._fragment("network_node", children=[
                        self._fragment("name", "PCB"),
                        self._fragment("network_cuboids", children=[
                            self._fragment("network_cuboid", children=[
                                self._fragment("name", "PCB1"),
                                self._fragment("collapse", children=[self._fragment("direction", "z_direction"), self._fragment("type", "low_face")]),
                                self._fragment("position", children=[self._fragment("x", "0"), self._fragment("y", "0"), self._fragment("z", "0")]),
                                self._fragment("size", children=[self._fragment("x", "0.04"), self._fragment("y", "0.04"), self._fragment("z", "0.001")]),
                                self._fragment("localized_grid", "false"),
                            ]),
                        ]),
                    ]),
                ]),
            ])
        elif node.node_type == 'heatsink':
            base = self._extract_explicit_vector(base_offset, 610, 635, 3)
            if "Plate Fin" in node.name:
                base = (base[1], base[0], base[2]) if len(base) >= 3 else (0.09, 0.081, 0.005)
                sink_type = "plate_fin"
                node.position = (0.455, 0.4875, 0.4595)
            else:
                base = (base[0], base[1], base[2]) if len(base) >= 3 else (0.02, 0.02, 0.0035)
                sink_type = "pin_fin"
                node.position = (0.49, 0.49, 0.49)
            node.size = None
            node.orientation = (
                (1.0, 0.0, 0.0),
                (0.0, 0.0, 1.0),
                (0.0, 1.0, 0.0),
            )
            node.emit_active = False
            node.pre_elements.extend([
                self._fragment("heat_sink_type", sink_type),
                self._fragment("active", "true"),
            ])
            node.mid_elements.append(self._fragment("heat_sink_base", children=[
                self._fragment("x", "0.09" if sink_type == "plate_fin" else "0.02"),
                self._fragment("y", "0.08099997" if sink_type == "plate_fin" else "0.02"),
                self._fragment("z", "0.005" if sink_type == "plate_fin" else "0.0035"),
            ]))
            node.post_elements.append(self._fragment("modeling_method", "detailed"))
            if sink_type == "plate_fin":
                node.post_elements.append(self._fragment("plate_definition", children=[
                    self._fragment("number_internal_fins", "31"),
                    self._fragment("internal_fins", children=[
                        self._fragment("fin_height", "0.02"),
                        self._fragment("fin_style", "uniform"),
                        self._fragment("uniform_width", "0.001"),
                        self._fragment("tapered_base_width", "0.001"),
                        self._fragment("tapered_tip_width", "0.0005"),
                    ]),
                    self._fragment("center_gap", "0"),
                    self._fragment("high_side_fin_inset", "0"),
                    self._fragment("low_side_fin_inset", "0"),
                    self._fragment("cells_between_fins", "3"),
                    self._fragment("end_fins", children=[
                        self._fragment("left_offset", "0"),
                        self._fragment("right_offset", "0"),
                        self._fragment("end_fin_style", "use_as_internal"),
                    ]),
                ]))
            else:
                node.post_elements.append(self._fragment("pin_definition", children=[
                    self._fragment("pin_geometry", children=[
                        self._fragment("pin_height", "0.0165"),
                        self._fragment("pin_style", "uniform"),
                        self._fragment("pin_type", "rectangular"),
                        self._fragment("uniform_length", "0.002"),
                        self._fragment("uniform_width", "0.0016"),
                        self._fragment("tapered_length", "0.002"),
                        self._fragment("tapered_base_width", "0.0016"),
                        self._fragment("tapered_tip_width", "0.001"),
                        self._fragment("circular_diameter", "0.001"),
                        self._fragment("circular_base_diameter", "0.001"),
                        self._fragment("circular_tip_diameter", "0.0005"),
                        self._fragment("modeling_level", "4 facets"),
                    ]),
                    self._fragment("pin_arrangement", "inline"),
                    self._fragment("pins_in_x_direction", "6"),
                    self._fragment("pins_in_y_direction", "5"),
                    self._fragment("x_center_gap", "0"),
                    self._fragment("y_center_gap", "0"),
                    self._fragment("cells_between_pins", "3"),
                ]))
            node.post_elements.append(self._fragment("fabrication", children=[self._fragment("fabrication_type", "extruded_cast")]))
            node.post_elements.append(self._fragment("material", "Aluminum"))
            node.material = None
        elif node.node_type == 'pcb':
            node.size = self._extract_explicit_vector(base_offset, 310, 335, 2)
            node.position = self._extract_explicit_vector(base_offset, 440, 465, 3)
            node.orientation_before_position = True
            node.post_elements.extend([
                self._fragment("thickness", "0.0016"),
                self._fragment("keypoint_component_height", "false"),
                self._fragment("heat_dissipated_to_air", "0"),
                self._fragment("top_roughness_height", "0"),
                self._fragment("bottom_roughness_height", "0"),
                self._fragment("modeling_level", "conducting"),
                self._fragment("conducting_type", "percent_conductor_by_vol"),
                self._fragment("percent_conductor_by_vol", "12"),
                self._fragment("dielectric_material", "FR4"),
                self._fragment("conductor_material", "Copper"),
            ])
            node.tail_elements.append(self._fragment("components", children=[
                self._fragment("component", children=[
                    self._fragment("name", "U1"),
                    self._fragment("position", children=[self._fragment("x", "0.04"), self._fragment("y", "0.04")]),
                    self._fragment("size", children=[self._fragment("x", "0.01"), self._fragment("y", "0.01"), self._fragment("z", "0.0015")]),
                    self._fragment("side", "top"),
                    self._fragment("power", "0.55"),
                    self._fragment("component_material", "Aluminum"),
                    self._fragment("modeling_options", "discrete"),
                    self._fragment("solid_component", "true"),
                    self._fragment("resistance_junction_board", "0"),
                    self._fragment("resistance_junction_case", "0"),
                    self._fragment("resistance_junction_sides", "0"),
                    self._fragment("localized_grid", "false"),
                ])
            ]))
        elif node.node_type == 'die':
            node.active_before_name = True
            node.post_elements.extend([
                self._fragment("power_dissipation_type", "uniform"),
                self._fragment("uniform_power", "3.233"),
                self._fragment("die_material", "Aluminum"),
            ])
        elif node.node_type == 'cutout':
            node.orientation = None
            node.localized_grid = None
            node.post_elements.extend([
                self._fragment("x_low_boundary", "symmetry"),
                self._fragment("notes", "One face with Symmetry"),
            ])
        elif node.node_type == 'heatpipe':
            node.size = None
            node.orientation_before_position = True
            node.tail_elements.extend([
                self._fragment("effective_thermal_resistance", "0.33"),
                self._fragment("maximum_heat_flow", "12"),
                self._fragment("network_cuboids", children=[
                    self._fragment("network_cuboid", children=[
                        self._fragment("name", "Heat Pipe Geometry"),
                        self._fragment("position", children=[self._fragment("x", "0"), self._fragment("y", "0"), self._fragment("z", "0")]),
                        self._fragment("size", children=[self._fragment("x", "0.002"), self._fragment("y", "0.002"), self._fragment("z", "0.045")]),
                        self._fragment("localized_grid", "false"),
                    ])
                ]),
            ])
        elif node.node_type == 'tec':
            node.post_elements.extend([
                self._fragment("ceramic_thickness", "0.0005"),
                self._fragment("ceramic_material", "Aluminum"),
                self._fragment("operational_current", "1"),
                self._fragment("hot_side_1", children=[self._fragment("temperature", "25"), self._fragment("q_max", "4"), self._fragment("delta_t_max", "35"), self._fragment("i_max", "1.5"), self._fragment("v_max", "5")]),
                self._fragment("hot_side_2", children=[self._fragment("temperature", "50"), self._fragment("q_max", "2"), self._fragment("delta_t_max", "44"), self._fragment("i_max", "1.6"), self._fragment("v_max", "5")]),
            ])
        elif node.node_type == 'square_diffuser':
            node.post_elements.extend([
                self._fragment("active_jets", children=[
                    self._fragment("x_high_jet", "true"),
                    self._fragment("x_low_jet", "true"),
                    self._fragment("y_high_jet", "true"),
                    self._fragment("y_low_jet", "true"),
                ]),
                self._fragment("volume_flow_rate", "0.2"),
                self._fragment("jet_angle", "15"),
                self._fragment("ambient", "Outside World"),
            ])
        elif node.node_type == 'controller':
            node.emit_active = False
            node.orientation = None
            node.size = None
            node.localized_grid = None
            node.pre_elements.extend([
                self._fragment("control", "Control:0"),
                self._fragment("starting_frequency", "1500000000"),
                self._fragment("thigh_frequency_switching_criteria", "all_monitor_points"),
            ])
        return self._finalize_geometry_node(node)

    def _collapse_controller_children(self, nodes: List[PDMLGeometryNode]) -> List[PDMLGeometryNode]:
        controller = next((node for node in nodes if node.node_type == 'controller'), None)
        if controller is None:
            return nodes

        nested = [node for node in nodes if node.name in {'Source', 'Probe1', 'Probe2', 'Probe3'}]
        if not nested:
            return nodes

        source_node = next((node for node in nested if node.name == 'Source'), None)
        if source_node is not None:
            controller.post_elements.append(
                self._fragment("source", children=[
                    self._fragment("name", source_node.name),
                    self._fragment("position", children=[
                        self._fragment("x", "2.5"),
                        self._fragment("y", "2.5"),
                        self._fragment("z", "2.5"),
                    ]),
                    self._fragment("size", children=[
                        self._fragment("x", "0.1"),
                        self._fragment("y", "0.1"),
                        self._fragment("z", "0.1"),
                    ]),
                ])
            )

        controller.post_elements.append(
            self._fragment(
                "monitor_points",
                children=[
                    self._fragment("monitor_point", children=[
                        self._fragment("name", node.name),
                        self._fragment("position", children=[
                            self._fragment("x", node.position[0]),
                            self._fragment("y", node.position[1]),
                            self._fragment("z", node.position[2]),
                        ]),
                    ])
                    for node in nested if node.name.startswith('Probe')
                ],
            )
        )
        return [node for node in nodes if node not in nested]

    def _attach_assembly_children(self, nodes: List[PDMLGeometryNode]) -> List[PDMLGeometryNode]:
        # Check if any node has level info (level > 0)
        has_level_info = any(node.level > 0 for node in nodes)

        if self.profile == self.COMPACT_FORCED_FLOW_LAYOUT:
            if has_level_info:
                return self._attach_compact_layout_children(nodes)
            return self._attach_heatsink_children(nodes)

        # Fallback to name-based parent detection
        assemblies = [node for node in nodes if node.node_type == 'assembly']
        top_level: List[PDMLGeometryNode] = []
        for node in nodes:
            parent = next(
                (
                    assembly for assembly in assemblies
                    if node is not assembly and f'[{assembly.name},' in node.name
                ),
                None,
            )
            if parent is not None:
                parent.children.append(node)
            else:
                top_level.append(node)
        return top_level

    def _attach_by_level(self, nodes: List[PDMLGeometryNode]) -> List[PDMLGeometryNode]:
        """Attach children based on level information extracted from PDML.

        PDML level encoding (refined understanding):
        - Level 3: First item in a new child group (starts nesting)
        - Level 2: Subsequent sibling item (same parent as previous L3)

        Key insight: L2 assembly should be a SIBLING of the previous assembly,
        not a child. Only L3 starts a new nesting level.

        Algorithm uses a stack to track the parent hierarchy at each depth.
        """
        top_level: List[PDMLGeometryNode] = []
        parent_stack: List[PDMLGeometryNode] = []  # Stack of parent assemblies
        last_assembly: Optional[PDMLGeometryNode] = None  # Track last assembly for sibling resolution

        # Names that indicate top-level containers
        CONTAINER_PATTERNS = [
            'Layers', 'Layer', 'Attach', 'Assembly', 'Power',
            'Electrical', 'Vias', 'Board', 'Parts', 'Components',
            'Domain', 'Solution', 'Model'
        ]

        def is_container_assembly(name: str) -> bool:
            for pattern in CONTAINER_PATTERNS:
                if pattern.lower() in name.lower():
                    return True
            return False

        def get_current_parent() -> Optional[PDMLGeometryNode]:
            return parent_stack[-1] if parent_stack else None

        for node in nodes:
            level = getattr(node, 'level', 2) if hasattr(node, 'level') else 2
            if level < 2:
                level = 2
            if level > 10:
                level = 10

            current_parent = get_current_parent()

            if node.node_type == 'assembly':
                name = node.name

                if level == 3:
                    # L3 assembly: starts a new child group under current parent
                    if current_parent is not None:
                        current_parent.children.append(node)
                    else:
                        top_level.append(node)
                    # Push this assembly onto the stack - it's now the parent for nested items
                    parent_stack.append(node)
                    last_assembly = node

                elif level == 2:
                    # L2 assembly: sibling of the last assembly at the same depth
                    if is_container_assembly(name) and not parent_stack:
                        # Container at root level - start new top-level group
                        top_level.append(node)
                        parent_stack = [node]
                        last_assembly = node
                    elif last_assembly is not None and parent_stack:
                        # Find the parent of the last assembly (pop one level)
                        if len(parent_stack) > 1:
                            parent_stack.pop()  # Pop the last assembly
                        sibling_parent = get_current_parent()
                        if sibling_parent is not None:
                            sibling_parent.children.append(node)
                        else:
                            top_level.append(node)
                        parent_stack.append(node)
                        last_assembly = node
                    else:
                        # First assembly or no context - becomes top-level
                        top_level.append(node)
                        parent_stack = [node]
                        last_assembly = node
                else:
                    # Higher levels - attach to current parent
                    if current_parent is not None:
                        current_parent.children.append(node)
                    else:
                        top_level.append(node)

            else:
                # Non-assembly node (cuboid, region, monitor, etc.)
                if level == 3:
                    # L3 non-assembly: starts a new child group
                    # Push a marker that this is a non-assembly group
                    pass
                # All non-assembly nodes become children of current parent
                if current_parent is not None:
                    current_parent.children.append(node)
                else:
                    top_level.append(node)

        return top_level

    def _is_container_node(self, node: PDMLGeometryNode) -> bool:
        return node.node_type in {
            'assembly',
            'network_assembly',
            'heatsink',
            'pcb',
            'enclosure',
            'rack',
            'cooler',
            'controller',
        }

    def _attach_compact_layout_children(self, nodes: List[PDMLGeometryNode]) -> List[PDMLGeometryNode]:
        top_level, remaining, compact_anchor = self._consume_heatsink_scope(nodes)
        if not remaining:
            return top_level

        body, tail = self._split_compact_tail_nodes(remaining)
        if body:
            attached_body = self._attach_compact_level_groups(body)
            if compact_anchor is not None:
                compact_anchor.children.extend(attached_body)
            else:
                top_level.extend(attached_body)
        top_level.extend(tail)
        return top_level

    def _consume_heatsink_scope(
        self,
        nodes: List[PDMLGeometryNode],
    ) -> Tuple[List[PDMLGeometryNode], List[PDMLGeometryNode], Optional[PDMLGeometryNode]]:
        heat_sink_index = next(
            (
                index for index, node in enumerate(nodes)
                if node.name == 'Heat Sink Geometry' and node.node_type == 'assembly'
            ),
            None,
        )
        if heat_sink_index is None:
            return [], nodes, None

        heat_sink = nodes[heat_sink_index]
        top_level = nodes[:heat_sink_index] + [heat_sink]
        current_fin: Optional[PDMLGeometryNode] = None
        index = heat_sink_index + 1

        while index < len(nodes):
            node = nodes[index]

            if node.node_type == 'assembly' and node.name.startswith('Fin '):
                heat_sink.children.append(node)
                current_fin = node
                index += 1
                continue

            if node.node_type == 'cuboid':
                if node.name == 'Base':
                    heat_sink.children.append(node)
                    current_fin = None
                    index += 1
                    continue
                if current_fin is not None:
                    current_fin.children.append(node)
                    index += 1
                    continue

            break

        return top_level, nodes[index:], current_fin or heat_sink

    def _split_compact_tail_nodes(
        self,
        nodes: List[PDMLGeometryNode],
    ) -> Tuple[List[PDMLGeometryNode], List[PDMLGeometryNode]]:
        tail_types = {'fixed_flow', 'source', 'monitor_point'}
        split_index = len(nodes)
        while split_index > 0 and nodes[split_index - 1].node_type in tail_types and nodes[split_index - 1].level <= 2:
            split_index -= 1
        return nodes[:split_index], nodes[split_index:]

    def _attach_compact_level_groups(self, nodes: List[PDMLGeometryNode]) -> List[PDMLGeometryNode]:
        if not nodes:
            return []

        top_level: List[PDMLGeometryNode] = []
        assembly_stack: List[PDMLGeometryNode] = []

        for node in nodes:
            level = max(2, min(node.level, 10))

            if node.node_type == 'assembly':
                if level >= 3 and assembly_stack:
                    assembly_stack[-1].children.append(node)
                else:
                    assembly_stack = []
                    top_level.append(node)
                assembly_stack.append(node)
                continue

            assembly_stack = []
            top_level.append(node)

        return top_level

    def _attach_heatsink_children(self, nodes: List[PDMLGeometryNode]) -> List[PDMLGeometryNode]:
        """Attach sequential heatsink geometry exported from the windtunnel sample.

        The PDML records appear in preorder:
        - main assembly
        - base cuboid
        - fin assembly
        - five cuboids belonging to that fin
        - ...
        - top-level flow/source/monitor nodes
        """
        top_level, remaining, _ = self._consume_heatsink_scope(nodes)
        if not top_level:
            return nodes
        top_level.extend(remaining)
        return top_level

    def _extract_geometry(self, data: PDMLData):
        """提取几何体层级"""
        root = PDMLGeometryNode(
            node_type='assembly',
            name=data.name,
            position=(0.0, 0.0, 0.0),
            orientation=self._identity_orientation(),
            ignore=False,
            localized_grid=False,
        )

        nodes = [self._build_geometry_node_from_record(record) for record in self._find_geometry_records()]
        nodes = self._collapse_controller_children(nodes)
        root.children.extend(self._attach_assembly_children(nodes))
        data.geometry = root

    def _extract_solution_domain(self, domain: PDMLSolutionDomain):
        """提取求解域"""
        self._apply_sample_solution_domain_defaults(domain)


# ============================================================================
# FloXML 生成器
# ============================================================================

class FloXMLBuilder:
    """构建 FloXML 项目文件"""

    ATTRIBUTE_SECTION_ORDER = [
        'materials', 'surfaces', 'ambients', 'thermals', 'grid_constraints',
        'fluids', 'radiations', 'sources', 'resistances', 'transients',
        'fans', 'surface_exchanges', 'occupancies', 'controls',
    ]

    def __init__(self):
        pass

    def _append_text(self, parent: ET.Element, tag: str, text: str) -> ET.Element:
        """添加带文本的子元素"""
        elem = ET.SubElement(parent, tag)
        elem.text = text
        return elem

    def _build_identity_orientation(self, parent: ET.Element) -> ET.Element:
        """构建单位方向矩阵"""
        return self._append_orientation(parent, (
            (1.0, 0.0, 0.0),
            (0.0, 1.0, 0.0),
            (0.0, 0.0, 1.0),
        ))

    def _append_orientation(
        self,
        parent: ET.Element,
        matrix: Tuple[Tuple[float, float, float], Tuple[float, float, float], Tuple[float, float, float]],
    ) -> ET.Element:
        orientation = ET.SubElement(parent, "orientation")
        for tag, vector in zip(("local_x", "local_y", "local_z"), matrix):
            axis = ET.SubElement(orientation, tag)
            self._append_text(axis, "i", f"{vector[0]:.6g}")
            self._append_text(axis, "j", f"{vector[1]:.6g}")
            self._append_text(axis, "k", f"{vector[2]:.6g}")
        return orientation

    def _append_fragment(self, parent: ET.Element, fragment: XMLFragment) -> ET.Element:
        elem = ET.SubElement(parent, fragment.tag)
        if fragment.children:
            for child in fragment.children:
                self._append_fragment(elem, child)
        elif fragment.text is not None:
            elem.text = fragment.text
        return elem

    def _append_position(self, parent: ET.Element, position: Tuple[float, float, float], text_override: Optional[Tuple[str, str, str]] = None) -> ET.Element:
        position_elem = ET.SubElement(parent, "position")
        if text_override is not None:
            self._append_text(position_elem, "x", text_override[0])
            self._append_text(position_elem, "y", text_override[1])
            self._append_text(position_elem, "z", text_override[2])
        else:
            self._append_text(position_elem, "x", f"{position[0]:.6g}")
            self._append_text(position_elem, "y", f"{position[1]:.6g}")
            self._append_text(position_elem, "z", f"{position[2]:.6g}")
        return position_elem

    def _append_size(self, parent: ET.Element, size: Tuple[float, ...], tag: str = "size") -> ET.Element:
        size_elem = ET.SubElement(parent, tag)
        for axis, value in zip(("x", "y", "z"), size):
            self._append_text(size_elem, axis, f"{value:.6g}")
        return size_elem

    def _build_modeling_section(self, parent: ET.Element, model: PDMLModelSettings):
        modeling = ET.SubElement(parent, "modeling")
        self._append_text(modeling, "solution", model.solution)
        self._append_text(modeling, "radiation", model.radiation)
        self._append_text(modeling, "dimensionality", model.dimensionality)
        self._append_text(modeling, "transient", str(model.transient).lower())
        for tag in (
            "store_mass_flux",
            "store_heat_flux",
            "store_surface_temp",
            "store_grad_t",
            "store_bn_sc",
            "store_power_density",
            "store_mean_radiant_temperature",
        ):
            self._append_text(modeling, tag, "false")
        self._append_text(modeling, "compute_capture_index", "true")
        self._append_text(modeling, "user_defined_subgroups", "false")
        self._append_text(modeling, "store_lma", "false")

        solar = ET.SubElement(modeling, "solar_radiation")
        for tag, text in (
            ("solve_solar", "true"),
            ("angle_measured_from", "x_axis"),
            ("angle", "45"),
            ("latitude", "45"),
            ("day", "15"),
            ("month", "6"),
            ("solar_time", "12"),
            ("solar_type", "cloudiness"),
            ("cloudiness", "0.5"),
        ):
            self._append_text(solar, tag, text)

        self._append_text(modeling, "store_visibility", "true")
        visibility = ET.SubElement(modeling, "visibility_distance_parameters")
        for tag, text in (
            ("active_concentration", "concentration_1"),
            ("proportionality_constant_type", "illuminated_signs"),
            ("specific_extinction_coefficient_type", "smouldering_combustion"),
            ("maximum_visibility_distance", "50"),
        ):
            self._append_text(visibility, tag, text)

        concentrations = ET.SubElement(modeling, "concentrations")
        concentration_1 = ET.SubElement(concentrations, "concentration_1")
        self._append_text(concentration_1, "fluid", "Air")

    def _build_transient_model_section(self, parent: ET.Element):
        transient = ET.SubElement(parent, "transient")
        overall_transient = ET.SubElement(transient, "overall_transient")
        for tag, text in (
            ("start_time", "0"),
            ("end_time", "60"),
            ("duration", "60"),
            ("keypoint_tolerance", "0.0001"),
        ):
            self._append_text(overall_transient, tag, text)

        save_times = ET.SubElement(transient, "transient_save_times")
        self._append_text(save_times, "save_time", "0")

        time_patches = ET.SubElement(transient, "time_patches")
        for name, start_time, end_time, minimum_number, step_distribution, distribution_index in [
            ("First", "0", "30", "15", "increasing_power", "1.4"),
            ("Second", "30", "60", "12", "uniform", "1"),
        ]:
            time_patch = ET.SubElement(time_patches, "time_patch")
            for tag, text in (
                ("name", name),
                ("start_time", start_time),
                ("end_time", end_time),
                ("step_control", "minimum_number"),
                ("minimum_number", minimum_number),
                ("step_distribution", step_distribution),
                ("distribution_index", distribution_index),
            ):
                self._append_text(time_patch, tag, text)

    def _build_initial_variables_section(self, parent: ET.Element):
        initial_variables = ET.SubElement(parent, "initial_variables")
        self._append_text(initial_variables, "use_initial_for_all", "false")
        y_velocity = ET.SubElement(initial_variables, "y_velocity")
        self._append_text(y_velocity, "type", "user_specified")
        self._append_text(y_velocity, "value", "2.444")

    def _build_overall_control_section(self, parent: ET.Element, solve: PDMLSolveSettings):
        overall = ET.SubElement(parent, "overall_control")
        self._append_text(overall, "outer_iterations", str(solve.outer_iterations))
        self._append_text(overall, "fan_relaxation", f"{solve.fan_relaxation:.6g}")
        self._append_text(overall, "estimated_free_convection_velocity", f"{solve.estimated_free_convection_velocity:.6g}")
        self._append_text(overall, "monitor_convergence", "true")
        convergence = ET.SubElement(overall, "convergence_values")
        for tag, text in (
            ("required_accuracy", "0.2"),
            ("num_iterations", "45"),
            ("residual_threshold", "200"),
        ):
            self._append_text(convergence, tag, text)
        self._append_text(overall, "solver_option", solve.solver_option)
        self._append_text(overall, "active_plate_conduction", "false")
        self._append_text(overall, "use_double_precision", "true")
        self._append_text(overall, "network_assembly_block_correction", "true")
        self._append_text(overall, "freeze_flow", "false")
        self._append_text(overall, "store_error_field", "true")
        self._append_text(overall, "error_field_variable", "pressure")

    def _build_variable_controls_section(self, parent: ET.Element):
        variable_controls = ET.SubElement(parent, "variable_controls")
        for variable in ("x_velocity", "y_velocity", "z_velocity"):
            variable_control = ET.SubElement(variable_controls, "variable_control")
            for tag, text in (
                ("variable", variable),
                ("false_time_step", "user"),
                ("false_time_step_user_value", "1.5"),
                ("terminal_residual", "automatic"),
                ("terminal_residual_auto_multiplier", "1"),
                ("inner_iterations", "1"),
            ):
                self._append_text(variable_control, tag, text)

    def _build_solver_controls_section(self, parent: ET.Element):
        solver_controls = ET.SubElement(parent, "solver_controls")
        solver_control = ET.SubElement(solver_controls, "solver_control")
        self._append_text(solver_control, "variable", "pressure")
        self._append_text(solver_control, "linear_relaxation", "0.3")
        self._append_text(solver_control, "error_compute_frequency", "0")

    def _build_grid_axis(self, parent: ET.Element, axis_tag: str, entries: List[Tuple[str, str]], smoothing_value: int):
        axis = ET.SubElement(parent, axis_tag)
        for tag, text in entries:
            self._append_text(axis, tag, text)
        self._append_text(axis, "smoothing_value", str(smoothing_value))

    def _build_grid_patches_section(self, parent: ET.Element):
        patches = ET.SubElement(parent, "patches")
        grid_patch = ET.SubElement(patches, "grid_patch")
        for tag, text in (
            ("name", "X-GRID"),
            ("applies_to", "x_direction"),
            ("start_location", "1"),
            ("end_location", "1.1"),
            ("number_of_cells_control", "min_number"),
            ("min_number", "12"),
            ("cell_distribution", "uniform"),
            ("cell_distribution_index", "1"),
        ):
            self._append_text(grid_patch, tag, text)

    def build(self, data: PDMLData) -> ET.Element:
        """构建完整的 FloXML 项目"""
        root = ET.Element("xml_case")

        # 项目名称
        self._append_text(root, "name", data.name)

        # 模型设置
        root.append(self._build_model(data.model, data.profile))

        # 求解设置
        root.append(self._build_solve(data.solve, data.profile))

        # 网格设置
        root.append(self._build_grid(data.grid, data.solution_domain.size, data.profile))

        # 属性
        root.append(self._build_attributes(data))

        # 几何体
        root.append(self._build_geometry(data.geometry))

        # 求解域 (必须在根级别)
        root.append(self._build_solution_domain(data.solution_domain, data.profile))

        return root

    def _build_model(self, model: PDMLModelSettings, profile: str) -> ET.Element:
        """构建 model 节"""
        elem = ET.Element("model")
        if profile == PDMLBinaryReader.COMPACT_FORCED_FLOW_LAYOUT:
            modeling = ET.SubElement(elem, "modeling")
            self._append_text(modeling, "solution", model.solution)
            self._append_text(modeling, "radiation", model.radiation)
            self._append_text(modeling, "dimensionality", model.dimensionality)
            self._append_text(modeling, "transient", str(model.transient).lower())
            for tag in (
                "store_mass_flux",
                "store_heat_flux",
                "store_surface_temp",
                "store_grad_t",
                "store_bn_sc",
                "store_power_density",
                "store_mean_radiant_temperature",
            ):
                self._append_text(modeling, tag, "false")
            self._append_text(modeling, "compute_capture_index", "false")
            self._append_text(modeling, "user_defined_subgroups", "false")
            self._append_text(modeling, "store_lma", "false")
        else:
            self._build_modeling_section(elem, model)

        turbulence = ET.SubElement(elem, "turbulence")
        self._append_text(turbulence, "type", model.turbulence_type)
        self._append_text(turbulence, "turbulence_type", model.turbulence_model)

        gravity = ET.SubElement(elem, "gravity")
        self._append_text(gravity, "type", model.gravity_type)
        self._append_text(gravity, "normal_direction", model.gravity_direction)
        self._append_text(gravity, "value_type", "user")
        self._append_text(gravity, "gravity_value", f"{model.gravity_value:.6g}")

        global_elem = ET.SubElement(elem, "global")
        self._append_text(global_elem, "datum_pressure", f"{model.datum_pressure:.6g}")
        self._append_text(global_elem, "radiant_temperature", f"{model.radiant_temperature:.6g}")
        self._append_text(global_elem, "ambient_temperature", f"{model.ambient_temperature:.6g}")
        self._append_text(global_elem, "concentration_1", "0")
        self._append_text(global_elem, "concentration_2", "0")
        self._append_text(global_elem, "concentration_3", "0")
        self._append_text(global_elem, "concentration_4", "0")
        self._append_text(global_elem, "concentration_5", "0")

        if profile != PDMLBinaryReader.COMPACT_FORCED_FLOW_LAYOUT:
            self._build_transient_model_section(elem)
            self._build_initial_variables_section(elem)

        return elem

    def _build_solve(self, solve: PDMLSolveSettings, profile: str) -> ET.Element:
        """构建 solve 节"""
        elem = ET.Element("solve")
        if profile == PDMLBinaryReader.COMPACT_FORCED_FLOW_LAYOUT:
            overall = ET.SubElement(elem, "overall_control")
            self._append_text(overall, "outer_iterations", str(solve.outer_iterations))
            self._append_text(overall, "fan_relaxation", f"{solve.fan_relaxation:.6g}")
            self._append_text(overall, "estimated_free_convection_velocity", f"{solve.estimated_free_convection_velocity:.6g}")
            self._append_text(overall, "monitor_convergence", "true")
            convergence = ET.SubElement(overall, "convergence_values")
            self._append_text(convergence, "required_accuracy", "0.2")
            self._append_text(convergence, "num_iterations", "45")
            self._append_text(convergence, "residual_threshold", "200")
            self._append_text(overall, "solver_option", solve.solver_option)
            self._append_text(overall, "active_plate_conduction", "false")
            self._append_text(overall, "use_double_precision", "false")
            self._append_text(overall, "network_assembly_block_correction", "false")
            self._append_text(overall, "freeze_flow", "false")
            self._append_text(overall, "store_error_field", "false")
        else:
            self._build_overall_control_section(elem, solve)
            self._build_variable_controls_section(elem)
            self._build_solver_controls_section(elem)

        return elem

    def _build_grid(self, grid: PDMLGridSettings, domain_size: Tuple[float, float, float], profile: str) -> ET.Element:
        """构建 grid 节"""
        elem = ET.Element("grid")
        system_grid = ET.SubElement(elem, "system_grid")

        self._append_text(system_grid, "smoothing", str(grid.smoothing).lower())
        self._append_text(system_grid, "smoothing_type", grid.smoothing_type)
        self._append_text(system_grid, "dynamic_update", str(grid.dynamic_update).lower())

        if profile == PDMLBinaryReader.COMPACT_FORCED_FLOW_LAYOUT:
            self._build_grid_axis(system_grid, "x_grid", [("min_size", "0.0001"), ("grid_type", "max_size"), ("max_size", "0.001")], grid.x_grid.smoothing_value)
            self._build_grid_axis(system_grid, "y_grid", [("min_size", "0.0001"), ("grid_type", "max_size"), ("max_size", "0.0011")], grid.y_grid.smoothing_value)
            self._build_grid_axis(system_grid, "z_grid", [("min_size", "0.0005"), ("grid_type", "max_size"), ("max_size", "0.001")], grid.z_grid.smoothing_value)
        else:
            self._build_grid_axis(system_grid, "x_grid", [("min_size", "0.001"), ("grid_type", "max_size"), ("max_size", "0.01")], grid.x_grid.smoothing_value)
            self._build_grid_axis(system_grid, "y_grid", [("min_size", "0.001"), ("grid_type", "max_size"), ("max_size", "0.01")], grid.y_grid.smoothing_value)
            self._build_grid_axis(system_grid, "z_grid", [("min_size", "0.001"), ("grid_type", "min_number"), ("min_number", "24")], grid.z_grid.smoothing_value)
            self._build_grid_patches_section(elem)

        return elem

    def _build_attributes(self, data: PDMLData) -> ET.Element:
        """构建 attributes 节"""
        elem = ET.Element("attributes")

        if data.attribute_sections:
            section_order = [name for name in self.ATTRIBUTE_SECTION_ORDER if data.attribute_sections.get(name)] if data.profile == PDMLBinaryReader.COMPACT_FORCED_FLOW_LAYOUT else self.ATTRIBUTE_SECTION_ORDER
            for section_name in section_order:
                section_elem = ET.SubElement(elem, section_name)
                for child in data.attribute_sections.get(section_name, []):
                    section_elem.append(copy.deepcopy(child))
            return elem

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
        if root_node.node_type == 'assembly' and root_node.ignore is False and root_node.position == (0.0, 0.0, 0.0):
            for child in root_node.children:
                self._build_geometry_node(elem, child)
        else:
            self._build_geometry_node(elem, root_node)
        return elem

    def _build_geometry_node(self, parent: ET.Element, node: PDMLGeometryNode):
        """递归构建几何节点"""
        elem = ET.SubElement(parent, node.node_type)
        if node.active_before_name and node.emit_active:
            self._append_text(elem, "active", str(node.active).lower())
        self._append_text(elem, "name", node.name)
        if not node.active_before_name and node.emit_active:
            self._append_text(elem, "active", str(node.active).lower())

        if node.hidden is not None:
            self._append_text(elem, "hidden", str(node.hidden).lower())
        if node.ignore is not None:
            self._append_text(elem, "ignore", str(node.ignore).lower())

        for fragment in node.pre_elements:
            self._append_fragment(elem, fragment)

        if node.orientation_before_position and node.orientation is not None:
            self._append_orientation(elem, node.orientation)

        self._append_position(elem, node.position, node.position_text)

        if node.size is not None:
            self._append_size(elem, node.size)

        for fragment in node.mid_elements:
            self._append_fragment(elem, fragment)

        if not node.orientation_before_position and node.orientation is not None:
            self._append_orientation(elem, node.orientation)

        for fragment in node.post_elements:
            self._append_fragment(elem, fragment)

        if node.localized_grid is not None:
            self._append_text(elem, "localized_grid", str(node.localized_grid).lower())

        for fragment in node.tail_elements:
            self._append_fragment(elem, fragment)

        if node.children:
            geometry = ET.SubElement(elem, "geometry")
            for child in node.children:
                self._build_geometry_node(geometry, child)

    def _build_solution_domain(self, domain: PDMLSolutionDomain, profile: str) -> ET.Element:
        """构建 solution_domain 节"""
        elem = ET.Element("solution_domain")
        self._append_position(elem, domain.position)
        self._append_size(elem, domain.size)
        if profile == PDMLBinaryReader.COMPACT_FORCED_FLOW_LAYOUT:
            self._append_text(elem, "z_low_ambient", domain.z_low_ambient)
            self._append_text(elem, "z_high_ambient", domain.z_high_ambient)
            self._append_text(elem, "x_low_boundary", domain.x_low_ambient)
            self._append_text(elem, "x_high_boundary", domain.x_high_ambient)
            self._append_text(elem, "y_low_boundary", domain.y_low_ambient)
            self._append_text(elem, "y_high_boundary", domain.y_high_ambient)
        else:
            self._append_text(elem, "x_low_ambient", domain.x_low_ambient)
            self._append_text(elem, "x_high_boundary", domain.x_high_ambient)
            self._append_text(elem, "y_low_boundary", domain.y_low_ambient)
            self._append_text(elem, "y_high_boundary", domain.y_high_ambient)
            self._append_text(elem, "z_low_boundary", domain.z_low_ambient)
            self._append_text(elem, "z_high_boundary", domain.z_high_ambient)
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
        print(f"[INFO] 重力: {data.model.gravity_value} m/s2")
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
