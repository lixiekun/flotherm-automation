#!/usr/bin/env python3
"""
Pack 到 FloXML 自动转换器

尝试多种方法将 Pack 文件转换为 FloXML 格式：

方法 1: 命令行转换（如果 FloTHERM 支持）
方法 2: Windows COM 自动化（控制 GUI 进行转换）
方法 3: AppleScript (macOS)
方法 4: 交互式指导（如果自动方法都失败）

使用方法:
    python pack_to_floxml_converter.py model.pack -o output.floxml
    python pack_to_floxml_converter.py model.pack --batch ./floxml_output/
    python pack_to_floxml_converter.py model.pack --method com
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


class PackToFloXMLConverter:
    """Pack 到 FloXML 转换器"""

    def __init__(self, flotherm_path: str = None):
        self.flotherm_path = flotherm_path or self._auto_detect_flotherm()
        self.platform = sys.platform

    def _auto_detect_flotherm(self) -> str:
        """自动检测 FloTHERM 路径"""
        if sys.platform == 'win32':
            paths = [
                r"C:\Program Files\Siemens\SimcenterFlotherm\2020.2\bin\flosuite.exe",
                r"C:\Program Files\Siemens\SimcenterFlotherm\2020.2\bin\flotherm.exe",
                r"C:\Program Files\Siemens\SimcenterFlotherm\2410\bin\flotherm.exe",
                r"C:\Program Files\Mentor Graphics\FloTHERM\v2020.2\flosuite\bin\flotherm.exe",
            ]
        else:
            paths = [
                "/opt/Siemens/SimcenterFlotherm/2020.2/bin/flotherm",
                "/Applications/FloTHERM.app/Contents/MacOS/flotherm",
            ]

        for path in paths:
            if os.path.exists(path):
                print(f"[INFO] 检测到 FloTHERM: {path}")
                return path

        return "flotherm"

    def convert(self, pack_file: str, output_floxml: str, method: str = 'auto') -> dict:
        """
        转换 Pack 文件到 FloXML

        Args:
            pack_file: Pack 文件路径
            output_floxml: 输出 FloXML 路径
            method: 转换方法 (auto, cli, com, applescript, guide)

        Returns:
            转换结果字典
        """
        result = {
            "input": str(pack_file),
            "output": str(output_floxml),
            "success": False,
            "method_used": None,
            "error": None
        }

        print(f"\n{'='*60}")
        print(f"  Pack → FloXML 转换器")
        print(f"{'='*60}")
        print(f"  输入: {pack_file}")
        print(f"  输出: {output_floxml}")
        print(f"  平台: {self.platform}")
        print(f"{'='*60}\n")

        # 检查输入文件
        if not os.path.exists(pack_file):
            result["error"] = f"输入文件不存在: {pack_file}"
            print(f"[ERROR] {result['error']}")
            return result

        # 根据方法选择转换方式
        methods = {
            'auto': self._convert_auto,
            'cli': self._convert_cli,
            'com': self._convert_com,
            'applescript': self._convert_applescript,
            'guide': self._show_guide,
        }

        if method not in methods:
            print(f"[ERROR] 未知方法: {method}")
            print(f"[INFO] 可用方法: {', '.join(methods.keys())}")
            result["error"] = f"未知方法: {method}"
            return result

        convert_func = methods[method]
        success = convert_func(pack_file, output_floxml)

        result["success"] = success
        result["method_used"] = method

        if success and os.path.exists(output_floxml):
            size = os.path.getsize(output_floxml)
            print(f"\n[SUCCESS] 转换成功!")
            print(f"          输出文件: {output_floxml}")
            print(f"          文件大小: {self._format_size(size)}")
        else:
            print(f"\n[FAILED] 转换失败")

        return result

    def _convert_auto(self, pack_file: str, output_floxml: str) -> bool:
        """自动尝试所有方法"""
        print("[INFO] 自动模式：尝试所有转换方法...\n")

        # 尝试顺序
        methods_to_try = []

        if self.platform == 'win32':
            methods_to_try = [
                ('CLI 命令行', self._convert_cli),
                ('COM 自动化', self._convert_com),
            ]
        else:
            methods_to_try = [
                ('CLI 命令行', self._convert_cli),
                ('AppleScript', self._convert_applescript),
            ]

        for name, method in methods_to_try:
            print(f"\n[INFO] 尝试方法: {name}")
            print("-" * 40)
            try:
                if method(pack_file, output_floxml):
                    print(f"[INFO] {name} 转换成功!")
                    return True
            except Exception as e:
                print(f"[WARN] {name} 失败: {e}")

        # 所有自动方法都失败，显示手动指南
        print("\n[INFO] 所有自动方法都失败，显示手动转换指南...")
        self._show_guide(pack_file, output_floxml)
        return False

    def _convert_cli(self, pack_file: str, output_floxml: str) -> bool:
        """尝试使用命令行参数转换"""
        print("[INFO] 尝试命令行转换...")

        # 先提取 Pack 内容，检查内部格式
        extracted_info = self._analyze_pack_contents(pack_file)
        pdml_file = extracted_info.get('pdml_file')

        # FloTHERM 可能的命令行参数
        cli_attempts = [
            # 尝试 1: 直接执行 Pack 文件
            [self.flotherm_path, "-b", pack_file],
            # 尝试 2: 直接执行 PDML（如果存在）
            [self.flotherm_path, "-b", pdml_file] if pdml_file else None,
            # 尝试 3: 使用 -nogui 参数
            [self.flotherm_path, "-nogui", pack_file],
            # 尝试 4: 使用 -batch 参数
            [self.flotherm_path, "-batch", pack_file],
        ]

        # 过滤掉 None
        cli_attempts = [cmd for cmd in cli_attempts if cmd is not None]

        for i, cmd in enumerate(cli_attempts, 1):
            print(f"\n  尝试 {i}: {' '.join(cmd)}")
            try:
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=30
                )

                print(f"  返回码: {result.returncode}")
                if result.stdout:
                    print(f"  输出: {result.stdout[:300]}")
                if result.stderr:
                    print(f"  错误: {result.stderr[:300]}")

                # 检查是否有 FloTHERM 进程在运行
                # 如果命令启动了 GUI，可能需要等待

            except subprocess.TimeoutExpired:
                print(f"  [WARN] 超时")
            except FileNotFoundError:
                print(f"  [WARN] 找不到 FloTHERM: {self.flotherm_path}")
                break
            except Exception as e:
                print(f"  [WARN] 错误: {e}")

        # 尝试使用宏文件导出
        print("\n[INFO] 尝试使用宏文件导出...")
        if self._try_export_with_macro(pack_file, output_floxml):
            return True

        print("\n[INFO] 命令行转换不支持")
        return False

    def _analyze_pack_contents(self, pack_file: str) -> dict:
        """分析 Pack 文件内容"""
        info = {'has_floxml': False, 'has_pdml': False, 'pdml_file': None}

        try:
            with zipfile.ZipFile(pack_file, 'r') as zf:
                files = zf.namelist()
                print(f"  [INFO] Pack 包含 {len(files)} 个文件")

                for f in files:
                    ext = Path(f).suffix.lower()
                    if ext == '.floxml':
                        info['has_floxml'] = True
                        print(f"  [FOUND] FloXML: {f}")
                    elif ext == '.pdml':
                        info['has_pdml'] = True
                        info['pdml_file'] = f
                        print(f"  [FOUND] PDML: {f}")

                # 列出主要文件
                for f in files[:10]:
                    print(f"    - {f}")
                if len(files) > 10:
                    print(f"    ... 还有 {len(files) - 10} 个文件")

        except Exception as e:
            print(f"  [ERROR] 分析 Pack 失败: {e}")

        return info

    def _try_export_with_macro(self, pack_file: str, output_floxml: str) -> bool:
        """尝试使用宏文件导出 FloXML"""
        abs_pack_path = os.path.abspath(pack_file)
        abs_output_path = os.path.abspath(output_floxml)
        output_dir = os.path.dirname(abs_output_path)

        # 创建一个导出宏
        macro_content = f'''<?xml version="1.0" encoding="UTF-8"?>
<FloSCRIPT version="1.0">
    <!-- 加载 Pack 文件 -->
    <Command name="Open" file="{abs_pack_path}"/>

    <!-- 等待加载 -->
    <Wait seconds="3"/>

    <!-- 保存为 FloXML（尝试） -->
    <Command name="SaveAs" file="{abs_output_path}" format="FloXML"/>
</FloSCRIPT>
'''

        macro_file = os.path.join(output_dir, "export_macro.xml")
        with open(macro_file, 'w', encoding='utf-8') as f:
            f.write(macro_content)

        print(f"  [INFO] 创建宏文件: {macro_file}")

        # 尝试执行宏
        cmd = [self.flotherm_path, "-b", "-f", macro_file]
        print(f"  [INFO] 执行: {' '.join(cmd)}")

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=60,
                cwd=output_dir
            )

            print(f"  返回码: {result.returncode}")
            if result.stdout:
                print(f"  输出: {result.stdout[:500]}")
            if result.stderr:
                print(f"  错误: {result.stderr[:500]}")

            if os.path.exists(abs_output_path):
                print(f"  [OK] 导出成功!")
                return True

        except subprocess.TimeoutExpired:
            print(f"  [WARN] 超时")
        except Exception as e:
            print(f"  [ERROR] {e}")

        return False

    def _convert_com(self, pack_file: str, output_floxml: str) -> bool:
        """
        使用 Windows COM 自动化转换

        这需要 pywin32 库: pip install pywin32
        """
        if self.platform != 'win32':
            print("[WARN] COM 自动化仅支持 Windows")
            return False

        print("[INFO] 尝试 COM 自动化...")

        try:
            import win32com.client
        except ImportError:
            print("[ERROR] 需要安装 pywin32: pip install pywin32")
            return False

        try:
            print("  [INFO] 连接 FloTHERM 应用...")

            # 尝试获取 FloTHERM COM 对象
            # FloTHERM 的 COM 接口名称可能是:
            # - "FloTHERM.Application"
            # - "SimcenterFlotherm.Application"
            com_names = [
                "FloTHERM.Application",
                "SimcenterFlotherm.Application",
                "MGC.FloTHERM.Application",
            ]

            app = None
            for com_name in com_names:
                try:
                    app = win32com.client.Dispatch(com_name)
                    print(f"  [OK] 已连接: {com_name}")
                    break
                except Exception as e:
                    continue

            if app is None:
                print("  [ERROR] 无法连接到 FloTHERM COM 接口")
                print("  [INFO] 请确保 FloTHERM 已正确安装并注册 COM 组件")
                return False

            # 打开 Pack 文件
            print(f"  [INFO] 打开文件: {pack_file}")
            abs_pack_path = os.path.abspath(pack_file)
            abs_floxml_path = os.path.abspath(output_floxml)

            # 尝试打开项目
            # 方法名可能是: OpenProject, Open, LoadProject
            try:
                app.OpenProject(abs_pack_path)
            except:
                try:
                    app.Open(abs_pack_path)
                except:
                    print("  [WARN] 无法打开项目")
                    return False

            print("  [OK] 文件已打开")

            # 导出为 FloXML
            print(f"  [INFO] 导出 FloXML: {abs_floxml_path}")
            try:
                app.ExportFloXML(abs_floxml_path)
            except:
                try:
                    app.Export(abs_floxml_path, "FloXML")
                except:
                    print("  [WARN] 无法导出 FloXML")
                    return False

            # 关闭项目
            try:
                app.CloseProject(False)  # 不保存更改
            except:
                pass

            if os.path.exists(abs_floxml_path):
                print("  [OK] FloXML 导出成功!")
                return True
            else:
                print("  [ERROR] 导出文件未创建")
                return False

        except Exception as e:
            print(f"  [ERROR] COM 自动化失败: {e}")
            return False

    def _convert_applescript(self, pack_file: str, output_floxml: str) -> bool:
        """
        使用 AppleScript 控制 macOS 应用

        注意: FloTHERM 可能没有 macOS 版本的 AppleScript 支持
        """
        if self.platform != 'darwin':
            print("[WARN] AppleScript 仅支持 macOS")
            return False

        print("[INFO] 尝试 AppleScript 自动化...")

        abs_pack_path = os.path.abspath(pack_file)
        abs_floxml_path = os.path.abspath(output_floxml)

        # AppleScript 代码
        script = f'''
        tell application "FloTHERM"
            activate
            open POSIX file "{abs_pack_path}"
            delay 2
            -- 尝试导出 FloXML
            -- 注意: 需要根据实际的菜单结构调整
        end tell
        '''

        try:
            result = subprocess.run(
                ['osascript', '-e', script],
                capture_output=True,
                text=True,
                timeout=60
            )

            if result.returncode == 0:
                print("  [OK] AppleScript 执行成功")
                # 检查文件是否创建
                if os.path.exists(abs_floxml_path):
                    return True
            else:
                print(f"  [WARN] AppleScript 错误: {result.stderr}")

        except subprocess.TimeoutExpired:
            print("  [WARN] AppleScript 超时")
        except Exception as e:
            print(f"  [ERROR] AppleScript 失败: {e}")

        return False

    def _show_guide(self, pack_file: str, output_floxml: str) -> bool:
        """显示手动转换指南"""
        # 先分析 Pack 内容
        info = self._analyze_pack_contents(pack_file)

        guide = f"""
================================================================================
                    FloTHERM 格式转换问题
================================================================================

⚠️  重要发现：FloTHERM GUI 没有 FloXML 导出功能！

FloTHERM 的格式支持：
  ✅ 导入 FloXML (File → Import → FloXML)
  ❌ 导出 FloXML (无此功能)
  ✅ 打开 Pack 文件
  ✅ 保存为 Pack 文件
  ✅ 导出 ECXML (部分版本支持)

================================================================================
                    可行的解决方案
================================================================================

方案 1: 直接使用 PDML 文件（如果可用）
─────────────────────────────────────────
"""

        if info.get('pdml_file'):
            guide += f"""✅ 你的 Pack 文件包含 PDML: {info['pdml_file']}

    # 解压 Pack 文件
    python pack_editor.py {pack_file} --extract ./extracted

    # 尝试直接使用 PDML
    flotherm -b ./extracted/{info['pdml_file']}
"""
        else:
            guide += """❌ Pack 文件中未找到 PDML 文件

    # 先解压查看内容
    python pack_editor.py {pack_file} --extract ./extracted
"""

        guide += f"""
方案 2: 录制宏来自动化求解
─────────────────────────────────────────
由于无法转换为 FloXML，可以使用宏来批量处理 Pack 文件：

    1. 在 FloTHERM GUI 中录制宏：
       - Tools → Macro → Record...
       - 打开 Pack 文件
       - 执行求解操作
       - 保存结果
       - Tools → Macro → Stop Recording

    2. 使用录制的宏进行批量处理：
       flotherm -b -f recorded_macro.xml

方案 3: 使用 ECXML（如果支持）
─────────────────────────────────────────
某些版本的 FloTHERM 支持 ECXML 导出：

    1. 在 GUI 中打开 Pack 文件
    2. File → Export → ECXML（如果有）
    3. 使用 ECXML 进行后续处理

方案 4: 使用 GUI 自动化工具
─────────────────────────────────────────
使用 PyAutoGUI 或类似工具自动化 GUI 操作：

    pip install pyautogui

    然后编写脚本自动点击菜单和按钮。

================================================================================
                    Pack 文件内容
================================================================================
"""

        # 显示 Pack 内容
        try:
            with zipfile.ZipFile(pack_file, 'r') as zf:
                files = zf.namelist()
                for f in files[:20]:
                    guide += f"  - {f}\n"
                if len(files) > 20:
                    guide += f"  ... 还有 {len(files) - 20} 个文件\n"
        except:
            pass

        guide += f"""
================================================================================
                    建议的工作流
================================================================================

由于 FloTHERM 的限制，建议：

1. 如果只需要求解，使用录制的宏：
   - 一次录制，多次使用
   - 适合批量处理相同类型的模型

2. 如果需要修改参数：
   - 使用 pack_editor.py 修改 Pack 内的 PDML 文件
   - 或使用 ecxml_editor.py 修改 ECXML（如果可以导出）

3. 联系 Siemens 支持：
   - 询问是否有命令行转换工具
   - 或是否有 API 可以导出 FloXML

================================================================================
"""
        print(guide)
        return False

    def batch_convert(self, pack_files: list, output_dir: str) -> dict:
        """
        批量转换 Pack 文件

        生成一个批处理脚本，指导用户进行批量转换
        """
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        results = {
            "total": len(pack_files),
            "converted": 0,
            "failed": 0,
            "files": []
        }

        print(f"\n{'='*60}")
        print(f"  批量转换模式")
        print(f"{'='*60}")
        print(f"  文件数量: {len(pack_files)}")
        print(f"  输出目录: {output_dir}")
        print(f"{'='*60}\n")

        # 如果是 Windows，生成批处理脚本
        if self.platform == 'win32':
            bat_file = output_dir / "convert_all.bat"
            with open(bat_file, 'w', encoding='utf-8') as f:
                f.write("@echo off\n")
                f.write("echo ========================================\n")
                f.write("echo   FloTHERM Pack 到 FloXML 批量转换\n")
                f.write("echo ========================================\n")
                f.write("echo.\n")
                f.write(f"set FLOTHERM={self.flotherm_path}\n")
                f.write("echo 请在 FloTHERM GUI 中手动完成转换:\n")
                f.write("echo   1. 打开 FloTHERM\n")
                f.write("echo   2. File -^> Open -^> 选择 Pack 文件\n")
                f.write("echo   3. File -^> Export -^> FloXML\n")
                f.write("echo.\n")
                f.write("pause\n")

                for pack_file in pack_files:
                    pack_path = Path(pack_file)
                    floxml_name = pack_path.stem + ".floxml"
                    floxml_path = output_dir / floxml_name

                    f.write(f"\necho 转换: {pack_path.name}\n")
                    f.write(f"echo   输入: {pack_path.absolute()}\n")
                    f.write(f"echo   输出: {floxml_path.absolute()}\n")

                f.write("\necho.\n")
                f.write("echo 转换完成后，运行:\n")
                f.write("echo   python floscript_runner.py <floxml_file> -o ./results\n")

            print(f"[INFO] 已生成批处理脚本: {bat_file}")

        # 生成 Python 批量转换脚本
        py_script = output_dir / "batch_convert_helper.py"
        with open(py_script, 'w', encoding='utf-8') as f:
            f.write('''#!/usr/bin/env python3
"""
批量转换辅助脚本

此脚本帮助你批量转换 Pack 文件到 FloXML。
由于 FloTHERM 的限制，需要通过 GUI 手动完成转换。

工作流程:
1. 此脚本依次打开每个 Pack 文件
2. 你在 GUI 中执行 File → Export → FloXML
3. 脚本等待你完成导出
4. 继续下一个文件
"""

import os
import sys
import subprocess
import time
from pathlib import Path

PACK_FILES = [
''')
            for pack_file in pack_files:
                f.write(f'    r"{os.path.abspath(pack_file)}",\n')

            f.write(''']

OUTPUT_DIR = r"''' + str(output_dir.absolute()) + '''"

def main():
    print("=" * 60)
    print("  批量转换辅助脚本")
    print("=" * 60)

    for i, pack_file in enumerate(PACK_FILES, 1):
        print(f"\\n[{i}/{len(PACK_FILES)}] 处理: {Path(pack_file).name}")
        print("-" * 40)

        pack_path = Path(pack_file)
        floxml_name = pack_path.stem + ".floxml"
        floxml_path = Path(OUTPUT_DIR) / floxml_name

        print(f"  输入: {pack_file}")
        print(f"  输出: {floxml_path}")
        print()
        print("  请执行以下操作:")
        print("  1. 在打开的 FloTHERM 中，File → Export → FloXML")
        print(f"  2. 保存为: {floxml_path}")
        print("  3. 完成后关闭项目")
        print()

        # 尝试打开 Pack 文件
        if sys.platform == 'win32':
            os.startfile(pack_file)
        else:
            subprocess.run(['open', pack_file])

        input("  按 Enter 继续下一个文件...")

        if floxml_path.exists():
            print(f"  [OK] 已找到输出文件")
        else:
            print(f"  [WARN] 未找到输出文件，请确认已正确导出")

    print("\\n" + "=" * 60)
    print("  批量转换完成!")
    print("=" * 60)
    print(f"\\n  输出目录: {OUTPUT_DIR}")
    print("\\n  下一步: 使用 floscript_runner.py 进行自动化求解")
    print("    python floscript_runner.py <floxml_file> -o ./results")

if __name__ == '__main__':
    main()
''')

        print(f"[INFO] 已生成批量转换辅助脚本: {py_script}")
        print(f"\n[INFO] 请运行以下命令开始批量转换:")
        print(f"      python {py_script}")

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
        description='Pack 到 FloXML 自动转换器',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
示例:
  # 单文件转换（自动选择方法）
  python pack_to_floxml_converter.py model.pack -o output.floxml

  # 指定转换方法
  python pack_to_floxml_converter.py model.pack -o output.floxml --method com

  # 批量转换
  python pack_to_floxml_converter.py *.pack --batch ./floxml_output/

  # 仅显示手动指南
  python pack_to_floxml_converter.py model.pack -o output.floxml --method guide

转换方法:
  auto       - 自动尝试所有方法（默认）
  cli        - 仅尝试命令行参数
  com        - 仅尝试 Windows COM 自动化
  applescript- 仅尝试 macOS AppleScript
  guide      - 显示手动转换指南
        '''
    )

    parser.add_argument('pack_files', nargs='+', help='Pack 文件路径')
    parser.add_argument('-o', '--output', help='输出 FloXML 路径（单文件模式）')
    parser.add_argument('--batch', metavar='DIR', help='批量转换输出目录')
    parser.add_argument('--method', choices=['auto', 'cli', 'com', 'applescript', 'guide'],
                       default='auto', help='转换方法')
    parser.add_argument('--flotherm', help='FloTHERM 可执行文件路径')

    args = parser.parse_args()

    converter = PackToFloXMLConverter(flotherm_path=args.flotherm)

    # 批量模式
    if args.batch:
        converter.batch_convert(args.pack_files, args.batch)
        return

    # 单文件模式
    if len(args.pack_files) > 1:
        print("[ERROR] 单文件模式只能指定一个 Pack 文件")
        print("[INFO] 使用 --batch 进行批量转换")
        sys.exit(1)

    if not args.output:
        # 自动生成输出文件名
        pack_path = Path(args.pack_files[0])
        args.output = str(pack_path.with_suffix('.floxml'))

    result = converter.convert(
        pack_file=args.pack_files[0],
        output_floxml=args.output,
        method=args.method
    )

    sys.exit(0 if result['success'] else 1)


if __name__ == '__main__':
    main()
