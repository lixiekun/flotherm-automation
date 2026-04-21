#!/usr/bin/env python3
"""
Add / modify non-linear source (power vs temperature curve) in FloXML.

FloTHERM non-linear sources define power as a function of temperature
via a lookup table (power_temp_curve_point). This tool writes that table
from a simple JSON config.

Usage:
    python -m floxml_tools.floxml_nonlinear_source input.xml --config sources.json -o output.xml
    python -m floxml_tools.floxml_nonlinear_source input.xml --csv curve.csv --source "Chip Power" -o output.xml
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional
import xml.etree.ElementTree as ET


# ============================================================================
# XML helpers
# ============================================================================

def _append_text(parent: ET.Element, tag: str, text: str) -> ET.Element:
    elem = ET.SubElement(parent, tag)
    elem.text = text
    return elem


def _set_text(parent: ET.Element, tag: str, text: str) -> ET.Element:
    child = parent.find(tag)
    if child is None:
        child = ET.SubElement(parent, tag)
    child.text = text
    return child


# ============================================================================
# Source attribute helpers
# ============================================================================

def _find_or_create_sources_section(root: ET.Element) -> ET.Element:
    """Find or create <attributes><sources> section."""
    attributes = root.find("attributes")
    if attributes is None:
        attributes = ET.Element("attributes")
        root.append(attributes)

    sources = attributes.find("sources")
    if sources is None:
        sources = ET.SubElement(attributes, "sources")
    return sources


def _find_source_by_name(sources: ET.Element, name: str) -> Optional[ET.Element]:
    """Find existing source_att by name."""
    for child in sources.findall("source_att"):
        if (child.findtext("name") or "").strip() == name:
            return child
    return None


def _upsert_source(sources: ET.Element, name: str) -> ET.Element:
    """Find or create a source_att element."""
    existing = _find_source_by_name(sources, name)
    if existing is not None:
        return existing
    elem = ET.SubElement(sources, "source_att")
    _append_text(elem, "name", name)
    return elem


def _apply_curve_to_option(opt_elem: ET.Element, curve: List[Dict[str, float]]) -> None:
    """Write non_linear_curve into a source option element."""
    _set_text(opt_elem, "type", "non_linear")

    # Remove existing curve
    existing = opt_elem.find("non_linear_curve")
    if existing is not None:
        opt_elem.remove(existing)

    curve_elem = ET.SubElement(opt_elem, "non_linear_curve")
    for point in curve:
        pt = ET.SubElement(curve_elem, "power_temp_curve_point")
        _append_text(pt, "temperature", f"{point['temperature']:.6g}")
        _append_text(pt, "power", f"{point['power']:.6g}")


def _apply_source(sources_section: ET.Element, cfg: Dict) -> Optional[ET.Element]:
    """Apply a single source config to the sources section.

    Accepts two formats:
      1. Simple: {"name", "applies_to", "curve": [...]}
      2. Full extract format: {"name", "source_options": [{"applies_to", "curve": [...]}]}

    Sources without a curve are silently skipped (allows round-trip with pdml_extract_sources).
    """
    name = cfg.get("name", "Source")
    elem = _upsert_source(sources_section, name)

    # Collect (applies_to, curve) pairs from either format
    curve_pairs: List[tuple] = []

    # Format 2: source_options list (from pdml_extract_sources)
    source_options = cfg.get("source_options")
    if source_options and isinstance(source_options, list):
        for opt in source_options:
            curve = opt.get("curve", [])
            if curve:
                curve_pairs.append((opt.get("applies_to", "temperature"), curve))
    else:
        # Format 1: simple top-level curve
        curve = cfg.get("curve", [])
        if curve:
            curve_pairs.append((cfg.get("applies_to", "temperature"), curve))

    if not curve_pairs:
        return None

    opts_elem = elem.find("source_options")
    if opts_elem is None:
        opts_elem = ET.SubElement(elem, "source_options")

    for applies_to, curve in curve_pairs:
        target_opt = None
        for opt in opts_elem.findall("option"):
            if (opt.findtext("applies_to") or "").strip() == applies_to:
                target_opt = opt
                break

        if target_opt is None:
            target_opt = ET.SubElement(opts_elem, "option")
            _append_text(target_opt, "applies_to", applies_to)

        _apply_curve_to_option(target_opt, curve)

    return elem


# ============================================================================
# Public API
# ============================================================================

def apply_nonlinear_sources(root: ET.Element, config: Dict) -> ET.Element:
    """Apply all non-linear source configs from JSON dict."""
    source_configs = config.get("sources", [])
    if not source_configs:
        raise ValueError("Config must contain a 'sources' list")

    sources_section = _find_or_create_sources_section(root)
    applied = 0

    for cfg in source_configs:
        result = _apply_source(sources_section, cfg)
        if result is not None:
            applied += 1

    if applied == 0:
        print("[WARN] No non-linear curves found in config (all sources skipped)")
    else:
        print(f"[OK] Applied {applied} non-linear source(s)")
    return root


# ============================================================================
# Config loaders
# ============================================================================

def load_json(path: Path) -> Dict:
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def load_csv(path: Path, source_name: str = "Source", applies_to: str = "temperature") -> Dict:
    """Load curve from CSV file.

    CSV format: temperature,power (with or without header row).
    """
    curve: List[Dict[str, float]] = []
    with path.open("r", encoding="utf-8", newline="") as fh:
        reader = csv.reader(fh)
        for row in reader:
            if len(row) < 2:
                continue
            # Skip header if values aren't numeric
            try:
                temp = float(row[0].strip())
                power = float(row[1].strip())
            except ValueError:
                continue
            curve.append({"temperature": temp, "power": power})

    if not curve:
        raise ValueError(f"No valid data points found in {path}")

    return {
        "sources": [
            {
                "name": source_name,
                "applies_to": applies_to,
                "curve": curve,
            }
        ]
    }


def load_config(path: Path, source_name: str = "Source", applies_to: str = "temperature") -> Dict:
    suffix = path.suffix.lower()
    if suffix == ".csv":
        return load_csv(path, source_name, applies_to)
    return load_json(path)


# ============================================================================
# XML formatting
# ============================================================================

def indent_xml(elem: ET.Element, level: int = 0) -> None:
    indent = "\n" + ("    " * level)
    if len(elem):
        if not elem.text or not elem.text.strip():
            elem.text = indent + "    "
        for child in elem:
            indent_xml(child, level + 1)
        if not elem[-1].tail or not elem[-1].tail.strip():
            elem[-1].tail = indent
    if level and (not elem.tail or not elem.tail.strip()):
        elem.tail = indent


# ============================================================================
# CLI
# ============================================================================

def main() -> int:
    parser = argparse.ArgumentParser(
        description="Add / modify non-linear source curves (power vs temperature) in FloXML",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # From JSON config (recommended)
  python -m floxml_tools.floxml_nonlinear_source input.xml --config sources.json -o output.xml

  # From CSV file
  python -m floxml_tools.floxml_nonlinear_source input.xml --csv curve.csv --source "Chip" -o output.xml

JSON config format:
  {
    "sources": [
      {
        "name": "Chip_Power",
        "applies_to": "temperature",
        "curve": [
          {"temperature": 25, "power": 0},
          {"temperature": 50, "power": 10},
          {"temperature": 100, "power": 15}
        ]
      }
    ]
  }

CSV format (temperature,power):
  temperature,power
  25,0
  50,10
  100,15
        """,
    )
    parser.add_argument("input", help="Input FloXML file")
    parser.add_argument("--config", help="JSON config file with source definitions")
    parser.add_argument("--csv", help="CSV file with temperature,power columns")
    parser.add_argument("--source", default="Source",
                        help="Source name (used with --csv, default: Source)")
    parser.add_argument("--applies-to", default="temperature",
                        help="Variable type (used with --csv, default: temperature)")
    parser.add_argument("-o", "--output", help="Output FloXML file")
    parser.add_argument("--create-template", metavar="PATH",
                        help="Create an example JSON template at PATH")
    args = parser.parse_args()

    if args.create_template:
        template = {
            "sources": [
                {
                    "name": "Chip_Power",
                    "applies_to": "temperature",
                    "curve": [
                        {"temperature": 25, "power": 0},
                        {"temperature": 40, "power": 5},
                        {"temperature": 60, "power": 12},
                        {"temperature": 85, "power": 15},
                        {"temperature": 100, "power": 18},
                    ],
                }
            ]
        }
        with open(args.create_template, "w", encoding="utf-8") as f:
            json.dump(template, f, indent=2, ensure_ascii=False)
        print(f"[OK] Template created: {args.create_template}")
        return 0

    if not args.input:
        parser.error("input file is required")
    if not args.config and not args.csv:
        parser.error("--config or --csv is required")

    input_path = Path(args.input)
    output_path = (
        Path(args.output) if args.output
        else input_path.with_name(f"{input_path.stem}_nl_source{input_path.suffix}")
    )

    # Load config
    if args.csv:
        config = load_csv(Path(args.csv), args.source, args.applies_to)
    else:
        config = load_json(Path(args.config))

    # Parse and modify
    tree = ET.parse(input_path)
    root = tree.getroot()
    apply_nonlinear_sources(root, config)
    indent_xml(root)
    tree.write(str(output_path), encoding="utf-8", xml_declaration=True)

    print(f"[OK] Output: {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
