#!/usr/bin/env python3
"""
FloXML 模板配置系统

支持从 JSON 文件加载 FloXML 项目配置模板，一比一映射到 FloXML 结构。
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Any


@dataclass
class GridAxisConfig:
    """单个轴的网格配置"""
    min_size: float = 0.001
    grid_type: str = "max_size"  # max_size or min_number
    max_size: Optional[float] = 0.01
    min_number: Optional[int] = None
    smoothing_value: int = 12


@dataclass
class SystemGridConfig:
    """系统网格配置"""
    smoothing: bool = True
    smoothing_type: str = "v3"
    dynamic_update: bool = True
    smoothing_value: int = 12
    x_grid: GridAxisConfig = field(default_factory=GridAxisConfig)
    y_grid: GridAxisConfig = field(default_factory=GridAxisConfig)
    z_grid: GridAxisConfig = field(default_factory=GridAxisConfig)


@dataclass
class ModelingConfig:
    """模型设置"""
    solution: str = "flow_heat"
    radiation: str = "off"
    dimensionality: str = "3d"
    transient: bool = False
    store_mass_flux: bool = False
    store_heat_flux: bool = False
    store_surface_temp: bool = False
    store_grad_t: bool = False
    store_bn_sc: bool = False
    store_power_density: bool = False
    store_mean_radiant_temperature: bool = False
    compute_capture_index: bool = False
    user_defined_subgroups: bool = False
    store_lma: bool = False


@dataclass
class TurbulenceConfig:
    """湍流配置"""
    type: str = "turbulent"
    turbulence_type: str = "auto_algebraic"


@dataclass
class GravityConfig:
    """重力配置"""
    type: str = "normal"
    normal_direction: str = "neg_y"
    value_type: str = "user"
    gravity_value: float = 9.81


@dataclass
class GlobalConfig:
    """全局设置"""
    datum_pressure: float = 101325
    radiant_temperature: float = 300.0
    ambient_temperature: float = 300.0
 concentration_1: float = 0.0
    concentration_2: float = 0.0
    concentration_3: float = 0.0
    concentration_4: float = 1.0
    concentration_5: float = 1.0


@dataclass
class ModelConfig:
    """完整模型配置"""
    modeling: ModelingConfig = field(default_factory=ModelingConfig)
    turbulence: TurbulenceConfig = field(default_factory=TurbulenceConfig)
    gravity: GravityConfig = field(default_factory=GravityConfig)
    global: GlobalConfig = field(default_factory=GlobalConfig)


@dataclass
class OverallControlConfig:
    """求解器总体控制"""
    outer_iterations: int = 500
    fan_relaxation: float = 1.0
    estimated_free_convection_velocity: float = 0.2
    solver_option: str = "multi_grid"
    active_plate_conduction: bool = False
    use_double_precision: bool = False
    network_assembly_block_correction: bool = False
    freeze_flow: bool = False
    store_error_field: bool = False


@dataclass
class SolveConfig:
    """求解配置"""
    overall_control: OverallControlConfig = field(default_factory=OverallControlConfig)


@dataclass
class SourceOptionConfig:
    """热源选项配置"""
    applies_to: str = "temperature"
    type: str = "total"
    value: float = 0.0
    power: float = 0.0
    linear_coefficient: float = 0.0


@dataclass
class SourceConfig:
    """热源配置"""
    name: str = "DefaultSource"
    options: List[SourceOptionConfig] = field(default_factory=list)


@dataclass
class FluidConfig:
    """流体配置"""
    name: str = "Air"
    conductivity_type: str = "constant"
    conductivity: float = 0.0261
    viscosity_type: str = "constant"
    viscosity: float = 0.0000184
    density_type: str = "constant"
    density: float = 1.16
    specific_heat: float = 1008.0
    expansivity: float = 0.003
    diffusivity: float = 0.0


@dataclass
class AmbientConfig:
    """环境配置"""
    name: str = "Ambient"
    pressure: float = 0.0
    temperature: float = 300.0
    radiant_temperature: float = 300.0
    heat_transfer_coeff: float = 0.0
    velocity: Dict[str, float] = field(default_factory=lambda: {"x": 0.0, "y": 0.0, "z": 0.0})
    turbulent_kinetic_energy: float = 0.0
    turbulent_dissipation_rate: float = 0.0
    concentration_1: float = 0.0
    concentration_2: float = 0.0
    concentration_3: float = 0.0
    concentration_4: float = 0.0
    concentration_5: float = 0.0


@dataclass
class MaterialConfig:
    """材料配置"""
    name: str = "Default"
    type: str = "isotropic"
    conductivity: float = 1.0
    density: float = 1.0
    specific_heat: float = 1.0


@dataclass
class AttributesConfig:
    """属性配置"""
    materials: List[MaterialConfig] = field(default_factory=list)
    fluids: List[FluidConfig] = field(default_factory=list)
    ambients: List[AmbientConfig] = field(default_factory=list)
    sources: List[SourceConfig] = field(default_factory=list)


@dataclass
class BoundaryConfig:
    """边界配置"""
    type: str = "ambient"
    ref: str = "Ambient"


@dataclass
class SolutionDomainConfig:
    """求解域配置"""
    padding_ratio: float = 0.1
    minimum_padding: float = 0.01
    x_low: BoundaryConfig = field(default_factory=BoundaryConfig)
    x_high: BoundaryConfig = field(default_factory=BoundaryConfig)
    y_low: BoundaryConfig = field(default_factory=BoundaryConfig)
    y_high: BoundaryConfig = field(default_factory=BoundaryConfig)
    z_low: BoundaryConfig = field(default_factory=BoundaryConfig)
    z_high: BoundaryConfig = field(default_factory=BoundaryConfig)
    fluid: str = "Air"


@dataclass
class DefaultReferencesConfig:
    """默认引用配置"""
    material: str = "Default"
    source_naming: str = "{name}_Source"


@dataclass
class FloXMLTemplate:
    """FloXML 项目模板"""
    model: ModelConfig = field(default_factory=ModelConfig)
    solve: SolveConfig = field(default_factory=SolveConfig)
    grid: SystemGridConfig = field(default_factory=SystemGridConfig)
    attributes: AttributesConfig = field(default_factory=AttributesConfig)
    solution_domain: SolutionDomainConfig = field(default_factory=SolutionDomainConfig)
    default_references: DefaultReferencesConfig = field(default_factory=DefaultReferencesConfig)

    @classmethod
    def from_dict(cls, data: Dict) -> 'FloXMLTemplate':
        """从字典创建模板"""
        template = cls()

        # model
        model_data = data.get('model', {})
        if model_data:
            template.model = ModelConfig.from_dict(model_data)

            # modeling
            modeling_data = model_data.get('modeling', {})
            if modeling_data:
                template.model.modeling = ModelingConfig.from_dict(modeling_data)

            # turbulence
            turb_data = model_data.get('turbulence', {})
            if turb_data:
                template.model.turbulence = TurbulenceConfig.from_dict(turb_data)

            # gravity
            grav_data = model_data.get('gravity', {})
            if grav_data:
                template.model.gravity = GravityConfig.from_dict(grav_data)

            # global
            glob_data = model_data.get('global', {})
            if glob_data:
                template.model.global = GlobalConfig.from_dict(glob_data)

        # solve
        solve_data = data.get('solve', {})
        if solve_data:
            template.solve = SolveConfig.from_dict(solve_data)

            # overall_control
            control_data = solve_data.get('overall_control', {})
            if control_data:
                template.solve.overall_control = OverallControlConfig.from_dict(control_data)

        # grid
        grid_data = data.get('grid', {})
        if grid_data:
            template.grid = SystemGridConfig.from_dict(grid_data)

        # attributes
        attrs_data = data.get('attributes', {})
        if attrs_data:
            template.attributes = AttributesConfig()

            # materials
            materials_data = attrs_data.get('materials', [])
            if materials_data:
                for mat_data in materials_data:
                    template.attributes.materials.append(
                        MaterialConfig.from_dict(mat_data)
                )

            # fluids
            fluids_data = attrs_data.get('fluids', [])
            if fluids_data:
                for fluid_data in fluids_data:
                    template.attributes.fluids.append(
                        FluidConfig.from_dict(fluid_data)
                )

            # ambients
            ambients_data = attrs_data.get('ambients', [])
            if ambients_data:
                for amb_data in ambients_data:
                    template.attributes.ambients.append(
                        AmbientConfig.from_dict(amb_data)
                )

            # sources
            sources_data = attrs_data.get('sources', [])
            if sources_data:
                for src_data in sources_data:
                    template.attributes.sources.append(
                        SourceConfig.from_dict(src_data)
                )

        # solution_domain
        domain_data = data.get('solution_domain', {})
        if domain_data:
            template.solution_domain = SolutionDomainConfig.from_dict(domain_data)

        # default_references
            refs_data = data.get('default_references', {})
            if refs_data:
                template.default_references = DefaultReferencesConfig.from_dict(refs_data)

        return template

    @classmethod
    def load_from_file(cls, filepath: str) -> 'FloXMLTemplate':
        """从 JSON 文件加载模板"""
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return cls.from_dict(data)


    @classmethod
    def get_default(cls) -> 'FloXMLTemplate':
        """获取默认模板"""
        return cls(
            model=ModelConfig(
                modeling=ModelingConfig(),
                turbulence=TurbulenceConfig(),
                gravity=GravityConfig(),
                global=GlobalConfig()
            ),
            solve=SolveConfig(
                overall_control=OverallControlConfig()
            ),
            grid=SystemGridConfig(
                x_grid=GridAxisConfig(),
                y_grid=GridAxisConfig(),
                z_grid=GridAxisConfig()
            ),
            attributes=AttributesConfig(
                materials=[
                    MaterialConfig(name="Default", conductivity=1.0, density=1.0, specific_heat=1.0)
                ],
                fluids=[
                    FluidConfig(
                        name="Air",
                        conductivity=0.0261,
                        viscosity=0.0000184,
                        density=1.16,
                        specific_heat=1008.0,
                        expansivity=0.003
                    )
                ],
                ambients=[
                    AmbientConfig(name="Ambient", temperature=300.0)
                ],
                sources=[
                    SourceConfig(name="DefaultSource")
                ]
            ),
            solution_domain=SolutionDomainConfig(
                x_low=BoundaryConfig(),
                x_high=BoundaryConfig(),
                y_low=BoundaryConfig(),
                y_high=BoundaryConfig(),
                z_low=BoundaryConfig(),
                z_high=BoundaryConfig(),
                fluid="Air"
            ),
            default_references=DefaultReferencesConfig()
        )


# ============================================================================
# FloXML 构建器
# ============================================================================

class FloXMLTemplateBuilder:
    """根据模板构建 FloXML 项目"""

    def __init__(self, template: FloXMLTemplate):
        self.template = template

    def _append_text(self, parent, tag: str, text: str) -> ET.Element:
        """添加带文本的子元素"""
        elem = ET.SubElement(parent, tag)
        elem.text = text
        return elem

    def _build_model(self, parent: ET.Element) -> None:
        """构建 model 节"""
        model = ET.SubElement(parent, "model")
        config = self.template.model

        # modeling
        modeling = ET.SubElement(model, "modeling")
        for tag in ['solution', 'radiation', 'dimensionality', 'transient',
             'store_mass_flux', 'store_heat_flux', 'store_surface_temp',
             'store_grad_t', 'store_bn_sc', 'store_power_density',
             'store_mean_radiant_temperature', 'compute_capture_index',
             'user_defined_subgroups', 'store_lma']:
            value = getattr(config.modeling, tag, "false")
            self._append_text(modeling, tag, value)

        # turbulence
        turbulence = ET.SubElement(model, "turbulence")
        self._append_text(turbulence, "type", config.model.turbulence.type)
        self._append_text(turbulence, "turbulence_type", config.model.turbulence.turbulence_type)

        # gravity
        gravity = ET.SubElement(model, "gravity")
        self._append_text(gravity, "type", config.model.gravity.type)
        self._append_text(gravity, "normal_direction", config.model.gravity.normal_direction)
        self._append_text(gravity, "value_type", config.model.gravity.value_type)
        self._append_text(gravity, "gravity_value", str(config.model.gravity.gravity_value))

        # global
        global_elem = ET.SubElement(model, "global")
        for tag in ['datum_pressure', 'radiant_temperature', 'ambient_temperature',
             'concentration_1', 'concentration_2', 'concentration_3', 'concentration_4', 'concentration_5']:
            value = str(getattr(config.model.global, tag, "0"))
            self._append_text(global_elem, tag, value)

    def _build_solve(self, parent: ET.Element) -> None:
        """构建 solve 节"""
        solve = ET.SubElement(parent, "solve")
        overall = ET.SubElement(solve, "overall_control")
        config = self.template.solve.overall_control

        for tag in ['outer_iterations', 'fan_relaxation', 'estimated_free_convection_velocity',
             'solver_option', 'active_plate_conduction', 'use_double_precision'
             'network_assembly_block_correction', 'freeze_flow', 'store_error_field']:
            value = str(getattr(config, tag))
            self._append_text(overall, tag, value)

    def _build_grid(self, parent: ET.Element) -> None:
        """构建 grid 节"""
        grid = ET.SubElement(parent, "grid")
        system_grid = ET.SubElement(grid, "system_grid")
        config = self.template.grid

        self._append_text(system_grid, "smoothing", "true" if config.smoothing else "false")
        self._append_text(system_grid, "smoothing_type", config.smoothing_type)
        self._append_text(system_grid, "dynamic_update", "true" if config.dynamic_update else "false")

        self._append_text(system_grid, "smoothing_value", str(config.smoothing_value))

        # 各轴网格
        for axis, ['x', 'y', 'z']:
            axis_config = getattr(config, axis)
            grid_axis = ET.SubElement(system_grid, f"{axis}_grid")
            self._append_text(grid_axis, "min_size", f"{axis_config.min_size:.6g}")

            grid_type = axis_config.grid_type
            self._append_text(grid_axis, "grid_type", grid_type)
            if grid_type == "max_size":
                self._append_text(grid_axis, "max_size", f"{axis_config.max_size:.6g}")
            elif grid_type == "min_number":
                self._append_text(grid_axis, "min_number", str(axis_config.min_number))

    def _build_attributes(self, parent: ET.Element) -> None:
        """构建 attributes 节"""
        attributes = ET.SubElement(parent, "attributes")
        config = self.template.attributes

        # materials
        materials = ET.SubElement(attributes, "materials")
        for mat_config in config.materials:
            mat_elem = ET.SubElement(materials, "isotropic_material_att")
            self._append_text(mat_elem, "name", mat_config.name)
            self._append_text(mat_elem, "conductivity", f"{mat_config.conductivity:.6g}")
            self._append_text(mat_elem, "density", f"{mat_config.density:.6g}")
            self._append_text(mat_elem, "specific_heat", f"{mat_config.specific_heat:.6g}")

        # fluids
        fluids = ET.SubElement(attributes, "fluids")
        for fluid_config in config.fluids:
            fluid_elem = ET.SubElement(fluids, "fluid_att")
            self._append_text(fluid_elem, "name", fluid_config.name)
            self._append_text(fluid_elem, "conductivity_type", fluid_config.conductivity_type)
            self._append_text(fluid_elem, "conductivity", f"{fluid_config.conductivity:.6g}")
            self._append_text(fluid_elem, "viscosity_type", fluid_config.viscosity_type)
            self._append_text(fluid_elem, "viscosity", f"{fluid_config.viscosity:.6g}")
            self._append_text(fluid_elem, "density_type", fluid_config.density_type)
            self._append_text(fluid_elem, "density", f"{fluid_config.density:.6g}")
            self._append_text(fluid_elem, "specific_heat", f"{fluid_config.specific_heat:.6g}")
            self._append_text(fluid_elem, "expansivity", f"{fluid_config.expansivity:.6g}")
            self._append_text(fluid_elem, "diffusivity", f"{fluid_config.diffusivity:.6g}")

        # ambients
        ambients = ET.SubElement(attributes, "ambients")
        for amb_config in config.ambients:
            ambient_elem = ET.SubElement(ambients, "ambient_att")
            self._append_text(ambient_elem, "name", amb_config.name)
            self._append_text(ambient_elem, "pressure", str(amb_config.pressure))
            self._append_text(ambient_elem, "temperature", str(amb_config.temperature))
            self._append_text(ambient_elem, "radiant_temperature", str(amb_config.radiant_temperature))
            self._append_text(ambient_elem, "heat_transfer_coeff", str(amb_config.heat_transfer_coeff))

            # velocity
            velocity = ET.SubElement(ambient_elem, "velocity")
            for axis in ['x', 'y', 'z']:
                vel_value = getattr(amb_config.velocity, axis, 0.0)
                self._append_text(velocity, axis, str(vel_value))

            for tag in ['turbulent_kinetic_energy', 'turbulent_dissipation_rate',
                  'concentration_1', 'concentration_2', 'concentration_3', 'concentration_4', 'concentration_5']:
                value = str(getattr(amb_config, tag, "0"))
                self._append_text(ambient_elem, tag, value)

        # sources
        sources = ET.SubElement(attributes, "sources")
        for src_config in config.sources:
            src_elem = ET.SubElement(sources, "source_att")
            self._append_text(src_elem, "name", src_config.name)

            # source_options
            options_elem = ET.SubElement(src_elem, "source_options")
            for opt_config in src_config.options:
                opt_elem = ET.SubElement(options_elem, "option")
                self._append_text(opt_elem, "applies_to", opt_config.applies_to)
                self._append_text(opt_elem, "type", opt_config.type)
                self._append_text(opt_elem, "value", str(opt_config.value))
                self._append_text(opt_elem, "power", str(opt_config.power))
                self._append_text(opt_elem, "linear_coefficient", str(opt_config.linear_coefficient))

    def _build_solution_domain(self, parent: ET.Element, domain_pos: Tuple[float, float, float],
                          domain_size: Tuple[float, float, float]) -> None:
        """构建 solution_domain 节"""
        domain = ET.SubElement(parent, "solution_domain")
 config = self.template.solution_domain

        # position
        pos = ET.SubElement(domain, "position")
        self._append_text(pos, "x", f"{domain_pos[0]:.6g}")
        self._append_text(pos, "y", f"{domain_pos[1]:.6g}")
        self._append_text(pos, "z", f"{domain_pos[2]:.6g}")

        # size
        size = ET.SubElement(domain, "size")
        self._append_text(size, "x", f"{domain_size[0]:.6g}")
        self._append_text(size, "y", f"{domain_size[1]:.6g}")
        self._append_text(size, "z", f"{domain_size[2]:.6g}")

        # boundaries
        for boundary_tag in ['x_low_ambient', 'x_high_ambient', 'y_low_ambient', 'y_high_ambient', 'z_low_ambient', 'z_high_ambient']:
            boundary_config = getattr(config, boundary_tag.replace('_ambient', ''), None)
            if boundary_config is None:
                # 使用新格式
                bc = config.x_low if boundary_tag == 'x_low_ambient' else \
                    config.x_high if boundary_tag == 'x_high_ambient' else \
                    config.y_low if boundary_tag == 'y_low_ambient' else \
                    config.y_high if boundary_tag == 'y_high_ambient' else \
                    config.z_low if boundary_tag == 'z_low_ambient' else \
                    config.z_high
                if bc:
                    self._append_text(domain, boundary_tag, bc.ref)

        # fluid
        self._append_text(domain, "fluid", config.fluid)

    def build_project(self, project_name: str, domain_pos: Tuple[float, float, float]
                      domain_size: Tuple[float, float, float]) -> ET.Element:
        """构建完整的 FloXML 项目"""
        root = ET.Element("xml_case")
        self._append_text(root, "name", project_name)

        # model
        self._build_model(root)

        # solve
        self._build_solve(root)

        # grid
        self._build_grid(root)

        # attributes
        self._build_attributes(root)

        # solution_domain
        self._build_solution_domain(root, domain_pos, domain_size)

        return root


# ============================================================================
# 模板加载器
# ============================================================================

def load_template(filepath: str) -> FloXMLTemplate:
    """从 JSON 文件加载模板"""
    path = Path(filepath)
    if not path.exists():
        raise FileNotFoundError(f"模板文件不存在: {filepath}")

    with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)

    return FloXMLTemplate.from_dict(data)


def get_default_template() -> FloXMLTemplate:
    """获取默认模板"""
    return FloXMLTemplate()

