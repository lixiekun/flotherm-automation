"""
FloXML 项目创建器

从零创建 FloXML 项目文件。

Usage:
    creator = FloXMLCreator()
    creator.create_project("MyProject")
    creator.add_material("Aluminum", conductivity=205.0)
    creator.add_cuboid("Block", x=0.1, y=0.1, z=0.02, material="Aluminum", power=10.0)
    creator.set_solution_domain(x=0, y=0, z=0, dx=0.5, dy=0.5, dz=0.5)
    creator.save("output.xml")
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional


class FloXMLCreator:
    """
    FloXML 项目创建器

    从零创建 FloXML 项目文件。
    """

    def __init__(self):
        """初始化创建器"""
        self._project_name: str = "Project"
        self._materials: List[Dict[str, Any]] = []
        self._geometry: List[Dict[str, Any]] = []
        self._solution_domain: Optional[Dict[str, float]] = None
        self._grid_settings: Optional[Dict[str, Any]] = None

    def create_project(self, name: str) -> FloXMLCreator:
        """
        初始化项目

        Args:
            name: 项目名称

        Returns:
            self，支持链式调用
        """
        self._project_name = name
        return self

    def add_material(self, name: str, conductivity: float,
                     density: float = None, specific_heat: float = None) -> FloXMLCreator:
        """
        添加材料

        Args:
            name: 材料名称
            conductivity: 导热率 (W/mK)
            density: 密度 (kg/m³)
            specific_heat: 比热容 (J/kgK)

        Returns:
            self，支持链式调用
        """
        material = {
            "name": name,
            "conductivity": conductivity,
            "density": density,
            "specific_heat": specific_heat
        }
        self._materials.append(material)
        return self

    def add_cuboid(self, name: str, x: float, y: float, z: float,
                   material: str = None, power: float = None,
                   location: tuple = (0, 0, 0)) -> FloXMLCreator:
        """
        添加立方体

        Args:
            name: 名称
            x, y, z: 尺寸
            material: 材料名称
            power: 功率 (W)
            location: 位置 (x, y, z)

        Returns:
            self，支持链式调用
        """
        cuboid = {
            "type": "cuboid",
            "name": name,
            "x_size": x,
            "y_size": y,
            "z_size": z,
            "material": material,
            "power": power,
            "location": location
        }
        self._geometry.append(cuboid)
        return self

    def set_solution_domain(self, x: float, y: float, z: float,
                             dx: float, dy: float, dz: float) -> FloXMLCreator:
        """
        设置求解域

        Args:
            x, y, z: 起始位置
            dx, dy, dz: 尺寸

        Returns:
            self，支持链式调用
        """
        self._solution_domain = {
            "x": x, "y": y, "z": z,
            "dx": dx, "dy": dy, "dz": dz
        }
        return self

    def set_grid(self, settings: Dict[str, Any]) -> FloXMLCreator:
        """
        设置网格

        Args:
            settings: 网格设置

        Returns:
            self，支持链式调用
        """
        self._grid_settings = settings
        return self

    def build(self) -> str:
        """
        构建并返回 FloXML 字符串

        Returns:
            FloXML 字符串
        """
        lines = [
            '<?xml version="1.0" encoding="UTF-8"?>',
            '<floxml>',
            f'    <project name="{self._project_name}"/>',
            '',
            '    <attributes>',
        ]

        # 添加材料
        for mat in self._materials:
            lines.append(f'        <material_att name="{mat["name"]}">')
            lines.append(f'            <conductivity>{mat["conductivity"]}</conductivity>')
            if mat["density"]:
                lines.append(f'            <density>{mat["density"]}</density>')
            if mat["specific_heat"]:
                lines.append(f'            <specific_heat>{mat["specific_heat"]}</specific_heat>')
            lines.append('        </material_att>')

        # 添加 source 属性
        for geom in self._geometry:
            if geom.get("power"):
                lines.append(f'        <source_att name="{geom["name"]}_source">')
                lines.append(f'            <power>{geom["power"]}</power>')
                lines.append('        </source_att>')

        lines.append('    </attributes>')
        lines.append('')
        lines.append('    <geometry>')

        # 添加几何
        for geom in self._geometry:
            if geom["type"] == "cuboid":
                loc = geom["location"]
                lines.append(f'        <cuboid name="{geom["name"]}">')
                lines.append(f'            <location>{loc[0]} {loc[1]} {loc[2]}</location>')
                lines.append(f'            <size>{geom["x_size"]} {geom["y_size"]} {geom["z_size"]}</size>')
                if geom["material"]:
                    lines.append(f'            <material_att>{geom["material"]}</material_att>')
                if geom.get("power"):
                    lines.append(f'            <source_att>{geom["name"]}_source</source_att>')
                lines.append('        </cuboid>')

        lines.append('    </geometry>')

        # 添加求解域
        if self._solution_domain:
            sd = self._solution_domain
            lines.append('')
            lines.append('    <solution_domain>')
            lines.append(f'        <location>{sd["x"]} {sd["y"]} {sd["z"]}</location>')
            lines.append(f'        <size>{sd["dx"]} {sd["dy"]} {sd["dz"]}</size>')
            lines.append('    </solution_domain>')

        lines.append('</floxml>')

        return '\n'.join(lines)

    def save(self, file_path: str | Path) -> str:
        """
        保存到文件

        Args:
            file_path: 输出文件路径

        Returns:
            保存的文件路径
        """
        content = self.build()
        Path(file_path).write_text(content, encoding="utf-8")
        return str(file_path)

    def __repr__(self) -> str:
        return f"FloXMLCreator(project={self._project_name})"
