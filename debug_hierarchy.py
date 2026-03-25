"""调试脚本：分析 PDML 层级结构"""
import sys
import struct
from pdml_to_floxml_converter import PDMLBinaryReader

def analyze_hierarchy(pdml_file):
    reader = PDMLBinaryReader(pdml_file)
    reader._extract_strings()
    reader._locate_sections()
    records = list(reader._find_geometry_records())

    print(f"=== 装配体层级分析: {pdml_file} ===")
    print(f"总记录数: {len(records)}")

    types = set(rec.get('node_type', '?') for rec in records)
    print(f"类型列表: {types}")

    print("\n=== 所有装配体详情（含原始字节）===")
    print("序号 | Level | 名称 | offset | 前几字节(hex)")
    print("-" * 80)

    assembly_count = 0
    for i, rec in enumerate(records):
        node_type = rec.get('node_type', '?')
        if node_type == 'assembly':
            assembly_count += 1
            level = rec.get('level', '?')
            name = rec.get('name', '?')[:30]
            offset = rec.get('offset', 0)

            # 读取 offset 前面的字节来分析 level 编码
            hex_bytes = ""
            if offset >= 16:
                raw = reader.data[offset-16:offset]
                hex_bytes = raw.hex()

            print(f"{assembly_count:3d}  | L{level}   | {name} | {offset} | {hex_bytes}")

    print(f"\n总装配体数: {assembly_count}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python debug_hierarchy.py <pdml文件>")
        sys.exit(1)
    analyze_hierarchy(sys.argv[1])
