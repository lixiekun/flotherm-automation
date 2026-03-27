from pathlib import Path
import xml.etree.ElementTree as ET

from ecxml_to_floxml_converter import ECXMLExtractor, ECXMLToFloXMLConverter


REPO_ROOT = Path(__file__).resolve().parents[2]
SAMPLE_ECXML = REPO_ROOT / "all.ecxml"


def test_extractor_parses_source2dblock_and_monitor_points():
    data = ECXMLExtractor(str(SAMPLE_ECXML)).extract_all()

    assert [source.name for source in data.sources] == ["Source-1"]
    assert [mp.name for mp in data.monitor_points] == ["MP-01", "Probe1", "Probe2", "Probe3"]


def test_converter_outputs_complete_project_with_sources_and_monitors(tmp_path):
    output_path = tmp_path / "converted.xml"

    result = ECXMLToFloXMLConverter().convert(SAMPLE_ECXML, output_path)

    assert result["success"], result["errors"]

    root = ET.parse(output_path).getroot()

    assert root.find("model") is not None
    assert root.find("solve") is not None
    assert root.find("grid") is not None
    assert root.find("solution_domain") is not None

    geometry = root.find("geometry")
    assert geometry is not None
    assert geometry.find("source") is not None

    monitor_points = geometry.findall("monitor_point")
    assert len(monitor_points) == 4

    source_attributes = root.findall("./attributes/sources/source_att")
    assert len(source_attributes) >= 1
