import argparse
import copy
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Optional, Tuple
from xml.dom import minidom
import xml.etree.ElementTree as ET


SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from pdml_to_floxml_converter import FloXMLBuilder, PDMLBinaryReader, PDMLData, PDMLGeometryNode


@dataclass(frozen=True)
class GeometryVariant:
    key: str
    description: str
    position_window: Optional[Tuple[int, int, int, int]] = None
    size_window: Optional[Tuple[int, int, int, int]] = None
    cuboid_center_to_corner: bool = False


VARIANTS = (
    GeometryVariant(
        key="g1_baseline",
        description="Current converter behavior",
    ),
    GeometryVariant(
        key="g2_cuboid_center",
        description="Treat cuboid position as center point",
        cuboid_center_to_corner=True,
    ),
    GeometryVariant(
        key="g3_alt_windows",
        description="Use later candidate windows for generic position/size",
        position_window=(430, 490, 440, 470),
        size_window=(300, 360, 310, 340),
    ),
    GeometryVariant(
        key="g4_alt_windows_cuboid_center",
        description="Later candidate windows plus cuboid center point",
        position_window=(430, 490, 440, 470),
        size_window=(300, 360, 310, 340),
        cuboid_center_to_corner=True,
    ),
)


class VariantPDMLReader(PDMLBinaryReader):
    def __init__(self, filepath: str, variant: GeometryVariant):
        super().__init__(filepath)
        self.variant = variant

    def _extract_standard_position(self, base_offset: int) -> Tuple[float, float, float]:
        if self.variant.position_window is None:
            return super()._extract_standard_position(base_offset)
        start_scan, end_scan, rel_min, rel_max = self.variant.position_window
        doubles = self._read_relative_doubles(base_offset, start_scan, end_scan)
        values = self._pick_values(doubles, 3, rel_min=rel_min, rel_max=rel_max)
        if len(values) >= 3:
            return (values[0], values[1], values[2])
        return super()._extract_standard_position(base_offset)

    def _extract_standard_size(self, base_offset: int, dimensions: int = 3) -> Tuple[float, ...]:
        if self.variant.size_window is None:
            return super()._extract_standard_size(base_offset, dimensions)
        start_scan, end_scan, rel_min, rel_max = self.variant.size_window
        doubles = self._read_relative_doubles(base_offset, start_scan, end_scan)
        values = self._pick_values(
            doubles,
            dimensions,
            positive_only=False,
            allow_zero=True,
            rel_min=rel_min,
            rel_max=rel_max,
        )
        if len(values) >= dimensions:
            return tuple(values[:dimensions])
        return super()._extract_standard_size(base_offset, dimensions)


def _iter_nodes(nodes: Iterable[PDMLGeometryNode]) -> Iterable[PDMLGeometryNode]:
    for node in nodes:
        yield node
        if node.children:
            yield from _iter_nodes(node.children)


def _apply_cuboid_center_to_corner(root: PDMLGeometryNode):
    for node in _iter_nodes(root.children):
        if node.node_type != "cuboid" or node.size is None or len(node.size) < 3:
            continue
        node.position = tuple(
            node.position[i] - (node.size[i] / 2.0)
            for i in range(3)
        )


def _build_variant_data(input_path: Path, variant: GeometryVariant) -> PDMLData:
    reader = VariantPDMLReader(str(input_path), variant)
    data = reader.read()
    if variant.cuboid_center_to_corner and data.geometry is not None:
        _apply_cuboid_center_to_corner(data.geometry)
    return data


def _prettify(elem: ET.Element) -> str:
    rough_string = ET.tostring(elem, encoding="unicode")
    reparsed = minidom.parseString(rough_string)
    return reparsed.toprettyxml(indent="    ")


def generate_variants(input_path: Path, output_dir: Path):
    output_dir.mkdir(parents=True, exist_ok=True)

    for variant in VARIANTS:
        data = _build_variant_data(input_path, variant)
        builder = FloXMLBuilder()
        root = builder.build(copy.deepcopy(data))
        output_path = output_dir / f"{input_path.stem}.{variant.key}.xml"
        output_path.write_text(_prettify(root), encoding="utf-8")
        print(f"[OK] {variant.key}: {output_path}")
        print(f"     {variant.description}")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Generate multiple PDML geometry interpretation FloXML variants",
    )
    parser.add_argument("input", help="Input PDML file")
    parser.add_argument(
        "-o",
        "--output-dir",
        help="Output directory for generated FloXML variants",
    )
    args = parser.parse_args()

    input_path = Path(args.input)
    if not input_path.exists():
        print(f"[ERROR] Input file not found: {input_path}")
        return 1

    output_dir = (
        Path(args.output_dir)
        if args.output_dir
        else input_path.parent / f"{input_path.stem}_geometry_variants"
    )

    try:
        generate_variants(input_path, output_dir)
    except Exception as exc:
        print(f"[ERROR] {exc}")
        return 1

    print(f"[INFO] Generated {len(VARIANTS)} FloXML files in: {output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
