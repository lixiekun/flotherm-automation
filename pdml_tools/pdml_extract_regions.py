#!/usr/bin/env python3
"""
从 PDML / FloXML 文件中提取 Volume Region 和 Grid Constraint 信息，
输出为 JSON 格式，可直接作为 floxml_add_volume_regions.py 的输入配置。

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
from typing import Dict, List, Optional, Any


def _strip_ns(tag: str) -> str:
    """去除 XML 命名空间前缀"""
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
    """解析 high_inflation / low_inflation"""
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
    """
    从 <attributes><grid_constraints> 中提取所有 grid_constraint_att。
    """
    results: List[Dict] = []

    # 查找 <grid_constraints> — 可能在 <attributes> 下
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

            # high_inflation
            hi = gca.find("high_inflation")
            if hi is not None:
                infl = _parse_inflation(hi)
                if infl:
                    entry["high_inflation"] = infl

            # low_inflation
            lo = gca.find("low_inflation")
            if lo is not None:
                infl = _parse_inflation(lo)
                if infl:
                    entry["low_inflation"] = infl

            if entry:
                results.append(entry)

    return results


def extract_regions(root: ET.Element) -> List[Dict]:
    """
    从 <geometry> 中提取所有 <region> 元素，输出为 JSON 配置格式。

    注意：position 在 PDML 中的参考系可能不同于 FloXML 目标模型，
    因此位置可能需要手动调整。但 name 和 size 是准确的。
    """
    results: List[Dict] = []

    for elem in root.iter():
        if _strip_ns(elem.tag) != "region":
            continue

        entry: Dict = {}

        # 名称
        name = _text(elem, "name")
        if name:
            entry["name"] = name

        # active
        v = _text(elem, "active")
        if v is not None:
            entry["active"] = v.lower() == "true"

        # hidden
        v = _text(elem, "hidden")
        if v is not None:
            entry["hidden"] = v.lower() == "true"

        # position
        pos = elem.find("position")
        if pos is not None:
            px = _float_text(pos, "x")
            py = _float_text(pos, "y")
            pz = _float_text(pos, "z")
            entry["position"] = [px, py, pz]

        # size
        size = elem.find("size")
        if size is not None:
            sx = _float_text(size, "x")
            sy = _float_text(size, "y")
            sz = _float_text(size, "z")
            entry["size"] = [sx, sy, sz]

        # grid constraints references
        for tag in ("x_grid_constraint", "y_grid_constraint",
                     "z_grid_constraint", "all_grid_constraint"):
            v = _text(elem, tag)
            if v:
                entry[tag] = v

        # localized_grid
        v = _text(elem, "localized_grid")
        if v is not None:
            entry["localized_grid"] = v.lower() == "true"

        if entry:
            results.append(entry)

    return results


def extract_object_constraints(root: ET.Element) -> List[Dict]:
    """
    从 geometry 中提取非 region 对象上绑定的 grid constraint 信息。
    即哪些 cuboid/source/fan 等对象直接引用了 grid constraint。
    """
    results: List[Dict] = []
    geometry_tags = {
        "cuboid", "source", "fan", "resistance", "prism", "tet",
        "inverted_tet", "sloping_block", "cylinder", "enclosure",
        "fixed_flow", "heat_transfer_coeff", "radiation_surface",
    }

    for elem in root.iter():
        tag = _strip_ns(elem.tag)
        if tag not in geometry_tags:
            continue

        # 检查是否有 grid constraint 引用
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


def extract_all(root: ET.Element) -> Dict:
    """提取所有 volume region 和 grid constraint 信息"""
    return {
        "grid_constraints": extract_grid_constraints(root),
        "object_constraints": extract_object_constraints(root),
        "regions": extract_regions(root),
    }


def print_summary(config: Dict) -> None:
    """打印提取结果摘要"""
    gc_list = config.get("grid_constraints", [])
    oc_list = config.get("object_constraints", [])
    region_list = config.get("regions", [])

    print("=" * 60)
    print("PDML Volume Region / Grid Constraint 提取结果")
    print("=" * 60)

    # Grid Constraints
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
        print("  (无)")

    # Object Constraints
    print(f"\nObject Constraints ({len(oc_list)}):")
    if oc_list:
        for oc in oc_list:
            names = oc.get("target_names", [])
            tags = oc.get("target_tags", [])
            gc_ref = oc.get("all_grid_constraint") or oc.get("x_grid_constraint", "")
            print(f"  - {', '.join(names)} [{', '.join(tags)}] -> {gc_ref}")
    else:
        print("  (无)")

    # Regions
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
        print("  (无)")

    print("\n" + "=" * 60)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="从 PDML/FloXML 提取 Volume Region 和 Grid Constraint 到 JSON",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python pdml_tools/pdml_extract_regions.py model.pdml -o regions.json
  python pdml_tools/pdml_extract_regions.py model.pdml --summary
  python pdml_tools/pdml_extract_regions.py model.xml -o regions.json

输出 JSON 可直接用于:
  python floxml_tools/floxml_add_volume_regions.py input.xml --config regions.json -o output.xml
        """,
    )
    parser.add_argument("input", help="输入 PDML 或 FloXML 文件")
    parser.add_argument("-o", "--output", help="输出 JSON 文件路径")
    parser.add_argument("--summary", action="store_true", help="打印摘要信息")

    args = parser.parse_args()

    input_path = Path(args.input)
    if not input_path.exists():
        print(f"[ERROR] 文件不存在: {input_path}", file=sys.stderr)
        return 1

    try:
        tree = ET.parse(str(input_path))
        root = tree.getroot()
    except ET.ParseError as e:
        print(f"[ERROR] XML 解析失败: {e}", file=sys.stderr)
        return 1

    config = extract_all(root)

    # 打印摘要
    if args.summary or not args.output:
        print_summary(config)

    # 输出 JSON
    if args.output:
        output_path = Path(args.output)
        with output_path.open("w", encoding="utf-8") as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        print(f"[OK] 已输出到: {output_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
