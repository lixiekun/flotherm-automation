#!/usr/bin/env python3
"""
PDML 二进制解析器

解析 FloTHERM PDML 二进制格式，提取模型设置。

已发现的编码:
- 头部: #FFFB V3.3 FloTHERM x.x\n
- 魔数: FF FB
- 浮点数: 0x06 + 8字节 Big-Endian double
- 字符串: 0x07 0x02 + 偏移(4B) + 长度(4B) + 字符串
- 块标记: 0x0A 0x01/0x02 开始, 0x01 0x00 0x00 0x00 结束
"""

import struct
import json
import sys
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Tuple


@dataclass
class PDMLValue:
    """PDML 值"""
    offset: int
    value: Any
    value_type: str


@dataclass
class PDMLFloat:
    """PDML 浮点数"""
    offset: int
    value: float


@dataclass
class PDMLString:
    """PDML 字符串"""
    offset: int
    value: str


class PDMLBinaryParser:
    """PDML 二进制解析器"""

    def __init__(self, filepath: str):
        self.filepath = filepath
        with open(filepath, 'rb') as f:
            self.data = f.read()

        self.floats: List[PDMLFloat] = []
        self.strings: List[PDMLString] = []
        self.structure: Dict[str, Any] = {}

    def parse(self) -> Dict[str, Any]:
        """解析 PDML 文件"""
        result = {
            'file': self.filepath,
            'header': self._parse_header(),
            'floats': [],
            'strings': [],
            'extracted': {}
        }

        # 解析浮点数
        self._extract_floats()
        result['floats'] = [
            {'offset': hex(f.offset), 'value': f.value}
            for f in self.floats
        ]

        # 解析字符串
        self._extract_strings()
        result['strings'] = [
            {'offset': hex(s.offset), 'value': s.value[:100]}
            for s in self.strings if len(s.value) > 3
        ]

        # 尝试提取已知字段
        result['extracted'] = self._extract_known_fields()

        return result

    def _parse_header(self) -> Dict[str, str]:
        """解析文件头部"""
        # 查找换行符
        newline_pos = self.data.find(b'\n')
        if newline_pos < 0:
            return {'error': 'Invalid PDML file'}

        header_line = self.data[:newline_pos].decode('ascii', errors='replace')
        parts = header_line.split()

        return {
            'format': parts[0] if len(parts) > 0 else '',
            'version': parts[1] if len(parts) > 1 else '',
            'product': ' '.join(parts[2:]) if len(parts) > 2 else ''
        }

    def _extract_floats(self):
        """提取所有浮点数 (0x06 + 8字节 BE double)"""
        pos = 0
        while pos < len(self.data) - 9:
            if self.data[pos] == 0x06:
                dbl_bytes = self.data[pos+1:pos+9]
                try:
                    value = struct.unpack('>d', dbl_bytes)[0]
                    # 过滤有效值
                    if -1e15 < value < 1e15 and abs(value) > 1e-15:
                        self.floats.append(PDMLFloat(pos, value))
                except:
                    pass
            pos += 1

    def _extract_strings(self):
        """提取所有字符串"""
        # 方法1: 查找 0x07 0x02 模式
        # 格式: 07 02 + offset(4B) + length(4B BE) + string
        pos = 0
        while pos < len(self.data) - 10:
            if self.data[pos:pos+2] == b'\x07\x02':
                # 读取偏移和长度 (使用大端序)
                if pos + 10 <= len(self.data):
                    offset_val = struct.unpack('>I', self.data[pos+2:pos+6])[0]
                    length = struct.unpack('>I', self.data[pos+6:pos+10])[0]

                    if 0 < length < 1000 and pos + 10 + length <= len(self.data):
                        str_data = self.data[pos+10:pos+10+length]
                        try:
                            value = str_data.decode('utf-8', errors='replace')
                            if value.strip():
                                self.strings.append(PDMLString(pos, value))
                        except:
                            pass
            pos += 1

        # 方法2: 查找连续可打印字符
        pos = 0
        while pos < len(self.data):
            if 32 <= self.data[pos] < 127:
                start = pos
                while pos < len(self.data) and 32 <= self.data[pos] < 127:
                    pos += 1
                length = pos - start
                if length >= 4:
                    try:
                        value = self.data[start:pos].decode('ascii')
                        # 避免重复
                        if not any(s.value == value for s in self.strings):
                            self.strings.append(PDMLString(start, value))
                    except:
                        pass
            else:
                pos += 1

    def _extract_known_fields(self) -> Dict[str, Any]:
        """提取已知字段"""
        extracted = {}

        # 字符串字段映射
        string_fields = {
            'gravity': 'gravity_direction',
            'modeldata': 'model_data',
            'overall control': 'solver_control',
            'grid smooth': 'grid_smoothing',
        }

        for s in self.strings:
            for key, field_name in string_fields.items():
                if key in s.value.lower():
                    if field_name not in extracted:
                        extracted[field_name] = []
                    extracted[field_name].append({
                        'offset': hex(s.offset),
                        'value': s.value
                    })

        # 浮点数字段映射 (基于上下文)
        float_fields = {
            (9.7, 9.9): 'gravity_value',
            (299, 301): 'ambient_temperature_300K',
            (100, 102): 'value_100',
            (499, 501): 'outer_iterations_500',
            (101320, 101330): 'datum_pressure',
        }

        for f in self.floats:
            for (low, high), field_name in float_fields.items():
                if low <= f.value <= high:
                    if field_name not in extracted:
                        extracted[field_name] = []
                    extracted[field_name].append({
                        'offset': hex(f.offset),
                        'value': f.value
                    })

        return extracted

    def extract_template(self) -> Dict[str, Any]:
        """
        提取模板配置

        尝试从 PDML 提取可用于 ECXML 转换的模板配置。
        """
        template = {
            'model': {
                'modeling': {
                    'solution': 'flow_heat',
                    'radiation': 'off',
                    'dimensionality': '3d',
                    'transient': False,
                },
                'gravity': {
                    'type': 'normal',
                    'normal_direction': 'neg_y',
                    'gravity_value': 9.81
                },
                'global': {
                    'datum_pressure': 101325,
                    'ambient_temperature': 300,
                }
            },
            'solve': {
                'overall_control': {
                    'outer_iterations': 500,
                }
            },
            'attributes': {
                'fluids': [{
                    'name': 'Air',
                    'conductivity': 0.0261,
                    'viscosity': 0.0000184,
                    'density': 1.16,
                    'specific_heat': 1008,
                }],
                'ambients': [{
                    'name': 'Ambient',
                    'temperature': 300,
                }]
            }
        }

        # 尝试从提取的数据更新模板
        extracted = self._extract_known_fields()

        # 更新 gravity
        if 'gravity_value' in extracted and extracted['gravity_value']:
            template['model']['gravity']['gravity_value'] = extracted['gravity_value'][0]['value']

        # 更新 outer_iterations
        if 'outer_iterations_500' in extracted and extracted['outer_iterations_500']:
            template['solve']['overall_control']['outer_iterations'] = int(
                extracted['outer_iterations_500'][0]['value']
            )

        # 更新 ambient_temperature
        if 'ambient_temperature_300K' in extracted and extracted['ambient_temperature_300K']:
            template['model']['global']['ambient_temperature'] = extracted['ambient_temperature_300K'][0]['value']
            template['attributes']['ambients'][0]['temperature'] = extracted['ambient_temperature_300K'][0]['value']

        return template

    def print_summary(self):
        """打印摘要"""
        result = self.parse()

        print("=" * 70)
        print(f"PDML 解析结果: {self.filepath}")
        print("=" * 70)

        print(f"\n[头部]")
        for k, v in result['header'].items():
            print(f"  {k}: {v}")

        print(f"\n[浮点数] 共 {len(self.floats)} 个")
        # 按值排序，显示一些有意义的值
        sorted_floats = sorted(self.floats, key=lambda f: f.value)
        meaningful = [f for f in sorted_floats if abs(f.value) > 0.1 and abs(f.value) < 1e8]
        for f in meaningful[:20]:
            print(f"  0x{f.offset:06X}: {f.value:.6g}")

        print(f"\n[字符串] 共 {len(self.strings)} 个")
        # 按长度排序
        sorted_strings = sorted(self.strings, key=lambda s: len(s.value), reverse=True)
        for s in sorted_strings[:20]:
            preview = s.value[:50] + '...' if len(s.value) > 50 else s.value
            print(f"  0x{s.offset:06X}: {preview}")

        print(f"\n[提取的字段]")
        for field, values in result['extracted'].items():
            print(f"  {field}:")
            for v in values[:3]:
                print(f"    - {v}")

        print(f"\n[生成的模板]")
        template = self.extract_template()
        print(json.dumps(template, indent=2))


def main():
    if len(sys.argv) < 2:
        print("用法: python pdml_binary_parser.py <file.pdml>")
        print("\n选项:")
        print("  --template    输出 JSON 模板")
        print("  --json        输出完整 JSON")
        return 1

    filepath = sys.argv[1]
    parser = PDMLBinaryParser(filepath)

    if '--template' in sys.argv:
        template = parser.extract_template()
        print(json.dumps(template, indent=2))
    elif '--json' in sys.argv:
        result = parser.parse()
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        parser.print_summary()

    return 0


if __name__ == "__main__":
    exit(main())
