#!/usr/bin/env python3
"""
FloTHERM 批量 Pack 文件求解器

解决多个 Pack 文件自动化求解的问题：

方法 1: 动态生成 FloSCRIPT XML（推荐）
    - 录制一个不包含打开文件操作的宏
    - 用 Python 脚本为每个 Pack 文件生成 FloSCRIPT XML
    - 批量执行生成的 FloSCRIPT

方法 2: 使用项目文件
    - 先将 Pack 文件导入并保存为 .prj 项目
    - 使用 -batch 参数批量执行

使用方法:
    # 批量处理多个 Pack 文件
    python batch_pack_solver.py pack1.pack pack2.pack pack3.pack -o ./results

    # 使用通配符
    python batch_pack_solver.py *.pack -o ./results

    # 并行执行（Windows）
    python batch_pack_solver.py *.pack -o ./results --parallel 4

工作原理:
    1. 读取录制好的宏模板（或使用内置模板）
    2. 为每个 Pack 文件生成一个 FloSCRIPT XML
    3. 执行: flotherm -b -f generated_script.xml
"""

import os
import sys
import subprocess
import argparse
import glob
from pathlib import Path
from datetime import datetime
import xml.etree.ElementTree as ET


class BatchPackSolver:
    """批量 Pack 文件求解器"""

    # 内置的 FloSCRIPT 模板
    FLOSCRIPT_TEMPLATE = '''<?xml version="1.0" encoding="UTF-8"?>
<FloSCRIPT version="1.0">
    <!-- FloTHERM 自动化脚本 - 由 Python 生成 -->
    <Command name="Open" file="{pack_file}"/>
    <Command name="Reinitialize"/>
    <Command name="Solve"/>
    <Command name="Save" file="{output_file}"/>
</FloSCRIPT>
'''

    def __init__(self, flotherm_path: str = None, macro_template: str = None):
        self.flotherm_path = flotherm_path or self._auto_detect_flotherm()
        self.macro_template = macro_template
        self.platform = sys.platform

    def _auto_detect_flotherm(self) -> str:
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

    def _load_macro_template(self, template_file: str = None) -> str:
        """加载宏模板"""
        if template_file and os.path.exists(template_file):
            with open(template_file, 'r', encoding='utf-8') as f:
                return f.read()

        # 使用内置模板
        return self.FLOSCRIPT_TEMPLATE

    def generate_floscript(self, pack_file: str, output_file: str,
                          template: str = None) -> str:
        """
        为单个 Pack 文件生成 FloSCRIPT XML

        Args:
            pack_file: Pack 文件路径
            output_file: 输出文件路径（求解后保存）
            template: FloSCRIPT 模板（可选）

        Returns:
            生成的 FloSCRIPT 文件路径
        """
        template = template or self._load_macro_template(self.macro_template)

        # 替换占位符
        abs_pack_path = os.path.abspath(pack_file).replace('\\', '/')
        abs_output_path = os.path.abspath(output_file).replace('\\', '/')

        script_content = template.format(
            pack_file=abs_pack_path,
            output_file=abs_output_path
        )

        # 生成输出文件名
        pack_name = Path(pack_file).stem
        script_file = Path(output_file).parent / f"floscript_{pack_name}.xml"

        with open(script_file, 'w', encoding='utf-8') as f:
            f.write(script_content)

        return str(script_file)

    def solve_single(self, pack_file: str, output_dir: str,
                     timeout: int = 7200) -> dict:
        """
        求解单个 Pack 文件

        Args:
            pack_file: Pack 文件路径
            output_dir: 输出目录
            timeout: 超时时间
        """
        start_time = datetime.now()
        pack_name = Path(pack_file).stem
        output_subdir = Path(output_dir) / pack_name
        output_subdir.mkdir(parents=True, exist_ok=True)

        results = {
            "pack_file": str(pack_file),
            "output_dir": str(output_subdir),
            "start_time": start_time.isoformat(),
            "success": False,
        }

        print(f"\n{'='*60}")
        print(f"  处理: {pack_name}")
        print(f"{'='*60}")

        # 生成输出文件路径
        output_pack = output_subdir / f"{pack_name}_solved.pack"

        # 生成 FloSCRIPT
        script_file = self.generate_floscript(pack_file, str(output_pack))
        print(f"[INFO] 生成 FloSCRIPT: {script_file}")

        # 执行求解
        log_file = output_subdir / "simulation.log"
        cmd = [self.flotherm_path, "-b", "-f", script_file]

        print(f"[INFO] 执行: {' '.join(cmd)}")

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
                cwd=str(output_subdir),
                startupinfo=startupinfo,
                creationflags=creationflags
            )

            # 实时输出
            print("-" * 40)
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
            print("-" * 40)
            print(f"[INFO] 返回码: {return_code}")

            results["return_code"] = return_code
            results["success"] = (return_code == 0)

            if results["success"] and output_pack.exists():
                print(f"[SUCCESS] 求解完成: {output_pack}")
            else:
                print(f"[FAILED] 求解失败")

        except FileNotFoundError:
            print(f"[ERROR] 找不到 FloTHERM: {self.flotherm_path}")
            results["error"] = "FloTHERM not found"

        except subprocess.TimeoutExpired:
            print(f"[ERROR] 超时 ({timeout}秒)")
            results["error"] = "Timeout"

        except Exception as e:
            print(f"[ERROR] {e}")
            results["error"] = str(e)

        results["end_time"] = datetime.now().isoformat()
        return results

    def solve_batch(self, pack_files: list, output_dir: str,
                    parallel: int = 1, timeout: int = 7200) -> list:
        """
        批量求解多个 Pack 文件

        Args:
            pack_files: Pack 文件列表
            output_dir: 输出目录
            parallel: 并行数（Windows 上支持）
            timeout: 超时时间
        """
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        print(f"\n{'='*60}")
        print(f"  FloTHERM 批量求解器")
        print(f"{'='*60}")
        print(f"  文件数量: {len(pack_files)}")
        print(f"  输出目录: {output_dir}")
        print(f"  并行数: {parallel}")
        print(f"{'='*60}")

        all_results = []

        if parallel > 1 and self.platform == 'win32':
            # Windows 并行执行
            all_results = self._solve_parallel_windows(
                pack_files, output_dir, parallel, timeout
            )
        else:
            # 顺序执行
            for i, pack_file in enumerate(pack_files, 1):
                print(f"\n[{i}/{len(pack_files)}] 处理: {Path(pack_file).name}")
                result = self.solve_single(pack_file, str(output_dir), timeout)
                all_results.append(result)

        # 汇总结果
        self._print_summary(all_results)

        # 保存结果报告
        self._save_report(all_results, output_dir)

        return all_results

    def _solve_parallel_windows(self, pack_files: list, output_dir: Path,
                                parallel: int, timeout: int) -> list:
        """Windows 并行执行"""
        import threading
        import queue

        results_queue = queue.Queue()
        active_processes = []

        def worker(pack_file):
            result = self.solve_single(pack_file, str(output_dir), timeout)
            results_queue.put(result)

        for i, pack_file in enumerate(pack_files):
            # 等待有空闲槽位
            while len(active_processes) >= parallel:
                active_processes = [p for p in active_processes if p.is_alive()]
                import time
                time.sleep(1)

            # 启动新线程
            t = threading.Thread(target=worker, args=(pack_file,))
            t.start()
            active_processes.append(t)

        # 等待所有线程完成
        for t in active_processes:
            t.join()

        # 收集结果
        results = []
        while not results_queue.empty():
            results.append(results_queue.get())

        return results

    def _print_summary(self, results: list):
        """打印汇总"""
        print(f"\n{'='*60}")
        print(f"  汇总结果")
        print(f"{'='*60}")

        success_count = 0
        for r in results:
            status = "✓" if r.get('success') else "✗"
            pack_name = Path(r.get('pack_file', '')).name
            print(f"  {status} {pack_name}")
            if r.get('success'):
                success_count += 1

        print(f"\n  成功: {success_count}/{len(results)}")

    def _save_report(self, results: list, output_dir: Path):
        """保存结果报告"""
        report_file = output_dir / "batch_report.txt"
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write("FloTHERM 批量求解报告\n")
            f.write(f"生成时间: {datetime.now().isoformat()}\n")
            f.write("=" * 60 + "\n\n")

            for r in results:
                status = "SUCCESS" if r.get('success') else "FAILED"
                f.write(f"文件: {r.get('pack_file')}\n")
                f.write(f"状态: {status}\n")
                f.write(f"输出: {r.get('output_dir')}\n")
                if r.get('error'):
                    f.write(f"错误: {r.get('error')}\n")
                f.write("-" * 40 + "\n")

        print(f"\n[INFO] 报告已保存: {report_file}")


def main():
    parser = argparse.ArgumentParser(
        description='FloTHERM 批量 Pack 文件求解器',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
示例:
  # 批量处理多个 Pack 文件
  python batch_pack_solver.py pack1.pack pack2.pack pack3.pack -o ./results

  # 使用通配符
  python batch_pack_solver.py *.pack -o ./results

  # 使用自定义宏模板
  python batch_pack_solver.py *.pack -o ./results --template my_macro.xml

  # 并行执行（Windows）
  python batch_pack_solver.py *.pack -o ./results --parallel 4

工作原理:
  1. 为每个 Pack 文件生成一个 FloSCRIPT XML
  2. FloSCRIPT 包含: 打开文件 → 求解 → 保存结果
  3. 执行: flotherm -b -f generated_script.xml

自定义宏模板:
  你可以录制一个宏作为模板，模板中需要包含以下占位符:
  - {pack_file}: 输入 Pack 文件路径
  - {output_file}: 输出文件路径

  示例模板:
  <?xml version="1.0" encoding="UTF-8"?>
  <FloSCRIPT version="1.0">
      <Command name="Open" file="{pack_file}"/>
      <Command name="Reinitialize"/>
      <Command name="Solve"/>
      <Command name="Save" file="{output_file}"/>
  </FloSCRIPT>
        '''
    )

    parser.add_argument('pack_files', nargs='+', help='Pack 文件路径（支持通配符）')
    parser.add_argument('-o', '--output', required=True, help='输出目录')
    parser.add_argument('--flotherm', help='FloTHERM 可执行文件路径')
    parser.add_argument('--template', help='FloSCRIPT 宏模板文件')
    parser.add_argument('--parallel', type=int, default=1,
                       help='并行数（仅 Windows）')
    parser.add_argument('--timeout', type=int, default=7200,
                       help='单个任务超时时间（秒）')

    args = parser.parse_args()

    # 处理通配符
    pack_files = []
    for pattern in args.pack_files:
        if '*' in pattern or '?' in pattern:
            pack_files.extend(glob.glob(pattern))
        else:
            pack_files.append(pattern)

    # 过滤存在的文件
    pack_files = [f for f in pack_files if os.path.exists(f)]

    if not pack_files:
        print("[ERROR] 没有找到 Pack 文件")
        sys.exit(1)

    print(f"[INFO] 找到 {len(pack_files)} 个 Pack 文件")

    # 创建求解器并执行
    solver = BatchPackSolver(
        flotherm_path=args.flotherm,
        macro_template=args.template
    )

    solver.solve_batch(
        pack_files=pack_files,
        output_dir=args.output,
        parallel=args.parallel,
        timeout=args.timeout
    )


if __name__ == '__main__':
    main()
