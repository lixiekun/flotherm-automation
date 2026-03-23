#!/usr/bin/env python3
"""
Base Editor - 编辑器基类

所有 Pack 编辑器的基类，提供通用功能。
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict, Optional

if TYPE_CHECKING:
    from ..pack_manager import PackManager


class BaseEditor(ABC):
    """
    编辑器基类

    子类需要实现:
        - load(): 从解压目录加载数据
        - save(): 保存修改到解压目录
    """

    def __init__(self, manager: "PackManager"):
        """
        初始化编辑器

        Args:
            manager: PackManager 实例
        """
        self.manager = manager
        self._loaded = False
        self._modified = False
        self._data: Dict[str, Any] = {}

    @property
    def extract_dir(self) -> Optional[Path]:
        """获取解压目录"""
        if self.manager.extracted:
            return self.manager.extracted.extract_dir
        return None

    @property
    def is_loaded(self) -> bool:
        """是否已加载"""
        return self._loaded

    @property
    def is_modified(self) -> bool:
        """是否已修改"""
        return self._modified

    def ensure_loaded(self) -> None:
        """确保数据已加载"""
        if not self._loaded:
            self.load()
            self._loaded = True

    def mark_modified(self) -> None:
        """标记为已修改"""
        self._modified = True

    @abstractmethod
    def load(self) -> None:
        """从解压目录加载数据"""
        pass

    @abstractmethod
    def save(self) -> None:
        """保存修改到解压目录"""
        pass

    def _find_floxml(self) -> Optional[Path]:
        """查找 FloXML 文件"""
        if not self.extract_dir:
            return None

        # 优先使用缓存的路径
        if self.manager.extracted and self.manager.extracted.floxml_path:
            return self.manager.extracted.floxml_path

        # 搜索 .floxml 或 .xml 文件
        for ext in [".floxml", ".xml"]:
            for f in self.extract_dir.rglob(f"*{ext}"):
                # 跳过 results_state_file.xml
                if "results_state_file" in f.name:
                    continue
                if self.manager.extracted:
                    self.manager.extracted.floxml_path = f
                return f

        return None

    def _read_floxml(self) -> Optional[str]:
        """读取 FloXML 内容"""
        floxml_path = self._find_floxml()
        if floxml_path and floxml_path.exists():
            return floxml_path.read_text(encoding="utf-8")
        return None

    def _write_floxml(self, content: str) -> None:
        """写入 FloXML 内容"""
        floxml_path = self._find_floxml()
        if floxml_path:
            floxml_path.write_text(content, encoding="utf-8")
        else:
            raise FileNotFoundError("No FloXML file found in extracted pack")
