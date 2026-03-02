#!/usr/bin/env python3
"""
FloTHERM 自动求解器

支持格式: .floxml | .pack | .prj | .ecxml | .pdml

重要发现：
    - flotherm -b file.floxml  ✅ 可以直接执行
    - flotherm -b file.pack    ❌ 不支持
    - flotherm -b file.ecxml   ❌ 不支持

推荐工作流:
    1. GUI 打开模型 → File → Export → FloXML
    2. python floscript_runner.py model.floxml -o ./results
    3. python floscript_runner.py model.floxml -o ./results --power U1_CPU 15.0

使用方法:
    # FloXML（推荐，直接执行）
    python floscript_runner.py model.floxml -o ./results

    # 修改功耗后执行
    python floscript_runner.py model.floxml -o ./results --power U1_CPU 15.0

    # 批量参数扫描
    python floscript_runner.py model.floxml -o ./results --power-range U1_CPU 5 10 15 20 25

    # Pack 文件（需要先在 GUI 中导出为 FloXML）
    python floscript_runner.py model.pack -o ./results
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
    """FloTHERM 自动求解器"""

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
            '.floxml': 'floxml',   # FloXML - 无头模式推荐格式
            '.pack': 'pack',
            '.ecxml': 'ecxml',
            '.pdml': 'pdml',
            '.prj': 'prj',
        }
        return type_map.get(ext, 'unknown')

    def run_floxml(self, floxml_file: str, output_dir: str,
                   modify_power: dict = None, timeout: int = 7200) -> dict:
        """
        直接执行 FloXML 文件（推荐方式）

        FloXML 可以直接用 flotherm -b 执行，无需宏文件！

        Args:
            floxml_file: FloXML 文件路径
            output_dir: 输出目录
            modify_power: 要修改的功耗 {组件名: 功耗值}
            timeout: 超时时间
        """
        start_time = datetime.now()
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        results = {
            "model": str(floxml_file),
            "output_dir": str(output_dir),
            "start_time": start_time.isoformat(),
            "success": False,
        }

        actual_model = floxml_file

        # 如果需要修改功耗
        if modify_power:
            print(f"[INFO] 修改功耗: {modify_power}")
            modified_model = output_dir / "modified_model.floxml"
            actual_model = self._modify_floxml_power(floxml_file, modified_model, modify_power)

            if actual_model:
                print(f"[INFO] 已创建修改后的模型: {actual_model}")
            else:
                print("[WARN] 修改功耗失败，使用原始模型")
                actual_model = floxml_file

        log_file = output_dir / "simulation.log"

        # 直接执行: flotherm -b model.floxml
        cmd = [self.flotherm_path, "-b", str(actual_model)]

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

    def _modify_floxml_power(self, floxml_file: str, output_file: str,
                             power_map: dict) -> str:
        """修改 FloXML 文件中的功耗"""
        try:
            tree = ET.parse(floxml_file)
            root = tree.getroot()

            modified = False
            for elem in root.iter():
                # 查找组件名称
                name = elem.get('Name', elem.get('name', ''))

                # 也检查子元素中的名称
                name_elem = elem.find('.//Name')
                if name_elem is not None and name_elem.text:
                    name = name_elem.text

                for comp_name, power in power_map.items():
                    if name == comp_name or comp_name.lower() in name.lower():
                        # 查找功耗字段
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

    def _extract_from_pack(self, pack_file: str, output_dir: str) -> str:
        """
        从 Pack 文件中提取可用的模型文件

        Pack 文件是 ZIP 格式，内部可能包含:
        - .floxml (FloXML - 可直接执行)
        - .pdml (PDML - 需要转换)
        - .prj (项目文件)
        - group.pdml (主模型文件)
        """
        import zipfile

        output_dir = Path(output_dir)
        extract_dir = output_dir / "extracted"
        extract_dir.mkdir(parents=True, exist_ok=True)

        print(f"[INFO] 解压 Pack 文件: {pack_file}")

        try:
            with zipfile.ZipFile(pack_file, 'r') as zf:
                # 列出所有文件
                files = zf.namelist()
                print(f"[INFO] Pack 包含 {len(files)} 个文件")

                # 优先级：FloXML > PDML > PRJ
                floxml_files = [f for f in files if f.lower().endswith('.floxml')]
                pdml_files = [f for f in files if f.lower().endswith('.pdml')]
                prj_files = [f for f in files if f.lower().endswith('.prj')]

                # 解压所有文件
                zf.extractall(extract_dir)

                # 查找可用的模型文件
                if floxml_files:
                    # 找到 FloXML，直接使用
                    floxml_path = extract_dir / floxml_files[0]
                    print(f"[INFO] 找到 FloXML: {floxml_files[0]}")
                    return str(floxml_path)

                elif pdml_files:
                    # 找到 PDML，可能需要转换
                    # 优先使用 group.pdml 或 project.pdml
                    main_pdml = None
                    for pdml in pdml_files:
                        if 'group' in pdml.lower() or 'project' in pdml.lower():
                            main_pdml = extract_dir / pdml
                            break

                    if main_pdml is None:
                        main_pdml = extract_dir / pdml_files[0]

                    print(f"[INFO] 找到 PDML: {main_pdml.name}")
                    print("[WARN] PDML 格式需要转换为 FloXML")
                    print("[INFO] 请在 FloTHERM GUI 中:")
                    print("       1. File → Open → 选择解压后的 PDML")
                    print("       2. File → Export → FloXML")
                    return None

                elif prj_files:
                    print(f"[INFO] 找到项目文件: {prj_files[0]}")
                    print("[WARN] PRJ 格式需要转换为 FloXML")
                    return None

                else:
                    print("[WARN] Pack 中未找到可用的模型文件")
                    print(f"[INFO] Pack 内容: {files[:10]}")
                    return None

        except Exception as e:
            print(f"[ERROR] 解压 Pack 失败: {e}")
            return None

    def run_with_macro(self, model_file: str, macro_file: str, output_dir: str,
                       modify_power: dict = None, timeout: int = 7200) -> dict:
        """
        使用宏文件执行（兼容旧方式）

        注意: 对于 FloXML 文件，建议使用 run_floxml() 直接执行
        """
        # 这里保留原来的宏整合逻辑...
        pass


def main():
    parser = argparse.ArgumentParser(
        description='FloTHERM 自动求解器',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
示例:
  # FloXML（推荐，直接执行）
  python floscript_runner.py model.floxml -o ./results

  # 修改功耗后执行
  python floscript_runner.py model.floxml -o ./results --power U1_CPU 15.0

  # 批量参数扫描
  python floscript_runner.py model.floxml -o ./results --power-range U1_CPU 5 10 15 20 25

重要提示:
  - flotherm -b file.floxml  ✅ 可以直接执行
  - flotherm -b file.pack    ❌ 不支持
  - flotherm -b file.ecxml   ❌ 不支持

  请先在 GUI 中将模型导出为 FloXML 格式！
        '''
    )

    parser.add_argument('model', help='模型文件 (.floxml 推荐, .pack, .ecxml)')
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

    file_type = runner._get_file_type(args.model)

    # 检查文件类型
    if file_type != 'floxml':
        print(f"\n[INFO] 文件类型: {file_type}")
        print("[INFO] flotherm -b 直接支持 .floxml 格式")
        print()

        if file_type == 'pack':
            # Pack 文件：提取内部的模型文件
            print("[INFO] 正在提取 Pack 文件内容...")
            extracted = runner._extract_from_pack(args.model, args.output)
            if extracted:
                print(f"[INFO] 提取成功，找到模型文件")
                print(f"[INFO] 使用提取的模型继续执行...")
                args.model = extracted
            else:
                print("[WARN] 无法从 Pack 中提取可用模型")
                print("[INFO] 请在 FloTHERM GUI 中:")
                print("       1. 打开 Pack 文件")
                print("       2. File → Export → FloXML")
                print("       3. 重新运行本脚本")
                sys.exit(1)
        else:
            print("[INFO] 请在 FloTHERM GUI 中导出为 FloXML:")
            print("       1. 打开模型")
            print("       2. File → Export → FloXML")
            print("       3. 重新运行本脚本")
            sys.exit(1)

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
            result = runner.run_floxml(
                floxml_file=args.model,
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
        runner.run_floxml(
            floxml_file=args.model,
            output_dir=args.output,
            modify_power=power_map if power_map else None,
            timeout=args.timeout
        )


if __name__ == '__main__':
    main()
