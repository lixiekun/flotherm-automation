#!/usr/bin/env python3
"""
Batch Editor - 批量编辑器

批量修改多个 Pack 文件。

Usage:
    from pack_editor.batch import BatchEditor

    batch = BatchEditor(["model1.pack", "model2.pack"])
    batch.add_power_change("CPU", 25.0)
    batch.add_grid_change(grid_config)
    batch.execute(output_dir="./results/", parallel=4)
"""

from __future__ import annotations

import json
import shutil
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Dict, List, Optional, Union

from ..group_binary import CalibrationRule, GroupBinaryHandler


@dataclass
class PowerChange:
    """功耗修改配置"""
    component_name: str
    power: float


@dataclass
class BatchResult:
    """批量处理结果"""
    input_pack: Path
    output_pack: Optional[Path]
    success: bool
    error: Optional[str] = None
    changes: List[str] = field(default_factory=list)


class BatchEditor:
    """
    批量 Pack 编辑器

    支持批量修改多个 Pack 文件的功耗、网格等设置。
    """

    def __init__(self, pack_files: Optional[List[Union[str, Path]]] = None):
        """
        初始化批量编辑器

        Args:
            pack_files: Pack 文件列表
        """
        self.pack_files: List[Path] = []
        self.power_changes: List[PowerChange] = []
        self.calibration_rules: Dict[str, CalibrationRule] = {}
        self.grid_config: Optional[Dict] = None

        if pack_files:
            self.add_packs(pack_files)

    def add_pack(self, pack_path: Union[str, Path]) -> None:
        """添加 Pack 文件"""
        pack_path = Path(pack_path)
        if pack_path.exists():
            self.pack_files.append(pack_path)
        else:
            raise FileNotFoundError(f"Pack file not found: {pack_path}")

    def add_packs(self, pack_paths: List[Union[str, Path]]) -> None:
        """添加多个 Pack 文件"""
        for path in pack_paths:
            self.add_pack(path)

    def add_power_change(self, component_name: str, power: float) -> None:
        """
        添加功耗修改

        Args:
            component_name: 组件名称
            power: 功耗值 (W)
        """
        self.power_changes.append(PowerChange(component_name, power))

    def add_calibration_rule(self, component_name: str, rule: CalibrationRule) -> None:
        """
        添加校准规则

        Args:
            component_name: 组件名称
            rule: 校准规则
        """
        self.calibration_rules[component_name] = rule

    def load_calibration_rule(self, component_name: str, rule_path: Union[str, Path]) -> None:
        """
        从文件加载校准规则

        Args:
            component_name: 组件名称
            rule_path: 规则文件路径
        """
        rule = CalibrationRule.load(rule_path)
        self.calibration_rules[component_name] = rule

    def set_grid_config(self, config: Dict) -> None:
        """设置网格配置"""
        self.grid_config = config

    def execute(
        self,
        output_dir: Union[str, Path],
        naming: str = "suffix",
        parallel: int = 1,
        progress_callback: Optional[Callable[[int, int, str], None]] = None,
    ) -> List[BatchResult]:
        """
        执行批量处理

        Args:
            output_dir: 输出目录
            naming: 命名方式 ("suffix", "folder", "custom")
            parallel: 并行数
            progress_callback: 进度回调函数 (current, total, status)

        Returns:
            List[BatchResult]: 处理结果列表
        """
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        results: List[BatchResult] = []
        total = len(self.pack_files)

        if parallel > 1:
            with ThreadPoolExecutor(max_workers=parallel) as executor:
                futures = {}
                for idx, pack_path in enumerate(self.pack_files):
                    future = executor.submit(
                        self._process_single,
                        pack_path,
                        output_dir,
                        naming,
                    )
                    futures[future] = (idx, pack_path)

                for future in as_completed(futures):
                    idx, pack_path = futures[future]
                    try:
                        result = future.result()
                        results.append(result)

                        if progress_callback:
                            progress_callback(idx + 1, total, f"Processed {pack_path.name}")
                    except Exception as e:
                        results.append(BatchResult(
                            input_pack=pack_path,
                            output_pack=None,
                            success=False,
                            error=str(e),
                        ))
        else:
            for idx, pack_path in enumerate(self.pack_files):
                try:
                    result = self._process_single(pack_path, output_dir, naming)
                    results.append(result)

                    if progress_callback:
                        progress_callback(idx + 1, total, f"Processed {pack_path.name}")
                except Exception as e:
                    results.append(BatchResult(
                        input_pack=pack_path,
                        output_pack=None,
                        success=False,
                        error=str(e),
                    ))

        # 保存处理报告
        self._save_report(output_dir, results)

        return results

    def _process_single(
        self,
        pack_path: Path,
        output_dir: Path,
        naming: str,
    ) -> BatchResult:
        """处理单个 Pack 文件"""
        # 确定输出文件名
        if naming == "suffix":
            output_name = f"{pack_path.stem}_modified.pack"
        elif naming == "folder":
            output_name = pack_path.name
        else:
            output_name = f"{pack_path.stem}_modified.pack"

        output_path = output_dir / output_name
        changes: List[str] = []

        try:
            # 复制原文件
            shutil.copy2(pack_path, output_path)

            # 应用功耗修改
            if self.power_changes:
                handler = GroupBinaryHandler()

                for change in self.power_changes:
                    if change.component_name in self.calibration_rules:
                        rule = self.calibration_rules[change.component_name]
                        temp_path = output_path.with_suffix(".tmp")
                        handler.apply_rule(output_path, rule, change.power, temp_path)
                        temp_path.rename(output_path)
                        changes.append(f"Power: {change.component_name} = {change.power}W")

            return BatchResult(
                input_pack=pack_path,
                output_pack=output_path,
                success=True,
                changes=changes,
            )

        except Exception as e:
            return BatchResult(
                input_pack=pack_path,
                output_pack=None,
                success=False,
                error=str(e),
            )

    def _save_report(self, output_dir: Path, results: List[BatchResult]) -> None:
        """保存处理报告"""
        report_path = output_dir / "batch_report.json"

        report = {
            "total": len(results),
            "success": sum(1 for r in results if r.success),
            "failed": sum(1 for r in results if not r.success),
            "results": [
                {
                    "input_pack": str(r.input_pack),
                    "output_pack": str(r.output_pack) if r.output_pack else None,
                    "success": r.success,
                    "error": r.error,
                    "changes": r.changes,
                }
                for r in results
            ],
        }

        report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
