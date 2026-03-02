#!/usr/bin/env python3
"""
FloSCRIPT 运行器 - 整合模型和宏的完整流程

将录制的宏操作与模型文件整合，生成完整的 FloSCRIPT XML 并执行。

支持格式: .pack | .prj | .ecxml | .pdml

使用方法:
    # 基本用法（ECXML + 宏）
    python floscript_runner.py model.ecxml solve_macro.xml -o ./results

    # 基本用法（Pack + 宏）
    python floscript_runner.py model.pack macro.xml -o ./results

    # 修改功耗后运行
    python floscript_runner.py model.ecxml macro.xml -o ./results --power U1_CPU 15.0

    # 批量参数扫描
    python floscript_runner.py model.ecxml macro.xml -o ./results --power-range U1_CPU 5 10 15 20 25

推荐工作流:
    1. 在 FloTHERM GUI 中录制宏（Tools → Macro → Record）
    2. 执行 Reinitialize → Solve → Stop Recording
    3. 使用本脚本整合 ECXML/Pack + 宏进行批量自动化
"""

import os
import sys
import subprocess
import argparse
import tempfile
import shutil
from pathlib import Path
from datetime import datetime
import xml.etree.ElementTree as ET


class FloScriptRunner:
    """FloSCRIPT 运行器"""

    def __init__(self, flotherm_path: str = None):
        self.flotherm_path = flotherm_path or self._auto_detect()

    def _auto_detect(self) -> str:
        """自动检测 FloTHERM 路径"""
        if sys.platform == 'win32':
            paths = [
                r"C:\Program Files\Siemens\SimcenterFlotherm\2020.2\bin\flotherm.exe",
                r"C:\Program Files\Siemens\SimcenterFlotherm\2410\bin\flotherm.exe",
                r"C:\Program Files\Mentor Graphics\FloTHERM\v2020.2\flosuite\bin\flotherm.exe",
            ]
        else:
            paths = [
                "/opt/Siemens/SimcenterFlotherm/2020.2/bin/flotherm",
            ]

        for path in paths:
            if os.path.exists(path):
                print(f"[INFO] 检测到 FloTHERM: {path}")
                return path

        return "flotherm"

    def _get_file_type(self, file_path: str) -> str:
        """识别文件类型"""
        ext = Path(file_path).suffix.lower()
        type_map = {
            '.pack': 'pack',
            '.ecxml': 'ecxml',
            '.pdml': 'pdml',
            '.prj': 'prj',
        }
        return type_map.get(ext, 'unknown')

    def create_floscript(self, model_file: str, macro_file: str,
                         output_file: str, result_pack: str = None) -> str:
        """
        创建完整的 FloSCRIPT XML

        Args:
            model_file: 模型文件路径 (.pack, .prj, .ecxml)
            macro_file: 录制的宏文件路径 (.xml)
            output_file: 输出的 FloSCRIPT 文件路径
            result_pack: 结果保存路径（可选）

        Returns:
            生成的 FloSCRIPT 文件路径
        """
        # 解析录制的宏
        macro_commands = self._extract_macro_commands(macro_file)

        # 创建完整的 FloSCRIPT
        floscript = ET.Element("FloSCRIPT")
        floscript.set("version", "1.0")

        file_type = self._get_file_type(model_file)

        # 1. 加载模型（根据文件类型使用不同命令）
        if file_type == 'ecxml':
            # ECXML 需要先导入
            import_cmd = ET.SubElement(floscript, "Command")
            import_cmd.set("name", "Import")
            import_cmd.set("type", "ECXML")
            import_cmd.set("file", os.path.abspath(model_file))
        else:
            # Pack/Prj/PDML 直接加载
            load_cmd = ET.SubElement(floscript, "Command")
            load_cmd.set("name", "Load")
            load_cmd.set("file", os.path.abspath(model_file))

        # 2. 插入录制的宏操作
        for cmd in macro_commands:
            floscript.append(cmd)

        # 3. 保存结果（如果宏中没有 Save 命令）
        if not self._has_save_command(macro_commands):
            save_cmd = ET.SubElement(floscript, "Command")
            save_cmd.set("name", "Save")
            if result_pack:
                save_cmd.set("file", os.path.abspath(result_pack))
            else:
                # 默认保存到模型同目录，添加 _solved 后缀
                model_path = Path(model_file)
                default_result = model_path.parent / f"{model_path.stem}_solved.pack"
                save_cmd.set("file", str(default_result))

        # 格式化并保存
        self._indent(floscript)
        tree = ET.ElementTree(floscript)
        tree.write(output_file, encoding='utf-8', xml_declaration=True)

        return output_file

    def _extract_macro_commands(self, macro_file: str) -> list:
        """从录制的宏中提取命令"""
        try:
            tree = ET.parse(macro_file)
            root = tree.getroot()

            commands = []
            # 查找所有 Command 元素
            for elem in root.iter():
                if self._strip_ns(elem.tag) == 'Command':
                    # 复制元素
                    new_cmd = ET.Element(elem.tag, elem.attrib)
                    commands.append(new_cmd)
                elif self._strip_ns(elem.tag) in ['Reinitialize', 'Solve', 'Initialize']:
                    # 单独的命令元素
                    new_cmd = ET.Element("Command")
                    new_cmd.set("name", self._strip_ns(elem.tag))
                    new_cmd.attrib.update(elem.attrib)
                    commands.append(new_cmd)

            print(f"[INFO] 从宏中提取了 {len(commands)} 个命令")
            return commands

        except Exception as e:
            print(f"[WARN] 解析宏文件失败: {e}")
            print("[INFO] 将使用默认命令序列")
            # 返回默认命令
            default_cmds = []
            for cmd_name in ['Reinitialize', 'Solve']:
                cmd = ET.Element('Command')
                cmd.set('name', cmd_name)
                default_cmds.append(cmd)
            return default_cmds

    def _has_save_command(self, commands: list) -> bool:
        """检查命令列表中是否有 Save 命令"""
        for cmd in commands:
            if cmd.get('name', '').lower() == 'save':
                return True
        return False

    def _strip_ns(self, tag: str) -> str:
        """去除命名空间"""
        if '}' in tag:
            return tag.split('}')[1]
        return tag

    def _indent(self, elem, level=0):
        """添加缩进"""
        indent = "\n" + "  " * level
        if len(elem):
            if not elem.text or not elem.text.strip():
                elem.text = indent + "  "
            if not elem.tail or not elem.tail.strip():
                elem.tail = indent
            for child in elem:
                self._indent(child, level + 1)
            if not child.tail or not child.tail.strip():
                child.tail = indent
        else:
            if level and (not elem.tail or not elem.tail.strip()):
                elem.tail = indent

    def run(self, model_file: str, macro_file: str, output_dir: str,
            modify_power: dict = None, timeout: int = 7200) -> dict:
        """
        执行完整流程

        Args:
            model_file: 模型文件 (.pack, .prj, .ecxml)
            macro_file: 宏文件
            output_dir: 输出目录
            modify_power: 要修改的功耗 {组件名: 功耗值}
            timeout: 超时时间

        Returns:
            执行结果
        """
        start_time = datetime.now()
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        file_type = self._get_file_type(model_file)

        results = {
            "model": str(model_file),
            "model_type": file_type,
            "macro": str(macro_file),
            "output_dir": str(output_dir),
            "start_time": start_time.isoformat(),
            "success": False,
        }

        # 如果需要修改功耗
        actual_model = model_file
        if modify_power:
            print(f"[INFO] 修改功耗: {modify_power}")

            if file_type == 'ecxml':
                # ECXML 文件直接修改
                modified_model = output_dir / "modified_model.ecxml"
                actual_model = self._modify_ecxml_power(model_file, modified_model, modify_power)
            elif file_type == 'pack':
                # Pack 文件需要解压修改
                modified_model = output_dir / "modified_model.pack"
                actual_model = self._modify_pack_power(model_file, modified_model, modify_power)
            else:
                print(f"[WARN] 不支持修改 {file_type} 格式的功耗")
                actual_model = model_file

            if actual_model:
                print(f"[INFO] 已创建修改后的模型: {actual_model}")
            else:
                print("[WARN] 修改功耗失败，使用原始模型")
                actual_model = model_file

        # 生成 FloSCRIPT
        floscript_file = output_dir / "solver_script.xml"
        result_pack = output_dir / "result.pack"

        self.create_floscript(
            model_file=actual_model,
            macro_file=macro_file,
            output_file=str(floscript_file),
            result_pack=str(result_pack)
        )
        print(f"[INFO] 已生成 FloSCRIPT: {floscript_file}")

        # 显示 FloSCRIPT 内容
        print("\n[FloSCRIPT 内容]:")
        print("-" * 50)
        with open(floscript_file, 'r', encoding='utf-8') as f:
            print(f.read())
        print("-" * 50)

        # 执行 FloTHERM
        log_file = output_dir / "simulation.log"

        cmd = [self.flotherm_path, "-b", "-f", str(floscript_file)]

        print(f"\n[INFO] 执行命令:")
        print(f"       {' '.join(cmd)}")
        print()

        try:
            # Windows 上隐藏窗口
            startupinfo = None
            creationflags = 0
            if sys.platform == 'win32':
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                startupinfo.wShowWindow = subprocess.SW_HIDE
                creationflags = subprocess.CREATE_NO_WINDOW

            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                cwd=str(output_dir),
                startupinfo=startupinfo,
                creationflags=creationflags
            )

            # 实时输出
            print("-" * 50)
            print("  实时日志")
            print("-" * 50)

            with open(log_file, 'w', encoding='utf-8') as log_f:
                while True:
                    line = process.stdout.readline()
                    if not line and process.poll() is not None:
                        break
                    if line:
                        line = line.rstrip()
                        print(f"  {line}")
                        log_f.write(line + '\n')
                        log_f.flush()

            return_code = process.poll()
            print("-" * 50)
            print(f"\n[INFO] 进程返回码: {return_code}")

            results["return_code"] = return_code
            results["success"] = (return_code == 0)

        except FileNotFoundError as e:
            print(f"\n[ERROR] 找不到 FloTHERM: {self.flotherm_path}")
            results["error"] = str(e)

        except subprocess.TimeoutExpired:
            print(f"\n[ERROR] 求解超时 ({timeout} 秒)")
            results["error"] = "超时"

        except Exception as e:
            print(f"\n[ERROR] 运行错误: {e}")
            results["error"] = str(e)

        # 统计输出
        print(f"\n[INFO] 输出目录内容:")
        output_files = []
        for f in output_dir.iterdir():
            if f.is_file():
                size = f.stat().st_size
                print(f"       {f.name} ({self._format_size(size)})")
                output_files.append(str(f))

        results["output_files"] = output_files
        results["end_time"] = datetime.now().isoformat()

        return results

    def _modify_ecxml_power(self, ecxml_file: str, output_file: str,
                            power_map: dict) -> str:
        """修改 ECXML 文件中的功耗"""
        try:
            tree = ET.parse(ecxml_file)
            root = tree.getroot()

            modified = False
            for elem in root.iter():
                # 查找组件名称
                name = elem.get('Name', elem.get('name', ''))

                for comp_name, power in power_map.items():
                    if name == comp_name or comp_name.lower() in name.lower():
                        # 查找功耗字段
                        for child in elem.iter():
                            tag = self._strip_ns(child.tag).lower()
                            if 'power' in tag or 'heat' in tag:
                                if child.text and child.text.strip():
                                    child.text = str(power)
                                    modified = True
                                    print(f"       {name}: {power}W")

            if modified:
                tree.write(output_file, encoding='utf-8', xml_declaration=True)
                return output_file
            else:
                print(f"[WARN] 未找到要修改的组件")
                return None

        except Exception as e:
            print(f"[ERROR] 修改 ECXML 失败: {e}")
            return None

    def _modify_pack_power(self, pack_file: str, output_file: str,
                           power_map: dict) -> str:
        """修改 pack 文件中的功耗"""
        try:
            # 使用 pack_editor.py 的逻辑
            import zipfile

            with tempfile.TemporaryDirectory() as temp_dir:
                # 解压
                with zipfile.ZipFile(pack_file, 'r') as zf:
                    zf.extractall(temp_dir)

                # 修改 XML 文件
                modified = False
                for root, dirs, files in os.walk(temp_dir):
                    for f in files:
                        if f.endswith(('.xml', '.pdml')):
                            xml_path = os.path.join(root, f)
                            if self._modify_xml_power(xml_path, power_map):
                                modified = True
                                print(f"       修改了: {f}")

                if not modified:
                    return None

                # 重新打包
                with zipfile.ZipFile(output_file, 'w', zipfile.ZIP_DEFLATED) as zf:
                    for root, dirs, files in os.walk(temp_dir):
                        for f in files:
                            file_path = os.path.join(root, f)
                            arc_name = os.path.relpath(file_path, temp_dir)
                            zf.write(file_path, arc_name)

                return output_file

        except Exception as e:
            print(f"[ERROR] 修改 pack 失败: {e}")
            return None

    def _modify_xml_power(self, xml_path: str, power_map: dict) -> bool:
        """修改 XML 文件中的功耗"""
        try:
            tree = ET.parse(xml_path)
            root = tree.getroot()

            modified = False
            for elem in root.iter():
                name = elem.get('name', elem.get('Name', ''))
                for comp_name, power in power_map.items():
                    if name == comp_name or comp_name.lower() in name.lower():
                        for child in elem:
                            tag = self._strip_ns(child.tag).lower()
                            if 'power' in tag or 'heat' in tag:
                                child.text = str(power)
                                modified = True
                                print(f"       {name}: {power}W")

            if modified:
                tree.write(xml_path, encoding='utf-8', xml_declaration=True)

            return modified

        except Exception as e:
            return False

    def _format_size(self, size: int) -> str:
        """格式化文件大小"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} TB"


def main():
    parser = argparse.ArgumentParser(
        description='FloSCRIPT 运行器 - 整合模型和宏的完整流程',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
示例:
  # 基本用法
  python floscript_runner.py model.pack recorded_macro.xml -o ./results

  # 修改功耗后运行
  python floscript_runner.py model.pack macro.xml -o ./results --power U1_CPU 15.0

  # 批量运行多个功耗点
  python floscript_runner.py model.pack macro.xml -o ./results --power-range U1_CPU 5 10 15 20 25
        '''
    )

    parser.add_argument('model', help='模型文件 (.pack, .prj, .ecxml)')
    parser.add_argument('macro', help='录制的宏文件 (.xml)')
    parser.add_argument('-o', '--output', required=True, help='输出目录')
    parser.add_argument('--flotherm', help='FloTHERM 可执行文件路径')
    parser.add_argument('--power', nargs=2, metavar=('NAME', 'POWER'),
                       action='append', default=[],
                       help='修改功耗 (可多次使用)')
    parser.add_argument('--power-range', nargs='+',
                       metavar=('NAME', 'P1', 'P2', ...),
                       help='批量运行多个功耗点')
    parser.add_argument('--timeout', type=int, default=7200, help='超时时间（秒）')

    args = parser.parse_args()

    runner = FloScriptRunner(flotherm_path=args.flotherm)

    # 处理功耗修改
    power_map = {}
    if args.power:
        for name, power in args.power:
            power_map[name] = float(power)

    # 批量运行
    if args.power_range:
        comp_name = args.power_range[0]
        powers = [float(p) for p in args.power_range[1:]]

        print(f"\n[INFO] 批量运行: {comp_name} 功耗点 {powers}")
        print("=" * 60)

        all_results = []
        for power in powers:
            print(f"\n{'='*60}")
            print(f"  运行: {comp_name} = {power}W")
            print("=" * 60)

            sub_dir = Path(args.output) / f"power_{power}W"
            result = runner.run(
                model_file=args.model,
                macro_file=args.macro,
                output_dir=str(sub_dir),
                modify_power={comp_name: power},
                timeout=args.timeout
            )
            result['power'] = power
            all_results.append(result)

        # 汇总结果
        print("\n" + "=" * 60)
        print("  汇总结果")
        print("=" * 60)
        for r in all_results:
            status = "✓" if r.get('success') else "✗"
            print(f"  {status} {r.get('power')}W: {r.get('output_dir')}")

    else:
        # 单次运行
        runner.run(
            model_file=args.model,
            macro_file=args.macro,
            output_dir=args.output,
            modify_power=power_map if power_map else None,
            timeout=args.timeout
        )


if __name__ == '__main__':
    main()
