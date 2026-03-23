#!/usr/bin/env python3
"""
Attributes Editor - 属性编辑器

编辑 FloXML 中的 <attributes> 部分，包括：
- Sources (热源)
- Materials (材质)
- Boundary Conditions (边界条件)
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING, Dict, List, Optional

from .base_editor import BaseEditor

if TYPE_CHECKING:
    from ..pack_manager import PackManager


class AttributesEditor(BaseEditor):
    """
    Attributes 编辑器

    Usage:
        pack = PackManager("model.pack")
        pack.extract()

        pack.attributes.set_source_power("CPU_Source", 25.0)
        pack.attributes.set_material_property("Aluminum", "conductivity", 200.0)

        pack.save()
    """

    def __init__(self, manager: "PackManager"):
        super().__init__(manager)
        self._sources: Dict[str, Dict] = {}
        self._materials: Dict[str, Dict] = {}
        self._boundary_conditions: Dict[str, Dict] = {}

    def load(self) -> None:
        """加载 Attributes"""
        content = self._read_floxml()
        if not content:
            return

        # 提取 Sources
        self._sources = {}
        for match in re.finditer(
            r'<source\s+[^>]*name="([^"]+)"[^>]*power="([^"]+)"',
            content
        ):
            name = match.group(1)
            try:
                power = float(match.group(2))
                self._sources[name] = {"power": power}
            except ValueError:
                pass

        # 提取 Materials
        self._materials = {}
        for match in re.finditer(
            r'<material\s+[^>]*name="([^"]+)"[^>]*conductivity="([^"]+)"',
            content
        ):
            name = match.group(1)
            try:
                conductivity = float(match.group(2))
                self._materials[name] = {"conductivity": conductivity}
            except ValueError:
                pass

    def save(self) -> None:
        """保存 Attributes"""
        if not self._modified:
            return

        content = self._read_floxml()
        if not content:
            return

        # 更新 Sources
        for name, attrs in self._sources.items():
            if "power" in attrs:
                # 匹配 source 标签并更新 power
                pattern = rf'(<source\s+[^>]*name="{re.escape(name)}"[^>]*power=")[^"]+(")'
                content = re.sub(
                    pattern,
                    f'\\g<1>{attrs["power"]}\\g<2>',
                    content
                )

        self._write_floxml(content)
        self._modified = False

    # ==================== API ====================

    def list_sources(self) -> List[str]:
        """列出所有热源"""
        self.ensure_loaded()
        return list(self._sources.keys())

    def get_source_power(self, name: str) -> Optional[float]:
        """获取热源功耗"""
        self.ensure_loaded()
        if name in self._sources:
            return self._sources[name].get("power")
        return None

    def set_source_power(self, name: str, power: float) -> None:
        """
        设置热源功耗

        Args:
            name: 热源名称
            power: 功耗值 (W)
        """
        self.ensure_loaded()
        if name not in self._sources:
            self._sources[name] = {}
        self._sources[name]["power"] = power
        self.mark_modified()

    def list_materials(self) -> List[str]:
        """列出所有材质"""
        self.ensure_loaded()
        return list(self._materials.keys())

    def get_material(self, name: str) -> Optional[Dict]:
        """获取材质属性"""
        self.ensure_loaded()
        return self._materials.get(name)

    def set_material_property(self, name: str, property_name: str, value: float) -> None:
        """
        设置材质属性

        Args:
            name: 材质名称
            property_name: 属性名 (conductivity, density, specific_heat)
            value: 属性值
        """
        self.ensure_loaded()
        if name not in self._materials:
            self._materials[name] = {}
        self._materials[name][property_name] = value
        self.mark_modified()

    def list_boundary_conditions(self) -> List[str]:
        """列出所有边界条件"""
        self.ensure_loaded()
        return list(self._boundary_conditions.keys())

    def get_boundary_condition(self, name: str) -> Optional[Dict]:
        """获取边界条件"""
        self.ensure_loaded()
        return self._boundary_conditions.get(name)

    def set_boundary_temperature(self, name: str, temperature: float) -> None:
        """
        设置边界条件温度

        Args:
            name: 边界条件名称
            temperature: 温度值 (K)
        """
        self.ensure_loaded()
        if name not in self._boundary_conditions:
            self._boundary_conditions[name] = {}
        self._boundary_conditions[name]["temperature"] = temperature
        self.mark_modified()
