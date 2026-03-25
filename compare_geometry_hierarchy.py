#!/usr/bin/env python3
"""Compare geometry hierarchy between reference ECXML/FloXML files.

This is meant for hierarchy-focused verification during PDML reverse
engineering. It normalizes the small tag-name differences between ECXML
and FloXML and reports duplicate-aware path mismatches.
"""

from __future__ import annotations

import argparse
from collections import Counter
from pathlib import Path
from typing import Iterable, Iterator, Sequence, Tuple
import xml.etree.ElementTree as ET


PathEntry = Tuple[str, str]
HierarchyPath = Tuple[PathEntry, ...]


TAG_ALIASES = {
    "solid3dBlock": "cuboid",
    "sourceBlock": "source",
    "monitorPoint": "monitor_point",
}


def normalize_tag(tag: str) -> str:
    return TAG_ALIASES.get(tag, tag)


def geometry_children(node: ET.Element) -> list[ET.Element]:
    geometry = node.find("geometry")
    return list(geometry) if geometry is not None else []


def flatten_geometry(container: ET.Element, prefix: HierarchyPath = ()) -> Iterator[HierarchyPath]:
    for child in list(container):
        entry = (normalize_tag(child.tag), child.findtext("name") or "")
        path = prefix + (entry,)
        yield path
        yield from flatten_geometry_container(child, path)


def flatten_geometry_container(node: ET.Element, prefix: HierarchyPath) -> Iterator[HierarchyPath]:
    for child in geometry_children(node):
        entry = (normalize_tag(child.tag), child.findtext("name") or "")
        path = prefix + (entry,)
        yield path
        yield from flatten_geometry_container(child, path)


def load_geometry_counter(path: Path) -> Counter[HierarchyPath]:
    root = ET.parse(path).getroot()
    geometry = root.find("geometry")
    if geometry is None:
        raise ValueError(f"{path} does not contain a <geometry> section")
    return Counter(flatten_geometry(geometry))


def format_path(path: HierarchyPath) -> str:
    return " -> ".join(f"{tag}:{name}" for tag, name in path)


def print_tree(path: Path) -> None:
    root = ET.parse(path).getroot()
    geometry = root.find("geometry")
    if geometry is None:
        raise ValueError(f"{path} does not contain a <geometry> section")

    def walk(container: ET.Element, depth: int = 0) -> None:
        for child in list(container):
            print(f"{'  ' * depth}{normalize_tag(child.tag)} {child.findtext('name') or ''}")
            child_geometry = child.find("geometry")
            if child_geometry is not None:
                walk(child_geometry, depth + 1)

    walk(geometry)


def compare(reference: Path, candidate: Path, limit: int) -> int:
    ref_counter = load_geometry_counter(reference)
    cand_counter = load_geometry_counter(candidate)

    only_ref: list[tuple[int, HierarchyPath]] = []
    only_cand: list[tuple[int, HierarchyPath]] = []

    for path in sorted(set(ref_counter) | set(cand_counter)):
        ref_count = ref_counter[path]
        cand_count = cand_counter[path]
        if ref_count > cand_count:
            only_ref.append((ref_count - cand_count, path))
        elif cand_count > ref_count:
            only_cand.append((cand_count - ref_count, path))

    print(f"reference: {reference}")
    print(f"candidate: {candidate}")
    print(f"missing_from_candidate: {sum(count for count, _ in only_ref)}")
    print(f"extra_in_candidate: {sum(count for count, _ in only_cand)}")

    if only_ref:
        print("\nMissing From Candidate")
        for count, path in only_ref[:limit]:
            print(f"{count:>3} x {format_path(path)}")

    if only_cand:
        print("\nExtra In Candidate")
        for count, path in only_cand[:limit]:
            print(f"{count:>3} x {format_path(path)}")

    return 1 if only_ref or only_cand else 0


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("reference", type=Path, help="Reference ECXML/FloXML file")
    parser.add_argument("candidate", type=Path, help="Generated FloXML file to compare")
    parser.add_argument(
        "--limit",
        type=int,
        default=40,
        help="Maximum mismatched paths to print per side",
    )
    parser.add_argument(
        "--print-tree",
        choices=("reference", "candidate", "both"),
        help="Print normalized geometry trees instead of only mismatch counts",
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)

    if args.print_tree in {"reference", "both"}:
        print("Reference Tree")
        print_tree(args.reference)
        print()

    if args.print_tree in {"candidate", "both"}:
        print("Candidate Tree")
        print_tree(args.candidate)
        print()

    return compare(args.reference, args.candidate, args.limit)


if __name__ == "__main__":
    raise SystemExit(main())
