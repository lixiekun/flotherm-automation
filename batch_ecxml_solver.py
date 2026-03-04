#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FloTHERM ECXML 批量求解器

使用方法:
    python batch_ecxml_solver.py input_folder -o output_folder

功能:
    - 扫描输入文件夹中的所有 ECXML 文件
    - 按顺序求解每个 ECXML 文件
    - 输出 PACK 文件到输出文件夹（带时间戳命名）
    - 显示求解进度和状态
"""

import os
import sys
import glob
import subprocess
import argparse
import time
import threading
from datetime import datetime
from pathlib import Path


class LoadingAnimation:
    """加载动画类"""

    def __init__(self):
        self.running = False
        self.thread = None
        self.start_time = None
        # 动画帧：旋转光标
        self.frames = ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏']

    def _animate(self):
        """动画循环"""
        idx = 0
        while self.running:
            elapsed = time.time() - self.start_time
            frame = self.frames[idx % len(self.frames)]
            # 打印动画帧，显示已用时间
            sys.stdout.write(f"\r  {frame} 求解中... {elapsed:.0f}秒 ")
            sys.stdout.flush()
            time.sleep(0.1)
            idx += 1
        # 清除动画行
        sys.stdout.write("\r" + " " * 40 + "\r")
        sys.stdout.flush()

    def start(self):
        """开始动画"""
        self.running = True
        self.start_time = time.time()
        self.thread = threading.Thread(target=self._animate)
        self.thread.daemon = True
        self.thread.start()

    def stop(self):
        """停止动画"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=0.5)


def find_ecxml_files(input_folder):
    """查找文件夹中的所有 ECXML 文件"""
    input_path = Path(input_folder)

    if not input_path.exists():
        print(f"❌ 错误: 输入文件夹不存在: {input_folder}")
        return []

    # 查找所有 ecxml 文件（不区分大小写）
    ecxml_files = []
    for pattern in ["*.ecxml", "*.ECXML", "*.Ecxml"]:
        ecxml_files.extend(input_path.glob(pattern))

    # 去重并排序
    ecxml_files = sorted(set(ecxml_files), key=lambda x: x.name)

    return ecxml_files


def find_flotherm_executable():
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

    # 尝试在 PATH 中查找
    try:
        result = subprocess.run(
            ["where", "flotherm"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            return result.stdout.strip().split('\n')[0]
    except:
        pass

    return None


def solve_ecxml(flotherm_exe, ecxml_path, output_pack_path, index, total):
    """
    求解单个 ECXML 文件

    参数:
        flotherm_exe: FloTHERM 可执行文件路径
        ecxml_path: 输入的 ECXML 文件路径
        output_pack_path: 输出的 PACK 文件路径
        index: 当前索引（从1开始）
        total: 总文件数

    返回:
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
        str(output_pack_path)
    ]

    # 启动加载动画
    animation = LoadingAnimation()

    try:
        animation.start()

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
                print(f"  ✅ 求解完成!")
                print(f"     耗时: {elapsed_time:.1f} 秒")
                print(f"     文件大小: {file_size:.2f} MB")
                return (True, elapsed_time, "成功")
            else:
                print(f"  ⚠️ 命令执行成功但未找到输出文件")
                return (False, elapsed_time, "输出文件不存在")
        else:
            print(f"  ❌ 求解失败!")
            print(f"     返回码: {result.returncode}")
            if result.stderr:
                print(f"     错误信息: {result.stderr[:500]}")
            return (False, elapsed_time, f"返回码: {result.returncode}")

    except subprocess.TimeoutExpired:
        elapsed_time = time.time() - start_time
        print(f"  ❌ 超时!")
        return (False, elapsed_time, "超时")
    except Exception as e:
        elapsed_time = time.time() - start_time
        print(f"  ❌ 异常: {e}")
        return (False, elapsed_time, str(e))
    finally:
        # 确保动画停止
        animation.stop()


def main():
    parser = argparse.ArgumentParser(
        description="FloTHERM ECXML 批量求解器",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
    python batch_ecxml_solver.py ./models -o ./results
    python batch_ecxml_solver.py C:\\input -o C:\\output --flotherm "C:\\Program Files\\Siemens\\SimcenterFlotherm\\2020.2\\bin\\flotherm.exe"
        """
    )

    parser.add_argument(
        "input_folder",
        help="输入文件夹路径（包含 ECXML 文件）"
    )

    parser.add_argument(
        "-o", "--output",
        required=True,
        help="输出文件夹路径（保存 PACK 文件）"
    )

    parser.add_argument(
        "--flotherm",
        help="FloTHERM 可执行文件路径（可选，自动检测）"
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="仅显示将要处理的文件，不实际执行"
    )

    args = parser.parse_args()

    # 打印标题
    print("""
╔════════════════════════════════════════════════════════════╗
║          FloTHERM ECXML 批量求解器 v1.0                    ║
║                                                            ║
║  命令格式: flotherm -b model.ecxml -z output.pack         ║
╚════════════════════════════════════════════════════════════╝
""")

    # 查找 FloTHERM
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

    # 查找 ECXML 文件
    ecxml_files = find_ecxml_files(args.input_folder)

    if not ecxml_files:
        print(f"❌ 错误: 在 {args.input_folder} 中未找到 ECXML 文件")
        sys.exit(1)

    print(f"✅ 找到 {len(ecxml_files)} 个 ECXML 文件")

    # 创建输出文件夹（带时间戳的子文件夹）
    base_output = Path(args.output)
    batch_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_folder = base_output / f"batch_{batch_timestamp}"
    output_folder.mkdir(parents=True, exist_ok=True)
    print(f"✅ 输出文件夹: {output_folder}")

    # 显示文件列表
    print(f"\n📁 待处理文件列表:")
    for i, f in enumerate(ecxml_files, 1):
        print(f"   {i}. {f.name}")

    # 如果是 dry-run 模式，到此结束
    if args.dry_run:
        print("\n🔍 Dry-run 模式，不执行求解")
        sys.exit(0)

    # 开始批量处理
    print(f"\n{'='*60}")
    print(f"  开始批量求解")
    print(f"{'='*60}")

    results = []
    total_start_time = time.time()

    for i, ecxml_path in enumerate(ecxml_files, 1):
        # 生成输出文件名（不带时间戳，因为文件夹已有时间戳）
        base_name = ecxml_path.stem  # 不含扩展名的文件名
        output_pack_name = f"{base_name}.pack"
        output_pack_path = output_folder / output_pack_name

        # 求解
        success, elapsed, message = solve_ecxml(
            flotherm_exe,
            ecxml_path,
            output_pack_path,
            i,
            len(ecxml_files)
        )

        results.append({
            "input": str(ecxml_path),
            "output": str(output_pack_path),
            "success": success,
            "elapsed": elapsed,
            "message": message
        })

    # 打印总结
    total_elapsed = time.time() - total_start_time
    success_count = sum(1 for r in results if r["success"])

    print(f"\n{'='*60}")
    print(f"  批量求解完成")
    print(f"{'='*60}")
    print(f"  总文件数: {len(results)}")
    print(f"  成功: {success_count}")
    print(f"  失败: {len(results) - success_count}")
    print(f"  总耗时: {total_elapsed:.1f} 秒")

    # 打印详细结果
    print(f"\n📊 详细结果:")
    print(f"  {'状态':<6} {'耗时':<10} {'文件名':<40}")
    print(f"  {'-'*56}")

    for r in results:
        status = "✅" if r["success"] else "❌"
        elapsed_str = f"{r['elapsed']:.1f}s"
        filename = Path(r["input"]).name
        print(f"  {status:<6} {elapsed_str:<10} {filename:<40}")

    # 保存报告
    report_path = output_folder / "batch_report.txt"
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("FloTHERM ECXML 批量求解报告\n")
        f.write(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"{'='*60}\n\n")
        f.write(f"总文件数: {len(results)}\n")
        f.write(f"成功: {success_count}\n")
        f.write(f"失败: {len(results) - success_count}\n")
        f.write(f"总耗时: {total_elapsed:.1f} 秒\n\n")
        f.write(f"详细结果:\n")
        f.write(f"{'-'*60}\n")

        for r in results:
            status = "成功" if r["success"] else "失败"
            f.write(f"\n[{status}] {Path(r['input']).name}\n")
            f.write(f"  输入: {r['input']}\n")
            f.write(f"  输出: {r['output']}\n")
            f.write(f"  耗时: {r['elapsed']:.1f}s\n")
            f.write(f"  信息: {r['message']}\n")

    print(f"\n📄 报告已保存: {report_path}")

    # 返回码
    sys.exit(0 if success_count == len(results) else 1)


if __name__ == "__main__":
    main()
