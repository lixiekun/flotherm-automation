"""
FloSCRIPT 命令构建器测试 (TDD)

测试 FloScriptCommandBuilder 类的功能。
"""

import pytest
import xml.etree.ElementTree as ET
from pathlib import Path


class TestFloScriptCommandBuilder:
    """FloScriptCommandBuilder 测试类"""

    # ==================== 导入和基础测试 ====================

    def test_import_builder(self):
        """测试 FloScriptCommandBuilder 可以导入"""
        from floscript.builder import FloScriptCommandBuilder
        assert FloScriptCommandBuilder is not None

    def test_create_builder_instance(self):
        """测试创建构建器实例"""
        from floscript.builder import FloScriptCommandBuilder
        builder = FloScriptCommandBuilder()
        assert builder is not None

    # ==================== 链式调用测试 ====================

    def test_method_chaining(self):
        """测试链式调用"""
        from floscript.builder import FloScriptCommandBuilder
        builder = FloScriptCommandBuilder()
        result = builder.project_load("test.pack").project_save()
        assert result is builder  # 返回 self 以支持链式调用

    # ==================== 空脚本测试 ====================

    def test_empty_script(self):
        """测试空脚本生成"""
        from floscript.builder import FloScriptCommandBuilder
        builder = FloScriptCommandBuilder()
        xml = builder.build()

        # 验证 XML 格式
        root = ET.fromstring(xml)
        assert root.tag == "xml_log_file"
        assert root.attrib.get("version") == "1.0"

    # ==================== project_load 测试 ====================

    def test_project_load(self):
        """测试 project_load 命令"""
        from floscript.builder import FloScriptCommandBuilder
        builder = FloScriptCommandBuilder()
        xml = builder.project_load("model.pack").build()

        assert '<project_load file="model.pack"/>' in xml

    def test_project_load_with_path_conversion(self):
        """测试路径自动转换（反斜杠转正斜杠）"""
        from floscript.builder import FloScriptCommandBuilder
        builder = FloScriptCommandBuilder()
        xml = builder.project_load(r"C:\test\model.pack").build()

        # FloSCRIPT 需要正斜杠
        assert "C:/test/model.pack" in xml or "C:\\test\\model.pack" not in xml

    # ==================== project_save 测试 ====================

    def test_project_save(self):
        """测试 project_save 命令"""
        from floscript.builder import FloScriptCommandBuilder
        builder = FloScriptCommandBuilder()
        xml = builder.project_save().build()

        assert "<project_save/>" in xml

    # ==================== project_save_as 测试 ====================

    def test_project_save_as(self):
        """测试 project_save_as 命令"""
        from floscript.builder import FloScriptCommandBuilder
        builder = FloScriptCommandBuilder()
        xml = builder.project_save_as("output.pack").build()

        assert '<project_save_as file="output.pack"/>' in xml

    # ==================== 多命令组合测试 ====================

    def test_load_and_save(self):
        """测试加载并保存"""
        from floscript.builder import FloScriptCommandBuilder
        builder = FloScriptCommandBuilder()
        xml = builder.project_load("input.pack").project_save().build()

        assert '<project_load file="input.pack"/>' in xml
        assert "<project_save/>" in xml
        # load 应该在 save 之前
        assert xml.index("project_load") < xml.index("project_save")

    def test_load_save_as_and_quit(self):
        """测试加载、另存为、退出"""
        from floscript.builder import FloScriptCommandBuilder
        builder = FloScriptCommandBuilder()
        xml = builder.project_load("input.pack").project_save_as("output.pack").quit().build()

        assert '<project_load file="input.pack"/>' in xml
        assert '<project_save_as file="output.pack"/>' in xml
        assert "<quit/>" in xml

    # ==================== clear 和 reset 测试 ====================

    def test_clear(self):
        """测试清除命令"""
        from floscript.builder import FloScriptCommandBuilder
        builder = FloScriptCommandBuilder()
        xml = builder.clear().build()
        assert "<clear/>" in xml or "<clear_select_geometry/>" in xml

    def test_reset(self):
        """测试重置命令"""
        from floscript.builder import FloScriptCommandBuilder
        builder = FloScriptCommandBuilder()
        xml = builder.reset().build()
        assert "<reset/>" in xml

    # ==================== XML 格式验证 ====================

    def test_valid_xml_structure(self):
        """测试 XML 结构有效性"""
        from floscript.builder import FloScriptCommandBuilder
        builder = FloScriptCommandBuilder()
        xml = builder.project_load("test.pack").project_save().build()

        # 验证可以解析
        root = ET.fromstring(xml)
        assert root.tag == "xml_log_file"

        # 验证有 version 属性
        assert "version" in root.attrib

    def test_xml_encoding(self):
        """测试 XML 编码声明"""
        from floscript.builder import FloScriptCommandBuilder
        builder = FloScriptCommandBuilder()
        xml = builder.build()

        assert xml.startswith('<?xml version="1.0"')
        assert "encoding=" in xml or "UTF-8" in xml

    # ==================== 注释支持 ====================

    def test_add_comment(self):
        """测试添加注释"""
        from floscript.builder import FloScriptCommandBuilder
        builder = FloScriptCommandBuilder()
        xml = builder.comment("Test comment").project_load("test.pack").build()

        assert "<!-- Test comment -->" in xml


# ==================== US-004: 几何参数修改测试 ====================

class TestGeometryCommands:
    """几何参数修改命令测试"""

    def test_find_by_name(self):
        """测试按名称查找"""
        from floscript.builder import FloScriptCommandBuilder
        builder = FloScriptCommandBuilder()
        xml = builder.find_by_name("U1_CPU").build()

        assert '<find filter="false" match="all" select_mode="all">' in xml
        assert '<value property_name="name" value="U1_CPU"/>' in xml
        assert '</find>' in xml

    def test_modify_geometry(self):
        """测试修改几何属性"""
        from floscript.builder import FloScriptCommandBuilder
        builder = FloScriptCommandBuilder()
        xml = builder.modify_geometry("power", 15.0).build()

        assert '<modify_geometry new_value="15.0" property_name="power"/>' in xml

    def test_set_power(self):
        """测试设置功率（封装方法）"""
        from floscript.builder import FloScriptCommandBuilder
        builder = FloScriptCommandBuilder()
        xml = builder.set_power("U1_CPU", 20.0).build()

        # 应该包含 find 和 modify_geometry
        assert '<value property_name="name" value="U1_CPU"/>' in xml
        assert '<modify_geometry new_value="20.0" property_name="power"/>' in xml
        assert '<clear_select_geometry/>' in xml

    def test_set_size_all(self):
        """测试设置全部尺寸"""
        from floscript.builder import FloScriptCommandBuilder
        builder = FloScriptCommandBuilder()
        xml = builder.set_size("Heatsink", x=0.1, y=0.1, z=0.02).build()

        assert 'property_name="x_size"' in xml
        assert 'property_name="y_size"' in xml
        assert 'property_name="z_size"' in xml

    def test_set_size_partial(self):
        """测试设置部分尺寸"""
        from floscript.builder import FloScriptCommandBuilder
        builder = FloScriptCommandBuilder()
        xml = builder.set_size("Block", x=0.05).build()

        assert 'property_name="x_size"' in xml
        assert 'property_name="y_size"' not in xml


# ==================== US-005: 材料属性修改测试 ====================

class TestMaterialCommands:
    """材料属性修改命令测试"""

    def test_modify_attribute(self):
        """测试修改属性"""
        from floscript.builder import FloScriptCommandBuilder
        builder = FloScriptCommandBuilder()
        xml = builder.modify_attribute("Aluminum", "material", "conductivity", 205.0).build()

        assert '<modify_attribute' in xml
        assert 'new_value="205.0"' in xml
        assert 'property_name="conductivity"' in xml

    def test_set_material_conductivity(self):
        """测试设置材料导热率"""
        from floscript.builder import FloScriptCommandBuilder
        builder = FloScriptCommandBuilder()
        xml = builder.set_material_conductivity("Copper", 385.0).build()

        assert '<modify_attribute' in xml
        assert 'Copper' in xml
        assert '385.0' in xml


# ==================== US-006: 网格配置测试 ====================

class TestGridCommands:
    """网格配置命令测试"""

    def test_create_grid_constraint(self):
        """测试创建网格约束"""
        from floscript.builder import FloScriptCommandBuilder
        builder = FloScriptCommandBuilder()
        xml = builder.create_grid_constraint("Grid_U1", min_size_value=0.01, min_number=10).build()

        assert '<create_attribute attribute_type="gridConstraint"' in xml
        assert 'minimumNumber"' in xml

    def test_apply_grid_constraint(self):
        """测试应用网格约束"""
        from floscript.builder import FloScriptCommandBuilder
        builder = FloScriptCommandBuilder()
        xml = builder.apply_grid_constraint("Grid_U1").build()

        assert 'gridConstraintAttachment' in xml
        assert 'localizeGrid' in xml

    def test_set_component_grid(self):
        """测试设置组件网格（封装方法）"""
        from floscript.builder import FloScriptCommandBuilder
        builder = FloScriptCommandBuilder()
        xml = builder.set_component_grid("U1_CPU", min_size_value=0.005, min_number=15).build()

        # 应该包含创建约束、查找、应用
        assert 'gridConstraint' in xml
        assert 'U1_CPU' in xml


# ==================== US-007: 求解器配置测试 ====================

class TestSolverCommands:
    """求解器配置命令测试"""

    def test_modify_solver_control(self):
        """测试修改求解器控制"""
        from floscript.builder import FloScriptCommandBuilder
        builder = FloScriptCommandBuilder()
        xml = builder.modify_solver_control("innerIterations", 500).build()

        assert '<modify_solver_control' in xml
        assert 'innerIterations' in xml
        assert '500' in xml

    def test_set_solver_iterations(self):
        """测试设置求解器迭代次数"""
        from floscript.builder import FloScriptCommandBuilder
        builder = FloScriptCommandBuilder()
        xml = builder.set_solver_iterations(300, variable="temperature").build()

        assert 'temperature' in xml
        assert '300' in xml

    def test_set_linear_relaxation(self):
        """测试设置线性松弛因子"""
        from floscript.builder import FloScriptCommandBuilder
        builder = FloScriptCommandBuilder()
        xml = builder.set_linear_relaxation(0.9).build()

        # 应该为所有变量设置
        assert 'pressure' in xml
        assert 'temperature' in xml
        assert 'linearRelaxation' in xml
        assert '0.9' in xml

    def test_solve_all(self):
        """测试求解命令"""
        from floscript.builder import FloScriptCommandBuilder
        builder = FloScriptCommandBuilder()
        xml = builder.solve_all().build()

        assert '<solve_all/>' in xml


class TestFloScriptValidationHelper:
    """FloSCRIPT 验证辅助测试"""

    def test_builder_output_is_valid_floscript(self):
        """测试生成的输出是有效的 FloSCRIPT"""
        from floscript.builder import FloScriptCommandBuilder
        builder = FloScriptCommandBuilder()

        xml = (
            builder
            .project_load("model.pack")
            .project_save_as("output.pack")
            .build()
        )

        # 验证 XML 可解析
        root = ET.fromstring(xml)

        # 验证根元素
        assert root.tag == "xml_log_file"
        assert root.attrib["version"] == "1.0"

        # 验证包含命令
        commands = list(root)
        assert len(commands) >= 2

    def test_full_simulation_script(self):
        """测试完整仿真脚本"""
        from floscript.builder import FloScriptCommandBuilder
        builder = FloScriptCommandBuilder()

        xml = (
            builder
            .project_load("model.pack")
            .set_power("U1_CPU", 15.0)
            .set_solver_iterations(500)
            .solve_all()
            .project_save_as("output.pack")
            .build()
        )

        # 验证 XML 可解析
        root = ET.fromstring(xml)
        assert root.tag == "xml_log_file"

        # 验证包含所有关键命令
        assert "project_load" in xml
        assert "modify_geometry" in xml
        assert "solve_all" in xml
        assert "project_save_as" in xml
