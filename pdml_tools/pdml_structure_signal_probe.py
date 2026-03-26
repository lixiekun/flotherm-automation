#!/usr/bin/env python3
"""Probe raw structural signals around PDML container records.

This tool does not try to build a hierarchy. It compares the raw bytes around
multiple container records side-by-side so we can look for fields that might
encode:

- child counts
- subtree spans
- parent identifiers
- block boundaries
"""

from __future__ import annotations

import argparse
import struct
from dataclasses import dataclass
from typing import Dict, List, Optional, Sequence, Tuple

from pdml_to_floxml_converter import PDMLBinaryReader


@dataclass
class RecordView:
    global_index: int
    offset: int
    section_guess: str
    node_type: str
    name: str


CONTAINER_TYPES = {
    "assembly",
    "network_assembly",
    "heatsink",
    "pcb",
    "enclosure",
    "rack",
    "cooler",
    "controller",
}


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


def load_records(pdml_file: str, all_records: bool) -> Tuple[PDMLBinaryReader, List[RecordView]]:
    reader = PDMLBinaryReader(pdml_file)
    reader._extract_strings()
    reader._locate_sections()

    records: List[RecordView] = []
    for index, record in enumerate(reader._find_geometry_records()):
        section_guess = classify_offset(record["offset"], reader.sections)
        if not all_records and section_guess != "geometry":
            continue
        if record["node_type"] not in CONTAINER_TYPES:
            continue
        records.append(
            RecordView(
                global_index=index,
                offset=record["offset"],
                section_guess=section_guess,
                node_type=record["node_type"],
                name=record["name"],
            )
        )
    return reader, records


def format_label(record: RecordView) -> str:
    return f"[{record.global_index}] {record.node_type}:{record.name}"


def print_inventory(records: Sequence[RecordView]) -> None:
    print("Container Inventory")
    print("gidx  section    type              offset    name")
    print("-" * 96)
    for record in records:
        print(
            f"{record.global_index:>4}  "
            f"{record.section_guess:<9} "
            f"{record.node_type:<16} "
            f"0x{record.offset:06X}  "
            f"{record.name}"
        )
    print()


def print_hex_windows(reader: PDMLBinaryReader, records: Sequence[RecordView], before: int, after: int) -> None:
    print(f"Raw Windows (before={before}, after={after})")
    for record in records:
        start = max(0, record.offset - before)
        end = min(len(reader.data), record.offset + after)
        prefix = reader.data[start:record.offset].hex(" ")
        suffix = reader.data[record.offset:end].hex(" ")
        print(format_label(record))
        print(f"  before: {prefix}")
        print(f"  at+after: {suffix}")
    print()


def read_value(data: bytes, absolute_offset: int, kind: str) -> Optional[int]:
    try:
        if kind == "u8":
            return data[absolute_offset]
        if kind == "u16be":
            return struct.unpack(">H", data[absolute_offset:absolute_offset + 2])[0]
        if kind == "u16le":
            return struct.unpack("<H", data[absolute_offset:absolute_offset + 2])[0]
        if kind == "u32be":
            return struct.unpack(">I", data[absolute_offset:absolute_offset + 4])[0]
        if kind == "u32le":
            return struct.unpack("<I", data[absolute_offset:absolute_offset + 4])[0]
    except Exception:
        return None
    return None


def interesting_value(value: Optional[int], kind: str, max_value: int) -> bool:
    if value is None:
        return False
    if value == 0:
        return False
    if kind == "u8":
        return value <= min(max_value, 255)
    return value <= max_value


def collect_rows(
    reader: PDMLBinaryReader,
    records: Sequence[RecordView],
    rel_start: int,
    rel_end: int,
    max_value: int,
    min_hits: int,
) -> Dict[str, List[Tuple[int, List[Optional[int]]]]]:
    rows: Dict[str, List[Tuple[int, List[Optional[int]]]]] = {kind: [] for kind in ("u8", "u16be", "u16le", "u32be", "u32le")}

    for kind in rows:
        width = {"u8": 1, "u16be": 2, "u16le": 2, "u32be": 4, "u32le": 4}[kind]
        for rel in range(rel_start, rel_end + 1):
            values: List[Optional[int]] = []
            hit_count = 0
            for record in records:
                absolute_offset = record.offset + rel
                if absolute_offset < 0 or absolute_offset + width > len(reader.data):
                    values.append(None)
                    continue
                value = read_value(reader.data, absolute_offset, kind)
                values.append(value)
                if interesting_value(value, kind, max_value):
                    hit_count += 1
            if hit_count < min_hits:
                continue

            interesting = [value for value in values if interesting_value(value, kind, max_value)]
            if not interesting:
                continue
            if len(set(interesting)) == 1 and interesting[0] == 1:
                continue

            rows[kind].append((rel, values))
    return rows


def print_rows(records: Sequence[RecordView], rows: Dict[str, List[Tuple[int, List[Optional[int]]]]]) -> None:
    labels = [str(record.global_index) for record in records]
    header = "rel".ljust(6) + "".join(label.rjust(10) for label in labels)

    print("Interesting Integer Fields")
    for kind, kind_rows in rows.items():
        if not kind_rows:
            continue
        print(f"\n[{kind}]")
        print(header)
        print("-" * len(header))
        for rel, values in kind_rows:
            row = f"{rel:+d}".ljust(6)
            for value in values:
                cell = "-" if value is None else str(value)
                row += cell.rjust(10)
            print(row)
    print()


def parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pdml_file", help="Input PDML file")
    parser.add_argument(
        "--all-records",
        action="store_true",
        help="Include container records outside the geometry section",
    )
    parser.add_argument(
        "--max-records",
        type=int,
        default=12,
        help="Maximum number of container records to print",
    )
    parser.add_argument(
        "--before",
        type=int,
        default=32,
        help="Bytes to print before each record offset",
    )
    parser.add_argument(
        "--after",
        type=int,
        default=32,
        help="Bytes to print from each record offset onward",
    )
    parser.add_argument(
        "--rel-start",
        type=int,
        default=-32,
        help="Relative start offset for integer scans",
    )
    parser.add_argument(
        "--rel-end",
        type=int,
        default=32,
        help="Relative end offset for integer scans",
    )
    parser.add_argument(
        "--max-value",
        type=int,
        default=4096,
        help="Maximum integer value considered interesting",
    )
    parser.add_argument(
        "--min-hits",
        type=int,
        default=2,
        help="Minimum number of records that must show a small integer at the same relative offset",
    )
    return parser.parse_args(argv)


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = parse_args(argv)
    reader, records = load_records(args.pdml_file, all_records=args.all_records)

    if not records:
        print("No container records found.")
        return 1

    selected = records[: args.max_records]
    if len(records) > len(selected):
        print(f"Showing first {len(selected)} of {len(records)} container records.\n")

    print_inventory(selected)
    print_hex_windows(reader, selected, args.before, args.after)
    rows = collect_rows(
        reader,
        selected,
        rel_start=args.rel_start,
        rel_end=args.rel_end,
        max_value=args.max_value,
        min_hits=args.min_hits,
    )
    print_rows(selected, rows)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
