#!/usr/bin/env python3
"""
FloTHERM 批量仿真自动化脚本
1. 读取模板 ecxml 文件
2. 根据参数配置生成多个仿真案例
3. 生成批处理脚本
"""

import os
import json
import shutil
from pathlib import Path
from datetime import datetime
from ecxml_editor import ECXMLParser, load_power_config


class BatchSimulationGenerator:
    """批量仿真生成器"""

    def __init__(self, template_path: str, output_dir: str):
        self.template_path = template_path
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # 复制模板到输出目录
        self.template_copy = self.output_dir / "template.ecxml"
        shutil.copy(template_path, self.template_copy)

    def generate_parametric_study(self, component_name: str,
                                   power_values: list,
                                   output_subdir: str = "parametric"):
        """
        生成参数化扫描案例

        Args:
            component_name: 器件名称
            power_values: 功耗值列表，如 [5, 10, 15, 20]
            output_subdir: 输出子目录名
        """
        study_dir = self.output_dir / output_subdir
        study_dir.mkdir(parents=True, exist_ok=True)

        cases = []

        for power in power_values:
            # 创建案例目录
            case_name = f"{component_name}_{power}W"
            case_dir = study_dir / case_name
            case_dir.mkdir(parents=True, exist_ok=True)

            # 加载并修改模板
            ecxml = ECXMLParser(str(self.template_copy))
            ecxml.set_power(component_name, power)

            # 保存案例文件
            case_file = case_dir / f"{case_name}.ecxml"
            ecxml.save(str(case_file))

            cases.append({
                "name": case_name,
                "path": str(case_file),
                "power": power
            })

            print(f"生成案例: {case_name}")

        # 生成案例索引
        index_file = study_dir / "cases.json"
        with open(index_file, 'w', encoding='utf-8') as f:
            json.dump({
                "component": component_name,
                "generated_at": datetime.now().isoformat(),
                "cases": cases
            }, f, indent=2, ensure_ascii=False)

        return cases

    def generate_multi_component_study(self, config_path: str,
                                        output_subdir: str = "multi"):
        """
        生成多器件变化案例

        config.json 格式:
        {
            "cases": [
                {
                    "name": "case1",
                    "powers": {"U1": 10, "U2": 20}
                },
                {
                    "name": "case2",
                    "powers": {"U1": 15, "U2": 25}
                }
            ]
        }
        """
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)

        study_dir = self.output_dir / output_subdir
        study_dir.mkdir(parents=True, exist_ok=True)

        cases = []

        for case_config in config.get('cases', []):
            case_name = case_config['name']
            case_dir = study_dir / case_name
            case_dir.mkdir(parents=True, exist_ok=True)

            # 加载并修改模板
            ecxml = ECXMLParser(str(self.template_copy))

            for comp_name, power in case_config.get('powers', {}).items():
                ecxml.set_power(comp_name, power)

            # 保存案例文件
            case_file = case_dir / f"{case_name}.ecxml"
            ecxml.save(str(case_file))

            cases.append({
                "name": case_name,
                "path": str(case_file),
                "powers": case_config.get('powers', {})
            })

            print(f"生成案例: {case_name}")

        return cases

    def generate_batch_script(self, cases: list, script_path: str,
                              flotherm_path: str = r"C:\Program Files\Siemens\SimcenterFlotherm\2410\bin\flotherm.exe"):
        """
        生成 Windows 批处理脚本
        """
        with open(script_path, 'w', encoding='utf-8') as f:
            f.write("@echo off\n")
            f.write("setlocal enabledelayedexpansion\n\n")
            f.write(f"set FLOTHERM={flotherm_path}\n")
            f.write(f"echo FloTHERM Batch Simulation\n")
            f.write(f"echo Generated: {datetime.now().strftime('%%Y-%%m-%%d %%H:%%M:%%S')}\n")
            f.write(f"echo Total cases: {len(cases)}\n\n")

            for i, case in enumerate(cases, 1):
                f.write(f"echo.\n")
                f.write(f"echo [{i}/{len(cases)}] Running: {case['name']}\n")
                f.write(f'"%FLOTHERM%" -batch "{case["path"]}" -nogui -solve -out "{case["path"]}.log"\n')
                f.write(f"if errorlevel 1 (\n")
                f.write(f"    echo ERROR: {case['name']} failed!\n")
                f.write(f") else (\n")
                f.write(f"    echo SUCCESS: {case['name']}\n")
                f.write(f")\n\n")

            f.write("echo.\n")
            f.write("echo All simulations completed!\n")
            f.write("pause\n")

        print(f"批处理脚本已生成: {script_path}")

    def generate_linux_script(self, cases: list, script_path: str,
                               flotherm_path: str = "/opt/Flotherm/bin/flotherm"):
        """
        生成 Linux Shell 脚本
        """
        with open(script_path, 'w', encoding='utf-8') as f:
            f.write("#!/bin/bash\n\n")
            f.write(f"# FloTHERM Batch Simulation\n")
            f.write(f"# Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"# Total cases: {len(cases)}\n\n")
            f.write(f"FLOTHERM={flotherm_path}\n\n")

            for i, case in enumerate(cases, 1):
                f.write(f"echo \"[{i}/{len(cases)}] Running: {case['name']}\"\n")
                f.write(f"$FLOTHERM -batch \"{case['path']}\" -nogui -solve > \"{case['path']}.log\" 2>&1\n")
                f.write(f"if [ $? -eq 0 ]; then\n")
                f.write(f"    echo \"SUCCESS: {case['name']}\"\n")
                f.write(f"else\n")
                f.write(f"    echo \"ERROR: {case['name']} failed!\"\n")
                f.write(f"fi\n\n")

            f.write("echo \"All simulations completed!\"\n")

        # 添加执行权限
        os.chmod(script_path, 0o755)
        print(f"Shell 脚本已生成: {script_path}")


def example_parametric_sweep():
    """示例：参数化扫描"""
    generator = BatchSimulationGenerator(
        template_path="template.ecxml",
        output_dir="./simulations"
    )

    # 生成功耗从 5W 到 25W 的扫描案例
    cases = generator.generate_parametric_study(
        component_name="U1_CPU",
        power_values=[5, 10, 15, 20, 25],
        output_subdir="cpu_power_sweep"
    )

    # 生成批处理脚本
    generator.generate_batch_script(
        cases,
        script_path="./simulations/cpu_power_sweep/run_all.bat"
    )


def example_multi_component():
    """示例：多器件变化"""
    # 先创建配置文件
    config = {
        "cases": [
            {
                "name": "baseline",
                "powers": {"U1_CPU": 15, "U2_GPU": 20}
            },
            {
                "name": "high_power",
                "powers": {"U1_CPU": 25, "U2_GPU": 35}
            },
            {
                "name": "low_power",
                "powers": {"U1_CPU": 10, "U2_GPU": 15}
            }
        ]
    }

    with open("multi_config.json", 'w') as f:
        json.dump(config, f, indent=2)

    generator = BatchSimulationGenerator(
        template_path="template.ecxml",
        output_dir="./simulations"
    )

    cases = generator.generate_multi_component_study(
        config_path="multi_config.json",
        output_subdir="multi_component"
    )

    generator.generate_batch_script(
        cases,
        script_path="./simulations/multi_component/run_all.bat"
    )


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='FloTHERM 批量仿真生成器')
    parser.add_argument('template', help='模板 ECXML 文件')
    parser.add_argument('-o', '--output', default='./simulations', help='输出目录')
    parser.add_argument('--component', help='参数扫描的器件名称')
    parser.add_argument('--powers', nargs='+', type=float, help='功耗值列表')
    parser.add_argument('--config', help='多器件配置文件 (JSON)')
    parser.add_argument('--os', choices=['windows', 'linux'], default='windows',
                       help='生成的脚本类型')

    args = parser.parse_args()

    generator = BatchSimulationGenerator(args.template, args.output)

    # 参数化扫描
    if args.component and args.powers:
        cases = generator.generate_parametric_study(
            component_name=args.component,
            power_values=args.powers
        )
    # 多器件配置
    elif args.config:
        cases = generator.generate_multi_component_study(args.config)
    else:
        print("请指定 --component 和 --powers，或 --config")
        exit(1)

    # 生成脚本
    if args.os == 'windows':
        generator.generate_batch_script(cases, f"{args.output}/run_all.bat")
    else:
        generator.generate_linux_script(cases, f"{args.output}/run_all.sh")
