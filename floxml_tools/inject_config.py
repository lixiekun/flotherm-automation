#!/usr/bin/env python3
"""
FloXML 属性注入工具

通过 JSON 配置文件向已有 FloXML 注入缺失的属性定义和属性分配。

支持的注入内容：
  - 属性定义: surfaces, surface_exchanges, radiations, resistances,
    fans, thermals, transients, advanced materials
  - 属性分配: 将 surface / radiation / thermal 等引用设置到 geometry 元素上
  - Volume regions / grid constraints (委托 floxml_add_volume_regions)

用法：
  # 注入到已有 FloXML
  python -m floxml_tools.inject_config target.xml --config my_config.json -o output.xml

  # 原地修改（覆盖原文件）
  python -m floxml_tools.inject_config target.xml --config my_config.json --in-place

  # ECXML → FloXML + 注入（一步到位）
  python -m floxml_tools.inject_config --ecxml model.ecxml --config my_config.json -o output.xml
"""

from __future__ import annotations

import argparse
import os
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Optional
from xml.dom import minidom


def _save_xml(root: ET.Element, output_path: str) -> None:
    """保存 XML 文件（带格式化）"""
    rough_string = ET.tostring(root, encoding='unicode')
    reparsed = minidom.parseString(rough_string)
    pretty_xml = reparsed.toprettyxml(indent="    ")
    lines = [line for line in pretty_xml.split('\n') if line.strip()]
    pretty_xml = '\n'.join(lines)

    os.makedirs(os.path.dirname(output_path) or '.', exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(pretty_xml)


def inject_config(target_path: str, config_path: str, output_path: str,
                  verbose: bool = False) -> None:
    """
    从 JSON 配置注入属性到已有 FloXML。

    Args:
        target_path: 目标 FloXML 文件路径
        config_path: JSON 配置文件路径
        output_path: 输出文件路径
        verbose: 详细输出
    """
    # 读取目标 FloXML
    tree = ET.parse(target_path)
    root = tree.getroot()
    print(f"[OK] 已读取 FloXML: {target_path}")

    # 注入
    from .config_injector import ConfigInjector
    injector = ConfigInjector(config_path)
    injector.inject(root)

    # 保存
    _save_xml(root, output_path)
    print(f"[OK] 已输出: {output_path}")


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        description="通过 JSON 配置向 FloXML 注入属性定义和属性分配",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 注入到已有 FloXML
  python -m floxml_tools.inject_config target.xml --config attrs.json -o output.xml

  # 原地修改
  python -m floxml_tools.inject_config target.xml --config attrs.json --in-place

  # ECXML → FloXML + 注入（一步到位）
  python -m floxml_tools.inject_config --ecxml model.ecxml --config attrs.json -o output.xml
        """
    )

    # 输入源（二选一）
    parser.add_argument("target", nargs='?', type=Path, default=None,
                        help="目标 FloXML 文件。使用 --ecxml 时可省略")
    parser.add_argument("--ecxml", type=Path,
                        help="ECXML 输入文件（自动转换后再注入）")

    # 必须指定 JSON 配置
    parser.add_argument("--config", type=Path, required=True,
                        help="统一 JSON 配置文件路径")

    # 输出
    parser.add_argument("-o", "--output", type=Path, default=None,
                        help="输出 FloXML 文件路径")
    parser.add_argument("--in-place", action="store_true",
                        help="原地修改目标文件（与 -o 互斥）")

    # ECXML 转换参数
    parser.add_argument("--padding-ratio", type=float, default=0.1,
                        help="ECXML 转换 padding 比例 (默认: 0.1)")
    parser.add_argument("--ambient-temp", type=float, default=300.0,
                        help="环境温度 K (默认: 300)")

    parser.add_argument("-v", "--verbose", action="store_true",
                        help="详细输出")

    args = parser.parse_args(list(argv) if argv else None)

    # 验证参数
    if args.in_place and args.output:
        parser.error("--in-place 和 -o 不能同时使用")

    if not args.ecxml and not args.target:
        parser.error("需要指定 target 或使用 --ecxml 参数")

    if not args.in_place and not args.output:
        parser.error("需要指定 -o 输出路径或使用 --in-place")

    target_path = args.target

    # 如果指定了 --ecxml，先转换
    if args.ecxml:
        from .ecxml_to_floxml_converter import (ECXMLExtractor, FloXMLBuilder,
                                                 ConversionConfig)
        config = ConversionConfig(
            padding_ratio=args.padding_ratio,
            ambient_temp=args.ambient_temp,
        )
        extractor = ECXMLExtractor(str(args.ecxml))
        ecxml_data = extractor.extract_all()
        builder = FloXMLBuilder(config)
        root = builder.build_project(ecxml_data)

        tmp_path = str(args.output or args.target) + ".tmp"
        _save_xml(root, tmp_path)
        target_path = Path(tmp_path)
        print(f"[OK] ECXML 已转换为 FloXML")

    # 确定输出路径
    if args.in_place:
        output_path = str(target_path)
    else:
        output_path = str(args.output)

    # 执行注入
    inject_config(
        target_path=str(target_path),
        config_path=str(args.config),
        output_path=output_path,
        verbose=args.verbose,
    )

    # 清理临时文件
    if args.ecxml and target_path != args.target:
        os.remove(str(target_path))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
