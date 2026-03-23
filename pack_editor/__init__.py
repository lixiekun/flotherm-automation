#!/usr/bin/env python3
"""
Pack Editor - FloTHERM Pack 文件编辑器

提供 Pack 文件的解压、编辑、打包功能。

Usage:
    from pack_editor import PackManager

    # 打开 Pack 文件
    pack = PackManager("model.pack")

    # 解压到目录
    pack.extract("./extracted/")

    # 编辑内容
    pack.model.set_ambient_temperature(308.15)
    pack.geometry.set_cuboid_power("CPU", 25.0)

    # 保存
    pack.save()
    pack.pack("modified.pack")

    # 二进制校准模式
    from pack_editor import GroupBinaryHandler, CalibrationRule

    handler = GroupBinaryHandler()
    rule = handler.calibrate("baseline.pack", "calibrated.pack",
                              "CPU", 10.0, 20.0)
    rule.save("rule.json")

    handler.apply_rule("baseline.pack", rule, 15.0, "output.pack")

    # 批量处理 (Phase 4)
    from pack_editor.batch import BatchEditor, ExcelBatchDriver

    batch = BatchEditor(["model1.pack", "model2.pack"])
    batch.add_power_change("CPU", 25.0)
    batch.execute("./results/", parallel=4)

    driver = ExcelBatchDriver("template.pack", "cases.xlsx")
    driver.run("./results/")
"""

from __future__ import annotations

from .pack_manager import PackManager
from .pack_inspector import PackInspector
from .data.pack_structure import PackEntry, PackStructure
from .group_binary import GroupBinaryHandler, CalibrationRule

__version__ = "0.3.0"
__all__ = [
    "PackManager",
    "PackInspector",
    "PackEntry",
    "PackStructure",
    "GroupBinaryHandler",
    "CalibrationRule",
]
