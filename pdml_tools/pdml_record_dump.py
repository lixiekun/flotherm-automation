#!/usr/bin/env python3
"""Structured PDML record dump for reverse-engineering handoff.

This tool is designed to make future PDML samples easier to analyze by both
humans and other AI models. It emits:

1. A machine-friendly JSON file with strings, geometry records, type-code
   statistics, candidate positions/sizes, nearby values, and anomaly flags.
2. A short Markdown summary that highlights the most important next questions.
"""

from __future__ import annotations

import argparse
import json
import struct
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence

from pdml_to_floxml_converter import PDMLBinaryReader


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


def to_jsonable(value: Any) -> Any:
    if isinstance(value, tuple):
        return [to_jsonable(item) for item in value]
    if isinstance(value, list):
        return [to_jsonable(item) for item in value]
    if isinstance(value, dict):
        return {key: to_jsonable(item) for key, item in value.items()}
    return value


def type_code_summary(reader: PDMLBinaryReader) -> List[Dict[str, Any]]:
    samples: Dict[int, List[str]] = defaultdict(list)
    counts: Counter[int] = Counter()

    for record in reader.tagged_strings:
        type_code = record["type_code"]
        counts[type_code] += 1
        if len(samples[type_code]) < 5:
            samples[type_code].append(record["value"])

    summary: List[Dict[str, Any]] = []
    for type_code, count in sorted(counts.items(), key=lambda item: (-item[1], item[0])):
        summary.append(
            {
                "type_code": type_code,
                "type_code_hex": f"0x{type_code:04X}",
                "count": count,
                "geometry_node_type_guess": reader.GEOMETRY_TYPE_CODES.get(type_code),
                "sample_values": samples[type_code],
            }
        )
    return summary


def nearby_string_context(reader: PDMLBinaryReader, offset: int, radius: int = 160, limit: int = 6) -> List[Dict[str, Any]]:
    matches: List[Dict[str, Any]] = []
    for record in reader.tagged_strings:
        string_offset = record["offset"]
        if string_offset == offset:
            continue
        if abs(string_offset - offset) > radius:
            continue
        matches.append(
            {
                "offset": string_offset,
                "offset_hex": f"0x{string_offset:06X}",
                "delta": string_offset - offset,
                "type_code": record["type_code"],
                "type_code_hex": f"0x{record['type_code']:04X}",
                "value": record["value"],
            }
        )
    matches.sort(key=lambda item: abs(item["delta"]))
    return matches[:limit]


def nearby_double_context(reader: PDMLBinaryReader, offset: int, radius: int = 160, limit: int = 12) -> List[Dict[str, Any]]:
    values = []
    for pos, value in reader._find_double_near(offset, range_size=radius):
        values.append(
            {
                "offset": pos,
                "offset_hex": f"0x{pos:06X}",
                "delta": pos - offset,
                "value": value,
            }
        )
    values.sort(key=lambda item: abs(item["delta"]))
    return values[:limit]


def level_probe(reader: PDMLBinaryReader, offset: int) -> Dict[str, Any]:
    start = max(0, offset - 12)
    raw_prefix = reader.data[start:offset]

    candidate_offset_6 = reader.data[offset - 6] if offset >= 6 else None
    candidate_offset_4_be = struct.unpack(">I", reader.data[offset - 4:offset])[0] if offset >= 4 else None
    candidate_offset_4_le = struct.unpack("<I", reader.data[offset - 4:offset])[0] if offset >= 4 else None

    def normalized_level(value: Optional[int]) -> Optional[int]:
        if value is None:
            return None
        return value if 1 <= value <= 20 else None

    return {
        "prefix_start_offset_hex": f"0x{start:06X}",
        "prefix_hex": raw_prefix.hex(" "),
        "offset_minus_6_byte": candidate_offset_6,
        "offset_minus_6_level_guess": normalized_level(candidate_offset_6),
        "offset_minus_4_uint32_be": candidate_offset_4_be,
        "offset_minus_4_be_level_guess": normalized_level(candidate_offset_4_be),
        "offset_minus_4_uint32_le": candidate_offset_4_le,
        "offset_minus_4_le_level_guess": normalized_level(candidate_offset_4_le),
    }


def geometry_record_dump(reader: PDMLBinaryReader) -> List[Dict[str, Any]]:
    records = reader._find_geometry_records()
    duplicate_names = Counter(record["name"] for record in records)
    dump: List[Dict[str, Any]] = []

    for index, record in enumerate(records):
        offset = record["offset"]
        prev_record = records[index - 1] if index > 0 else None
        next_record = records[index + 1] if index + 1 < len(records) else None

        position = reader._extract_standard_position(offset)
        size = reader._extract_standard_size(offset, 3)
        notes: List[str] = []

        section_name = classify_offset(offset, reader.sections)
        if section_name != "geometry":
            notes.append("outside_geometry_section")
        if duplicate_names[record["name"]] > 1:
            notes.append("duplicate_name")
        if record["level"] > 2:
            notes.append("nested_level_record")
        if prev_record is not None and abs(record["level"] - prev_record["level"]) > 1:
            notes.append("level_jump_gt_1")
        if record["node_type"] in {"network_assembly", "pcb", "heatsink"}:
            notes.append("special_object_needs_context")

        dump.append(
            {
                "index": index,
                "offset": offset,
                "offset_hex": f"0x{offset:06X}",
                "section_guess": section_name,
                "type_code": record["type_code"],
                "type_code_hex": f"0x{record['type_code']:04X}",
                "node_type_guess": record["node_type"],
                "name": record["name"],
                "level": record["level"],
                "raw_level_probe": level_probe(reader, offset),
                "candidate_position": list(position),
                "candidate_size": list(size) if size is not None else None,
                "nearby_strings": nearby_string_context(reader, offset),
                "nearby_doubles": nearby_double_context(reader, offset),
                "previous_record": (
                    {
                        "index": index - 1,
                        "name": prev_record["name"],
                        "node_type_guess": prev_record["node_type"],
                        "level": prev_record["level"],
                    }
                    if prev_record is not None
                    else None
                ),
                "next_record": (
                    {
                        "index": index + 1,
                        "name": next_record["name"],
                        "node_type_guess": next_record["node_type"],
                        "level": next_record["level"],
                    }
                    if next_record is not None
                    else None
                ),
                "notes": notes,
            }
        )
    return dump


def string_record_dump(reader: PDMLBinaryReader, limit: Optional[int] = None) -> List[Dict[str, Any]]:
    records = []
    source = reader.tagged_strings if limit is None else reader.tagged_strings[:limit]
    for index, record in enumerate(source):
        offset = record["offset"]
        records.append(
            {
                "index": index,
                "offset": offset,
                "offset_hex": f"0x{offset:06X}",
                "section_guess": classify_offset(offset, reader.sections),
                "type_code": record["type_code"],
                "type_code_hex": f"0x{record['type_code']:04X}",
                "value": record["value"],
            }
        )
    return records


def build_anomalies(reader: PDMLBinaryReader, geometry_records: List[Dict[str, Any]]) -> Dict[str, Any]:
    duplicate_geometry_names = [
        {"name": name, "count": count}
        for name, count in Counter(record["name"] for record in geometry_records).items()
        if count > 1
    ]
    duplicate_geometry_names.sort(key=lambda item: (-item["count"], item["name"]))

    outside_geometry = [record for record in geometry_records if "outside_geometry_section" in record["notes"]]
    level_jumps = [record for record in geometry_records if "level_jump_gt_1" in record["notes"]]
    special_objects = [
        {
            "index": record["index"],
            "name": record["name"],
            "node_type_guess": record["node_type_guess"],
            "level": record["level"],
        }
        for record in geometry_records
        if "special_object_needs_context" in record["notes"]
    ]

    return {
        "duplicate_geometry_names": duplicate_geometry_names,
        "outside_geometry_section": [
            {
                "index": record["index"],
                "name": record["name"],
                "node_type_guess": record["node_type_guess"],
                "section_guess": record["section_guess"],
            }
            for record in outside_geometry
        ],
        "suspicious_level_jumps": [
            {
                "index": record["index"],
                "name": record["name"],
                "level": record["level"],
                "previous_record": record["previous_record"],
            }
            for record in level_jumps
        ],
        "special_objects_requiring_context": special_objects,
        "geometry_type_counts": dict(Counter(record["node_type_guess"] for record in geometry_records)),
    }


def build_summary_markdown(report: Dict[str, Any]) -> str:
    meta = report["meta"]
    anomalies = report["anomalies"]
    geometry_records = report["geometry_records"]

    lines = [
        "# PDML Record Dump Summary",
        "",
        "## File",
        f"- Input: `{meta['input_file']}`",
        f"- Size: `{meta['file_size_bytes']}` bytes",
        f"- Version: `{meta['header'].get('version', '')}`",
        f"- Product: `{meta['header'].get('product', '')}`",
        f"- Project Name Guess: `{meta['project_name_guess']}`",
        f"- Profile Guess: `{meta['profile_guess']}`",
        "",
        "## Counts",
        f"- Tagged Strings: `{meta['tagged_string_count']}`",
        f"- Geometry Records: `{len(geometry_records)}`",
        f"- Section Markers: `{len(meta['sections'])}`",
        "",
        "## Sections",
    ]

    if meta["sections"]:
        for name, offset in sorted(meta["sections"].items(), key=lambda item: item[1]):
            lines.append(f"- `{name}` at `0x{offset:06X}`")
    else:
        lines.append("- No section markers detected")

    lines.extend(
        [
            "",
            "## Geometry Type Counts",
        ]
    )
    for node_type, count in sorted(anomalies["geometry_type_counts"].items(), key=lambda item: (-item[1], item[0])):
        lines.append(f"- `{node_type}`: `{count}`")

    lines.extend(
        [
            "",
            "## Anomalies",
            f"- Duplicate Geometry Names: `{len(anomalies['duplicate_geometry_names'])}`",
            f"- Geometry Records Outside Geometry Section: `{len(anomalies['outside_geometry_section'])}`",
            f"- Suspicious Level Jumps: `{len(anomalies['suspicious_level_jumps'])}`",
            f"- Special Objects Requiring Context: `{len(anomalies['special_objects_requiring_context'])}`",
        ]
    )

    if anomalies["duplicate_geometry_names"]:
        lines.extend(["", "### Duplicate Geometry Names"])
        for item in anomalies["duplicate_geometry_names"][:15]:
            lines.append(f"- `{item['name']}` x `{item['count']}`")

    if anomalies["outside_geometry_section"]:
        lines.extend(["", "### Geometry Records Outside Geometry Section"])
        for item in anomalies["outside_geometry_section"][:15]:
            lines.append(
                f"- `#{item['index']}` `{item['node_type_guess']}` `{item['name']}` in `{item['section_guess']}`"
            )

    if anomalies["special_objects_requiring_context"]:
        lines.extend(["", "### Special Objects To Inspect Next"])
        for item in anomalies["special_objects_requiring_context"][:15]:
            lines.append(
                f"- `#{item['index']}` `{item['node_type_guess']}` `{item['name']}` level `{item['level']}`"
            )

    lines.extend(
        [
            "",
            "## Recommended Next Steps",
            "- Check `geometry_records[*].nearby_strings` to find parent/group markers near suspicious objects.",
            "- Check `geometry_records[*].nearby_doubles` plus `candidate_position` / `candidate_size` to validate field layouts.",
            "- Compare duplicate names together before changing converter logic; repeated names often signal siblings or GUI-expanded objects.",
            "- Use this dump alongside `compare_geometry_hierarchy.py` when a new PDML sample has an ECXML/FloXML reference.",
        ]
    )

    return "\n".join(lines) + "\n"


def build_report(reader: PDMLBinaryReader, input_path: Path, string_limit: Optional[int]) -> Dict[str, Any]:
    header = reader._parse_header()
    reader._extract_strings()
    project_name = reader._extract_project_name()
    profile_guess = reader._detect_profile(project_name)
    reader.profile = profile_guess
    reader._locate_sections()

    geometry_records = geometry_record_dump(reader)

    return {
        "schema_version": 1,
        "meta": {
            "input_file": str(input_path),
            "file_size_bytes": len(reader.data),
            "header": header,
            "project_name_guess": project_name,
            "profile_guess": profile_guess,
            "sections": reader.sections,
            "tagged_string_count": len(reader.tagged_strings),
        },
        "type_code_stats": type_code_summary(reader),
        "geometry_records": geometry_records,
        "string_records": string_record_dump(reader, limit=string_limit),
        "anomalies": build_anomalies(reader, geometry_records),
    }


def default_output_paths(input_path: Path, output_json: Optional[Path], output_summary: Optional[Path]) -> tuple[Path, Path]:
    if output_json is None:
        output_json = input_path.with_suffix(input_path.suffix + ".dump.json")
    if output_summary is None:
        output_summary = input_path.with_suffix(input_path.suffix + ".dump.md")
    return output_json, output_summary


def parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path, help="PDML file to analyze")
    parser.add_argument("-o", "--output-json", type=Path, help="Path for JSON dump output")
    parser.add_argument("-s", "--output-summary", type=Path, help="Path for Markdown summary output")
    parser.add_argument(
        "--string-limit",
        type=int,
        default=None,
        help="Limit stored string records in JSON to reduce file size",
    )
    parser.add_argument(
        "--summary-only",
        action="store_true",
        help="Print summary to stdout instead of only writing files",
    )
    return parser.parse_args(argv)


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = parse_args(argv)
    input_path = args.input.resolve()
    output_json, output_summary = default_output_paths(input_path, args.output_json, args.output_summary)

    reader = PDMLBinaryReader(str(input_path))
    report = build_report(reader, input_path, args.string_limit)
    summary = build_summary_markdown(report)

    output_json.write_text(json.dumps(to_jsonable(report), indent=2, ensure_ascii=False), encoding="utf-8")
    output_summary.write_text(summary, encoding="utf-8")

    print(f"[INFO] JSON dump: {output_json}")
    print(f"[INFO] Summary: {output_summary}")
    if args.summary_only:
        print()
        print(summary, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
