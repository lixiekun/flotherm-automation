#!/usr/bin/env python3
"""
Pack Manager - Pack 文件管理器

提供 Pack 文件的解压、打包、编辑功能。
"""

from __future__ import annotations

import shutil
import tempfile
import zipfile
from pathlib import Path
from typing import Dict, List, Optional, Union

from .data.pack_structure import PackEntry, PackStructure, ExtractedPack


class PackManagerError(Exception):
    """Pack 管理器错误"""
    pass


class PackManager:
    """
    Pack 文件管理器

    提供 Pack 文件的解压、打包、编辑功能。

    Usage:
        pack = PackManager("model.pack")
        pack.extract("./extracted/")
        pack.save()
        pack.pack("modified.pack")
    """

    # 二进制文件扩展名
    BINARY_EXTENSIONS = {
        ".pack", ".bin", ".lck", ".derprop",
    }

    # 文本文件扩展名
    TEXT_EXTENSIONS = {
        ".xml", ".floxml", ".cat", ".grid", ".pdml",
    }

    def __init__(self, pack_path: Optional[Union[str, Path]] = None):
        """
        初始化 Pack 管理器

        Args:
            pack_path: Pack 文件路径 (可选)
        """
        self.pack_path = Path(pack_path) if pack_path else None
        self.structure: Optional[PackStructure] = None
        self.extracted: Optional[ExtractedPack] = None

        # 编辑器 (Phase 2 实现)
        self._model_editor = None
        self._solve_editor = None
        self._grid_editor = None
        self._attributes_editor = None
        self._geometry_editor = None
        self._domain_editor = None

        if self.pack_path and self.pack_path.exists():
            self._analyze_pack()

    # ==================== 解压/打包 ====================

    def extract(self, output_dir: Optional[Union[str, Path]] = None,
                overwrite: bool = False) -> Path:
        """
        解压 Pack 文件到目录

        Args:
            output_dir: 输出目录 (默认为 Pack 文件名去掉扩展名)
            overwrite: 是否覆盖已存在的目录

        Returns:
            解压后的目录路径
        """
        if not self.pack_path:
            raise PackManagerError("No pack file loaded")

        if not self.pack_path.exists():
            raise PackManagerError(f"Pack file not found: {self.pack_path}")

        # 确定输出目录
        if output_dir:
            output_dir = Path(output_dir)
        else:
            output_dir = self.pack_path.with_suffix("")

        # 检查目录是否存在
        if output_dir.exists():
            if overwrite:
                shutil.rmtree(output_dir)
            else:
                raise PackManagerError(f"Output directory already exists: {output_dir}")

        # 创建目录
        output_dir.mkdir(parents=True, exist_ok=True)

        # 解压
        with zipfile.ZipFile(self.pack_path, "r") as zf:
            zf.extractall(output_dir)

        # 记录解压信息
        self.extracted = ExtractedPack(
            source_pack=self.pack_path,
            extract_dir=output_dir,
            structure=self.structure,
        )

        # 查找关键文件路径
        self._locate_extracted_files()

        return output_dir

    def load_from_dir(self, dir_path: Union[str, Path]) -> None:
        """
        从已解压的目录加载

        Args:
            dir_path: 解压目录路径
        """
        dir_path = Path(dir_path)

        if not dir_path.exists():
            raise PackManagerError(f"Directory not found: {dir_path}")

        self.extracted = ExtractedPack(
            source_pack=None,
            extract_dir=dir_path,
        )

        self._locate_extracted_files()

    def pack(self, output_path: Optional[Union[str, Path]] = None,
             compression: int = zipfile.ZIP_STORED) -> Path:
        """
        将解压后的内容打包为 .pack 文件

        Args:
            output_path: 输出文件路径 (默认为原文件名或目录名)
            compression: 压缩方式 (默认不压缩，与 FloTHERM 一致)

        Returns:
            打包后的文件路径
        """
        if not self.extracted:
            raise PackManagerError("No extracted content to pack")

        # 确定输出路径
        if output_path:
            output_path = Path(output_path)
        elif self.pack_path:
            output_path = self.pack_path.with_name(
                f"{self.pack_path.stem}_new.pack"
            )
        else:
            output_path = self.extracted.extract_dir.with_suffix(".pack")

        # 确保 .pack 扩展名
        if output_path.suffix.lower() != ".pack":
            output_path = output_path.with_suffix(".pack")

        # 创建 pack 文件
        with zipfile.ZipFile(output_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
            # 收集所有目录（包括空目录）
            all_dirs = set()
            for file_path in self.extracted.extract_dir.rglob("*"):
                if file_path.is_dir():
                    arcname = file_path.relative_to(self.extracted.extract_dir)
                    all_dirs.add(str(arcname))

            # 先添加所有目录
            for dir_path in sorted(all_dirs):
                zf.write(self.extracted.extract_dir / dir_path, dir_path + "/",
                        compress_type=zipfile.ZIP_STORED)

            # 添加所有文件，保留原始压缩方式
            for file_path in self.extracted.extract_dir.rglob("*"):
                if file_path.is_file():
                    arcname = file_path.relative_to(self.extracted.extract_dir)
                    # 查找原始压缩方式
                    orig_compress = zipfile.ZIP_DEFLATED
                    if self.structure:
                        entry = self.structure.entries.get(str(arcname))
                        if entry:
                            orig_compress = entry.compress_type
                    zf.write(file_path, arcname, compress_type=orig_compress)

        return output_path

    def save(self) -> None:
        """保存修改到解压目录"""
        if not self.extracted:
            raise PackManagerError("No extracted content to save")

        # 触发所有编辑器保存
        for editor in [
            self._model_editor, self._solve_editor, self._grid_editor,
            self._attributes_editor, self._geometry_editor, self._domain_editor
        ]:
            if editor and hasattr(editor, 'save'):
                editor.save()

    # ==================== 信息获取 ====================

    def get_structure(self) -> PackStructure:
        """获取 Pack 文件结构"""
        if not self.structure:
            self._analyze_pack()
        return self.structure

    def info(self) -> Dict:
        """获取 Pack 文件信息摘要"""
        if not self.structure:
            self._analyze_pack()

        info = {
            "pack_path": str(self.pack_path) if self.pack_path else None,
            "extracted": self.extracted is not None,
            "extract_dir": str(self.extracted.extract_dir) if self.extracted else None,
        }

        if self.structure:
            info.update(self.structure.summarize())

        return info

    # ==================== 内部方法 ====================

    def _analyze_pack(self) -> None:
        """分析 Pack 文件结构"""
        if not self.pack_path or not self.pack_path.exists():
            return

        if not zipfile.is_zipfile(self.pack_path):
            raise PackManagerError(f"Not a valid pack file: {self.pack_path}")

        self.structure = PackStructure()

        with zipfile.ZipFile(self.pack_path, "r") as zf:
            # 获取根目录前缀
            names = zf.namelist()
            if names:
                first_name = names[0]
                if "/" in first_name:
                    self.structure.root_prefix = first_name.split("/")[0]

                # 解析项目名称和 GUID
                if "." in self.structure.root_prefix:
                    parts = self.structure.root_prefix.rsplit(".", 1)
                    if len(parts) == 2 and len(parts[1]) == 32:
                        self.structure.project_name = parts[0]
                        self.structure.project_guid = parts[1]

            # 分析所有条目
            for info in zf.infolist():
                if info.is_dir():
                    continue

                entry = self._create_entry(info)

                # 索引条目
                self.structure.entries[entry.name] = entry

                # 特殊条目引用
                self._link_special_entry(entry)

            # 提取 FloTHERM 版本
            self._extract_version()

    def _create_entry(self, info: zipfile.ZipInfo) -> PackEntry:
        """从 ZipInfo 创建 PackEntry"""
        # 计算相对名称
        full_path = info.filename
        if "/" in full_path:
            name = full_path.split("/", 1)[1] if "/" in full_path else full_path
        else:
            name = full_path

        # 判断文件类型
        ext = Path(name).suffix.lower()
        is_binary = ext in self.BINARY_EXTENSIONS or ext not in self.TEXT_EXTENSIONS

        return PackEntry(
            name=name,
            full_path=full_path,
            size=info.file_size,
            compressed_size=info.compress_size,
            is_binary=is_binary,
            compress_type=info.compress_type,
            date_time=info.date_time,
        )

    def _link_special_entry(self, entry: PackEntry) -> None:
        """链接特殊条目"""
        name = entry.name.lower()

        if name == "pdproject/group":
            self.structure.group = entry
        elif name == "pdproject/group.bak":
            self.structure.group_bak = entry
        elif name == "pdproject/results_state_file.xml":
            self.structure.results_state_file = entry
        elif name == "datasets/solution.cat":
            self.structure.solution_cat = entry
        elif name == "datasets/basesolution/grid":
            self.structure.base_solution_grid = entry
        elif name == "datasets/basesolution/connectivity":
            self.structure.base_solution_connectivity = entry

    def _extract_version(self) -> None:
        """从 group 文件提取 FloTHERM 版本"""
        if not self.structure or not self.structure.group:
            return

        try:
            with zipfile.ZipFile(self.pack_path, "r") as zf:
                content = zf.read(self.structure.group.full_path)
                # 第一行是版本信息
                first_line = content.split(b"\n")[0]
                self.structure.flotherm_version = first_line.decode(
                    "latin-1", errors="ignore"
                ).strip()
        except Exception:
            pass

    def _locate_extracted_files(self) -> None:
        """定位解压后的关键文件"""
        if not self.extracted:
            return

        # 查找 group 文件
        for f in self.extracted.extract_dir.rglob("group"):
            if f.parent.name == "PDProject":
                self.extracted.group_path = f
                break

        # 查找 grid 文件
        for f in self.extracted.extract_dir.rglob("grid"):
            if "BaseSolution" in str(f):
                self.extracted.grid_path = f
                break

        # 查找 FloXML 文件
        self.extracted.find_floxml()

    # ==================== 编辑器属性 (Phase 2) ====================

    @property
    def model(self):
        """获取 Model 编辑器"""
        if self._model_editor is None:
            from .editors.model_editor import ModelEditor
            self._model_editor = ModelEditor(self)
        return self._model_editor

    @property
    def solve(self):
        """获取 Solve 编辑器"""
        if self._solve_editor is None:
            from .editors.solve_editor import SolveEditor
            self._solve_editor = SolveEditor(self)
        return self._solve_editor

    @property
    def grid(self):
        """获取 Grid 编辑器"""
        if self._grid_editor is None:
            from .editors.grid_editor import GridEditor
            self._grid_editor = GridEditor(self)
        return self._grid_editor

    @property
    def attributes(self):
        """获取 Attributes 编辑器"""
        if self._attributes_editor is None:
            from .editors.attributes_editor import AttributesEditor
            self._attributes_editor = AttributesEditor(self)
        return self._attributes_editor

    @property
    def geometry(self):
        """获取 Geometry 编辑器"""
        if self._geometry_editor is None:
            from .editors.geometry_editor import GeometryEditor
            self._geometry_editor = GeometryEditor(self)
        return self._geometry_editor

    @property
    def domain(self):
        """获取 Domain 编辑器"""
        if self._domain_editor is None:
            from .editors.domain_editor import DomainEditor
            self._domain_editor = DomainEditor(self)
        return self._domain_editor

    # ==================== 上下文管理器 ====================

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        # 清理临时文件
        return False
