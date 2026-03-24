"""
批量仿真脚本生成器测试 (TDD)

测试 BatchSimulationGenerator 类的功能。
"""

import pytest
import json
import tempfile
from pathlib import Path
from openpyxl import Workbook


class TestBatchSimulationGenerator:
    """BatchSimulationGenerator 测试类"""

    # ==================== Fixtures ====================

    @pytest.fixture
    def sample_json_config(self, temp_dir: Path) -> Path:
        """创建示例 JSON 配置文件"""
        config = {
            "input_pack": "model.pack",
            "output_dir": str(temp_dir / "output"),
            "modifications": [
                {"type": "power", "component": "U1_CPU", "value": 15.0},
                {"type": "power", "component": "U2_GPU", "value": 10.0},
            ],
            "solve": True
        }
        config_path = temp_dir / "config.json"
        config_path.write_text(json.dumps(config), encoding="utf-8")
        return config_path

    @pytest.fixture
    def sample_param_sweep_config(self, temp_dir: Path) -> Path:
        """创建参数扫描配置"""
        config = {
            "input_pack": "model.pack",
            "output_dir": str(temp_dir / "output"),
            "parameter_sweep": {
                "component": "U1_CPU",
                "parameter": "power",
                "values": [5.0, 10.0, 15.0, 20.0]
            },
            "solve": True
        }
        config_path = temp_dir / "sweep_config.json"
        config_path.write_text(json.dumps(config), encoding="utf-8")
        return config_path

    # ==================== 基础功能测试 ====================

    def test_import_batch_generator(self):
        """测试 BatchSimulationGenerator 可以导入"""
        from floscript.batch_generator import BatchSimulationGenerator
        assert BatchSimulationGenerator is not None

    def test_create_from_json(self, sample_json_config: Path):
        """测试从 JSON 配置创建"""
        from floscript.batch_generator import BatchSimulationGenerator

        generator = BatchSimulationGenerator.from_json(sample_json_config)
        assert generator is not None

    def test_generate_single_script(self, sample_json_config: Path, temp_dir: Path):
        """测试生成单个脚本"""
        from floscript.batch_generator import BatchSimulationGenerator

        generator = BatchSimulationGenerator.from_json(sample_json_config)
        generator.output_dir = temp_dir / "scripts"

        scripts = generator.generate_scripts()

        assert len(scripts) == 1
        assert scripts[0].suffix == ".xml"
        assert scripts[0].exists()

    def test_script_contains_modifications(self, sample_json_config: Path, temp_dir: Path):
        """测试脚本包含修改命令"""
        from floscript.batch_generator import BatchSimulationGenerator

        generator = BatchSimulationGenerator.from_json(sample_json_config)
        generator.output_dir = temp_dir / "scripts"

        scripts = generator.generate_scripts()
        content = scripts[0].read_text(encoding="utf-8")

        assert "U1_CPU" in content
        assert "15" in content
        assert "U2_GPU" in content
        assert "10" in content

    def test_script_contains_solve(self, sample_json_config: Path, temp_dir: Path):
        """测试脚本包含求解命令"""
        from floscript.batch_generator import BatchSimulationGenerator

        generator = BatchSimulationGenerator.from_json(sample_json_config)
        generator.output_dir = temp_dir / "scripts"

        scripts = generator.generate_scripts()
        content = scripts[0].read_text(encoding="utf-8")

        assert "<solve_all/>" in content

    # ==================== 参数扫描测试 ====================

    def test_parameter_sweep_generates_multiple_scripts(
        self, sample_param_sweep_config: Path, temp_dir: Path
    ):
        """测试参数扫描生成多个脚本"""
        from floscript.batch_generator import BatchSimulationGenerator

        generator = BatchSimulationGenerator.from_json(sample_param_sweep_config)
        generator.output_dir = temp_dir / "scripts"

        scripts = generator.generate_scripts()

        # 应该生成 4 个脚本（5, 10, 15, 20 W）
        assert len(scripts) == 4

    def test_parameter_sweep_script_names(
        self, sample_param_sweep_config: Path, temp_dir: Path
    ):
        """测试参数扫描脚本命名包含参数值"""
        from floscript.batch_generator import BatchSimulationGenerator

        generator = BatchSimulationGenerator.from_json(sample_param_sweep_config)
        generator.output_dir = temp_dir / "scripts"

        scripts = generator.generate_scripts()
        script_names = [s.stem for s in scripts]

        # 脚本名应包含参数值
        assert any("5" in name or "05" in name for name in script_names)
        assert any("10" in name for name in script_names)
        assert any("15" in name for name in script_names)
        assert any("20" in name for name in script_names)

    def test_parameter_sweep_different_values(
        self, sample_param_sweep_config: Path, temp_dir: Path
    ):
        """测试每个参数扫描脚本有不同的值"""
        from floscript.batch_generator import BatchSimulationGenerator

        generator = BatchSimulationGenerator.from_json(sample_param_sweep_config)
        generator.output_dir = temp_dir / "scripts"

        scripts = generator.generate_scripts()

        # 检查每个脚本包含不同的功率值
        values_found = []
        for script in scripts:
            content = script.read_text(encoding="utf-8")
            for val in [5.0, 10.0, 15.0, 20.0]:
                if f'new_value="{val}"' in content:
                    values_found.append(val)

        assert set(values_found) == {5.0, 10.0, 15.0, 20.0}

    # ==================== 输出目录测试 ====================

    def test_output_dir_created(self, sample_json_config: Path, temp_dir: Path):
        """测试输出目录自动创建"""
        from floscript.batch_generator import BatchSimulationGenerator

        output_dir = temp_dir / "new_output_dir"
        generator = BatchSimulationGenerator.from_json(sample_json_config)
        generator.output_dir = output_dir

        generator.generate_scripts()

        assert output_dir.exists()
        assert output_dir.is_dir()

    # ==================== 配置验证测试 ====================

    def test_missing_input_pack_raises_error(self, temp_dir: Path):
        """测试缺少 input_pack 时抛出错误"""
        from floscript.batch_generator import BatchSimulationGenerator

        config = {"modifications": []}  # 缺少 input_pack
        config_path = temp_dir / "bad_config.json"
        config_path.write_text(json.dumps(config), encoding="utf-8")

        with pytest.raises(ValueError, match="input_pack"):
            BatchSimulationGenerator.from_json(config_path)
