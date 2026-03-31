#!/usr/bin/env python3
"""
Unified JSON config injector for FloXML.

Reads a single JSON config file and injects missing FloXML attributes
into an existing FloXML element tree.  This includes:

- Attribute definitions: surfaces, surface_exchanges, radiations,
  resistances, fans, thermals, transients, advanced materials
- Attribute assignments: apply surface / radiation / thermal / etc.
  references onto geometry elements (cuboid, assembly, source, …)
- Volume regions / grid constraints: delegates to
  floxml_add_volume_regions when those sections are present

Usage (from the converter or standalone)::

    from floxml_tools.config_injector import ConfigInjector

    injector = ConfigInjector("my_config.json")
    injector.inject(root)          # modifies root in-place
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional
import xml.etree.ElementTree as ET

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _set_text(parent: ET.Element, tag: str, text: str) -> ET.Element:
    """Find-or-create a child element and set its text."""
    child = parent.find(tag)
    if child is None:
        child = ET.SubElement(parent, tag)
    child.text = text
    return child


def _find_or_create(root: ET.Element, tag: str) -> ET.Element:
    """Find-or-create a direct child of *root*."""
    child = root.find(tag)
    if child is None:
        child = ET.SubElement(root, tag)
    return child


def _find_or_create_attributes(root: ET.Element) -> ET.Element:
    """Ensure <attributes> exists under the <xml_case> root."""
    attrs = root.find("attributes")
    if attrs is not None:
        return attrs

    # Insert before <geometry> or at end
    insert_at = len(list(root))
    for idx, child in enumerate(list(root)):
        if child.tag in {"geometry", "solution_domain"}:
            insert_at = idx
            break
    attrs = ET.Element("attributes")
    root.insert(insert_at, attrs)
    return attrs


def _find_or_create_section(attributes: ET.Element, section_tag: str) -> ET.Element:
    """Find-or-create a subsection like <surfaces> inside <attributes>."""
    sec = attributes.find(section_tag)
    if sec is None:
        sec = ET.SubElement(attributes, section_tag)
    return sec


def _val(cfg: Dict, key: str, default: Any = None) -> Any:
    return cfg.get(key, default)


# ---------------------------------------------------------------------------
# Generic dict → XML builder
# ---------------------------------------------------------------------------

def _dict_to_xml(parent: ET.Element, data: Dict) -> None:
    """Recursively build XML child elements from a dict.

    Convention:
      - str / int / float / None → element with text
      - bool → element with "true"/"false"
      - dict → nested element, recurse
      - list → multiple sibling elements with the same tag, each recursed
    """
    for key, value in data.items():
        if value is None:
            # <tag /> — empty element
            ET.SubElement(parent, key)
        elif isinstance(value, bool):
            el = ET.SubElement(parent, key)
            el.text = str(value).lower()
        elif isinstance(value, dict):
            el = ET.SubElement(parent, key)
            _dict_to_xml(el, value)
        elif isinstance(value, list):
            for item in value:
                el = ET.SubElement(parent, key)
                if isinstance(item, dict):
                    _dict_to_xml(el, item)
                elif isinstance(item, bool):
                    el.text = str(item).lower()
                elif item is not None:
                    el.text = str(item)
        else:
            el = ET.SubElement(parent, key)
            el.text = str(value)


def _replace_section(root: ET.Element, tag: str, data: Dict) -> None:
    """Replace (or insert) a top-level <tag> section built from *data*."""
    old = root.find(tag)
    if old is not None:
        root.remove(old)
    # Insert before <geometry> if possible, to keep FloXML ordering
    insert_at = len(list(root))
    for idx, child in enumerate(list(root)):
        if child.tag == "geometry":
            insert_at = idx
            break
    new = ET.Element(tag)
    _dict_to_xml(new, data)
    root.insert(insert_at, new)


# ---------------------------------------------------------------------------
# Attribute builders
# Each builds the appropriate *_att element and appends it to its section.
# ---------------------------------------------------------------------------

def _build_surface_att(section: ET.Element, cfg: Dict) -> None:
    el = ET.SubElement(section, "surface_att")
    _set_text(el, "name", str(cfg["name"]))
    if "emissivity" in cfg:
        _set_text(el, "emissivity", str(cfg["emissivity"]))
    if "roughness" in cfg:
        _set_text(el, "roughness", str(cfg["roughness"]))
    if "rsurf_fluid" in cfg:
        _set_text(el, "rsurf_fluid", str(cfg["rsurf_fluid"]))
    if "rsurf_solid" in cfg:
        _set_text(el, "rsurf_solid", str(cfg["rsurf_solid"]))
    if "area_factor" in cfg:
        _set_text(el, "area_factor", str(cfg["area_factor"]))
    if "solar_reflectivity" in cfg:
        _set_text(el, "solar_reflectivity", str(cfg["solar_reflectivity"]))


def _build_surface_exchange_att(section: ET.Element, cfg: Dict) -> None:
    el = ET.SubElement(section, "surface_exchange_att")
    _set_text(el, "name", str(cfg["name"]))
    if "heat_transfer_method" in cfg:
        _set_text(el, "heat_transfer_method", str(cfg["heat_transfer_method"]))
    if "extent_of_heat_transfer" in cfg:
        _set_text(el, "extent_of_heat_transfer", str(cfg["extent_of_heat_transfer"]))
    if "heat_transfer_coefficient" in cfg:
        _set_text(el, "heat_transfer_coefficient", str(cfg["heat_transfer_coefficient"]))
    if "specified_constant_value" in cfg:
        _set_text(el, "specified_constant_value", str(cfg["specified_constant_value"]))
    if "reference_temperature" in cfg:
        _set_text(el, "reference_temperature", str(cfg["reference_temperature"]))
    if "reference_temperature_value" in cfg:
        _set_text(el, "reference_temperature_value", str(cfg["reference_temperature_value"]))
    if "wetted_area_volume_transfer" in cfg:
        _set_text(el, "wetted_area_volume_transfer", str(cfg["wetted_area_volume_transfer"]))
    # Profile (heat sink curve)
    if "profile" in cfg:
        prof = ET.SubElement(el, "profile")
        for pt in cfg["profile"]:
            pt_el = ET.SubElement(prof, "heat_sink_curve_point")
            _set_text(pt_el, "speed", str(pt["speed"]))
            _set_text(pt_el, "thermal_resistance", str(pt["thermal_resistance"]))


def _build_radiation_att(section: ET.Element, cfg: Dict) -> None:
    el = ET.SubElement(section, "radiation_att")
    _set_text(el, "name", str(cfg["name"]))
    if "surface" in cfg:
        _set_text(el, "surface", str(cfg["surface"]))
    if "min_area" in cfg:
        _set_text(el, "min_area", str(cfg["min_area"]))
    if "subdivided_surface_tolerance" in cfg:
        _set_text(el, "subdivided_surface_tolerance", str(cfg["subdivided_surface_tolerance"]))


def _build_resistance_direction(parent: ET.Element, tag: str, cfg: Dict) -> None:
    """Build a resistance_x/y/z sub-element."""
    el = ET.SubElement(parent, tag)
    for key in ("a_coefficient", "b_coefficient", "free_area_ratio", "length_scale", "index"):
        if key in cfg:
            _set_text(el, key, str(cfg[key]))


def _build_resistance_att(section: ET.Element, cfg: Dict) -> None:
    el = ET.SubElement(section, "resistance_att")
    _set_text(el, "name", str(cfg["name"]))
    if "resistance_type" in cfg:
        _set_text(el, "resistance_type", str(cfg["resistance_type"]))
    if "loss_coefficients_based_on" in cfg:
        _set_text(el, "loss_coefficients_based_on", str(cfg["loss_coefficients_based_on"]))
    if "formula_type" in cfg:
        _set_text(el, "formula_type", str(cfg["formula_type"]))
    for axis in ("resistance_x", "resistance_y", "resistance_z"):
        if axis in cfg:
            _build_resistance_direction(el, axis, cfg[axis])
    if "transparent_to_radiation" in cfg:
        _set_text(el, "transparent_to_radiation", str(cfg["transparent_to_radiation"]).lower())


def _build_fan_att(section: ET.Element, cfg: Dict) -> None:
    el = ET.SubElement(section, "fan_att")
    _set_text(el, "name", str(cfg["name"]))
    if "flow_type" in cfg:
        _set_text(el, "flow_type", str(cfg["flow_type"]))
    if "flow_spec" in cfg:
        _set_text(el, "flow_spec", str(cfg["flow_spec"]))
    if "open_volume_flow_rate" in cfg:
        _set_text(el, "open_volume_flow_rate", str(cfg["open_volume_flow_rate"]))
    if "stagnation_pressure" in cfg:
        _set_text(el, "stagnation_pressure", str(cfg["stagnation_pressure"]))
    if "flow_rate" in cfg:
        _set_text(el, "flow_rate", str(cfg["flow_rate"]))
    if "flow_direction" in cfg:
        _set_text(el, "flow_direction", str(cfg["flow_direction"]))
    if "swirl_model" in cfg:
        _set_text(el, "swirl_model", str(cfg["swirl_model"]))
    if "swirl_direction" in cfg:
        _set_text(el, "swirl_direction", str(cfg["swirl_direction"]))
    if "swirl_speed" in cfg:
        _set_text(el, "swirl_speed", str(cfg["swirl_speed"]))
    if "swirl_angle" in cfg:
        _set_text(el, "swirl_angle", str(cfg["swirl_angle"]))
    if "derating_factor" in cfg:
        _set_text(el, "derating_factor", str(cfg["derating_factor"]))
    if "free_area_ratio" in cfg:
        _set_text(el, "free_area_ratio", str(cfg["free_area_ratio"]))
    if "fan_power" in cfg:
        _set_text(el, "fan_power", str(cfg["fan_power"]))
    if "fan_curve_points" in cfg:
        pts = ET.SubElement(el, "fan_curve_points")
        for pt in cfg["fan_curve_points"]:
            pt_el = ET.SubElement(pts, "fan_curve_point")
            _set_text(pt_el, "volume_flow", str(pt["volume_flow"]))
            _set_text(pt_el, "pressure", str(pt["pressure"]))


def _build_thermal_att(section: ET.Element, cfg: Dict) -> None:
    el = ET.SubElement(section, "thermal_att")
    _set_text(el, "name", str(cfg["name"]))
    if "thermal_model" in cfg:
        _set_text(el, "thermal_model", str(cfg["thermal_model"]))
    if "power" in cfg:
        _set_text(el, "power", str(cfg["power"]))
    if "fixed_temperature" in cfg:
        _set_text(el, "fixed_temperature", str(cfg["fixed_temperature"]))
    if "transient" in cfg:
        _set_text(el, "transient", str(cfg["transient"]))


def _build_transient_att(section: ET.Element, cfg: Dict) -> None:
    el = ET.SubElement(section, "transient_att")
    _set_text(el, "name", str(cfg["name"]))
    if "transient_type" in cfg:
        _set_text(el, "transient_type", str(cfg["transient_type"]))
    if "overlapping_functions" in cfg:
        _set_text(el, "overlapping_functions", str(cfg["overlapping_functions"]))
    if "periodic" in cfg:
        _set_text(el, "periodic", str(cfg["periodic"]).lower())
    if "trans_curve_points" in cfg:
        pts = ET.SubElement(el, "trans_curve_points")
        for pt in cfg["trans_curve_points"]:
            pt_el = ET.SubElement(pts, "trans_curve_point")
            _set_text(pt_el, "time", str(pt["time"]))
            _set_text(pt_el, "coef", str(pt["coef"]))
    if "sub_functions" in cfg:
        subs = ET.SubElement(el, "sub_functions")
        for sf in cfg["sub_functions"]:
            sf_el = ET.SubElement(subs, "sub_fuction")  # FloTHERM's typo
            _set_text(sf_el, "name", str(sf.get("name", "")))
            _set_text(sf_el, "start_time", str(sf.get("start_time", 0)))
            _set_text(sf_el, "finish_time", str(sf.get("finish_time", 0)))
            type_el = ET.SubElement(sf_el, "type")
            for fn_type in ("linear", "pulse", "power_law", "exponential", "sinusoidal", "gaussian"):
                if fn_type in sf:
                    fn_el = ET.SubElement(type_el, fn_type)
                    fn_cfg = sf[fn_type]
                    for k, v in fn_cfg.items():
                        _set_text(fn_el, k, str(v))
                    break


def _build_advanced_material(section: ET.Element, cfg: Dict) -> None:
    """Build orthotropic / biaxial / temperature_dependent material."""
    mat_type = cfg.get("type", "orthotropic")
    if mat_type == "orthotropic":
        el = ET.SubElement(section, "orthotropic_material_att")
        _set_text(el, "name", str(cfg["name"]))
        if "x_conductivity" in cfg:
            _set_text(el, "x_conductivity", str(cfg["x_conductivity"]))
        if "y_conductivity" in cfg:
            _set_text(el, "y_conductivity", str(cfg["y_conductivity"]))
        if "z_conductivity" in cfg:
            _set_text(el, "z_conductivity", str(cfg["z_conductivity"]))
    elif mat_type == "biaxial":
        el = ET.SubElement(section, "biaxial_material_att")
        _set_text(el, "name", str(cfg["name"]))
        if "in_plane_conductivity" in cfg:
            _set_text(el, "in_plane_conductivity", str(cfg["in_plane_conductivity"]))
        if "normal_conductivity" in cfg:
            _set_text(el, "normal_conductivity", str(cfg["normal_conductivity"]))
    else:
        return  # isotropic handled by existing converter
    if "density" in cfg:
        _set_text(el, "density", str(cfg["density"]))
    if "specific_heat" in cfg:
        _set_text(el, "specific_heat", str(cfg["specific_heat"]))


# ---------------------------------------------------------------------------
# Geometry matching (reuse from floxml_add_volume_regions)
# ---------------------------------------------------------------------------

def _iter_all_geometry_items(geometry_elem: ET.Element):
    """Yield (element, name, tag) for every geometry item recursively."""
    import fnmatch
    from typing import Iterable, Tuple
    for child in list(geometry_elem):
        tag = child.tag
        name = (child.findtext("name") or "").strip()
        yield child, name, tag
        child_geo = child.find("geometry")
        if child_geo is not None:
            yield from _iter_all_geometry_items(child_geo)


def _match_geometry(root_geometry: ET.Element,
                    target_names: List[str],
                    target_patterns: List[str],
                    target_tags: List[str],
                    scope_assembly: Optional[str] = None) -> List[ET.Element]:
    """Match geometry items by name, pattern, and tag. Returns matched elements."""
    import fnmatch
    matches = []
    for elem, name, tag in _iter_all_geometry_items(root_geometry):
        if not name:
            continue
        if target_tags and tag not in target_tags:
            continue
        matched = False
        if target_names and name in target_names:
            matched = True
        if not matched and target_patterns:
            for pat in target_patterns:
                if fnmatch.fnmatch(name, pat):
                    matched = True
                    break
        if matched:
            matches.append(elem)
    return matches


# ---------------------------------------------------------------------------
# Main injector
# ---------------------------------------------------------------------------

# Mapping: JSON key -> (section tag, builder function)
_ATTRIBUTE_BUILDERS = {
    "surfaces":            ("surfaces",            _build_surface_att),
    "surface_exchanges":   ("surface_exchanges",   _build_surface_exchange_att),
    "radiations":          ("radiations",          _build_radiation_att),
    "resistances":         ("resistances",         _build_resistance_att),
    "fans":                ("fans",                _build_fan_att),
    "thermals":            ("thermals",            _build_thermal_att),
    "transients":          ("transients",          _build_transient_att),
}


class ConfigInjector:
    """Inject missing FloXML attributes from a unified JSON config."""

    def __init__(self, config_path: str):
        with open(config_path, "r", encoding="utf-8") as f:
            self._cfg: Dict = json.load(f)
        print(f"[INFO] 已加载配置: {config_path}")

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def inject(self, root: ET.Element) -> None:
        """Main entry — modify *root* in-place."""
        # 0. Override top-level sections that the converter auto-generated
        for section_tag in ("model", "solve"):
            section_cfg = self._cfg.get(section_tag)
            if section_cfg:
                _replace_section(root, section_tag, section_cfg)
                print(f"[OK] 已覆盖 <{section_tag}> (来自 JSON 配置)")

        # 0b. Override / add fluid in attributes
        fluid_cfg = self._cfg.get("fluid")
        if fluid_cfg:
            self._inject_fluid(root, fluid_cfg)

        # 0c. Override / add ambient in attributes
        ambient_cfg = self._cfg.get("ambient")
        if ambient_cfg:
            self._inject_ambient(root, ambient_cfg)

        # 1. Inject attribute definitions
        attrs_cfg = self._cfg.get("attributes", {})
        for key, (section_tag, builder) in _ATTRIBUTE_BUILDERS.items():
            items = attrs_cfg.get(key)
            if items:
                self._inject_attribute_section(root, section_tag, builder, items)

        # 2. Advanced materials
        materials = attrs_cfg.get("materials")
        if materials:
            advanced = [m for m in materials if m.get("type", "isotropic") != "isotropic"]
            if advanced:
                attributes = _find_or_create_attributes(root)
                section = _find_or_create_section(attributes, "materials")
                for m in advanced:
                    _build_advanced_material(section, m)
                    print(f"[OK] 已注入材质: {m['name']} ({m.get('type')})")

        # 3. Geometry assignments
        geo_cfg = self._cfg.get("geometry", {})
        assignments = geo_cfg.get("assignments", [])
        if assignments:
            self._inject_geometry_assignments(root, assignments)

        # 4. Volume regions / grid constraints / object constraints
        #    Delegate to floxml_add_volume_regions if any of these keys exist
        regions_cfg = {}
        for key in ("grid_constraints", "object_constraints", "regions"):
            if key in self._cfg:
                regions_cfg[key] = self._cfg[key]
        if regions_cfg:
            self._inject_volume_regions(root, regions_cfg)

    # ------------------------------------------------------------------
    # Fluid / Ambient override
    # ------------------------------------------------------------------

    def _inject_fluid(self, root: ET.Element, fluid_cfg: Dict) -> None:
        """Replace (or add) the default fluid in <attributes><fluids>."""
        fluid_name = fluid_cfg.get("name", "Air")
        attributes = _find_or_create_attributes(root)
        fluids = _find_or_create_section(attributes, "fluids")

        # Remove existing fluid with same name
        for old in list(fluids):
            name_el = old.find("name")
            if name_el is not None and name_el.text == fluid_name:
                fluids.remove(old)
                break

        el = ET.SubElement(fluids, "fluid_att")
        _dict_to_xml(el, fluid_cfg)
        print(f"[OK] 已覆盖 <fluid>: {fluid_name}")

    def _inject_ambient(self, root: ET.Element, ambient_cfg: Dict) -> None:
        """Replace (or add) the default ambient in <attributes><ambients>."""
        ambient_name = ambient_cfg.get("name", "Ambient")
        attributes = _find_or_create_attributes(root)
        ambients = _find_or_create_section(attributes, "ambients")

        # Remove existing ambient with same name
        for old in list(ambients):
            name_el = old.find("name")
            if name_el is not None and name_el.text == ambient_name:
                ambients.remove(old)
                break

        el = ET.SubElement(ambients, "ambient_att")
        _dict_to_xml(el, ambient_cfg)
        print(f"[OK] 已覆盖 <ambient>: {ambient_name}")

    # ------------------------------------------------------------------
    # Attribute section injector
    # ------------------------------------------------------------------

    def _inject_attribute_section(self, root: ET.Element,
                                   section_tag: str,
                                   builder,
                                   items: List[Dict]) -> None:
        attributes = _find_or_create_attributes(root)
        section = _find_or_create_section(attributes, section_tag)
        for item in items:
            builder(section, item)
            print(f"[OK] 已注入 {section_tag}: {item.get('name', '?')}")

    # ------------------------------------------------------------------
    # Geometry assignments
    # ------------------------------------------------------------------

    def _inject_geometry_assignments(self, root: ET.Element,
                                      assignments: List[Dict]) -> None:
        root_geo = root.find("geometry")
        if root_geo is None:
            print("[WARN] FloXML 中未找到 <geometry>，跳过属性分配")
            return

        total = 0
        for rule in assignments:
            names = rule.get("target_names", [])
            patterns = rule.get("target_patterns", [])
            tags = rule.get("target_tags", [])
            scope = rule.get("scope_assembly")
            props = rule.get("properties", {})

            matched = _match_geometry(root_geo, names, patterns, tags, scope)
            for elem in matched:
                for prop_tag, prop_val in props.items():
                    _set_text(elem, prop_tag, str(prop_val))
                total += 1

            rule_desc = ", ".join(
                filter(None, [
                    f"names={names}" if names else "",
                    f"patterns={patterns}" if patterns else "",
                    f"tags={tags}" if tags else "",
                ])
            )
            print(f"[OK] 已分配属性到 {len(matched)} 个元素 ({rule_desc})")

        print(f"[INFO] 共处理 {total} 次属性分配")

    # ------------------------------------------------------------------
    # Volume regions (delegate)
    # ------------------------------------------------------------------

    def _inject_volume_regions(self, root: ET.Element, cfg: Dict) -> None:
        """Delegate to floxml_add_volume_regions.add_regions()."""
        try:
            from .floxml_add_volume_regions import add_regions
            add_regions(root, cfg)
        except ImportError:
            print("[WARN] 无法导入 floxml_add_volume_regions，跳过 volume regions 注入")
        except Exception as e:
            print(f"[WARN] volume regions 注入失败: {e}")
