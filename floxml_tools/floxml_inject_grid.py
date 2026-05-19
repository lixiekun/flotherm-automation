#!/usr/bin/env python3
"""
将 system grid 设置 XML 导入（注入）到 FloXML 项目文件中。

用法:
    python3 floxml_tools/floxml_inject_grid.py grid.xml target.xml -o output.xml
    python3 floxml_tools/floxml_inject_grid.py grid.xml target.pdml -o output.xml
    python3 floxml_tools/floxml_inject_grid.py grid.xml target.xml --summary
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
from pdml_tools.pdml_extract_grid import (
    _strip_tag, _clean_copy, _indent, _prettify, print_summary,
)


def _parse_target(filepath: str) -> ET.Element:
    if is_binary_pdml(filepath):
        print("[INFO] Target is binary PDML, converting to FloXML...", file=sys.stderr)
        from pdml_tools.pdml_to_floxml_converter import PDMLBinaryReader, FloXMLBuilder
        reader = PDMLBinaryReader(filepath)
        data = reader.read()
        builder = FloXMLBuilder()
        return builder.build(data)
    return ET.parse(filepath).getroot()


_SECTION_ORDER = [
    "name", "model", "solve", "grid", "attributes",
    "geometry", "solution_domain",
]


def _section_index(tag: str) -> int:
    tag = _strip_tag(tag)
    if tag in _SECTION_ORDER:
        return _SECTION_ORDER.index(tag)
    return len(_SECTION_ORDER)


def inject_grid(source_path: str, target_path: str) -> ET.Element:
    """Read <grid> from source XML, inject into target FloXML."""
    source_root = ET.parse(source_path).getroot()
    target_root = _parse_target(target_path)

    grid = source_root.find("grid")
    if grid is None:
        print("[ERROR] No <grid> section found in source.", file=sys.stderr)
        return target_root

    existing = target_root.find("grid")
    if existing is not None:
        target_root.remove(existing)

    grid_copy = _clean_copy(grid)

    insert_idx = len(list(target_root))
    for i, child in enumerate(target_root):
        if _section_index("grid") < _section_index(child.tag):
            insert_idx = i
            break
    target_root.insert(insert_idx, grid_copy)
    print("[OK] Injected <grid> section.", file=sys.stderr)

    return target_root


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Inject grid settings XML into a FloXML project file",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 floxml_tools/floxml_inject_grid.py grid.xml target.xml -o output.xml
  python3 floxml_tools/floxml_inject_grid.py grid.xml target.pdml -o output.xml
        """,
    )
    parser.add_argument("source", help="Source XML with <grid> to import")
    parser.add_argument("target", help="Target FloXML or PDML file")
    parser.add_argument("-o", "--output", help="Output FloXML file path")
    parser.add_argument("--summary", action="store_true", help="Print summary after injection")

    args = parser.parse_args()

    if not Path(args.source).exists():
        print(f"[ERROR] Source not found: {args.source}", file=sys.stderr)
        return 1
    if not Path(args.target).exists():
        print(f"[ERROR] Target not found: {args.target}", file=sys.stderr)
        return 1

    try:
        result = inject_grid(args.source, args.target)
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
