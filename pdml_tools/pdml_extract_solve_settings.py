#!/usr/bin/env python3
"""
从 PDML / FloXML 文件中提取求解设置（model / solve / grid / solution_domain），
输出为 JSON 格式。

支持:
  - FloXML (.xml / .floxml) — XML 文本格式，直接解析
  - PDML (.pdml) — FloTHERM 二进制格式，先转 FloXML 再提取

用法:
    python pdml_tools/pdml_extract_solve_settings.py model.pdml -o solve.json
    python pdml_tools/pdml_extract_solve_settings.py model.xml -o solve.json
    python pdml_tools/pdml_extract_solve_settings.py model.pdml  # 打印摘要
"""

import argparse
import json
import os
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any, Dict, List, Optional

from pdml_tools.pdml_extract_regions import (
    is_binary_pdml,
    _strip_ns,
    _float_text,
    _text,
)


# ============================================================================
# Helper: bool text parsing
# ============================================================================

def _bool_text(elem: ET.Element, tag: str, default: bool = False) -> Optional[bool]:
    v = _text(elem, tag)
    if v is None:
        return None
    return v.lower() == "true"


def _int_text(elem: ET.Element, tag: str, default: int = 0) -> Optional[int]:
    v = _text(elem, tag)
    if v is None:
        return None
    try:
        return int(float(v))
    except (ValueError, TypeError):
        return None


# ============================================================================
# Model section extractors
# ============================================================================

def extract_modeling(root: ET.Element) -> Optional[Dict]:
    """Extract <model><modeling> section."""
    model = root.find("model")
    if model is None:
        return None
    modeling = model.find("modeling")
    if modeling is None:
        return None

    result: Dict[str, Any] = {}

    for key in ("solution", "radiation", "dimensionality"):
        v = _text(modeling, key)
        if v is not None:
            result[key] = v

    # transient
    v = _bool_text(modeling, "transient")
    if v is not None:
        result["transient"] = v

    # joule_heating (may not exist in all files)
    v = _bool_text(modeling, "joule_heating")
    if v is not None:
        result["joule_heating"] = v

    # store options
    for key in ("store_mass_flux", "store_heat_flux", "store_surface_temp",
                "store_grad_t", "store_bn_sc", "store_power_density",
                "store_mean_radiant_temperature", "compute_capture_index",
                "user_defined_subgroups", "store_lma"):
        v = _bool_text(modeling, key)
        if v is not None:
            result[key] = v

    return result if result else None


def extract_turbulence(root: ET.Element) -> Optional[Dict]:
    """Extract <model><turbulence> section."""
    model = root.find("model")
    if model is None:
        return None
    turb = model.find("turbulence")
    if turb is None:
        return None

    result: Dict[str, Any] = {}
    v = _text(turb, "type")
    if v is not None:
        result["type"] = v
    v = _text(turb, "turbulence_type")
    if v is not None:
        result["turbulence_type"] = v
    return result if result else None


def extract_gravity(root: ET.Element) -> Optional[Dict]:
    """Extract <model><gravity> section."""
    model = root.find("model")
    if model is None:
        return None
    grav = model.find("gravity")
    if grav is None:
        return None

    result: Dict[str, Any] = {}
    v = _text(grav, "type")
    if v is not None:
        result["type"] = v
    v = _text(grav, "normal_direction")
    if v is not None:
        result["normal_direction"] = v
    v = _text(grav, "value_type")
    if v is not None:
        result["value_type"] = v
    v = _float_text(grav, "gravity_value")
    if v != 0.0 or grav.find("gravity_value") is not None:
        result["gravity_value"] = v
    return result if result else None


def extract_global(root: ET.Element) -> Optional[Dict]:
    """Extract <model><global> section."""
    model = root.find("model")
    if model is None:
        return None
    gl = model.find("global")
    if gl is None:
        return None

    result: Dict[str, Any] = {}
    for key in ("datum_pressure", "ambient_temperature", "radiant_temperature",
                "concentration_1", "concentration_2", "concentration_3",
                "concentration_4", "concentration_5"):
        child = gl.find(key)
        if child is not None and child.text:
            try:
                result[key] = float(child.text.strip())
            except ValueError:
                pass
    return result if result else None


def extract_initial_variables(root: ET.Element) -> Optional[Dict]:
    """Extract <model><initial_variables> section."""
    model = root.find("model")
    if model is None:
        return None
    iv = model.find("initial_variables")
    if iv is None:
        return None

    result: Dict[str, Any] = {}
    v = _bool_text(iv, "use_initial_for_all")
    if v is not None:
        result["use_initial_for_all"] = v

    variables: List[Dict] = []
    for child in iv:
        tag = _strip_ns(child.tag)
        if tag in ("use_initial_for_all",):
            continue
        var_entry: Dict[str, str] = {"variable": tag}
        v = _text(child, "type")
        if v is not None:
            var_entry["type"] = v
        v = _text(child, "value")
        if v is not None:
            try:
                var_entry["value"] = float(v)
            except ValueError:
                var_entry["value"] = v
        variables.append(var_entry)

    if variables:
        result["variables"] = variables
    return result if result else None


# ============================================================================
# Solve section extractors
# ============================================================================

def extract_overall_control(root: ET.Element) -> Optional[Dict]:
    """Extract <solve><overall_control> section."""
    solve = root.find("solve")
    if solve is None:
        return None
    oc = solve.find("overall_control")
    if oc is None:
        return None

    result: Dict[str, Any] = {}

    v = _int_text(oc, "outer_iterations")
    if v is not None:
        result["outer_iterations"] = v
    v = _float_text(oc, "fan_relaxation")
    if oc.find("fan_relaxation") is not None:
        result["fan_relaxation"] = v
    v = _float_text(oc, "estimated_free_convection_velocity")
    if oc.find("estimated_free_convection_velocity") is not None:
        result["estimated_free_convection_velocity"] = v
    v = _text(oc, "solver_option")
    if v is not None:
        result["solver_option"] = v

    for key in ("monitor_convergence", "active_plate_conduction",
                "use_double_precision", "multi_grid_damping",
                "network_assembly_block_correction", "freeze_flow",
                "store_error_field"):
        v = _bool_text(oc, key)
        if v is not None:
            result[key] = v

    v = _text(oc, "error_field_variable")
    if v is not None:
        result["error_field_variable"] = v

    # convergence_values
    cv = oc.find("convergence_values")
    if cv is not None:
        cv_dict: Dict[str, Any] = {}
        v = _float_text(cv, "required_accuracy")
        if cv.find("required_accuracy") is not None:
            cv_dict["required_accuracy"] = v
        v = _int_text(cv, "num_iterations")
        if v is not None:
            cv_dict["num_iterations"] = v
        v = _float_text(cv, "residual_threshold")
        if cv.find("residual_threshold") is not None:
            cv_dict["residual_threshold"] = v
        if cv_dict:
            result["convergence_values"] = cv_dict

    # monitor_point_transient_termination_criteria (optional)
    mpttc = oc.find("monitor_point_transient_termination_criteria")
    if mpttc is not None:
        mpt: Dict[str, Any] = {}
        v = _bool_text(mpttc, "use_monitor_point_transient_termination_criteria")
        if v is not None:
            mpt["use_monitor_point_transient_termination_criteria"] = v
        terms: List[Dict] = []
        for t in mpttc.findall("terminating_monitor_point"):
            entry: Dict[str, Any] = {}
            mp_name = _text(t, "monitor_point")
            if mp_name:
                entry["monitor_point"] = mp_name
            temp_v = _text(t, "temperature")
            if temp_v is not None:
                try:
                    entry["temperature"] = float(temp_v)
                except ValueError:
                    entry["temperature"] = temp_v
            if entry:
                terms.append(entry)
        if terms:
            mpt["terminating_monitor_points"] = terms
        if mpt:
            result["monitor_point_transient_termination_criteria"] = mpt

    return result if result else None


def extract_variable_controls(root: ET.Element) -> Optional[List[Dict]]:
    """Extract <solve><variable_controls><variable_control> entries."""
    solve = root.find("solve")
    if solve is None:
        return None
    vc_parent = solve.find("variable_controls")
    if vc_parent is None:
        return None

    results: List[Dict] = []
    for vc in vc_parent.findall("variable_control"):
        entry: Dict[str, Any] = {}
        v = _text(vc, "variable")
        if v is not None:
            entry["variable"] = v
        v = _text(vc, "false_time_step")
        if v is not None:
            entry["false_time_step"] = v
        v = _float_text(vc, "false_time_step_user_value")
        if vc.find("false_time_step_user_value") is not None:
            entry["false_time_step_user_value"] = v
        v = _float_text(vc, "false_time_step_damping_auto_multiplier")
        if vc.find("false_time_step_damping_auto_multiplier") is not None:
            entry["false_time_step_damping_auto_multiplier"] = v
        v = _text(vc, "terminal_residual")
        if v is not None:
            entry["terminal_residual"] = v
        v = _float_text(vc, "terminal_residual_auto_multiplier")
        if vc.find("terminal_residual_auto_multiplier") is not None:
            entry["terminal_residual_auto_multiplier"] = v
        v = _float_text(vc, "terminal_residual_user_value")
        if vc.find("terminal_residual_user_value") is not None:
            entry["terminal_residual_user_value"] = v
        v = _int_text(vc, "inner_iterations")
        if v is not None:
            entry["inner_iterations"] = v
        if entry:
            results.append(entry)

    return results if results else None


def extract_solver_controls(root: ET.Element) -> Optional[List[Dict]]:
    """Extract <solve><solver_controls><solver_control> entries."""
    solve = root.find("solve")
    if solve is None:
        return None
    sc_parent = solve.find("solver_controls")
    if sc_parent is None:
        return None

    results: List[Dict] = []
    for sc in sc_parent.findall("solver_control"):
        entry: Dict[str, Any] = {}
        v = _text(sc, "variable")
        if v is not None:
            entry["variable"] = v
        v = _float_text(sc, "linear_relaxation")
        if sc.find("linear_relaxation") is not None:
            entry["linear_relaxation"] = v
        v = _int_text(sc, "error_compute_frequency")
        if v is not None:
            entry["error_compute_frequency"] = v
        if entry:
            results.append(entry)

    return results if results else None


# ============================================================================
# Transient section extractor
# ============================================================================

def extract_transient(root: ET.Element) -> Optional[Dict]:
    """Extract <model><transient> section."""
    model = root.find("model")
    if model is None:
        return None
    tr = model.find("transient")
    if tr is None:
        return None

    result: Dict[str, Any] = {}

    # overall_transient
    ot = tr.find("overall_transient")
    if ot is not None:
        ot_dict: Dict[str, Any] = {}
        for key in ("start_time", "end_time", "duration", "keypoint_tolerance"):
            child = ot.find(key)
            if child is not None and child.text:
                try:
                    ot_dict[key] = float(child.text.strip())
                except ValueError:
                    pass
        if ot_dict:
            result["overall_transient"] = ot_dict

    # save_times
    st_parent = tr.find("transient_save_times")
    if st_parent is not None:
        save_times: List[float] = []
        for st in st_parent.findall("save_time"):
            if st.text:
                try:
                    save_times.append(float(st.text.strip()))
                except ValueError:
                    pass
        if save_times:
            result["save_times"] = save_times

    # time_patches
    tp_parent = tr.find("time_patches")
    if tp_parent is not None:
        patches: List[Dict] = []
        for tp in tp_parent.findall("time_patch"):
            entry: Dict[str, Any] = {}
            v = _text(tp, "name")
            if v is not None:
                entry["name"] = v
            for key in ("start_time", "end_time", "distribution_index"):
                child = tp.find(key)
                if child is not None and child.text:
                    try:
                        entry[key] = float(child.text.strip())
                    except ValueError:
                        pass
            v = _text(tp, "step_control")
            if v is not None:
                entry["step_control"] = v
            v = _int_text(tp, "minimum_number")
            if v is not None:
                entry["minimum_number"] = v
            v = _text(tp, "step_distribution")
            if v is not None:
                entry["step_distribution"] = v
            if entry:
                patches.append(entry)
        if patches:
            result["time_patches"] = patches

    return result if result else None


# ============================================================================
# Grid section extractor
# ============================================================================

def _extract_grid_axis(elem: ET.Element, axis_tag: str) -> Optional[Dict]:
    """Extract x_grid / y_grid / z_grid sub-element."""
    axis = elem.find(axis_tag)
    if axis is None:
        return None

    result: Dict[str, Any] = {}
    v = _float_text(axis, "min_size")
    if axis.find("min_size") is not None:
        result["min_size"] = v
    v = _text(axis, "grid_type")
    if v is not None:
        result["grid_type"] = v
    v = _float_text(axis, "max_size")
    if axis.find("max_size") is not None:
        result["max_size"] = v
    v = _int_text(axis, "min_number")
    if v is not None:
        result["min_number"] = v
    v = _int_text(axis, "smoothing_value")
    if v is not None:
        result["smoothing_value"] = v
    return result if result else None


def extract_grid(root: ET.Element) -> Optional[Dict]:
    """Extract <grid> section including system_grid and patches."""
    grid = root.find("grid")
    if grid is None:
        return None

    result: Dict[str, Any] = {}

    # system_grid
    sg = grid.find("system_grid")
    if sg is not None:
        sg_dict: Dict[str, Any] = {}
        v = _bool_text(sg, "smoothing")
        if v is not None:
            sg_dict["smoothing"] = v
        v = _text(sg, "smoothing_type")
        if v is not None:
            sg_dict["smoothing_type"] = v
        v = _bool_text(sg, "dynamic_update")
        if v is not None:
            sg_dict["dynamic_update"] = v

        for axis_tag in ("x_grid", "y_grid", "z_grid"):
            axis_data = _extract_grid_axis(sg, axis_tag)
            if axis_data:
                sg_dict[axis_tag] = axis_data

        if sg_dict:
            result["system_grid"] = sg_dict

    # patches
    patches_parent = grid.find("patches")
    if patches_parent is not None:
        patches: List[Dict] = []
        for gp in patches_parent.findall("grid_patch"):
            entry: Dict[str, Any] = {}
            v = _text(gp, "name")
            if v is not None:
                entry["name"] = v
            v = _text(gp, "applies_to")
            if v is not None:
                entry["applies_to"] = v
            for key in ("start_location", "end_location"):
                child = gp.find(key)
                if child is not None and child.text:
                    try:
                        entry[key] = float(child.text.strip())
                    except ValueError:
                        pass
            v = _text(gp, "number_of_cells_control")
            if v is not None:
                entry["number_of_cells_control"] = v
            v = _int_text(gp, "min_number")
            if v is not None:
                entry["min_number"] = v
            v = _text(gp, "cell_distribution")
            if v is not None:
                entry["cell_distribution"] = v
            v = _float_text(gp, "cell_distribution_index")
            if gp.find("cell_distribution_index") is not None:
                entry["cell_distribution_index"] = v
            if entry:
                patches.append(entry)
        if patches:
            result["patches"] = patches

    return result if result else None


# ============================================================================
# Solution domain extractor
# ============================================================================

_BOUNDARY_KEYS = [
    ("x_low", ["x_low_ambient", "x_low_boundary"]),
    ("x_high", ["x_high_ambient", "x_high_boundary"]),
    ("y_low", ["y_low_ambient", "y_low_boundary"]),
    ("y_high", ["y_high_ambient", "y_high_boundary"]),
    ("z_low", ["z_low_ambient", "z_low_boundary"]),
    ("z_high", ["z_high_ambient", "z_high_boundary"]),
]


def extract_solution_domain(root: ET.Element) -> Optional[Dict]:
    """Extract <solution_domain> section."""
    sd = root.find("solution_domain")
    if sd is None:
        return None

    result: Dict[str, Any] = {}

    # position
    pos = sd.find("position")
    if pos is not None:
        result["position"] = [_float_text(pos, "x"), _float_text(pos, "y"), _float_text(pos, "z")]

    # size
    sz = sd.find("size")
    if sz is not None:
        result["size"] = [_float_text(sz, "x"), _float_text(sz, "y"), _float_text(sz, "z")]

    # boundaries - try both tag naming conventions
    for key, tags in _BOUNDARY_KEYS:
        for tag in tags:
            v = _text(sd, tag)
            if v is not None:
                result[key] = v
                break

    v = _text(sd, "fluid")
    if v is not None:
        result["fluid"] = v

    return result if result else None


# ============================================================================
# Combined extraction
# ============================================================================

def extract_all_from_xml(root: ET.Element) -> Dict:
    """从 FloXML ElementTree 提取所有求解设置"""
    result: Dict[str, Any] = {}

    modeling = extract_modeling(root)
    if modeling:
        result["modeling"] = modeling

    turbulence = extract_turbulence(root)
    if turbulence:
        result["turbulence"] = turbulence

    gravity = extract_gravity(root)
    if gravity:
        result["gravity"] = gravity

    gl = extract_global(root)
    if gl:
        result["global"] = gl

    iv = extract_initial_variables(root)
    if iv:
        result["initial_variables"] = iv

    oc = extract_overall_control(root)
    if oc:
        result["overall_control"] = oc

    vc = extract_variable_controls(root)
    if vc:
        result["variable_controls"] = vc

    sc = extract_solver_controls(root)
    if sc:
        result["solver_controls"] = sc

    tr = extract_transient(root)
    if tr:
        result["transient"] = tr

    grid = extract_grid(root)
    if grid:
        result["grid"] = grid

    sd = extract_solution_domain(root)
    if sd:
        result["solution_domain"] = sd

    return result


# ============================================================================
# Entry: auto-detect + PDML conversion
# ============================================================================

def _pdml_to_floxml_root(filepath: str) -> ET.Element:
    """用 pdml_to_floxml_converter 将二进制 PDML 转为内存中的 FloXML ElementTree"""
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if project_root not in sys.path:
        sys.path.insert(0, project_root)
    from pdml_tools.pdml_to_floxml_converter import PDMLBinaryReader, FloXMLBuilder

    reader = PDMLBinaryReader(filepath)
    data = reader.read()
    builder = FloXMLBuilder()
    return builder.build(data)


def extract_all(filepath: str) -> Dict:
    """自动检测格式：PDML 先转 FloXML，然后统一从 XML 提取"""
    if is_binary_pdml(filepath):
        print(f"[INFO] Detected binary PDML, converting to FloXML first...", file=sys.stderr)
        root = _pdml_to_floxml_root(filepath)
    else:
        tree = ET.parse(filepath)
        root = tree.getroot()
    return extract_all_from_xml(root)


# ============================================================================
# Summary output
# ============================================================================

def print_summary(config: Dict) -> None:
    print("=" * 60)
    print("Solve Settings Extract Results")
    print("=" * 60)

    modeling = config.get("modeling", {})
    if modeling:
        print(f"\nModeling:")
        print(f"  solution={modeling.get('solution', '?')}, "
              f"radiation={modeling.get('radiation', '?')}, "
              f"dimensionality={modeling.get('dimensionality', '?')}")
        print(f"  transient={modeling.get('transient', '?')}")

    turb = config.get("turbulence", {})
    if turb:
        print(f"\nTurbulence: type={turb.get('type', '?')}, "
              f"model={turb.get('turbulence_type', 'N/A')}")

    grav = config.get("gravity", {})
    if grav:
        print(f"\nGravity: type={grav.get('type', '?')}, "
              f"dir={grav.get('normal_direction', 'N/A')}, "
              f"value={grav.get('gravity_value', 'N/A')}")

    gl = config.get("global", {})
    if gl:
        print(f"\nGlobal: datum_pressure={gl.get('datum_pressure', '?')}, "
              f"ambient_T={gl.get('ambient_temperature', '?')}")

    iv = config.get("initial_variables", {})
    if iv:
        vars_list = iv.get("variables", [])
        print(f"\nInitial Variables ({len(vars_list)}):")
        for v in vars_list:
            print(f"  - {v.get('variable', '?')}: type={v.get('type', '?')}, "
                  f"value={v.get('value', 'N/A')}")

    oc = config.get("overall_control", {})
    if oc:
        print(f"\nOverall Control:")
        print(f"  outer_iterations={oc.get('outer_iterations', '?')}")
        print(f"  solver_option={oc.get('solver_option', '?')}")
        print(f"  monitor_convergence={oc.get('monitor_convergence', '?')}")
        cv = oc.get("convergence_values", {})
        if cv:
            print(f"  convergence: accuracy={cv.get('required_accuracy', '?')}, "
                  f"iterations={cv.get('num_iterations', '?')}, "
                  f"threshold={cv.get('residual_threshold', '?')}")

    vc_list = config.get("variable_controls", [])
    if vc_list:
        print(f"\nVariable Controls ({len(vc_list)}):")
        for vc in vc_list:
            print(f"  - {vc.get('variable', '?')}: "
                  f"fts={vc.get('false_time_step', '?')} "
                  f"({vc.get('false_time_step_user_value', '?')}), "
                  f"inner_iter={vc.get('inner_iterations', '?')}")

    sc_list = config.get("solver_controls", [])
    if sc_list:
        print(f"\nSolver Controls ({len(sc_list)}):")
        for sc in sc_list:
            print(f"  - {sc.get('variable', '?')}: "
                  f"relaxation={sc.get('linear_relaxation', '?')}, "
                  f"error_freq={sc.get('error_compute_frequency', '?')}")

    tr = config.get("transient", {})
    if tr:
        ot = tr.get("overall_transient", {})
        print(f"\nTransient:")
        if ot:
            print(f"  duration: {ot.get('start_time', 0)} -> {ot.get('end_time', '?')}")
        patches = tr.get("time_patches", [])
        if patches:
            print(f"  time_patches ({len(patches)}):")
            for tp in patches:
                print(f"    - {tp.get('name', '?')}: "
                      f"{tp.get('start_time', '?')} -> {tp.get('end_time', '?')}, "
                      f"control={tp.get('step_control', '?')}, "
                      f"min={tp.get('minimum_number', '?')}")

    grid = config.get("grid", {})
    if grid:
        sg = grid.get("system_grid", {})
        if sg:
            print(f"\nGrid:")
            print(f"  smoothing={sg.get('smoothing', '?')}, "
                  f"type={sg.get('smoothing_type', '?')}")
            for axis in ("x_grid", "y_grid", "z_grid"):
                ax = sg.get(axis)
                if ax:
                    print(f"  {axis}: min_size={ax.get('min_size', '?')}, "
                          f"grid_type={ax.get('grid_type', '?')}, "
                          f"max_size={ax.get('max_size', 'N/A')}")
        patches = grid.get("patches", [])
        if patches:
            print(f"  grid_patches ({len(patches)}):")
            for p in patches:
                print(f"    - {p.get('name', '?')}: {p.get('applies_to', '?')} "
                      f"[{p.get('start_location', '?')} - {p.get('end_location', '?')}]")

    sd = config.get("solution_domain", {})
    if sd:
        pos = sd.get("position", [0, 0, 0])
        sz = sd.get("size", [0, 0, 0])
        print(f"\nSolution Domain:")
        print(f"  position={pos}")
        print(f"  size={sz}")
        for key in ("x_low", "x_high", "y_low", "y_high", "z_low", "z_high"):
            v = sd.get(key)
            if v:
                print(f"  {key}: {v}")
        print(f"  fluid={sd.get('fluid', '?')}")

    print("\n" + "=" * 60)


# ============================================================================
# CLI
# ============================================================================

def main() -> int:
    parser = argparse.ArgumentParser(
        description="Extract solve settings from PDML/FloXML to JSON",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python pdml_tools/pdml_extract_solve_settings.py model.pdml -o solve.json
  python pdml_tools/pdml_extract_solve_settings.py model.xml -o solve.json
  python pdml_tools/pdml_extract_solve_settings.py model.pdml --summary
        """,
    )
    parser.add_argument("input", help="Input PDML or FloXML file")
    parser.add_argument("-o", "--output", help="Output JSON file path")
    parser.add_argument("--summary", action="store_true", help="Print summary")

    args = parser.parse_args()

    input_path = Path(args.input)
    if not input_path.exists():
        print(f"[ERROR] File not found: {input_path}", file=sys.stderr)
        return 1

    try:
        config = extract_all(str(input_path))
    except ET.ParseError as e:
        print(f"[ERROR] XML parse failed: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"[ERROR] {type(e).__name__}: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1

    if args.summary or not args.output:
        print_summary(config)

    if args.output:
        output_path = Path(args.output)
        with output_path.open("w", encoding="utf-8") as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        print(f"[OK] Output: {output_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
