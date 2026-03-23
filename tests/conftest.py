"""
Pytest 共享 fixtures 和配置

提供测试所需的共享资源和工具函数。
"""

import os
import sys
import pytest
import tempfile
from pathlib import Path

# 添加项目根目录到 Python 路径
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


# ==================== 路径 fixtures ====================

@pytest.fixture
def project_root() -> Path:
    """项目根目录"""
    return PROJECT_ROOT


@pytest.fixture
def test_data_dir(project_root: Path) -> Path:
    """测试数据目录"""
    return project_root / "tests" / "data"


@pytest.fixture
def examples_dir(project_root: Path) -> Path:
    """示例文件目录"""
    return project_root / "examples"


# ==================== 临时文件 fixtures ====================

@pytest.fixture
def temp_dir():
    """临时目录，测试后自动清理"""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def temp_file(temp_dir: Path):
    """临时文件工厂函数"""
    def _create_file(content: str = "", suffix: str = ".xml") -> Path:
        file_path = temp_dir / f"test_{os.urandom(4).hex()}{suffix}"
        if content:
            file_path.write_text(content, encoding='utf-8')
        return file_path
    return _create_file


# ==================== 示例数据 fixtures ====================

@pytest.fixture
def sample_floscript_minimal() -> str:
    """最小 FloSCRIPT 示例"""
    return '''<?xml version="1.0" encoding="UTF-8"?>
<xml_log_file version="1.0">
    <project_load file="test.pack"/>
    <project_save/>
</xml_log_file>'''


@pytest.fixture
def sample_floscript_solve() -> str:
    """包含求解的 FloSCRIPT 示例"""
    return '''<?xml version="1.0" encoding="UTF-8"?>
<xml_log_file version="1.0">
    <project_load file="test.pack"/>
    <solve_all/>
    <project_save_as file="output.pack"/>
</xml_log_file>'''


@pytest.fixture
def sample_excel_config_rows() -> list:
    """示例 Excel 配置数据（模拟读取后的行）"""
    return [
        {"component": "U1_CPU", "parameter": "power", "value": 15.0},
        {"component": "U2_GPU", "parameter": "power", "value": 10.0},
        {"component": "U1_CPU", "parameter": "x_size", "value": 0.02},
        {"component": "U1_CPU", "parameter": "y_size", "value": 0.02},
        {"component": "U1_CPU", "parameter": "z_size", "value": 0.001},
    ]


@pytest.fixture
def sample_json_config() -> dict:
    """示例 JSON 配置"""
    return {
        "input_pack": "model.pack",
        "output_pack": "output.pack",
        "modifications": [
            {"type": "power", "component": "U1_CPU", "value": 15.0},
            {"type": "solver", "max_iterations": 500},
        ],
        "solve": True
    }


# ==================== FloTHERM 路径 fixtures ====================

@pytest.fixture
def flotherm_paths() -> list:
    """可能的 FloTHERM 安装路径"""
    return [
        r"D:\Program Files\Siemens\SimcenterFlotherm\2504\WinXP\bin\flotherm.exe",
        r"C:\Program Files\Siemens\SimcenterFlotherm\2020.2\bin\flotherm.exe",
        r"C:\Program Files\Siemens\SimcenterFlotherm\2410\bin\flotherm.exe",
    ]


@pytest.fixture
def flotherm_exe(flotherm_paths: list) -> Path:
    """找到的 FloTHERM 可执行文件路径"""
    for path in flotherm_paths:
        if os.path.exists(path):
            return Path(path)
    pytest.skip("FloTHERM not found")


# ==================== 工具函数 ====================

def assert_valid_xml(content: str) -> None:
    """验证 XML 格式是否有效"""
    import xml.etree.ElementTree as ET
    try:
        ET.fromstring(content)
    except ET.ParseError as e:
        pytest.fail(f"Invalid XML: {e}")


def assert_floscript_valid(content: str) -> None:
    """验证 FloSCRIPT 格式是否有效"""
    import xml.etree.ElementTree as ET
    try:
        root = ET.fromstring(content)
        assert root.tag == "xml_log_file", f"Root tag should be 'xml_log_file', got '{root.tag}'"
        assert "version" in root.attrib, "Missing 'version' attribute"
    except ET.ParseError as e:
        pytest.fail(f"Invalid FloSCRIPT XML: {e}")
