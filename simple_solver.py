#!/usr/bin/env python3
"""
FloTHERM 求解脚本
支持多种输入格式和求解模式

重要说明：
FloSCRIPT XML 和 FloXML 是两种完全不同的格式！
- FloSCRIPT XML: 用于自动化脚本，通过 flotherm -b -f script.xml 执行
- FloXML: 用于导入模型，格式完全不同

使用方法:
    # 方法1: 使用已有的 FloSCRIPT XML 文件（推荐）
    python simple_solver.py script.xml -o ./results --mode floscript

    # 方法2: 批处理模式（使用 .pack 或 .prj 文件）
    python simple_solver.py model.pack -o ./results

    # 方法3: 使用宏录制
    # 1. 在 FloTHERM GUI 中打开模型
    # 2. 使用 Macro -> Record 录制操作
    # 3. 保存录制的 .xml 文件
    # 4. 使用 flotherm -b -f recorded.xml 执行

官方示例位置（FloTHERM 2020.2）:
    C:\\Program Files\\Siemens\\SimcenterFlotherm\\2020.2\\examples\\FloSCRIPT\\
    C:\\Program Files\\Siemens\\SimcenterFlotherm\\2020.2\\docs\\Schema-Documentation\\FloSCRIPT\\
"""

import os
import sys
import subprocess
import argparse
import time
import zipfile
import tempfile
import shutil
import xml.etree.ElementTree as ET
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict


class SimpleFloTHERMSolver:
    """FloTHERM 求解器"""

    def __init__(self, flotherm_path: str = None):
        self.flotherm_path = flotherm_path or self._auto_detect()

    def _auto_detect(self) -> str:
        """自动检测 FloTHERM 路径"""
        if sys.platform == 'win32':
            paths = [
                r"C:\Program Files\Siemens\SimcenterFlotherm\2020.2\bin\flotherm.exe",
                r"C:\Program Files\Siemens\SimcenterFlotherm\2410\bin\flotherm.exe",
                r"C:\Program Files\Mentor Graphics\FloTHERM\v2020.2\flosuite\bin\flotherm.exe",
                r"C:\Program Files (x86)\Mentor Graphics\FloTHERM\v2020.2\flosuite\bin\flotherm.exe",
            ]
        else:
            paths = [
                "/opt/Siemens/SimcenterFlotherm/2020.2/bin/flotherm",
                "/opt/flotherm/v2020.2/bin/flotherm",
            ]

        for path in paths:
            if os.path.exists(path):
                print(f"[INFO] 检测到 FloTHERM: {path}")
                return path

        return "flotherm"

    def _get_file_type(self, input_file: str) -> str:
        """识别文件类型"""
        ext = Path(input_file).suffix.lower()
        type_map = {
            '.pack': 'pack',
            '.ecxml': 'ecxml',
            '.pdml': 'pdml',
            '.prj': 'prj',
            '.xml': 'xml',  # 可能是 FloSCRIPT
            '.floxml': 'floscript',
        }
        return type_map.get(ext, 'unknown')

    def _is_floscript(self, input_file: str) -> bool:
        """检查是否是 FloSCRIPT XML"""
        try:
            tree = ET.parse(input_file)
            root = tree.getroot()
            # FloSCRIPT 通常有这些根元素
            floscript_roots = ['FloSCRIPT', 'floscript', 'FloScript', 'Simulation']
            return any(root.tag.endswith(r) for r in floscript_roots)
        except:
            return False

    def solve(self, input_file: str, output_dir: str,
              mode: str = 'auto', timeout: int = 7200) -> dict:
        """
        执行求解

        Args:
            input_file: 输入文件
            output_dir: 输出目录
            mode: 求解模式
                - 'auto': 自动检测
                - 'floscript': FloSCRIPT 模式（无头）
                - 'batch': 批处理模式
            timeout: 超时时间（秒）
        """
        start_time = time.time()
        output_dir = Path(output_dir).resolve()
        output_dir.mkdir(parents=True, exist_ok=True)

        log_file = output_dir / "simulation.log"
        temp_dir = None
        actual_input = input_file
        floscript_file = None

        results = {
            "input": str(input_file),
            "output_dir": str(output_dir),
            "log_file": str(log_file),
            "start_time": datetime.now().isoformat(),
            "success": False,
            "mode": mode,
        }

        file_type = self._get_file_type(input_file)

        print("\n" + "=" * 60)
        print("  FloTHERM 求解器")
        print("=" * 60)
        print(f"  输入文件: {input_file}")
        print(f"  文件类型: {file_type.upper()}")
        print(f"  求解模式: {mode}")
        print(f"  输出目录: {output_dir}")
        print(f"  FloTHERM: {self.flotherm_path}")
        print("=" * 60 + "\n")

        if not os.path.exists(input_file):
            print(f"[ERROR] 输入文件不存在: {input_file}")
            results["error"] = "输入文件不存在"
            return results

        # 自动检测模式
        if mode == 'auto':
            if self._is_floscript(input_file):
                mode = 'floscript'
                print("[INFO] 检测到 FloSCRIPT 文件，使用无头模式")
            elif file_type in ['pack', 'prj']:
                mode = 'batch'
                print("[INFO] 使用批处理模式")
            elif file_type == 'ecxml':
                # ECXML 需要转换为 FloSCRIPT
                mode = 'floscript'
                print("[INFO] ECXML 文件，将生成 FloSCRIPT 进行无头求解")

        results["mode"] = mode

        # 处理 pack 文件
        if file_type == 'pack':
            print("[INFO] 解压 Pack 文件...")
            temp_dir = tempfile.mkdtemp(prefix="flotherm_")
            try:
                with zipfile.ZipFile(input_file, 'r') as zf:
                    zf.extractall(temp_dir)
                actual_input = self._find_project_file(temp_dir)
                if actual_input:
                    print(f"[INFO] 找到项目文件: {Path(actual_input).name}")
                else:
                    actual_input = temp_dir
            except Exception as e:
                print(f"[ERROR] 解压失败: {e}")
                results["error"] = str(e)
                return results

        # FloSCRIPT 模式：生成 FloSCRIPT XML
        if mode == 'floscript' and file_type == 'ecxml':
            floscript_file = output_dir / "solver_script.xml"
            self._create_floscript(actual_input, str(floscript_file), output_dir)
            actual_input = str(floscript_file)
            print(f"[INFO] 已生成 FloSCRIPT: {floscript_file.name}")

        # 构建命令
        cmd = self._build_command(actual_input, mode, log_file)

        print(f"[INFO] 执行命令:")
        print(f"       {' '.join(cmd)}")
        print()

        # 运行进程
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
            print("-" * 60)
            print("  实时日志")
            print("-" * 60)

            with open(log_file, 'w', encoding='utf-8') as log_f:
                line_count = 0
                while True:
                    line = process.stdout.readline()
                    if not line and process.poll() is not None:
                        break
                    if line:
                        line = line.rstrip()
                        print(f"  {line}")
                        log_f.write(line + '\n')
                        log_f.flush()
                        line_count += 1

            return_code = process.poll()
            print("-" * 60)
            print(f"\n[INFO] 进程返回码: {return_code}")
            print(f"[INFO] 日志行数: {line_count}")

            results["return_code"] = return_code
            results["success"] = (return_code == 0)

        except FileNotFoundError as e:
            print(f"\n[ERROR] 找不到 FloTHERM: {self.flotherm_path}")
            print("[INFO] 请使用 --flotherm 参数指定正确路径")
            results["error"] = str(e)

        except subprocess.TimeoutExpired:
            print(f"\n[ERROR] 求解超时 ({timeout} 秒)")
            results["error"] = "超时"

        except Exception as e:
            print(f"\n[ERROR] 运行错误: {e}")
            results["error"] = str(e)

        finally:
            if temp_dir and os.path.exists(temp_dir):
                shutil.rmtree(temp_dir, ignore_errors=True)

        # 统计输出
        print(f"\n[INFO] 输出目录内容:")
        output_files = []
        for f in output_dir.iterdir():
            if f.is_file():
                size = f.stat().st_size
                print(f"       {f.name} ({self._format_size(size)})")
                output_files.append(str(f))

        results["output_files"] = output_files
        results["elapsed_time"] = time.time() - start_time
        results["end_time"] = datetime.now().isoformat()

        print(f"\n[INFO] 总耗时: {results['elapsed_time']:.1f} 秒")

        return results

    def _build_command(self, input_file: str, mode: str, log_file: Path) -> List[str]:
        """构建 FloTHERM 命令"""

        if mode == 'floscript':
            # FloSCRIPT 模式（无头）
            # 使用 -b -f 参数执行 FloSCRIPT XML
            # 参考: flotherm -b -f script.xml
            return [
                self.flotherm_path,
                "-b",
                "-f",
                str(input_file)
            ]
        else:
            # 批处理模式
            # 注意：-nogui 参数可能不会完全禁用 GUI
            # 对于真正的无头模式，建议使用 FloSCRIPT
            return [
                self.flotherm_path,
                "-batch", str(input_file),
                "-nogui",
                "-solve",
                "-out", str(log_file)
            ]

    def _create_floscript(self, input_file: str, output_file: str, output_dir: Path):
        """
        创建 FloSCRIPT XML 文件

        警告: 自动生成的 FloSCRIPT XML 可能不被 FloTHERM 识别！
        FloSCRIPT 有严格的 Schema 定义，建议使用以下方法：

        方法1: 录制宏（推荐）
        1. 在 FloTHERM GUI 中打开你的模型
        2. 菜单 Tools -> Macro -> Record
        3. 执行你想要的操作（Reinitialize, Solve 等）
        4. 停止录制并保存 .xml 文件
        5. 使用 flotherm -b -f your_macro.xml 执行

        方法2: 参考官方示例
        位置: FloTHERM安装目录\\examples\\FloSCRIPT\\
        """

        print("[WARN] 自动生成 FloSCRIPT XML 可能不被识别！")
        print("[INFO] 建议使用 GUI 录制宏或参考官方示例")
        print()

        # 尝试创建简单的 FloSCRIPT（基于官方 Schema）
        # 注意：这是基于有限信息的尝试，可能需要调整
        floscript = ET.Element("FloSCRIPT")
        floscript.set("version", "1.0")

        # 添加注释
        comment = ET.Comment("""
            警告：此文件是自动生成的，可能不符合 FloTHERM Schema！
            如果执行失败，请使用以下方法：
            1. 在 FloTHERM GUI 中录制宏
            2. 参考官方示例目录中的 .xml 文件
            官方示例位置: FloTHERM安装目录\\examples\\FloSCRIPT\\
        """)
        floscript.append(comment)

        # 尝试基本的命令结构
        # 注意：实际结构需要参考官方 Schema 文档
        commands = ET.SubElement(floscript, "Commands")

        # Load 命令
        load_cmd = ET.SubElement(commands, "Command")
        load_cmd.set("name", "Load")
        load_cmd.set("file", os.path.abspath(input_file))

        # Reinitialize 命令
        reinit_cmd = ET.SubElement(commands, "Command")
        reinit_cmd.set("name", "Reinitialize")

        # Solve 命令
        solve_cmd = ET.SubElement(commands, "Command")
        solve_cmd.set("name", "Solve")

        # Save 命令
        save_cmd = ET.SubElement(commands, "Command")
        save_cmd.set("name", "Save")
        save_cmd.set("file", str(output_dir / "solved_project.pack"))

        # 格式化并保存
        self._indent(floscript)
        tree = ET.ElementTree(floscript)
        tree.write(output_file, encoding='utf-8', xml_declaration=True)

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

    def _find_project_file(self, directory: str) -> Optional[str]:
        """查找项目文件"""
        priority_files = ['project.prj', 'group.pdml', 'model.pdml']

        for pf in priority_files:
            for root, dirs, files in os.walk(directory):
                if pf in files:
                    return os.path.join(root, pf)

        for root, dirs, files in os.walk(directory):
            for f in files:
                if f.endswith(('.prj', '.pdml')):
                    return os.path.join(root, f)

        return None

    def _format_size(self, size: int) -> str:
        """格式化文件大小"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} TB"


def main():
    parser = argparse.ArgumentParser(
        description='FloTHERM 求解脚本 - 支持无头模式',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
求解模式:
  --mode floscript  FloSCRIPT 模式（无头，推荐）
  --mode batch      批处理模式
  --mode auto       自动检测（默认）

示例:
  # ECXML 文件（自动生成 FloSCRIPT，无头模式）
  python simple_solver.py model.ecxml -o ./results

  # 使用已有的 FloSCRIPT XML
  python simple_solver.py script.xml -o ./results --mode floscript

  # Pack 文件（批处理模式）
  python simple_solver.py model.pack -o ./results --mode batch
        '''
    )

    parser.add_argument('input', help='输入文件')
    parser.add_argument('-o', '--output', required=True, help='输出目录')
    parser.add_argument('--flotherm', help='FloTHERM 可执行文件路径')
    parser.add_argument('--mode', choices=['auto', 'floscript', 'batch'],
                       default='auto', help='求解模式（默认 auto）')
    parser.add_argument('--timeout', type=int, default=7200, help='超时时间（秒）')

    args = parser.parse_args()

    solver = SimpleFloTHERMSolver(flotherm_path=args.flotherm)
    results = solver.solve(
        input_file=args.input,
        output_dir=args.output,
        mode=args.mode,
        timeout=args.timeout
    )

    sys.exit(0 if results["success"] else 1)


if __name__ == '__main__':
    main()
