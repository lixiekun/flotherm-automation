"""
批量仿真脚本生成器

根据配置生成批量 FloSCRIPT 脚本。

支持：
- 单配置生成
- 参数扫描（如功率 5W, 10W, 15W 生成三个脚本）
- 从 JSON/Excel 配置生成

Usage:
    generator = BatchSimulationGenerator.from_json("config.json")
    scripts = generator.generate_scripts()
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from .builder import FloScriptCommandBuilder


class BatchSimulationGeneratorError(Exception):
    """批量生成器错误"""
    pass


class BatchSimulationGenerator:
    """
    批量仿真脚本生成器

    根据配置生成批量 FloSCRIPT 脚本。

    Example:
        generator = BatchSimulationGenerator.from_json("config.json")
        generator.output_dir = Path("./scripts")
        scripts = generator.generate_scripts()
    """

    def __init__(self, config: Dict[str, Any]):
        """
        初始化生成器

        Args:
            config: 配置字典
        """
        self.config = config
        self._output_dir: Optional[Path] = None

    @classmethod
    def from_json(cls, json_path: str | Path) -> BatchSimulationGenerator:
        """
        从 JSON 文件创建生成器

        Args:
            json_path: JSON 配置文件路径

        Returns:
            BatchSimulationGenerator 实例
        """
        json_path = Path(json_path)
        content = json_path.read_text(encoding="utf-8")
        config = json.loads(content)

        # 验证必要字段
        if "input_pack" not in config:
            raise ValueError("Config must contain 'input_pack' field")

        return cls(config)

    @property
    def output_dir(self) -> Path:
        """输出目录"""
        if self._output_dir is None:
            # 从配置获取或使用默认值
            output_dir = self.config.get("output_dir", "./output_scripts")
            self._output_dir = Path(output_dir)
        return self._output_dir

    @output_dir.setter
    def output_dir(self, value: str | Path):
        self._output_dir = Path(value)

    def generate_scripts(self) -> List[Path]:
        """
        生成 FloSCRIPT 脚本

        Returns:
            生成的脚本文件路径列表
        """
        # 确保输出目录存在
        self.output_dir.mkdir(parents=True, exist_ok=True)

        scripts: List[Path] = []

        # 检查是否为参数扫描模式
        if "parameter_sweep" in self.config:
            scripts = self._generate_sweep_scripts()
        else:
            scripts = self._generate_single_script()

        return scripts

    def _generate_single_script(self) -> List[Path]:
        """生成单个脚本"""
        builder = FloScriptCommandBuilder()

        # 加载项目
        input_pack = self.config["input_pack"]
        builder.project_load(input_pack)

        # 应用修改
        modifications = self.config.get("modifications", [])
        for mod in modifications:
            self._apply_modification(builder, mod)

        # 求解
        if self.config.get("solve", False):
            builder.solve_all()

        # 保存
        output_pack = self.config.get("output_pack", "output.pack")
        builder.project_save_as(output_pack)

        # 生成脚本文件
        script_path = self.output_dir / "simulation.xml"
        builder.save(script_path)

        return [script_path]

    def _generate_sweep_scripts(self) -> List[Path]:
        """生成参数扫描脚本"""
        sweep_config = self.config["parameter_sweep"]
        component = sweep_config["component"]
        parameter = sweep_config["parameter"]
        values = sweep_config["values"]

        scripts: List[Path] = []

        for value in values:
            builder = FloScriptCommandBuilder()

            # 加载项目
            input_pack = self.config["input_pack"]
            builder.project_load(input_pack)

            # 应用参数扫描值
            if parameter == "power":
                builder.set_power(component, value)
            elif parameter == "x_size":
                builder.set_size(component, x=value)
            elif parameter == "y_size":
                builder.set_size(component, y=value)
            elif parameter == "z_size":
                builder.set_size(component, z=value)
            else:
                builder.find_by_name(component)
                builder.modify_geometry(parameter, value)
                builder.clear()

            # 求解
            if self.config.get("solve", False):
                builder.solve_all()

            # 保存
            output_pack = self.config.get(
                "output_pack",
                f"output_{parameter}_{value}.pack"
            )
            # 替换参数值
            output_pack = output_pack.replace("{value}", str(value))
            builder.project_save_as(output_pack)

            # 生成脚本文件（包含参数值在文件名中）
            script_name = f"simulation_{parameter}_{value}.xml"
            script_path = self.output_dir / script_name
            builder.save(script_path)

            scripts.append(script_path)

        return scripts

    def _apply_modification(self, builder: FloScriptCommandBuilder,
                             mod: Dict[str, Any]) -> None:
        """应用单个修改配置"""
        mod_type = mod.get("type")

        if mod_type == "power":
            builder.set_power(mod["component"], mod["value"])

        elif mod_type == "size":
            builder.set_size(
                mod["component"],
                x=mod.get("x"),
                y=mod.get("y"),
                z=mod.get("z")
            )

        elif mod_type == "material":
            builder.set_material_conductivity(mod["name"], mod["conductivity"])

        elif mod_type == "solver":
            if "max_iterations" in mod:
                builder.set_solver_iterations(mod["max_iterations"])
            if "linear_relaxation" in mod:
                builder.set_linear_relaxation(mod["linear_relaxation"])

        elif mod_type == "grid":
            builder.set_component_grid(
                mod["component"],
                min_size_value=mod.get("min_size", 0.01),
                min_number=mod.get("min_number", 10)
            )

        else:
            # 通用修改
            if "component" in mod:
                builder.find_by_name(mod["component"])
                builder.modify_geometry(mod["parameter"], mod["value"])
                builder.clear()

    def __repr__(self) -> str:
        return f"BatchSimulationGenerator(output_dir={self.output_dir})"
