"""调试脚本：分析 PDML 层级结构"""
import sys
from pdml_to_floxml_converter import PDMLBinaryReader

def analyze_hierarchy(pdml_file):
    reader = PDMLBinaryReader(pdml_file)
    reader._extract_strings()
    reader._locate_sections()
    records = list(reader._find_geometry_records())

    print(f"=== 装配体层级分析: {pdml_file} ===")
    print(f"总记录数: {len(records)}")

    # 先看看有哪些类型
    types = set(rec.get('node_type', '?') for rec in records)
    print(f"类型列表: {types}")

    print("\n序号 | Level | 类型 | 名称")
    print("-" * 60)

    assembly_count = 0
    for i, rec in enumerate(records):
        node_type = rec.get('node_type', '?')
        if node_type == 'assembly':
            assembly_count += 1
            level = rec.get('level', '?')
            name = rec.get('name', '?')[:50]
            print(f"{assembly_count:3d}  | L{level}   | {node_type} | {name}")

    if assembly_count == 0:
        print("\n未找到 assembly 类型，显示前 20 条记录:")
        for i, rec in enumerate(records[:20]):
            level = rec.get('level', '?')
            node_type = rec.get('node_type', '?')
            name = rec.get('name', '?')[:40]
            print(f"{i:3d}  | L{level}   | {node_type} | {name}")

    print(f"\n总装配体数: {assembly_count}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python debug_hierarchy.py <pdml文件>")
        sys.exit(1)
    analyze_hierarchy(sys.argv[1])
