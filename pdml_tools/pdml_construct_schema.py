#!/usr/bin/env python3
"""
Construct-based helpers for reverse-engineering FloTHERM PDML files.

This module is intentionally schema-first:
- use `construct` for the byte-level primitives we already trust
- keep scanning logic explicit for the parts of PDML that are still evolving
- expose reusable helpers that can feed the main converter later
"""

from __future__ import annotations

import argparse
import struct
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, Iterator, List, Optional

try:
    from construct import Bytes, Const, Int16ub, Int32ub, Struct, this
except ImportError as exc:  # pragma: no cover - dependency check only
    raise SystemExit(
        "Missing dependency: construct\n"
        "Install it with: pip install construct"
    ) from exc


STRING_MARKER = b"\x07\x02"
DOUBLE_MARKER = 0x06
HEADER_ENCODING = "ascii"
TEXT_ENCODING = "utf-8"


KNOWN_SECTION_MARKERS = {
    "gravity": "model",
    "overall control": "solve",
    "grid smooth": "grid",
    "modeldata": "attributes",
    "solution domain": "solution_domain",
    "geometry": "geometry",
}


GEOMETRY_TYPE_CODES = {
    0x0010: "pcb",
    0x01D0: "resistance",
    0x0250: "cuboid",
    0x0260: "cutout",
    0x0270: "monitor_point",
    0x0280: "prism",
    0x0290: "region",
    0x02A0: "resistance",
    0x02C0: "source",
    0x02E0: "assembly",
    0x02F0: "cuboid",
    0x0300: "cylinder",
    0x0310: "enclosure",
    0x0320: "fan",
    0x0330: "fixed_flow",
    0x0340: "heatsink",
    0x0350: "pcb",
    0x0370: "recirc_device",
    0x0380: "sloping_block",
    0x0530: "square_diffuser",
    0x05D0: "perforated_plate",
    0x0731: "tet",
    0x0732: "inverted_tet",
    0x0740: "network_assembly",
    0x0770: "heatpipe",
    0x0800: "tec",
    0x0810: "die",
    0x0840: "cooler",
    0x0870: "rack",
    0x09A0: "controller",
}


PdmlTaggedString = Struct(
    "marker" / Const(STRING_MARKER),
    "type_code" / Int16ub,
    "reserved" / Int16ub,
    "length" / Int32ub,
    "payload" / Bytes(this.length),
)


@dataclass(frozen=True)
class PdmlHeader:
    raw: str
    format_name: str
    version: str
    product: str


@dataclass(frozen=True)
class TaggedString:
    offset: int
    type_code: int
    reserved: int
    raw_bytes: bytes
    text: str

    @property
    def geometry_type(self) -> Optional[str]:
        return GEOMETRY_TYPE_CODES.get(self.type_code)


@dataclass(frozen=True)
class TaggedDouble:
    offset: int
    value: float


@dataclass(frozen=True)
class GeometryCandidate:
    offset: int
    name: str
    type_code: int
    geometry_type: str
    nearby_doubles: List[TaggedDouble]


class PdmlConstructScanner:
    """Low-level scanner that mixes trusted construct blocks with byte scans."""

    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.data = self.path.read_bytes()
        self._strings: Optional[List[TaggedString]] = None
        self._doubles: Optional[List[TaggedDouble]] = None

    def parse_header(self) -> PdmlHeader:
        newline = self.data.find(b"\n")
        if newline < 0:
            raise ValueError("PDML header terminator not found")

        raw = self.data[:newline].decode(HEADER_ENCODING, errors="replace").strip()
        parts = raw.split()
        return PdmlHeader(
            raw=raw,
            format_name=parts[0] if len(parts) > 0 else "",
            version=parts[1] if len(parts) > 1 else "",
            product=" ".join(parts[2:]) if len(parts) > 2 else "",
        )

    def scan_strings(self) -> List[TaggedString]:
        if self._strings is not None:
            return self._strings

        results: List[TaggedString] = []
        limit = len(self.data) - 10

        for offset in range(limit):
            if self.data[offset : offset + 2] != STRING_MARKER:
                continue

            try:
                record = PdmlTaggedString.parse(self.data[offset:])
            except Exception:
                continue

            if record.length <= 0 or record.length > 4096:
                continue

            end = offset + 10 + record.length
            if end > len(self.data):
                continue

            raw_bytes = bytes(record.payload)
            text = raw_bytes.decode(TEXT_ENCODING, errors="replace").strip("\x00\r\n\t ")
            if not text:
                continue

            results.append(
                TaggedString(
                    offset=offset,
                    type_code=record.type_code,
                    reserved=record.reserved,
                    raw_bytes=raw_bytes,
                    text=text,
                )
            )

        self._strings = results
        return results

    def scan_doubles(self) -> List[TaggedDouble]:
        if self._doubles is not None:
            return self._doubles

        results: List[TaggedDouble] = []
        limit = len(self.data) - 9

        for offset in range(limit):
            if self.data[offset] != DOUBLE_MARKER:
                continue

            value = struct.unpack(">d", self.data[offset + 1 : offset + 9])[0]
            if value != value:
                continue
            if not (-1e15 < value < 1e15):
                continue

            results.append(TaggedDouble(offset=offset, value=value))

        self._doubles = results
        return results

    def locate_sections(self) -> Dict[str, int]:
        sections: Dict[str, int] = {}
        for record in self.scan_strings():
            section_name = KNOWN_SECTION_MARKERS.get(record.text.lower())
            if section_name and section_name not in sections:
                sections[section_name] = record.offset
        return sections

    def geometry_candidates(self, search_window: int = 500) -> List[GeometryCandidate]:
        doubles = self.scan_doubles()
        candidates: List[GeometryCandidate] = []

        for record in self.scan_strings():
            geometry_type = record.geometry_type
            if not geometry_type:
                continue

            nearby = [
                item
                for item in doubles
                if record.offset <= item.offset <= record.offset + search_window
            ]

            candidates.append(
                GeometryCandidate(
                    offset=record.offset,
                    name=record.text,
                    type_code=record.type_code,
                    geometry_type=geometry_type,
                    nearby_doubles=nearby,
                )
            )

        return candidates

    def candidate_triplets(
        self,
        candidate: GeometryCandidate,
        start_rel: int,
        end_rel: int,
        *,
        positive_only: bool = False,
    ) -> List[float]:
        values = [
            item.value
            for item in candidate.nearby_doubles
            if start_rel <= item.offset - candidate.offset <= end_rel
        ]
        if positive_only:
            values = [value for value in values if value > 0]
        return values


def _format_summary(scanner: PdmlConstructScanner) -> str:
    header = scanner.parse_header()
    sections = scanner.locate_sections()
    strings = scanner.scan_strings()
    doubles = scanner.scan_doubles()
    geometry = scanner.geometry_candidates()

    lines = [
        f"file: {scanner.path.name}",
        f"header: {header.raw}",
        f"strings: {len(strings)}",
        f"doubles: {len(doubles)}",
        "sections:",
    ]
    for name, offset in sections.items():
        lines.append(f"  - {name}: 0x{offset:06X}")

    lines.append("geometry candidates:")
    for candidate in geometry[:20]:
        size_guess = scanner.candidate_triplets(candidate, 200, 370, positive_only=True)[:3]
        pos_guess = scanner.candidate_triplets(candidate, 370, 450)[:3]
        lines.append(
            "  - "
            f"{candidate.name} "
            f"(type=0x{candidate.type_code:04X}, xml={candidate.geometry_type}, "
            f"offset=0x{candidate.offset:06X}, size_guess={size_guess}, pos_guess={pos_guess})"
        )

    return "\n".join(lines)


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Scan PDML with construct-based primitives")
    parser.add_argument("pdml_path", help="Path to a PDML file")
    parser.add_argument(
        "--mode",
        choices=("summary", "strings", "geometry"),
        default="summary",
        help="Select which view to print",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=20,
        help="Maximum number of rows to print for list views",
    )
    return parser


def _iter_string_rows(strings: Iterable[TaggedString], limit: int) -> Iterator[str]:
    for idx, record in enumerate(strings):
        if idx >= limit:
            break
        xml_type = record.geometry_type or "-"
        yield (
            f"0x{record.offset:06X} "
            f"type=0x{record.type_code:04X} "
            f"geom={xml_type:<18} "
            f"text={record.text}"
        )


def _iter_geometry_rows(
    scanner: PdmlConstructScanner, candidates: Iterable[GeometryCandidate], limit: int
) -> Iterator[str]:
    for idx, candidate in enumerate(candidates):
        if idx >= limit:
            break
        size_guess = scanner.candidate_triplets(candidate, 200, 370, positive_only=True)[:3]
        pos_guess = scanner.candidate_triplets(candidate, 370, 450)[:3]
        yield (
            f"0x{candidate.offset:06X} "
            f"type=0x{candidate.type_code:04X} "
            f"xml={candidate.geometry_type:<18} "
            f"name={candidate.name} "
            f"size_guess={size_guess} "
            f"pos_guess={pos_guess}"
        )


def main() -> int:
    args = build_arg_parser().parse_args()
    scanner = PdmlConstructScanner(args.pdml_path)

    if args.mode == "summary":
        print(_format_summary(scanner))
        return 0

    if args.mode == "strings":
        for row in _iter_string_rows(scanner.scan_strings(), args.limit):
            print(row)
        return 0

    if args.mode == "geometry":
        for row in _iter_geometry_rows(scanner, scanner.geometry_candidates(), args.limit):
            print(row)
        return 0

    raise AssertionError(f"Unsupported mode: {args.mode}")


if __name__ == "__main__":
    raise SystemExit(main())
