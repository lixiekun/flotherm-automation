#!/usr/bin/env python3
"""
FloTHERM 简易求解脚本（直接使用命令行模式）
不依赖 FloSCRIPT XML 结构，直接使用 -batch -solve 参数

使用方法:
    python simple_solver.py input.ecxml -o ./results
"""

import os
import sys
import subprocess
import argparse
import time
import threading
from pathlib import Path
from datetime import datetime


class SimpleFloTHERMSolver:
    """简易 FloTHERM 求解器"""

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

        return "flotherm"  # 假设已在 PATH 中

    def solve(self, input_file: str, output_dir: str, timeout: int = 7200) -> dict:
        """
        执行求解

        Args:
            input_file: 输入文件（.ecxml 或 .pack）
            output_dir: 输出目录
            timeout: 超时时间（秒）

        Returns:
            结果字典
        """
        start_time = time.time()
        output_dir = Path(output_dir).resolve()
        output_dir.mkdir(parents=True, exist_ok=True)

        log_file = output_dir / "simulation.log"

        results = {
            "input": str(input_file),
            "output_dir": str(output_dir),
            "log_file": str(log_file),
            "start_time": datetime.now().isoformat(),
            "success": False,
        }

        print("\n" + "=" * 60)
        print("  FloTHERM 求解器")
        print("=" * 60)
        print(f"  输入文件: {input_file}")
        print(f"  输出目录: {output_dir}")
        print(f"  日志文件: {log_file}")
        print(f"  FloTHERM: {self.flotherm_path}")
        print("=" * 60 + "\n")

        # 检查输入文件
        if not os.path.exists(input_file):
            print(f"[ERROR] 输入文件不存在: {input_file}")
            results["error"] = "输入文件不存在"
            return results

        # 构建命令
        cmd = [
            self.flotherm_path,
            "-batch", str(input_file),
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
                        # 打印到控制台
                        print(f"  {line}")
                        # 写入日志文件
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

    def _format_size(self, size: int) -> str:
        """格式化文件大小"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} TB"


def main():
    parser = argparse.ArgumentParser(
        description='FloTHERM 简易求解脚本',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
示例:
  python simple_solver.py model.ecxml -o ./results
  python simple_solver.py model.pack -o ./results --flotherm "C:\\FloTHERM\\bin\\flotherm.exe"
        '''
    )

    parser.add_argument('input', help='输入文件 (.ecxml 或 .pack)')
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

    # 返回状态码
    sys.exit(0 if results["success"] else 1)


if __name__ == '__main__':
    main()
