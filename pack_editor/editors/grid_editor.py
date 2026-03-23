#!/usr/bin/env python3
"""
Grid Editor - 网格配置编辑器

编辑 FloXML 中的 <grid> 部分，包括：
- System Grid
- Grid Patches
- Grid Constraints
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING, Dict, List, Optional

from .base_editor import BaseEditor

if TYPE_CHECKING:
    from ..pack_manager import PackManager


class GridEditor(BaseEditor):
    """
    Grid 配置编辑器

    Usage:
        pack = PackManager("model.pack")
        pack.extract()

        pack.grid.set_system_grid(x_size=0.002, y_size=0.002, z_size=0.001)
        pack.grid.add_patch("CPU", x_size=0.001)

        pack.save()
    """

    def __init__(self, manager: "PackManager"):
        super().__init__(manager)
        self._system_grid: Dict[str, float] = {}
        self._patches: List[Dict] = []
        self._constraints: List[Dict] = []

    def load(self) -> None:
        """加载 Grid 配置"""
        content = self._read_floxml()
        if not content:
            return

        # 提取 System Grid
        match = re.search(
            r'<system_grid\s+[^>]*x_size="([^"]+)"[^>]*y_size="([^"]+)"[^>]*z_size="([^"]+)"',
            content
        )
        if match:
            self._system_grid = {
                "x_size": float(match.group(1)),
                "y_size": float(match.group(2)),
                "z_size": float(match.group(3)),
            }

        # 提取 Grid Patches
        self._patches = []
        for match in re.finditer(
            r'<grid_patch\s+[^>]*name="([^"]+)"[^>]*x_size="([^"]+)"[^>]*y_size="([^"]+)"[^>]*z_size="([^"]+)"',
            content
        ):
            self._patches.append({
                "name": match.group(1),
                "x_size": float(match.group(2)),
                "y_size": float(match.group(3)),
                "z_size": float(match.group(4)),
            })

        # 提取 Grid Constraints
        self._constraints = []
        for match in re.finditer(
            r'<grid_constraint\s+[^>]*applies_to="([^"]+)"[^>]*/>',
            content
        ):
            self._constraints.append({
                "applies_to": match.group(1),
            })

    def save(self) -> None:
        """保存 Grid 配置"""
        if not self._modified:
            return

        content = self._read_floxml()
        if not content:
            return

        # 更新 System Grid
        if self._system_grid:
            x = self._system_grid.get("x_size", 0.01)
            y = self._system_grid.get("y_size", 0.01)
            z = self._system_grid.get("z_size", 0.01)

            if '<system_grid' in content:
                content = re.sub(
                    r'(<system_grid\s+[^>]*x_size=")[^"]+(")',
                    f'\\g<1>{x}\\g<2>',
                    content
                )
                content = re.sub(
                    r'(<system_grid\s+[^>]*y_size=")[^"]+(")',
                    f'\\g<1>{y}\\g<2>',
                    content
                )
                content = re.sub(
                    r'(<system_grid\s+[^>]*z_size=")[^"]+(")',
                    f'\\g<1>{z}\\g<2>',
                    content
                )

        self._write_floxml(content)
        self._modified = False

    # ==================== API ====================

    def get_system_grid(self) -> Optional[Dict[str, float]]:
        """获取 System Grid 设置"""
        self.ensure_loaded()
        return self._system_grid.copy() if self._system_grid else None

    def set_system_grid(self, x_size: float, y_size: float, z_size: float) -> None:
        """
        设置 System Grid

        Args:
            x_size: X 方向网格尺寸 (m)
            y_size: Y 方向网格尺寸 (m)
            z_size: Z 方向网格尺寸 (m)
        """
        self.ensure_loaded()
        self._system_grid = {
            "x_size": x_size,
            "y_size": y_size,
            "z_size": z_size,
        }
        self.mark_modified()

    def get_patches(self) -> List[Dict]:
        """获取 Grid Patches"""
        self.ensure_loaded()
        return self._patches.copy()

    def add_patch(self, name: str, x_size: float, y_size: float, z_size: float) -> None:
        """
        添加 Grid Patch

        Args:
            name: Patch 名称
            x_size: X 方向网格尺寸 (m)
            y_size: Y 方向网格尺寸 (m)
            z_size: Z 方向网格尺寸 (m)
        """
        self.ensure_loaded()
        self._patches.append({
            "name": name,
            "x_size": x_size,
            "y_size": y_size,
            "z_size": z_size,
        })
        self.mark_modified()

    def get_constraints(self) -> List[Dict]:
        """获取 Grid Constraints"""
        self.ensure_loaded()
        return self._constraints.copy()

    def apply_config(self, config: Dict) -> None:
        """
        应用网格配置

        Args:
            config: 网格配置字典，包含 system_grid, patches, constraints
        """
        self.ensure_loaded()

        if "system_grid" in config:
            sg = config["system_grid"]
            self.set_system_grid(
                sg.get("x_size", 0.01),
                sg.get("y_size", 0.01),
                sg.get("z_size", 0.01),
            )

        if "patches" in config:
            for patch in config["patches"]:
                self.add_patch(
                    patch["name"],
                    patch.get("x_size", 0.01),
                    patch.get("y_size", 0.01),
                    patch.get("z_size", 0.01),
                )
