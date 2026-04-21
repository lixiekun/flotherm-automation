#!/usr/bin/env python3
"""
Extract source attributes (including non-linear power vs temperature curves)
from PDML / FloXML files to JSON format.

Supports:
  - FloXML (.xml / .floxml) — XML text format, direct parsing
  - PDML (.pdml) — FloTHERM binary format, direct binary extraction

For PDML binary files, source data is extracted directly without going through
the FloXML converter, preserving non-linear curve data that the converter drops.

Binary structure:
  - 0x01E0: source attribute name
  - 0x01F0: source option data (fields with applies_to, type, power, curve)
  - 0x02C0: source geometry node

Output JSON is compatible with floxml_nonlinear_source.py.

Usage:
    python pdml_tools/pdml_extract_sources.py model.pdml -o sources.json
    python pdml_tools/pdml_extract_sources.py model.xml -o sources.json
    python pdml_tools/pdml_extract_sources.py model.pdml  # print summary
    python pdml_tools/pdml_extract_sources.py model.pdml --csv curves/
    python pdml_tools/pdml_extract_sources.py model.pdml --diag  # raw binary diagnostic
"""

import argparse
import csv
import json
import os
import struct
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from pdml_tools.pdml_extract_regions import (
    is_binary_pdml,
    _strip_ns,
    _float_text,
    _text,
)

# Enum mappings extracted from PDML binary analysis.
# The byte after type_code 0x00C0 is the applies_to enum value.
# PDML internal enum differs from FloXML text names — confirmed empirically:
#   0x03 → x_velocity (section with value=0.05)
#   0x08 → temperature (section with power=23.3)
#   More values TBD as more PDML files are analyzed.
_APPLIES_TO_MAP = {
    1: "temperature", 2: "pressure",
    3: "x_velocity", 4: "y_velocity", 5: "z_velocity",
    6: "concentration_1", 7: "concentration_2", 8: "temperature",
    9: "concentration_4", 10: "concentration_5",
    11: "ke_turb", 12: "diss_turb",
}

# source_type: byte after type_code 0x0250.
#   0x03 → total (confirmed).
# For non_linear, value TBD — likely different from 0x03.
_SOURCE_TYPE_MAP = {
    1: "total", 2: "volume", 3: "total",
    4: "fixed", 5: "linear", 6: "non_linear",
}


# ============================================================================
# PDML binary source extraction
# ============================================================================

def _extract_source_fields(reader, section_offset: int, section_end: int) -> Dict[str, Any]:
    """Extract source option fields from a 0x01F0 section by parsing raw binary.

    Field layout:
      field[1]: applies_to enum (type_code 0x00C0)
      field[2]: source_type enum (type_code 0x0250)
      field[3]: value (double)
      field[4]: linear_coefficient (double)
      field[5]: power (double)
      field[6-7]: additional doubles
      Higher fields: non_linear curve data or flags
    """
    raw = reader.data
    section = raw[section_offset:section_end]
    result: Dict[str, Any] = {}
    curve_points: List[Dict[str, float]] = []

    # Parse field markers: 0a 02 01 f0 [FIELD_INDEX]
    field_data: Dict[int, Dict] = {}
    i = 0
    while i < len(section) - 5:
        if section[i:i+4] == bytes([0x0a, 0x02, 0x01, 0xf0]):
            field_idx = section[i+4]
            rest = section[i+5:min(i+35, len(section))]

            if len(rest) >= 5 and rest[0] == 0x0c and rest[1] == 0x03:
                tc = struct.unpack('>H', rest[2:4])[0]
                st = rest[4]
                field_data[field_idx] = {"type_code": tc, "sub_type": st}
                i += 5
                continue

            if len(rest) >= 9 and rest[0] == 0x06:
                val = struct.unpack('>d', rest[1:9])[0]
                if -1e15 < val < 1e15:
                    field_data[field_idx] = {"double": val}
                i += 5
                continue

        i += 1

    # Map fields to source option parameters
    # Field 1: applies_to
    f1 = field_data.get(1, {})
    if "sub_type" in f1:
        result["applies_to"] = _APPLIES_TO_MAP.get(f1["sub_type"], f"enum_{f1['sub_type']}")

    # Field 2: source_type
    f2 = field_data.get(2, {})
    if "sub_type" in f2:
        result["type"] = _SOURCE_TYPE_MAP.get(f2["sub_type"], f"enum_{f2['sub_type']}")

    # Fields 3-7: doubles
    double_fields = {idx: f["double"] for idx, f in field_data.items() if "double" in f}

    if 3 in double_fields:
        result["value"] = double_fields[3]
    if 4 in double_fields:
        result["linear_coefficient"] = double_fields[4]
    if 5 in double_fields:
        result["power"] = double_fields[5]

    # Non-linear curve detection: look for paired doubles beyond field 7
    # Curve points are stored as consecutive (temperature, power) pairs
    is_nonlinear = result.get("type") == "non_linear"

    if is_nonlinear:
        curve_fields = sorted(
            [(idx, val) for idx, val in double_fields.items() if idx > 7],
            key=lambda x: x[0],
        )
        # Try pairing: even fields = temperature, odd fields = power
        if len(curve_fields) >= 2:
            j = 0
            while j + 1 < len(curve_fields):
                temp = curve_fields[j][1]
                power = curve_fields[j + 1][1]
                curve_points.append({"temperature": temp, "power": power})
                j += 2

        # If no curve from high fields, scan for paired doubles in the section
        if not curve_points:
            curve_points = _scan_curve_doubles(reader, section_offset, section_end)

        if curve_points:
            result["curve"] = curve_points

    return result


def _scan_curve_doubles(reader, base: int, end: int) -> List[Dict[str, float]]:
    """Scan for physically plausible temperature-power pairs in a binary range.

    Heuristic: pairs of doubles where first is temperature (-50 to 500 C)
    and second is power (0 to 10000 W), with monotonically increasing temperatures.
    """
    doubles = reader._read_relative_doubles(base, 0, end - base)
    # Filter to physically plausible ranges
    candidates = []
    for rel, val in doubles:
        if -50 <= val <= 500:
            candidates.append(("temp", rel, val))
        elif 0 < val <= 10000:
            candidates.append(("power", rel, val))

    # Try to find alternating temp-power pairs
    points = []
    i = 0
    while i < len(candidates) - 1:
        kind1, rel1, val1 = candidates[i]
        kind2, rel2, val2 = candidates[i + 1]
        # Expect temp followed by power, close together
        if kind1 == "temp" and kind2 == "power" and 0 < rel2 - rel1 < 30:
            if not points or val1 > points[-1]["temperature"]:
                points.append({"temperature": val1, "power": val2})
                i += 2
                continue
        i += 1

    return points if len(points) >= 2 else []


def extract_sources_from_pdml(filepath: str) -> Dict:
    """Extract source attributes directly from PDML binary."""
    from pdml_tools.pdml_to_floxml_converter import PDMLBinaryReader

    reader = PDMLBinaryReader(filepath)
    data = reader.read()

    # Collect source attribute names (0x01E0) and their 0x01F0 option sections
    source_names: List[Dict] = []
    option_sections: List[Dict] = []
    all_tagged = sorted(reader.tagged_strings, key=lambda r: r['offset'])

    for rec in all_tagged:
        if rec['type_code'] == 0x01E0:
            source_names.append({"name": rec['value'], "offset": rec['offset']})
        elif rec['type_code'] == 0x01F0:
            option_sections.append({"offset": rec['offset']})

    # Also find source geometry nodes (0x02C0) for reference mapping
    source_geom_refs: Dict[str, List[str]] = {}
    for rec in all_tagged:
        if rec['type_code'] == 0x02C0:
            name = rec['value']
            # The source attribute reference is stored near the geometry node
            doubles = reader._read_relative_doubles(rec['offset'], 0, 200)
            # Look for the source attribute reference in geometry node post_elements
            # For now just record that this geometry source exists
            source_geom_refs.setdefault(name, [])

    # Associate 0x01F0 option sections with source names
    # Each source name is followed by its option sections
    results: List[Dict] = []
    for src_info in source_names:
        src_name = src_info["name"]
        src_offset = src_info["offset"]

        # Find option sections between this source name and the next source name
        next_src_offsets = [
            s["offset"] for s in source_names if s["offset"] > src_offset
        ]
        next_src = min(next_src_offsets) if next_src_offsets else len(reader.data)

        src_options: List[Dict] = []
        for opt_sec in option_sections:
            opt_offset = opt_sec["offset"]
            if opt_offset <= src_offset:
                continue
            if opt_offset >= next_src:
                break

            # Find extent of this option section
            next_offsets = [
                r['offset'] for r in all_tagged if r['offset'] > opt_offset
            ]
            opt_end = min(next_offsets) if next_offsets else opt_offset + 600

            opt_data = _extract_source_fields(reader, opt_offset, opt_end)
            if opt_data:
                src_options.append(opt_data)

        entry: Dict[str, Any] = {"name": src_name}
        if src_options:
            entry["source_options"] = src_options

        # Geometry references
        geom_refs = []
        for rec in all_tagged:
            if rec['type_code'] == 0x02C0:
                # Check if this geometry source references this source attribute
                # The reference is stored in the geometry node's post_elements
                # For now, we look for the source name nearby
                pass

        results.append(entry)

    return {"sources": results}


def extract_sources_from_pdml_diagnostic(filepath: str) -> None:
    """Print raw binary diagnostic for source-related data in PDML."""
    from pdml_tools.pdml_to_floxml_converter import PDMLBinaryReader

    reader = PDMLBinaryReader(filepath)
    data = reader.read()
    raw = reader.data

    print("=" * 70)
    print(f"PDML Source Diagnostic: {filepath}")
    print("=" * 70)

    # Source attribute names (0x01E0)
    source_names = [r for r in reader.tagged_strings if r['type_code'] == 0x01E0]
    option_sections = [r for r in reader.tagged_strings if r['type_code'] == 0x01F0]
    source_nodes = [r for r in reader.tagged_strings if r['type_code'] == 0x02C0]

    print(f"\nSource attribute names (0x01E0): {len(source_names)}")
    for rec in source_names:
        print(f'  offset={rec["offset"]:6d}  value="{rec["value"]}"')

    print(f"\nSource option sections (0x01F0): {len(option_sections)}")
    for rec in option_sections:
        offset = rec["offset"]
        nexts = [r['offset'] for r in reader.tagged_strings if r['offset'] > offset]
        end = min(nexts, default=offset + 600)

        print(f'\n  Section at offset {offset} (size={end - offset}B):')

        # Dump hex
        section = raw[offset:end]
        for j in range(0, min(len(section), 200), 16):
            hex_part = ' '.join(f'{b:02x}' for b in section[j:j+16])
            ascii_part = ''.join(chr(b) if 32 <= b < 127 else '.' for b in section[j:j+16])
            print(f'    +{j:3d}: {hex_part:<48s} {ascii_part}')

        # Parse fields
        fields = reader._scan_typed_fields(offset, end, 0x01F0)
        if fields:
            print(f'    Typed fields:')
            for idx in sorted(fields.keys()):
                print(f'      field[{idx}]: {fields[idx]}')

        # All doubles
        doubles = reader._read_relative_doubles(offset, 0, end - offset)
        meaningful = [(r, v) for r, v in doubles if abs(v) > 1e-10 and abs(v) < 1e10]
        if meaningful:
            print(f'    Doubles:')
            for r, v in meaningful:
                print(f'      rel={r:4d} val={v:.10g}')

    print(f"\nSource geometry nodes (0x02C0): {len(source_nodes)}")
    for rec in source_nodes:
        print(f'  offset={rec["offset"]:6d}  value="{rec["value"]}"')

    print("\n" + "=" * 70)


# ============================================================================
# FloXML source extraction
# ============================================================================

def _parse_curve(curve_elem: ET.Element) -> List[Dict[str, float]]:
    points = []
    for pt in curve_elem.findall("power_temp_curve_point"):
        temp = _float_text(pt, "temperature")
        power = _float_text(pt, "power")
        points.append({"temperature": temp, "power": power})
    return points


def _parse_source_option(opt: ET.Element) -> Dict[str, Any]:
    entry: Dict[str, Any] = {}
    v = _text(opt, "applies_to")
    if v is not None:
        entry["applies_to"] = v
    v = _text(opt, "type")
    if v is not None:
        entry["type"] = v
    if opt.find("power") is not None:
        entry["power"] = _float_text(opt, "power")
    if opt.find("value") is not None:
        entry["value"] = _float_text(opt, "value")
    if opt.find("linear_coefficient") is not None:
        entry["linear_coefficient"] = _float_text(opt, "linear_coefficient")
    v = _text(opt, "transient")
    if v is not None:
        entry["transient"] = v
    curve_elem = opt.find("non_linear_curve")
    if curve_elem is not None:
        curve = _parse_curve(curve_elem)
        if curve:
            entry["curve"] = curve
    return entry


def _parse_source_att(elem: ET.Element) -> Dict[str, Any]:
    entry: Dict[str, Any] = {}
    v = _text(elem, "name")
    if v is not None:
        entry["name"] = v
    v = _text(elem, "notes")
    if v is not None:
        entry["notes"] = v

    opts_elem = elem.find("source_options")
    if opts_elem is not None:
        options = [_parse_source_option(o) for o in opts_elem.findall("option")]
        if options:
            entry["source_options"] = options
    else:
        single: Dict[str, Any] = {}
        for key in ("applies_to", "type", "transient"):
            v = _text(elem, key)
            if v is not None:
                single[key] = v
        for key in ("power", "value", "linear_coefficient"):
            if elem.find(key) is not None:
                single[key] = _float_text(elem, key)
        curve_elem = elem.find("non_linear_curve")
        if curve_elem is not None:
            curve = _parse_curve(curve_elem)
            if curve:
                single["curve"] = curve
        if single:
            entry["source_options"] = [single]

    return entry


def extract_sources(root: ET.Element) -> List[Dict]:
    results: List[Dict] = []
    attributes = root.find("attributes")
    if attributes is None:
        return results
    sources = attributes.find("sources")
    if sources is None:
        return results
    for sa in sources.findall("source_att"):
        entry = _parse_source_att(sa)
        if entry:
            results.append(entry)
    return results


def extract_source_references(root: ET.Element) -> Dict[str, List[str]]:
    refs: Dict[str, List[str]] = {}
    for elem in root.iter():
        tag = _strip_ns(elem.tag)
        source_ref = _text(elem, "source")
        name = _text(elem, "name")
        if source_ref and name and tag not in ("source_att",):
            refs.setdefault(source_ref, []).append(name)
    return refs


def extract_all_from_xml(root: ET.Element) -> Dict:
    sources = extract_sources(root)
    references = extract_source_references(root)
    for src in sources:
        name = src.get("name", "")
        if name in references:
            src["geometry_objects"] = references[name]
    return {"sources": sources}


# ============================================================================
# Entry: auto-detect format
# ============================================================================

def extract_all(filepath: str) -> Dict:
    """Auto-detect format and extract sources."""
    if is_binary_pdml(filepath):
        print(f"[INFO] Detected binary PDML, extracting directly...", file=sys.stderr)
        return extract_sources_from_pdml(filepath)
    else:
        tree = ET.parse(filepath)
        root = tree.getroot()
        return extract_all_from_xml(root)


# ============================================================================
# Summary + CSV export
# ============================================================================

def print_summary(config: Dict) -> None:
    sources = config.get("sources", [])

    print("=" * 60)
    print("Source Extract Results")
    print("=" * 60)

    if not sources:
        print("\n  (no sources found)")
    else:
        print(f"\nSources ({len(sources)}):")
        for src in sources:
            name = src.get("name", "<unnamed>")
            notes = src.get("notes", "")
            geom = src.get("geometry_objects", [])

            print(f"\n  [{name}]" + (f"  ({notes})" if notes else ""))
            if geom:
                print(f"    used by: {', '.join(geom)}")

            opts = src.get("source_options", [])
            for i, opt in enumerate(opts):
                applies = opt.get("applies_to", "?")
                stype = opt.get("type", "?")
                print(f"    option[{i}]: applies_to={applies}, type={stype}")

                if stype == "non_linear" and "curve" in opt:
                    curve = opt["curve"]
                    print(f"      curve ({len(curve)} points):")
                    for pt in curve:
                        print(f"        T={pt['temperature']:.6g}  P={pt['power']:.6g}")
                elif "power" in opt:
                    print(f"      power={opt['power']:.6g}")
                if "value" in opt:
                    print(f"      value={opt['value']:.6g}")

    print("\n" + "=" * 60)


def export_csv(config: Dict, output_dir: str) -> None:
    os.makedirs(output_dir, exist_ok=True)
    count = 0
    for src in config.get("sources", []):
        name = src.get("name", "Source")
        for opt in src.get("source_options", []):
            curve = opt.get("curve")
            if not curve:
                continue
            safe_name = name.replace(" ", "_").replace("/", "_")
            csv_path = os.path.join(output_dir, f"{safe_name}.csv")
            with open(csv_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(["temperature", "power"])
                for pt in curve:
                    writer.writerow([pt["temperature"], pt["power"]])
            print(f"[OK] {csv_path} ({len(curve)} points)")
            count += 1
    if count == 0:
        print("[WARN] No non-linear curves found to export", file=sys.stderr)
    else:
        print(f"[OK] Exported {count} curve(s) to {output_dir}/")


# ============================================================================
# CLI
# ============================================================================

def main() -> int:
    parser = argparse.ArgumentParser(
        description="Extract source attributes from PDML/FloXML to JSON/CSV",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python pdml_tools/pdml_extract_sources.py model.pdml -o sources.json
  python pdml_tools/pdml_extract_sources.py model.xml -o sources.json
  python pdml_tools/pdml_extract_sources.py model.pdml --summary
  python pdml_tools/pdml_extract_sources.py model.pdml --csv curves/
  python pdml_tools/pdml_extract_sources.py model.pdml --diag

Output JSON can be used directly:
  python -m floxml_tools.floxml_nonlinear_source input.xml --config sources.json -o output.xml
        """,
    )
    parser.add_argument("input", help="Input PDML or FloXML file")
    parser.add_argument("-o", "--output", help="Output JSON file path")
    parser.add_argument("--summary", action="store_true", help="Print summary")
    parser.add_argument("--csv", metavar="DIR",
                        help="Export non-linear curves as individual CSV files to DIR")
    parser.add_argument("--diag", action="store_true",
                        help="Print raw binary diagnostic (PDML only)")
    args = parser.parse_args()

    input_path = Path(args.input)
    if not input_path.exists():
        print(f"[ERROR] File not found: {input_path}", file=sys.stderr)
        return 1

    try:
        if args.diag:
            if not is_binary_pdml(str(input_path)):
                print("[ERROR] --diag only works with PDML binary files", file=sys.stderr)
                return 1
            extract_sources_from_pdml_diagnostic(str(input_path))
            return 0

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

    if args.csv:
        export_csv(config, args.csv)

    if args.output:
        output_path = Path(args.output)
        with output_path.open("w", encoding="utf-8") as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        print(f"[OK] Output: {output_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
