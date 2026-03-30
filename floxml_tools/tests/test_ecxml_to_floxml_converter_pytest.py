from pathlib import Path
import xml.etree.ElementTree as ET

from floxml_tools.ecxml_to_floxml_converter import ECXMLExtractor, ECXMLToFloXMLConverter


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


def test_extractor_and_converter_handle_nested_assembly_sources_and_monitors(tmp_path):
    ecxml_path = tmp_path / "nested.ecxml"
    ecxml_path.write_text(
        """<?xml version="1.0" encoding="UTF-8"?>
<neutralXML>
  <name>Nested Test</name>
  <geometry>
    <assembly>
      <name>RootAsm</name>
      <active>true</active>
      <location><x>0</x><y>0</y><z>0</z></location>
      <geometry>
        <sourceBlock>
          <name>NestedSource</name>
          <active>true</active>
          <location><x>1</x><y>2</y><z>3</z></location>
          <size><x>4</x><y>5</y><z>6</z></size>
          <powerDissipation>7</powerDissipation>
        </sourceBlock>
        <monitorPoint>
          <name>NestedMP</name>
          <active>true</active>
          <location><x>8</x><y>9</y><z>10</z></location>
        </monitorPoint>
      </geometry>
    </assembly>
  </geometry>
</neutralXML>
""",
        encoding="utf-8",
    )

    data = ECXMLExtractor(str(ecxml_path)).extract_all()
    assert data.root_assembly is not None
    assert [source.name for source in data.root_assembly.sources] == ["NestedSource"]
    assert [mp.name for mp in data.root_assembly.monitor_points] == ["NestedMP"]

    output_path = tmp_path / "nested.xml"
    result = ECXMLToFloXMLConverter().convert(ecxml_path, output_path)
    assert result["success"], result["errors"]

    root = ET.parse(output_path).getroot()
    assert root.find("./geometry/assembly/geometry/source") is not None
    assert root.find("./geometry/assembly/geometry/monitor_point") is not None
    assert root.find("./attributes/sources/source_att/name").text == "NestedSource_Source"
