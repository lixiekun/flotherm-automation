#!/usr/bin/env python3
"""
FloTHERM 批处理求解器

基于官方文档和社区调研的正确自动化方法：

支持的执行方式：
1. 项目文件 (.prj) - 使用 -batch 参数
2. FloXML 文件 (.floxml) - 使用 -b 参数
3. FloSCRIPT 宏 (.xml) - 使用 -b -f 参数

使用方法:
    # 使用项目文件（推荐）
    python flotherm_batch_solver.py project.prj -o ./results

    # 使用 FloXML
    python flotherm_batch_solver.py model.floxml -o ./results

    # 使用 FloSCRIPT 宏
    python flotherm_batch_solver.py macro.xml --mode floscript -o ./results

    # 批量参数扫描
    python flotherm_batch_solver.py model.floxml -o ./results --power-range U1_CPU 5 10 15 20 25

参考文档：
    - FloTHERM 安装目录/examples/FloSCRIPT/Tutorial/
    - FloTHERM 安装目录/docs/Schema-Documentation/FloSCRIPT/
"""

import os
import sys
import subprocess
import argparse
import tempfile
import shutil
import zipfile
from pathlib import Path
from datetime import datetime
import xml.etree.ElementTree as ET


class FlothermBatchSolver:
    """FloTHERM 批处理求解器"""

    def __init__(self, flotherm_path: str = None):
        self.flotherm_path = flotherm_path or self._auto_detect_flotherm()
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

    def _get_file_type(self, file_path: str) -> str:
        """识别文件类型"""
        ext = Path(file_path).suffix.lower()
        type_map = {
            '.prj': 'project',      # 项目文件 - 使用 -batch
            '.floxml': 'floxml',    # FloXML - 使用 -b
            '.pack': 'pack',        # Pack 文件 - 需要导入
            '.pdml': 'pdml',        # PDML 文件 - 需要导入
            '.ecxml': 'ecxml',      # ECXML 文件 - 需要导入
            '.xml': 'floscript',    # 可能是 FloSCRIPT
        }
        return type_map.get(ext, 'unknown')

    def solve(self, input_file: str, output_dir: str,
              mode: str = 'auto', modify_power: dict = None,
              timeout: int = 7200) -> dict:
        """
        执行求解

        Args:
            input_file: 输入文件路径
            output_dir: 输出目录
            mode: 执行模式 (auto, project, floxml, floscript)
            modify_power: 要修改的功耗 {组件名: 功耗值}
            timeout: 超时时间
        """
        start_time = datetime.now()
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        results = {
            "input": str(input_file),
            "output_dir": str(output_dir),
            "start_time": start_time.isoformat(),
            "success": False,
        }

        # 自动检测文件类型
        file_type = self._get_file_type(input_file)
        print(f"\n{'='*60}")
        print(f"  FloTHERM 批处理求解器")
        print(f"{'='*60}")
        print(f"  输入文件: {input_file}")
        print(f"  文件类型: {file_type}")
        print(f"  输出目录: {output_dir}")
        print(f"  FloTHERM: {self.flotherm_path}")
        print(f"{'='*60}\n")

        # 根据文件类型选择执行方式
        if mode == 'auto':
            if file_type == 'project':
                mode = 'project'
            elif file_type == 'floxml':
                mode = 'floxml'
            elif file_type == 'floscript':
                mode = 'floscript'
            else:
                print(f"[ERROR] 不支持的文件类型: {file_type}")
                print("[INFO] 支持的格式: .prj, .floxml, .xml (FloSCRIPT)")
                results["error"] = f"不支持的文件类型: {file_type}"
                return results

        # 执行求解
        if mode == 'project':
            success = self._solve_project(input_file, output_dir, timeout)
        elif mode == 'floxml':
            success = self._solve_floxml(input_file, output_dir, modify_power, timeout)
        elif mode == 'floscript':
            success = self._solve_floscript(input_file, output_dir, timeout)
        else:
            print(f"[ERROR] 未知模式: {mode}")
            results["error"] = f"未知模式: {mode}"
            return results

        results["success"] = success
        results["end_time"] = datetime.now().isoformat()

        # 统计输出
        print(f"\n[INFO] 输出目录内容:")
        output_files = []
        for f in output_dir.iterdir():
            if f.is_file():
                size = f.stat().st_size
                print(f"       {f.name} ({self._format_size(size)})")
                output_files.append(str(f))

        results["output_files"] = output_files

        return results

    def _solve_project(self, project_file: str, output_dir: str, timeout: int) -> bool:
        """
        使用项目文件求解（推荐方式）

        命令: flotherm.exe -batch "project.prj" -nogui -solve -out "log.txt"
        """
        log_file = Path(output_dir) / "simulation.log"

        # 构建命令
        cmd = [
            self.flotherm_path,
            "-batch", str(project_file),
            "-nogui",
            "-solve",
            "-out", str(log_file)
        ]

        print(f"[INFO] 执行命令:")
        print(f"       {' '.join(cmd)}")
        print()

        return self._run_command(cmd, output_dir, log_file, timeout)

    def _solve_floxml(self, floxml_file: str, output_dir: str,
                      modify_power: dict, timeout: int) -> bool:
        """
        使用 FloXML 文件求解

        命令: flotherm -b model.floxml
        """
        actual_model = floxml_file

        # 如果需要修改功耗
        if modify_power:
            print(f"[INFO] 修改功耗: {modify_power}")
            modified_model = Path(output_dir) / "modified_model.floxml"
            actual_model = self._modify_floxml_power(floxml_file, modified_model, modify_power)

            if actual_model:
                print(f"[INFO] 已创建修改后的模型: {actual_model}")
            else:
                print("[WARN] 修改功耗失败，使用原始模型")
                actual_model = floxml_file

        log_file = Path(output_dir) / "simulation.log"

        # 构建命令: flotherm -b model.floxml
        cmd = [
            self.flotherm_path,
            "-b", str(actual_model)
        ]

        print(f"[INFO] 执行命令:")
        print(f"       {' '.join(cmd)}")
        print()

        return self._run_command(cmd, output_dir, log_file, timeout)

    def _solve_floscript(self, script_file: str, output_dir: str, timeout: int) -> bool:
        """
        使用 FloSCRIPT 宏求解

        命令: flotherm -b -f script.xml
        """
        log_file = Path(output_dir) / "simulation.log"

        # 构建命令: flotherm -b -f script.xml
        cmd = [
            self.flotherm_path,
            "-b",
            "-f", str(script_file)
        ]

        print(f"[INFO] 执行 FloSCRIPT 宏:")
        print(f"       {' '.join(cmd)}")
        print()

        return self._run_command(cmd, output_dir, log_file, timeout)

    def _run_command(self, cmd: list, output_dir: str, log_file: Path, timeout: int) -> bool:
        """执行命令并捕获输出"""
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
            print("-" * 60)
            print(f"\n[INFO] 进程返回码: {return_code}")

            return return_code == 0

        except FileNotFoundError as e:
            print(f"\n[ERROR] 找不到 FloTHERM: {self.flotherm_path}")
            return False

        except subprocess.TimeoutExpired:
            print(f"\n[ERROR] 求解超时 ({timeout} 秒)")
            return False

        except Exception as e:
            print(f"\n[ERROR] 运行错误: {e}")
            return False

    def _modify_floxml_power(self, floxml_file: str, output_file: str,
                             power_map: dict) -> str:
        """修改 FloXML 文件中的功耗"""
        try:
            tree = ET.parse(floxml_file)
            root = tree.getroot()

            modified = False
            for elem in root.iter():
                name = elem.get('Name', elem.get('name', ''))

                name_elem = elem.find('.//Name')
                if name_elem is not None and name_elem.text:
                    name = name_elem.text

                for comp_name, power in power_map.items():
                    if name == comp_name or comp_name.lower() in name.lower():
                        for child in elem.iter():
                            tag = self._strip_ns(child.tag).lower()
                            if 'power' in tag or 'heat' in tag:
                                if child.text and child.text.strip():
                                    old_power = child.text
                                    child.text = str(power)
                                    modified = True
                                    print(f"       {name}: {old_power}W -> {power}W")

            if modified:
                tree.write(output_file, encoding='utf-8', xml_declaration=True)
                return output_file
            else:
                print(f"[WARN] 未找到要修改的组件")
                return None

        except Exception as e:
            print(f"[ERROR] 修改 FloXML 失败: {e}")
            return None

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

    def batch_solve(self, input_file: str, component: str,
                    powers: list, output_dir: str, timeout: int = 7200):
        """批量参数扫描"""
        print(f"\n[INFO] 批量运行: {component} 功耗点 {powers}")
        print("=" * 60)

        all_results = []
        for power in powers:
            print(f"\n{'='*60}")
            print(f"  运行: {component} = {power}W")
            print("=" * 60)

            sub_dir = Path(output_dir) / f"power_{power}W"
            result = self.solve(
                input_file=input_file,
                output_dir=str(sub_dir),
                mode='auto',
                modify_power={component: power},
                timeout=timeout
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

        return all_results


def main():
    parser = argparse.ArgumentParser(
        description='FloTHERM 批处理求解器',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
示例:
  # 使用项目文件（推荐）
  python flotherm_batch_solver.py project.prj -o ./results

  # 使用 FloXML
  python flotherm_batch_solver.py model.floxml -o ./results

  # 使用 FloSCRIPT 宏
  python flotherm_batch_solver.py macro.xml --mode floscript -o ./results

  # 修改功耗后执行
  python flotherm_batch_solver.py model.floxml -o ./results --power U1_CPU 15.0

  # 批量参数扫描
  python flotherm_batch_solver.py model.floxml -o ./results --power-range U1_CPU 5 10 15 20 25

命令行参数参考:
  flotherm.exe -batch "project.prj" -nogui -solve -out "log.txt"
  flotherm -b model.floxml
  flotherm -b -f script.xml
        '''
    )

    parser.add_argument('input', help='输入文件 (.prj, .floxml, .xml)')
    parser.add_argument('-o', '--output', required=True, help='输出目录')
    parser.add_argument('--flotherm', help='FloTHERM 可执行文件路径')
    parser.add_argument('--mode', choices=['auto', 'project', 'floxml', 'floscript'],
                       default='auto', help='执行模式')
    parser.add_argument('--power', nargs=2, metavar=('NAME', 'POWER'),
                       action='append', default=[],
                       help='修改功耗 (可多次使用)')
    parser.add_argument('--power-range', nargs='+',
                       metavar=('NAME', 'P1', 'P2', ...),
                       help='批量运行多个功耗点')
    parser.add_argument('--timeout', type=int, default=7200, help='超时时间（秒）')

    args = parser.parse_args()

    solver = FlothermBatchSolver(flotherm_path=args.flotherm)

    # 处理功耗修改
    power_map = {}
    if args.power:
        for name, power in args.power:
            power_map[name] = float(power)

    # 批量运行
    if args.power_range:
        comp_name = args.power_range[0]
        powers = [float(p) for p in args.power_range[1:]]
        solver.batch_solve(
            input_file=args.input,
            component=comp_name,
            powers=powers,
            output_dir=args.output,
            timeout=args.timeout
        )
    else:
        # 单次运行
        solver.solve(
            input_file=args.input,
            output_dir=args.output,
            mode=args.mode,
            modify_power=power_map if power_map else None,
            timeout=args.timeout
        )


if __name__ == '__main__':
    main()
