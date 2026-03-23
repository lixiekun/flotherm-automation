#!/usr/bin/env python3
"""
Solve Editor - 求解配置编辑器

编辑 FloXML 中的 <solve> 部分，包括：
- 最大迭代次数
- 收敛标准
- 求解器选项
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING, Optional

from .base_editor import BaseEditor

if TYPE_CHECKING:
    from ..pack_manager import PackManager


class SolveEditor(BaseEditor):
    """
    Solve 配置编辑器

    Usage:
        pack = PackManager("model.pack")
        pack.extract()

        pack.solve.set_iterations(1000)
        pack.solve.set_convergence(1e-4)

        pack.save()
    """

    def __init__(self, manager: "PackManager"):
        super().__init__(manager)
        self._max_iterations: Optional[int] = None
        self._convergence: Optional[float] = None
        self._parallel_threads: Optional[int] = None

    def load(self) -> None:
        """加载 Solve 配置"""
        content = self._read_floxml()
        if not content:
            return

        # 提取最大迭代次数
        match = re.search(r'<solve\s+[^>]*max_iterations="(\d+)"', content)
        if match:
            self._max_iterations = int(match.group(1))

        # 提取收敛标准
        match = re.search(r'<solve\s+[^>]*convergence="([^"]+)"', content)
        if match:
            try:
                self._convergence = float(match.group(1))
            except ValueError:
                pass

    def save(self) -> None:
        """保存 Solve 配置"""
        if not self._modified:
            return

        content = self._read_floxml()
        if not content:
            return

        # 更新最大迭代次数
        if self._max_iterations is not None:
            if 'max_iterations=' in content:
                content = re.sub(
                    r'(max_iterations=")\d+(")',
                    f'\\g<1>{self._max_iterations}\\g<2>',
                    content
                )
            else:
                # 添加属性
                content = re.sub(
                    r'(<solve\s+)',
                    f'\\g<1>max_iterations="{self._max_iterations}" ',
                    content
                )

        # 更新收敛标准
        if self._convergence is not None:
            if 'convergence=' in content:
                content = re.sub(
                    r'(convergence=")[^"]+(")',
                    f'\\g<1>{self._convergence}\\g<2>',
                    content
                )
            else:
                content = re.sub(
                    r'(<solve\s+)',
                    f'\\g<1>convergence="{self._convergence}" ',
                    content
                )

        self._write_floxml(content)
        self._modified = False

    # ==================== API ====================

    def get_iterations(self) -> Optional[int]:
        """获取最大迭代次数"""
        self.ensure_loaded()
        return self._max_iterations

    def set_iterations(self, iterations: int) -> None:
        """
        设置最大迭代次数

        Args:
            iterations: 最大迭代次数
        """
        self.ensure_loaded()
        self._max_iterations = iterations
        self.mark_modified()

    def get_convergence(self) -> Optional[float]:
        """获取收敛标准"""
        self.ensure_loaded()
        return self._convergence

    def set_convergence(self, convergence: float) -> None:
        """
        设置收敛标准

        Args:
            convergence: 收敛标准值
        """
        self.ensure_loaded()
        self._convergence = convergence
        self.mark_modified()

    def get_parallel_threads(self) -> Optional[int]:
        """获取并行线程数"""
        self.ensure_loaded()
        return self._parallel_threads

    def set_parallel_threads(self, threads: int) -> None:
        """
        设置并行线程数

        Args:
            threads: 并行线程数
        """
        self.ensure_loaded()
        self._parallel_threads = threads
        self.mark_modified()
