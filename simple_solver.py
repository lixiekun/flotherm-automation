#!/usr/bin/env python3
"""
FloTHERM 简易求解脚本（直接使用命令行模式）
支持 ECXML、Pack、PDML 格式

使用方法:
    python simple_solver.py input.ecxml -o ./results
    python simple_solver.py input.pack -o ./results
"""

import os
import sys
import subprocess
import argparse
import time
import zipfile
import tempfile
import shutil
from pathlib import Path
from datetime import datetime
from typing import Optional


class SimpleFloTHERMSolver:
    """简易 FloTHERM 求解器 - 支持 ECXML、Pack、PDML 格式"""

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
        if ext == '.pack':
            return 'pack'
        elif ext == '.ecxml':
            return 'ecxml'
        elif ext == '.pdml':
            return 'pdml'
        elif ext == '.prj':
            return 'prj'
        else:
            return 'unknown'

    def solve(self, input_file: str, output_dir: str, timeout: int = 7200) -> dict:
        """
        执行求解 - 支持 ECXML、Pack、PDML 格式
        """
        start_time = time.time()
        output_dir = Path(output_dir).resolve()
        output_dir.mkdir(parents=True, exist_ok=True)

        log_file = output_dir / "simulation.log"
        temp_dir = None
        actual_input = input_file

        results = {
            "input": str(input_file),
            "output_dir": str(output_dir),
            "log_file": str(log_file),
            "start_time": datetime.now().isoformat(),
            "success": False,
        }

        # 识别文件类型
        file_type = self._get_file_type(input_file)
        print(f"[INFO] 文件类型: {file_type.upper()}")

        print("\n" + "=" * 60)
        print("  FloTHERM 求解器")
        print("=" * 60)
        print(f"  输入文件: {input_file}")
        print(f"  文件类型: {file_type.upper()}")
        print(f"  输出目录: {output_dir}")
        print(f"  日志文件: {log_file}")
        print(f"  FloTHERM: {self.flotherm_path}")
        print("=" * 60 + "\n")

        # 检查输入文件
        if not os.path.exists(input_file):
            print(f"[ERROR] 输入文件不存在: {input_file}")
            results["error"] = "输入文件不存在"
            return results

        # 如果是 pack 文件，解压后找到项目文件
        if file_type == 'pack':
            print("[INFO] 解压 Pack 文件...")
            temp_dir = tempfile.mkdtemp(prefix="flotherm_")
            try:
                with zipfile.ZipFile(input_file, 'r') as zf:
                    zf.extractall(temp_dir)
                print(f"[INFO] 已解压到临时目录")

                # 查找项目文件
                actual_input = self._find_project_file(temp_dir)
                if actual_input:
                    print(f"[INFO] 找到项目文件: {Path(actual_input).name}")
                else:
                    # 使用目录作为输入
                    actual_input = temp_dir
                    print(f"[INFO] 使用目录作为输入")
            except Exception as e:
                print(f"[ERROR] 解压失败: {e}")
                results["error"] = str(e)
                return results

        # 构建命令
        cmd = [
            self.flotherm_path,
            "-batch", str(actual_input),
            "-nogui",
            "-solve",
            "-out", str(log_file)
        ]

        print(f"[INFO] 执行命令:")
        print(f"       {' '.join(cmd)}")
        print()

        # 运行进程
        try:
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                cwd=str(output_dir)
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
            # 清理临时目录
            if temp_dir and os.path.exists(temp_dir):
                shutil.rmtree(temp_dir, ignore_errors=True)
                print("[INFO] 已清理临时目录")

        # 统计输出文件
        print(f"\n[INFO] 输出目录内容:")
        output_files = []
        for f in output_dir.iterdir():
            if f.is_file():
                size = f.stat().st_size
                size_str = self._format_size(size)
                print(f"       {f.name} ({size_str})")
                output_files.append(str(f))

        results["output_files"] = output_files
        results["elapsed_time"] = time.time() - start_time
        results["end_time"] = datetime.now().isoformat()

        print(f"\n[INFO] 总耗时: {results['elapsed_time']:.1f} 秒")

        return results

    def _find_project_file(self, directory: str) -> Optional[str]:
        """在解压目录中查找项目文件"""
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
        description='FloTHERM 简易求解脚本 - 支持 ECXML、Pack、PDML 格式',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
支持的格式:
  .ecxml  - ECXML 格式
  .pack   - Pack 格式 (自动解压)
  .pdml   - PDML 格式
  .prj    - 项目文件

示例:
  python simple_solver.py model.ecxml -o ./results
  python simple_solver.py model.pack -o ./results
  python simple_solver.py model.pack -o ./results --flotherm "C:\\FloTHERM\\bin\\flotherm.exe"
        '''
    )

    parser.add_argument('input', help='输入文件 (.ecxml, .pack, .pdml, .prj)')
    parser.add_argument('-o', '--output', required=True, help='输出目录')
    parser.add_argument('--flotherm', help='FloTHERM 可执行文件路径')
    parser.add_argument('--timeout', type=int, default=7200, help='超时时间（秒）')

    args = parser.parse_args()

    solver = SimpleFloTHERMSolver(flotherm_path=args.flotherm)
    results = solver.solve(
        input_file=args.input,
        output_dir=args.output,
        timeout=args.timeout
    )

    sys.exit(0 if results["success"] else 1)


if __name__ == '__main__':
    main()
