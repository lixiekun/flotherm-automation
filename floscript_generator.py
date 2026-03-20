#!/usr/bin/env python3
"""
FloSCRIPT 宏生成器

快速生成各种 FloTHERM 自动化宏脚本

支持的宏类型:
    - export_floxml: 导出 FloXML
    - export_pack: 导出 Pack
    - solve: 求解模型
    - batch: 批量操作
    - custom: 自定义宏
"""

import os
import argparse
from datetime import datetime
from pathlib import Path
from typing import List, Optional


class FloScriptGenerator:
    """FloSCRIPT 宏生成器"""

    def __init__(self):
        self.commands = []

    def add_open(self, file_path: str) -> 'FloScriptGenerator':
        """添加打开文件命令"""
        self.commands.append(f'    <open file="{os.path.abspath(file_path)}"/>')
        return self

    def add_save(self, file_path: str = None) -> 'FloScriptGenerator':
        """添加保存命令"""
        if file_path:
            self.commands.append(f'    <save file="{os.path.abspath(file_path)}"/>')
        else:
            self.commands.append('    <save/>')
        return self

    def add_save_as(self, file_path: str) -> 'FloScriptGenerator':
        """添加另存为命令"""
        self.commands.append(f'    <save file="{os.path.abspath(file_path)}"/>')
        return self

    def add_close(self) -> 'FloScriptGenerator':
        """添加关闭命令"""
        self.commands.append('    <close/>')
        return self

    def add_export_floxml(self, file_path: str) -> 'FloScriptGenerator':
        """添加导出 FloXML 命令"""
        self.commands.append(f'    <export_floxml file="{os.path.abspath(file_path)}"/>')
        return self

    def add_export_pack(self, file_path: str) -> 'FloScriptGenerator':
        """添加导出 Pack 命令"""
        self.commands.append(f'    <export_pack file="{os.path.abspath(file_path)}"/>')
        return self

    def add_solve(self) -> 'FloScriptGenerator':
        """添加求解命令"""
        self.commands.append('    <solve/>')
        return self

    def add_reinitialize(self) -> 'FloScriptGenerator':
        """添加重新初始化命令"""
        self.commands.append('    <reinitialize/>')
        return self

    def add_export_report(self, file_path: str) -> 'FloScriptGenerator':
        """添加导出报告命令"""
        self.commands.append(f'    <export_report file="{os.path.abspath(file_path)}"/>')
        return self

    def add_export_table(self, table_name: str, file_path: str) -> 'FloScriptGenerator':
        """添加导出表格命令"""
        self.commands.append(
            f'    <export_table name="{table_name}" file="{os.path.abspath(file_path)}"/>'
        )
        return self

    def add_custom(self, command: str) -> 'FloScriptGenerator':
        """添加自定义命令"""
        self.commands.append(f'    {command}')
        return self

    def add_comment(self, comment: str) -> 'FloScriptGenerator':
        """添加注释"""
        self.commands.append(f'    <!-- {comment} -->')
        return self

    def generate(self, description: str = None) -> str:
        """生成宏内容"""
        header = f'''<?xml version="1.0" encoding="UTF-8"?>
<xml_log_file version="1.0">'''

        if description:
            header += f'\n    <!-- {description} -->'

        footer = '''</xml_log_file>'''

        return f'{header}\n{chr(10).join(self.commands)}\n{footer}'

    def save(self, file_path: str, description: str = None) -> str:
        """保存宏到文件"""
        content = self.generate(description)
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return file_path

    def clear(self) -> 'FloScriptGenerator':
        """清空命令"""
        self.commands = []
        return self


def generate_solve_macro(input_file: str, output_file: str = None) -> str:
    """生成求解宏"""
    gen = FloScriptGenerator()
    gen.add_comment(f"Generated: {datetime.now().isoformat()}")
    gen.add_open(input_file)
    gen.add_reinitialize()
    gen.add_solve()
    if output_file:
        gen.add_save_as(output_file)
    else:
        gen.add_save()
    gen.add_close()
    return gen.generate(description=f"Solve: {Path(input_file).name}")


def generate_export_floxml_macro(input_file: str, output_file: str) -> str:
    """生成导出 FloXML 宏"""
    gen = FloScriptGenerator()
    gen.add_comment(f"Generated: {datetime.now().isoformat()}")
    gen.add_open(input_file)
    gen.add_export_floxml(output_file)
    gen.add_close()
    return gen.generate(description=f"Export FloXML: {Path(input_file).name}")


def generate_batch_solve_macro(input_files: List[str], output_dir: str) -> str:
    """生成批量求解宏"""
    gen = FloScriptGenerator()
    gen.add_comment(f"Generated: {datetime.now().isoformat()}")
    gen.add_comment(f"Total files: {len(input_files)}")

    for input_file in input_files:
        basename = Path(input_file).stem
        output_file = os.path.join(output_dir, f"{basename}_solved.pack")
        gen.add_comment(f"Process: {basename}")
        gen.add_open(input_file)
        gen.add_reinitialize()
        gen.add_solve()
        gen.add_save_as(output_file)
        gen.add_close()

    return gen.generate(description="Batch Solve")


def generate_batch_export_floxml_macro(input_files: List[str], output_dir: str) -> str:
    """生成批量导出 FloXML 宏"""
    gen = FloScriptGenerator()
    gen.add_comment(f"Generated: {datetime.now().isoformat()}")
    gen.add_comment(f"Total files: {len(input_files)}")

    for input_file in input_files:
        basename = Path(input_file).stem
        output_file = os.path.join(output_dir, f"{basename}.xml")
        gen.add_comment(f"Export: {basename}")
        gen.add_open(input_file)
        gen.add_export_floxml(output_file)
        gen.add_close()

    return gen.generate(description="Batch Export FloXML")


def main():
    parser = argparse.ArgumentParser(
        description='FloSCRIPT 宏生成器',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
示例:
  # 生成导出 FloXML 的宏
  python floscript_generator.py export_floxml model.pack -o output.xml

  # 生成求解宏
  python floscript_generator.py solve model.pack -o solved.pack

  # 批量生成
  python floscript_generator.py batch_export ./input_folder -o ./output_folder

  # 交互式构建
  python floscript_generator.py interactive
        '''
    )

    subparsers = parser.add_subparsers(dest='command', help='命令类型')

    # export_floxml 命令
    export_parser = subparsers.add_parser('export_floxml', help='导出 FloXML')
    export_parser.add_argument('input', help='输入文件')
    export_parser.add_argument('-o', '--output', required=True, help='输出文件')
    export_parser.add_argument('--save-macro', help='保存宏到文件')

    # export_pack 命令
    pack_parser = subparsers.add_parser('export_pack', help='导出 Pack')
    pack_parser.add_argument('input', help='输入文件')
    pack_parser.add_argument('-o', '--output', required=True, help='输出文件')
    pack_parser.add_argument('--save-macro', help='保存宏到文件')

    # solve 命令
    solve_parser = subparsers.add_parser('solve', help='求解模型')
    solve_parser.add_argument('input', help='输入文件')
    solve_parser.add_argument('-o', '--output', help='输出文件（可选）')
    solve_parser.add_argument('--save-macro', help='保存宏到文件')

    # batch_export 命令
    batch_parser = subparsers.add_parser('batch_export', help='批量导出 FloXML')
    batch_parser.add_argument('input_dir', help='输入目录')
    batch_parser.add_argument('-o', '--output', required=True, help='输出目录')
    batch_parser.add_argument('--save-macro', help='保存宏到文件')

    # batch_solve 命令
    batch_solve_parser = subparsers.add_parser('batch_solve', help='批量求解')
    batch_solve_parser.add_argument('input_dir', help='输入目录')
    batch_solve_parser.add_argument('-o', '--output', required=True, help='输出目录')
    batch_solve_parser.add_argument('--save-macro', help='保存宏到文件')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    # 执行命令
    if args.command == 'export_floxml':
        macro = generate_export_floxml_macro(args.input, args.output)
        print(macro)
        if args.save_macro:
            with open(args.save_macro, 'w', encoding='utf-8') as f:
                f.write(macro)
            print(f"\n[INFO] 宏已保存到: {args.save_macro}")

    elif args.command == 'export_pack':
        gen = FloScriptGenerator()
        gen.add_open(args.input)
        gen.add_export_pack(args.output)
        gen.add_close()
        macro = gen.generate()
        print(macro)
        if args.save_macro:
            with open(args.save_macro, 'w', encoding='utf-8') as f:
                f.write(macro)
            print(f"\n[INFO] 宏已保存到: {args.save_macro}")

    elif args.command == 'solve':
        macro = generate_solve_macro(args.input, args.output)
        print(macro)
        if args.save_macro:
            with open(args.save_macro, 'w', encoding='utf-8') as f:
                f.write(macro)
            print(f"\n[INFO] 宏已保存到: {args.save_macro}")

    elif args.command == 'batch_export':
        input_path = Path(args.input_dir)
        files = list(input_path.glob('*.pack')) + list(input_path.glob('*.ecxml'))
        if not files:
            print(f"[ERROR] 未找到 Pack/ECXML 文件: {args.input_dir}")
            return
        macro = generate_batch_export_floxml_macro([str(f) for f in files], args.output)
        print(macro)
        if args.save_macro:
            with open(args.save_macro, 'w', encoding='utf-8') as f:
                f.write(macro)
            print(f"\n[INFO] 宏已保存到: {args.save_macro}")

    elif args.command == 'batch_solve':
        input_path = Path(args.input_dir)
        files = list(input_path.glob('*.pack')) + list(input_path.glob('*.ecxml'))
        if not files:
            print(f"[ERROR] 未找到 Pack/ECXML 文件: {args.input_dir}")
            return
        macro = generate_batch_solve_macro([str(f) for f in files], args.output)
        print(macro)
        if args.save_macro:
            with open(args.save_macro, 'w', encoding='utf-8') as f:
                f.write(macro)
            print(f"\n[INFO] 宏已保存到: {args.save_macro}")


if __name__ == '__main__':
    main()
