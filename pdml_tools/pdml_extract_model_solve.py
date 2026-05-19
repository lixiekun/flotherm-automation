#!/usr/bin/env python3
"""
从 PDML / FloXML 文件中提取 model setup 和 solver control 设置，
输出为 FloXML 格式的 XML 文件，可直接导入 FloTHERM 使用。

支持:
  - FloXML (.xml / .floxml) — 直接解析
  - PDML (.pdml) — 二进制格式，先转 FloXML 再提取

用法:
    python pdml_tools/pdml_extract_model_solve.py model.pdml -o model_solve.xml
    python pdml_tools/pdml_extract_model_solve.py model.xml -o model_solve.xml
    python pdml_tools/pdml_extract_model_solve.py model.pdml  # 打印摘要
"""

import argparse
import json
import os
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any, Dict, Optional

# Ensure project root is on sys.path
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from pdml_tools.pdml_extract_regions import is_binary_pdml


# ============================================================================
# PDML -> FloXML root
# ============================================================================

def _pdml_to_floxml_root(filepath: str) -> ET.Element:
    """Convert binary PDML to FloXML ElementTree in memory."""
    from pdml_tools.pdml_to_floxml_converter import PDMLBinaryReader, FloXMLBuilder
    reader = PDMLBinaryReader(filepath)
    data = reader.read()
    builder = FloXMLBuilder()
    return builder.build(data)


def _parse_input(filepath: str) -> ET.Element:
    """Auto-detect format and return FloXML root element."""
    if is_binary_pdml(filepath):
        print("[INFO] Detected binary PDML, converting to FloXML...", file=sys.stderr)
        return _pdml_to_floxml_root(filepath)
    tree = ET.parse(filepath)
    return tree.getroot()


# ============================================================================
# Extract model + solve sections
# ============================================================================

def extract_model_solve_floxml(input_path: str, output_path: Optional[str] = None) -> ET.Element:
    """
    Extract <model> and <solve> from PDML/FloXML, build a standalone FloXML.

    Returns the root element of the new FloXML tree.
    """
    root = _parse_input(input_path)

    xml_case = ET.Element("xml_case")

    name_elem = root.find("name")
    if name_elem is not None and name_elem.text:
        name = ET.SubElement(xml_case, "name")
        name.text = name_elem.text

    # Copy <model> section
    model = root.find("model")
    if model is not None:
        xml_case.append(_clean_copy(model))
    else:
        print("[WARN] No <model> section found in input.", file=sys.stderr)

    # Copy <solve> section
    solve = root.find("solve")
    if solve is not None:
        xml_case.append(_clean_copy(solve))
    else:
        print("[WARN] No <solve> section found in input.", file=sys.stderr)

    return xml_case


def _clean_copy(elem: ET.Element) -> ET.Element:
    """Deep copy an element, removing namespace prefixes."""
    new = ET.Element(_strip_tag(elem.tag))
    new.text = elem.text
    new.tail = elem.tail
    for k, v in elem.attrib.items():
        new.set(_strip_tag(k), v)
    for child in elem:
        new.append(_clean_copy(child))
    return new


def _strip_tag(tag: str) -> str:
    """Remove XML namespace prefix from tag."""
    if "}" in tag:
        return tag.split("}", 1)[1]
    return tag


# ============================================================================
# Pretty print
# ============================================================================

def _prettify(elem: ET.Element, indent: str = "    ") -> str:
    """Pretty-print XML with proper indentation."""
    _indent(elem, 0, indent)
    rough = ET.tostring(elem, encoding="unicode", xml_declaration=False)
    return '<?xml version="1.0" encoding="utf-8"?>\n' + rough + "\n"


def _indent(elem: ET.Element, level: int, indent: str) -> None:
    """Add indentation whitespace to XML tree in-place."""
    i = "\n" + indent * level
    if len(elem):
        if not elem.text or not elem.text.strip():
            elem.text = i + indent
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
        for child in elem:
            _indent(child, level + 1, indent)
        if not child.tail or not child.tail.strip():
            child.tail = i
    else:
        if level and (not elem.tail or not elem.tail.strip()):
            elem.tail = i
    if not level:
        elem.tail = "\n"


# ============================================================================
# Summary
# ============================================================================

def print_summary(root: ET.Element) -> None:
    """Print a human-readable summary of extracted settings."""
    print("=" * 60)
    print("Model & Solve Settings")
    print("=" * 60)

    model = root.find("model")
    if model is not None:
        _print_model(model)
    else:
        print("\n  (no model section)")

    solve = root.find("solve")
    if solve is not None:
        _print_solve(solve)
    else:
        print("\n  (no solve section)")

    print("=" * 60)


def _print_model(model: ET.Element) -> None:
    print("\n[Model]")

    modeling = model.find("modeling")
    if modeling is not None:
        print("  Modeling:")
        for child in modeling:
            tag = _strip_tag(child.tag)
            if len(child):
                continue  # skip complex sub-elements in summary
            print(f"    {tag} = {child.text}")

    turbulence = model.find("turbulence")
    if turbulence is not None:
        print("  Turbulence:")
        for child in turbulence:
            tag = _strip_tag(child.tag)
            print(f"    {tag} = {child.text}")

    gravity = model.find("gravity")
    if gravity is not None:
        print("  Gravity:")
        for child in gravity:
            tag = _strip_tag(child.tag)
            if len(child):
                continue
            print(f"    {tag} = {child.text}")

    gl = model.find("global")
    if gl is not None:
        print("  Global:")
        for child in gl:
            tag = _strip_tag(child.tag)
            print(f"    {tag} = {child.text}")

    transient = model.find("transient")
    if transient is not None:
        print("  Transient: (settings present)")

    iv = model.find("initial_variables")
    if iv is not None:
        print("  Initial Variables: (settings present)")


def _print_solve(solve: ET.Element) -> None:
    print("\n[Solve]")

    oc = solve.find("overall_control")
    if oc is not None:
        print("  Overall Control:")
        for child in oc:
            tag = _strip_tag(child.tag)
            if tag == "convergence_values":
                cv_lines = []
                for cv_child in child:
                    cv_lines.append(f"{_strip_tag(cv_child.tag)}={cv_child.text}")
                print(f"    convergence_values: {', '.join(cv_lines)}")
            elif tag == "monitor_point_transient_termination_criteria":
                print(f"    monitor_point_transient_termination_criteria: (present)")
            else:
                print(f"    {tag} = {child.text}")

    vc_parent = solve.find("variable_controls")
    if vc_parent is not None:
        vcs = vc_parent.findall("variable_control")
        print(f"  Variable Controls ({len(vcs)}):")
        for vc in vcs:
            var = vc.findtext("variable", "?")
            fts = vc.findtext("false_time_step", "?")
            inner = vc.findtext("inner_iterations", "?")
            print(f"    {var}: fts={fts}, inner_iter={inner}")

    sc_parent = solve.find("solver_controls")
    if sc_parent is not None:
        scs = sc_parent.findall("solver_control")
        print(f"  Solver Controls ({len(scs)}):")
        for sc in scs:
            var = sc.findtext("variable", "?")
            relax = sc.findtext("linear_relaxation", "?")
            print(f"    {var}: relaxation={relax}")


# ============================================================================
# JSON output
# ============================================================================

def _text_to_value(text: Optional[str]) -> Any:
    """Convert XML text to int/float/bool/str."""
    if text is None or not text.strip():
        return None
    text = text.strip()
    if text.lower() in ("true", "false"):
        return text.lower()
    try:
        return int(text)
    except ValueError:
        pass
    try:
        return float(text)
    except ValueError:
        pass
    return text


def _elem_to_dict(elem: ET.Element) -> Dict[str, Any]:
    """Recursively convert XML element children to dict."""
    result: Dict[str, Any] = {}
    for child in elem:
        ctag = _strip_tag(child.tag)
        sub_children = list(child)
        if sub_children:
            result[ctag] = _elem_to_dict(child)
        else:
            result[ctag] = _text_to_value(child.text)
    return result


def _is_list_section(section: ET.Element) -> bool:
    """Check if a section contains repeated child elements (list) vs unique tags (dict).

    A section is a list if all children share the same tag (e.g. variable_controls
    containing multiple variable_control elements, or solver_controls with 1 solver_control).
    """
    children = list(section)
    if not children:
        return False
    tags = [_strip_tag(c.tag) for c in children]
    return len(set(tags)) == 1


def to_json_dict(root: ET.Element) -> Dict[str, Any]:
    """Convert model/solve XML tree to a JSON-serializable dict."""
    result: Dict[str, Any] = {}

    name_elem = root.find("name")
    if name_elem is not None and name_elem.text:
        result["name"] = name_elem.text

    model = root.find("model")
    if model is not None:
        model_dict: Dict[str, Any] = {}
        for section in model:
            tag = _strip_tag(section.tag)
            section_dict = _elem_to_dict(section)
            if section_dict:
                model_dict[tag] = section_dict
        if model_dict:
            result["model"] = model_dict

    solve = root.find("solve")
    if solve is not None:
        solve_dict: Dict[str, Any] = {}
        for section in solve:
            tag = _strip_tag(section.tag)
            if _is_list_section(section):
                # List section: variable_controls → [variable_control, ...]
                entries = [_elem_to_dict(item) for item in section]
                solve_dict[tag] = [e for e in entries if e]
            else:
                section_dict = _elem_to_dict(section)
                if section_dict:
                    solve_dict[tag] = section_dict
        if solve_dict:
            result["solve"] = solve_dict

    return result


# ============================================================================
# CLI
# ============================================================================

def main() -> int:
    parser = argparse.ArgumentParser(
        description="Extract model setup and solver control from PDML/FloXML",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python pdml_tools/pdml_extract_model_solve.py model.pdml -o model_solve.xml
  python pdml_tools/pdml_extract_model_solve.py model.pdml -o model_solve.json --json
  python pdml_tools/pdml_extract_model_solve.py model.xml --summary
  python pdml_tools/pdml_extract_model_solve.py model.pdml --json
        """,
    )
    parser.add_argument("input", help="Input PDML or FloXML file")
    parser.add_argument("-o", "--output", help="Output file path")
    parser.add_argument("--json", action="store_true", help="Output as JSON instead of XML")
    parser.add_argument("--summary", action="store_true", help="Print summary")

    args = parser.parse_args()

    input_path = Path(args.input)
    if not input_path.exists():
        print(f"[ERROR] File not found: {input_path}", file=sys.stderr)
        return 1

    try:
        xml_case = extract_model_solve_floxml(str(input_path))
    except ET.ParseError as e:
        print(f"[ERROR] XML parse failed: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"[ERROR] {type(e).__name__}: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1

    if args.summary or not args.output:
        print_summary(xml_case)

    if args.json:
        result = to_json_dict(xml_case)
        if args.output:
            output_path = Path(args.output)
            with output_path.open("w", encoding="utf-8") as f:
                json.dump(result, f, indent=2, ensure_ascii=False)
            print(f"[OK] JSON output: {output_path}")
        else:
            print(json.dumps(result, indent=2, ensure_ascii=False))
    elif args.output:
        xml_str = _prettify(xml_case)
        output_path = Path(args.output)
        output_path.write_text(xml_str, encoding="utf-8")
        print(f"[OK] XML output: {output_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
