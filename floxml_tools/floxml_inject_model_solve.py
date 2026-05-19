#!/usr/bin/env python3
"""
将 model/solve 设置 XML 导入（注入）到 FloXML 项目文件中。

支持从 pdml_extract_model_solve.py 生成的 XML 或任何包含 <model>/<solve> 的 FloXML
导入到目标 FloXML 项目文件，替换其 <model> 和 <solve> 部分。

支持:
  - 目标文件: FloXML (.xml / .floxml) 或 PDML (.pdml, 二进制)
  - 导入源: 包含 <model> 和/或 <solve> 的 XML 文件
  - 可选: 只导入 model 或只导入 solve

用法:
    # 导入 model + solve
    python3 floxml_tools/floxml_inject_model_solve.py settings.xml target.xml -o output.xml

    # 只导入 solve 部分
    python3 floxml_tools/floxml_inject_model_solve.py settings.xml target.xml -o output.xml --solve-only

    # 只导入 model 部分
    python3 floxml_tools/floxml_inject_model_solve.py settings.xml target.xml -o output.xml --model-only

    # 从 PDML 目标导入（自动转 FloXML）
    python3 floxml_tools/floxml_inject_model_solve.py settings.xml target.pdml -o output.xml
"""

import argparse
import os
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from pdml_tools.pdml_extract_regions import is_binary_pdml


def _strip_tag(tag: str) -> str:
    if "}" in tag:
        return tag.split("}", 1)[1]
    return tag


def _clean_copy(elem: ET.Element) -> ET.Element:
    new = ET.Element(_strip_tag(elem.tag))
    new.text = elem.text
    new.tail = elem.tail
    for k, v in elem.attrib.items():
        new.set(_strip_tag(k), v)
    for child in elem:
        new.append(_clean_copy(child))
    return new


def _indent(elem: ET.Element, level: int, indent: str = "    ") -> None:
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


def _prettify(elem: ET.Element) -> str:
    _indent(elem, 0)
    rough = ET.tostring(elem, encoding="unicode", xml_declaration=False)
    return '<?xml version="1.0" encoding="utf-8"?>\n' + rough + "\n"


def _parse_target(filepath: str) -> ET.Element:
    """Parse target file (FloXML or binary PDML)."""
    if is_binary_pdml(filepath):
        print("[INFO] Target is binary PDML, converting to FloXML...", file=sys.stderr)
        from pdml_tools.pdml_to_floxml_converter import PDMLBinaryReader, FloXMLBuilder
        reader = PDMLBinaryReader(filepath)
        data = reader.read()
        builder = FloXMLBuilder()
        return builder.build(data)
    return ET.parse(filepath).getroot()


# ============================================================================
# Section ordering in FloXML
# ============================================================================

# Canonical order of top-level children under <xml_case>
_SECTION_ORDER = [
    "name", "model", "solve", "grid", "attributes",
    "geometry", "solution_domain",
]


def _section_index(tag: str) -> int:
    """Return sort index for a section tag."""
    tag = _strip_tag(tag)
    if tag in _SECTION_ORDER:
        return _SECTION_ORDER.index(tag)
    return len(_SECTION_ORDER)


def _replace_section(root: ET.Element, tag: str, new_elem: ET.Element) -> None:
    """Replace (or insert) a top-level child section by tag name."""
    existing = root.find(tag)
    if existing is not None:
        root.remove(existing)

    new_copy = _clean_copy(new_elem)

    # Find correct insertion position to maintain section order
    insert_idx = len(list(root))
    for i, child in enumerate(root):
        if _section_index(tag) < _section_index(child.tag):
            insert_idx = i
            break

    root.insert(insert_idx, new_copy)


# ============================================================================
# Core: inject model/solve from source into target
# ============================================================================

def inject_model_solve(source_path: str, target_path: str,
                       model_only: bool = False, solve_only: bool = False) -> ET.Element:
    """
    Read <model> and/or <solve> from source XML, inject into target FloXML.

    Returns the modified target root element.
    """
    source_root = ET.parse(source_path).getroot()
    target_root = _parse_target(target_path)

    if model_only and solve_only:
        print("[WARN] Both --model-only and --solve-only specified, nothing to do.", file=sys.stderr)
        return target_root

    if not solve_only:
        model = source_root.find("model")
        if model is not None:
            _replace_section(target_root, "model", model)
            print("[OK] Injected <model> section.", file=sys.stderr)
        else:
            print("[WARN] No <model> section found in source.", file=sys.stderr)

    if not model_only:
        solve = source_root.find("solve")
        if solve is not None:
            _replace_section(target_root, "solve", solve)
            print("[OK] Injected <solve> section.", file=sys.stderr)
        else:
            print("[WARN] No <solve> section found in source.", file=sys.stderr)

    return target_root


# ============================================================================
# Summary
# ============================================================================

def print_summary(root: ET.Element) -> None:
    """Print current model + solve settings in target."""
    print("=" * 60)
    print("Current Model & Solve Settings")
    print("=" * 60)

    model = root.find("model")
    if model is not None:
        print("\n[Model]")
        for section_tag in ("modeling", "turbulence", "gravity", "global", "transient", "initial_variables"):
            sec = model.find(section_tag)
            if sec is not None:
                print(f"  {section_tag}: present")
                for child in sec:
                    tag = _strip_tag(child.tag)
                    if not len(child):
                        print(f"    {tag} = {child.text}")
    else:
        print("\n[Model] (none)")

    solve = root.find("solve")
    if solve is not None:
        print("\n[Solve]")
        oc = solve.find("overall_control")
        if oc is not None:
            print("  overall_control: present")
            for child in oc:
                tag = _strip_tag(child.tag)
                if not len(child):
                    print(f"    {tag} = {child.text}")
        vc = solve.find("variable_controls")
        if vc is not None:
            print(f"  variable_controls: {len(vc)} entries")
        sc = solve.find("solver_controls")
        if sc is not None:
            print(f"  solver_controls: {len(sc)} entries")
    else:
        print("\n[Solve] (none)")

    print("=" * 60)


# ============================================================================
# CLI
# ============================================================================

def main() -> int:
    parser = argparse.ArgumentParser(
        description="Inject model/solve settings XML into a FloXML project file",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Inject both model and solve
  python3 floxml_tools/floxml_inject_model_solve.py settings.xml target.xml -o output.xml

  # Inject only solve
  python3 floxml_tools/floxml_inject_model_solve.py settings.xml target.xml -o output.xml --solve-only

  # Inject only model
  python3 floxml_tools/floxml_inject_model_solve.py settings.xml target.xml -o output.xml --model-only

  # Preview without writing
  python3 floxml_tools/floxml_inject_model_solve.py settings.xml target.xml --summary
        """,
    )
    parser.add_argument("source", help="Source XML with <model>/<solve> to import")
    parser.add_argument("target", help="Target FloXML or PDML file to inject into")
    parser.add_argument("-o", "--output", help="Output FloXML file path")
    parser.add_argument("--model-only", action="store_true", help="Only inject <model> section")
    parser.add_argument("--solve-only", action="store_true", help="Only inject <solve> section")
    parser.add_argument("--summary", action="store_true", help="Print summary after injection")

    args = parser.parse_args()

    source_path = Path(args.source)
    target_path = Path(args.target)
    if not source_path.exists():
        print(f"[ERROR] Source file not found: {source_path}", file=sys.stderr)
        return 1
    if not target_path.exists():
        print(f"[ERROR] Target file not found: {target_path}", file=sys.stderr)
        return 1

    try:
        result = inject_model_solve(
            str(source_path), str(target_path),
            model_only=args.model_only,
            solve_only=args.solve_only,
        )
    except ET.ParseError as e:
        print(f"[ERROR] XML parse failed: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"[ERROR] {type(e).__name__}: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1

    if args.summary or not args.output:
        print_summary(result)

    if args.output:
        xml_str = _prettify(result)
        output_path = Path(args.output)
        output_path.write_text(xml_str, encoding="utf-8")
        print(f"[OK] Output: {output_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
