#!/usr/bin/env python3
"""
FloXML 网格注入工具

从源 FloXML 项目文件中提取网格设置（system_grid、patches、grid_constraints），
注入到目标 FloXML 文件（通常是 ECXML 转换生成的 FloXML）。

使用场景：
  用户有同一个项目的 FloXML 和 ECXML，希望将项目 FloXML 中的网格设置
  应用到 ECXML 转换后的 FloXML 中。

用法：
  # 基本用法：源 FloXML + 目标 FloXML
  python -m floxml_tools.inject_grid_from_floxml project.floxml target.xml -o output.xml

  # 一步到位：ECXML → FloXML + 注入网格
  python -m floxml_tools.inject_grid_from_floxml project.floxml --ecxml model.ecxml -o output.xml

  # 仅注入网格约束（不替换 system_grid）
  python -m floxml_tools.inject_grid_from_floxml project.floxml target.xml -o output.xml --constraints-only

  # 仅注入 system_grid（不注入网格约束）
  python -m floxml_tools.inject_grid_from_floxml project.floxml target.xml -o output.xml --grid-only
"""

import xml.etree.ElementTree as ET
from xml.dom import minidom
import argparse
import sys
import os
from pathlib import Path
from typing import Optional
from copy import deepcopy


def _strip_ns(tag: str) -> str:
    """去除命名空间前缀"""
    if '}' in tag:
        return tag.split('}', 1)[1]
    return tag


def _find_child(parent: ET.Element, tag: str) -> Optional[ET.Element]:
    """查找子元素（忽略命名空间）"""
    child = parent.find(tag)
    if child is not None:
        return child
    for c in parent:
        if _strip_ns(c.tag) == tag:
            return c
    return None


def _find_or_none(root: ET.Element, *path) -> Optional[ET.Element]:
    """沿路径查找元素，任一级不存在返回 None"""
    current = root
    for tag in path:
        found = _find_child(current, tag)
        if found is None:
            return None
        current = found
    return current


def _remove_child(parent: ET.Element, tag: str) -> bool:
    """删除指定标签的子元素"""
    child = _find_child(parent, tag)
    if child is not None:
        parent.remove(child)
        return True
    return False


def inject_grid(source_path: str, target_path: str, output_path: str,
                grid_only: bool = False, constraints_only: bool = False,
                verbose: bool = False) -> None:
    """
    从源 FloXML 提取网格设置并注入到目标 FloXML。

    Args:
        source_path: 源 FloXML 文件路径（包含网格设置的项目文件）
        target_path: 目标 FloXML 文件路径（通常是 ECXML 转换结果）
        output_path: 输出文件路径
        grid_only: 仅注入 system_grid + patches，不注入 grid_constraints
        constraints_only: 仅注入 grid_constraints，不替换 system_grid
        verbose: 详细输出
    """
    # 解析源文件
    src_tree = ET.parse(source_path)
    src_root = src_tree.getroot()

    # 解析目标文件
    tgt_tree = ET.parse(target_path)
    tgt_root = tgt_tree.getroot()

    # --- 注入 <grid>（system_grid + patches）---
    if not constraints_only:
        src_grid = _find_child(src_root, 'grid')
        if src_grid is not None:
            # 删除目标中已有的 grid
            _remove_child(tgt_root, 'grid')
            # 深拷贝源 grid 到目标
            tgt_root.insert(0, deepcopy(src_grid))
            if verbose:
                _print_grid_summary(src_grid)
            print(f"[OK] 已注入 <grid> (system_grid + patches)")
        else:
            print("[WARN] 源文件中未找到 <grid> 元素")

    # --- 注入 <grid_constraints> ---
    if not grid_only:
        src_gc = _find_child(src_root, 'grid_constraints')
        if src_gc is not None:
            # grid_constraints 在 <attributes> 下
            tgt_attrs = _find_child(tgt_root, 'attributes')
            if tgt_attrs is None:
                # 如果没有 attributes，直接放在根元素下
                _remove_child(tgt_root, 'grid_constraints')
                tgt_root.append(deepcopy(src_gc))
            else:
                _remove_child(tgt_attrs, 'grid_constraints')
                tgt_attrs.append(deepcopy(src_gc))

            constraint_count = len([c for c in src_gc if _strip_ns(c.tag) == 'grid_constraint_att'])
            print(f"[OK] 已注入 <grid_constraints> ({constraint_count} 个约束)")
        else:
            # 也检查 attributes 下的 grid_constraints
            src_attrs = _find_child(src_root, 'attributes')
            if src_attrs is not None:
                src_gc = _find_child(src_attrs, 'grid_constraints')
            if src_gc is not None:
                tgt_attrs = _find_child(tgt_root, 'attributes')
                if tgt_attrs is None:
                    _remove_child(tgt_root, 'grid_constraints')
                    tgt_root.append(deepcopy(src_gc))
                else:
                    _remove_child(tgt_attrs, 'grid_constraints')
                    tgt_attrs.append(deepcopy(src_gc))
                constraint_count = len([c for c in src_gc if _strip_ns(c.tag) == 'grid_constraint_att'])
                print(f"[OK] 已注入 <grid_constraints> ({constraint_count} 个约束，来自 <attributes>)")
            else:
                print("[WARN] 源文件中未找到 <grid_constraints> 元素")

    # 保存
    _save_xml(tgt_root, output_path)
    print(f"[OK] 已保存: {output_path}")


def _print_grid_summary(grid: ET.Element) -> None:
    """打印网格摘要"""
    sg = _find_child(grid, 'system_grid')
    if sg is None:
        return

    for axis_tag in ('x_grid', 'y_grid', 'z_grid'):
        axis = _find_child(sg, axis_tag)
        if axis is None:
            continue
        parts = []
        for child in axis:
            tag = _strip_ns(child.tag)
            if child.text:
                parts.append(f"{tag}={child.text.strip()}")
        print(f"  {axis_tag}: {', '.join(parts)}")

    patches = _find_child(sg, 'patches')
    if patches is not None:
        patch_count = len(list(patches))
        print(f"  patches: {patch_count} 个网格分区")


def _save_xml(root: ET.Element, output_path: str) -> None:
    """保存 XML 文件（带格式化）"""
    rough_string = ET.tostring(root, encoding='unicode')
    reparsed = minidom.parseString(rough_string)
    pretty_xml = reparsed.toprettyxml(indent="  ")
    # 移除多余空行
    lines = [line for line in pretty_xml.split('\n') if line.strip()]
    pretty_xml = '\n'.join(lines)

    os.makedirs(os.path.dirname(output_path) or '.', exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(pretty_xml)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        description="从源 FloXML 提取网格设置并注入到目标 FloXML",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 注入网格到已有 FloXML
  python -m floxml_tools.inject_grid_from_floxml project.floxml target.xml -o output.xml

  # ECXML → FloXML + 注入网格（一步到位）
  python -m floxml_tools.inject_grid_from_floxml project.floxml --ecxml model.ecxml -o output.xml

  # 仅注入 grid_constraints
  python -m floxml_tools.inject_grid_from_floxml project.floxml target.xml -o output.xml --constraints-only

  # 仅替换 system_grid
  python -m floxml_tools.inject_grid_from_floxml project.floxml target.xml -o output.xml --grid-only
        """
    )

    parser.add_argument("source", type=Path,
                        help="源 FloXML 文件（包含网格设置的项目文件）")
    parser.add_argument("target", nargs='?', type=Path, default=None,
                        help="目标 FloXML 文件（ECXML 转换结果）。使用 --ecxml 时可省略")
    parser.add_argument("-o", "--output", type=Path, required=True,
                        help="输出 FloXML 文件路径")

    # 组合模式：一步完成 ECXML→FloXML + 注入网格
    parser.add_argument("--ecxml", type=Path,
                        help="ECXML 输入文件（自动转换后再注入网格）")
    parser.add_argument("--padding-ratio", type=float, default=0.1,
                        help="ECXML 转换 padding 比例 (默认: 0.1)")
    parser.add_argument("--ambient-temp", type=float, default=300.0,
                        help="环境温度 K (默认: 300)")

    # 注入选项
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--grid-only", action="store_true",
                       help="仅注入 system_grid + patches")
    group.add_argument("--constraints-only", action="store_true",
                       help="仅注入 grid_constraints")

    parser.add_argument("-v", "--verbose", action="store_true",
                        help="详细输出")

    args = parser.parse_args(list(argv) if argv else None)

    # 确定目标文件
    target_path = args.target

    if args.ecxml:
        # 先将 ECXML 转换为 FloXML 到临时文件
        from .ecxml_to_floxml_converter import ECXMLToFloXMLConverter, ConversionConfig
        config = ConversionConfig(
            padding_ratio=args.padding_ratio,
            ambient_temp=args.ambient_temp,
        )
        converter = ECXMLToFloXMLConverter(config)
        floxml_root = converter.convert(str(args.ecxml))

        # 写临时文件
        tmp_path = str(args.output) + ".tmp"
        _save_xml(floxml_root, tmp_path)
        target_path = Path(tmp_path)
        print(f"[OK] ECXML 已转换为 FloXML")
    elif target_path is None:
        parser.error("需要指定 target 或使用 --ecxml 参数")

    # 执行注入
    inject_grid(
        source_path=str(args.source),
        target_path=str(target_path),
        output_path=str(args.output),
        grid_only=args.grid_only,
        constraints_only=args.constraints_only,
        verbose=args.verbose,
    )

    # 清理临时文件
    if args.ecxml:
        tmp_path = str(args.output) + ".tmp"
        if os.path.exists(tmp_path):
            os.remove(tmp_path)

    return 0


if __name__ == "__main__":
    sys.exit(main())
