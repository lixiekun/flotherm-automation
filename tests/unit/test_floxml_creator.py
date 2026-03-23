"""
FloXML 项目创建器测试 (TDD)
"""

import pytest
import xml.etree.ElementTree as ET
from pathlib import Path


class TestFloXMLCreator:
    """FloXMLCreator 测试类"""

    def test_import_creator(self):
        """测试可以导入"""
        from floxml.creator import FloXMLCreator
        assert FloXMLCreator is not None

    def test_create_project(self):
        """测试创建项目"""
        from floxml.creator import FloXMLCreator

        creator = FloXMLCreator()
        creator.create_project("TestProject")
        xml = creator.build()

        assert "TestProject" in xml
        root = ET.fromstring(xml)
        assert root.tag == "floxml"

    def test_add_cuboid(self):
        """测试添加立方体"""
        from floxml.creator import FloXMLCreator

        creator = FloXMLCreator()
        creator.create_project("Test")
        creator.add_cuboid("Block1", x=0.1, y=0.1, z=0.02, material="Aluminum", power=10.0)
        xml = creator.build()

        assert "Block1" in xml
        assert "0.1" in xml
        assert "Aluminum" in xml

    def test_add_material(self):
        """测试添加材料"""
        from floxml.creator import FloXMLCreator

        creator = FloXMLCreator()
        creator.create_project("Test")
        creator.add_material("Copper", conductivity=385.0)
        xml = creator.build()

        assert "Copper" in xml
        assert "385" in xml

    def test_set_solution_domain(self):
        """测试设置求解域"""
        from floxml.creator import FloXMLCreator

        creator = FloXMLCreator()
        creator.create_project("Test")
        creator.set_solution_domain(x=0, y=0, z=0, dx=0.5, dy=0.5, dz=0.5)
        xml = creator.build()

        assert "solution_domain" in xml

    def test_build_returns_valid_xml(self):
        """测试返回有效 XML"""
        from floxml.creator import FloXMLCreator

        creator = FloXMLCreator()
        creator.create_project("Test")
        xml = creator.build()

        # 验证可解析
        root = ET.fromstring(xml)
        assert root is not None

    def test_save_to_file(self, temp_dir: Path):
        """测试保存到文件"""
        from floxml.creator import FloXMLCreator

        creator = FloXMLCreator()
        creator.create_project("Test")
        output_path = temp_dir / "test.xml"
        creator.save(output_path)

        assert output_path.exists()
        content = output_path.read_text(encoding="utf-8")
        assert "floxml" in content
