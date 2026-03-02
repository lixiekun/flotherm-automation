#!/usr/bin/env python3
"""
FloSCRIPT 创建指南

由于 FloSCRIPT XML 有严格的 Schema 定义，自动生成可能不被识别。
本脚本提供以下方法来获取正确的 FloSCRIPT XML：

方法1: 在 FloTHERM GUI 中录制宏（推荐）
方法2: 使用官方示例模板
方法3: 手动编辑 Schema 兼容的 XML

使用方法:
    python create_floscript_guide.py --show-gui-steps
    python create_floscript_guide.py --list-examples
    python create_floscript_guide.py --create-template
"""

import os
import sys
import argparse
from pathlib import Path

# FloSCRIPT 录制步骤指南
GUI_RECORDING_STEPS = """
================================================================================
                    FloTHERM 宏录制步骤（推荐）
================================================================================

1. 启动 FloTHERM GUI
   - 打开 FloTHERM 软件

2. 打开你的模型
   - File -> Open -> 选择你的 .pack 或 .prj 文件

3. 开始录制宏
   - 菜单: Tools -> Macro -> Record...
   - 选择保存位置和文件名（例如: solve_simulation.xml）

4. 执行你想要的操作
   - Model -> Reinitialize（重新初始化）
   - Model -> Solve（求解）
   - 等待求解完成
   - File -> Save As...（保存结果）

5. 停止录制
   - 菜单: Tools -> Macro -> Stop Recording

6. 测试录制的宏
   命令行执行:
   flotherm -b -f solve_simulation.xml

7. 批量使用
   - 可以编辑录制的 .xml 文件
   - 修改模型路径、参数等
   - 用于批量自动化

================================================================================
"""

# 官方示例目录说明
OFFICIAL_EXAMPLES_INFO = """
================================================================================
                    FloTHERM 官方示例位置
================================================================================

FloSCRIPT 示例目录（包含可用的 .xml 脚本）:
  - FloTHERM 2020.2:
    C:\\Program Files\\Siemens\\SimcenterFlotherm\\2020.2\\examples\\FloSCRIPT\\

  - FloTHERM v12:
    D:\\flotherm\\flosuite_v12\\flotherm\\examples\\FloSCRIPT\\

  - 通用路径:
    <FloTHERM安装目录>\\examples\\FloSCRIPT\\

FloSCRIPT Schema 文档（XML 格式定义）:
  <FloTHERM安装目录>\\docs\\Schema-Documentation\\FloSCRIPT\\

教程文件:
  <FloTHERM安装目录>\\examples\\FloSCRIPT\\Tutorial\\FloSCRIPTv11-Tutorial

常用示例文件:
  - Utilities/Grid-HeatSinks-and-Fans.xml  (网格和散热器示例)
  - Tutorial/  (教程示例)

================================================================================
"""

# FloSCRIPT 基本模板
FLOSCRIPT_TEMPLATE = """
<!-- FloSCRIPT 基本模板 -->
<!-- 注意：此模板可能需要根据你的 FloTHERM 版本调整 -->

<FloSCRIPT version="1.0">
    <!-- 加载项目文件 -->
    <Command name="Load" file="YOUR_MODEL_PATH.pack"/>

    <!-- 重新初始化 -->
    <Command name="Reinitialize"/>

    <!-- 求解 -->
    <Command name="Solve"/>

    <!-- 保存结果 -->
    <Command name="Save" file="OUTPUT_PATH.pack"/>
</FloSCRIPT>

使用方法:
1. 将 YOUR_MODEL_PATH.pack 替换为你的模型路径
2. 将 OUTPUT_PATH.pack 替换为输出路径
3. 执行: flotherm -b -f this_script.xml

警告: 此模板可能不被所有 FloTHERM 版本识别！
建议使用 GUI 录制宏来获取正确的 XML 格式。
"""


def find_flotherm_examples():
    """查找 FloTHERM 示例目录"""
    possible_paths = [
        r"C:\Program Files\Siemens\SimcenterFlotherm\2020.2\examples\FloSCRIPT",
        r"C:\Program Files\Siemens\SimcenterFlotherm\2410\examples\FloSCRIPT",
        r"C:\Program Files\Mentor Graphics\FloTHERM\v2020.2\examples\FloSCRIPT",
        r"C:\Program Files (x86)\Mentor Graphics\FloTHERM\v2020.2\examples\FloSCRIPT",
        r"D:\flotherm\flosuite_v12\flotherm\examples\FloSCRIPT",
    ]

    found = []
    for path in possible_paths:
        if os.path.exists(path):
            found.append(path)

    return found


def list_example_files(example_dir):
    """列出示例目录中的文件"""
    if not os.path.exists(example_dir):
        print(f"[ERROR] 目录不存在: {example_dir}")
        return

    print(f"\n示例目录: {example_dir}")
    print("-" * 60)

    for root, dirs, files in os.walk(example_dir):
        level = root.replace(example_dir, '').count(os.sep)
        indent = ' ' * 2 * level
        print(f"{indent}{os.path.basename(root)}/")
        subindent = ' ' * 2 * (level + 1)
        for file in files:
            if file.endswith('.xml'):
                print(f"{subindent}{file}")


def create_basic_template(output_path):
    """创建基本模板文件"""
    template = """<?xml version="1.0" encoding="UTF-8"?>
<!--
FloSCRIPT 模板 - 需要根据实际情况修改

重要提示:
1. FloSCRIPT XML 有严格的 Schema 定义
2. 建议使用 FloTHERM GUI 录制宏来获取正确的格式
3. 参考 FloTHERM 安装目录下的 examples/FloSCRIPT/ 示例

使用方法:
1. 修改下面的模型路径
2. 执行: flotherm -b -f this_script.xml
-->
<FloSCRIPT version="1.0">
    <!-- 修改为你的模型路径 -->
    <Command name="Load" file="C:/path/to/your/model.pack"/>

    <!-- 重新初始化网格 -->
    <Command name="Reinitialize"/>

    <!-- 执行求解 -->
    <Command name="Solve"/>

    <!-- 保存结果 -->
    <Command name="Save" file="C:/path/to/output/solved.pack"/>
</FloSCRIPT>
"""
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(template)

    print(f"[INFO] 模板已创建: {output_path}")
    print("[WARN] 此模板可能需要调整才能正常工作！")
    print("[INFO] 建议使用 GUI 录制宏来获取正确的格式")


def main():
    parser = argparse.ArgumentParser(
        description='FloSCRIPT 创建指南',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
示例:
  # 显示 GUI 录制步骤
  python create_floscript_guide.py --show-gui-steps

  # 显示官方示例位置
  python create_floscript_guide.py --list-examples

  # 创建基本模板
  python create_floscript_guide.py --create-template template.xml
        '''
    )

    parser.add_argument('--show-gui-steps', action='store_true',
                       help='显示 GUI 录制步骤')
    parser.add_argument('--list-examples', action='store_true',
                       help='列出官方示例位置')
    parser.add_argument('--create-template', metavar='FILE',
                       help='创建基本模板文件')
    parser.add_argument('--find-examples', action='store_true',
                       help='自动查找 FloTHERM 示例目录')

    args = parser.parse_args()

    if args.show_gui_steps:
        print(GUI_RECORDING_STEPS)

    if args.list_examples:
        print(OFFICIAL_EXAMPLES_INFO)

    if args.find_examples:
        found = find_flotherm_examples()
        if found:
            print("\n找到 FloSCRIPT 示例目录:")
            for path in found:
                print(f"  - {path}")
                list_example_files(path)
        else:
            print("[WARN] 未找到 FloTHERM 示例目录")
            print("[INFO] 请确认 FloTHERM 已安装")

    if args.create_template:
        create_basic_template(args.create_template)

    # 如果没有参数，显示所有信息
    if len(sys.argv) == 1:
        print(GUI_RECORDING_STEPS)
        print(OFFICIAL_EXAMPLES_INFO)
        print("\n快速开始:")
        print("  1. 在 FloTHERM GUI 中录制宏（推荐）")
        print("  2. 执行: flotherm -b -f your_macro.xml")
        print()
        print("更多帮助:")
        print("  python create_floscript_guide.py --show-gui-steps")
        print("  python create_floscript_guide.py --list-examples")


if __name__ == '__main__':
    main()
