#!/usr/bin/env python3
"""
PDML XPath 批量修改工具

示例:
  python pdml_xpath_editor.py model.pdml \
    --set-text "//d:Power[@name='CPU']" "35.5" \
    --set-attr "//d:Component[@name='U1']" material "AL6061" \
    --in-place
"""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path
from typing import Dict, List, Tuple

try:
    from lxml import etree
except ImportError:
    print("[ERROR] 需要安装 lxml: pip install lxml", file=sys.stderr)
    raise


def parse_ns_args(items: List[str]) -> Dict[str, str]:
    namespaces: Dict[str, str] = {}
    for item in items:
        if "=" not in item:
            raise ValueError(f"命名空间参数格式错误: {item}，应为 prefix=uri")
        prefix, uri = item.split("=", 1)
        prefix = prefix.strip()
        uri = uri.strip()
        if not prefix or not uri:
            raise ValueError(f"命名空间参数格式错误: {item}，应为 prefix=uri")
        namespaces[prefix] = uri
    return namespaces


def build_xpath_namespaces(root: etree._Element, extra_ns: Dict[str, str]) -> Dict[str, str]:
    namespaces: Dict[str, str] = {}
    for prefix, uri in (root.nsmap or {}).items():
        if not uri:
            continue
        if prefix is None:
            namespaces["d"] = uri
        else:
            namespaces[prefix] = uri
    namespaces.update(extra_ns)
    return namespaces


def apply_text_update(
    root: etree._Element,
    xpath: str,
    value: str,
    namespaces: Dict[str, str],
) -> Tuple[int, List[str]]:
    nodes = root.xpath(xpath, namespaces=namespaces)
    changes = 0
    detail: List[str] = []
    for node in nodes:
        if not isinstance(node, etree._Element):
            continue
        old_value = node.text or ""
        if old_value != value:
            node.text = value
            changes += 1
            detail.append(f"text: <{node.tag}> '{old_value}' -> '{value}'")
    return len(nodes), detail


def apply_attr_update(
    root: etree._Element,
    xpath: str,
    attr_name: str,
    value: str,
    namespaces: Dict[str, str],
) -> Tuple[int, List[str]]:
    nodes = root.xpath(xpath, namespaces=namespaces)
    changes = 0
    detail: List[str] = []
    for node in nodes:
        if not isinstance(node, etree._Element):
            continue
        old_value = node.get(attr_name, "")
        if old_value != value:
            node.set(attr_name, value)
            changes += 1
            detail.append(f"attr: <{node.tag}> @{attr_name} '{old_value}' -> '{value}'")
    return len(nodes), detail


def main() -> int:
    parser = argparse.ArgumentParser(description="按 XPath 批量修改 PDML/XML 文件")
    parser.add_argument("input", help="输入 PDML/XML 文件路径")
    parser.add_argument(
        "-o",
        "--output",
        help="输出文件路径（不指定时需搭配 --in-place）",
    )
    parser.add_argument(
        "--in-place",
        action="store_true",
        help="原地修改输入文件",
    )
    parser.add_argument(
        "--backup-suffix",
        default=".bak",
        help="原地修改时的备份后缀（默认: .bak）",
    )
    parser.add_argument(
        "--set-text",
        nargs=2,
        metavar=("XPATH", "VALUE"),
        action="append",
        default=[],
        help="批量设置匹配节点的 text，可重复",
    )
    parser.add_argument(
        "--set-attr",
        nargs=3,
        metavar=("XPATH", "ATTR", "VALUE"),
        action="append",
        default=[],
        help="批量设置匹配节点的属性，可重复",
    )
    parser.add_argument(
        "--ns",
        action="append",
        default=[],
        metavar="PREFIX=URI",
        help="额外 XPath 命名空间映射，可重复",
    )
    parser.add_argument(
        "--allow-empty-match",
        action="store_true",
        help="允许某条 XPath 未匹配到节点（默认未匹配即报错）",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="仅打印修改计划，不写回文件",
    )

    args = parser.parse_args()

    if not args.set_text and not args.set_attr:
        print("[ERROR] 至少需要一条 --set-text 或 --set-attr 规则", file=sys.stderr)
        return 2

    input_path = Path(args.input).expanduser().resolve()
    if not input_path.exists():
        print(f"[ERROR] 输入文件不存在: {input_path}", file=sys.stderr)
        return 2

    if not args.in_place and not args.output and not args.dry_run:
        print("[ERROR] 请使用 --in-place 或 --output 指定写入目标", file=sys.stderr)
        return 2

    parser_xml = etree.XMLParser(remove_blank_text=False, recover=False)
    tree = etree.parse(str(input_path), parser_xml)
    root = tree.getroot()

    try:
        extra_ns = parse_ns_args(args.ns)
    except ValueError as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        return 2
    namespaces = build_xpath_namespaces(root, extra_ns)

    if "d" in namespaces:
        print(f"[INFO] 检测到默认命名空间，可在 XPath 使用前缀 d: {namespaces['d']}")

    total_changed = 0
    errors: List[str] = []

    for xpath, value in args.set_text:
        matched, changes = apply_text_update(root, xpath, value, namespaces)
        if matched == 0 and not args.allow_empty_match:
            errors.append(f"XPath 未匹配: {xpath}")
        total_changed += len(changes)
        for line in changes[:10]:
            print(f"[CHANGE] {line}")
        if len(changes) > 10:
            print(f"[CHANGE] ... 其余 {len(changes) - 10} 条省略")

    for xpath, attr_name, value in args.set_attr:
        matched, changes = apply_attr_update(root, xpath, attr_name, value, namespaces)
        if matched == 0 and not args.allow_empty_match:
            errors.append(f"XPath 未匹配: {xpath}")
        total_changed += len(changes)
        for line in changes[:10]:
            print(f"[CHANGE] {line}")
        if len(changes) > 10:
            print(f"[CHANGE] ... 其余 {len(changes) - 10} 条省略")

    if errors:
        for err in errors:
            print(f"[ERROR] {err}", file=sys.stderr)
        print("[ERROR] 存在未匹配规则，未写入文件。可使用 --allow-empty-match 放宽。", file=sys.stderr)
        return 3

    print(f"[INFO] 总修改数: {total_changed}")
    if args.dry_run:
        print("[INFO] dry-run 模式，未写入文件")
        return 0

    if args.in_place:
        output_path = input_path
        backup_path = input_path.with_suffix(input_path.suffix + args.backup_suffix)
        shutil.copy2(input_path, backup_path)
        print(f"[INFO] 已创建备份: {backup_path}")
    else:
        output_path = Path(args.output).expanduser().resolve()
        output_path.parent.mkdir(parents=True, exist_ok=True)

    tree.write(
        str(output_path),
        encoding="utf-8",
        xml_declaration=True,
        pretty_print=False,
    )
    print(f"[INFO] 已写入: {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
