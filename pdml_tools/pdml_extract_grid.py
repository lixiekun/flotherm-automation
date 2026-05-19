#!/usr/bin/env python3
"""
从 PDML / FloXML 文件中提取 system grid 设置，
输出为 FloXML 格式的 XML 文件，可用于导入到其他 FloTHERM 项目。

支持:
  - FloXML (.xml / .floxml) — 直接解析
  - PDML (.pdml) — 二进制格式，先转 FloXML 再提取

用法:
    python3 pdml_tools/pdml_extract_grid.py model.pdml -o grid.xml
    python3 pdml_tools/pdml_extract_grid.py model.xml -o grid.xml
    python3 pdml_tools/pdml_extract_grid.py model.pdml --summary
"""

import argparse
import os
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Optional

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


def _pdml_to_floxml_root(filepath: str) -> ET.Element:
    from pdml_tools.pdml_to_floxml_converter import PDMLBinaryReader, FloXMLBuilder
    reader = PDMLBinaryReader(filepath)
    data = reader.read()
    builder = FloXMLBuilder()
    return builder.build(data)


def _parse_input(filepath: str) -> ET.Element:
    if is_binary_pdml(filepath):
        print("[INFO] Detected binary PDML, converting to FloXML...", file=sys.stderr)
        return _pdml_to_floxml_root(filepath)
    return ET.parse(filepath).getroot()


# ============================================================================
# Extract grid section
# ============================================================================

def extract_grid_floxml(input_path: str) -> Optional[ET.Element]:
    """
    Extract <grid> from PDML/FloXML, return standalone FloXML root element.
    """
    root = _parse_input(input_path)

    grid = root.find("grid")
    if grid is None:
        return None

    xml_case = ET.Element("xml_case")

    name_elem = root.find("name")
    if name_elem is not None and name_elem.text:
        name = ET.SubElement(xml_case, "name")
        name.text = name_elem.text

    xml_case.append(_clean_copy(grid))
    return xml_case


# ============================================================================
# Summary
# ============================================================================

def print_summary(root: ET.Element) -> None:
    print("=" * 60)
    print("Grid Settings")
    print("=" * 60)

    grid = root.find("grid")
    if grid is None:
        print("\n  (no grid section)")
        print("=" * 60)
        return

    sg = grid.find("system_grid")
    if sg is not None:
        print("\n[System Grid]")
        for key in ("smoothing", "smoothing_type", "dynamic_update"):
            v = sg.findtext(key)
            if v is not None:
                print(f"  {key} = {v}")

        for axis in ("x_grid", "y_grid", "z_grid"):
            ax = sg.find(axis)
            if ax is not None:
                print(f"\n  {axis}:")
                for child in ax:
                    print(f"    {_strip_tag(child.tag)} = {child.text}")

    patches_parent = grid.find("patches")
    if patches_parent is not None:
        patches = patches_parent.findall("grid_patch")
        print(f"\n[Grid Patches] ({len(patches)})")
        for gp in patches:
            name = gp.findtext("name", "?")
            applies = gp.findtext("applies_to", "?")
            start = gp.findtext("start_location", "?")
            end = gp.findtext("end_location", "?")
            control = gp.findtext("number_of_cells_control", "?")
            print(f"  {name}: {applies} [{start} - {end}], control={control}")

    print("=" * 60)


# ============================================================================
# CLI
# ============================================================================

def main() -> int:
    parser = argparse.ArgumentParser(
        description="Extract system grid settings from PDML/FloXML to FloXML",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 pdml_tools/pdml_extract_grid.py model.pdml -o grid.xml
  python3 pdml_tools/pdml_extract_grid.py model.xml -o grid.xml
  python3 pdml_tools/pdml_extract_grid.py model.pdml --summary
        """,
    )
    parser.add_argument("input", help="Input PDML or FloXML file")
    parser.add_argument("-o", "--output", help="Output FloXML file path")
    parser.add_argument("--summary", action="store_true", help="Print summary")

    args = parser.parse_args()

    input_path = Path(args.input)
    if not input_path.exists():
        print(f"[ERROR] File not found: {input_path}", file=sys.stderr)
        return 1

    try:
        xml_case = extract_grid_floxml(str(input_path))
    except ET.ParseError as e:
        print(f"[ERROR] XML parse failed: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"[ERROR] {type(e).__name__}: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1

    if xml_case is None:
        print("[ERROR] No <grid> section found in input.", file=sys.stderr)
        return 1

    if args.summary or not args.output:
        print_summary(xml_case)

    if args.output:
        xml_str = _prettify(xml_case)
        output_path = Path(args.output)
        output_path.write_text(xml_str, encoding="utf-8")
        print(f"[OK] Output: {output_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
