#!/usr/bin/env python3
"""
FloTHERM 批量仿真命令行工具

Usage:
    # 从配置生成脚本
    python batch_sim.py generate config.json -o ./scripts

    # 从配置生成并执行
    python batch_sim.py run config.json --pack model.pack

    # 预览生成的脚本
    python batch_sim.py generate config.json --dry-run

    # 提取结果
    python batch_sim.py extract solved.pack -o results.json
"""

import argparse
import sys
from pathlib import Path


def cmd_generate(args):
    """生成 FloSCRIPT 脚本"""
    from floscript.batch_generator import BatchSimulationGenerator

    config_path = Path(args.config)
    if not config_path.exists():
        print(f"[ERROR] Config file not found: {config_path}")
        return 1

    output_dir = Path(args.output) if args.output else Path("./scripts")

    generator = BatchSimulationGenerator.from_json(config_path)
    generator.output_dir = output_dir

    if args.dry_run:
        print("[DRY-RUN] Would generate scripts to:", output_dir)
        print("[DRY-RUN] Config:", config_path)
        return 0

    scripts = generator.generate_scripts()
    print(f"[OK] Generated {len(scripts)} script(s) to {output_dir}")
    for script in scripts:
        print(f"  - {script.name}")

    return 0


def cmd_run(args):
    """生成并执行脚本"""
    from floscript.batch_generator import BatchSimulationGenerator
    from floscript.executor import FlothermExecutor

    config_path = Path(args.config)
    if not config_path.exists():
        print(f"[ERROR] Config file not found: {config_path}")
        return 1

    output_dir = Path(args.output) if args.output else Path("./scripts")

    # 生成脚本
    generator = BatchSimulationGenerator.from_json(config_path)
    generator.output_dir = output_dir
    scripts = generator.generate_scripts()

    print(f"[OK] Generated {len(scripts)} script(s)")

    if args.dry_run:
        print("[DRY-RUN] Would execute scripts with FloTHERM")
        return 0

    # 执行脚本
    executor = FlothermExecutor()
    detected = executor.auto_detect_path()
    if not detected:
        print("[ERROR] FloTHERM not found. Please install or set path.")
        return 1

    print(f"[INFO] Using FloTHERM: {executor.flotherm_path}")

    success_count = 0
    for script in scripts:
        print(f"\n[INFO] Executing: {script.name}")
        success, elapsed, msg = executor.execute(script, timeout=args.timeout)
        if success:
            print(f"  [OK] Completed in {elapsed:.1f}s")
            success_count += 1
        else:
            print(f"  [ERROR] {msg}")

    print(f"\n[SUMMARY] {success_count}/{len(scripts)} succeeded")
    return 0 if success_count == len(scripts) else 1


def cmd_extract(args):
    """提取结果"""
    from results.extractor import ResultExtractor

    pack_path = Path(args.pack)
    if not pack_path.exists():
        print(f"[ERROR] Pack file not found: {pack_path}")
        return 1

    extractor = ResultExtractor(pack_path)

    if args.format == "json":
        output_path = Path(args.output) if args.output else Path("results.json")
        extractor.export_json(output_path)
    else:
        output_path = Path(args.output) if args.output else Path("results.csv")
        extractor.export_csv(output_path)

    print(f"[OK] Results exported to {output_path}")
    return 0


def cmd_create_floxml(args):
    """创建 FloXML 项目"""
    from floxml.creator import FloXMLCreator

    creator = FloXMLCreator()
    creator.create_project(args.name or "NewProject")

    # 添加基本材料
    creator.add_material("Air", conductivity=0.026, density=1.2, specific_heat=1005)
    creator.add_material("Aluminum", conductivity=205, density=2700, specific_heat=900)

    # 设置默认求解域
    creator.set_solution_domain(0, 0, 0, 0.5, 0.5, 0.5)

    output_path = Path(args.output) if args.output else Path("project.xml")
    creator.save(output_path)

    print(f"[OK] FloXML project created: {output_path}")
    return 0


def main():
    parser = argparse.ArgumentParser(
        description="FloTHERM 批量仿真工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 生成脚本
  python batch_sim.py generate config.json -o ./scripts

  # 生成并执行
  python batch_sim.py run config.json

  # 提取结果
  python batch_sim.py extract solved.pack -o results.json

  # 创建 FloXML 项目
  python batch_sim.py create-floxml -o project.xml
        """
    )

    subparsers = parser.add_subparsers(dest="command", help="命令")

    # generate 命令
    gen_parser = subparsers.add_parser("generate", help="生成 FloSCRIPT 脚本")
    gen_parser.add_argument("config", help="配置文件 (JSON)")
    gen_parser.add_argument("-o", "--output", help="输出目录")
    gen_parser.add_argument("--dry-run", action="store_true", help="预览不执行")

    # run 命令
    run_parser = subparsers.add_parser("run", help="生成并执行脚本")
    run_parser.add_argument("config", help="配置文件 (JSON)")
    run_parser.add_argument("-o", "--output", help="脚本输出目录")
    run_parser.add_argument("--dry-run", action="store_true", help="预览不执行")
    run_parser.add_argument("--timeout", type=int, default=3600, help="超时时间(秒)")

    # extract 命令
    ext_parser = subparsers.add_parser("extract", help="提取结果")
    ext_parser.add_argument("pack", help="Pack 文件")
    ext_parser.add_argument("-o", "--output", help="输出文件")
    ext_parser.add_argument("--format", choices=["json", "csv"], default="json", help="输出格式")

    # create-floxml 命令
    floxml_parser = subparsers.add_parser("create-floxml", help="创建 FloXML 项目")
    floxml_parser.add_argument("-n", "--name", help="项目名称")
    floxml_parser.add_argument("-o", "--output", help="输出文件")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 0

    if args.command == "generate":
        return cmd_generate(args)
    elif args.command == "run":
        return cmd_run(args)
    elif args.command == "extract":
        return cmd_extract(args)
    elif args.command == "create-floxml":
        return cmd_create_floxml(args)

    return 0


if __name__ == "__main__":
    sys.exit(main())
