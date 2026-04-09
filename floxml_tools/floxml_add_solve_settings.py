#!/usr/bin/env python3
"""
Add/update FloTHERM solve settings (<solve>) and transient settings (<transient>)
in an existing FloXML project using JSON or Excel config.

Supported sections:

  Solve settings (<solve>):
  1. overall_control  – outer iterations, solver option, convergence, booleans
  2. variable_controls – per-variable (x/y/z_velocity, temperature) solver tuning
  3. solver_controls   – per-variable linear solver settings (pressure, temperature, …)

  Transient settings (<model>/<transient>):
  4. overall_transient – start_time, end_time, duration, keypoint_tolerance
  5. time_patches      – named time intervals with step control and distribution
  6. save_times        – time points at which to save solution snapshots

Usage:
  python -m floxml_tools.floxml_add_solve_settings model.xml --config solve.json -o out.xml
  python -m floxml_tools.floxml_add_solve_settings model.xml --config solve.xlsx -o out.xml
  python -m floxml_tools.floxml_add_solve_settings --create-template template.xlsx
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Dict, List, Optional
import xml.etree.ElementTree as ET


# ============================================================================
# XML helpers (same pattern as floxml_add_volume_regions.py)
# ============================================================================

def _set_text(parent: ET.Element, tag: str, text: str) -> ET.Element:
    child = parent.find(tag)
    if child is None:
        child = ET.SubElement(parent, tag)
    child.text = text
    return child


def _find_or_create(parent: ET.Element, tag: str) -> ET.Element:
    child = parent.find(tag)
    if child is None:
        child = ET.SubElement(parent, tag)
    return child


def _find_or_create_solve(root: ET.Element) -> ET.Element:
    """Find existing <solve> or create it (inserted before <grid> if possible)."""
    solve = root.find("solve")
    if solve is not None:
        return solve

    solve = ET.Element("solve")
    # Insert before <grid> or <solution_domain> for tidy ordering
    insert_before = None
    for idx, child in enumerate(list(root)):
        if child.tag in ("grid", "solution_domain"):
            insert_before = idx
            break
    if insert_before is not None:
        root.insert(insert_before, solve)
    else:
        root.append(solve)
    return solve


# ============================================================================
# Section builders
# ============================================================================

BOOL_FIELDS = (
    "monitor_convergence",
    "active_plate_conduction",
    "use_double_precision",
    "network_assembly_block_correction",
    "freeze_flow",
    "store_error_field",
)

INT_FIELDS = (
    "outer_iterations",
)

FLOAT_FIELDS = (
    "fan_relaxation",
    "estimated_free_convection_velocity",
)

STRING_FIELDS = (
    "solver_option",
    "error_field_variable",
)

CONVERGENCE_FIELDS = {
    "required_accuracy": float,
    "num_iterations": int,
    "residual_threshold": int,
}


def _format_value(value, python_type):
    """Convert a config value to the correct type and return its XML text form."""
    if python_type is bool:
        if isinstance(value, bool):
            return "true" if value else "false"
        s = str(value).strip().lower()
        return "true" if s in ("true", "1", "yes") else "false"
    if python_type is int:
        return str(int(float(value)))
    if python_type is float:
        return str(float(value))
    return str(value)


def _apply_overall_control(solve: ET.Element, cfg: Dict) -> None:
    """Create/update <overall_control> inside <solve>."""
    oc = _find_or_create(solve, "overall_control")

    # Simple scalar fields
    for field in BOOL_FIELDS:
        if field in cfg:
            _set_text(oc, field, _format_value(cfg[field], bool))

    for field in INT_FIELDS:
        if field in cfg:
            _set_text(oc, field, _format_value(cfg[field], int))

    for field in FLOAT_FIELDS:
        if field in cfg:
            _set_text(oc, field, _format_value(cfg[field], float))

    for field in STRING_FIELDS:
        if field in cfg:
            _set_text(oc, field, _format_value(cfg[field], str))

    # convergence_values sub-element
    cv_cfg = cfg.get("convergence_values")
    if cv_cfg and isinstance(cv_cfg, dict):
        cv = _find_or_create(oc, "convergence_values")
        for fname, ftype in CONVERGENCE_FIELDS.items():
            if fname in cv_cfg:
                _set_text(cv, fname, _format_value(cv_cfg[fname], ftype))


def _apply_variable_controls(solve: ET.Element, controls: List[Dict]) -> None:
    """Create/update <variable_controls> with multiple <variable_control> entries."""
    vc_parent = _find_or_create(solve, "variable_controls")

    for ctrl_cfg in controls:
        variable = ctrl_cfg.get("variable")
        if not variable:
            continue

        # Find existing entry for this variable, or create new
        entry = None
        for child in vc_parent.findall("variable_control"):
            v_elem = child.find("variable")
            if v_elem is not None and (v_elem.text or "").strip() == variable:
                entry = child
                break
        if entry is None:
            entry = ET.SubElement(vc_parent, "variable_control")

        _set_text(entry, "variable", variable)

        for field, ftype in (
            ("false_time_step", str),
            ("false_time_step_user_value", float),
            ("terminal_residual", str),
            ("terminal_residual_auto_multiplier", int),
            ("inner_iterations", int),
        ):
            if field in ctrl_cfg:
                _set_text(entry, field, _format_value(ctrl_cfg[field], ftype))


def _apply_solver_controls(solve: ET.Element, controls: List[Dict]) -> None:
    """Create/update <solver_controls> with multiple <solver_control> entries."""
    sc_parent = _find_or_create(solve, "solver_controls")

    for ctrl_cfg in controls:
        variable = ctrl_cfg.get("variable")
        if not variable:
            continue

        # Find existing entry for this variable, or create new
        entry = None
        for child in sc_parent.findall("solver_control"):
            v_elem = child.find("variable")
            if v_elem is not None and (v_elem.text or "").strip() == variable:
                entry = child
                break
        if entry is None:
            entry = ET.SubElement(sc_parent, "solver_control")

        _set_text(entry, "variable", variable)

        for field, ftype in (
            ("linear_relaxation", float),
            ("error_compute_frequency", int),
        ):
            if field in ctrl_cfg:
                _set_text(entry, field, _format_value(ctrl_cfg[field], ftype))


# ============================================================================
# Transient settings (<model>/<transient>)
# ============================================================================

OVERALL_TRANSIENT_FIELDS = {
    "start_time": float,
    "end_time": float,
    "duration": float,
    "keypoint_tolerance": float,
}

TIME_PATCH_FIELDS = {
    "start_time": float,
    "end_time": float,
    "step_control": str,
    "additional_steps": int,
    "minimum_number": int,
    "maximum_size": float,
    "step_distribution": str,
    "distribution_index": float,
}


def _find_or_create_model(root: ET.Element) -> ET.Element:
    """Find or create <model> element."""
    model = root.find("model")
    if model is None:
        model = ET.SubElement(root, "model")
    return model


def _find_or_create_modeling(model: ET.Element) -> ET.Element:
    """Find or create <modeling> inside <model>."""
    modeling = model.find("modeling")
    if modeling is None:
        modeling = ET.SubElement(model, "modeling")
    return modeling


def _apply_transient_toggle(model: ET.Element, enabled: bool) -> None:
    """Set <modeling>/<transient> true/false."""
    modeling = _find_or_create_modeling(model)
    _set_text(modeling, "transient", "true" if enabled else "false")


def _apply_overall_transient(model: ET.Element, cfg: Dict) -> None:
    """Create/update <model>/<transient>/<overall_transient>."""
    transient = _find_or_create(model, "transient")
    ot = _find_or_create(transient, "overall_transient")

    for fname, ftype in OVERALL_TRANSIENT_FIELDS.items():
        if fname in cfg:
            _set_text(ot, fname, _format_value(cfg[fname], ftype))


def _apply_save_times(model: ET.Element, times: List[float]) -> None:
    """Create/update <model>/<transient>/<transient_save_times>."""
    transient = _find_or_create(model, "transient")
    st_parent = _find_or_create(transient, "transient_save_times")

    # Remove existing save_time entries and re-create
    for old in st_parent.findall("save_time"):
        st_parent.remove(old)

    for t in times:
        st = ET.SubElement(st_parent, "save_time")
        st.text = _format_value(t, float)


def _apply_time_patches(model: ET.Element, patches: List[Dict]) -> None:
    """Create/update <model>/<transient>/<time_patches>."""
    transient = _find_or_create(model, "transient")
    tp_parent = _find_or_create(transient, "time_patches")

    for patch_cfg in patches:
        name = patch_cfg.get("name")
        if not name:
            continue

        # Find existing time_patch by name, or create new
        entry = None
        for child in tp_parent.findall("time_patch"):
            n = child.find("name")
            if n is not None and (n.text or "").strip() == name:
                entry = child
                break
        if entry is None:
            entry = ET.SubElement(tp_parent, "time_patch")

        _set_text(entry, "name", name)

        for fname, ftype in TIME_PATCH_FIELDS.items():
            if fname in patch_cfg:
                _set_text(entry, fname, _format_value(patch_cfg[fname], ftype))


def _apply_transient_settings(root: ET.Element, config: Dict) -> None:
    """Apply all transient config sections."""
    transient_cfg = config.get("transient")
    if not transient_cfg:
        return

    model = _find_or_create_model(root)

    # Enable transient in <modeling>
    _apply_transient_toggle(model, True)

    # overall_transient
    if "overall_transient" in transient_cfg:
        _apply_overall_transient(model, transient_cfg["overall_transient"])

    # save_times
    if "save_times" in transient_cfg:
        _apply_save_times(model, transient_cfg["save_times"])

    # time_patches
    if "time_patches" in transient_cfg:
        _apply_time_patches(model, transient_cfg["time_patches"])


# ============================================================================
# Main entry
# ============================================================================

def apply_solve_settings(root: ET.Element, config: Dict) -> ET.Element:
    """Main entry: apply all solve and transient config sections to a FloXML tree."""
    solve = _find_or_create_solve(root)

    if "overall_control" in config:
        _apply_overall_control(solve, config["overall_control"])

    if "variable_controls" in config:
        _apply_variable_controls(solve, config["variable_controls"])

    if "solver_controls" in config:
        _apply_solver_controls(solve, config["solver_controls"])

    if "transient" in config:
        _apply_transient_settings(root, config)

    return root


# ============================================================================
# JSON config loader
# ============================================================================

def load_json(path: Path) -> Dict:
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


# ============================================================================
# Excel config loader
# ============================================================================

def _parse_bool(value):
    if value is None:
        return None
    if isinstance(value, bool):
        return value
    s = str(value).strip().lower()
    if s in ("true", "1", "yes"):
        return True
    if s in ("false", "0", "no", ""):
        return False
    return None


def _parse_number(value):
    if value is None:
        return None
    try:
        return float(value)
    except (ValueError, TypeError):
        return None


def _row_dict(ws, row: int, headers: List[str]) -> Dict:
    values = [ws.cell(row=row, column=c).value for c in range(1, len(headers) + 1)]
    if all(v is None for v in values):
        return {}
    return dict(zip(headers, values))


def _read_overall_control_sheet(ws) -> Dict:
    """Read overall_control sheet -> single dict (merged across rows)."""
    headers = [str(ws.cell(row=1, column=c).value or "").strip()
               for c in range(1, ws.max_column + 1)]
    if not headers or not headers[0]:
        return {}

    result: Dict = {}
    for row in range(2, ws.max_row + 1):
        rd = _row_dict(ws, row, headers)
        if not rd:
            continue

        # Top-level scalar fields
        for col_name, target_name, parser in (
            ("outer_iterations", "outer_iterations", lambda v: int(float(v)) if v is not None else None),
            ("fan_relaxation", "fan_relaxation", _parse_number),
            ("estimated_free_convection_velocity", "estimated_free_convection_velocity", _parse_number),
            ("solver_option", "solver_option", lambda v: str(v).strip() if v and str(v).strip() else None),
            ("error_field_variable", "error_field_variable", lambda v: str(v).strip() if v and str(v).strip() else None),
        ):
            v = rd.get(col_name)
            if v is not None and (not isinstance(v, str) or v.strip()):
                parsed = parser(v)
                if parsed is not None:
                    result[target_name] = parsed

        # Boolean fields
        for col_name in BOOL_FIELDS:
            v = _parse_bool(rd.get(col_name))
            if v is not None:
                result[col_name] = v

        # Convergence values
        cv: Dict = {}
        for col_name, ftype in CONVERGENCE_FIELDS.items():
            raw = rd.get(col_name)
            if raw is not None and (not isinstance(raw, str) or raw.strip()):
                try:
                    cv[col_name] = ftype(float(raw))
                except (ValueError, TypeError):
                    pass
        if cv:
            result.setdefault("convergence_values", {}).update(cv)

    return {"overall_control": result} if result else {}


def _read_controls_sheet(ws, entry_tag: str) -> List[Dict]:
    """Read variable_controls or solver_controls sheet -> list of dicts."""
    headers = [str(ws.cell(row=1, column=c).value or "").strip()
               for c in range(1, ws.max_column + 1)]
    if not headers or not headers[0]:
        return []

    results: List[Dict] = []
    for row in range(2, ws.max_row + 1):
        rd = _row_dict(ws, row, headers)
        if not rd:
            continue

        variable = rd.get("variable")
        if not variable or not str(variable).strip():
            continue

        entry: Dict = {"variable": str(variable).strip()}

        if entry_tag == "variable_controls":
            for col, key, ftype in (
                ("false_time_step", "false_time_step", str),
                ("false_time_step_user_value", "false_time_step_user_value", float),
                ("terminal_residual", "terminal_residual", str),
                ("terminal_residual_auto_multiplier", "terminal_residual_auto_multiplier", int),
                ("inner_iterations", "inner_iterations", int),
            ):
                raw = rd.get(col)
                if raw is not None and (not isinstance(raw, str) or raw.strip()):
                    try:
                        entry[key] = ftype(float(raw)) if ftype in (int, float) else ftype(raw)
                    except (ValueError, TypeError):
                        pass

        elif entry_tag == "solver_controls":
            for col, key, ftype in (
                ("linear_relaxation", "linear_relaxation", float),
                ("error_compute_frequency", "error_compute_frequency", int),
            ):
                raw = rd.get(col)
                if raw is not None and (not isinstance(raw, str) or raw.strip()):
                    try:
                        entry[key] = ftype(float(raw))
                    except (ValueError, TypeError):
                        pass

        if len(entry) > 1:
            results.append(entry)
    return results


def _read_transient_overall_sheet(ws) -> Dict:
    """Read transient_overall sheet -> single dict (merged across rows)."""
    headers = [str(ws.cell(row=1, column=c).value or "").strip()
               for c in range(1, ws.max_column + 1)]
    if not headers or not headers[0]:
        return {}

    result: Dict = {}
    for row in range(2, ws.max_row + 1):
        rd = _row_dict(ws, row, headers)
        if not rd:
            continue
        for col_name, ftype in OVERALL_TRANSIENT_FIELDS.items():
            raw = rd.get(col_name)
            if raw is not None and (not isinstance(raw, str) or raw.strip()):
                try:
                    result[col_name] = ftype(float(raw))
                except (ValueError, TypeError):
                    pass
    return result


def _read_transient_save_times_sheet(ws) -> List[float]:
    """Read transient_save_times sheet -> list of time values."""
    headers = [str(ws.cell(row=1, column=c).value or "").strip()
               for c in range(1, ws.max_column + 1)]
    if not headers or not headers[0]:
        return []

    times: List[float] = []
    for row in range(2, ws.max_row + 1):
        rd = _row_dict(ws, row, headers)
        if not rd:
            continue
        raw = rd.get("save_time")
        if raw is not None and (not isinstance(raw, str) or raw.strip()):
            try:
                times.append(float(raw))
            except (ValueError, TypeError):
                pass
    return times


def _read_time_patches_sheet(ws) -> List[Dict]:
    """Read time_patches sheet -> list of time_patch dicts."""
    headers = [str(ws.cell(row=1, column=c).value or "").strip()
               for c in range(1, ws.max_column + 1)]
    if not headers or not headers[0]:
        return []

    results: List[Dict] = []
    for row in range(2, ws.max_row + 1):
        rd = _row_dict(ws, row, headers)
        if not rd:
            continue

        name = rd.get("name")
        if not name or not str(name).strip():
            continue

        entry: Dict = {"name": str(name).strip()}
        for col_name, ftype in TIME_PATCH_FIELDS.items():
            raw = rd.get(col_name)
            if raw is not None and (not isinstance(raw, str) or raw.strip()):
                try:
                    entry[col_name] = ftype(float(raw)) if ftype in (int, float) else str(raw).strip()
                except (ValueError, TypeError):
                    pass

        if len(entry) > 1:
            results.append(entry)
    return results


def load_excel(path: Path) -> Dict:
    try:
        from openpyxl import load_workbook as _load_wb
    except ImportError:
        raise ImportError("openpyxl required: pip install openpyxl")

    wb = _load_wb(str(path), read_only=True, data_only=True)
    config: Dict = {}

    # overall_control
    if "overall_control" in wb.sheetnames:
        data = _read_overall_control_sheet(wb["overall_control"])
        config.update(data)

    # variable_controls
    if "variable_controls" in wb.sheetnames:
        data = _read_controls_sheet(wb["variable_controls"], "variable_controls")
        if data:
            config["variable_controls"] = data

    # solver_controls
    if "solver_controls" in wb.sheetnames:
        data = _read_controls_sheet(wb["solver_controls"], "solver_controls")
        if data:
            config["solver_controls"] = data

    # transient_overall
    if "transient_overall" in wb.sheetnames:
        data = _read_transient_overall_sheet(wb["transient_overall"])
        if data:
            config.setdefault("transient", {}).setdefault("overall_transient", {}).update(data)

    # transient_save_times
    if "transient_save_times" in wb.sheetnames:
        data = _read_transient_save_times_sheet(wb["transient_save_times"])
        if data:
            config.setdefault("transient", {})["save_times"] = data

    # time_patches
    if "time_patches" in wb.sheetnames:
        data = _read_time_patches_sheet(wb["time_patches"])
        if data:
            config.setdefault("transient", {})["time_patches"] = data

    wb.close()
    return config


def load_config(path: Path) -> Dict:
    suffix = path.suffix.lower()
    if suffix in (".xlsx", ".xls", ".xlsm"):
        return load_excel(path)
    return load_json(path)


# ============================================================================
# Excel template generator
# ============================================================================

def create_template_excel(output_path: str) -> None:
    from openpyxl import Workbook
    from openpyxl.styles import Font, Alignment

    wb = Workbook()
    header_font = Font(bold=True)
    center = Alignment(horizontal="center")

    def _headers(ws, names):
        for col, h in enumerate(names, 1):
            cell = ws.cell(row=1, column=col, value=h)
            cell.font = header_font
            cell.alignment = center

    def _widths(ws, w=20):
        for idx in range(1, ws.max_column + 1):
            ws.column_dimensions[ws.cell(row=1, column=idx).column_letter].width = w

    # ── Sheet 1: overall_control ──
    ws1 = wb.active
    ws1.title = "overall_control"
    _headers(ws1, [
        "outer_iterations", "fan_relaxation", "estimated_free_convection_velocity",
        "solver_option", "monitor_convergence",
        "active_plate_conduction", "use_double_precision",
        "network_assembly_block_correction", "freeze_flow", "store_error_field",
        "error_field_variable",
        "required_accuracy", "num_iterations", "residual_threshold",
    ])
    example1 = [500, 0.9, 0.2, "multi_grid", "true",
                "false", "false", "false", "false", "false",
                "", 0.2, 45, 200]
    for c, val in enumerate(example1, 1):
        ws1.cell(row=2, column=c, value=val)
    _widths(ws1)

    # ── Sheet 2: variable_controls ──
    ws2 = wb.create_sheet("variable_controls")
    _headers(ws2, [
        "variable", "false_time_step", "false_time_step_user_value",
        "terminal_residual", "terminal_residual_auto_multiplier", "inner_iterations",
    ])
    for r, (var, fts, ftsv, tr, tram, ii) in enumerate([
        ("x_velocity", "user", 1.5, "automatic", 1, 1),
        ("y_velocity", "user", 1.5, "automatic", 1, 1),
        ("z_velocity", "user", 1.5, "automatic", 1, 1),
        ("temperature", "user", 1.5, "automatic", 1, 1),
    ], 2):
        ws2.cell(row=r, column=1, value=var)
        ws2.cell(row=r, column=2, value=fts)
        ws2.cell(row=r, column=3, value=ftsv)
        ws2.cell(row=r, column=4, value=tr)
        ws2.cell(row=r, column=5, value=tram)
        ws2.cell(row=r, column=6, value=ii)
    _widths(ws2)

    # ── Sheet 3: solver_controls ──
    ws3 = wb.create_sheet("solver_controls")
    _headers(ws3, ["variable", "linear_relaxation", "error_compute_frequency"])
    for r, (var, lr, ecf) in enumerate([
        ("pressure", 0.3, 0),
        ("temperature", 0.7, 0),
    ], 2):
        ws3.cell(row=r, column=1, value=var)
        ws3.cell(row=r, column=2, value=lr)
        ws3.cell(row=r, column=3, value=ecf)
    _widths(ws3)

    # ── Sheet 4: transient_overall ──
    ws4 = wb.create_sheet("transient_overall")
    _headers(ws4, ["start_time", "end_time", "duration", "keypoint_tolerance"])
    for c, val in enumerate([0, 60, 60, 0.0001], 1):
        ws4.cell(row=2, column=c, value=val)
    _widths(ws4)

    # ── Sheet 5: transient_save_times ──
    ws5 = wb.create_sheet("transient_save_times")
    _headers(ws5, ["save_time"])
    for r, val in enumerate([0, 30, 60], 2):
        ws5.cell(row=r, column=1, value=val)
    _widths(ws5)

    # ── Sheet 6: time_patches ──
    ws6 = wb.create_sheet("time_patches")
    _headers(ws6, [
        "name", "start_time", "end_time",
        "step_control", "additional_steps", "minimum_number", "maximum_size",
        "step_distribution", "distribution_index",
    ])
    for r, row_data in enumerate([
        ("First", 0, 30, "minimum_number", None, 15, None, "increasing_power", 1.4),
        ("Second", 30, 60, "minimum_number", None, 12, None, "uniform", 1),
    ], 2):
        for c, val in enumerate(row_data, 1):
            if val is not None:
                ws6.cell(row=r, column=c, value=val)
    _widths(ws6)

    wb.save(output_path)
    print(f"[OK] Template created: {output_path}")


# ============================================================================
# XML indentation
# ============================================================================

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


# ============================================================================
# CLI
# ============================================================================

def main() -> int:
    parser = argparse.ArgumentParser(
        description="Add/update solve settings in a FloXML project via JSON or Excel config"
    )
    parser.add_argument("input", nargs="?", help="Input FloXML file")
    parser.add_argument("--config", help="Solve config file (.json or .xlsx)")
    parser.add_argument("-o", "--output", help="Output FloXML file")
    parser.add_argument("--create-template", metavar="PATH",
                        help="Create an example Excel template at PATH")
    args = parser.parse_args()

    if args.create_template:
        create_template_excel(args.create_template)
        return 0

    if not args.input or not args.config:
        parser.error("input and --config are required (unless using --create-template)")

    input_path = Path(args.input)
    config_path = Path(args.config)
    output_path = (Path(args.output) if args.output
                   else input_path.with_name(f"{input_path.stem}_with_solve{input_path.suffix}"))

    tree = ET.parse(input_path)
    root = tree.getroot()
    config = load_config(config_path)
    root = apply_solve_settings(root, config)
    indent_xml(root)
    tree.write(output_path, encoding="utf-8", xml_declaration=True)

    sections = []
    if "overall_control" in config:
        sections.append("overall_control")
    if "variable_controls" in config:
        sections.append(f"{len(config['variable_controls'])} variable_control(s)")
    if "solver_controls" in config:
        sections.append(f"{len(config['solver_controls'])} solver_control(s)")
    if "transient" in config:
        tr = config["transient"]
        parts = []
        if "overall_transient" in tr:
            parts.append("overall_transient")
        if "time_patches" in tr:
            parts.append(f"{len(tr['time_patches'])} time_patch(es)")
        if "save_times" in tr:
            parts.append(f"{len(tr['save_times'])} save_time(s)")
        if parts:
            sections.append("transient(" + ", ".join(parts) + ")")
    print(f"[OK] Applied solve settings ({', '.join(sections)}): {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
