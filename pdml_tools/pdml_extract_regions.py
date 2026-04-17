#!/usr/bin/env python3
"""
从 PDML / FloXML 文件中提取 Volume Region 和 Grid Constraint 信息，
输出为 JSON 格式，可直接作为 floxml_add_volume_regions.py 的输入配置。

支持:
  - FloXML (.xml / .floxml) — XML 文本格式，直接解析
  - PDML (.pdml) — FloTHERM 二进制格式，先转 FloXML 再提取

用法:
    python pdml_tools/pdml_extract_regions.py model.pdml -o regions.json
    python pdml_tools/pdml_extract_regions.py model.xml -o regions.json
    python pdml_tools/pdml_extract_regions.py model.pdml  # 打印摘要
"""

import argparse
import io
import json
import os
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, List, Optional, Any


# ============================================================================
# 自动检测格式
# ============================================================================

def is_binary_pdml(filepath: str) -> bool:
    """检测文件是否为 PDML 二进制格式 (#FFFB)"""
    try:
        with open(filepath, "rb") as f:
            header = f.read(200)
        stripped = header.lstrip()
        if stripped[:5] == b'<?xml' or stripped[:1] == b'<':
            return False
        newline_pos = header.find(b'\n')
        if newline_pos > 0:
            first_line = header[:newline_pos]
            if first_line.startswith(b'#FFFB') or first_line.startswith(b'PDML'):
                return True
            if b'Flotherm' in first_line or b'FloTHERM' in first_line:
                return True
        if b'<?xml' not in header and filepath.lower().endswith('.pdml'):
            return True
        return False
    except Exception:
        return False


# ============================================================================
# FloXML 解析
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


def extract_grid_constraints(root: ET.Element) -> List[Dict]:
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


def _get_elem_position(elem: ET.Element) -> List[float]:
    """从元素中提取 position"""
    pos = elem.find("position")
    if pos is not None:
        return [_float_text(pos, "x"), _float_text(pos, "y"), _float_text(pos, "z")]
    return [0.0, 0.0, 0.0]


def _get_elem_size(elem: ET.Element) -> Optional[List[float]]:
    """从元素中提取 size"""
    size = elem.find("size")
    if size is not None:
        return [_float_text(size, "x"), _float_text(size, "y"), _float_text(size, "z")]
    return None


def extract_regions(root: ET.Element) -> List[Dict]:
    """
    提取所有 region，计算全局坐标（累积父级 assembly 偏移）。

    FloXML geometry 是层级结构：assembly 包含子 geometry，子元素 position 是局部的。
    这里递归遍历树，将 region 的 position 转为全局坐标。
    同时保留 parent_assembly 和 local_position 供参考。
    """
    results: List[Dict] = []

    def _visit(parent: ET.Element, offset: List[float], assembly_path: List[str]):
        for elem in parent:
            tag = _strip_ns(elem.tag)
            name = _text(elem, "name") or ""
            local_pos = _get_elem_position(elem)

            # 计算全局坐标
            global_pos = [offset[i] + local_pos[i] for i in range(3)]

            if tag == "region":
                entry: Dict = {"name": name}
                v = _text(elem, "active")
                if v is not None:
                    entry["active"] = v.lower() == "true"
                v = _text(elem, "hidden")
                if v is not None:
                    entry["hidden"] = v.lower() == "true"

                # 全局坐标
                entry["position"] = global_pos

                size = _get_elem_size(elem)
                if size:
                    entry["size"] = size

                # 如果在 assembly 内部，记录父级信息和局部坐标
                if assembly_path:
                    entry["parent_assembly"] = assembly_path[-1]
                    entry["local_position"] = local_pos

                for ctag in ("x_grid_constraint", "y_grid_constraint",
                             "z_grid_constraint", "all_grid_constraint"):
                    v = _text(elem, ctag)
                    if v:
                        entry[ctag] = v
                v = _text(elem, "localized_grid")
                if v is not None:
                    entry["localized_grid"] = v.lower() == "true"
                if entry:
                    results.append(entry)

            # 如果是 assembly，递归进入其 <geometry> 子节点
            if tag == "assembly":
                child_geom = elem.find("geometry")
                if child_geom is not None:
                    _visit(child_geom, global_pos, assembly_path + [name])
            # 非 assembly 也可能有 <geometry>（如 enclosure）
            elif tag not in ("region",):
                child_geom = elem.find("geometry")
                if child_geom is not None:
                    _visit(child_geom, global_pos, assembly_path)

    # 找到根 <geometry>
    geometry = root.find("geometry")
    if geometry is not None:
        _visit(geometry, [0.0, 0.0, 0.0], [])

    return results


def extract_object_constraints(root: ET.Element) -> List[Dict]:
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


def extract_all_from_xml(root: ET.Element) -> Dict:
    """从 FloXML ElementTree 提取所有 region 和 grid constraint 信息"""
    return {
        "grid_constraints": extract_grid_constraints(root),
        "object_constraints": extract_object_constraints(root),
        "regions": extract_regions(root),
    }


# ============================================================================
# 入口：自动检测 + PDML 转换
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
