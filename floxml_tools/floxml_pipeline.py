#!/usr/bin/env python3
"""FloXML build pipeline: combine wrap, grid/regions, and solve settings in one pass.

Usage:
    # Single config for both grid and solve
    python -m floxml_tools.floxml_pipeline geometry.xml -c config.json --wrap -o project.xml

    # Separate configs still supported
    python -m floxml_tools.floxml_pipeline base.xml --grid grid.json --solve solve.json -o out.xml

    # Grid only
    python -m floxml_tools.floxml_pipeline base.xml --grid grid.json -o out.xml

    # Solve only
    python -m floxml_tools.floxml_pipeline base.xml --solve solve.json -o out.xml
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Optional
import xml.etree.ElementTree as ET

from floxml_tools.floxml_add_volume_regions import (
    add_regions,
    load_config as load_grid_config,
    indent_xml,
)
from floxml_tools.floxml_add_solve_settings import (
    apply_solve_settings,
    load_config as load_solve_config,
)
from floxml_tools.wrap_geometry_floxml_as_project import (
    _build_default_model,
    _build_default_solve,
    _build_default_grid,
    _clone,
    _compute_geometry_bounds,
    _ensure_ambient,
    _ensure_fluid,
    _find_first_name,
    _append_text,
)


def wrap_element(
    root: ET.Element,
    name_stem: str = "",
    padding_ratio: float = 0.1,
    minimum_padding: float = 0.01,
) -> ET.Element:
    """Wrap a geometry/assembly FloXML root as a project FloXML (in-memory).

    Reuses internal helpers from wrap_geometry_floxml_as_project to avoid
    file I/O — operates entirely on the parsed element tree.
    """
    if root.tag != "xml_case":
        raise ValueError("input root element must be <xml_case>")

    if root.find("model") is not None or root.find("solve") is not None or root.find("grid") is not None:
        raise ValueError(
            "input already looks like a project FloXML; --wrap is for geometry/assembly FloXML only"
        )

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

    input_name = root.findtext("name", default=name_stem).strip()
    wrapped_root = ET.Element("xml_case")
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

    return wrapped_root


def _load_json(path: Path) -> dict:
    """Load a JSON config file."""
    import json
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


# Keys recognized by add_regions (grid/regions)
_GRID_KEYS = {"grid_constraints", "object_constraints", "regions"}
# Keys recognized by apply_solve_settings (model/solve)
_SOLVE_KEYS = {
    "modeling", "turbulence", "gravity", "global", "initial_variables",
    "overall_control", "variable_controls", "solver_controls", "transient",
}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="FloXML build pipeline: wrap, grid/regions, and solve settings in one pass"
    )
    parser.add_argument("input", help="Input FloXML file (.xml)")
    parser.add_argument(
        "-c", "--config",
        help="Unified config file (.json) containing both grid and solve settings",
    )
    parser.add_argument("--grid", help="Grid/regions config file (.json or .xlsx)")
    parser.add_argument("--solve", help="Solve settings config file (.json or .xlsx)")
    parser.add_argument(
        "--wrap",
        action="store_true",
        help="Wrap geometry/assembly FloXML as project FloXML first",
    )
    parser.add_argument(
        "--padding-ratio",
        type=float,
        default=0.1,
        help="Domain padding ratio for --wrap (default: 0.1)",
    )
    parser.add_argument(
        "--minimum-padding",
        type=float,
        default=0.01,
        help="Minimum padding in meters for --wrap (default: 0.01)",
    )
    parser.add_argument("-o", "--output", help="Output FloXML file")
    return parser


def main(argv: Optional[list[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if not any([args.config, args.grid, args.solve, args.wrap]):
        parser.error("At least one of -c, --grid, --solve, or --wrap is required")

    input_path = Path(args.input).resolve()
    if not input_path.is_file():
        print(f"[ERROR] Input file not found: {input_path}", file=sys.stderr)
        return 1

    output_path = (
        Path(args.output).resolve()
        if args.output
        else input_path.with_name(f"{input_path.stem}_built.xml")
    )

    # Resolve config sources: -c splits into grid + solve; --grid/--solve override
    grid_config = None
    solve_config = None

    if args.config:
        config_path = Path(args.config).resolve()
        if not config_path.is_file():
            print(f"[ERROR] Config not found: {config_path}", file=sys.stderr)
            return 1
        unified = _load_json(config_path)
        # Split by recognized keys
        grid_part = {k: v for k, v in unified.items() if k in _GRID_KEYS}
        solve_part = {k: v for k, v in unified.items() if k in _SOLVE_KEYS}
        unknown = set(unified) - _GRID_KEYS - _SOLVE_KEYS
        if unknown:
            print(f"[WARN] Unknown keys in config ignored: {unknown}", file=sys.stderr)
        if grid_part:
            grid_config = grid_part
        if solve_part:
            solve_config = solve_part

    if args.grid:
        grid_config_path = Path(args.grid).resolve()
        if not grid_config_path.is_file():
            print(f"[ERROR] Grid config not found: {grid_config_path}", file=sys.stderr)
            return 1
        grid_config = load_grid_config(grid_config_path)

    if args.solve:
        solve_config_path = Path(args.solve).resolve()
        if not solve_config_path.is_file():
            print(f"[ERROR] Solve config not found: {solve_config_path}", file=sys.stderr)
            return 1
        solve_config = load_solve_config(solve_config_path)

    try:
        tree = ET.parse(input_path)
        root = tree.getroot()

        # Step 1: Wrap as project FloXML (if requested)
        if args.wrap:
            root = wrap_element(
                root,
                name_stem=input_path.stem,
                padding_ratio=args.padding_ratio,
                minimum_padding=args.minimum_padding,
            )

        # Step 2: Add grid/regions (if config has grid keys)
        if grid_config:
            root = add_regions(root, grid_config)

        # Step 3: Add solve settings (if config has solve keys)
        if solve_config:
            root = apply_solve_settings(root, solve_config)

        # Step 4: Indent and write
        indent_xml(root)
        out_tree = ET.ElementTree(root)
        out_tree.write(output_path, encoding="utf-8", xml_declaration=True)

    except Exception as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        return 1

    steps = []
    if args.wrap:
        steps.append("wrapped as project")
    if grid_config:
        steps.append("added grid/regions")
    if solve_config:
        steps.append("applied solve settings")
    print(f"[OK] {' -> '.join(steps)}: {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
