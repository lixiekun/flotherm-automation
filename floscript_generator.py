#!/usr/bin/env python3
"""
FloSCRIPT 生成器

根据 Schema 和示例自动生成 FloSCRIPT XML 脚本。
支持修改 Pack 文件中的参数并求解。

基于 FloSCRIPT Schema v1.0 规范

使用方法:
    # 生成修改功率的脚本
    python floscript_generator.py modify-power model.pack U1_CPU 15.0 -o script.xml

    # 生成批量修改脚本（从 JSON 配置）
    python floscript_generator.py from-config config.json -o script.xml

    # 直接执行（生成并运行）
    python floscript_generator.py run model.pack --power U1_CPU=15.0 --solve
"""

import os
import sys
import json
import subprocess
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any


class FloScriptGenerator:
    """
    FloSCRIPT XML 生成器

    基于 FloSCRIPT Schema v1.0 生成符合规范的 XML 脚本
    """

    VERSION = "1.0"

    # 支持的几何节点类型 (来自 Schema)
    NODE_TYPES = [
        "assembly", "blockWithHoles", "compactComponent", "cuboid",
        "pcbComponent", "controller", "cooler", "cutout", "cylinder",
        "die", "enclosure", "edaBoard", "edaComponent", "fan",
        "fixedFlow", "heatPipe", "heatSink", "hole", "monitorPoint",
        "pcb", "perforatedPlate", "prism", "rack", "recirculation",
        "slopingBlock", "source", "tec", "tet", "volumeRegion"
    ]

    # 属性类型
    ATTRIBUTE_TYPES = [
        "ambient", "fluid", "gridConstraint", "material", "occupancy",
        "radiation", "resistance", "source", "surface", "surfaceExchange",
        "thermal", "transient"
    ]

    def __init__(self):
        self.commands: List[str] = []
        self.header_comments = [
            "FloSCRIPT 自动化脚本",
            f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "由 floscript_generator.py 生成"
        ]

    # ==================== 项目操作 ====================

    def load_project(self, pack_path: str) -> 'FloScriptGenerator':
        """加载项目文件"""
        pack_path = pack_path.replace("\\", "/")
        self._add_comment(f"加载项目: {pack_path}")
        self.commands.append(f'    <project_load file="{pack_path}"/>')
        return self

    def save_project(self) -> 'FloScriptGenerator':
        """保存项目"""
        self._add_comment("保存项目")
        self.commands.append("    <project_save/>")
        return self

    def save_project_as(self, output_path: str) -> 'FloScriptGenerator':
        """另存为"""
        output_path = output_path.replace("\\", "/")
        self._add_comment(f"另存为: {output_path}")
        self.commands.append(f'    <project_save_as file="{output_path}"/>')
        return self

    def close_project(self) -> 'FloScriptGenerator':
        """关闭项目"""
        self.commands.append("    <project_delete/>")
        return self

    # ==================== 查找/选择 ====================

    def find_by_name(self, name: str, select_mode: str = "all") -> 'FloScriptGenerator':
        """按名称查找几何对象"""
        self._add_comment(f"查找对象: {name}")
        self.commands.append(f'''    <find filter="false" match="all" select_mode="{select_mode}">
        <enum_query_constraint criteria_type="common" is_positive="true">
            <value property_name="name" value="{name}"/>
        </enum_query_constraint>
    </find>''')
        return self

    def find_by_type(self, node_type: str, select_mode: str = "all") -> 'FloScriptGenerator':
        """按类型查找几何对象"""
        self._add_comment(f"查找类型: {node_type}")
        self.commands.append(f'''    <find filter="false" match="all" select_mode="{select_mode}">
        <enum_query_constraint criteria_type="common" is_positive="true">
            <value property_name="geometryType" value="{node_type}"/>
        </enum_query_constraint>
    </find>''')
        return self

    def find_with_power(self, select_mode: str = "all") -> 'FloScriptGenerator':
        """查找有功率的组件"""
        self._add_comment("查找有功率的组件")
        self.commands.append(f'''    <find filter="false" match="all" select_mode="{select_mode}">
        <double_query_constraint criteria_type="common" comparison_operator="greaterThan">
            <value property_name="power" value="0"/>
        </double_query_constraint>
    </find>''')
        return self

    def clear_selection(self) -> 'FloScriptGenerator':
        """清除选择"""
        self.commands.append("    <clear_select_geometry/>")
        return self

    # ==================== 修改几何 ====================

    def modify_geometry(self, property_name: str, new_value: Any,
                        group_name: str = None) -> 'FloScriptGenerator':
        """修改几何属性"""
        if group_name:
            self.commands.append(
                f'    <modify_geometry new_value="{new_value}" '
                f'property_name="{property_name}" group_name="{group_name}"/>'
            )
        else:
            self.commands.append(
                f'    <modify_geometry new_value="{new_value}" '
                f'property_name="{property_name}"/>'
            )
        return self

    def set_power(self, component_name: str, power_value: float) -> 'FloScriptGenerator':
        """设置组件功率"""
        self.find_by_name(component_name)
        self.modify_geometry("power", power_value)
        self.clear_selection()
        return self

    def set_size(self, component_name: str, x: float = None, y: float = None,
                 z: float = None) -> 'FloScriptGenerator':
        """设置组件尺寸"""
        self.find_by_name(component_name)
        if x is not None:
            self.modify_geometry("x_size", x)
        if y is not None:
            self.modify_geometry("y_size", y)
        if z is not None:
            self.modify_geometry("z_size", z)
        self.clear_selection()
        return self

    # ==================== 修改属性/材料 ====================

    def modify_attribute(self, attribute_name: str, attribute_type: str,
                         property_name: str, new_value: Any,
                         group_name: str = None) -> 'FloScriptGenerator':
        """修改属性"""
        if group_name:
            self.commands.append(f'''    <modify_attribute new_value="{new_value}" property_name="{property_name}" group_name="{group_name}">
        <attribute_name name="{attribute_name}" type="{attribute_type}"/>
    </modify_attribute>''')
        else:
            self.commands.append(f'''    <modify_attribute new_value="{new_value}" property_name="{property_name}">
        <attribute_name name="{attribute_name}" type="{attribute_type}"/>
    </modify_attribute>''')
        return self

    def set_material_conductivity(self, material_name: str, conductivity: float) -> 'FloScriptGenerator':
        """设置材料导热率"""
        self._add_comment(f"设置材料导热率: {material_name} = {conductivity}")
        self.modify_attribute(material_name, "material", "conductivity", conductivity)
        return self

    # ==================== 求解器控制 ====================

    def modify_solver_control(self, property_name: str, new_value: Any,
                              group_name: str = None,
                              variable: str = None) -> 'FloScriptGenerator':
        """修改求解器控制参数"""
        if variable:
            self.commands.append(
                f'    <modify_solver_control new_value="{variable}" property_name="variable"/>'
            )
        if group_name:
            self.commands.append(
                f'    <modify_solver_control new_value="{new_value}" '
                f'property_name="{property_name}" group_name="{group_name}"/>'
            )
        else:
            self.commands.append(
                f'    <modify_solver_control new_value="{new_value}" '
                f'property_name="{property_name}"/>'
            )
        return self

    def set_solver_iterations(self, max_iterations: int,
                               variable: str = "temperature") -> 'FloScriptGenerator':
        """设置求解器最大迭代次数"""
        self._add_comment(f"设置 {variable} 迭代次数: {max_iterations}")
        self.modify_solver_control("innerIterations", max_iterations, variable=variable)
        return self

    def set_linear_relaxation(self, value: float,
                               variables: List[str] = None) -> 'FloScriptGenerator':
        """设置线性松弛因子"""
        if variables is None:
            variables = ["pressure", "xVelocity", "yVelocity", "zVelocity", "temperature"]

        self._add_comment(f"设置线性松弛因子: {value}")
        for var in variables:
            self.modify_solver_control("linearRelaxation", value,
                                       group_name=var, variable=var)
        return self

    # ==================== 网格控制 ====================

    def create_grid_constraint(self, name: str, min_size: bool = True,
                                min_size_value: float = 0.01,
                                min_number: int = 10) -> 'FloScriptGenerator':
        """创建网格约束"""
        self._add_comment(f"创建网格约束: {name}")

        self.commands.append(f'    <create_attribute attribute_type="gridConstraint" id="{name}"/>')
        self.commands.append(f'''    <modify_attribute new_value="{name}" property_name="name">
        <attribute_name id="{name}"/>
    </modify_attribute>''')

        if min_size:
            self.commands.append(f'''    <modify_attribute new_value="true" property_name="minimumSize">
        <attribute_name id="{name}"/>
    </modify_attribute>''')
            self.commands.append(f'''    <modify_attribute new_value="mm" property_name="lengthUnit">
        <attribute_name id="{name}"/>
    </modify_attribute>''')
            self.commands.append(f'''    <modify_attribute new_value="{min_size_value}" property_name="minimumSizeValue">
        <attribute_name id="{name}"/>
    </modify_attribute>''')

        self.commands.append(f'''    <modify_attribute new_value="{min_number}" property_name="minimumNumber">
        <attribute_name id="{name}"/>
    </modify_attribute>''')
        return self

    def apply_grid_constraint(self, constraint_name: str) -> 'FloScriptGenerator':
        """将网格约束应用到当前选中的几何对象"""
        self._add_comment(f"应用网格约束: {constraint_name}")
        self.commands.append(f'    <modify_geometry new_value="{constraint_name}" property_name="gridConstraintAttachment"/>')
        self.commands.append(f'    <modify_geometry new_value="true" property_name="localizeGrid"/>')
        return self

    # ==================== 求解 ====================

    def solve_all(self) -> 'FloScriptGenerator':
        """求解所有场景"""
        self._add_comment("执行求解")
        self.commands.append("    <solve_all/>")
        return self

    def solve_scenario(self, scenario_id: int) -> 'FloScriptGenerator':
        """求解指定场景"""
        self._add_comment(f"求解场景 {scenario_id}")
        self.commands.append(f'''    <solve_scenario>
        <scenario_id scenario_id="{scenario_id}"/>
    </solve_scenario>''')
        return self

    def reset(self) -> 'FloScriptGenerator':
        """重新初始化"""
        self._add_comment("重新初始化")
        self.commands.append("    <reset/>")
        return self

    # ==================== 其他 ====================

    def wait(self, delay_ms: int) -> 'FloScriptGenerator':
        """等待"""
        self.commands.append(f'    <wait delay="{delay_ms}"/>')
        return self

    def quit(self) -> 'FloScriptGenerator':
        """退出"""
        self.commands.append("    <quit/>")
        return self

    def add_custom_command(self, command: str) -> 'FloScriptGenerator':
        """添加自定义命令"""
        self.commands.append(f"    {command}")
        return self

    def _add_comment(self, text: str) -> None:
        """添加注释"""
        self.commands.append(f"    <!-- {text} -->")

    # ==================== 生成输出 ====================

    def generate(self) -> str:
        """生成完整的 FloSCRIPT XML"""
        lines = ['<?xml version="1.0" encoding="UTF-8"?>']
        lines.append(f'<xml_log_file version="{self.VERSION}">')

        for comment in self.header_comments:
            lines.append(f"    <!-- {comment} -->")

        lines.extend(self.commands)
        lines.append("</xml_log_file>")

        return "\n".join(lines)

    def save(self, output_path: str) -> str:
        """保存到文件"""
        xml_content = self.generate()
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(xml_content)
        print(f"[OK] FloSCRIPT 已生成: {output_path}")
        return output_path


# ==================== 便捷函数 ====================

def create_power_modification_script(pack_path: str, output_path: str,
                                     component_name: str, power_value: float,
                                     solve: bool = False) -> str:
    """创建修改功率的脚本"""
    gen = FloScriptGenerator()
    gen.load_project(pack_path)
    gen.set_power(component_name, power_value)
    if solve:
        gen.solve_all()
    gen.save_project_as(output_path)
    return gen.generate()


def create_batch_modification_script(pack_path: str, output_path: str,
                                     modifications: List[Dict],
                                     solve: bool = False) -> str:
    """
    创建批量修改脚本

    modifications 格式:
        [
            {"type": "power", "component": "U1", "value": 15.0},
            {"type": "size", "component": "Heatsink", "x": 100, "y": 100, "z": 20},
            {"type": "solver", "max_iterations": 500},
            {"type": "grid", "component": "U1", "min_size": 0.01, "min_number": 10},
            {"type": "material", "name": "Aluminum", "conductivity": 200},
        ]
    """
    gen = FloScriptGenerator()
    gen.load_project(pack_path)

    for mod in modifications:
        mod_type = mod.get("type")

        if mod_type == "power":
            gen.set_power(mod["component"], mod["value"])

        elif mod_type == "size":
            gen.find_by_name(mod["component"])
            gen.modify_geometry("x_size", mod.get("x"))
            gen.modify_geometry("y_size", mod.get("y"))
            gen.modify_geometry("z_size", mod.get("z"))
            gen.clear_selection()

        elif mod_type == "solver":
            if "max_iterations" in mod:
                gen.set_solver_iterations(mod["max_iterations"])
            if "linear_relaxation" in mod:
                gen.set_linear_relaxation(mod["linear_relaxation"])

        elif mod_type == "grid":
            constraint_name = f"Grid_{mod['component']}"
            gen.create_grid_constraint(constraint_name,
                                       min_size_value=mod.get("min_size", 0.01),
                                       min_number=mod.get("min_number", 10))
            gen.find_by_name(mod["component"])
            gen.apply_grid_constraint(constraint_name)
            gen.clear_selection()

        elif mod_type == "material":
            gen.set_material_conductivity(mod["name"], mod["conductivity"])

    if solve:
        gen.solve_all()

    gen.save_project_as(output_path)
    return gen.generate()


def run_floscript(script_path: str, flotherm_path: str = None,
                  timeout: int = 3600) -> bool:
    """
    执行 FloSCRIPT

    Args:
        script_path: FloSCRIPT XML 文件路径
        flotherm_path: FloTHERM 可执行文件路径
        timeout: 超时时间（秒）

    Returns:
        是否成功
    """
    # 自动检测 FloTHERM 路径
    if not flotherm_path:
        possible_paths = [
            r"D:\Program Files\Siemens\SimcenterFlotherm\2504\bin\flotherm.exe",
            r"C:\Program Files\Siemens\SimcenterFlotherm\2020.2\bin\flotherm.exe",
            r"C:\Program Files\Siemens\SimcenterFlotherm\2410\bin\flotherm.exe",
        ]
        for path in possible_paths:
            if os.path.exists(path):
                flotherm_path = path
                break

    if not flotherm_path or not os.path.exists(flotherm_path):
        print(f"[ERROR] 未找到 FloTHERM，请指定路径")
        return False

    print(f"[INFO] FloTHERM: {flotherm_path}")
    print(f"[INFO] FloSCRIPT: {script_path}")

    cmd = [flotherm_path, "-b", "-f", script_path]
    print(f"[INFO] 执行命令: {' '.join(cmd)}")

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)

        if result.returncode == 0:
            print("[OK] FloSCRIPT 执行成功")
            return True
        else:
            print(f"[ERROR] FloSCRIPT 执行失败: {result.returncode}")
            if result.stderr:
                print(f"       错误: {result.stderr[:500]}")
            return False

    except subprocess.TimeoutExpired:
        print(f"[ERROR] 执行超时 ({timeout}秒)")
        return False
    except Exception as e:
        print(f"[ERROR] 执行异常: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(
        description='FloSCRIPT 生成器 - 自动生成 FloTHERM 自动化脚本',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
示例:
  # 修改功率并生成脚本
  python floscript_generator.py modify-power model.pack U1_CPU 15.0 -o script.xml

  # 从 JSON 配置生成脚本
  python floscript_generator.py from-config config.json -o script.xml

  # 生成并执行
  python floscript_generator.py run model.pack --power U1_CPU=15.0 --solve

  # 执行已有的 FloSCRIPT
  python floscript_generator.py execute script.xml
        '''
    )

    subparsers = parser.add_subparsers(dest='command', help='命令')

    # modify-power 子命令
    power_parser = subparsers.add_parser('modify-power', help='修改功率')
    power_parser.add_argument('pack', help='Pack 文件路径')
    power_parser.add_argument('component', help='组件名称')
    power_parser.add_argument('power', type=float, help='功率值 (W)')
    power_parser.add_argument('-o', '--output', required=True, help='输出脚本路径')
    power_parser.add_argument('--output-pack', help='输出 Pack 路径')
    power_parser.add_argument('--solve', action='store_true', help='求解')

    # from-config 子命令
    config_parser = subparsers.add_parser('from-config', help='从配置文件生成')
    config_parser.add_argument('config', help='JSON 配置文件')
    config_parser.add_argument('-o', '--output', required=True, help='输出脚本路径')

    # run 子命令
    run_parser = subparsers.add_parser('run', help='生成并执行')
    run_parser.add_argument('pack', help='Pack 文件路径')
    run_parser.add_argument('--power', action='append', help='功率设置 (组件=值)')
    run_parser.add_argument('--solve', action='store_true', help='求解')
    run_parser.add_argument('--output-pack', help='输出 Pack 路径')

    # execute 子命令
    exec_parser = subparsers.add_parser('execute', help='执行 FloSCRIPT')
    exec_parser.add_argument('script', help='FloSCRIPT XML 文件')
    exec_parser.add_argument('--flotherm', help='FloTHERM 路径')

    # generate 子命令（生成示例脚本）
    gen_parser = subparsers.add_parser('generate', help='生成示例脚本')
    gen_parser.add_argument('type', choices=['solve', 'modify', 'batch'],
                           help='脚本类型')
    gen_parser.add_argument('-o', '--output', help='输出文件')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    if args.command == 'modify-power':
        output_pack = args.output_pack or args.pack.replace(".pack", "_modified.pack")
        xml = create_power_modification_script(
            args.pack, output_pack, args.component, args.power, args.solve
        )
        with open(args.output, 'w', encoding='utf-8') as f:
            f.write(xml)
        print(f"[OK] 脚本已生成: {args.output}")
        print(f"[INFO] 输出 Pack: {output_pack}")

    elif args.command == 'from-config':
        with open(args.config, 'r', encoding='utf-8') as f:
            config = json.load(f)

        xml = create_batch_modification_script(
            config["input_pack"],
            config.get("output_pack", config["input_pack"].replace(".pack", "_modified.pack")),
            config["modifications"],
            config.get("solve", False)
        )
        with open(args.output, 'w', encoding='utf-8') as f:
            f.write(xml)
        print(f"[OK] 脚本已生成: {args.output}")

    elif args.command == 'run':
        gen = FloScriptGenerator()
        gen.load_project(args.pack)

        if args.power:
            for power_setting in args.power:
                parts = power_setting.split("=")
                if len(parts) == 2:
                    component, value = parts
                    gen.set_power(component, float(value))

        if args.solve:
            gen.solve_all()

        if args.output_pack:
            gen.save_project_as(args.output_pack)
        else:
            gen.save_project()

        temp_script = "_temp_floscript.xml"
        gen.save(temp_script)
        success = run_floscript(temp_script)

        if success and os.path.exists(temp_script):
            os.remove(temp_script)

    elif args.command == 'execute':
        run_floscript(args.script, args.flotherm)

    elif args.command == 'generate':
        gen = FloScriptGenerator()

        if args.type == 'solve':
            gen.load_project("YOUR_MODEL.pack")
            gen.reset()
            gen.solve_all()
            gen.save_project()

        elif args.type == 'modify':
            gen.load_project("YOUR_MODEL.pack")
            gen.set_power("U1_CPU", 15.0)
            gen.set_solver_iterations(500)
            gen.solve_all()
            gen.save_project_as("OUTPUT.pack")

        elif args.type == 'batch':
            gen.load_project("YOUR_MODEL.pack")
            for i, power in enumerate([5, 10, 15, 20]):
                gen.set_power("U1_CPU", power)
                gen.solve_all()
                gen.save_project_as(f"OUTPUT_{i}.pack")

        output = args.output or f"example_{args.type}.xml"
        gen.save(output)
        print(f"[OK] 示例脚本已生成: {output}")


if __name__ == '__main__':
    main()
