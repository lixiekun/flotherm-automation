#!/usr/bin/env python3
"""
从 PDML / FloXML 文件中提取 Volume Region 和 Grid Constraint 信息，
输出为 JSON 格式，可直接作为 floxml_add_volume_regions.py 的输入配置。

支持:
  - FloXML (.xml / .floxml) — XML 文本格式
  - PDML (.pdml) — FloTHERM 二进制格式

用法:
    python pdml_tools/pdml_extract_regions.py model.pdml -o regions.json
    python pdml_tools/pdml_extract_regions.py model.xml -o regions.json
    python pdml_tools/pdml_extract_regions.py model.pdml  # 打印摘要
"""

import argparse
import json
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple


# ============================================================================
# XML (FloXML) 提取
# ============================================================================

def _strip_ns(tag: str) -> str:
    if "}" in tag:
        return tag.split("}")[1]
    return tag


def _float_text(elem: ET.Element, tag: str, default: float = 0.0) -> float:
    child = elem.find(tag)
    if child is None or child.text is None:
        return default
    try:
        return float(child.text.strip())
    except ValueError:
        return default


def _text(elem: ET.Element, tag: str) -> Optional[str]:
    child = elem.find(tag)
    if child is not None and child.text:
        return child.text.strip()
    return None


def _parse_inflation(elem: ET.Element) -> Optional[Dict]:
    infl: Dict = {}
    v = _text(elem, "inflation_type")
    if v is not None:
        infl["inflation_type"] = v
    v = _text(elem, "inflation_size")
    if v is not None:
        try:
            infl["inflation_size"] = float(v)
        except ValueError:
            pass
    v = _text(elem, "inflation_percent")
    if v is not None:
        try:
            infl["inflation_percent"] = float(v)
        except ValueError:
            pass
    v = _text(elem, "number_cells_control")
    if v is not None:
        infl["number_cells_control"] = v
    v = _text(elem, "min_number")
    if v is not None:
        try:
            infl["min_number"] = int(float(v))
        except ValueError:
            pass
    v = _text(elem, "max_size")
    if v is not None:
        try:
            infl["max_size"] = float(v)
        except ValueError:
            pass
    return infl if infl else None


def extract_grid_constraints_xml(root: ET.Element) -> List[Dict]:
    results: List[Dict] = []
    for gc_parent in root.iter():
        if _strip_ns(gc_parent.tag) != "grid_constraints":
            continue
        for gca in gc_parent:
            if _strip_ns(gca.tag) != "grid_constraint_att":
                continue
            entry: Dict = {}
            name = _text(gca, "name")
            if name:
                entry["name"] = name
            v = _text(gca, "enable_min_cell_size")
            if v is not None:
                entry["enable_min_cell_size"] = v.lower() == "true"
            v = _text(gca, "min_cell_size")
            if v is not None:
                try:
                    entry["min_cell_size"] = float(v)
                except ValueError:
                    pass
            v = _text(gca, "number_cells_control")
            if v is not None:
                entry["number_cells_control"] = v
            v = _text(gca, "min_number")
            if v is not None:
                try:
                    entry["min_number"] = int(float(v))
                except ValueError:
                    pass
            v = _text(gca, "max_size")
            if v is not None:
                try:
                    entry["max_size"] = float(v)
                except ValueError:
                    pass
            hi = gca.find("high_inflation")
            if hi is not None:
                infl = _parse_inflation(hi)
                if infl:
                    entry["high_inflation"] = infl
            lo = gca.find("low_inflation")
            if lo is not None:
                infl = _parse_inflation(lo)
                if infl:
                    entry["low_inflation"] = infl
            if entry:
                results.append(entry)
    return results


def extract_regions_xml(root: ET.Element) -> List[Dict]:
    results: List[Dict] = []
    for elem in root.iter():
        if _strip_ns(elem.tag) != "region":
            continue
        entry: Dict = {}
        name = _text(elem, "name")
        if name:
            entry["name"] = name
        v = _text(elem, "active")
        if v is not None:
            entry["active"] = v.lower() == "true"
        v = _text(elem, "hidden")
        if v is not None:
            entry["hidden"] = v.lower() == "true"
        pos = elem.find("position")
        if pos is not None:
            entry["position"] = [
                _float_text(pos, "x"),
                _float_text(pos, "y"),
                _float_text(pos, "z"),
            ]
        size = elem.find("size")
        if size is not None:
            entry["size"] = [
                _float_text(size, "x"),
                _float_text(size, "y"),
                _float_text(size, "z"),
            ]
        for tag in ("x_grid_constraint", "y_grid_constraint",
                     "z_grid_constraint", "all_grid_constraint"):
            v = _text(elem, tag)
            if v:
                entry[tag] = v
        v = _text(elem, "localized_grid")
        if v is not None:
            entry["localized_grid"] = v.lower() == "true"
        if entry:
            results.append(entry)
    return results


def extract_object_constraints_xml(root: ET.Element) -> List[Dict]:
    results: List[Dict] = []
    geometry_tags = {
        "cuboid", "source", "fan", "resistance", "prism", "tet",
        "inverted_tet", "sloping_block", "cylinder", "enclosure",
        "fixed_flow", "heat_transfer_coeff", "radiation_surface",
        "heatsink", "pcb", "cooler",
    }
    for elem in root.iter():
        tag = _strip_ns(elem.tag)
        if tag not in geometry_tags:
            continue
        has_constraint = False
        constraint_entry: Dict = {}
        name = _text(elem, "name")
        if not name:
            continue
        for ctag in ("x_grid_constraint", "y_grid_constraint",
                      "z_grid_constraint", "all_grid_constraint"):
            v = _text(elem, ctag)
            if v:
                constraint_entry[ctag] = v
                has_constraint = True
        v = _text(elem, "localized_grid")
        if v is not None:
            constraint_entry["localized_grid"] = v.lower() == "true"
        if has_constraint:
            constraint_entry["target_names"] = [name]
            constraint_entry["target_tags"] = [tag]
            results.append(constraint_entry)
    return results


def extract_all_xml(root: ET.Element) -> Dict:
    return {
        "grid_constraints": extract_grid_constraints_xml(root),
        "object_constraints": extract_object_constraints_xml(root),
        "regions": extract_regions_xml(root),
    }


# ============================================================================
# PDML 二进制提取
# ============================================================================

def extract_all_pdml(filepath: str) -> Dict:
    """从 PDML 二进制文件提取 region 和 grid constraint 信息"""
    import os
    import sys
    # 确保项目根目录在 sys.path 中
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if project_root not in sys.path:
        sys.path.insert(0, project_root)
    from pdml_tools.pdml_to_floxml_converter import PDMLBinaryReader

    reader = PDMLBinaryReader(filepath)
    data = reader.read()

    def _round(v, digits=10):
        """Round floats from binary to remove IEEE 754 noise"""
        return round(v, digits) if isinstance(v, float) else v

    # 1. Grid Constraints
    gc_list = []
    for gc in data.grid_constraints:
        entry: Dict = {"name": gc.name}
        entry["enable_min_cell_size"] = gc.enable_min_cell_size
        entry["min_cell_size"] = _round(gc.min_cell_size)
        entry["number_cells_control"] = gc.number_cells_control
        entry["min_number"] = gc.min_number
        if gc.high_inflation_inflation_size > 0:
            entry["high_inflation"] = {
                "inflation_type": gc.high_inflation_inflation_type,
                "inflation_size": _round(gc.high_inflation_inflation_size),
                "number_cells_control": gc.high_inflation_number_cells_control,
                "min_number": gc.high_inflation_min_number,
            }
        gc_list.append(entry)

    # 2. Regions — 遍历 geometry tree
    region_list = []
    obj_constraint_list = []

    def _visit_node(node, parent_path=()):
        # 提取 region
        if node.node_type == "region":
            r_entry: Dict = {"name": node.name}
            r_entry["active"] = node.active
            if node.hidden:
                r_entry["hidden"] = True
            if node.position:
                r_entry["position"] = [_round(v) for v in node.position]
            if node.size:
                r_entry["size"] = [_round(v) for v in node.size]
            # 从 post_elements 中提取 grid constraint 引用
            for frag in node.post_elements:
                if frag.tag in ("all_grid_constraint", "x_grid_constraint",
                                "y_grid_constraint", "z_grid_constraint"):
                    r_entry[frag.tag] = frag.text
            if node.localized_grid is not None:
                r_entry["localized_grid"] = node.localized_grid
            region_list.append(r_entry)
        else:
            # 提取非 region 对象上的 grid constraint
            gc_refs = {}
            for frag in node.post_elements:
                if frag.tag in ("all_grid_constraint", "x_grid_constraint",
                                "y_grid_constraint", "z_grid_constraint"):
                    gc_refs[frag.tag] = frag.text
            if gc_refs and node.name:
                oc_entry: Dict = {"target_names": [node.name], "target_tags": [node.node_type]}
                oc_entry.update(gc_refs)
                if node.localized_grid is not None:
                    oc_entry["localized_grid"] = node.localized_grid
                obj_constraint_list.append(oc_entry)

        # 递归子节点
        for child in node.children:
            _visit_node(child, parent_path + (node.name,))

    if data.geometry:
        _visit_node(data.geometry)

    return {
        "grid_constraints": gc_list,
        "object_constraints": obj_constraint_list,
        "regions": region_list,
    }


# ============================================================================
# 自动检测格式 & 公共接口
# ============================================================================

def is_binary_pdml(filepath: str) -> bool:
    """检测文件是否为 PDML 二进制格式 (#FFFB)"""
    try:
        with open(filepath, "rb") as f:
            header = f.read(200)
        # XML 文件以 <?xml 或直接 <tag> 开头
        stripped = header.lstrip()
        if stripped[:5] == b'<?xml' or stripped[:1] == b'<':
            return False
        # PDML 二进制：首行以 #FFFB 开头 (Simcenter Flotherm 2504+)
        # 或以 "PDML" 开头 (旧版本)
        newline_pos = header.find(b'\n')
        if newline_pos > 0:
            first_line = header[:newline_pos]
            if first_line.startswith(b'#FFFB') or first_line.startswith(b'PDML'):
                return True
            if b'Flotherm' in first_line or b'FloTHERM' in first_line:
                return True
        # 兜底：文件中无 <?xml 且扩展名是 .pdml → 视为二进制
        if b'<?xml' not in header and filepath.lower().endswith('.pdml'):
            return True
        return False
    except Exception:
        return False


def extract_all(filepath: str) -> Dict:
    """自动检测格式并提取"""
    if is_binary_pdml(filepath):
        return extract_all_pdml(filepath)
    else:
        tree = ET.parse(filepath)
        return extract_all_xml(tree.getroot())


# ============================================================================
# 摘要输出
# ============================================================================

def print_summary(config: Dict) -> None:
    gc_list = config.get("grid_constraints", [])
    oc_list = config.get("object_constraints", [])
    region_list = config.get("regions", [])

    print("=" * 60)
    print("Volume Region / Grid Constraint Extract Results")
    print("=" * 60)

    print(f"\nGrid Constraints ({len(gc_list)}):")
    if gc_list:
        for gc in gc_list:
            name = gc.get("name", "<unnamed>")
            ctrl = gc.get("number_cells_control", "?")
            print(f"  - {name}: {ctrl}", end="")
            if "min_number" in gc:
                print(f", min_number={gc['min_number']}", end="")
            if "max_size" in gc:
                print(f", max_size={gc['max_size']}", end="")
            if "high_inflation" in gc:
                hi = gc["high_inflation"]
                print(f", high_inflation({hi.get('inflation_type', '?')})", end="")
            print()
    else:
        print("  (none)")

    print(f"\nObject Constraints ({len(oc_list)}):")
    if oc_list:
        for oc in oc_list:
            names = oc.get("target_names", [])
            tags = oc.get("target_tags", [])
            gc_ref = oc.get("all_grid_constraint") or oc.get("x_grid_constraint", "")
            print(f"  - {', '.join(names)} [{', '.join(tags)}] -> {gc_ref}")
    else:
        print("  (none)")

    print(f"\nVolume Regions ({len(region_list)}):")
    if region_list:
        for r in region_list:
            name = r.get("name", "<unnamed>")
            pos = r.get("position", [0, 0, 0])
            size = r.get("size", [0, 0, 0])
            gc_ref = r.get("all_grid_constraint") or r.get("x_grid_constraint", "")
            hidden = "(hidden) " if r.get("hidden") else ""
            print(f"  - {hidden}{name}: pos={pos}, size={size}, grid={gc_ref}")
    else:
        print("  (none)")

    print("\n" + "=" * 60)


# ============================================================================
# CLI
# ============================================================================

def main() -> int:
    parser = argparse.ArgumentParser(
        description="Extract Volume Regions and Grid Constraints from PDML/FloXML to JSON",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python pdml_tools/pdml_extract_regions.py model.pdml -o regions.json
  python pdml_tools/pdml_extract_regions.py model.xml -o regions.json
  python pdml_tools/pdml_extract_regions.py model.pdml --summary

Output JSON can be used directly:
  python floxml_tools/floxml_add_volume_regions.py input.xml --config regions.json -o output.xml
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
        print("Hint: If this is a binary PDML file, it will be auto-detected.", file=sys.stderr)
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
