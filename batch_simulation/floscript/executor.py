"""
FloTHERM 执行器

执行 FloSCRIPT 脚本并监控执行状态。

Usage:
    executor = FlothermExecutor()
    executor.flotherm_path = executor.auto_detect_path()
    success, elapsed, msg = executor.execute("script.xml")
"""

from __future__ import annotations

import os
import subprocess
import time
from pathlib import Path
from typing import List, Optional, Tuple


class FlothermExecutorError(Exception):
    """执行器错误"""
    pass


class FlothermExecutor:
    """
    FloTHERM 执行器

    执行 FloSCRIPT 脚本并监控执行状态。

    Example:
        executor = FlothermExecutor()
        success, elapsed, msg = executor.execute("simulation.xml")
    """

    # 可能的 FloTHERM 安装路径
    POSSIBLE_PATHS = [
        Path(r"D:\Program Files\Siemens\SimcenterFlotherm\2504\WinXP\bin\flotherm.exe"),
        Path(r"C:\Program Files\Siemens\SimcenterFlotherm\2504\WinXP\bin\flotherm.exe"),
        Path(r"C:\Program Files\Siemens\SimcenterFlotherm\2020.2\bin\flotherm.exe"),
        Path(r"C:\Program Files\Siemens\SimcenterFlotherm\2410\bin\flotherm.exe"),
        Path(r"C:\Program Files\Mentor Graphics\FloTHERM\v2020.2\flosuite\bin\flotherm.exe"),
    ]

    def __init__(self, flotherm_path: str | Path = None):
        """
        初始化执行器

        Args:
            flotherm_path: FloTHERM 可执行文件路径（可选）
        """
        self._flotherm_path: Optional[Path] = None
        if flotherm_path:
            self._flotherm_path = Path(flotherm_path)

    @property
    def flotherm_path(self) -> Optional[Path]:
        """FloTHERM 可执行文件路径"""
        return self._flotherm_path

    @flotherm_path.setter
    def flotherm_path(self, value: str | Path):
        self._flotherm_path = Path(value)

    def get_possible_paths(self) -> List[Path]:
        """
        获取可能的安装路径列表

        Returns:
            可能的路径列表
        """
        return self.POSSIBLE_PATHS.copy()

    def auto_detect_path(self) -> Optional[Path]:
        """
        自动检测 FloTHERM 安装路径

        Returns:
            找到的路径，如果未找到返回 None
        """
        for path in self.POSSIBLE_PATHS:
            if path.exists():
                self._flotherm_path = path
                return path
        return None

    def _build_command(self, script_path: Path) -> List[str]:
        """
        构建执行命令

        Args:
            script_path: 脚本文件路径

        Returns:
            命令参数列表
        """
        return [
            str(self._flotherm_path),
            "-b",
            "-f",
            str(script_path)
        ]

    def execute(self, script_path: str | Path,
                timeout: int = 3600,
                skip_path_check: bool = False) -> Tuple[bool, float, str]:
        """
        执行 FloSCRIPT 脚本

        Args:
            script_path: 脚本文件路径
            timeout: 超时时间（秒）
            skip_path_check: 跳过路径存在性检查（用于测试）

        Returns:
            (success, elapsed_time, message) 元组

        Raises:
            FileNotFoundError: 脚本文件不存在
        """
        script_path = Path(script_path)

        # 验证脚本存在
        if not script_path.exists():
            raise FileNotFoundError(f"Script file not found: {script_path}")

        # 检查 FloTHERM 路径
        if not self._flotherm_path:
            detected = self.auto_detect_path()
            if not detected:
                return False, 0, "FloTHERM not found. Please set flotherm_path."

        if not skip_path_check and not self._flotherm_path.exists():
            return False, 0, f"FloTHERM not found at: {self._flotherm_path}"

        # 构建命令
        cmd = self._build_command(script_path)

        # 执行
        start_time = time.time()

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout
            )

            elapsed = time.time() - start_time

            if result.returncode == 0:
                return True, elapsed, "Success"
            else:
                error_msg = result.stderr[:500] if result.stderr else f"Return code: {result.returncode}"
                return False, elapsed, error_msg

        except subprocess.TimeoutExpired:
            elapsed = time.time() - start_time
            return False, elapsed, f"Timeout ({timeout} seconds)"

        except Exception as e:
            elapsed = time.time() - start_time
            return False, elapsed, str(e)

    def __repr__(self) -> str:
        path_str = str(self._flotherm_path) if self._flotherm_path else "Not set"
        return f"FlothermExecutor(path={path_str})"
