#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Excel 多配置批量仿真工具

功能:
    1. 从 Excel 读取多个测试配置
    2. 根据每个配置修改 ECXML 模板文件
    3. 批量调用 FloTHERM 求解

使用方法:
    python excel_batch_simulation.py template.ecxml config.xlsx -o ./output
    python excel_batch_simulation.py template.ecxml config.xlsx -o ./output --no-solve
    python excel_batch_simulation.py template.ecxml config.xlsx -o ./output --sheet "配置1"

Excel 格式（简单格式）:
    | config_name | U1_CPU | U2_GPU | Ambient |
    |-------------|--------|--------|---------|
    | case1       | 10     | 5      | 25      |
    | case2       | 15     | 8      | 35      |

    - 第一列必须是 config_name（配置名称）
    - 其他列名对应 ECXML 中的器件名或边界条件名
    - 数值自动识别：功耗（W）或温度（°C）
"""

import os
import sys
import argparse
import shutil
import time
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional

# 尝试导入 openpyxl 或 pandas
try:
    import openpyxl
    HAS_OPENPYXL = True
except ImportError:
    HAS_OPENPYXL = False

try:
    import pandas as pd
    HAS_PANDAS = True
except ImportError:
    HAS_PANDAS = False

# 导入现有的 ECXML 编辑器
from ecxml_editor import ECXMLParser


class ExcelConfigReader:
    """Excel 配置读取器"""

    def __init__(self, filepath: str, sheet_name: str = None):
        """
        初始化

        Args:
            filepath: Excel 文件路径
            sheet_name: Sheet 名称（可选，默认使用第一个 sheet）
        """
        self.filepath = filepath
        self.sheet_name = sheet_name
        self.configs = []

        if not os.path.exists(filepath):
            raise FileNotFoundError(f"Excel 文件不存在: {filepath}")

    def read(self) -> List[Dict[str, Any]]:
        """
        读取 Excel 配置

        Returns:
            配置列表，每个配置是一个字典
        """
        if HAS_OPENPYXL:
            return self._read_with_openpyxl()
        elif HAS_PANDAS:
            return self._read_with_pandas()
        else:
            raise ImportError("需要安装 openpyxl 或 pandas 来读取 Excel 文件\n"
                            "安装命令: pip install openpyxl 或 pip install pandas")

    def _read_with_openpyxl(self) -> List[Dict[str, Any]]:
        """使用 openpyxl 读取"""
        wb = openpyxl.load_workbook(self.filepath)

        # 选择 sheet
        if self.sheet_name:
            if self.sheet_name not in wb.sheetnames:
                raise ValueError(f"Sheet '{self.sheet_name}' 不存在，可用: {wb.sheetnames}")
            ws = wb[self.sheet_name]
        else:
            ws = wb.active

        # 读取表头
        headers = []
        for cell in ws[1]:
            if cell.value:
                headers.append(str(cell.value).strip())
            else:
                headers.append(f"col_{cell.column}")

        # 验证第一列是 config_name
        if headers[0].lower() != 'config_name':
            print(f"⚠️ 警告: 第一列不是 'config_name'，使用 '{headers[0]}' 作为配置名称列")

        # 读取数据行
        configs = []
        for row_idx, row in enumerate(ws.iter_rows(min_row=2, values_only=True), start=2):
            if not row[0]:  # 跳过空行
                continue

            config = {'_row': row_idx}
            for i, header in enumerate(headers):
                if i < len(row):
                    config[header] = row[i]

            configs.append(config)

        wb.close()
        self.configs = configs
        return configs

    def _read_with_pandas(self) -> List[Dict[str, Any]]:
        """使用 pandas 读取"""
        df = pd.read_excel(self.filepath, sheet_name=self.sheet_name or 0)

        # 验证第一列
        first_col = df.columns[0]
        if first_col.lower() != 'config_name':
            print(f"⚠️ 警告: 第一列不是 'config_name'，使用 '{first_col}' 作为配置名称列")

        # 转换为字典列表
        configs = []
        for idx, row in df.iterrows():
            config = {'_row': idx + 2}  # Excel 行号从 2 开始（1 是表头）
            for col in df.columns:
                val = row[col]
                if pd.isna(val):
                    continue
                config[col] = val
            configs.append(config)

        self.configs = configs
        return configs

    def get_config_names(self) -> List[str]:
        """获取所有配置名称"""
        name_col = None
        if self.configs:
            for key in self.configs[0]:
                if key.lower() == 'config_name' or key == '_row':
                    continue
                name_col = key
                break
            if 'config_name' in self.configs[0]:
                name_col = 'config_name'
            elif self.configs:
                name_col = list(self.configs[0].keys())[1] if len(self.configs[0]) > 1 else None

        if name_col:
            return [c.get(name_col, f"config_{i}") for i, c in enumerate(self.configs)]
        return [f"config_{i}" for i in range(len(self.configs))]


def find_flotherm_executable() -> Optional[str]:
    """查找 FloTHERM 可执行文件"""
    possible_paths = [
        # Siemens 版本路径
        r"C:\Program Files\Siemens\SimcenterFlotherm\2020.2\bin\flotherm.exe",
        r"C:\Program Files\Siemens\SimcenterFlotherm\2021.1\bin\flotherm.exe",
        r"C:\Program Files\Siemens\SimcenterFlotherm\2021.2\bin\flotherm.exe",
        r"C:\Program Files\Siemens\SimcenterFlotherm\2022.1\bin\flotherm.exe",
        r"C:\Program Files\Siemens\SimcenterFlotherm\2023.1\bin\flotherm.exe",
        r"C:\Program Files\Siemens\SimcenterFlotherm\2024.1\bin\flotherm.exe",
        r"C:\Program Files (x86)\Siemens\SimcenterFlotherm\2020.2\bin\flotherm.exe",
        # Mentor 版本路径
        r"C:\Program Files\MentorMA\flosuite_v13\flotherm\bin\flotherm.exe",
        r"C:\Program Files (x86)\MentorMA\flosuite_v13\flotherm\bin\flotherm.exe",
        # 尝试 PATH 中的 flotherm
        "flotherm",
        "flotherm.exe",
    ]

    for path in possible_paths:
        if os.path.exists(path):
            return path

    return None


def apply_config_to_ecxml(template_path: str, config: Dict[str, Any], output_path: str) -> bool:
    """
    将配置应用到 ECXML 模板

    支持的 Excel 列名格式:
        - "CPU"                        → 自动识别（功耗/温度）
        - "CPU.powerDissipation"       → 设置功耗
        - "Heatsink.Material.density"  → 多层路径
        - "Fan@flowRate"               → 设置属性
        - "PCB.Size@width"             → 子元素属性

    Args:
        template_path: 模板 ECXML 文件路径
        config: 配置字典
        output_path: 输出文件路径

    Returns:
        是否成功
    """
    # 复制模板
    shutil.copy(template_path, output_path)

    # 创建解析器并修改
    parser = ECXMLParser(output_path)

    modified_count = 0

    for key, value in config.items():
        if key.startswith('_') or key.lower() == 'config_name':
            continue

        if value is None:
            continue

        # 尝试转换为数值
        try:
            if isinstance(value, str):
                value = float(value)
            elif not isinstance(value, (int, float)):
                continue
        except (ValueError, TypeError):
            continue

        # 使用路径定位设置值（支持多种格式）
        if parser.set_value_by_path(key, value):
            modified_count += 1
        else:
            print(f"    ⚠ 未找到参数: {key}")

    # 保存修改
    parser.save(output_path)

    return modified_count > 0


def solve_ecxml(flotherm_exe: str, ecxml_path: str, output_pack_path: str,
                output_html_path: str, index: int, total: int) -> tuple:
    """
    求解单个 ECXML 文件

    Args:
        flotherm_exe: FloTHERM 可执行文件路径
        ecxml_path: 输入的 ECXML 文件路径
        output_pack_path: 输出的 PACK 文件路径
        output_html_path: 输出的 HTML 报告路径
        index: 当前索引（从1开始）
        total: 总文件数

    Returns:
        (success, elapsed_time, message)
    """
    print(f"\n{'='*60}")
    print(f"  [{index}/{total}] 正在求解: {Path(ecxml_path).name}")
    print(f"{'='*60}")
    print(f"  输入: {ecxml_path}")
    print(f"  输出: {output_pack_path}")
    print(f"  开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"  (命令行会等待求解完成，请勿关闭)\n")

    start_time = time.time()

    # 构建命令
    cmd = [
        flotherm_exe,
        "-b",
        str(ecxml_path),
        "-z",
        str(output_pack_path),
        "-r",
        str(output_html_path)
    ]

    try:
        # 运行 FloTHERM
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
        )

        elapsed_time = time.time() - start_time

        if result.returncode == 0:
            # 检查输出文件是否存在
            if os.path.exists(output_pack_path):
                file_size = os.path.getsize(output_pack_path) / (1024 * 1024)  # MB
                print(f"\n  ✅ 求解完成!")
                print(f"     耗时: {elapsed_time:.1f} 秒")
                print(f"     文件大小: {file_size:.2f} MB")
                return (True, elapsed_time, "成功")
            else:
                print(f"\n  ⚠️ 命令执行成功但未找到输出文件")
                return (False, elapsed_time, "输出文件不存在")
        else:
            print(f"  ❌ 求解失败!")
            print(f"     返回码: {result.returncode}")
            if result.stderr:
                print(f"     错误信息: {result.stderr[:500]}")
            return (False, elapsed_time, f"返回码: {result.returncode}")

    except subprocess.TimeoutExpired:
        elapsed_time = time.time() - start_time
        print(f"\n  ❌ 超时!")
        return (False, elapsed_time, "超时")
    except Exception as e:
        elapsed_time = time.time() - start_time
        print(f"\n  ❌ 异常: {e}")
        return (False, elapsed_time, str(e))


def generate_summary_report(output_folder: Path, configs: List[Dict],
                           results: List[Dict], template_name: str):
    """
    生成汇总报告

    Args:
        output_folder: 输出文件夹
        configs: 配置列表
        results: 结果列表
        template_name: 模板文件名
    """
    # 文本报告
    report_path = output_folder / "batch_report.txt"
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("Excel 多配置批量仿真报告\n")
        f.write(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"模板文件: {template_name}\n")
        f.write(f"{'='*60}\n\n")
        f.write(f"总配置数: {len(results)}\n")
        success_count = sum(1 for r in results if r["success"])
        f.write(f"成功: {success_count}\n")
        f.write(f"失败: {len(results) - success_count}\n\n")

        f.write("详细结果:\n")
        f.write("-" * 60 + "\n")

        for r in results:
            status = "成功" if r["success"] else "失败"
            f.write(f"\n[{status}] {r['config_name']}\n")
            f.write(f"  ECXML: {r['ecxml_path']}\n")
            f.write(f"  PACK: {r['pack_path']}\n")
            if r.get('html_path'):
                f.write(f"  报告: {r['html_path']}\n")
            f.write(f"  耗时: {r['elapsed']:.1f}s\n")
            f.write(f"  信息: {r['message']}\n")

            # 写入配置参数
            config = r.get('config', {})
            f.write(f"  配置参数:\n")
            for key, val in config.items():
                if not key.startswith('_') and key.lower() != 'config_name':
                    f.write(f"    {key}: {val}\n")

    print(f"\n📄 报告已保存: {report_path}")

    # 如果有 pandas，生成 Excel 汇总
    if HAS_PANDAS:
        summary_path = output_folder / "summary.xlsx"
        summary_data = []
        for r in results:
            row = {
                'config_name': r['config_name'],
                'status': '成功' if r['success'] else '失败',
                'elapsed_s': r['elapsed'],
                'ecxml': Path(r['ecxml_path']).name if r.get('ecxml_path') else '',
                'pack': Path(r['pack_path']).name if r.get('pack_path') else '',
                'message': r['message']
            }
            # 添加配置参数
            config = r.get('config', {})
            for key, val in config.items():
                if not key.startswith('_') and key.lower() != 'config_name':
                    row[key] = val
            summary_data.append(row)

        df = pd.DataFrame(summary_data)
        df.to_excel(summary_path, index=False)
        print(f"📊 Excel 汇总: {summary_path}")


def main():
    parser = argparse.ArgumentParser(
        description="Excel 多配置批量仿真工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Excel 格式示例:
    | config_name | U1_CPU | U2_GPU | Ambient |
    |-------------|--------|--------|---------|
    | case1       | 10     | 5      | 25      |
    | case2       | 15     | 8      | 35      |

示例命令:
    python excel_batch_simulation.py template.ecxml config.xlsx -o ./output
    python excel_batch_simulation.py template.ecxml config.xlsx -o ./output --no-solve
    python excel_batch_simulation.py template.ecxml config.xlsx -o ./output --sheet "Sheet2"
        """
    )

    parser.add_argument(
        "template",
        help="ECXML 模板文件路径"
    )

    parser.add_argument(
        "excel",
        help="Excel 配置文件路径"
    )

    parser.add_argument(
        "-o", "--output",
        required=True,
        help="输出文件夹路径"
    )

    parser.add_argument(
        "--sheet",
        help="Excel Sheet 名称（默认使用第一个 sheet）"
    )

    parser.add_argument(
        "--flotherm",
        help="FloTHERM 可执行文件路径（可选，自动检测）"
    )

    parser.add_argument(
        "--no-solve",
        action="store_true",
        help="仅生成 ECXML 文件，不调用 FloTHERM 求解"
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="仅显示将要处理的配置，不实际执行"
    )

    args = parser.parse_args()

    # 打印标题
    print("""
╔════════════════════════════════════════════════════════════╗
║          Excel 多配置批量仿真工具 v1.0                      ║
║                                                            ║
║  流程: Excel配置 → 修改ECXML → 批量求解                    ║
╚════════════════════════════════════════════════════════════╝
""")

    # 检查模板文件
    if not os.path.exists(args.template):
        print(f"❌ 错误: 模板文件不存在: {args.template}")
        sys.exit(1)

    print(f"✅ 模板文件: {args.template}")

    # 检查 Excel 文件
    if not os.path.exists(args.excel):
        print(f"❌ 错误: Excel 文件不存在: {args.excel}")
        sys.exit(1)

    print(f"✅ Excel 文件: {args.excel}")

    # 读取 Excel 配置
    print(f"\n📖 读取 Excel 配置...")
    try:
        reader = ExcelConfigReader(args.excel, args.sheet)
        configs = reader.read()
    except Exception as e:
        print(f"❌ 读取 Excel 失败: {e}")
        sys.exit(1)

    if not configs:
        print("❌ 错误: Excel 中没有找到配置数据")
        sys.exit(1)

    print(f"✅ 找到 {len(configs)} 个配置")

    # 显示配置预览
    print(f"\n📋 配置预览:")
    for i, config in enumerate(configs[:5], 1):  # 最多显示5个
        config_name = config.get('config_name', config.get(list(config.keys())[1] if len(config) > 1 else f"config_{i}"))
        params = [f"{k}={v}" for k, v in list(config.items())[:4] if not k.startswith('_')]
        print(f"   {i}. {config_name}: {', '.join(params)}")
    if len(configs) > 5:
        print(f"   ... 还有 {len(configs) - 5} 个配置")

    # 如果是 dry-run 模式，到此结束
    if args.dry_run:
        print("\n🔍 Dry-run 模式，不执行操作")
        sys.exit(0)

    # 创建输出文件夹（带时间戳的子文件夹）
    base_output = Path(args.output)
    batch_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_folder = base_output / f"batch_{batch_timestamp}"
    output_folder.mkdir(parents=True, exist_ok=True)
    print(f"\n✅ 输出文件夹: {output_folder}")

    # 查找 FloTHERM（如果需要求解）
    flotherm_exe = None
    if not args.no_solve:
        if args.flotherm:
            flotherm_exe = args.flotherm
            if not os.path.exists(flotherm_exe):
                print(f"❌ 错误: 指定的 FloTHERM 不存在: {flotherm_exe}")
                sys.exit(1)
        else:
            flotherm_exe = find_flotherm_executable()
            if not flotherm_exe:
                print("❌ 错误: 未找到 FloTHERM，请使用 --flotherm 参数指定路径")
                sys.exit(1)

        print(f"✅ FloTHERM: {flotherm_exe}")

    # 开始处理
    print(f"\n{'='*60}")
    print(f"  开始生成 ECXML 文件")
    print(f"{'='*60}")

    results = []
    total_start_time = time.time()

    for i, config in enumerate(configs, 1):
        # 获取配置名称
        config_name = config.get('config_name',
                     config.get(list(config.keys())[1] if len(config) > 1 else f"config_{i}"))

        # 生成输出文件名
        ecxml_path = output_folder / f"{config_name}.ecxml"
        pack_path = output_folder / f"{config_name}.pack"
        html_path = output_folder / f"{config_name}_report.html"

        print(f"\n[{i}/{len(configs)}] 生成: {config_name}")

        # 应用配置到模板
        try:
            success = apply_config_to_ecxml(args.template, config, str(ecxml_path))
            if not success:
                print(f"    ⚠️ 没有修改任何参数")
        except Exception as e:
            print(f"    ❌ 修改失败: {e}")
            results.append({
                'config_name': config_name,
                'config': config,
                'ecxml_path': str(ecxml_path),
                'pack_path': '',
                'html_path': '',
                'success': False,
                'elapsed': 0,
                'message': f'修改失败: {e}'
            })
            continue

        # 求解（如果需要）
        if not args.no_solve and flotherm_exe:
            solve_success, elapsed, message = solve_ecxml(
                flotherm_exe,
                str(ecxml_path),
                str(pack_path),
                str(html_path),
                i,
                len(configs)
            )

            results.append({
                'config_name': config_name,
                'config': config,
                'ecxml_path': str(ecxml_path),
                'pack_path': str(pack_path) if solve_success else '',
                'html_path': str(html_path) if solve_success else '',
                'success': solve_success,
                'elapsed': elapsed,
                'message': message
            })
        else:
            # 仅生成模式
            results.append({
                'config_name': config_name,
                'config': config,
                'ecxml_path': str(ecxml_path),
                'pack_path': '',
                'html_path': '',
                'success': True,
                'elapsed': 0,
                'message': '仅生成 ECXML'
            })

    # 打印总结
    total_elapsed = time.time() - total_start_time
    success_count = sum(1 for r in results if r["success"])

    print(f"\n{'='*60}")
    print(f"  处理完成")
    print(f"{'='*60}")
    print(f"  总配置数: {len(results)}")
    print(f"  成功: {success_count}")
    print(f"  失败: {len(results) - success_count}")
    print(f"  总耗时: {total_elapsed:.1f} 秒")

    # 生成汇总报告
    generate_summary_report(output_folder, configs, results, Path(args.template).name)

    # 返回码
    sys.exit(0 if success_count == len(results) else 1)


if __name__ == "__main__":
    main()
