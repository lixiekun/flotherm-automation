#!/usr/bin/env python3
"""
Domain Editor - Solution Domain 编辑器

编辑 FloXML 中的 <solution_domain> 部分，包括：
- 计算域尺寸
- 计算域位置
- 边界条件设置
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING, Dict, Optional

from .base_editor import BaseEditor

if TYPE_CHECKING:
    from ..pack_manager import PackManager


class DomainEditor(BaseEditor):
    """
    Solution Domain 编辑器

    Usage:
        pack = PackManager("model.pack")
        pack.extract()

        pack.domain.set_size(0.1, 0.1, 0.05)
        pack.domain.set_origin(0, 0, 0)

        pack.save()
    """

    def __init__(self, manager: "PackManager"):
        super().__init__(manager)
        self._size: Dict[str, float] = {}
        self._origin: Dict[str, float] = {}
        self._boundaries: Dict[str, str] = {}

    def load(self) -> None:
        """加载 Solution Domain"""
        content = self._read_floxml()
        if not content:
            return

        # 提取尺寸
        match = re.search(
            r'<solution_domain\s+[^>]*x_size="([^"]+)"[^>]*y_size="([^"]+)"[^>]*z_size="([^"]+)"',
            content
        )
        if match:
            self._size = {
                "x_size": float(match.group(1)),
                "y_size": float(match.group(2)),
                "z_size": float(match.group(3)),
            }

        # 提取原点
        match = re.search(
            r'<solution_domain\s+[^>]*x_origin="([^"]+)"[^>]*y_origin="([^"]+)"[^>]*z_origin="([^"]+)"',
            content
        )
        if match:
            self._origin = {
                "x_origin": float(match.group(1)),
                "y_origin": float(match.group(2)),
                "z_origin": float(match.group(3)),
            }

    def save(self) -> None:
        """保存 Solution Domain"""
        if not self._modified:
            return

        content = self._read_floxml()
        if not content:
            return

        # 更新尺寸
        for dim in ["x_size", "y_size", "z_size"]:
            if dim in self._size:
                pattern = rf'(<solution_domain\s+[^>]*{dim}=")[^"]+(")'
                if re.search(pattern, content):
                    content = re.sub(
                        pattern,
                        f'\\g<1>{self._size[dim]}\\g<2>',
                        content
                    )

        # 更新原点
        for dim in ["x_origin", "y_origin", "z_origin"]:
            if dim in self._origin:
                pattern = rf'(<solution_domain\s+[^>]*{dim}=")[^"]+(")'
                if re.search(pattern, content):
                    content = re.sub(
                        pattern,
                        f'\\g<1>{self._origin[dim]}\\g<2>',
                        content
                    )

        self._write_floxml(content)
        self._modified = False

    # ==================== API ====================

    def get_size(self) -> Optional[Dict[str, float]]:
        """获取计算域尺寸"""
        self.ensure_loaded()
        return self._size.copy() if self._size else None

    def set_size(self, x_size: float, y_size: float, z_size: float) -> None:
        """
        设置计算域尺寸

        Args:
            x_size: X 方向尺寸 (m)
            y_size: Y 方向尺寸 (m)
            z_size: Z 方向尺寸 (m)
        """
        self.ensure_loaded()
        self._size = {
            "x_size": x_size,
            "y_size": y_size,
            "z_size": z_size,
        }
        self.mark_modified()

    def get_origin(self) -> Optional[Dict[str, float]]:
        """获取计算域原点"""
        self.ensure_loaded()
        return self._origin.copy() if self._origin else None

    def set_origin(self, x_origin: float, y_origin: float, z_origin: float) -> None:
        """
        设置计算域原点

        Args:
            x_origin: X 方向原点 (m)
            y_origin: Y 方向原点 (m)
            z_origin: Z 方向原点 (m)
        """
        self.ensure_loaded()
        self._origin = {
            "x_origin": x_origin,
            "y_origin": y_origin,
            "z_origin": z_origin,
        }
        self.mark_modified()

    def set_boundary(self, side: str, condition: str) -> None:
        """
        设置边界条件

        Args:
            side: 边界位置 (x_min, x_max, y_min, y_max, z_min, z_max)
            condition: 边界条件类型 (ambient, symmetry, wall)
        """
        self.ensure_loaded()
        self._boundaries[side] = condition
        self.mark_modified()
