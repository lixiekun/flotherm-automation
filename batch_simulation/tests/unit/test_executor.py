"""
FloTHERM 执行器测试 (TDD)

测试 FlothermExecutor 类的功能。
"""

import pytest
import subprocess
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock


class TestFlothermExecutor:
    """FlothermExecutor 测试类"""

    # ==================== 导入和基础测试 ====================

    def test_import_executor(self):
        """测试 FlothermExecutor 可以导入"""
        from floscript.executor import FlothermExecutor
        assert FlothermExecutor is not None

    def test_create_executor_instance(self):
        """测试创建执行器实例"""
        from floscript.executor import FlothermExecutor
        executor = FlothermExecutor()
        assert executor is not None

    # ==================== 路径检测测试 ====================

    def test_auto_detect_path_returns_path_or_none(self):
        """测试自动检测返回路径或 None"""
        from floscript.executor import FlothermExecutor

        executor = FlothermExecutor()
        path = executor.auto_detect_path()

        # 应该返回 Path 对象或 None
        assert path is None or isinstance(path, Path)

    def test_custom_path(self):
        """测试设置自定义路径"""
        from floscript.executor import FlothermExecutor

        custom_path = r"D:\Custom\flotherm.exe"
        executor = FlothermExecutor(flotherm_path=custom_path)

        assert str(executor.flotherm_path) == custom_path

    def test_possible_paths(self):
        """测试可能的安装路径列表"""
        from floscript.executor import FlothermExecutor

        executor = FlothermExecutor()
        paths = executor.get_possible_paths()

        assert len(paths) > 0
        assert all(isinstance(p, Path) for p in paths)

    # ==================== 执行测试（使用 Mock）====================

    def test_execute_calls_subprocess(self, temp_dir: Path):
        """测试 execute 调用 subprocess"""
        from floscript.executor import FlothermExecutor

        # 创建测试脚本
        script_path = temp_dir / "test.xml"
        script_path.write_text('<?xml version="1.0"?><xml_log_file version="1.0"></xml_log_file>')

        executor = FlothermExecutor()
        executor.flotherm_path = Path("flotherm.exe")  # 设置假路径

        with patch.object(subprocess, 'run') as mock_run:
            mock_run.return_value = Mock(returncode=0, stderr="", stdout="")

            success, elapsed, msg = executor.execute(script_path, skip_path_check=True)

            # 验证 subprocess.run 被调用
            assert mock_run.called
            # 验证命令参数
            call_args = mock_run.call_args[0][0]
            assert "-b" in call_args
            assert "-f" in call_args
            assert str(script_path) in call_args

    def test_execute_success_returns_true(self, temp_dir: Path):
        """测试执行成功返回 True"""
        from floscript.executor import FlothermExecutor

        script_path = temp_dir / "test.xml"
        script_path.write_text('<?xml version="1.0"?><xml_log_file version="1.0"></xml_log_file>')

        executor = FlothermExecutor()
        executor.flotherm_path = Path("flotherm.exe")

        with patch.object(subprocess, 'run') as mock_run:
            mock_run.return_value = Mock(returncode=0, stderr="", stdout="")

            success, elapsed, msg = executor.execute(script_path, skip_path_check=True)

            assert success is True
            assert elapsed >= 0

    def test_execute_failure_returns_false(self, temp_dir: Path):
        """测试执行失败返回 False"""
        from floscript.executor import FlothermExecutor

        script_path = temp_dir / "test.xml"
        script_path.write_text('<?xml version="1.0"?><xml_log_file version="1.0"></xml_log_file>')

        executor = FlothermExecutor()
        executor.flotherm_path = Path("flotherm.exe")

        with patch.object(subprocess, 'run') as mock_run:
            mock_run.return_value = Mock(returncode=1, stderr="Error", stdout="")

            success, elapsed, msg = executor.execute(script_path, skip_path_check=True)

            assert success is False
            assert "Error" in msg or "1" in msg

    def test_execute_timeout(self, temp_dir: Path):
        """测试执行超时"""
        from floscript.executor import FlothermExecutor

        script_path = temp_dir / "test.xml"
        script_path.write_text('<?xml version="1.0"?><xml_log_file version="1.0"></xml_log_file>')

        executor = FlothermExecutor()
        executor.flotherm_path = Path("flotherm.exe")

        with patch.object(subprocess, 'run') as mock_run:
            mock_run.side_effect = subprocess.TimeoutExpired(cmd="flotherm", timeout=10)

            success, elapsed, msg = executor.execute(script_path, timeout=10, skip_path_check=True)

            assert success is False
            assert "timeout" in msg.lower() or "超时" in msg

    # ==================== 命令构建测试 ====================

    def test_build_command(self, temp_dir: Path):
        """测试构建命令"""
        from floscript.executor import FlothermExecutor

        executor = FlothermExecutor()
        executor.flotherm_path = Path("flotherm.exe")

        script_path = temp_dir / "test.xml"
        script_path.write_text("test")

        cmd = executor._build_command(script_path)

        assert cmd[0] == "flotherm.exe"
        assert "-b" in cmd
        assert "-f" in cmd
        assert str(script_path) in cmd

    # ==================== 脚本验证测试 ====================

    def test_execute_validates_script_exists(self, temp_dir: Path):
        """测试验证脚本文件存在"""
        from floscript.executor import FlothermExecutor

        executor = FlothermExecutor()
        non_existent = temp_dir / "not_found.xml"

        with pytest.raises(FileNotFoundError):
            executor.execute(non_existent)
