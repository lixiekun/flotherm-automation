#!/usr/bin/env python3
"""
PDML 网格信息探测工具（只读，不修改文件）

用途:
1. 判断 PDML/XML 中是否存在网格相关信息
2. 输出命中的节点路径、标签、属性和值样例
3. 给出后续可用于修改的 XPath 建议

示例:
  python pdml_grid_inspector.py model.pdml
  python pdml_grid_inspector.py model.pdml --max-samples 40
  python pdml_grid_inspector.py model.pdml --keywords "grid,mesh,cell,refine,spacing,resolution"
"""

from __future__ import annotations

import argparse
import re
import sys
import xml.etree.ElementTree as ET
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Tuple


DEFAULT_KEYWORDS = ["grid", "mesh", "cell", "refine", "spacing", "resolution", "voxel", "lattice"]


@dataclass
class MatchRecord:
    path: str
    tag: str
    reasons: List[str]
    attrs_preview: str
    text_preview: str


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="探测 PDML/XML 中的网格相关信息")
    parser.add_argument("input", help="输入 PDML/XML 文件")
    parser.add_argument(
        "--keywords",
        default=",".join(DEFAULT_KEYWORDS),
        help="逗号分隔关键词，默认: grid,mesh,cell,refine,spacing,resolution,voxel,lattice",
    )
    parser.add_argument(
        "--max-samples",
        type=int,
        default=25,
        help="最多打印多少条命中样例（默认 25）",
    )
    parser.add_argument(
        "--text-limit",
        type=int,
        default=80,
        help="文本/属性预览最大长度（默认 80）",
    )
    return parser


def normalize_keywords(value: str) -> List[str]:
    items = [part.strip().lower() for part in value.split(",")]
    dedup: List[str] = []
    for item in items:
        if item and item not in dedup:
            dedup.append(item)
    return dedup


def strip_ns(tag: str) -> str:
    if "}" in tag:
        return tag.split("}", 1)[1]
    return tag


def truncate(text: str, limit: int) -> str:
    if len(text) <= limit:
        return text
    return text[: limit - 3] + "..."


def detect_namespaces(path: Path) -> Dict[str, str]:
    namespaces: Dict[str, str] = {}
    for _, elem in ET.iterparse(str(path), events=("start-ns",)):
        prefix, uri = elem
        key = prefix if prefix else "(default)"
        if key not in namespaces:
            namespaces[key] = uri
    return namespaces


def any_keyword_hit(text: str, keywords: Iterable[str]) -> List[str]:
    lowered = text.lower()
    hits = [kw for kw in keywords if kw in lowered]
    return hits


def inspect_element(
    elem: ET.Element,
    path: str,
    keywords: List[str],
    text_limit: int,
) -> Tuple[MatchRecord | None, Counter]:
    reason_counter: Counter = Counter()
    reasons: List[str] = []

    local_tag = strip_ns(elem.tag)
    tag_hits = any_keyword_hit(local_tag, keywords)
    if tag_hits:
        reasons.append(f"tag={local_tag}")
        for hit in tag_hits:
            reason_counter[f"keyword:{hit}"] += 1

    attrs = elem.attrib or {}
    attr_previews: List[str] = []
    for key, value in attrs.items():
        local_key = strip_ns(key)
        key_hits = any_keyword_hit(local_key, keywords)
        val_hits = any_keyword_hit(value, keywords)
        if key_hits or val_hits:
            reasons.append(f"attr={local_key}")
        for hit in key_hits + val_hits:
            reason_counter[f"keyword:{hit}"] += 1
        attr_previews.append(f"{local_key}={value}")

    text_content = (elem.text or "").strip()
    text_hits = any_keyword_hit(text_content, keywords) if text_content else []
    if text_hits:
        reasons.append("text")
        for hit in text_hits:
            reason_counter[f"keyword:{hit}"] += 1

    if not reasons:
        return None, reason_counter

    attrs_preview = truncate(", ".join(attr_previews), text_limit)
    text_preview = truncate(text_content, text_limit)
    record = MatchRecord(
        path=path,
        tag=local_tag,
        reasons=sorted(set(reasons)),
        attrs_preview=attrs_preview,
        text_preview=text_preview,
    )
    reason_counter[f"tag:{local_tag}"] += 1
    return record, reason_counter


def walk_and_collect(
    root: ET.Element,
    keywords: List[str],
    text_limit: int,
) -> Tuple[List[MatchRecord], Counter]:
    records: List[MatchRecord] = []
    counters: Counter = Counter()

    def visit(node: ET.Element, parent_path: str) -> None:
        children = list(node)
        local_counter: Counter = Counter()
        for child in children:
            child_name = strip_ns(child.tag)
            local_counter[child_name] += 1
            index = local_counter[child_name]
            child_path = f"{parent_path}/{child_name}[{index}]"

            record, reason_counter = inspect_element(child, child_path, keywords, text_limit)
            counters.update(reason_counter)
            if record:
                records.append(record)
            visit(child, child_path)

    root_name = strip_ns(root.tag)
    root_path = f"/{root_name}[1]"
    root_record, root_counter = inspect_element(root, root_path, keywords, text_limit)
    counters.update(root_counter)
    if root_record:
        records.append(root_record)
    visit(root, root_path)
    return records, counters


def print_report(
    input_path: Path,
    namespaces: Dict[str, str],
    keywords: List[str],
    records: List[MatchRecord],
    counters: Counter,
    max_samples: int,
) -> None:
    print(f"[INFO] 文件: {input_path}")
    print(f"[INFO] 关键词: {', '.join(keywords)}")
    if namespaces:
        print("[INFO] 命名空间:")
        for prefix, uri in namespaces.items():
            print(f"  - {prefix}: {uri}")
    else:
        print("[INFO] 命名空间: 无")

    print(f"[SUMMARY] 命中节点数: {len(records)}")
    matched_tags = [(k[4:], v) for k, v in counters.items() if k.startswith("tag:")]
    matched_tags.sort(key=lambda x: (-x[1], x[0]))
    if matched_tags:
        print("[SUMMARY] 命中标签 Top 10:")
        for tag, count in matched_tags[:10]:
            print(f"  - {tag}: {count}")

    matched_keywords = [(k[8:], v) for k, v in counters.items() if k.startswith("keyword:")]
    matched_keywords.sort(key=lambda x: (-x[1], x[0]))
    if matched_keywords:
        print("[SUMMARY] 命中关键词:")
        for kw, count in matched_keywords:
            print(f"  - {kw}: {count}")

    if not records:
        print("[RESULT] 未发现明显网格关键词，PDML 里可能不含显式网格参数。")
        print("[SUGGEST] 可扩大关键词后重试，例如: --keywords \"grid,mesh,cell,size,layer,coarse,fine\"")
        return

    print(f"[RESULT] 检测到网格相关线索，可继续定位并修改（建议先 dry-run）。")
    print(f"[SAMPLES] 显示前 {min(len(records), max_samples)} 条:")
    for i, rec in enumerate(records[:max_samples], start=1):
        reason = ",".join(rec.reasons)
        print(f"  {i}. path={rec.path}")
        print(f"     tag={rec.tag} reasons={reason}")
        if rec.attrs_preview:
            print(f"     attrs={rec.attrs_preview}")
        if rec.text_preview:
            print(f"     text={rec.text_preview}")

    print("[XPATH] 建议先用这些表达式二次确认:")
    print('  - //*[contains(translate(local-name(), "ABCDEFGHIJKLMNOPQRSTUVWXYZ", "abcdefghijklmnopqrstuvwxyz"), "grid")]')
    print('  - //*[contains(translate(local-name(), "ABCDEFGHIJKLMNOPQRSTUVWXYZ", "abcdefghijklmnopqrstuvwxyz"), "mesh")]')
    print('  - //@*[contains(translate(name(), "ABCDEFGHIJKLMNOPQRSTUVWXYZ", "abcdefghijklmnopqrstuvwxyz"), "grid")]')
    print('  - //@*[contains(translate(name(), "ABCDEFGHIJKLMNOPQRSTUVWXYZ", "abcdefghijklmnopqrstuvwxyz"), "mesh")]')


def main() -> int:
    args = build_parser().parse_args()

    input_path = Path(args.input).expanduser().resolve()
    if not input_path.exists():
        print(f"[ERROR] 文件不存在: {input_path}", file=sys.stderr)
        return 2
    if not input_path.is_file():
        print(f"[ERROR] 不是文件: {input_path}", file=sys.stderr)
        return 2

    keywords = normalize_keywords(args.keywords)
    if not keywords:
        print("[ERROR] 至少需要一个关键词", file=sys.stderr)
        return 2

    try:
        namespaces = detect_namespaces(input_path)
        tree = ET.parse(str(input_path))
    except ET.ParseError as exc:
        print(f"[ERROR] XML 解析失败: {exc}", file=sys.stderr)
        return 3

    root = tree.getroot()
    records, counters = walk_and_collect(root, keywords, args.text_limit)
    print_report(input_path, namespaces, keywords, records, counters, args.max_samples)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
