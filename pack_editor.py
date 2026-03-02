#!/usr/bin/env python3
"""
FloTHERM Pack 文件处理工具
Pack 文件是 zip 格式的压缩包，包含项目文件和结果

功能:
    - 解压 pack 文件
    - 查看/修改内部 XML 文件
    - 重新打包
    - 提取 ECXML

使用方法:
    python pack_editor.py model.pack --list                    # 列出内容
    python pack_editor.py model.pack --extract ./extracted     # 解压
    python pack_editor.py model.pack --to-ecxml output.ecxml   # 转换为 ECXML
    python pack_editor.py model.pack --set-power U1 15.0 -o modified.pack  # 修改功耗
"""

import os
import sys
import zipfile
import argparse
import tempfile
import shutil
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import xml.etree.ElementTree as ET


class PackFileHandler:
    """Pack 文件处理器"""

    def __init__(self, pack_path: str):
        self.pack_path = pack_path
        self.temp_dir = None
        self._validate()

    def _validate(self):
        """验证 pack 文件"""
        if not os.path.exists(self.pack_path):
            raise FileNotFoundError(f"Pack 文件不存在: {self.pack_path}")

        if not zipfile.is_zipfile(self.pack_path):
            raise ValueError(f"不是有效的 Pack 文件: {self.pack_path}")

    def list_contents(self) -> List[Dict]:
        """列出 pack 文件内容"""
        contents = []
        with zipfile.ZipFile(self.pack_path, 'r') as zf:
            for info in zf.infolist():
                contents.append({
                    "name": info.filename,
                    "size": info.file_size,
                    "compressed_size": info.compress_size,
                    "is_dir": info.is_dir(),
                    "modified": datetime(*info.date_time).isoformat()
                })
        return contents

    def print_contents(self):
        """打印 pack 文件内容"""
        contents = self.list_contents()
        print(f"\n{'='*60}")
        print(f"Pack 文件内容: {self.pack_path}")
        print(f"{'='*60}")
        print(f"{'文件名':<40} {'大小':>12}")
        print(f"{'-'*60}")

        total_size = 0
        for item in contents:
            if not item['is_dir']:
                size_str = self._format_size(item['size'])
                print(f"{item['name']:<40} {size_str:>12}")
                total_size += item['size']

        print(f"{'-'*60}")
        print(f"总计: {len([i for i in contents if not i['is_dir']])} 个文件, {self._format_size(total_size)}")
        print(f"{'='*60}\n")

    def extract(self, output_dir: str) -> str:
        """解压 pack 文件"""
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        with zipfile.ZipFile(self.pack_path, 'r') as zf:
            zf.extractall(output_dir)

        print(f"[INFO] 已解压到: {output_dir}")
        return str(output_dir)

    def _find_main_xml(self, extract_dir: str) -> Optional[str]:
        """查找主 XML 文件"""
        # 常见的主文件名
        main_files = ['group.pdml', 'project.pdml', 'model.xml', 'project.xml']

        for root, dirs, files in os.walk(extract_dir):
            for f in files:
                if f.lower() in main_files or f.endswith('.pdml'):
                    return os.path.join(root, f)

        # 如果没找到，返回第一个 XML/PDML 文件
        for root, dirs, files in os.walk(extract_dir):
            for f in files:
                if f.endswith(('.xml', '.pdml')):
                    return os.path.join(root, f)

        return None

    def to_ecxml(self, output_path: str) -> str:
        """
        将 pack 转换为 ecxml 格式
        注意：这只是提取内部的 XML，可能需要 FloTHERM 来做完整转换
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            # 解压
            self.extract(temp_dir)

            # 查找主 XML
            main_xml = self._find_main_xml(temp_dir)
            if main_xml:
                # 复制到输出路径
                shutil.copy(main_xml, output_path)
                print(f"[INFO] 已提取 XML 到: {output_path}")
                return output_path
            else:
                raise ValueError("Pack 文件中未找到 XML 文件")

    def get_xml_structure(self) -> Dict:
        """获取 pack 内部 XML 结构"""
        with tempfile.TemporaryDirectory() as temp_dir:
            self.extract(temp_dir)
            main_xml = self._find_main_xml(temp_dir)

            if not main_xml:
                return {"error": "未找到 XML 文件"}

            tree = ET.parse(main_xml)
            root = tree.getroot()

            def get_structure(elem, depth=0):
                if depth > 3:
                    return {"...": "truncated"}

                result = {
                    "tag": self._strip_ns(elem.tag),
                    "attrs": dict(list(elem.attrib.items())[:5]),
                    "children": []
                }

                for child in elem:
                    result["children"].append(get_structure(child, depth + 1))

                return result

            return get_structure(root)

    def modify_parameter(self, component_name: str, power: float,
                         output_path: str = None) -> bool:
        """
        修改 pack 文件中的参数

        Args:
            component_name: 器件名称
            power: 功耗值 (W)
            output_path: 输出路径（默认覆盖原文件）
        """
        if output_path is None:
            output_path = self.pack_path

        with tempfile.TemporaryDirectory() as temp_dir:
            # 解压
            self.extract(temp_dir)

            # 查找并修改 XML
            modified = False
            for root, dirs, files in os.walk(temp_dir):
                for f in files:
                    if f.endswith(('.xml', '.pdml')):
                        xml_path = os.path.join(root, f)
                        if self._modify_xml_power(xml_path, component_name, power):
                            modified = True
                            print(f"[INFO] 已修改: {f}")

            if not modified:
                print(f"[WARN] 未找到器件: {component_name}")
                return False

            # 重新打包
            self._create_pack(temp_dir, output_path)
            print(f"[INFO] 已保存到: {output_path}")
            return True

    def _modify_xml_power(self, xml_path: str, component_name: str, power: float) -> bool:
        """修改 XML 文件中的功耗"""
        try:
            tree = ET.parse(xml_path)
            root = tree.getroot()

            modified = False
            for elem in root.iter():
                # 查找匹配的器件
                name = elem.get('name', elem.get('Name', ''))
                if name == component_name or component_name.lower() in name.lower():
                    # 查找功耗字段
                    for child in elem:
                        tag_lower = self._strip_ns(child.tag).lower()
                        if 'power' in tag_lower or 'heat' in tag_lower:
                            child.text = str(power)
                            modified = True
                            print(f"       修改 {name}: {power}W")

            if modified:
                tree.write(xml_path, encoding='utf-8', xml_declaration=True)

            return modified

        except Exception as e:
            print(f"[ERROR] 修改 XML 失败: {e}")
            return False

    def _create_pack(self, source_dir: str, output_path: str):
        """创建 pack 文件"""
        with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zf:
            for root, dirs, files in os.walk(source_dir):
                for f in files:
                    file_path = os.path.join(root, f)
                    arc_name = os.path.relpath(file_path, source_dir)
                    zf.write(file_path, arc_name)

    def batch_modify(self, power_map: Dict[str, float],
                     output_path: str = None) -> Tuple[int, int]:
        """
        批量修改功耗

        Args:
            power_map: {器件名: 功耗} 字典
            output_path: 输出路径

        Returns:
            (成功数, 总数)
        """
        if output_path is None:
            output_path = self.pack_path

        with tempfile.TemporaryDirectory() as temp_dir:
            self.extract(temp_dir)

            success_count = 0
            for root, dirs, files in os.walk(temp_dir):
                for f in files:
                    if f.endswith(('.xml', '.pdml')):
                        xml_path = os.path.join(root, f)
                        for name, power in power_map.items():
                            if self._modify_xml_power(xml_path, name, power):
                                success_count += 1

            self._create_pack(temp_dir, output_path)
            print(f"[INFO] 已保存到: {output_path}")

            return success_count, len(power_map)

    def _strip_ns(self, tag: str) -> str:
        """去除命名空间"""
        if '}' in tag:
            return tag.split('}')[1]
        return tag

    def _format_size(self, size: int) -> str:
        """格式化文件大小"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} TB"


def main():
    parser = argparse.ArgumentParser(
        description='FloTHERM Pack 文件处理工具',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
示例:
  # 列出 pack 文件内容
  python pack_editor.py model.pack --list

  # 解压 pack 文件
  python pack_editor.py model.pack --extract ./extracted

  # 提取 XML
  python pack_editor.py model.pack --to-ecxml output.xml

  # 修改功耗
  python pack_editor.py model.pack --set-power U1_CPU 15.0 -o modified.pack

  # 批量修改功耗
  python pack_editor.py model.pack --power-config power.json -o modified.pack
        '''
    )

    parser.add_argument('input', help='输入 Pack 文件')
    parser.add_argument('-o', '--output', help='输出文件路径')

    # 操作命令
    parser.add_argument('--list', '-l', action='store_true', help='列出 pack 文件内容')
    parser.add_argument('--extract', metavar='DIR', help='解压到指定目录')
    parser.add_argument('--to-ecxml', metavar='FILE', help='转换为 ECXML 文件')
    parser.add_argument('--set-power', nargs=2, metavar=('NAME', 'POWER'),
                       help='设置器件功耗')
    parser.add_argument('--power-config', help='从 JSON 文件批量加载功耗设置')
    parser.add_argument('--info', action='store_true', help='显示详细信息')

    args = parser.parse_args()

    try:
        handler = PackFileHandler(args.input)

        # 列出内容
        if args.list:
            handler.print_contents()
            return

        # 解压
        if args.extract:
            handler.extract(args.extract)
            return

        # 转换为 ECXML
        if args.to_ecxml:
            handler.to_ecxml(args.to_ecxml)
            return

        # 显示详细信息
        if args.info:
            handler.print_contents()
            structure = handler.get_xml_structure()
            print("\nXML 结构:")
            import json
            print(json.dumps(structure, indent=2, ensure_ascii=False)[:2000])
            return

        # 设置功耗
        if args.set_power:
            name, power = args.set_power
            power = float(power)
            handler.modify_parameter(name, power, args.output)
            return

        # 批量设置功耗
        if args.power_config:
            import json
            with open(args.power_config, 'r', encoding='utf-8') as f:
                power_map = json.load(f)
            success, total = handler.batch_modify(power_map, args.output)
            print(f"[INFO] 成功修改 {success}/{total} 个器件")
            return

        # 默认显示内容
        handler.print_contents()

    except Exception as e:
        print(f"[ERROR] {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
