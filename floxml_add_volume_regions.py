#!/usr/bin/env python3
"""
Add FloTHERM volume regions (<region>) to an existing FloXML project using JSON config.

The same config can also:
- create/update grid_constraint_att definitions
- assign grid constraints directly onto existing geometry objects

Supported region definition modes:
1. Explicit:
   - position: [x, y, z]
   - size: [sx, sy, sz]

2. Derived from existing geometry bounding boxes:
   - bbox_from:
       include_names: ["PCB", "U1", "U2"]
       include_patterns: ["R22 *", "C*"]
       padding: 0.001
       or padding: [0.001, 0.001, 0.0005]

Each region may be inserted at root geometry or under a named assembly.
"""

from __future__ import annotations

import argparse
import copy
import fnmatch
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple
import xml.etree.ElementTree as ET


Vector3 = Tuple[float, float, float]


@dataclass
class GeometryItem:
    name: str
    tag: str
    position: Vector3
    size: Optional[Vector3]
    global_position: Vector3
    global_size: Optional[Vector3]
    element: ET.Element
    parent_geometry: ET.Element
    assembly_path: Tuple[str, ...]


def _float_text(parent: ET.Element, tag: str, default: float = 0.0) -> float:
    child = parent.find(tag)
    if child is None or child.text is None:
        return default
    try:
        return float(child.text.strip())
    except ValueError:
        return default


def _parse_position(elem: ET.Element) -> Vector3:
    pos = elem.find("position")
    if pos is None:
        return (0.0, 0.0, 0.0)
    return (
        _float_text(pos, "x"),
        _float_text(pos, "y"),
        _float_text(pos, "z"),
    )


def _parse_size(elem: ET.Element) -> Optional[Vector3]:
    size = elem.find("size")
    if size is None:
        return None
    return (
        _float_text(size, "x"),
        _float_text(size, "y"),
        _float_text(size, "z"),
    )


def _append_text(parent: ET.Element, tag: str, text: str) -> ET.Element:
    elem = ET.SubElement(parent, tag)
    elem.text = text
    return elem


def _set_text(parent: ET.Element, tag: str, text: str) -> ET.Element:
    child = parent.find(tag)
    if child is None:
        child = ET.SubElement(parent, tag)
    child.text = text
    return child


def _vector_add(a: Vector3, b: Vector3) -> Vector3:
    return (a[0] + b[0], a[1] + b[1], a[2] + b[2])


def _vector_sub(a: Vector3, b: Vector3) -> Vector3:
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def _normalize_padding(value) -> Vector3:
    if isinstance(value, (int, float)):
        padding = float(value)
        return (padding, padding, padding)
    if isinstance(value, list) and len(value) == 3:
        return (float(value[0]), float(value[1]), float(value[2]))
    return (0.0, 0.0, 0.0)


def _iter_geometry_items(
    geometry_elem: ET.Element,
    parent_global: Vector3 = (0.0, 0.0, 0.0),
    assembly_path: Tuple[str, ...] = (),
) -> Iterable[GeometryItem]:
    for child in list(geometry_elem):
        tag = child.tag
        position = _parse_position(child)
        size = _parse_size(child)
        global_position = _vector_add(parent_global, position)
        global_size = size
        name = (child.findtext("name") or "").strip()

        yield GeometryItem(
            name=name,
            tag=tag,
            position=position,
            size=size,
            global_position=global_position,
            global_size=global_size,
            element=child,
            parent_geometry=geometry_elem,
            assembly_path=assembly_path,
        )

        child_geometry = child.find("geometry")
        if child_geometry is not None:
            next_path = assembly_path
            if tag == "assembly" and name:
                next_path = assembly_path + (name,)
            yield from _iter_geometry_items(
                child_geometry,
                parent_global=global_position,
                assembly_path=next_path,
            )


def _iter_all_geometry_items(root_geometry: ET.Element) -> Iterable[GeometryItem]:
    for item in _iter_geometry_items(root_geometry):
        yield item
        child_geometry = item.element.find("geometry")
        if child_geometry is not None:
            next_path = item.assembly_path
            if item.tag == "assembly" and item.name:
                next_path = item.assembly_path + (item.name,)
            yield from _iter_geometry_items(
                child_geometry,
                parent_global=item.global_position,
                assembly_path=next_path,
            )


def _find_root_geometry(root: ET.Element) -> ET.Element:
    geometry = root.find("geometry")
    if geometry is None:
        raise ValueError("FloXML missing <geometry> section")
    return geometry


def _find_or_create_attributes(root: ET.Element) -> ET.Element:
    attributes = root.find("attributes")
    if attributes is None:
        insert_at = 0
        for idx, child in enumerate(list(root)):
            if child.tag in {"geometry", "solution_domain"}:
                insert_at = idx
                break
            insert_at = idx + 1
        attributes = ET.Element("attributes")
        root.insert(insert_at, attributes)
    return attributes


def _find_or_create_grid_constraints(attributes: ET.Element) -> ET.Element:
    grid_constraints = attributes.find("grid_constraints")
    if grid_constraints is None:
        grid_constraints = ET.SubElement(attributes, "grid_constraints")
    return grid_constraints


def _find_assembly_element(root_geometry: ET.Element, assembly_name: str) -> Optional[ET.Element]:
    for item in _iter_all_geometry_items(root_geometry):
        if item.tag == "assembly" and item.name == assembly_name:
            return item.element
    return None


def _ensure_geometry_container(parent_elem: ET.Element) -> ET.Element:
    geometry = parent_elem.find("geometry")
    if geometry is None:
        geometry = ET.SubElement(parent_elem, "geometry")
    return geometry


def _compute_bbox(items: List[GeometryItem]) -> Tuple[Vector3, Vector3]:
    if not items:
        raise ValueError("No matching geometry items found for bbox_from")

    mins = [float("inf")] * 3
    maxs = [float("-inf")] * 3

    for item in items:
        if item.global_size is None:
            continue
        for axis in range(3):
            mins[axis] = min(mins[axis], item.global_position[axis])
            maxs[axis] = max(maxs[axis], item.global_position[axis] + item.global_size[axis])

    if mins[0] == float("inf"):
        raise ValueError("Matching items did not have usable size data for bbox_from")

    return (tuple(mins), tuple(maxs))  # type: ignore[arg-type]


def _match_items(
    root_geometry: ET.Element,
    include_names: List[str],
    include_patterns: List[str],
    scope_assembly: Optional[str],
) -> List[GeometryItem]:
    matches: List[GeometryItem] = []
    for item in _iter_all_geometry_items(root_geometry):
        if not item.name:
            continue
        if scope_assembly and scope_assembly not in item.assembly_path and item.name != scope_assembly:
            continue
        if item.name in include_names or any(fnmatch.fnmatch(item.name, pattern) for pattern in include_patterns):
            matches.append(item)
    return matches


def _apply_object_constraint(item: GeometryItem, cfg: Dict) -> None:
    for constraint_tag in ("x_grid_constraint", "y_grid_constraint", "z_grid_constraint", "all_grid_constraint"):
        if cfg.get(constraint_tag):
            _set_text(item.element, constraint_tag, str(cfg[constraint_tag]))
    if cfg.get("localized_grid") is not None:
        _set_text(item.element, "localized_grid", "true" if cfg["localized_grid"] else "false")


def _apply_object_constraints(root_geometry: ET.Element, config: Dict) -> int:
    applied = 0
    for obj_cfg in config.get("object_constraints", []):
        include_names = list(obj_cfg.get("target_names", []))
        include_patterns = list(obj_cfg.get("target_patterns", []))
        scope_assembly = obj_cfg.get("scope_assembly")
        matches = _match_items(root_geometry, include_names, include_patterns, scope_assembly)
        if not matches:
            raise ValueError(
                f"object_constraints target did not match any geometry: "
                f"names={include_names}, patterns={include_patterns}, scope_assembly={scope_assembly}"
            )
        for item in matches:
            _apply_object_constraint(item, obj_cfg)
            applied += 1
    return applied


def _build_region_element(name: str, position: Vector3, size: Vector3, cfg: Dict) -> ET.Element:
    region = ET.Element("region")
    _append_text(region, "name", name)
    _append_text(region, "active", "true" if cfg.get("active", True) else "false")
    if cfg.get("hidden") is not None:
        _append_text(region, "hidden", "true" if cfg["hidden"] else "false")

    pos = ET.SubElement(region, "position")
    _append_text(pos, "x", f"{position[0]:.6g}")
    _append_text(pos, "y", f"{position[1]:.6g}")
    _append_text(pos, "z", f"{position[2]:.6g}")

    size_elem = ET.SubElement(region, "size")
    _append_text(size_elem, "x", f"{size[0]:.6g}")
    _append_text(size_elem, "y", f"{size[1]:.6g}")
    _append_text(size_elem, "z", f"{size[2]:.6g}")

    orientation = ET.SubElement(region, "orientation")
    for axis_tag, vec in (
        ("local_x", ("1", "0", "0")),
        ("local_y", ("0", "0", "1")),
        ("local_z", ("0", "1", "0")),
    ):
        axis = ET.SubElement(orientation, axis_tag)
        _append_text(axis, "i", vec[0])
        _append_text(axis, "j", vec[1])
        _append_text(axis, "k", vec[2])

    for constraint_tag in ("x_grid_constraint", "y_grid_constraint", "z_grid_constraint"):
        if cfg.get(constraint_tag):
            _append_text(region, constraint_tag, str(cfg[constraint_tag]))

    if cfg.get("all_grid_constraint"):
        _append_text(region, "all_grid_constraint", str(cfg["all_grid_constraint"]))

    _append_text(region, "localized_grid", "true" if cfg.get("localized_grid", True) else "false")
    return region


def _upsert_grid_constraint(grid_constraints_elem: ET.Element, cfg: Dict) -> ET.Element:
    name = cfg.get("name")
    if not name:
        raise ValueError("Each grid constraint requires a name")

    existing = None
    for child in grid_constraints_elem.findall("grid_constraint_att"):
        if (child.findtext("name") or "").strip() == name:
            existing = child
            break

    elem = existing if existing is not None else ET.SubElement(grid_constraints_elem, "grid_constraint_att")
    _set_text(elem, "name", str(name))
    _set_text(elem, "enable_min_cell_size", "true" if cfg.get("enable_min_cell_size", True) else "false")

    if cfg.get("min_cell_size") is not None:
        _set_text(elem, "min_cell_size", f"{float(cfg['min_cell_size']):.6g}")

    _set_text(elem, "number_cells_control", str(cfg.get("number_cells_control", "min_number")))
    if cfg.get("min_number") is not None:
        _set_text(elem, "min_number", str(cfg["min_number"]))

    hi_cfg = cfg.get("high_inflation")
    if hi_cfg:
        hi = elem.find("high_inflation")
        if hi is None:
            hi = ET.SubElement(elem, "high_inflation")
        _set_text(hi, "inflation_type", str(hi_cfg.get("inflation_type", "size")))
        if hi_cfg.get("inflation_size") is not None:
            _set_text(hi, "inflation_size", f"{float(hi_cfg['inflation_size']):.6g}")
        _set_text(hi, "number_cells_control", str(hi_cfg.get("number_cells_control", "min_number")))
        if hi_cfg.get("min_number") is not None:
            _set_text(hi, "min_number", str(hi_cfg["min_number"]))

    return elem


def _resolve_region_geometry(
    root_geometry: ET.Element,
    region_cfg: Dict,
) -> Tuple[Vector3, Vector3]:
    if "position" in region_cfg and "size" in region_cfg:
        position = tuple(float(v) for v in region_cfg["position"])
        size = tuple(float(v) for v in region_cfg["size"])
        return position, size  # type: ignore[return-value]

    bbox_cfg = region_cfg.get("bbox_from")
    if not bbox_cfg:
        raise ValueError(f"Region '{region_cfg.get('name', '<unnamed>')}' missing position/size or bbox_from")

    include_names = list(bbox_cfg.get("include_names", []))
    include_patterns = list(bbox_cfg.get("include_patterns", []))
    scope_assembly = bbox_cfg.get("scope_assembly")
    matches = _match_items(root_geometry, include_names, include_patterns, scope_assembly)
    lower, upper = _compute_bbox(matches)
    padding = _normalize_padding(bbox_cfg.get("padding", 0.0))
    position = tuple(lower[i] - padding[i] for i in range(3))
    size = tuple((upper[i] - lower[i]) + (2.0 * padding[i]) for i in range(3))
    return position, size  # type: ignore[return-value]


def _target_geometry(root_geometry: ET.Element, region_cfg: Dict) -> Tuple[ET.Element, Vector3]:
    parent_assembly = region_cfg.get("parent_assembly")
    if not parent_assembly:
        return root_geometry, (0.0, 0.0, 0.0)

    assembly_elem = _find_assembly_element(root_geometry, parent_assembly)
    if assembly_elem is None:
        raise ValueError(f"parent_assembly not found: {parent_assembly}")

    geometry_elem = _ensure_geometry_container(assembly_elem)

    # Assembly positions are local; convert global region position to parent-local.
    global_offset = (0.0, 0.0, 0.0)
    for item in _iter_all_geometry_items(root_geometry):
        if item.element is assembly_elem:
            global_offset = item.global_position
            break

    return geometry_elem, global_offset


def add_regions(root: ET.Element, config: Dict) -> ET.Element:
    geometry = _find_root_geometry(root)
    regions = config.get("regions", [])
    grid_constraints = config.get("grid_constraints", [])
    object_constraints = config.get("object_constraints", [])
    if not regions and not grid_constraints and not object_constraints:
        raise ValueError("JSON config must contain 'regions', 'grid_constraints', and/or 'object_constraints'")

    if grid_constraints:
        attributes = _find_or_create_attributes(root)
        grid_constraints_elem = _find_or_create_grid_constraints(attributes)
        for constraint_cfg in grid_constraints:
            _upsert_grid_constraint(grid_constraints_elem, constraint_cfg)

    _apply_object_constraints(geometry, config)

    for region_cfg in regions:
        name = region_cfg.get("name")
        if not name:
            raise ValueError("Each region requires a name")

        global_position, size = _resolve_region_geometry(geometry, region_cfg)
        target_geometry, parent_offset = _target_geometry(geometry, region_cfg)
        local_position = _vector_sub(global_position, parent_offset)
        region_elem = _build_region_element(name, local_position, size, region_cfg)
        target_geometry.append(region_elem)

    return root


def indent_xml(elem: ET.Element, level: int = 0) -> None:
    indent = "\n" + ("    " * level)
    if len(elem):
        if not elem.text or not elem.text.strip():
            elem.text = indent + "    "
        for child in elem:
            indent_xml(child, level + 1)
        if not elem[-1].tail or not elem[-1].tail.strip():
            elem[-1].tail = indent
    if level and (not elem.tail or not elem.tail.strip()):
        elem.tail = indent


def load_json(path: Path) -> Dict:
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def main() -> int:
    parser = argparse.ArgumentParser(description="Add volume regions to FloXML using JSON config")
    parser.add_argument("input", help="Input FloXML file")
    parser.add_argument("--config", required=True, help="Region JSON config")
    parser.add_argument("-o", "--output", help="Output FloXML file")
    args = parser.parse_args()

    input_path = Path(args.input)
    config_path = Path(args.config)
    output_path = Path(args.output) if args.output else input_path.with_name(f"{input_path.stem}_with_regions{input_path.suffix}")

    tree = ET.parse(input_path)
    root = tree.getroot()
    config = load_json(config_path)
    root = add_regions(root, config)
    indent_xml(root)
    tree.write(output_path, encoding="utf-8", xml_declaration=True)

    print(
        f"[OK] Added {len(config.get('regions', []))} region(s), "
        f"upserted {len(config.get('grid_constraints', []))} grid constraint(s), "
        f"applied {len(config.get('object_constraints', []))} object constraint rule(s): {output_path}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
