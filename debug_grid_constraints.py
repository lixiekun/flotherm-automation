#!/usr/bin/env python3
"""Diagnostic: dump grid constraint and region localized_grid from PDML binary."""
import sys
import struct
from pdml_tools.pdml_to_floxml_converter import PDMLBinaryReader, FloXMLBuilder
import xml.etree.ElementTree as ET


def diagnose(pdml_path: str):
    print(f"=== Diagnosing: {pdml_path} ===\n")

    reader = PDMLBinaryReader(pdml_path)
    reader.read()

    # 1. Raw binary fields for grid constraints
    print("--- Grid Constraint Raw Binary Fields ---")
    gc_positions = []
    for r in reader.tagged_strings:
        if r['type_code'] == 0x0190:
            gc_positions.append((r['offset'], r['value']))

    if not gc_positions:
        print("  (none found by type_code 0x0190)")
        for r in reader.tagged_strings:
            if 'Grid Constraint' in r['value']:
                gc_positions.append((r['offset'], r['value']))
        if gc_positions:
            print("  (found by name fallback)")

    for gc_offset, gc_name in gc_positions:
        string_end = gc_offset + 10 + len(gc_name.encode('utf-8'))
        scan_start = string_end
        scan_end = min(scan_start + 600, len(reader.data) - 20)

        print(f"\n  GC: {gc_name!r} (offset={gc_offset})")
        i = scan_start
        while i < scan_end:
            if not (reader.data[i] == 0x0a and i + 4 < scan_end
                    and reader.data[i + 1] == 0x02
                    and reader.data[i + 2] == 0x01
                    and reader.data[i + 3] == 0x90):
                i += 1
                continue
            field_index = reader.data[i + 4]
            j = i + 5
            raw = reader.data[j:j+30]
            hex_str = ' '.join(f'{b:02x}' for b in raw)
            desc = ""

            if j + 4 < scan_end and reader.data[j] == 0x0c and reader.data[j + 1] == 0x03:
                tc = struct.unpack('>H', reader.data[j + 2:j + 4])[0]
                vt = reader.data[j + 4]
                if vt == 0x02 and j + 13 < scan_end and reader.data[j + 5] == 0x06:
                    dv = struct.unpack('>d', reader.data[j + 6:j + 14])[0]
                    desc = f"tc=0x{tc:04X} double={dv}"
                elif vt == 0x01:
                    desc = f"tc=0x{tc:04X} vt=0x01 flag={reader.data[j+5]}"
                elif vt == 0x02:
                    # compound flags
                    flags = []
                    pos = j + 5
                    while pos + 4 < scan_end and len(flags) < 5:
                        flags.append(reader.data[pos])
                        pos += 5
                    ncc_map = {0: 'max_size', 1: 'min_number'}
                    ncc_strs = [f"{f}({ncc_map.get(f, '?')})" for f in flags]
                    desc = f"tc=0x{tc:04X} vt=0x02 compound_flags={ncc_strs}"
                else:
                    desc = f"tc=0x{tc:04X} vt=0x{vt:02x}"
            elif j + 8 < scan_end and reader.data[j] == 0x06:
                dv = struct.unpack('>d', reader.data[j + 1:j + 9])[0]
                desc = f"direct double={dv}"

            print(f"    field[{field_index:2d}]: {hex_str}")
            if desc:
                print(f"             -> {desc}")
            i += 5
            while i < scan_end:
                if reader.data[i] == 0x0a and i + 3 < scan_end and reader.data[i + 1] == 0x02:
                    break
                i += 1

    # 2. Region binary: field[4] and field[5]
    print("\n\n--- Region Raw Binary (field 4=gc_index, field 5=localized_grid) ---")
    region_names = []
    for r in reader.tagged_strings:
        if r['type_code'] == 0x0150:
            region_names.append((r['offset'], r['value']))

    if not region_names:
        # Fallback: search for "Region" or "GR-" strings
        for r in reader.tagged_strings:
            if r['value'] in ('Region',) or r['value'].startswith('GR-'):
                region_names.append((r['offset'], r['value']))

    for r_offset, r_name in region_names[:10]:  # limit to first 10
        scan_start = r_offset + 10 + len(r_name.encode('utf-8'))
        scan_end = min(scan_start + 300, len(reader.data) - 10)

        print(f"\n  Region: {r_name!r}")
        for i in range(scan_start, scan_end):
            if (reader.data[i] == 0x0a and i + 4 < scan_end
                    and reader.data[i + 1] == 0x01
                    and reader.data[i + 2] == 0x00
                    and reader.data[i + 3] == 0x30):
                field_index = reader.data[i + 4]
                if field_index in (4, 5):
                    j = i + 5
                    raw = reader.data[j:j+10]
                    hex_str = ' '.join(f'{b:02x}' for b in raw)
                    desc = ""
                    if j + 4 < scan_end and reader.data[j] == 0x0c and reader.data[j + 1] == 0x03:
                        tc = struct.unpack('>H', reader.data[j + 2:j + 4])[0]
                        vt = reader.data[j + 4]
                        flag = reader.data[j + 5]
                        lg = "true" if (vt == 0x01 and flag == 1) else "false"
                        if field_index == 4:
                            desc = f"tc=0x{tc:04X} vt=0x{vt:02x} gc_index={flag} (1-based)"
                        else:
                            desc = f"tc=0x{tc:04X} vt=0x{vt:02x} flag={flag} => localized_grid={lg}"
                    print(f"    field[{field_index}]: {hex_str}  -> {desc}")
                i += 5
                while i < scan_end:
                    if reader.data[i] == 0x0a and i + 3 < scan_end:
                        break
                    i += 1

    # 3. Final parsed output
    print("\n\n--- Parsed Output (from FloXMLBuilder) ---")
    builder = FloXMLBuilder()
    root = builder.build(reader.read() if hasattr(reader, '_gc_names_cache') else reader.read())

    for gc_att in root.iter('grid_constraint_att'):
        name_el = gc_att.find('name')
        ncc = gc_att.find('number_cells_control')
        min_num = gc_att.find('min_number')
        max_sz = gc_att.find('max_size')
        hi = gc_att.find('high_inflation')
        hi_ncc = hi.find('number_cells_control') if hi is not None else None
        hi_min = hi.find('min_number') if hi is not None else None
        print(f"  grid_constraint: {name_el.text if name_el is not None else '?'}")
        print(f"    number_cells_control: {ncc.text if ncc is not None else 'MISSING'}")
        if min_num is not None:
            print(f"    min_number: {min_num.text}")
        if max_sz is not None:
            print(f"    max_size: {max_sz.text}")
        if hi is not None:
            print(f"    high_inflation.number_cells_control: {hi_ncc.text if hi_ncc is not None else 'MISSING'}")
            print(f"    high_inflation.min_number: {hi_min.text if hi_min is not None else 'MISSING'}")

    for reg in root.iter('region'):
        name_el = reg.find('name')
        lg = reg.find('localized_grid')
        agc = reg.find('all_grid_constraint')
        xgc = reg.find('x_grid_constraint')
        print(f"  region: {name_el.text if name_el is not None else '?'}")
        print(f"    localized_grid: {lg.text if lg is not None else 'MISSING'}")
        if agc is not None:
            print(f"    all_grid_constraint: {agc.text}")
        if xgc is not None:
            print(f"    x_grid_constraint: {xgc.text}")

    print("\n=== Done ===")


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python debug_grid_constraints.py <file.pdml>")
        sys.exit(1)
    diagnose(sys.argv[1])
