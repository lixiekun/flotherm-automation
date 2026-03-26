#!/usr/bin/env python3
"""Print multiple candidate hierarchy trees around a target PDML assembly.

This tool is intentionally diagnostic. It does not assume the current
converter's hierarchy interpretation is correct. Instead it:

1. Scans geometry records from a PDML file.
2. Shows the raw level probes around a chosen assembly.
3. Builds several candidate trees using different level sources / rules.
4. Prints the target subtree for each candidate so the user can compare it
   against FloTHERM's GUI tree.
"""

from __future__ import annotations

import argparse
import struct
from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

from pdml_to_floxml_converter import PDMLBinaryReader


@dataclass
class RecordView:
    global_index: int
    offset: int
    offset_hex: str
    section_guess: str
    node_type: str
    name: str
    current_level: int
    off6_level: Optional[int]
    off4be_level: Optional[int]
    off4le_level: Optional[int]


@dataclass
class TreeNode:
    record: RecordView
    level_used: int
    children: List["TreeNode"] = field(default_factory=list)


def classify_offset(offset: int, sections: Dict[str, int]) -> str:
    if not sections:
        return "unknown"

    ordered = sorted(sections.items(), key=lambda item: item[1])
    current = ordered[0][0]
    for name, start in ordered:
        if offset >= start:
            current = name
        else:
            break
    return current


def normalize_level(value: Optional[int]) -> Optional[int]:
    if value is None:
        return None
    return value if 1 <= value <= 20 else None


def probe_levels(reader: PDMLBinaryReader, offset: int) -> Tuple[Optional[int], Optional[int], Optional[int]]:
    off6 = reader.data[offset - 6] if offset >= 6 else None
    off4be = struct.unpack(">I", reader.data[offset - 4:offset])[0] if offset >= 4 else None
    off4le = struct.unpack("<I", reader.data[offset - 4:offset])[0] if offset >= 4 else None
    return normalize_level(off6), normalize_level(off4be), normalize_level(off4le)


def load_records(pdml_file: str, geometry_only: bool) -> Tuple[PDMLBinaryReader, List[RecordView]]:
    reader = PDMLBinaryReader(pdml_file)
    reader._extract_strings()
    reader._locate_sections()

    records: List[RecordView] = []
    for index, record in enumerate(reader._find_geometry_records()):
        section_guess = classify_offset(record["offset"], reader.sections)
        if geometry_only and section_guess != "geometry":
            continue
        off6, off4be, off4le = probe_levels(reader, record["offset"])
        records.append(
            RecordView(
                global_index=index,
                offset=record["offset"],
                offset_hex=f"0x{record['offset']:06X}",
                section_guess=section_guess,
                node_type=record["node_type"],
                name=record["name"],
                current_level=record["level"],
                off6_level=off6,
                off4be_level=off4be,
                off4le_level=off4le,
            )
        )
    return reader, records


def is_container_node(node_type: str) -> bool:
    return node_type in {
        "assembly",
        "network_assembly",
        "heatsink",
        "pcb",
        "enclosure",
        "rack",
        "cooler",
        "controller",
    }


def is_container_assembly_name(name: str) -> bool:
    patterns = [
        "Layers",
        "Layer",
        "Attach",
        "Assembly",
        "Power",
        "Electrical",
        "Vias",
        "Board",
        "Parts",
        "Components",
        "Domain",
        "Solution",
        "Model",
    ]
    lowered = name.lower()
    return any(pattern.lower() in lowered for pattern in patterns)


def get_level(record: RecordView, mode: str) -> int:
    value: Optional[int]
    if mode == "current":
        value = record.current_level
    elif mode == "off6":
        value = record.off6_level
    elif mode == "off4be":
        value = record.off4be_level
    elif mode == "off4le":
        value = record.off4le_level
    else:
        raise ValueError(f"Unknown level mode: {mode}")

    if value is None or value < 1:
        return 2
    return min(value, 20)


def build_tree_stack(records: Sequence[RecordView], level_mode: str) -> List[TreeNode]:
    forest: List[TreeNode] = []
    parent_stack: List[Tuple[int, TreeNode]] = []

    def get_parent_for_level(target_level: int) -> Optional[TreeNode]:
        while parent_stack and parent_stack[-1][0] >= target_level:
            parent_stack.pop()
        return parent_stack[-1][1] if parent_stack else None

    for record in records:
        level = max(2, get_level(record, level_mode))
        node = TreeNode(record=record, level_used=level)
        parent = get_parent_for_level(level)
        if parent is not None:
            parent.children.append(node)
        else:
            forest.append(node)
        if is_container_node(record.node_type):
            parent_stack.append((level, node))
    return forest


def build_tree_l3_group(records: Sequence[RecordView], level_mode: str) -> List[TreeNode]:
    forest: List[TreeNode] = []
    parent_stack: List[TreeNode] = []
    last_assembly: Optional[TreeNode] = None

    def current_parent() -> Optional[TreeNode]:
        return parent_stack[-1] if parent_stack else None

    for record in records:
        level = max(2, min(get_level(record, level_mode), 10))
        node = TreeNode(record=record, level_used=level)
        parent = current_parent()

        if record.node_type == "assembly":
            if level == 3:
                if parent is not None:
                    parent.children.append(node)
                else:
                    forest.append(node)
                parent_stack.append(node)
                last_assembly = node
            elif level == 2:
                if is_container_assembly_name(record.name) and not parent_stack:
                    forest.append(node)
                    parent_stack = [node]
                    last_assembly = node
                elif last_assembly is not None and parent_stack:
                    if len(parent_stack) > 1:
                        parent_stack.pop()
                    sibling_parent = current_parent()
                    if sibling_parent is not None:
                        sibling_parent.children.append(node)
                    else:
                        forest.append(node)
                    parent_stack.append(node)
                    last_assembly = node
                else:
                    forest.append(node)
                    parent_stack = [node]
                    last_assembly = node
            else:
                if parent is not None:
                    parent.children.append(node)
                else:
                    forest.append(node)
        else:
            if parent is not None:
                parent.children.append(node)
            else:
                forest.append(node)

    return forest


def walk_forest(nodes: Iterable[TreeNode]) -> Iterable[TreeNode]:
    for node in nodes:
        yield node
        yield from walk_forest(node.children)


def find_target(nodes: Sequence[TreeNode], global_index: int) -> Optional[TreeNode]:
    for node in walk_forest(nodes):
        if node.record.global_index == global_index:
            return node
    return None


def print_subtree(node: TreeNode, max_depth: int, depth: int = 0) -> None:
    indent = "  " * depth
    print(
        f"{indent}{node.record.node_type} {node.record.name} "
        f"[idx={node.record.global_index} level={node.level_used}]"
    )
    if depth >= max_depth:
        if node.children:
            print(f"{indent}  ... {len(node.children)} more child nodes")
        return
    for child in node.children:
        print_subtree(child, max_depth, depth + 1)


def print_context(records: Sequence[RecordView], target_index: int, radius: int) -> None:
    local_index = next(i for i, record in enumerate(records) if record.global_index == target_index)
    start = max(0, local_index - radius)
    end = min(len(records), local_index + radius + 1)

    print("Context Records")
    print("gidx  type              cur  off6 off4be off4le  name")
    print("-" * 88)
    for record in records[start:end]:
        marker = ">" if record.global_index == target_index else " "
        print(
            f"{marker}{record.global_index:>3}  "
            f"{record.node_type:<16} "
            f"{record.current_level:>3}  "
            f"{str(record.off6_level or '-'):>4} "
            f"{str(record.off4be_level or '-'):>6} "
            f"{str(record.off4le_level or '-'):>6}  "
            f"{record.name}"
        )
    print()


def parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pdml_file", help="Input PDML file")
    parser.add_argument("assembly_name", help="Assembly name substring to inspect")
    parser.add_argument(
        "--all-records",
        action="store_true",
        help="Include records outside the geometry section",
    )
    parser.add_argument(
        "--context",
        type=int,
        default=10,
        help="How many records before/after the target to print",
    )
    parser.add_argument(
        "--depth",
        type=int,
        default=5,
        help="Maximum subtree depth to print per candidate",
    )
    return parser.parse_args(argv)


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = parse_args(argv)
    _, records = load_records(args.pdml_file, geometry_only=not args.all_records)

    matches = [record for record in records if args.assembly_name.lower() in record.name.lower()]
    if not matches:
        print(f"No geometry record matched assembly name substring: {args.assembly_name}")
        return 1

    target = matches[0]
    print(f"Matched target: idx={target.global_index} type={target.node_type} name={target.name}")
    if len(matches) > 1:
        print("Other matches:")
        for item in matches[1:6]:
            print(f"  idx={item.global_index} type={item.node_type} name={item.name}")
        print()

    print_context(records, target.global_index, args.context)

    candidates = [
        ("stack/off4be", build_tree_stack(records, "off4be")),
        ("l3-group/off4be", build_tree_l3_group(records, "off4be")),
        ("l3-group/off6", build_tree_l3_group(records, "off6")),
        ("stack/off6", build_tree_stack(records, "off6")),
    ]

    for name, forest in candidates:
        target_node = find_target(forest, target.global_index)
        print(f"Candidate: {name}")
        if target_node is None:
            print("  target not found in candidate tree")
        else:
            print_subtree(target_node, args.depth)
        print()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
