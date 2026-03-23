#!/usr/bin/env python3
"""
Model Editor - 模型设置编辑器

编辑 FloXML 中的 <model> 部分，包括：
- 环境温度
- 重力方向
- 气压
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING, Optional, Tuple

from .base_editor import BaseEditor

if TYPE_CHECKING:
    from ..pack_manager import PackManager


class ModelEditor(BaseEditor):
    """
    Model 设置编辑器

    Usage:
        pack = PackManager("model.pack")
        pack.extract()

        # 设置环境温度
        pack.model.set_ambient_temperature(308.15)  # Kelvin

        # 设置重力方向
        pack.model.set_gravity("neg_y", 9.81)

        pack.save()
    """

    # 重力方向映射
    GRAVITY_MAP = {
        "pos_x": ("1", "0", "0"),
        "neg_x": ("-1", "0", "0"),
        "pos_y": ("0", "1", "0"),
        "neg_y": ("0", "-1", "0"),
        "pos_z": ("0", "0", "1"),
        "neg_z": ("0", "0", "-1"),
    }

    def __init__(self, manager: "PackManager"):
        super().__init__(manager)
        self._ambient_temp: Optional[float] = None
        self._gravity_dir: Optional[str] = None
        self._gravity_mag: Optional[float] = None
        self._pressure: Optional[float] = None

    def load(self) -> None:
        """加载 Model 设置"""
        content = self._read_floxml()
        if not content:
            return

        # 提取环境温度
        match = re.search(r'<ambient\s+[^>]*temperature="([^"]+)"', content)
        if match:
            try:
                self._ambient_temp = float(match.group(1))
            except ValueError:
                pass

        # 提取重力
        match = re.search(
            r'<gravity\s+[^>]*x_direction="([^"]+)"[^>]*y_direction="([^"]+)"[^>]*z_direction="([^"]+)"',
            content
        )
        if match:
            x, y, z = match.groups()
            # 判断方向
            if x == "1":
                self._gravity_dir = "pos_x"
            elif x == "-1":
                self._gravity_dir = "neg_x"
            elif y == "1":
                self._gravity_dir = "pos_y"
            elif y == "-1":
                self._gravity_dir = "neg_y"
            elif z == "1":
                self._gravity_dir = "pos_z"
            elif z == "-1":
                self._gravity_dir = "neg_z"

    def save(self) -> None:
        """保存 Model 设置"""
        if not self._modified:
            return

        content = self._read_floxml()
        if not content:
            return

        # 更新环境温度
        if self._ambient_temp is not None:
            content = re.sub(
                r'(<ambient\s+[^>]*temperature=")[^"]+(")',
                f'\\g<1>{self._ambient_temp}\\g<2>',
                content
            )

        # 更新重力
        if self._gravity_dir is not None and self._gravity_dir in self.GRAVITY_MAP:
            x, y, z = self.GRAVITY_MAP[self._gravity_dir]
            content = re.sub(
                r'(<gravity\s+[^>]*x_direction=")[^"]+(")',
                f'\\g<1>{x}\\g<2>',
                content
            )
            content = re.sub(
                r'(<gravity\s+[^>]*y_direction=")[^"]+(")',
                f'\\g<1>{y}\\g<2>',
                content
            )
            content = re.sub(
                r'(<gravity\s+[^>]*z_direction=")[^"]+(")',
                f'\\g<1>{z}\\g<2>',
                content
            )

        # 更新气压
        if self._pressure is not None:
            content = re.sub(
                r'(<ambient\s+[^>]*pressure=")[^"]+(")',
                f'\\g<1>{self._pressure}\\g<2>',
                content
            )

        self._write_floxml(content)
        self._modified = False

    # ==================== API ====================

    def get_ambient_temperature(self) -> Optional[float]:
        """获取环境温度 (Kelvin)"""
        self.ensure_loaded()
        return self._ambient_temp

    def set_ambient_temperature(self, temp: float) -> None:
        """
        设置环境温度

        Args:
            temp: 温度值 (Kelvin)
        """
        self.ensure_loaded()
        self._ambient_temp = temp
        self.mark_modified()

    def get_gravity(self) -> Optional[Tuple[str, float]]:
        """获取重力设置 (方向, 大小)"""
        self.ensure_loaded()
        if self._gravity_dir:
            return (self._gravity_dir, self._gravity_mag or 9.81)
        return None

    def set_gravity(self, direction: str, magnitude: float = 9.81) -> None:
        """
        设置重力方向

        Args:
            direction: 方向 (pos_x, neg_x, pos_y, neg_y, pos_z, neg_z)
            magnitude: 大小 (m/s²), 默认 9.81
        """
        self.ensure_loaded()

        if direction not in self.GRAVITY_MAP:
            raise ValueError(f"Invalid gravity direction: {direction}")

        self._gravity_dir = direction
        self._gravity_mag = magnitude
        self.mark_modified()

    def get_pressure(self) -> Optional[float]:
        """获取气压 (Pa)"""
        self.ensure_loaded()
        return self._pressure

    def set_pressure(self, pressure: float) -> None:
        """
        设置气压

        Args:
            pressure: 气压值 (Pa)
        """
        self.ensure_loaded()
        self._pressure = pressure
        self.mark_modified()
