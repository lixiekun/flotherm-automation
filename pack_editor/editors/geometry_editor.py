#!/usr/bin/env python3
"""
Geometry Editor - 几何编辑器

编辑 FloXML 中的 <geometry> 部分，包括：
- Cuboids (长方体)
- Assemblies (装配体)
- Heatsinks (散热器)
- Fans (风扇)
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING, Dict, List, Optional

from .base_editor import BaseEditor

if TYPE_CHECKING:
    from ..pack_manager import PackManager


class GeometryEditor(BaseEditor):
    """
    Geometry 编辑器

    Usage:
        pack = PackManager("model.pack")
        pack.extract()

        pack.geometry.set_cuboid_power("CPU", 25.0)
        pack.geometry.set_cuboid_material("Heatsink", "Aluminum")
        pack.geometry.set_cuboid_size("CPU", 0.01, 0.01, 0.002)

        pack.save()
    """

    def __init__(self, manager: "PackManager"):
        super().__init__(manager)
        self._cuboids: Dict[str, Dict] = {}
        self._assemblies: Dict[str, Dict] = {}

    def load(self) -> None:
        """加载 Geometry"""
        content = self._read_floxml()
        if not content:
            return

        # 提取 Cuboids
        self._cuboids = {}
        for match in re.finditer(
            r'<cuboid\s+[^>]*name="([^"]+)"[^>]*material="([^"]+)"',
            content
        ):
            name = match.group(1)
            material = match.group(2)

            # 提取尺寸
            size_match = re.search(
                r'x_size="([^"]+)"[^>]*y_size="([^"]+)"[^>]*z_size="([^"]+)"',
                match.group(0)
            )

            self._cuboids[name] = {
                "material": material,
                "x_size": float(size_match.group(1)) if size_match else None,
                "y_size": float(size_match.group(2)) if size_match else None,
                "z_size": float(size_match.group(3)) if size_match else None,
            }

        # 提取关联的 Source
        for match in re.finditer(
            r'<cuboid\s+[^>]*name="([^"]+)"[^>]*source="([^"]+)"',
            content
        ):
            name = match.group(1)
            source = match.group(2)
            if name in self._cuboids:
                self._cuboids[name]["source"] = source

    def save(self) -> None:
        """保存 Geometry"""
        if not self._modified:
            return

        content = self._read_floxml()
        if not content:
            return

        # 更新 Cuboids
        for name, attrs in self._cuboids.items():
            # 更新材质
            if "material" in attrs:
                pattern = rf'(<cuboid\s+[^>]*name="{re.escape(name)}"[^>]*material=")[^"]+(")'
                if re.search(pattern, content):
                    content = re.sub(
                        pattern,
                        f'\\g<1>{attrs["material"]}\\g<2>',
                        content
                    )

            # 更新尺寸
            for dim in ["x_size", "y_size", "z_size"]:
                if attrs.get(dim) is not None:
                    pattern = rf'(<cuboid\s+[^>]*name="{re.escape(name)}"[^>]*{dim}=")[^"]+(")'
                    if re.search(pattern, content):
                        content = re.sub(
                            pattern,
                            f'\\g<1>{attrs[dim]}\\g<2>',
                            content
                        )

        self._write_floxml(content)
        self._modified = False

    # ==================== API ====================

    def list_cuboids(self) -> List[str]:
        """列出所有 Cuboid"""
        self.ensure_loaded()
        return list(self._cuboids.keys())

    def get_cuboid(self, name: str) -> Optional[Dict]:
        """获取 Cuboid 信息"""
        self.ensure_loaded()
        return self._cuboids.get(name)

    def set_cuboid_power(self, name: str, power: float) -> None:
        """
        设置 Cuboid 功耗

        实际上是设置关联的 Source 的功耗

        Args:
            name: Cuboid 名称
            power: 功耗值 (W)
        """
        self.ensure_loaded()

        # 查找关联的 source
        if name in self._cuboids:
            source_name = self._cuboids[name].get("source", f"{name}_Source")
            self.manager.attributes.set_source_power(source_name, power)
        else:
            # 尝试直接使用名称作为 source
            self.manager.attributes.set_source_power(name, power)

    def set_cuboid_material(self, name: str, material: str) -> None:
        """
        设置 Cuboid 材质

        Args:
            name: Cuboid 名称
            material: 材质名称
        """
        self.ensure_loaded()
        if name not in self._cuboids:
            self._cuboids[name] = {}
        self._cuboids[name]["material"] = material
        self.mark_modified()

    def set_cuboid_size(self, name: str, x_size: float, y_size: float, z_size: float) -> None:
        """
        设置 Cuboid 尺寸

        Args:
            name: Cuboid 名称
            x_size: X 方向尺寸 (m)
            y_size: Y 方向尺寸 (m)
            z_size: Z 方向尺寸 (m)
        """
        self.ensure_loaded()
        if name not in self._cuboids:
            self._cuboids[name] = {}
        self._cuboids[name]["x_size"] = x_size
        self._cuboids[name]["y_size"] = y_size
        self._cuboids[name]["z_size"] = z_size
        self.mark_modified()

    def list_assemblies(self) -> List[str]:
        """列出所有 Assembly"""
        self.ensure_loaded()
        return list(self._assemblies.keys())

    def get_assembly(self, name: str) -> Optional[Dict]:
        """获取 Assembly 信息"""
        self.ensure_loaded()
        return self._assemblies.get(name)
