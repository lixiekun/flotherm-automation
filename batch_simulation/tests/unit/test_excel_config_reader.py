"""
Excel 配置读取器测试 (TDD)

测试 ExcelConfigReader 类的功能。
配置格式：
- 第一行为表头：component, parameter, value
- 后续行为数据行
"""

import pytest
import tempfile
from pathlib import Path
from openpyxl import Workbook


# 将在 config/excel_config_reader.py 中实现
# from config.excel_config_reader import ExcelConfigReader


class TestExcelConfigReader:
    """ExcelConfigReader 测试类"""

    # ==================== Fixtures ====================

    @pytest.fixture
    def create_excel_file(self, temp_dir: Path):
        """创建 Excel 测试文件的工厂函数"""
        def _create(rows: list, headers: list = None) -> Path:
            if headers is None:
                headers = ["component", "parameter", "value"]

            wb = Workbook()
            ws = wb.active
            ws.append(headers)
            for row in rows:
                ws.append(row)

            file_path = temp_dir / f"test_config_{len(rows)}.xlsx"
            wb.save(file_path)
            return file_path
        return _create

    # ==================== 基础功能测试 ====================

    def test_import_excel_config_reader(self):
        """测试 ExcelConfigReader 可以导入"""
        from config.excel_config_reader import ExcelConfigReader
        assert ExcelConfigReader is not None

    def test_read_single_row(self, create_excel_file):
        """测试读取单行配置"""
        from config.excel_config_reader import ExcelConfigReader

        # 创建测试文件
        file_path = create_excel_file([
            ["U1_CPU", "power", 15.0]
        ])

        # 读取配置
        reader = ExcelConfigReader(file_path)
        config = reader.read()

        # 验证
        assert len(config) == 1
        assert config[0]["component"] == "U1_CPU"
        assert config[0]["parameter"] == "power"
        assert config[0]["value"] == 15.0

    def test_read_multiple_rows(self, create_excel_file):
        """测试读取多行配置"""
        from config.excel_config_reader import ExcelConfigReader

        file_path = create_excel_file([
            ["U1_CPU", "power", 15.0],
            ["U2_GPU", "power", 10.0],
            ["U1_CPU", "x_size", 0.02],
        ])

        reader = ExcelConfigReader(file_path)
        config = reader.read()

        assert len(config) == 3
        assert config[0]["component"] == "U1_CPU"
        assert config[1]["component"] == "U2_GPU"
        assert config[2]["parameter"] == "x_size"

    def test_read_empty_file(self, create_excel_file):
        """测试读取空文件（只有表头）"""
        from config.excel_config_reader import ExcelConfigReader

        file_path = create_excel_file([])  # 只有表头

        reader = ExcelConfigReader(file_path)
        config = reader.read()

        assert len(config) == 0

    # ==================== 数据类型测试 ====================

    def test_numeric_values(self, create_excel_file):
        """测试数值类型"""
        from config.excel_config_reader import ExcelConfigReader

        file_path = create_excel_file([
            ["U1", "power", 15.5],      # float
            ["U2", "count", 10],         # int
            ["U3", "ratio", 0.001],      # small float
        ])

        reader = ExcelConfigReader(file_path)
        config = reader.read()

        assert config[0]["value"] == 15.5
        assert config[1]["value"] == 10
        assert config[2]["value"] == 0.001

    def test_string_values(self, create_excel_file):
        """测试字符串类型"""
        from config.excel_config_reader import ExcelConfigReader

        file_path = create_excel_file([
            ["Mat1", "name", "Aluminum"],
            ["Mat2", "type", "isotropic"],
        ])

        reader = ExcelConfigReader(file_path)
        config = reader.read()

        assert config[0]["value"] == "Aluminum"
        assert config[1]["value"] == "isotropic"

    # ==================== 错误处理测试 ====================

    def test_missing_column_raises_error(self, create_excel_file):
        """测试缺少必要列时抛出错误"""
        from config.excel_config_reader import ExcelConfigReader, MissingColumnError

        # 缺少 value 列
        file_path = create_excel_file(
            [["U1", "power"]],
            headers=["component", "parameter"]  # 缺少 value
        )

        reader = ExcelConfigReader(file_path)
        with pytest.raises(MissingColumnError, match="Missing required columns"):
            reader.read()

    def test_file_not_found(self, temp_dir: Path):
        """测试文件不存在时抛出错误"""
        from config.excel_config_reader import ExcelConfigReader

        non_existent = temp_dir / "not_found.xlsx"
        reader = ExcelConfigReader(non_existent)

        with pytest.raises(FileNotFoundError):
            reader.read()

    def test_invalid_file_type(self, temp_dir: Path):
        """测试非 Excel 文件时抛出错误"""
        from config.excel_config_reader import ExcelConfigReader

        # 创建一个非 Excel 文件
        invalid_file = temp_dir / "invalid.txt"
        invalid_file.write_text("not an excel file")

        reader = ExcelConfigReader(invalid_file)
        with pytest.raises(Exception):  # 可能是 InvalidFileException
            reader.read()

    # ==================== 高级功能测试 ====================

    def test_get_components(self, create_excel_file):
        """测试获取组件列表"""
        from config.excel_config_reader import ExcelConfigReader

        file_path = create_excel_file([
            ["U1_CPU", "power", 15.0],
            ["U1_CPU", "x_size", 0.02],
            ["U2_GPU", "power", 10.0],
        ])

        reader = ExcelConfigReader(file_path)
        components = reader.get_components()

        assert len(components) == 2
        assert "U1_CPU" in components
        assert "U2_GPU" in components

    def test_get_by_component(self, create_excel_file):
        """测试按组件筛选配置"""
        from config.excel_config_reader import ExcelConfigReader

        file_path = create_excel_file([
            ["U1_CPU", "power", 15.0],
            ["U1_CPU", "x_size", 0.02],
            ["U2_GPU", "power", 10.0],
        ])

        reader = ExcelConfigReader(file_path)
        u1_config = reader.get_by_component("U1_CPU")

        assert len(u1_config) == 2
        assert all(c["component"] == "U1_CPU" for c in u1_config)

    def test_to_dict(self, create_excel_file):
        """测试转换为字典格式"""
        from config.excel_config_reader import ExcelConfigReader

        file_path = create_excel_file([
            ["U1_CPU", "power", 15.0],
            ["U1_CPU", "x_size", 0.02],
        ])

        reader = ExcelConfigReader(file_path)
        config_dict = reader.to_dict()

        assert "U1_CPU" in config_dict
        assert config_dict["U1_CPU"]["power"] == 15.0
        assert config_dict["U1_CPU"]["x_size"] == 0.02
