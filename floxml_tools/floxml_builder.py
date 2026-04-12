"""FloXML 项目生成器 — 覆盖 FloTHERM/FloVENT V10.1 Schema 全部对象。

从 Siemens 官方 VBA Class_XML_Subs_FCv11.cls (7196 行) 转换而来。
使用 xml.etree.ElementTree 程序化构建 XML，用命名参数 + 字符串枚举替代 VBA 的位置参数 + 魔术数字。

用法:
    from floxml_tools.floxml_builder import FloXMLBuilder

    b = FloXMLBuilder("My Model")
    with b.model_section():
        b.modeling_setup(solution="flow_heat", radiation="on")
        b.turbulence_setup(model="auto_algebraic")
        b.gravity_setup(gravity_type="normal", direction="neg_z", value=9.81)
        b.global_setup(ambient_temperature=300)
    with b.solve_section():
        b.overall_control(max_iterations=1500)
    with b.grid_section():
        b.system_grid(x_min_size=0.001, x_control=("min_number", 24))
    with b.attributes_section():
        with b.materials_section():
            b.create_material("Aluminum", k=160, rho=2300, cp=455)
    with b.geometry_section():
        b.build_cuboid("Block", size=(1, 2, 3), material="Aluminum")
    b.build_solution_domain(size=(5, 5, 5), ambient="Outside World", fluid="Air")
    b.write("output.xml")

命令行:
    python -m floxml_tools.floxml_builder -o output.xml
"""

from __future__ import annotations

import xml.etree.ElementTree as ET
from contextlib import contextmanager
from typing import Optional, Sequence, Tuple, List, Union

# ── type aliases ──────────────────────────────────────────────────────
Vector3 = Tuple[float, float, float]
Orientation = Tuple[Vector3, Vector3, Vector3]
IDENTITY_ORIENTATION = ((1, 0, 0), (0, 1, 0), (0, 0, 1))


# ── helpers ───────────────────────────────────────────────────────────
def _t(parent: ET.Element, tag: str, text: str) -> ET.Element:
    """Append a text sub-element."""
    e = ET.SubElement(parent, tag)
    e.text = str(text)
    return e


def _f(parent: ET.Element, tag: str, value) -> None:
    """Conditionally append a text sub-element (skip if None/0/''/False)."""
    if value is None or value == 0 or value == "" or value is False:
        return
    if isinstance(value, float):
        _t(parent, tag, f"{value:.6g}")
    else:
        _t(parent, tag, str(value))


def _pos(parent: ET.Element, p: Vector3) -> ET.Element:
    """Append <position><x>...</x><y>...</y><z>...</z></position>."""
    pe = ET.SubElement(parent, "position")
    _t(pe, "x", f"{p[0]:.6g}")
    _t(pe, "y", f"{p[1]:.6g}")
    _t(pe, "z", f"{p[2]:.6g}")
    return pe


def _ori(parent: ET.Element, o: Orientation) -> ET.Element:
    """Append <orientation><local_x>...<local_y>...<local_z>...</orientation>."""
    oe = ET.SubElement(parent, "orientation")
    for label, v in [("local_x", o[0]), ("local_y", o[1]), ("local_z", o[2])]:
        le = ET.SubElement(oe, label)
        _t(le, "i", f"{v[0]:.6g}")
        _t(le, "j", f"{v[1]:.6g}")
        _t(le, "k", f"{v[2]:.6g}")
    return oe


def _common(obj: ET.Element, *, name: str, position: Vector3 = (0, 0, 0),
            orientation: Optional[Orientation] = None,
            active: bool = True, hidden: bool = False,
            notes: Optional[str] = None) -> None:
    """Write common geometry fields: name, position, orientation, active, hidden, notes."""
    _t(obj, "name", name)
    if not active:
        _t(obj, "active", "false")
    if hidden:
        _t(obj, "hidden", "true")
    _pos(obj, position)
    if orientation and orientation != IDENTITY_ORIENTATION:
        _ori(obj, orientation)


def _attr_refs(obj: ET.Element, *, material: Optional[str] = None,
               thermal: Optional[str] = None, surface: Optional[str] = None,
               radiation: Optional[str] = None, fan: Optional[str] = None,
               resistance: Optional[str] = None,
               x_grid: Optional[str] = None, y_grid: Optional[str] = None,
               z_grid: Optional[str] = None, all_grid: Optional[str] = None) -> None:
    """Write attribute reference fields (skip when None)."""
    if material:
        _t(obj, "material", material)
    if thermal:
        _t(obj, "thermal", thermal)
    if surface:
        _t(obj, "surface", surface)
    if radiation:
        _t(obj, "all_radiation", radiation)
    if fan:
        _t(obj, "fan", fan)
    if resistance:
        _t(obj, "resistance", resistance)
    if x_grid:
        _t(obj, "x_grid_constraint", x_grid)
    if y_grid:
        _t(obj, "y_grid_constraint", y_grid)
    if z_grid:
        _t(obj, "z_grid_constraint", z_grid)
    if all_grid:
        _t(obj, "all_grid_constraint", all_grid)


# ── section context manager helper ────────────────────────────────────
def _section(parent: ET.Element, tag: str):
    """Context manager that creates a sub-element and yields it."""
    @contextmanager
    def _ctx():
        elem = ET.SubElement(parent, tag)
        yield elem
    return _ctx()


# ======================================================================
# FloXMLBuilder
# ======================================================================
class FloXMLBuilder:
    """FloXML 项目生成器 — 覆盖 FloTHERM/FloVENT V10.1 Schema。

    用上下文管理器管理 section 嵌套，用命名参数替代 VBA 魔术数字。
    """

    def __init__(self, project_name: str):
        self.root = ET.Element("xml_case")
        _t(self.root, "name", project_name)
        self._current = self.root  # current insertion point

    # ── output ────────────────────────────────────────────────────────
    def write(self, path: str, encoding: str = "utf-8") -> None:
        """Write FloXML to file with XML declaration."""
        tree = ET.ElementTree(self.root)
        ET.indent(tree, space="  ")
        with open(path, "wb") as f:
            f.write(f'<?xml version="1.0" encoding="{encoding}" standalone="no" ?>\n'.encode(encoding))
            tree.write(f, encoding=encoding, xml_declaration=False)

    def to_string(self) -> str:
        """Return FloXML as string."""
        ET.indent(self.root, space="  ")
        return ET.tostring(self.root, encoding="unicode")

    # ── section context managers ──────────────────────────────────────
    @contextmanager
    def model_section(self):
        elem = ET.SubElement(self._current, "model")
        self._current = elem
        try:
            yield elem
        finally:
            self._current = self.root

    @contextmanager
    def solve_section(self):
        elem = ET.SubElement(self._current, "solve")
        self._current = elem
        try:
            yield elem
        finally:
            self._current = self.root

    @contextmanager
    def grid_section(self):
        elem = ET.SubElement(self._current, "grid")
        self._current = elem
        try:
            yield elem
        finally:
            self._current = self.root

    @contextmanager
    def attributes_section(self):
        elem = ET.SubElement(self._current, "attributes")
        self._current = elem
        try:
            yield elem
        finally:
            self._current = self.root

    @contextmanager
    def geometry_section(self):
        elem = ET.SubElement(self._current, "geometry")
        self._current = elem
        try:
            yield elem
        finally:
            self._current = self.root

    # ── attribute sub-sections ────────────────────────────────────────
    @contextmanager
    def _attr_section(self, tag: str):
        """Generic context manager for attribute sub-sections."""
        elem = ET.SubElement(self._current, tag)
        prev = self._current
        self._current = elem
        try:
            yield elem
        finally:
            self._current = prev

    def materials_section(self):
        return self._attr_section("materials")

    def surfaces_section(self):
        return self._attr_section("surfaces")

    def ambients_section(self):
        return self._attr_section("ambients")

    def thermals_section(self):
        return self._attr_section("thermals")

    def fluids_section(self):
        return self._attr_section("fluids")

    def sources_section(self):
        return self._attr_section("sources")

    def resistances_section(self):
        return self._attr_section("resistances")

    def radiations_section(self):
        return self._attr_section("radiations")

    def surface_exchanges_section(self):
        return self._attr_section("surface_exchanges")

    def gridconstraints_section(self):
        return self._attr_section("gridconstraints")

    def transients_section(self):
        return self._attr_section("transients")

    def fans_section(self):
        return self._attr_section("fans")

    def occupancies_section(self):
        return self._attr_section("occupancies")

    # ==================================================================
    # MODEL section methods
    # ==================================================================
    def modeling_setup(self, *, solution: str = "flow_heat",
                       radiation: str = "on",
                       dimensionality: str = "3d",
                       transient: bool = False,
                       joule_heating: bool = False) -> None:
        """Write <modeling> setup inside model section.

        Args:
            solution: "flow_heat" | "flow_only" | "conduction_only"
            radiation: "off" | "on" | "high_accuracy"
            dimensionality: "2d" | "3d"
            transient: enable transient analysis
            joule_heating: enable joule heating
        """
        parent = self._current
        m = ET.SubElement(parent, "modeling")
        _t(m, "solution", solution)
        _t(m, "radiation", radiation)
        _t(m, "dimensionality", dimensionality)
        if transient:
            _t(m, "transient", "true")
        else:
            _t(m, "transient", "false")
        if joule_heating:
            _t(m, "joule_heating", "true")
        else:
            _t(m, "joule_heating", "false")

    def store_options(self, *, mass_flux: bool = False, heat_flux: bool = False,
                      surface_temp: bool = False, grad_t: bool = False,
                      bnsc: bool = False, power_density: bool = False,
                      mean_radiant_temperature: bool = False,
                      capture_index: bool = False,
                      lma: bool = False,
                      lma_recirculation_ratio: float = 0) -> None:
        """Write store options inside <modeling>."""
        m = self._current.find("modeling")
        if m is None:
            m = ET.SubElement(self._current, "modeling")
        mapping = {
            "store_mass_flux": mass_flux, "store_heat_flux": heat_flux,
            "store_surface_temp": surface_temp, "store_grad_t": grad_t,
            "store_bn_sc": bnsc, "store_power_density": power_density,
            "store_mean_radiant_temperature": mean_radiant_temperature,
            "compute_capture_index": capture_index,
        }
        for tag, val in mapping.items():
            _t(m, tag, "true" if val else "false")
        if lma:
            _t(m, "store_lma", "true")
            _t(m, "recirculation_ratio", f"{lma_recirculation_ratio:.6g}")

    def solar_setup(self, *, solve: bool = True, angle_from: str = "x_axis",
                    angle: float = 45, latitude: float = 45,
                    day: int = 15, month: int = 6, solar_time: float = 12,
                    solar_type: str = "solar_intensity",
                    solar_intensity: float = 0,
                    cloudiness: float = 0.5) -> None:
        """Write <solar_radiation> inside <modeling>."""
        m = self._current.find("modeling")
        if m is None:
            m = ET.SubElement(self._current, "modeling")
        s = ET.SubElement(m, "solar_radiation")
        _t(s, "solve_solar", "true" if solve else "false")
        _t(s, "angle_measured_from", angle_from)
        _t(s, "angle", f"{angle:.6g}")
        _t(s, "latitude", f"{latitude:.6g}")
        _t(s, "day", str(day))
        _t(s, "month", str(month))
        _t(s, "solar_time", f"{solar_time:.6g}")
        if solar_type == "solar_intensity":
            _t(s, "solar_type", "solar_intensity")
            _t(s, "solar_intensity", f"{solar_intensity:.6g}")
        else:
            _t(s, "solar_type", "cloudiness")
            _t(s, "cloudiness", f"{cloudiness:.6g}")

    def turbulence_setup(self, *, turb_type: str = "turbulent",
                         model: str = "auto_algebraic",
                         revised_velocity: float = 0,
                         revised_length: float = 0,
                         lvel_stratification: bool = False,
                         capped_lvel_multiplier: float = 0) -> None:
        """Write <turbulence> inside model section.

        Args:
            turb_type: "laminar" | "turbulent"
            model: "revised_algebraic" | "auto_algebraic" | "lvel_k_epsilon" |
                   "lvel_algebraic" | "capped_lvel"
        """
        t = ET.SubElement(self._current, "turbulence")
        _t(t, "type", turb_type)
        if model == "revised_algebraic":
            _t(t, "turbulence_type", "revised_algebraic")
            re = ET.SubElement(t, "revised_algebraic")
            _t(re, "velocity", f"{revised_velocity:.6g}")
            _t(re, "length", f"{revised_length:.6g}")
        elif model == "auto_algebraic":
            _t(t, "turbulence_type", "auto_algebraic")
        elif model == "lvel_k_epsilon":
            _t(t, "turbulence_type", "lvel_k_epsilon")
            if lvel_stratification:
                _t(t, "lvel_k_epsilon_stratification", "true")
        elif model == "lvel_algebraic":
            _t(t, "turbulence_type", "lvel_algebraic")
        elif model == "capped_lvel":
            _t(t, "turbulence_type", "capped_lvel")
            _t(t, "capped_lvel_multiplier", f"{capped_lvel_multiplier:.6g}")

    def gravity_setup(self, *, gravity_type: str = "normal",
                      direction: str = "neg_z",
                      angled_direction: Optional[Vector3] = None,
                      value: float = 9.81) -> None:
        """Write <gravity> inside model section.

        Args:
            gravity_type: "off" | "normal" | "angled"
            direction: "neg_x"|"pos_x"|"neg_y"|"pos_y"|"neg_z"|"pos_z"
        """
        g = ET.SubElement(self._current, "gravity")
        _t(g, "type", gravity_type)
        if gravity_type == "normal":
            _t(g, "normal_direction", direction)
        elif gravity_type == "angled" and angled_direction:
            ae = ET.SubElement(g, "angled_direction")
            _t(ae, "x", f"{angled_direction[0]:.6g}")
            _t(ae, "y", f"{angled_direction[1]:.6g}")
            _t(ae, "z", f"{angled_direction[2]:.6g}")
        _t(g, "value_type", "user")
        _t(g, "gravity_value", f"{value:.6g}")

    def global_setup(self, *, datum_pressure: float = 101325,
                     ambient_temperature: float = 300,
                     radiant_temperature: float = 300,
                     radiant_transient: Optional[str] = None,
                     ambient_transient: Optional[str] = None,
                     concentrations: Optional[List[float]] = None) -> None:
        """Write <global> inside model section."""
        g = ET.SubElement(self._current, "global")
        _t(g, "datum_pressure", f"{datum_pressure:.6g}")
        _t(g, "radiant_temperature", f"{radiant_temperature:.6g}")
        _t(g, "ambient_temperature", f"{ambient_temperature:.6g}")
        if radiant_transient:
            _t(g, "radiant_transient", radiant_transient)
        if ambient_transient:
            _t(g, "ambient_transient", ambient_transient)
        if concentrations:
            for i, c in enumerate(concentrations, 1):
                _t(g, f"concentration_{i}", f"{c:.6g}")

    # ==================================================================
    # SOLVE section methods
    # ==================================================================
    def overall_control(self, *, max_iterations: int = 1500,
                        double_precision: bool = True,
                        convergence_criterion: float = 0.2,
                        monitor_point_check_freq: int = 30,
                        min_iterations: int = 10,
                        parallel: bool = False,
                        autosolve: bool = False,
                        autosolve_factor: float = 0.9,
                        use_bc_resid: bool = False,
                        print_frequency: int = 1,
                        solution_interpolation: bool = False,
                        autosolve_residual_criterion: bool = False,
                        autosolve_use_single_factor: bool = True,
                        autosolve_residual_factor: float = 0.2,
                        autosolve_monitor_point_factor: bool = True,
                        monitor_point_termination: Optional[str] = None) -> None:
        """Write <overall_control> inside solve section."""
        o = ET.SubElement(self._current, "overall_control")
        _t(o, "max_iterations", str(max_iterations))
        _t(o, "double_precision", "true" if double_precision else "false")
        _t(o, "convergence_criterion", f"{convergence_criterion:.6g}")
        _t(o, "monitor_point_check_frequency", str(monitor_point_check_freq))
        _t(o, "min_iterations", str(min_iterations))
        _t(o, "parallel", "true" if parallel else "false")
        _t(o, "autosolve", "true" if autosolve else "false")
        _t(o, "autosolve_factor", f"{autosolve_factor:.6g}")
        _t(o, "use_bc_residuals", "true" if use_bc_resid else "false")
        _t(o, "print_frequency", str(print_frequency))
        _t(o, "solution_interpolation", "true" if solution_interpolation else "false")
        _t(o, "autosolve_residual_criterion", "true" if autosolve_residual_criterion else "false")
        _t(o, "autosolve_use_single_factor", "true" if autosolve_use_single_factor else "false")
        _t(o, "autosolve_residual_factor", f"{autosolve_residual_factor:.6g}")
        _t(o, "autosolve_monitor_point_factor", "true" if autosolve_monitor_point_factor else "false")
        if monitor_point_termination:
            _t(o, "monitor_point_termination", monitor_point_termination)

    def variable_control(self, variable: str, *,
                         false_time_step_type: str = "automatic",
                         false_time_step_multiplier: float = 1.0,
                         false_time_step_value: float = 0,
                         termination_residual_type: str = "automatic",
                         termination_residual_multiplier: float = 1.0,
                         termination_residual_value: float = 0,
                         inner_iterations: int = 1) -> None:
        """Write a <variable_control> entry.

        Args:
            variable: "pressure"|"x_velocity"|"y_velocity"|"z_velocity"|
                      "temperature"|"ke_turb"|"diss_turb"|
                      "concentration_1"..."concentration_5"|"potential"
        """
        vc = ET.SubElement(self._current, "variable_control")
        _t(vc, "variable", variable)
        _t(vc, "false_time_step_type", false_time_step_type)
        if false_time_step_type == "automatic":
            _t(vc, "false_time_step_auto_multiplier", f"{false_time_step_multiplier:.6g}")
        else:
            _t(vc, "false_time_step_user_value", f"{false_time_step_value:.6g}")
        if termination_residual_type == "automatic":
            _t(vc, "terminal_residual", "automatic")
            _t(vc, "terminal_residual_auto_multiplier", f"{termination_residual_multiplier:.6g}")
        else:
            _t(vc, "terminal_residual", "user")
            _t(vc, "terminal_residual_user_value", f"{termination_residual_value:.6g}")
        _t(vc, "inner_iterations", str(inner_iterations))

    def solver_control(self, variable: str, *,
                       linear_relaxation: float = 0.3,
                       error_compute_frequency: int = 0) -> None:
        """Write a <solver_control> entry.

        Args:
            variable: same names as variable_control
        """
        sc = ET.SubElement(self._current, "solver_control")
        _t(sc, "variable", variable)
        _t(sc, "linear_relaxation", f"{linear_relaxation:.6g}")
        _t(sc, "error_compute_frequency", str(error_compute_frequency))

    # ==================================================================
    # GRID section methods
    # ==================================================================
    def system_grid(self, *,
                    x_min_size: float = 0.001, x_control: tuple = ("min_number", 24),
                    y_min_size: float = 0.001, y_control: tuple = ("min_number", 24),
                    z_min_size: float = 0.001, z_control: tuple = ("min_number", 24),
                    smoothing: bool = False,
                    x_smoothing: float = 0, y_smoothing: float = 0, z_smoothing: float = 0,
                    smoothing_type: str = "v3",
                    dynamic_update: bool = True) -> None:
        """Write <system_grid>.

        Args:
            x_control: ("min_number", N) or ("max_size", S)
        """
        sg = ET.SubElement(self._current, "system_grid")
        _t(sg, "smoothing", "true" if smoothing else "false")
        if smoothing:
            _t(sg, "smoothing_type", smoothing_type)
        _t(sg, "dynamic_update", "true" if dynamic_update else "false")

        for axis, min_size, ctrl, sm_val in [
            ("x", x_min_size, x_control, x_smoothing),
            ("y", y_min_size, y_control, y_smoothing),
            ("z", z_min_size, z_control, z_smoothing),
        ]:
            g = ET.SubElement(sg, f"{axis}_grid")
            _t(g, "min_size", f"{min_size:.6g}")
            _t(g, "grid_type", ctrl[0])
            _t(g, ctrl[0], f"{ctrl[1]:.6g}" if isinstance(ctrl[1], float) else str(ctrl[1]))
            if smoothing:
                _t(g, "smoothing_value", f"{sm_val:.6g}")

    def grid_patch(self, name: str, direction: str, *,
                   start: float, end: float,
                   control: tuple = ("min_number", 12),
                   distribution: str = "uniform",
                   distribution_index: float = 1.0) -> None:
        """Write a <grid_patch>.

        Args:
            direction: "x" | "y" | "z"
            control: ("min_number", N) or ("max_size", S)
            distribution: "uniform"|"increasing"|"decreasing"|"symmetrical"
        """
        patches = self._current.find("patches")
        if patches is None:
            patches = ET.SubElement(self._current, "patches")
        p = ET.SubElement(patches, "grid_patch")
        _t(p, "name", name)
        _t(p, "applies_to", f"{direction}_direction")
        _t(p, "start_location", f"{start:.6g}")
        _t(p, "end_location", f"{end:.6g}")
        _t(p, "number_of_cells_control", control[0])
        _t(p, control[0], f"{control[1]:.6g}" if isinstance(control[1], float) else str(control[1]))
        _t(p, "cell_distribution", distribution)
        _t(p, "cell_distribution_index", f"{distribution_index:.6g}")

    # ==================================================================
    # ATTRIBUTE methods
    # ==================================================================
    def create_material(self, name: str, *,
                        k: float = 0, kx: float = 0, ky: float = 0, kz: float = 0,
                        rho: float = 0, cp: float = 0,
                        coeff: float = 0, tref: float = 0,
                        surface: Optional[str] = None,
                        notes: Optional[str] = None) -> None:
        """Create a material attribute. Auto-detects isotropic vs orthotropic."""
        if kx == 0 and ky == 0 and kz == 0:
            kx = ky = kz = k

        if kx == ky == kz:
            m = ET.SubElement(self._current, "isotropic_material_att")
            _t(m, "name", name)
            _t(m, "conductivity", f"{kx:.6g}")
            _t(m, "density", f"{rho:.6g}")
            _t(m, "specific_heat", f"{cp:.6g}")
        else:
            m = ET.SubElement(self._current, "orthotropic_material_att")
            _t(m, "name", name)
            _t(m, "x_conductivity", f"{kx:.6g}")
            _t(m, "y_conductivity", f"{ky:.6g}")
            _t(m, "z_conductivity", f"{kz:.6g}")
            _t(m, "density", f"{rho:.6g}")
            _t(m, "specific_heat", f"{cp:.6g}")

        if surface:
            _t(m, "surface", surface)
        if notes:
            _t(m, "notes", notes)

    def create_surface(self, name: str, *,
                       emissivity: float = 1.0, roughness: float = 0,
                       rsurf_fluid: float = 0, rsurf_solid: float = 0,
                       area_factor: float = 1, solar_reflectivity: float = 0,
                       red: float = 0.3, green: float = 0.5, blue: float = 1,
                       shininess: float = 0, brightness: float = 0,
                       electrical_resistance: float = 0,
                       notes: Optional[str] = None) -> None:
        """Create a surface attribute."""
        s = ET.SubElement(self._current, "surface_att")
        _t(s, "name", name)
        _t(s, "emissivity", f"{emissivity:.6g}")
        _t(s, "roughness", f"{roughness:.6g}")
        _t(s, "rsurf_fluid", f"{rsurf_fluid:.6g}")
        _t(s, "rsurf_solid", f"{rsurf_solid:.6g}")
        _t(s, "area_factor", f"{area_factor:.6g}")
        _t(s, "solar_reflectivity", f"{solar_reflectivity:.6g}")
        _t(s, "electrical_resistance", f"{electrical_resistance:.6g}")
        ds = ET.SubElement(s, "display_settings")
        c = ET.SubElement(ds, "color")
        _t(c, "red", f"{red:.6g}")
        _t(c, "green", f"{green:.6g}")
        _t(c, "blue", f"{blue:.6g}")
        _t(ds, "shininess", f"{shininess:.6g}")
        _t(ds, "brightness", f"{brightness:.6g}")
        if notes:
            _t(s, "notes", notes)

    def create_ambient(self, name: str, *,
                       pressure: float = 0, temperature: float = 293,
                       radiant_temperature: float = 293,
                       htc: float = 12,
                       velocity: Vector3 = (0, 0, 0),
                       temperature_transient: Optional[str] = None,
                       radiant_transient: Optional[str] = None,
                       concentrations: Optional[List[float]] = None,
                       turbulent_kinetic_energy: float = 0,
                       turbulent_dissipation_rate: float = 0,
                       notes: Optional[str] = None) -> None:
        """Create an ambient attribute."""
        a = ET.SubElement(self._current, "ambient_att")
        _t(a, "name", name)
        _t(a, "pressure", f"{pressure:.6g}")
        _t(a, "temperature", f"{temperature:.6g}")
        _t(a, "radiant_temperature", f"{radiant_temperature:.6g}")
        _t(a, "heat_transfer_coeff", f"{htc:.6g}")
        ve = ET.SubElement(a, "velocity")
        _t(ve, "x", f"{velocity[0]:.6g}")
        _t(ve, "y", f"{velocity[1]:.6g}")
        _t(ve, "z", f"{velocity[2]:.6g}")
        _t(a, "turbulent_kinetic_energy", f"{turbulent_kinetic_energy:.6g}")
        _t(a, "turbulent_dissipation_rate", f"{turbulent_dissipation_rate:.6g}")
        if concentrations:
            for i, c in enumerate(concentrations, 1):
                _t(a, f"concentration_{i}", f"{c:.6g}")
        if temperature_transient:
            _t(a, "ambient_transient", temperature_transient)
        if radiant_transient:
            _t(a, "radiant_transient", radiant_transient)
        if notes:
            _t(a, "notes", notes)

    def create_thermal(self, name: str, *,
                       model_type: str = "total_power",
                       power: float = 0, power_area: float = 0,
                       fixed_temperature: float = 0,
                       joule_using: str = "current",
                       current: float = 0, voltage: float = 0,
                       joule_direction: str = "longest",
                       transient: Optional[str] = None,
                       notes: Optional[str] = None) -> None:
        """Create a thermal attribute.

        Args:
            model_type: "conduction"|"total_power"|"power_area"|
                        "fixed_temperature"|"joule_heating"
            joule_using: "current" | "voltage"
            joule_direction: "longest"|"x"|"y"|"z"
        """
        t = ET.SubElement(self._current, "thermal_att")
        _t(t, "name", name)

        if model_type == "conduction":
            _t(t, "thermal_model", "conduction")
            _t(t, "power", f"{power:.6g}")
        elif model_type == "total_power":
            _t(t, "thermal_model", "fixed_heat_flow")
            _t(t, "fixed_heat_flow", "total_power")
            _t(t, "power", f"{power:.6g}")
        elif model_type == "power_area":
            _t(t, "thermal_model", "fixed_heat_flow")
            _t(t, "fixed_heat_flow", "power_area")
            _t(t, "power_area", f"{power_area:.6g}")
        elif model_type == "fixed_temperature":
            _t(t, "thermal_model", "fixed_temperature")
            _t(t, "fixed_temperature", f"{fixed_temperature:.6g}")
        elif model_type == "joule_heating":
            _t(t, "thermal_model", "joule_heating")
            jh = ET.SubElement(t, "joule_heating")
            _t(jh, "using", joule_using)
            _t(jh, joule_using, f"{current if joule_using == 'current' else voltage:.6g}")
            _t(jh, "joule_heating_flow_direction", joule_direction)

        if transient:
            _t(t, "transient", transient)
        if notes:
            _t(t, "notes", notes)

    def create_fluid(self, name: str, *,
                     conductivity: float = 0.0261,
                     conductivity_type: str = "constant",
                     conductivity_coeff: float = 0, conductivity_tref: float = 0,
                     viscosity: float = 0.000018,
                     viscosity_type: str = "constant",
                     viscosity_coeff: float = 0, viscosity_tref: float = 0,
                     density: float = 1.16, density_type: str = "constant",
                     specific_heat: float = 1008,
                     expansivity: float = 0.003,
                     diffusivity: float = 0,
                     notes: Optional[str] = None) -> None:
        """Create a fluid attribute."""
        f = ET.SubElement(self._current, "fluid_att")
        _t(f, "name", name)
        _t(f, "conductivity_type", conductivity_type)
        _t(f, "conductivity", f"{conductivity:.6g}")
        if conductivity_type == "temperature_dependant":
            _t(f, "coeff", f"{conductivity_coeff:.6g}")
            _t(f, "t_ref", f"{conductivity_tref:.6g}")
        _t(f, "viscosity_type", viscosity_type)
        _t(f, "viscosity", f"{viscosity:.6g}")
        if viscosity_type == "temperature_dependant":
            _t(f, "coeff", f"{viscosity_coeff:.6g}")
            _t(f, "t_ref", f"{viscosity_tref:.6g}")
        _t(f, "density_type", density_type)
        _t(f, "density", f"{density:.6g}")
        _t(f, "specific_heat", f"{specific_heat:.6g}")
        _t(f, "expansivity", f"{expansivity:.6g}")
        _t(f, "diffusivity", f"{diffusivity:.6g}")
        if notes:
            _t(f, "notes", notes)

    def create_source(self, name: str, *,
                      applies_to: str = "temperature",
                      source_type: str = "fixed",
                      power: float = 0,
                      value: float = 0,
                      linear_coefficient: float = 0,
                      nonlinear_curve: Optional[str] = None,
                      transient: Optional[str] = None,
                      apply_transient_to_coeff: bool = False,
                      notes: Optional[str] = None) -> None:
        """Create a source attribute.

        Args:
            applies_to: "temperature"|"concentration_1"..."concentration_5"|
                        "pressure"|"x_velocity"|"y_velocity"|"z_velocity"|
                        "ke_turb"|"diss_turb"|"potential"
            source_type: "total"|"volume"|"area"|"fixed"|"linear"|"nonlinear"
        """
        s = ET.SubElement(self._current, "source_att")
        _t(s, "name", name)
        _t(s, "applies_to", applies_to)
        _t(s, "type", source_type)
        if source_type in ("total", "volume", "area", "fixed"):
            _t(s, "value", f"{power:.6g}")
        elif source_type == "linear":
            _t(s, "value", f"{value:.6g}")
            _t(s, "linear_coefficient", f"{linear_coefficient:.6g}")
        elif source_type == "nonlinear" and nonlinear_curve:
            _t(s, "value", f"{value:.6g}")
            pts = nonlinear_curve.split(",")
            if len(pts) >= 4:
                pts_elem = ET.SubElement(s, "non_linear_profile_points")
                for i in range(0, len(pts) - 1, 2):
                    pp = ET.SubElement(pts_elem, "profile_point")
                    _t(pp, "x", pts[i].strip())
                    _t(pp, "y", pts[i + 1].strip())
        if transient:
            _t(s, "transient", transient)
        if apply_transient_to_coeff:
            _t(s, "apply_transient_to_coeff", "false")
        if notes:
            _t(s, "notes", notes)

    def create_resistance(self, name: str, *,
                          resistance_type: str = "planar",
                          advanced: bool = False,
                          x_a: float = 0, x_b: float = 0, x_far: float = 0,
                          x_length_scale: float = 0, x_index: float = 0,
                          y_a: float = 0, y_b: float = 0, y_far: float = 0,
                          y_length_scale: float = 0, y_index: float = 0,
                          z_a: float = 0, z_b: float = 0, z_far: float = 0,
                          z_length_scale: float = 0, z_index: float = 0,
                          loss_based_on: str = "approach_velocity",
                          notes: Optional[str] = None) -> None:
        """Create a resistance attribute.

        Args:
            resistance_type: "planar" | "volume"
            loss_based_on: "approach_velocity"|"device_velocity"|"accelerated"
        """
        r = ET.SubElement(self._current, "resistance_att")
        _t(r, "name", name)

        def _write_axis(axis: str, a: float, b: float, far: float, ls: float, idx: float):
            re = ET.SubElement(r, f"resistance_{axis}")
            if advanced:
                _t(re, "a_coefficient", f"{a:.6g}")
                _t(re, "b_coefficient", f"{b:.6g}")
                _t(re, "free_area_ratio", f"{far:.6g}")
                _t(re, "length_scale", f"{ls:.6g}")
                _t(re, "index", f"{idx:.6g}")
            else:
                _t(re, "loss_coefficient", f"{a:.6g}")

        if resistance_type == "planar":
            _write_axis("z", z_a, z_b, z_far, z_length_scale, z_index)
        else:
            _write_axis("x", x_a, x_b, x_far, x_length_scale, x_index)
            _write_axis("y", y_a, y_b, y_far, y_length_scale, y_index)
            _write_axis("z", z_a, z_b, z_far, z_length_scale, z_index)

        _t(r, "loss_coefficients_based_on", loss_based_on)
        if notes:
            _t(r, "notes", notes)

    def create_radiation(self, name: str, *,
                         rad_type: str = "subdivided",
                         min_area: float = 0,
                         subdivided_tolerance: float = 0.01) -> None:
        """Create a radiation attribute.

        Args:
            rad_type: "nonradiating"|"single"|"subdivided"
        """
        r = ET.SubElement(self._current, "radiation_att")
        _t(r, "name", name)
        _t(r, "type", rad_type)
        if rad_type == "subdivided":
            _t(r, "subdivided_surface_tolerance", f"{subdivided_tolerance:.6g}")

    def create_surface_exchange(self, name: str, *,
                                method: str = "volume",
                                extent: float = 0,
                                coefficient_type: str = "calculated",
                                profile_points: Optional[str] = None,
                                constant_value: float = 0,
                                wetted_area: float = 0,
                                ref_temp_type: str = "calculated",
                                ref_temp_value: float = 0,
                                notes: Optional[str] = None) -> None:
        """Create a surface exchange attribute."""
        se = ET.SubElement(self._current, "surface_exchange_att")
        _t(se, "name", name)
        _t(se, "heat_transfer_method", method)
        _t(se, "extent_of_heat_transfer", f"{extent:.6g}")
        _t(se, "heat_transfer_coefficient", coefficient_type)
        if coefficient_type == "specified" and profile_points:
            pts = profile_points.split(",")
            pts_elem = ET.SubElement(se, "profile_points")
            for i in range(0, len(pts) - 1, 2):
                pp = ET.SubElement(pts_elem, "profile_point")
                _t(pp, "x", pts[i].strip())
                _t(pp, "y", pts[i + 1].strip())
        elif coefficient_type == "constant":
            _t(se, "specified_constant_value", f"{constant_value:.6g}")
        _t(se, "wetted_area_volume_transfer", f"{wetted_area:.6g}")
        _t(se, "reference_temperature_type", ref_temp_type)
        if ref_temp_type == "specified":
            _t(se, "reference_temperature_value", f"{ref_temp_value:.6g}")
        if notes:
            _t(se, "notes", notes)

    def create_gridconstraint(self, name: str, *,
                              min_size_active: bool = True,
                              min_cell_size: float = 0.001,
                              number_cells_control: str = "max_size",
                              max_size_or_min_number: float = 43,
                              high_inflation: str = "size",
                              high_size_or_percent: float = 0,
                              high_cells_control: str = "max_size",
                              high_max_size: float = 0,
                              low_inflation: str = "size",
                              low_size_or_percent: float = 0,
                              low_cells_control: str = "max_size",
                              low_max_size: float = 0) -> None:
        """Create a grid constraint attribute."""
        g = ET.SubElement(self._current, "gridconstraint_att")
        _t(g, "name", name)
        _t(g, "min_size_active", "true" if min_size_active else "false")
        if min_size_active:
            _t(g, "min_cell_size", f"{min_cell_size:.6g}")
        _t(g, "number_cells_control", number_cells_control)
        _t(g, number_cells_control, f"{max_size_or_min_number:.6g}")
        _t(g, "high_inflation", high_inflation)
        _t(g, "high_cells_control", high_cells_control)
        _t(g, high_cells_control, f"{high_max_size:.6g}")
        _t(g, "low_inflation", low_inflation)
        _t(g, "low_cells_control", low_cells_control)
        _t(g, low_cells_control, f"{low_max_size:.6g}")

    def create_occupancy(self, name: str, *,
                         occupancy_level: float = 0,
                         activity_level: str = "low",
                         specified_activity_value: float = 0,
                         notes: Optional[str] = None) -> None:
        """Create an occupancy attribute (FloVENT)."""
        o = ET.SubElement(self._current, "occupancy_att")
        _t(o, "name", name)
        _t(o, "occupancy_level", f"{occupancy_level:.6g}")
        _t(o, "activity_level", activity_level)
        if activity_level == "specified":
            _t(o, "specified_activity_value", f"{specified_activity_value:.6g}")
        if notes:
            _t(o, "notes", notes)

    def create_transient(self, name: str, *,
                         time_curve: Optional[str] = None,
                         mp_curve_increasing: Optional[str] = None,
                         mp_curve_decreasing: Optional[str] = None,
                         monitor_point: Optional[str] = None,
                         periodic: bool = False,
                         notes: Optional[str] = None) -> None:
        """Create a transient attribute.

        Args:
            time_curve: "0,1,2,1" pairs of (time, multiplier)
            mp_curve_increasing: "25,1,90,1" pairs
            mp_curve_decreasing: "25,1,70,1" pairs
        """
        t = ET.SubElement(self._current, "transient_att")
        _t(t, "name", name)
        if time_curve:
            _t(t, "multiplier_vs_time_active", "true")
            pts = time_curve.split(",")
            pts_elem = ET.SubElement(t, "time_multiplier_pairs")
            for i in range(0, len(pts) - 1, 2):
                pp = ET.SubElement(pts_elem, "pair")
                _t(pp, "time", pts[i].strip())
                _t(pp, "multiplier", pts[i + 1].strip())
        if mp_curve_increasing:
            _t(t, "multiplier_vs_MP_active", "true")
            pts = mp_curve_increasing.split(",")
            pts_elem = ET.SubElement(t, "MP_multiplier_pairs_increasing")
            for i in range(0, len(pts) - 1, 2):
                pp = ET.SubElement(pts_elem, "pair")
                _t(pp, "temperature", pts[i].strip())
                _t(pp, "multiplier", pts[i + 1].strip())
        if mp_curve_decreasing:
            _t(t, "multiplier_vs_MP_hysteresis_active", "true")
            pts = mp_curve_decreasing.split(",")
            pts_elem = ET.SubElement(t, "MP_multiplier_pairs_decreasing")
            for i in range(0, len(pts) - 1, 2):
                pp = ET.SubElement(pts_elem, "pair")
                _t(pp, "temperature", pts[i].strip())
                _t(pp, "multiplier", pts[i + 1].strip())
        if monitor_point:
            _t(t, "associated_monitor_point", monitor_point)
        if periodic:
            _t(t, "periodic", "true")
        if notes:
            _t(t, "notes", notes)

    def create_fan(self, name: str, *,
                  flow_type: str = "normal",
                  flow_direction: Optional[Vector3] = None,
                  swirl_model: Optional[str] = None,
                  swirl_direction: Optional[str] = None,
                  swirl_speed: float = 0,
                  curve_type: str = "non_linear",
                  open_flow_rate: float = 0,
                  stagnation_pressure: float = 0,
                  fan_curve: Optional[List[Tuple[float, float]]] = None) -> None:
        """Create a fan attribute.

        Args:
            flow_type: "normal"|"angled"|"swirl"|"circular"
            curve_type: "fixed"|"linear"|"non_linear"
            fan_curve: [(flow, pressure), ...] pairs
        """
        f = ET.SubElement(self._current, "fan_att")
        _t(f, "name", name)
        _t(f, "flow_type", flow_type)
        if flow_type == "angled" and flow_direction:
            fd = ET.SubElement(f, "flow_direction")
            _t(fd, "x", f"{flow_direction[0]:.6g}")
            _t(fd, "y", f"{flow_direction[1]:.6g}")
            _t(fd, "z", f"{flow_direction[2]:.6g}")
        elif flow_type == "swirl":
            if swirl_model:
                _t(f, "swirl_model", swirl_model)
            if swirl_direction:
                _t(f, "swirl_direction", swirl_direction)
            _t(f, "swirl_speed", f"{swirl_speed:.6g}")

        if curve_type == "fixed":
            _t(f, "flow_spec", "fixed")
            _t(f, "flow_rate", f"{open_flow_rate:.6g}")
        elif curve_type == "linear":
            _t(f, "flow_spec", "linear")
            _t(f, "open_volume_flow_rate", f"{open_flow_rate:.6g}")
            _t(f, "stagnation_pressure", f"{stagnation_pressure:.6g}")
        elif curve_type == "non_linear":
            _t(f, "flow_spec", "non_linear")
            _t(f, "open_volume_flow_rate", f"{open_flow_rate:.6g}")
            _t(f, "stagnation_pressure", f"{stagnation_pressure:.6g}")
            if fan_curve:
                fcp = ET.SubElement(f, "fan_curve_points")
                for flow, pressure in fan_curve:
                    p = ET.SubElement(fcp, "fan_curve_point")
                    _t(p, "volume_flow", f"{flow:.6g}")
                    _t(p, "pressure", f"{pressure:.6g}")

    # ==================================================================
    # GEOMETRY builders
    # ==================================================================
    def build_cuboid(self, name: str, *,
                     size: Vector3 = (0, 0, 0),
                     position: Vector3 = (0, 0, 0),
                     orientation: Optional[Orientation] = None,
                     active: bool = True, hidden: bool = False,
                     material: Optional[str] = None,
                     thermal: Optional[str] = None,
                     surface: Optional[str] = None,
                     radiation: Optional[str] = None,
                     x_grid: Optional[str] = None,
                     y_grid: Optional[str] = None,
                     z_grid: Optional[str] = None,
                     all_grid: Optional[str] = None,
                     monitor_point: bool = False,
                     localized_grid: bool = False,
                     notes: Optional[str] = None) -> ET.Element:
        """Build a <cuboid> geometry element."""
        c = ET.SubElement(self._current, "cuboid")
        _common(c, name=name, position=position, orientation=orientation,
                active=active, hidden=hidden, notes=notes)
        se = ET.SubElement(c, "size")
        _t(se, "x", f"{size[0]:.6g}")
        _t(se, "y", f"{size[1]:.6g}")
        _t(se, "z", f"{size[2]:.6g}")
        if orientation and orientation != IDENTITY_ORIENTATION:
            _ori(c, orientation)
        if monitor_point:
            _t(c, "monitor_point", "true")
        _attr_refs(c, material=material, thermal=thermal, surface=surface,
                   radiation=radiation, x_grid=x_grid, y_grid=y_grid,
                   z_grid=z_grid, all_grid=all_grid)
        if localized_grid:
            _t(c, "localized_grid", "true")
        return c

    def build_cylinder(self, name: str, *,
                       radius: float, height: float, facets: int = 12,
                       position: Vector3 = (0, 0, 0),
                       orientation: Optional[Orientation] = None,
                       active: bool = True, hidden: bool = False,
                       material: Optional[str] = None,
                       thermal: Optional[str] = None,
                       surface: Optional[str] = None,
                       radiation: Optional[str] = None,
                       x_grid: Optional[str] = None,
                       y_grid: Optional[str] = None,
                       z_grid: Optional[str] = None,
                       all_grid: Optional[str] = None,
                       localized_grid: bool = False,
                       notes: Optional[str] = None) -> ET.Element:
        """Build a <cylinder> geometry element."""
        cy = ET.SubElement(self._current, "cylinder")
        _common(cy, name=name, position=position, orientation=orientation,
                active=active, hidden=hidden, notes=notes)
        _t(cy, "radius", f"{radius:.6g}")
        _t(cy, "height", f"{height:.6g}")
        _t(cy, "modeling_level", f"{facets} facets")
        if orientation and orientation != IDENTITY_ORIENTATION:
            _ori(cy, orientation)
        _attr_refs(cy, material=material, thermal=thermal, surface=surface,
                   radiation=radiation, x_grid=x_grid, y_grid=y_grid,
                   z_grid=z_grid, all_grid=all_grid)
        if localized_grid:
            _t(cy, "localized_grid", "true")
        return cy

    @contextmanager
    def build_assembly(self, name: str, *,
                       position: Vector3 = (0, 0, 0),
                       orientation: Optional[Orientation] = None,
                       active: bool = True, hidden: bool = False,
                       material: Optional[str] = None,
                       x_grid: Optional[str] = None,
                       y_grid: Optional[str] = None,
                       z_grid: Optional[str] = None,
                       all_grid: Optional[str] = None,
                       localized_grid: bool = False,
                       notes: Optional[str] = None):
        """Build an <assembly> (context manager for nesting children)."""
        a = ET.SubElement(self._current, "assembly")
        _common(a, name=name, position=position, orientation=orientation,
                active=active, hidden=hidden, notes=notes)
        if orientation and orientation != IDENTITY_ORIENTATION:
            _ori(a, orientation)
        _attr_refs(a, material=material, x_grid=x_grid, y_grid=y_grid,
                   z_grid=z_grid, all_grid=all_grid)
        if localized_grid:
            _t(a, "localized_grid", "true")
        prev = self._current
        self._current = a
        try:
            yield a
        finally:
            self._current = prev

    def build_monitor_point(self, name: str, *,
                            position: Vector3 = (0, 0, 0),
                            active: bool = True, hidden: bool = False,
                            notes: Optional[str] = None) -> ET.Element:
        """Build a <monitor_point> geometry element."""
        mp = ET.SubElement(self._current, "monitor_point")
        _common(mp, name=name, position=position, active=active,
                hidden=hidden, notes=notes)
        return mp

    def build_region(self, name: str, *,
                     size: Vector3 = (0, 0, 0),
                     position: Vector3 = (0, 0, 0),
                     orientation: Optional[Orientation] = None,
                     collapse_direction: str = "none",
                     collapse_face: str = "lowface",
                     fluid: Optional[str] = None,
                     x_grid: Optional[str] = None,
                     y_grid: Optional[str] = None,
                     z_grid: Optional[str] = None,
                     all_grid: Optional[str] = None,
                     localized_grid: bool = False,
                     active: bool = True, hidden: bool = False,
                     notes: Optional[str] = None) -> ET.Element:
        """Build a <region> geometry element."""
        r = ET.SubElement(self._current, "region")
        _common(r, name=name, position=position, orientation=orientation,
                active=active, hidden=hidden, notes=notes)
        se = ET.SubElement(r, "size")
        _t(se, "x", f"{size[0]:.6g}")
        _t(se, "y", f"{size[1]:.6g}")
        _t(se, "z", f"{size[2]:.6g}")
        if orientation and orientation != IDENTITY_ORIENTATION:
            _ori(r, orientation)
        _t(r, "collapse_direction", collapse_direction)
        _t(r, "collapse_face", collapse_face)
        if fluid:
            _t(r, "fluid", fluid)
        _attr_refs(r, x_grid=x_grid, y_grid=y_grid, z_grid=z_grid, all_grid=all_grid)
        if localized_grid:
            _t(r, "localized_grid", "true")
        return r

    def build_source(self, name: str, *,
                     size: Vector3 = (0, 0, 0),
                     position: Vector3 = (0, 0, 0),
                     source_attribute: Optional[str] = None,
                     active: bool = True, hidden: bool = False,
                     notes: Optional[str] = None) -> ET.Element:
        """Build a <source> geometry element."""
        s = ET.SubElement(self._current, "source")
        _common(s, name=name, position=position, active=active,
                hidden=hidden, notes=notes)
        se = ET.SubElement(s, "size")
        _t(se, "x", f"{size[0]:.6g}")
        _t(se, "y", f"{size[1]:.6g}")
        _t(se, "z", f"{size[2]:.6g}")
        if source_attribute:
            _t(s, "source", source_attribute)
        return s

    def build_domain(self, *,
                     position: Vector3 = (0, 0, 0),
                     size: Vector3 = (0, 0, 0),
                     ambient: Optional[str] = None,
                     x_low_ambient: Optional[str] = None,
                     x_high_ambient: Optional[str] = None,
                     y_low_ambient: Optional[str] = None,
                     y_high_ambient: Optional[str] = None,
                     z_low_ambient: Optional[str] = None,
                     z_high_ambient: Optional[str] = None,
                     x_low_boundary: str = "open",
                     x_high_boundary: str = "open",
                     y_low_boundary: str = "open",
                     y_high_boundary: str = "open",
                     z_low_boundary: str = "open",
                     z_high_boundary: str = "open",
                     fluid: Optional[str] = None,
                     notes: Optional[str] = None) -> ET.Element:
        """Build <solution_domain> — required for project FloXML."""
        sd = ET.SubElement(self._current, "solution_domain")
        _pos(sd, position)
        se = ET.SubElement(sd, "size")
        _t(se, "x", f"{size[0]:.6g}")
        _t(se, "y", f"{size[1]:.6g}")
        _t(se, "z", f"{size[2]:.6g}")
        if ambient:
            for face in ["x_low", "x_high", "y_low", "y_high", "z_low", "z_high"]:
                _t(sd, f"{face}_ambient", ambient)
        if x_low_ambient:
            _t(sd, "x_low_ambient", x_low_ambient)
        if x_high_ambient:
            _t(sd, "x_high_ambient", x_high_ambient)
        if y_low_ambient:
            _t(sd, "y_low_ambient", y_low_ambient)
        if y_high_ambient:
            _t(sd, "y_high_ambient", y_high_ambient)
        if z_low_ambient:
            _t(sd, "z_low_ambient", z_low_ambient)
        if z_high_ambient:
            _t(sd, "z_high_ambient", z_high_ambient)
        if x_low_boundary == "symmetry":
            _t(sd, "x_low_boundary", "symmetry")
        if x_high_boundary == "symmetry":
            _t(sd, "x_high_boundary", "symmetry")
        if y_low_boundary == "symmetry":
            _t(sd, "y_low_boundary", "symmetry")
        if y_high_boundary == "symmetry":
            _t(sd, "y_high_boundary", "symmetry")
        if z_low_boundary == "symmetry":
            _t(sd, "z_low_boundary", "symmetry")
        if z_high_boundary == "symmetry":
            _t(sd, "z_high_boundary", "symmetry")
        if fluid:
            _t(sd, "fluid", fluid)
        if notes:
            _t(sd, "notes", notes)
        return sd

    # Alias
    build_solution_domain = build_domain

    def build_pdml(self, name: str, file: str, *,
                   position: Vector3 = (0, 0, 0),
                   orientation: Optional[Orientation] = None,
                   notes: Optional[str] = None) -> ET.Element:
        """Build a <pdml> file reference element."""
        p = ET.SubElement(self._current, "pdml")
        _t(p, "name", name)
        _t(p, "file", file)
        _pos(p, position)
        if orientation and orientation != IDENTITY_ORIENTATION:
            _ori(p, orientation)
        if notes:
            _t(p, "notes", notes)
        return p

    def build_powermap(self, name: str, file: str, *,
                       position: Vector3 = (0, 0, 0),
                       orientation: Optional[Orientation] = None,
                       material: Optional[str] = None,
                       surface: Optional[str] = None,
                       radiation: Optional[str] = None,
                       x_grid: Optional[str] = None,
                       y_grid: Optional[str] = None,
                       z_grid: Optional[str] = None,
                       all_grid: Optional[str] = None,
                       localized_grid: bool = False,
                       active: bool = True, hidden: bool = False,
                       notes: Optional[str] = None) -> ET.Element:
        """Build a <powermap> element."""
        pm = ET.SubElement(self._current, "powermap")
        _common(pm, name=name, position=position, orientation=orientation,
                active=active, hidden=hidden, notes=notes)
        _t(pm, "file", file)
        if orientation and orientation != IDENTITY_ORIENTATION:
            _ori(pm, orientation)
        _attr_refs(pm, material=material, surface=surface,
                   radiation=radiation, x_grid=x_grid, y_grid=y_grid,
                   z_grid=z_grid, all_grid=all_grid)
        if localized_grid:
            _t(pm, "localized_grid", "true")
        return pm

    # ── DCIM / SmartPart geometry ─────────────────────────────────────

    @contextmanager
    def build_rack(self, name: str, *,
                   position: Vector3 = (0, 0, 0),
                   orientation: Optional[Orientation] = None,
                   power: float = 0,
                   flow_type: str = "volume_flow_rate",
                   flow_value: float = 0,
                   x_grid: Optional[str] = None,
                   active: bool = True, hidden: bool = False):
        """Build a <rack> (FloTHERM DCIM). Context manager for supplies/extracts."""
        r = ET.SubElement(self._current, "rack")
        _common(r, name=name, position=position, orientation=orientation,
                active=active, hidden=hidden)
        if power:
            _t(r, "power_dissipation", f"{power:.6g}")
        _t(r, "flow_type", flow_type)
        if flow_value:
            _t(r, "flow_rate", f"{flow_value:.6g}")
        if x_grid:
            _t(r, "x_grid_constraint", x_grid)
        prev = self._current
        self._current = r
        try:
            yield r
        finally:
            self._current = prev

    @contextmanager
    def build_cooler(self, name: str, *,
                     position: Vector3 = (0, 0, 0),
                     orientation: Optional[Orientation] = None,
                     flow_type: str = "volume_flow_rate",
                     flow_value: float = 0,
                     supply_temperature: float = 0,
                     active: bool = True):
        """Build a <cooler> (FloTHERM DCIM). Context manager for supplies/extracts."""
        c = ET.SubElement(self._current, "cooler")
        _common(c, name=name, position=position, orientation=orientation, active=active)
        _t(c, "airflow_type", flow_type)
        if flow_value:
            _t(c, "flow_rate", f"{flow_value:.6g}")
        if supply_temperature:
            _t(c, "temperature_set_point", f"{supply_temperature:.6g}")
        prev = self._current
        self._current = c
        try:
            yield c
        finally:
            self._current = prev

    def build_supply(self, name: str, *,
                     position: Vector3 = (0, 0, 0),
                     orientation: Optional[Orientation] = None,
                     size: Vector3 = (0, 0, 0),
                     free_area_ratio: float = 1,
                     active: bool = True, hidden: bool = False,
                     notes: Optional[str] = None) -> ET.Element:
        """Build a <supply> element inside rack/cooler."""
        s = ET.SubElement(self._current, "supply")
        _common(s, name=name, position=position, orientation=orientation,
                active=active, hidden=hidden, notes=notes)
        se = ET.SubElement(s, "size")
        _t(se, "x", f"{size[0]:.6g}")
        _t(se, "y", f"{size[1]:.6g}")
        _t(s, "free_area_ratio", f"{free_area_ratio:.6g}")
        return s

    def build_extract(self, name: str, *,
                      position: Vector3 = (0, 0, 0),
                      orientation: Optional[Orientation] = None,
                      size: Vector3 = (0, 0, 0),
                      active: bool = True, hidden: bool = False,
                      notes: Optional[str] = None) -> ET.Element:
        """Build an <extract> element inside rack/cooler."""
        e = ET.SubElement(self._current, "extract")
        _common(e, name=name, position=position, orientation=orientation,
                active=active, hidden=hidden, notes=notes)
        se = ET.SubElement(e, "size")
        _t(se, "x", f"{size[0]:.6g}")
        _t(se, "y", f"{size[1]:.6g}")
        return e

    def build_perforated_plate(self, name: str, *,
                               size: Vector3 = (0, 0, 0),
                               position: Vector3 = (0, 0, 0),
                               orientation: Optional[Orientation] = None,
                               free_area_ratio: float = 0.55,
                               resistance: Optional[str] = None,
                               x_grid: Optional[str] = None,
                               active: bool = True, hidden: bool = False,
                               notes: Optional[str] = None) -> ET.Element:
        """Build a <perforated_plate> element."""
        pp = ET.SubElement(self._current, "perforated_plate")
        _common(pp, name=name, position=position, orientation=orientation,
                active=active, hidden=hidden, notes=notes)
        se = ET.SubElement(pp, "size")
        _t(se, "x", f"{size[0]:.6g}")
        _t(se, "y", f"{size[1]:.6g}")
        if orientation and orientation != IDENTITY_ORIENTATION:
            _ori(pp, orientation)
        _t(pp, "hole_type", "perforated")
        _t(pp, "coverage", f"{free_area_ratio:.6g}")
        _attr_refs(pp, resistance=resistance, x_grid=x_grid)
        return pp

    @contextmanager
    def build_enclosure(self, name: str, *,
                        size: Vector3 = (0, 0, 0),
                        position: Vector3 = (0, 0, 0),
                        wall_thickness: float = 0.001,
                        material: Optional[str] = None,
                        radiation: Optional[str] = None,
                        active: bool = True, hidden: bool = False):
        """Build an <enclosure> smartpart."""
        e = ET.SubElement(self._current, "enclosure")
        _common(e, name=name, position=position, active=active, hidden=hidden)
        se = ET.SubElement(e, "size")
        _t(se, "x", f"{size[0]:.6g}")
        _t(se, "y", f"{size[1]:.6g}")
        _t(se, "z", f"{size[2]:.6g}")
        _t(e, "wall_thickness", f"{wall_thickness:.6g}")
        _attr_refs(e, material=material, radiation=radiation)
        prev = self._current
        self._current = e
        try:
            yield e
        finally:
            self._current = prev

    def build_fixed_flow(self, name: str, *,
                         position: Vector3 = (0, 0, 0),
                         orientation: Optional[Orientation] = None,
                         size: Vector3 = (0, 0, 0),
                         flow_type: str = "volume_flow_rate",
                         flow_value: float = 0,
                         ambient: Optional[str] = None,
                         active: bool = True, hidden: bool = False,
                         notes: Optional[str] = None) -> ET.Element:
        """Build a <fixed_flow> element."""
        ff = ET.SubElement(self._current, "fixed_flow")
        _common(ff, name=name, position=position, orientation=orientation,
                active=active, hidden=hidden, notes=notes)
        se = ET.SubElement(ff, "size")
        _t(se, "x", f"{size[0]:.6g}")
        _t(se, "y", f"{size[1]:.6g}")
        _t(ff, "flow_type", flow_type)
        _t(ff, "flow_rate", f"{flow_value:.6g}")
        if ambient:
            _t(ff, "ambient", ambient)
        return ff

    @contextmanager
    def build_fan_geometry(self, name: str, *,
                           position: Vector3 = (0, 0, 0),
                           orientation: Optional[Orientation] = None,
                           fan_attribute: Optional[str] = None,
                           material: Optional[str] = None,
                           derating_factor: float = 1,
                           active: bool = True, hidden: bool = False):
        """Build a <fan> geometry element (context manager)."""
        f = ET.SubElement(self._current, "fan")
        _common(f, name=name, position=position, orientation=orientation,
                active=active, hidden=hidden)
        if orientation and orientation != IDENTITY_ORIENTATION:
            _ori(f, orientation)
        _t(f, "derating_factor", f"{derating_factor:.6g}")
        if fan_attribute:
            _t(f, "fan", fan_attribute)
        if material:
            _t(f, "material", material)
        prev = self._current
        self._current = f
        try:
            yield f
        finally:
            self._current = prev


# ======================================================================
# Example model — mirrors VBA CREATEMODEL()
# ======================================================================
def create_example_model() -> FloXMLBuilder:
    """Create an example model containing all supported object types."""
    b = FloXMLBuilder("My Model")

    # MODEL
    with b.model_section():
        b.modeling_setup(solution="flow_heat", radiation="on")
        b.turbulence_setup(model="auto_algebraic")
        b.gravity_setup(direction="neg_z", value=9.81)
        b.global_setup(ambient_temperature=300)

    # SOLVE
    with b.solve_section():
        b.overall_control(max_iterations=1500)

    # GRID
    with b.grid_section():
        b.system_grid(x_min_size=0.001, x_control=("min_number", 24))

    # ATTRIBUTES
    with b.attributes_section():
        with b.materials_section():
            b.create_material("Aluminum", k=160, rho=2300, cp=455)
            b.create_material("FR4", k=0.3, rho=1200, cp=880)
            b.create_material("Copper", k=400, rho=8930, cp=385)

        with b.ambients_section():
            b.create_ambient("Outside World", temperature=293)

        with b.fluids_section():
            b.create_fluid("Air", notes="AIR STANDARD PROPERTIES")

        with b.thermals_section():
            b.create_thermal("Heat", model_type="total_power", power=12.5)

        with b.radiations_section():
            b.create_radiation("Sub-Divided1", rad_type="subdivided")

        with b.fans_section():
            b.create_fan("Fan Curve 1", curve_type="non_linear",
                         open_flow_rate=200, stagnation_pressure=100,
                         fan_curve=[(0, 200), (0.1, 195), (0.2, 164),
                                    (0.3, 112), (0.4, 44), (0.5, 0)])

    # GEOMETRY
    with b.geometry_section():
        b.build_cuboid("Block", size=(1.1, 2.2, 3.3),
                       material="Aluminum", thermal="Heat",
                       radiation="Sub-Divided1")

        with b.build_assembly("Sub Assembly 1", position=(1, 0, 0)):
            b.build_cuboid("Block in Assembly", size=(0.5, 0.5, 0.5),
                           material="FR4")

        b.build_monitor_point("MP-01", position=(0.025, 0.025, 0.025))

    # SOLUTION DOMAIN
    b.build_solution_domain(size=(0.05, 0.05, 0.05),
                            ambient="Outside World", fluid="Air")

    return b


# ======================================================================
# CLI
# ======================================================================
def main():
    import argparse
    parser = argparse.ArgumentParser(description="FloXML 项目生成器")
    parser.add_argument("-o", "--output", default="output.xml",
                        help="输出文件路径 (default: output.xml)")
    parser.add_argument("--example", action="store_true",
                        help="生成包含全部对象类型的示例模型")
    args = parser.parse_args()

    if args.example:
        builder = create_example_model()
    else:
        builder = create_example_model()  # default to example for now

    builder.write(args.output)
    print(f"[OK] FloXML written to {args.output}")


if __name__ == "__main__":
    main()
