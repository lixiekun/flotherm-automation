"""
结果提取器测试 (TDD)
"""

import pytest
import zipfile
import tempfile
from pathlib import Path


class TestResultExtractor:
    """ResultExtractor 测试类"""

    @pytest.fixture
    def sample_pack_with_results(self, temp_dir: Path) -> Path:
        """创建包含结果的示例 pack 文件"""
        pack_path = temp_dir / "test_results.pack"

        with zipfile.ZipFile(pack_path, 'w') as zf:
            # 创建基本结构
            zf.writestr("Project.GUID/", "")
            zf.writestr("Project.GUID/PDProject/", "")
            zf.writestr("Project.GUID/PDProject/group", b"test data")
            zf.writestr("Project.GUID/PDProject/results_state_file.xml",
                       '<?xml version="1.0"?><results><temp value="85.5"/></results>')
            zf.writestr("Project.GUID/DataSets/", "")
            zf.writestr("Project.GUID/DataSets/BaseSolution/", "")
            zf.writestr("Project.GUID/DataSets/BaseSolution/grid", b"grid data")

        return pack_path

    def test_import_extractor(self):
        """测试可以导入"""
        from results.extractor import ResultExtractor
        assert ResultExtractor is not None

    def test_load_pack(self, sample_pack_with_results: Path):
        """测试加载 pack 文件"""
        from results.extractor import ResultExtractor

        extractor = ResultExtractor(sample_pack_with_results)
        assert extractor is not None

    def test_extract_results_state(self, sample_pack_with_results: Path):
        """测试提取结果状态"""
        from results.extractor import ResultExtractor

        extractor = ResultExtractor(sample_pack_with_results)
        results = extractor.extract_results_state()

        assert results is not None
        assert "temp" in results or "results" in str(results).lower()

    def test_get_temperature_data(self, sample_pack_with_results: Path):
        """测试获取温度数据"""
        from results.extractor import ResultExtractor

        extractor = ResultExtractor(sample_pack_with_results)
        temps = extractor.get_temperatures()

        # 应该返回列表或字典
        assert temps is not None

    def test_export_to_json(self, sample_pack_with_results: Path, temp_dir: Path):
        """测试导出为 JSON"""
        from results.extractor import ResultExtractor

        extractor = ResultExtractor(sample_pack_with_results)
        output_path = temp_dir / "results.json"
        extractor.export_json(output_path)

        assert output_path.exists()

    def test_pack_not_found_raises_error(self, temp_dir: Path):
        """测试 pack 文件不存在时抛出错误"""
        from results.extractor import ResultExtractor

        non_existent = temp_dir / "not_found.pack"
        with pytest.raises(FileNotFoundError):
            ResultExtractor(non_existent)
