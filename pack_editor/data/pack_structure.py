#!/usr/bin/env python3
"""
Pack 文件结构数据类

定义 Pack 文件的内部结构表示。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional
import zipfile


@dataclass
class PackEntry:
    """Pack 文件中的单个条目"""

    name: str  # 条目名称 (相对路径)
    full_path: str  # ZIP 内完整路径
    size: int  # 原始大小 (bytes)
    compressed_size: int = 0  # 压缩后大小

    # 内容 (延迟加载)
    is_binary: bool = False
    content: Optional[bytes] = None
    text_content: Optional[str] = None

    # ZIP 元信息
    compress_type: int = zipfile.ZIP_STORED
    date_time: Optional[tuple] = None

    @property
    def is_text(self) -> bool:
        """是否为文本文件"""
        return not self.is_binary

    @property
    def extension(self) -> str:
        """文件扩展名"""
        return Path(self.name).suffix.lower()

    def load_content(self, zip_file: zipfile.ZipFile) -> None:
        """从 ZIP 文件加载内容"""
        self.content = zip_file.read(self.full_path)
        if not self.is_binary:
            try:
                self.text_content = self.content.decode("utf-8")
            except UnicodeDecodeError:
                try:
                    self.text_content = self.content.decode("latin-1")
                except:
                    self.is_binary = True

    def __repr__(self) -> str:
        return f"PackEntry({self.name}, {self.size} bytes)"


@dataclass
class PackStructure:
    """Pack 文件的完整结构"""

    # 根目录前缀 (如 "ProjectName.GUID")
    root_prefix: str = ""

    # 所有条目 (按相对路径索引)
    entries: Dict[str, PackEntry] = field(default_factory=dict)

    # 核心条目引用 (方便快速访问)
    group: Optional[PackEntry] = None
    group_bak: Optional[PackEntry] = None
    results_state_file: Optional[PackEntry] = None

    # 数据集
    solution_cat: Optional[PackEntry] = None
    base_solution_grid: Optional[PackEntry] = None
    base_solution_connectivity: Optional[PackEntry] = None

    # 元信息
    flotherm_version: str = ""
    project_name: str = ""
    project_guid: str = ""

    @property
    def has_group(self) -> bool:
        """是否包含 group 文件"""
        return self.group is not None

    @property
    def has_base_solution(self) -> bool:
        """是否包含求解结果"""
        return self.base_solution_grid is not None

    def get_entry(self, name: str) -> Optional[PackEntry]:
        """按名称获取条目"""
        return self.entries.get(name)

    def list_entries(self, pattern: str = "*") -> List[PackEntry]:
        """列出匹配的条目"""
        from fnmatch import fnmatch

        return [e for e in self.entries.values() if fnmatch(e.name, pattern)]

    def summarize(self) -> Dict:
        """返回结构摘要"""
        return {
            "root_prefix": self.root_prefix,
            "project_name": self.project_name,
            "flotherm_version": self.flotherm_version,
            "total_entries": len(self.entries),
            "has_group": self.has_group,
            "has_solution": self.has_base_solution,
            "binary_files": sum(1 for e in self.entries.values() if e.is_binary),
            "text_files": sum(1 for e in self.entries.values() if e.is_text),
        }


@dataclass
class ExtractedPack:
    """解压后的 Pack 目录"""

    source_pack: Optional[Path] = None
    extract_dir: Path = Path(".")
    structure: Optional[PackStructure] = None

    # 核心文件路径
    group_path: Optional[Path] = None
    grid_path: Optional[Path] = None
    floxml_path: Optional[Path] = None  # 如果存在

    def validate(self) -> bool:
        """验证目录结构是否有效"""
        if not self.extract_dir.exists():
            return False

        # 检查必要的文件
        if self.group_path and not self.group_path.exists():
            return False

        return True

    def find_floxml(self) -> Optional[Path]:
        """查找解压目录中的 FloXML 文件"""
        if self.floxml_path and self.floxml_path.exists():
            return self.floxml_path

        # 搜索 .floxml 文件
        for f in self.extract_dir.rglob("*.floxml"):
            self.floxml_path = f
            return f

        return None
