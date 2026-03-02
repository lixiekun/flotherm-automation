#!/usr/bin/env python3
"""
FloTHERM 自动化求解脚本
1. 加载 ECXML 文件
2. 执行 reinitialize 和 solve
3. 导出结果（文字和图表）
4. 实时打印运行日志

使用方法:
    python flotherm_solver.py input.ecxml --output ./results
"""

import os
import sys
import subprocess
import argparse
import shutil
import time
from pathlib import Path
from datetime import datetime
import xml.etree.ElementTree as ET


class FloTHERMSolver:
    """FloTHERM 自动化求解器"""

    # 默认 FloTHERM 安装路径（根据实际修改）
    DEFAULT_FLOTHERM_PATHS = {
        'windows': [
            r"C:\Program Files\Siemens\SimcenterFlotherm\2020.2\bin\flotherm.exe",
            r"C:\Program Files\Mentor Graphics\FloTHERM\v2020.2\flosuite\bin\flotherm.exe",
            r"C:\Program Files\FloTHERM\v2020.2\flosuite\bin\flotherm.exe",
        ],
        'linux': [
            "/opt/Siemens/SimcenterFlotherm/2020.2/bin/flotherm",
            "/opt/flotherm/v2020.2/bin/flotherm",
        ]
    }

    def __init__(self, flotherm_path: str = None):
        self.flotherm_path = flotherm_path or self._find_flotherm()
        self.log_callback = None

    def _find_flotherm(self) -> str:
        """自动查找 FloTHERM 安装路径"""
        platform = 'windows' if sys.platform == 'win32' else 'linux'
        paths = self.DEFAULT_FLOTHERM_PATHS.get(platform, [])

        for path in paths:
            if os.path.exists(path):
                return path

        # 如果找不到，返回默认值
        return paths[0] if paths else "flotherm"

    def _create_floscript(self, ecxml_path: str, output_dir: str,
                          export_images: bool = True) -> str:
        """
        创建 FloSCRIPT XML 文件

        FloSCRIPT 文件结构基于 FloTHERM 文档
        """
        output_dir = os.path.abspath(output_dir)
        os.makedirs(output_dir, exist_ok=True)

        # 构建 FloSCRIPT XML
        floscript = ET.Element("FloSCRIPT")
        floscript.set("version", "2.0")

        # 日志文件设置
        log_elem = ET.SubElement(floscript, "LogFile")
        log_elem.set("path", os.path.join(output_dir, "solver.log"))

        # 导入 ECXML 模型
        import_elem = ET.SubElement(floscript, "Import")
        import_elem.set("type", "ECXML")
        import_elem.set("path", os.path.abspath(ecxml_path))

        # 重新初始化
        reinit_elem = ET.SubElement(floscript, "Command")
        reinit_elem.set("name", "Reinitialize")

        # 求解
        solve_elem = ET.SubElement(floscript, "Command")
        solve_elem.set("name", "Solve")
        solve_elem.set("wait", "true")

        # 导出结果 - 温度数据
        export_temp = ET.SubElement(floscript, "Export")
        export_temp.set("type", "Temperature")
        export_temp.set("format", "CSV")
        export_temp.set("path", os.path.join(output_dir, "temperature_results.csv"))

        # 导出结果 - 速度数据
        export_vel = ET.SubElement(floscript, "Export")
        export_vel.set("type", "Velocity")
        export_vel.set("format", "CSV")
        export_vel.set("path", os.path.join(output_dir, "velocity_results.csv"))

        # 导出结果 - 汇总报告
        export_report = ET.SubElement(floscript, "Export")
        export_report.set("type", "SummaryReport")
        export_report.set("format", "TXT")
        export_report.set("path", os.path.join(output_dir, "summary_report.txt"))

        # 导出图表
        if export_images:
            # 温度云图
            export_temp_img = ET.SubElement(floscript, "Export")
            export_temp_img.set("type", "TemperaturePlot")
            export_temp_img.set("format", "PNG")
            export_temp_img.set("path", os.path.join(output_dir, "temperature_plot.png"))
            export_temp_img.set("view", "XY")

            # 3D 温度视图
            export_3d = ET.SubElement(floscript, "Export")
            export_3d.set("type", "TemperaturePlot3D")
            export_3d.set("format", "PNG")
            export_3d.set("path", os.path.join(output_dir, "temperature_3d.png"))

            # 速度矢量图
            export_vel_img = ET.SubElement(floscript, "Export")
            export_vel_img.set("type", "VelocityVectorPlot")
            export_vel_img.set("format", "PNG")
            export_vel_img.set("path", os.path.join(output_dir, "velocity_vectors.png"))

        # 保存项目
        save_elem = ET.SubElement(floscript, "SaveProject")
        save_elem.set("path", os.path.join(output_dir, "solved_project.pack"))

        # 格式化 XML
        self._indent(floscript)
        tree = ET.ElementTree(floscript)

        floscript_path = os.path.join(output_dir, "solver_script.xml")
        tree.write(floscript_path, encoding='utf-8', xml_declaration=True)

        return floscript_path

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

    def _create_batch_script(self, ecxml_path: str, output_dir: str,
                              floscript_path: str) -> str:
        """创建批处理脚本（备用方案）"""
        if sys.platform == 'win32':
            batch_path = os.path.join(output_dir, "run_simulation.bat")
            with open(batch_path, 'w') as f:
                f.write('@echo off\n')
                f.write(f'set FLOTHERM={self.flotherm_path}\n')
                f.write(f'echo Starting FloTHERM simulation...\n')
                f.write(f'echo Input: {ecxml_path}\n')
                f.write(f'echo Output: {output_dir}\n\n')

                # 方式1：使用批处理模式直接求解
                f.write(f'echo Running simulation...\n')
                f.write(f'"{self.flotherm_path}" -batch "{ecxml_path}" -nogui -solve -out "{output_dir}\\simulation.log"\n')

                f.write(f'\necho Simulation completed.\n')
                f.write(f'pause\n')
            return batch_path
        else:
            batch_path = os.path.join(output_dir, "run_simulation.sh")
            with open(batch_path, 'w') as f:
                f.write('#!/bin/bash\n\n')
                f.write(f'FLOTHERM="{self.flotherm_path}"\n')
                f.write(f'echo "Starting FloTHERM simulation..."\n')
                f.write(f'echo "Input: {ecxml_path}"\n')
                f.write(f'echo "Output: {output_dir}"\n\n')

                f.write(f'echo "Running simulation..."\n')
                f.write(f'$FLOTHERM -batch "{ecxml_path}" -nogui -solve > "{output_dir}/simulation.log" 2>&1\n')

                f.write(f'\necho "Simulation completed."\n')
            os.chmod(batch_path, 0o755)
            return batch_path

    def set_log_callback(self, callback):
        """设置日志回调函数"""
        self.log_callback = callback

    def _log(self, message: str, level: str = "INFO"):
        """打印日志"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_line = f"[{timestamp}] [{level}] {message}"
        print(log_line)
        if self.log_callback:
            self.log_callback(log_line)

    def solve(self, ecxml_path: str, output_dir: str,
              export_images: bool = True,
              timeout: int = 3600) -> dict:
        """
        执行求解

        Args:
            ecxml_path: ECXML 输入文件路径
            output_dir: 输出目录
            export_images: 是否导出图表
            timeout: 超时时间（秒）

        Returns:
            结果字典
        """
        start_time = time.time()
        output_dir = os.path.abspath(output_dir)
        os.makedirs(output_dir, exist_ok=True)

        results = {
            "input_file": ecxml_path,
            "output_dir": output_dir,
            "start_time": datetime.now().isoformat(),
            "success": False,
            "log_file": None,
            "output_files": [],
            "error": None
        }

        self._log(f"开始处理: {ecxml_path}")
        self._log(f"输出目录: {output_dir}")
        self._log(f"FloTHERM 路径: {self.flotherm_path}")

        # 检查输入文件
        if not os.path.exists(ecxml_path):
            results["error"] = f"输入文件不存在: {ecxml_path}"
            self._log(results["error"], "ERROR")
            return results

        # 创建 FloSCRIPT
        self._log("创建 FloSCRIPT...")
        floscript_path = self._create_floscript(ecxml_path, output_dir, export_images)
        self._log(f"FloSCRIPT 已创建: {floscript_path}")
        results["floscript_file"] = floscript_path

        # 创建批处理脚本（备用）
        batch_path = self._create_batch_script(ecxml_path, output_dir, floscript_path)
        self._log(f"批处理脚本已创建: {batch_path}")
        results["batch_file"] = batch_path

        # 运行 FloTHERM
        log_file = os.path.join(output_dir, "simulation.log")
        results["log_file"] = log_file

        self._log("启动 FloTHERM 求解...")
        self._log("-" * 50)

        try:
            # 构建命令
            cmd = [
                self.flotherm_path,
                "-batch", ecxml_path,
                "-nogui",
                "-solve",
                "-out", log_file
            ]

            self._log(f"命令: {' '.join(cmd)}")

            # 使用 Popen 实时读取输出
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding='utf-8',
                errors='replace',
                bufsize=1,
                cwd=output_dir
            )

            # 实时打印输出
            with open(log_file, 'w', encoding='utf-8') as log_f:
                try:
                    while True:
                        line = process.stdout.readline()
                        if not line and process.poll() is not None:
                            break
                        if line:
                            line = line.rstrip()
                            print(line)
                            log_f.write(line + '\n')
                            log_f.flush()
                except subprocess.TimeoutExpired:
                    process.kill()
                    results["error"] = f"求解超时 ({timeout}秒)"
                    self._log(results["error"], "ERROR")

            return_code = process.poll()
            results["return_code"] = return_code

            self._log("-" * 50)

            if return_code == 0:
                results["success"] = True
                self._log("求解完成!", "SUCCESS")
            else:
                results["error"] = f"FloTHERM 返回错误代码: {return_code}"
                self._log(results["error"], "ERROR")

        except FileNotFoundError:
            results["error"] = f"找不到 FloTHERM: {self.flotherm_path}"
            self._log(results["error"], "ERROR")
            self._log("请使用 --flotherm 参数指定 FloTHERM 安装路径", "INFO")

        except Exception as e:
            results["error"] = str(e)
            self._log(f"运行错误: {e}", "ERROR")

        # 检查输出文件
        self._log("检查输出文件...")
        for f in os.listdir(output_dir):
            file_path = os.path.join(output_dir, f)
            if os.path.isfile(file_path) and f not in ['solver_script.xml', 'run_simulation.bat', 'run_simulation.sh']:
                results["output_files"].append(file_path)
                self._log(f"  - {f}")

        # 统计
        elapsed = time.time() - start_time
        results["elapsed_time"] = elapsed
        results["end_time"] = datetime.now().isoformat()

        self._log(f"总耗时: {elapsed:.1f} 秒")

        # 保存结果摘要
        summary_path = os.path.join(output_dir, "run_summary.json")
        import json
        with open(summary_path, 'w', encoding='utf-8') as f:
            # 只保存可序列化的字段
            summary = {k: v for k, v in results.items() if not isinstance(v, (bytes, bytearray))}
            json.dump(summary, f, indent=2, ensure_ascii=False)
        self._log(f"运行摘要已保存: {summary_path}")

        return results


def main():
    parser = argparse.ArgumentParser(
        description='FloTHERM 自动化求解脚本',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
示例:
  # 基本用法
  python flotherm_solver.py model.ecxml --output ./results

  # 指定 FloTHERM 路径
  python flotherm_solver.py model.ecxml --output ./results --flotherm "C:\\Program Files\\FloTHERM\\v2020.2\\bin\\flotherm.exe"

  # 不导出图表
  python flotherm_solver.py model.ecxml --output ./results --no-images

  # 设置超时时间（秒）
  python flotherm_solver.py model.ecxml --output ./results --timeout 7200
        '''
    )

    parser.add_argument('input', help='输入 ECXML 文件路径')
    parser.add_argument('-o', '--output', required=True, help='输出目录')
    parser.add_argument('--flotherm', help='FloTHERM 安装路径（自动检测如果未指定）')
    parser.add_argument('--no-images', action='store_true', help='不导出图表文件')
    parser.add_argument('--timeout', type=int, default=3600, help='超时时间（秒），默认 3600')
    parser.add_argument('--dry-run', action='store_true', help='只生成脚本，不执行')

    args = parser.parse_args()

    # 创建求解器
    solver = FloTHERMSolver(flotherm_path=args.flotherm)

    print("\n" + "=" * 60)
    print("FloTHERM 自动化求解")
    print("=" * 60)
    print(f"输入文件: {args.input}")
    print(f"输出目录: {args.output}")
    print(f"FloTHERM: {solver.flotherm_path}")
    print(f"导出图表: {'否' if args.no_images else '是'}")
    print(f"超时时间: {args.timeout} 秒")
    print("=" * 60 + "\n")

    if args.dry_run:
        # 只生成脚本
        output_dir = os.path.abspath(args.output)
        os.makedirs(output_dir, exist_ok=True)

        floscript_path = solver._create_floscript(
            args.input, output_dir,
            export_images=not args.no_images
        )
        batch_path = solver._create_batch_script(
            args.input, output_dir, floscript_path
        )

        print(f"[DRY RUN] 已生成:")
        print(f"  - FloSCRIPT: {floscript_path}")
        print(f"  - 批处理脚本: {batch_path}")
        print(f"\n你可以手动运行批处理脚本，或去掉 --dry-run 参数直接执行。")
        return

    # 执行求解
    results = solver.solve(
        ecxml_path=args.input,
        output_dir=args.output,
        export_images=not args.no_images,
        timeout=args.timeout
    )

    print("\n" + "=" * 60)
    print("求解结果")
    print("=" * 60)
    print(f"状态: {'成功' if results['success'] else '失败'}")
    if results.get('error'):
        print(f"错误: {results['error']}")
    print(f"耗时: {results.get('elapsed_time', 0):.1f} 秒")
    print(f"输出文件数: {len(results.get('output_files', []))}")
    print("=" * 60)

    sys.exit(0 if results['success'] else 1)


if __name__ == '__main__':
    main()
