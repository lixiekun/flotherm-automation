#!/usr/bin/env python3
"""
Wrap a geometry/assembly FloXML file as a minimal project FloXML.

This is useful for spreadsheet-generated compact-model XML files that
contain only:
  - <attributes>
  - <geometry>

The wrapper preserves the original attributes/geometry and adds the
minimum project-level sections required for project-style import:
  - <model>
  - <solve>
  - <grid>
  - <solution_domain>

Input requirements:
  1. Input must be an XML FloXML file, not an Excel workbook.
  2. Root element must be <xml_case>.
  3. File must contain <geometry>.
  4. File should not already be a full project FloXML with <model>,
     <solve>, <grid>, or <solution_domain>.
"""

from __future__ import annotations

import argparse
import copy
from pathlib import Path
from typing import Iterable, Optional, Tuple
import xml.etree.ElementTree as ET


def _float_text(parent: ET.Element, tag: str) -> Optional[float]:
    child = parent.find(tag)
    if child is None or child.text is None:
        return None
    try:
        return float(child.text.strip())
    except ValueError:
        return None


def _clone(element: ET.Element) -> ET.Element:
    return copy.deepcopy(element)


def _find_first_name(attributes: ET.Element, section_tag: str, item_tag: str) -> Optional[str]:
    section = attributes.find(section_tag)
    if section is None:
        return None
    for item in section.findall(item_tag):
        name = item.find("name")
        if name is not None and name.text:
            return name.text.strip()
    return None


def _compute_geometry_bounds(geometry: ET.Element) -> Optional[Tuple[float, float, float, float, float, float]]:
    bounds: Optional[Tuple[float, float, float, float, float, float]] = None

    for element in geometry.iter():
        position = element.find("position")
        size = element.find("size")
        if position is None or size is None:
            continue

        px = _float_text(position, "x")
        py = _float_text(position, "y")
        pz = _float_text(position, "z")
        sx = _float_text(size, "x")
        sy = _float_text(size, "y")
        sz = _float_text(size, "z")
        if None in (px, py, pz, sx, sy, sz):
            continue

        element_bounds = (px, py, pz, px + sx, py + sy, pz + sz)
        if bounds is None:
            bounds = element_bounds
        else:
            bounds = (
                min(bounds[0], element_bounds[0]),
                min(bounds[1], element_bounds[1]),
                min(bounds[2], element_bounds[2]),
                max(bounds[3], element_bounds[3]),
                max(bounds[4], element_bounds[4]),
                max(bounds[5], element_bounds[5]),
            )

    return bounds


def _append_text(parent: ET.Element, tag: str, text: str) -> ET.Element:
    element = ET.SubElement(parent, tag)
    element.text = text
    return element


def _build_default_model() -> ET.Element:
    model = ET.Element("model")

    modeling = ET.SubElement(model, "modeling")
    for tag, value in (
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
        _append_text(modeling, tag, value)

    turbulence = ET.SubElement(model, "turbulence")
    _append_text(turbulence, "type", "turbulent")
    _append_text(turbulence, "turbulence_type", "auto_algebraic")

    gravity = ET.SubElement(model, "gravity")
    _append_text(gravity, "type", "normal")
    _append_text(gravity, "normal_direction", "neg_y")
    _append_text(gravity, "value_type", "user")
    _append_text(gravity, "gravity_value", "9.81")

    global_settings = ET.SubElement(model, "global")
    for tag, value in (
        ("datum_pressure", "101325"),
        ("radiant_temperature", "300"),
        ("ambient_temperature", "300"),
        ("concentration_1", "0"),
        ("concentration_2", "0"),
        ("concentration_3", "0"),
        ("concentration_4", "0"),
        ("concentration_5", "0"),
    ):
        _append_text(global_settings, tag, value)

    return model


def _build_default_solve() -> ET.Element:
    solve = ET.Element("solve")
    overall = ET.SubElement(solve, "overall_control")
    for tag, value in (
        ("outer_iterations", "500"),
        ("fan_relaxation", "1"),
        ("estimated_free_convection_velocity", "0.2"),
        ("solver_option", "multi_grid"),
        ("active_plate_conduction", "false"),
        ("use_double_precision", "false"),
        ("network_assembly_block_correction", "false"),
        ("freeze_flow", "false"),
        ("store_error_field", "false"),
    ):
        _append_text(overall, tag, value)
    return solve


def _grid_axis(parent: ET.Element, axis_tag: str, min_size: float, max_size: float) -> None:
    axis = ET.SubElement(parent, axis_tag)
    _append_text(axis, "min_size", f"{min_size:.6g}")
    _append_text(axis, "grid_type", "max_size")
    _append_text(axis, "max_size", f"{max_size:.6g}")
    _append_text(axis, "smoothing_value", "12")


def _build_default_grid(domain_size: Tuple[float, float, float]) -> ET.Element:
    x_size, y_size, z_size = domain_size
    grid = ET.Element("grid")
    system_grid = ET.SubElement(grid, "system_grid")
    _append_text(system_grid, "smoothing", "true")
    _append_text(system_grid, "smoothing_type", "v3")
    _append_text(system_grid, "dynamic_update", "true")

    _grid_axis(system_grid, "x_grid", min(max(x_size / 100.0, 1e-4), 0.001), max(x_size / 12.0, 0.001))
    _grid_axis(system_grid, "y_grid", min(max(y_size / 100.0, 1e-4), 0.001), max(y_size / 12.0, 0.001))
    _grid_axis(system_grid, "z_grid", min(max(z_size / 100.0, 1e-4), 0.0005), max(z_size / 8.0, 0.001))
    return grid


def _ensure_ambient(attributes: ET.Element, ambient_name: str) -> None:
    if attributes.find("ambients") is not None:
        return

    ambients = ET.SubElement(attributes, "ambients")
    ambient = ET.SubElement(ambients, "ambient_att")
    for tag, value in (
        ("name", ambient_name),
        ("pressure", "0"),
        ("temperature", "300"),
        ("radiant_temperature", "300"),
        ("heat_transfer_coeff", "0"),
    ):
        _append_text(ambient, tag, value)

    velocity = ET.SubElement(ambient, "velocity")
    for tag in ("x", "y", "z"):
        _append_text(velocity, tag, "0")

    for tag in (
        "turbulent_kinetic_energy",
        "turbulent_dissipation_rate",
        "concentration_1",
        "concentration_2",
        "concentration_3",
        "concentration_4",
        "concentration_5",
    ):
        _append_text(ambient, tag, "0")


def _ensure_fluid(attributes: ET.Element, fluid_name: str) -> None:
    if attributes.find("fluids") is not None:
        return

    fluids = ET.SubElement(attributes, "fluids")
    fluid = ET.SubElement(fluids, "fluid_att")
    for tag, value in (
        ("name", fluid_name),
        ("conductivity_type", "constant"),
        ("conductivity", "0.0261"),
        ("viscosity_type", "constant"),
        ("viscosity", "0.0000184"),
        ("density_type", "constant"),
        ("density", "1.16"),
        ("specific_heat", "1008"),
        ("expansivity", "0.003"),
        ("diffusivity", "0"),
    ):
        _append_text(fluid, tag, value)


def wrap_geometry_floxml(
    input_path: Path,
    output_path: Path,
    padding_ratio: float = 0.1,
    minimum_padding: float = 0.01,
) -> None:
    if input_path.suffix.lower() in {".xlsm", ".xlsx", ".xls"}:
        raise ValueError("input must be a FloXML .xml file, not an Excel workbook")

    tree = ET.parse(input_path)
    root = tree.getroot()
    if root.tag != "xml_case":
        raise ValueError("input root element must be <xml_case>")

    if root.find("model") is not None or root.find("solve") is not None or root.find("grid") is not None:
        raise ValueError("input already looks like a project FloXML; wrapper is for geometry/assembly FloXML only")

    geometry = root.find("geometry")
    if geometry is None:
        raise ValueError("input FloXML must contain <geometry>")

    input_attributes = root.find("attributes")
    attributes = _clone(input_attributes) if input_attributes is not None else ET.Element("attributes")

    ambient_name = _find_first_name(attributes, "ambients", "ambient_att") or "Ambient"
    fluid_name = _find_first_name(attributes, "fluids", "fluid_att") or "Air"
    _ensure_ambient(attributes, ambient_name)
    _ensure_fluid(attributes, fluid_name)

    bounds = _compute_geometry_bounds(geometry)
    if bounds is None:
        bounds = (0.0, 0.0, 0.0, 1.0, 1.0, 1.0)

    min_x, min_y, min_z, max_x, max_y, max_z = bounds
    geom_x = max(max_x - min_x, 0.001)
    geom_y = max(max_y - min_y, 0.001)
    geom_z = max(max_z - min_z, 0.001)

    pad_x = max(geom_x * padding_ratio, minimum_padding)
    pad_y = max(geom_y * padding_ratio, minimum_padding)
    pad_z = max(geom_z * padding_ratio, minimum_padding)

    domain_pos = (min_x - pad_x / 2.0, min_y - pad_y / 2.0, min_z - pad_z / 2.0)
    domain_size = (geom_x + pad_x, geom_y + pad_y, geom_z + pad_z)

    wrapped_root = ET.Element("xml_case")
    input_name = root.findtext("name", default=input_path.stem).strip()
    _append_text(wrapped_root, "name", f"{input_name}_Project")
    wrapped_root.append(_build_default_model())
    wrapped_root.append(_build_default_solve())
    wrapped_root.append(_build_default_grid(domain_size))
    wrapped_root.append(attributes)
    wrapped_root.append(_clone(geometry))

    solution_domain = ET.SubElement(wrapped_root, "solution_domain")
    position = ET.SubElement(solution_domain, "position")
    _append_text(position, "x", f"{domain_pos[0]:.6g}")
    _append_text(position, "y", f"{domain_pos[1]:.6g}")
    _append_text(position, "z", f"{domain_pos[2]:.6g}")
    size = ET.SubElement(solution_domain, "size")
    _append_text(size, "x", f"{domain_size[0]:.6g}")
    _append_text(size, "y", f"{domain_size[1]:.6g}")
    _append_text(size, "z", f"{domain_size[2]:.6g}")

    for tag in (
        "x_low_ambient",
        "x_high_ambient",
        "y_low_ambient",
        "y_high_ambient",
        "z_low_ambient",
        "z_high_ambient",
    ):
        _append_text(solution_domain, tag, ambient_name)
    _append_text(solution_domain, "fluid", fluid_name)

    wrapped_tree = ET.ElementTree(wrapped_root)
    ET.indent(wrapped_tree, space="    ")
    xml_bytes = ET.tostring(wrapped_root, encoding="utf-8")
    output_text = '<?xml version="1.0" encoding="UTF-8" standalone="no" ?>\n' + xml_bytes.decode("utf-8")
    output_path.write_text(output_text, encoding="utf-8", newline="\n")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Wrap a geometry/assembly FloXML file as a project FloXML"
    )
    parser.add_argument("input", type=Path, help="input geometry/assembly FloXML (.xml)")
    parser.add_argument("-o", "--output", type=Path, help="output project FloXML (.xml)")
    parser.add_argument(
        "--padding-ratio",
        type=float,
        default=0.1,
        help="domain padding ratio relative to geometry size (default: 0.1)",
    )
    parser.add_argument(
        "--minimum-padding",
        type=float,
        default=0.01,
        help="minimum absolute domain padding in meters (default: 0.01)",
    )
    return parser


def main(argv: Optional[Iterable[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)

    input_path = args.input.resolve()
    if args.output is None:
        output_path = input_path.with_name(f"{input_path.stem}_project.xml")
    else:
        output_path = args.output.resolve()

    try:
        wrap_geometry_floxml(
            input_path=input_path,
            output_path=output_path,
            padding_ratio=args.padding_ratio,
            minimum_padding=args.minimum_padding,
        )
    except Exception as exc:
        print(f"[ERROR] {exc}")
        return 1

    print("=" * 60)
    print("FloXML Project Wrapper")
    print("=" * 60)
    print(f"Input  : {input_path}")
    print(f"Output : {output_path}")
    print("[OK] Project FloXML created successfully.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
