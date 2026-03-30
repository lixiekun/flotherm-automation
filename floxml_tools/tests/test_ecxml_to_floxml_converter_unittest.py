#!/usr/bin/env python3
import tempfile
import textwrap
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

from floxml_tools.ecxml_to_floxml_converter import ECXMLToFloXMLConverter


SAMPLE_ECXML = textwrap.dedent(
    """\
    <?xml version="1.0" encoding="UTF-8"?>
    <ecxml:ThermalModel xmlns:ecxml="http://www.jedec.org/ecxml" name="DemoBoard">
        <ecxml:Component name="CPU_Package">
            <ecxml:Position x="0.05" y="0.05" z="0.0" />
            <ecxml:Geometry>
                <ecxml:Size width="0.04" height="0.04" depth="0.002" />
            </ecxml:Geometry>
            <ecxml:Material name="Copper" />
            <ecxml:powerDissipation>12.5</ecxml:powerDissipation>
        </ecxml:Component>
        <ecxml:Component name="GPU_Package">
            <ecxml:Position x="0.1" y="0.05" z="0.0" />
            <ecxml:Size width="0.03" height="0.03" depth="0.0015" />
            <ecxml:Material name="Aluminum" />
            <ecxml:Power>8.0</ecxml:Power>
        </ecxml:Component>
        <ecxml:Device name="DDR_Memory">
            <ecxml:Position x="0.02" y="0.1" z="0.0" />
            <ecxml:Geometry>
                <ecxml:Size width="0.08" height="0.015" depth="0.001" />
            </ecxml:Geometry>
            <ecxml:power>3.25</ecxml:power>
        </ecxml:Device>
    </ecxml:ThermalModel>
    """
)


class ECXMLToFloXMLConverterTests(unittest.TestCase):
    def test_convert_builds_expected_project_sections(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            input_path = tmp_path / "sample.ecxml"
            output_path = tmp_path / "nested" / "sample_floxml.xml"
            input_path.write_text(SAMPLE_ECXML, encoding="utf-8")

            converter = ECXMLToFloXMLConverter()
            result = converter.convert(input_path, output_path)

            self.assertTrue(result["success"], result["errors"])
            self.assertEqual(result["components"], 3)
            self.assertTrue(output_path.exists())

            root = ET.parse(output_path).getroot()
            self.assertEqual(root.tag, "xml_case")
            self.assertEqual(root.findtext("name"), "DemoBoard_Project")
            self.assertIsNotNone(root.find("model"))
            self.assertIsNotNone(root.find("solve"))
            self.assertIsNotNone(root.find("grid"))
            self.assertIsNotNone(root.find("solution_domain"))

            geometry = root.find("geometry")
            self.assertIsNotNone(geometry)
            assembly = geometry.find("assembly")
            self.assertIsNotNone(assembly)
            self.assertEqual(assembly.findtext("name"), "DemoBoard_Assembly")
            self.assertEqual(assembly.findtext("active"), "true")
            self.assertEqual(assembly.findtext("ignore"), "false")
            self.assertEqual(assembly.findtext("material"), "Default")
            self.assertEqual(assembly.findtext("localized_grid"), "false")
            self.assertIsNotNone(assembly.find("orientation"))

            assembly_geometry = assembly.find("geometry")
            self.assertIsNotNone(assembly_geometry)
            cuboids = assembly_geometry.findall("cuboid")
            self.assertEqual(len(cuboids), 3)

            first = cuboids[0]
            self.assertEqual(first.findtext("name"), "CPU_Package")
            self.assertEqual(first.find("size").findtext("x"), "0.04")
            self.assertEqual(first.find("size").findtext("y"), "0.04")
            self.assertEqual(first.find("size").findtext("z"), "0.002")
            self.assertEqual(first.findtext("material"), "Copper")
            self.assertEqual(first.findtext("source"), "CPU_Package_Source")

            sources = root.find("attributes").find("sources").findall("source_att")
            source_map = {source.findtext("name"): source.findtext("power") for source in sources}
            self.assertEqual(
                source_map,
                {
                    "CPU_Package_Source": "12.5",
                    "GPU_Package_Source": "8",
                    "DDR_Memory_Source": "3.25",
                },
            )

            domain = root.find("solution_domain")
            self.assertEqual(domain.findtext("fluid"), "Air")
            self.assertEqual(domain.findtext("x_low_ambient"), "Ambient")
            self.assertIsNotNone(domain.find("position"))
            self.assertIsNotNone(domain.find("size"))

    def test_write_floxml_falls_back_when_indent_is_unavailable(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            input_path = tmp_path / "sample.ecxml"
            output_path = tmp_path / "fallback.xml"
            input_path.write_text(SAMPLE_ECXML, encoding="utf-8")

            converter = ECXMLToFloXMLConverter()
            original_indent = ET.indent

            def missing_indent(*args, **kwargs):
                raise AttributeError("indent unavailable")

            ET.indent = missing_indent
            try:
                result = converter.convert(input_path, output_path)
            finally:
                ET.indent = original_indent

            self.assertTrue(result["success"], result["errors"])
            content = output_path.read_text(encoding="utf-8")
            self.assertIn("\n    <name>DemoBoard_Project</name>\n", content)
            self.assertIn("\n        <assembly>\n", content)
            self.assertIn("\n                <cuboid>\n", content)


if __name__ == "__main__":
    unittest.main()
