#!/usr/bin/env python3
"""
Pack Editor CLI - 命令行接口

Usage:
    python -m pack_editor extract model.pack -o ./extracted/
    python -m pack_editor info model.pack
    python -m pack_editor pack ./extracted/ -o new.pack
    python -m pack_editor edit model.pack --set-power "CPU=25.0" -o modified.pack
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import List, Optional

from .pack_manager import PackManager, PackManagerError
from .pack_inspector import PackInspector
from .group_binary import GroupBinaryHandler, GroupBinaryError, CalibrationRule


def _format_size(size: int) -> str:
    """格式化文件大小"""
    for unit in ["B", "KB", "MB", "GB"]:
        if size < 1024:
            return f"{size:.1f} {unit}"
        size /= 1024
    return f"{size:.1f} TB"


def _print_tree(inspector: PackInspector, show_size: bool = False) -> None:
    """打印目录树"""
    s = inspector.structure
    print(f"\n{s.root_prefix}/")

    # 按目录组织
    dirs = {}
    for entry in s.entries.values():
        parts = entry.name.split("/")
        dir_name = parts[0] if len(parts) > 1 else "."
        if dir_name not in dirs:
            dirs[dir_name] = []
        dirs[dir_name].append(entry)

    for dir_name in sorted(dirs.keys()):
        entries = sorted(dirs[dir_name], key=lambda e: e.name)
        print(f"├── {dir_name}/")

        for i, entry in enumerate(entries):
            is_last = (i == len(entries) - 1)
            prefix = "│   └── " if is_last else "│   ├── "
            name = "/".join(entry.name.split("/")[1:]) if "/" in entry.name else entry.name

            if show_size:
                size_str = _format_size(entry.size)
                print(f"{prefix}{name} ({size_str})")
            else:
                print(f"{prefix}{name}")


def _print_entries(inspector: PackInspector, pattern: str) -> None:
    """打印匹配的条目"""
    from fnmatch import fnmatch
    entries = [e for e in inspector.structure.entries.values() if fnmatch(e.name, pattern)]

    if not entries:
        print(f"No entries matching: {pattern}")
        return

    print(f"\nEntries matching '{pattern}':")
    print("-" * 60)

    for entry in sorted(entries, key=lambda e: e.name):
        size_str = _format_size(entry.size)
        print(f"  {entry.name:40} {size_str:>12}")

    print("-" * 60)
    print(f"Total: {len(entries)} entries")


def cmd_extract(args: argparse.Namespace) -> int:
    """解压 Pack 文件"""
    pack_path = Path(args.pack_file)

    if not pack_path.exists():
        print(f"Error: Pack file not found: {pack_path}", file=sys.stderr)
        return 1

    output_dir = args.output if args.output else None

    try:
        manager = PackManager(pack_path)
        result_dir = manager.extract(output_dir, overwrite=args.force)
        print(f"Extracted to: {result_dir}")
        return 0
    except PackManagerError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


def cmd_pack(args: argparse.Namespace) -> int:
    """打包目录为 Pack 文件"""
    dir_path = Path(args.directory)

    if not dir_path.exists():
        print(f"Error: Directory not found: {dir_path}", file=sys.stderr)
        return 1

    output_path = args.output if args.output else None

    try:
        manager = PackManager()
        manager.load_from_dir(dir_path)
        result_path = manager.pack(output_path)
        print(f"Packed to: {result_path}")
        return 0
    except PackManagerError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


def cmd_info(args: argparse.Namespace) -> int:
    """显示 Pack 文件信息"""
    pack_path = Path(args.pack_file)

    if not pack_path.exists():
        print(f"Error: Pack file not found: {pack_path}", file=sys.stderr)
        return 1

    try:
        inspector = PackInspector(pack_path)

        if args.tree:
            _print_tree(inspector, show_size=args.size)
        elif args.entries:
            _print_entries(inspector, args.entries)
        else:
            inspector.print_info()

        return 0
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


def cmd_edit(args: argparse.Namespace) -> int:
    """编辑 Pack 文件"""
    pack_path = Path(args.pack_file)

    if not pack_path.exists():
        print(f"Error: Pack file not found: {pack_path}", file=sys.stderr)
        return 1

    output_path = Path(args.output) if args.output else pack_path.with_name(
        f"{pack_path.stem}_modified.pack"
    )

    try:
        manager = PackManager(pack_path)

        # 解压到临时目录
        import tempfile
        with tempfile.TemporaryDirectory() as temp_dir:
            manager.extract(temp_dir, overwrite=True)

            # 应用编辑
            changes_made = False

            # 环境温度
            if args.ambient_temp is not None:
                manager.model.set_ambient_temperature(args.ambient_temp)
                changes_made = True
                print(f"Set ambient temperature: {args.ambient_temp} K")

            # 重力方向
            if args.gravity:
                manager.model.set_gravity(args.gravity)
                changes_made = True
                print(f"Set gravity direction: {args.gravity}")

            # 功耗设置
            if args.set_power:
                for power_spec in args.set_power:
                    name, value = power_spec.split("=")
                    manager.geometry.set_cuboid_power(name, float(value))
                    changes_made = True
                    print(f"Set power: {name} = {value} W")

            # 材质设置
            if args.set_material:
                for mat_spec in args.set_material:
                    name, material = mat_spec.split("=")
                    manager.geometry.set_cuboid_material(name, material)
                    changes_made = True
                    print(f"Set material: {name} = {material}")

            # 网格配置
            if args.grid_config:
                # Phase 2 功能
                print(f"Grid config: {args.grid_config} (not yet implemented)")

            if changes_made:
                manager.save()

            # 打包
            result_path = manager.pack(output_path)
            print(f"Saved to: {result_path}")

        return 0
    except PackManagerError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


def cmd_list(args: argparse.Namespace) -> int:
    """列出 Pack 文件内容"""
    pack_path = Path(args.pack_file)

    if not pack_path.exists():
        print(f"Error: Pack file not found: {pack_path}", file=sys.stderr)
        return 1

    try:
        inspector = PackInspector(pack_path)

        pattern = args.pattern if args.pattern else "*"
        _print_entries(inspector, pattern)

        return 0
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


def cmd_calibrate(args: argparse.Namespace) -> int:
    """创建校准规则"""
    baseline_pack = Path(args.baseline_pack)
    calibrated_pack = Path(args.calibrated_pack)
    output_path = Path(args.output)

    if not baseline_pack.exists():
        print(f"Error: Baseline pack not found: {baseline_pack}", file=sys.stderr)
        return 1

    if not calibrated_pack.exists():
        print(f"Error: Calibrated pack not found: {calibrated_pack}", file=sys.stderr)
        return 1

    try:
        handler = GroupBinaryHandler()
        rule = handler.calibrate(
            baseline_pack=baseline_pack,
            calibrated_pack=calibrated_pack,
            component_name=args.component_name,
            baseline_power=float(args.baseline_power),
            calibrated_power=float(args.calibrated_power),
        )
        rule.save(output_path)

        print(f"[OK] Wrote calibration rule: {output_path}")
        print(f"[OK] Component: {rule.component_name}")
        print(f"[OK] FloTHERM version: {rule.flotherm_version}")

        for entry in rule.entries:
            offsets = ", ".join(f"{o.offset}:{o.encoding}" for o in entry.offsets)
            print(f"[OK] {entry.entry_suffix} -> {offsets}")

        return 0
    except GroupBinaryError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


def cmd_apply(args: argparse.Namespace) -> int:
    """应用校准规则"""
    input_pack = Path(args.input_pack)
    output_pack = Path(args.output)

    if not input_pack.exists():
        print(f"Error: Input pack not found: {input_pack}", file=sys.stderr)
        return 1

    try:
        handler = GroupBinaryHandler()
        rule = CalibrationRule.load(args.rule)
        result = handler.apply_rule(
            input_pack=input_pack,
            rule=rule,
            new_power=args.new_power,
            output_pack=output_pack,
        )

        print(f"[OK] Wrote patched pack: {result}")
        return 0
    except GroupBinaryError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


def cmd_inspect(args: argparse.Namespace) -> int:
    """检查 Pack 文件二进制内容"""
    pack_path = Path(args.pack_file)

    if not pack_path.exists():
        print(f"Error: Pack file not found: {pack_path}", file=sys.stderr)
        return 1

    try:
        inspector = PackInspector(pack_path)

        print(f"\nPack: {pack_path}")
        inspector.print_info()

        if args.strings:
            print("\nGroup File Analysis:")
            inspector.print_group_analysis()

        return 0
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


def cmd_batch(args: argparse.Namespace) -> int:
    """批量处理 Pack 文件"""
    from .batch import ExcelBatchDriver

    input_pack = Path(args.input_pack)
    cases_file = Path(args.cases)
    output_dir = Path(args.output_dir)

    if not input_pack.exists():
        print(f"Error: Input pack not found: {input_pack}", file=sys.stderr)
        return 1

    if not cases_file.exists():
        print(f"Error: Cases file not found: {cases_file}", file=sys.stderr)
        return 1

    try:
        # 构建校准规则映射
        calibration_rules = {}
        if args.rule:
            for rule_spec in args.rule:
                if "=" in rule_spec:
                    component, rule_path = rule_spec.split("=", 1)
                    calibration_rules[component] = rule_path

        driver = ExcelBatchDriver(
            template_pack=input_pack,
            config_file=cases_file,
            calibration_rules=calibration_rules,
        )

        cases = driver.get_cases()
        print(f"[OK] Loaded {len(cases)} cases from {cases_file}")

        # 进度回调
        def progress_callback(current: int, total: int, status: str) -> None:
            print(f"[{current}/{total}] {status}")

        manifest = driver.run(
            output_dir=output_dir,
            parallel=args.parallel,
        )

        success_count = sum(1 for c in manifest["cases"] if c["success"])
        total_count = len(manifest["cases"])

        print(f"\n[OK] Batch processing complete: {success_count}/{total_count} cases successful")
        print(f"[OK] Results saved to: {output_dir}")
        print(f"[OK] Manifest: {output_dir}/run_manifest.json")

        return 0 if success_count == total_count else 1

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1


def cmd_template(args: argparse.Namespace) -> int:
    """创建配置模板文件"""
    from .batch import ExcelBatchDriver

    output_path = Path(args.output)

    try:
        if args.format == "csv":
            result = ExcelBatchDriver.create_template_csv(output_path)
        else:
            result = ExcelBatchDriver.create_template_excel(output_path)

        print(f"[OK] Created template: {result}")
        return 0
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


def main(argv: Optional[List[str]] = None) -> int:
    """CLI 主入口"""
    parser = argparse.ArgumentParser(
        prog="pack-editor",
        description="FloTHERM Pack File Editor",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  pack-editor extract model.pack -o ./extracted/
  pack-editor info model.pack --tree
  pack-editor pack ./extracted/ -o new.pack
  pack-editor edit model.pack --set-power "CPU=25.0" -o modified.pack

  # Calibration workflow (Phase 3)
  pack-editor calibrate baseline.pack calibrated.pack --component-name CPU \
      --baseline-power 10 --calibrated-power 20 -o rule.json
  pack-editor apply baseline.pack --rule rule.json --new-power 15 -o modified.pack
  pack-editor inspect model.pack --strings

  # Batch processing (Phase 4)
  pack-editor template -o cases.xlsx
  pack-editor batch template.pack --cases cases.xlsx -o ./results/
  pack-editor batch template.pack --cases cases.xlsx --rule CPU=rule.json -o ./results/
        """,
    )

    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # extract 命令
    extract_parser = subparsers.add_parser("extract", help="Extract pack file")
    extract_parser.add_argument("pack_file", help="Pack file to extract")
    extract_parser.add_argument("-o", "--output", help="Output directory")
    extract_parser.add_argument("-f", "--force", action="store_true",
                                help="Overwrite existing directory")
    extract_parser.set_defaults(func=cmd_extract)

    # pack 命令
    pack_parser = subparsers.add_parser("pack", help="Pack directory to .pack file")
    pack_parser.add_argument("directory", help="Directory to pack")
    pack_parser.add_argument("-o", "--output", help="Output pack file")
    pack_parser.set_defaults(func=cmd_pack)

    # info 命令
    info_parser = subparsers.add_parser("info", help="Show pack file information")
    info_parser.add_argument("pack_file", help="Pack file to inspect")
    info_parser.add_argument("--tree", action="store_true", help="Show directory tree")
    info_parser.add_argument("--entries", metavar="PATTERN", help="List entries matching pattern")
    info_parser.add_argument("--size", action="store_true", help="Show file sizes")
    info_parser.set_defaults(func=cmd_info)

    # list 命令
    list_parser = subparsers.add_parser("list", help="List pack file contents")
    list_parser.add_argument("pack_file", help="Pack file to list")
    list_parser.add_argument("pattern", nargs="?", help="File pattern (e.g., *.xml)")
    list_parser.set_defaults(func=cmd_list)

    # edit 命令 (Phase 2)
    edit_parser = subparsers.add_parser("edit", help="Edit pack file")
    edit_parser.add_argument("pack_file", help="Pack file to edit")
    edit_parser.add_argument("-o", "--output", help="Output pack file")
    edit_parser.add_argument("--ambient-temp", type=float, metavar="K",
                             help="Set ambient temperature (Kelvin)")
    edit_parser.add_argument("--gravity", choices=["pos_x", "neg_x", "pos_y", "neg_y", "pos_z", "neg_z"],
                             help="Set gravity direction")
    edit_parser.add_argument("--set-power", action="append", metavar="NAME=VALUE",
                             help="Set component power (e.g., CPU=25.0)")
    edit_parser.add_argument("--set-material", action="append", metavar="NAME=MATERIAL",
                             help="Set component material")
    edit_parser.add_argument("--grid-config", metavar="FILE",
                             help="Grid configuration Excel file")
    edit_parser.set_defaults(func=cmd_edit)

    # calibrate 命令 (Phase 3)
    calibrate_parser = subparsers.add_parser("calibrate", help="Create calibration rule")
    calibrate_parser.add_argument("baseline_pack", help="Baseline pack file")
    calibrate_parser.add_argument("calibrated_pack", help="Calibrated pack file")
    calibrate_parser.add_argument("--component-name", required=True, help="Component name")
    calibrate_parser.add_argument("--baseline-power", required=True, help="Baseline power value")
    calibrate_parser.add_argument("--calibrated-power", required=True, help="Calibrated power value")
    calibrate_parser.add_argument("-o", "--output", required=True, help="Output rule file (JSON)")
    calibrate_parser.set_defaults(func=cmd_calibrate)

    # apply 命令 (Phase 3)
    apply_parser = subparsers.add_parser("apply", help="Apply calibration rule")
    apply_parser.add_argument("input_pack", help="Input pack file")
    apply_parser.add_argument("--rule", required=True, help="Calibration rule file (JSON)")
    apply_parser.add_argument("--new-power", required=True, type=float, help="New power value")
    apply_parser.add_argument("-o", "--output", required=True, help="Output pack file")
    apply_parser.set_defaults(func=cmd_apply)

    # inspect 命令 (Phase 3)
    inspect_parser = subparsers.add_parser("inspect", help="Inspect pack binary content")
    inspect_parser.add_argument("pack_file", help="Pack file to inspect")
    inspect_parser.add_argument("--strings", action="store_true", help="Show group file strings")
    inspect_parser.set_defaults(func=cmd_inspect)

    # batch 命令 (Phase 4)
    batch_parser = subparsers.add_parser("batch", help="Batch process pack files")
    batch_parser.add_argument("input_pack", help="Template pack file")
    batch_parser.add_argument("--cases", required=True, help="Cases file (Excel or CSV)")
    batch_parser.add_argument("-o", "--output-dir", required=True, help="Output directory")
    batch_parser.add_argument("--rule", action="append", metavar="NAME=PATH",
                             help="Calibration rule file (e.g., CPU=rule.json)")
    batch_parser.add_argument("--parallel", type=int, default=1, help="Parallel workers")
    batch_parser.set_defaults(func=cmd_batch)

    # template 命令 (Phase 4)
    template_parser = subparsers.add_parser("template", help="Create config template")
    template_parser.add_argument("-o", "--output", required=True, help="Output file path")
    template_parser.add_argument("--format", choices=["csv", "xlsx"], default="xlsx",
                                help="Template format (default: xlsx)")
    template_parser.set_defaults(func=cmd_template)

    args = parser.parse_args(argv)

    if args.command is None:
        parser.print_help()
        return 0

    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
