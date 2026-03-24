"""
FloSCRIPT 命令构建器

生成符合 FloSCRIPT Schema v1.0 的 XML 脚本。

支持链式调用，便于构建复杂的自动化脚本。

Usage:
    builder = FloScriptCommandBuilder()
    xml = (
        builder
        .project_load("model.pack")
        .project_save_as("output.pack")
        .build()
    )
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any, List, Optional


class FloScriptCommandBuilder:
    """
    FloSCRIPT 命令构建器

    生成符合 FloSCRIPT Schema v1.0 的 XML 脚本。
    支持链式调用。

    Example:
        builder = FloScriptCommandBuilder()
        xml = (
            builder
            .project_load("model.pack")
            .project_save()
            .build()
        )
    """

    VERSION = "1.0"

    def __init__(self):
        """初始化构建器"""
        self._commands: List[str] = []
        self._comments: List[str] = []

    # ==================== 项目操作 ====================

    def project_load(self, file_path: str) -> FloScriptCommandBuilder:
        """
        加载项目文件

        Args:
            file_path: Pack 文件路径

        Returns:
            self，支持链式调用
        """
        # 转换路径为正斜杠（FloSCRIPT 要求）
        normalized_path = str(file_path).replace("\\", "/")
        self._commands.append(f'<project_load file="{normalized_path}"/>')
        return self

    def project_save(self) -> FloScriptCommandBuilder:
        """
        保存项目

        Returns:
            self，支持链式调用
        """
        self._commands.append("<project_save/>")
        return self

    def project_save_as(self, file_path: str) -> FloScriptCommandBuilder:
        """
        另存为

        Args:
            file_path: 输出文件路径

        Returns:
            self，支持链式调用
        """
        normalized_path = str(file_path).replace("\\", "/")
        self._commands.append(f'<project_save_as file="{normalized_path}"/>')
        return self

    def project_delete(self) -> FloScriptCommandBuilder:
        """
        关闭/删除当前项目

        Returns:
            self，支持链式调用
        """
        self._commands.append("<project_delete/>")
        return self

    # ==================== 求解操作 ====================

    def solve_all(self) -> FloScriptCommandBuilder:
        """
        求解所有场景

        Returns:
            self，支持链式调用
        """
        self._commands.append("<solve_all/>")
        return self

    def reset(self) -> FloScriptCommandBuilder:
        """
        重置/重新初始化

        Returns:
            self，支持链式调用
        """
        self._commands.append("<reset/>")
        return self

    # ==================== 选择操作 ====================

    def clear(self) -> FloScriptCommandBuilder:
        """
        清除选择

        Returns:
            self，支持链式调用
        """
        self._commands.append("<clear_select_geometry/>")
        return self

    # ==================== 其他操作 ====================

    def quit(self) -> FloScriptCommandBuilder:
        """
        退出 FloTHERM

        Returns:
            self，支持链式调用
        """
        self._commands.append("<quit/>")
        return self

    def comment(self, text: str) -> FloScriptCommandBuilder:
        """
        添加注释

        Args:
            text: 注释内容

        Returns:
            self，支持链式调用
        """
        self._commands.append(f"<!-- {text} -->")
        return self

    def custom(self, xml_fragment: str) -> FloScriptCommandBuilder:
        """
        添加自定义 XML 片段

        Args:
            xml_fragment: XML 片段字符串

        Returns:
            self，支持链式调用
        """
        self._commands.append(xml_fragment)
        return self

    # ==================== US-004: 几何参数修改 ====================

    def find_by_name(self, name: str, select_mode: str = "all") -> FloScriptCommandBuilder:
        """
        按名称查找几何对象

        Args:
            name: 对象名称
            select_mode: 选择模式 (all/cycle)

        Returns:
            self，支持链式调用
        """
        self._commands.append(f'''<find filter="false" match="all" select_mode="{select_mode}">
        <enum_query_constraint criteria_type="common" is_positive="true">
            <value property_name="name" value="{name}"/>
        </enum_query_constraint>
    </find>''')
        return self

    def modify_geometry(self, property_name: str, value: Any,
                        group_name: str = None) -> FloScriptCommandBuilder:
        """
        修改几何属性

        Args:
            property_name: 属性名
            value: 新值
            group_name: 组名（可选）

        Returns:
            self，支持链式调用
        """
        if group_name:
            self._commands.append(
                f'<modify_geometry new_value="{value}" property_name="{property_name}" '
                f'group_name="{group_name}"/>'
            )
        else:
            self._commands.append(
                f'<modify_geometry new_value="{value}" property_name="{property_name}"/>'
            )
        return self

    def set_power(self, component_name: str, power_value: float) -> FloScriptCommandBuilder:
        """
        设置组件功率（封装方法）

        Args:
            component_name: 组件名称
            power_value: 功率值 (W)

        Returns:
            self，支持链式调用
        """
        self.find_by_name(component_name)
        self.modify_geometry("power", power_value)
        self.clear()
        return self

    def set_size(self, component_name: str, x: float = None, y: float = None,
                 z: float = None) -> FloScriptCommandBuilder:
        """
        设置组件尺寸

        Args:
            component_name: 组件名称
            x: X 尺寸（可选）
            y: Y 尺寸（可选）
            z: Z 尺寸（可选）

        Returns:
            self，支持链式调用
        """
        self.find_by_name(component_name)
        if x is not None:
            self.modify_geometry("x_size", x)
        if y is not None:
            self.modify_geometry("y_size", y)
        if z is not None:
            self.modify_geometry("z_size", z)
        self.clear()
        return self

    # ==================== US-005: 材料属性修改 ====================

    def modify_attribute(self, attribute_name: str, attribute_type: str,
                         property_name: str, value: Any,
                         group_name: str = None) -> FloScriptCommandBuilder:
        """
        修改属性

        Args:
            attribute_name: 属性名称
            attribute_type: 属性类型 (material, source, etc.)
            property_name: 要修改的属性
            value: 新值
            group_name: 组名

        Returns:
            self，支持链式调用
        """
        if group_name:
            self._commands.append(
                f'<modify_attribute new_value="{value}" property_name="{property_name}" '
                f'group_name="{group_name}">\n'
                f'        <attribute_name name="{attribute_name}" type="{attribute_type}"/>\n'
                f'    </modify_attribute>'
            )
        else:
            self._commands.append(
                f'<modify_attribute new_value="{value}" property_name="{property_name}">\n'
                f'        <attribute_name name="{attribute_name}" type="{attribute_type}"/>\n'
                f'    </modify_attribute>'
            )
        return self

    def set_material_conductivity(self, material_name: str,
                                   conductivity: float) -> FloScriptCommandBuilder:
        """
        设置材料导热率

        Args:
            material_name: 材料名称
            conductivity: 导热率 (W/mK)

        Returns:
            self，支持链式调用
        """
        return self.modify_attribute(material_name, "material", "conductivity", conductivity)

    # ==================== US-006: 网格配置 ====================

    def create_grid_constraint(self, name: str, min_size: bool = True,
                                min_size_value: float = 0.01,
                                min_number: int = 10) -> FloScriptCommandBuilder:
        """
        创建网格约束

        Args:
            name: 约束名称
            min_size: 是否使用最小尺寸
            min_size_value: 最小尺寸值
            min_number: 最小单元数

        Returns:
            self，支持链式调用
        """
        # 创建约束
        self._commands.append(f'<create_attribute attribute_type="gridConstraint" id="{name}"/>')

        # 设置名称
        self._commands.append(
            f'<modify_attribute new_value="{name}" property_name="name">\n'
            f'        <attribute_name id="{name}"/>\n'
            f'    </modify_attribute>'
        )

        # 设置最小尺寸
        if min_size:
            self._commands.append(
                f'<modify_attribute new_value="true" property_name="minimumSize">\n'
                f'        <attribute_name id="{name}"/>\n'
                f'    </modify_attribute>'
            )
            self._commands.append(
                f'<modify_attribute new_value="mm" property_name="lengthUnit">\n'
                f'        <attribute_name id="{name}"/>\n'
                f'    </modify_attribute>'
            )
            self._commands.append(
                f'<modify_attribute new_value="{min_size_value}" property_name="minimumSizeValue">\n'
                f'        <attribute_name id="{name}"/>\n'
                f'    </modify_attribute>'
            )

        # 设置最小单元数
        self._commands.append(
            f'<modify_attribute new_value="{min_number}" property_name="minimumNumber">\n'
            f'        <attribute_name id="{name}"/>\n'
            f'    </modify_attribute>'
        )

        return self

    def apply_grid_constraint(self, constraint_name: str) -> FloScriptCommandBuilder:
        """
        将网格约束应用到当前选中的几何对象

        Args:
            constraint_name: 约束名称

        Returns:
            self，支持链式调用
        """
        self._commands.append(
            f'<modify_geometry new_value="{constraint_name}" '
            f'property_name="gridConstraintAttachment"/>'
        )
        self._commands.append(
            f'<modify_geometry new_value="true" property_name="localizeGrid"/>'
        )
        return self

    def set_component_grid(self, component_name: str, min_size_value: float = 0.01,
                            min_number: int = 10) -> FloScriptCommandBuilder:
        """
        设置组件网格（封装方法）

        Args:
            component_name: 组件名称
            min_size_value: 最小尺寸值
            min_number: 最小单元数

        Returns:
            self，支持链式调用
        """
        constraint_name = f"Grid_{component_name}"
        self.create_grid_constraint(constraint_name, min_size_value=min_size_value,
                                    min_number=min_number)
        self.find_by_name(component_name)
        self.apply_grid_constraint(constraint_name)
        self.clear()
        return self

    # ==================== US-007: 求解器配置 ====================

    def modify_solver_control(self, property_name: str, value: Any,
                              group_name: str = None,
                              variable: str = None) -> FloScriptCommandBuilder:
        """
        修改求解器控制参数

        Args:
            property_name: 属性名
            value: 新值
            group_name: 组名
            variable: 变量名 (pressure, temperature, xVelocity 等)

        Returns:
            self，支持链式调用
        """
        if variable:
            self._commands.append(
                f'<modify_solver_control new_value="{variable}" property_name="variable"/>'
            )
        if group_name:
            self._commands.append(
                f'<modify_solver_control new_value="{value}" property_name="{property_name}" '
                f'group_name="{group_name}"/>'
            )
        else:
            self._commands.append(
                f'<modify_solver_control new_value="{value}" property_name="{property_name}"/>'
            )
        return self

    def set_solver_iterations(self, max_iterations: int,
                               variable: str = "temperature") -> FloScriptCommandBuilder:
        """
        设置求解器最大迭代次数

        Args:
            max_iterations: 最大迭代次数
            variable: 变量名

        Returns:
            self，支持链式调用
        """
        return self.modify_solver_control("innerIterations", max_iterations, variable=variable)

    def set_linear_relaxation(self, value: float,
                               variables: List[str] = None) -> FloScriptCommandBuilder:
        """
        设置线性松弛因子

        Args:
            value: 松弛因子值 (0-1)
            variables: 变量列表（默认为所有主要变量）

        Returns:
            self，支持链式调用
        """
        if variables is None:
            variables = ["pressure", "xVelocity", "yVelocity", "zVelocity", "temperature"]

        for var in variables:
            self.modify_solver_control("linearRelaxation", value,
                                       group_name=var, variable=var)
        return self

    # ==================== 输出 ====================

    def build(self) -> str:
        """
        构建并返回完整的 FloSCRIPT XML

        Returns:
            完整的 FloSCRIPT XML 字符串
        """
        lines = [
            '<?xml version="1.0" encoding="UTF-8"?>',
            f'<xml_log_file version="{self.VERSION}">',
        ]

        # 添加命令
        for cmd in self._commands:
            lines.append(f"    {cmd}")

        lines.append("</xml_log_file>")

        return "\n".join(lines)

    def save(self, file_path: str) -> str:
        """
        保存到文件

        Args:
            file_path: 输出文件路径

        Returns:
            保存的文件路径
        """
        content = self.build()
        Path(file_path).write_text(content, encoding="utf-8")
        return file_path

    def clear_commands(self) -> FloScriptCommandBuilder:
        """
        清空所有命令

        Returns:
            self，支持链式调用
        """
        self._commands.clear()
        return self

    def __repr__(self) -> str:
        return f"FloScriptCommandBuilder(commands={len(self._commands)})"
