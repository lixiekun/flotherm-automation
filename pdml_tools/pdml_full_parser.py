#!/usr/bin/env python3
"""
PDML 完整解析器 v2

解析 FloTHERM PDML 二进制格式，提取模型设置。

## 已发现的编码规则

### 头部
- ASCII: `#FFFB V3.3 FloTHERM x.x\n`
- 魔数: `FF FB`

### 数据块标记
- `0x07 0x02` + offset(4B) + len(4B) + string - 字符串块
- `0x0A 0x01` - 块开始类型1
- `0x0A 0x02` + type(2B) - 块开始类型2
- `0x01 0x00 0x00 0x00` - 块结束
- `0x03 0x00 0x00 0x00` + count(4B) - 计数器

### 数据值
- `0x06` + double(8B, BE) - 浮点数/整数
- `0x0C 0x03` + type(2B) + value(4B or 8B) - 带类型的值

### 枚举值
- 257 (0x101) = true / on / yes
- 258 (0x102) = false / off / no
- 259 (0x103) = 选项3
- 260 (0x104) = 选项4

### 类型代码 (0x0C 0x03 后的 2 字节)
高字节 = 类别, 低字节 = 子类型

类型代码映射:
- 0xXX00 - 基础值
- 0xXX06 - 布尔值 (257=true, 258=false)
- 0xB004 - outer_iterations
- 0x9004 - 某个设置
"""

import struct
import json
import sys
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Tuple


@dataclass
class PDMLField:
    """PDML 字段"""
    name: str
    offset: int
    value: Any
    value_type: str
    raw_bytes: bytes = b''


class PDMLFullParser:
    """PDML 完整解析器 v2"""

    # 枚举值映射
    ENUM_VALUES = {
        257: True,   # true / on / yes
        258: False,  # false / off / no
        259: 'option_3',
        260: 'option_4',
        261: 'option_5',
        262: 'option_6',
    }

    # 类型代码映射 (基于分析)
    TYPE_CODES = {
        # 0x0X00 系列 - 基础设置
        0x0000: 'unknown_flag',
        0x0001: 'count_value',
        0x0005: 'index_value',
        0x0009: 'id_value',
        0x000A: 'option_index',

        # 0x1X00 系列 - 存储和标志
        0x1000: 'store_option',
        0x1004: 'store_flag_1',
        0x1005: 'store_flag_2',
        0x1007: 'turbulence_flag',
        0x100C: 'mesh_option',

        # 0x2X00 系列 - 网格相关
        0x2000: 'grid_flag_1',
        0x2001: 'grid_flag_2',
        0x2004: 'grid_store_flag',
        0x2006: 'grid_constraint',
        0x2009: 'grid_option_1',
        0x200B: 'grid_option_2',
        0x200C: 'grid_mesh_option',

        # 0x3X00 系列 - 维度和尺寸
        0x3000: 'dimensionality_flag',
        0x3001: 'dimensionality',
        0x3004: 'size_option',
        0x3005: 'size_flag',
        0x300B: 'dimension_option',
        0x300C: 'dimension_mesh_option',

        # 0x4X00 系列 - 求解器
        0x4000: 'solver_flag',
        0x4002: 'solver_option_1',
        0x4004: 'solver_store_flag',
        0x4008: 'solver_monitor',
        0x400B: 'solver_mesh_option',

        # 0x5X00 系列 - 平滑和收敛
        0x5000: 'smoothing_flag',
        0x5001: 'smoothing_option_1',
        0x5002: 'smoothing_option_2',
        0x5004: 'smoothing_store_flag',
        0x5005: 'smoothing_value_2',
        0x5008: 'smoothing_value',

        # 0x6X00 系列 - 监控
        0x6000: 'monitor_flag',
        0x6008: 'monitor_option_1',
        0x6009: 'monitor_option_2',

        # 0x7X00 系列 - 重力
        0x7000: 'gravity_direction',
        0x7004: 'gravity_option_1',
        0x7005: 'gravity_option_2',
        0x7008: 'gravity_monitor',
        0x700A: 'gravity_flag',

        # 0x8X00 系列 - 压力
        0x8000: 'gravity_type',
        0x8002: 'pressure_option',
        0x8009: 'pressure_monitor',
        0x800A: 'pressure_flag',

        # 0x9X00 系列 - 收敛控制
        0x9000: 'convergence_flag',
        0x9001: 'monitor_flag',
        0x9004: 'convergence_flag_2',
        0x9005: 'convergence_option',
        0x9009: 'convergence_monitor',
        0x900A: 'convergence_store_flag',

        # 0xAX00 系列 - 布尔标志
        0xA000: 'boolean_main_flag',
        0xA005: 'boolean_option',
        0xA006: 'boolean_flag',
        0xA009: 'boolean_monitor',
        0xA00A: 'boolean_store_flag',

        # 0xBX00 系列 - 迭代控制
        0xB000: 'outer_iterations',
        0xB004: 'outer_iterations_2',
        0xB008: 'iteration_monitor',
        0xB009: 'iteration_option',

        # 0xCX00 系列 - Fan 松弛
        0xC000: 'fan_relaxation_type',
        0xC004: 'fan_option_1',
        0xC005: 'solver_option',
        0xC006: 'fan_option_2',
        0xC009: 'fan_monitor',

        # 0xDX00 系列 - 辐射
        0xD001: 'radiation_option_1',
        0xD003: 'radiation_option_2',

        # 0xEX00 系列 - 网格类型
        0xE000: 'grid_type',
        0xE001: 'grid_option_3',
        0xE003: 'smoothing_type',
        0xE007: 'dynamic_update',
        0xE008: 'grid_monitor',
        0xE00A: 'grid_store_option',

        # 0xFX00 系列 - 其他
        0xF003: 'special_option_1',
        0xF004: 'special_option_2',
        0xF008: 'special_monitor',
        0xF009: 'special_store_flag',
    }

    def __init__(self, filepath: str):
        self.filepath = filepath
        with open(filepath, 'rb') as f:
            self.data = f.read()

        self.fields: List[PDMLField] = []
        self.strings: Dict[int, str] = {}
        self.structure: Dict[str, Any] = {}

    def parse(self) -> Dict[str, Any]:
        """完整解析 PDML 文件"""
        result = {
            'file': self.filepath,
            'header': self._parse_header(),
            'fields': [],
            'extracted_config': {},
            'raw_values': []
        }

        # 1. 提取所有字符串（作为字段名参考）
        self._extract_all_strings()

        # 2. 提取所有 0x06 + double 值
        self._extract_double_values()

        # 3. 提取所有 0x0C 0x03 块
        self._extract_typed_blocks()

        # 4. 基于字符串上下文识别字段
        result['fields'] = self._identify_fields()

        # 5. 提取配置
        result['extracted_config'] = self._extract_config()

        # 6. 原始值列表
        result['raw_values'] = [
            {
                'offset': hex(f.offset),
                'name': f.name,
                'value': f.value,
                'type': f.value_type
            }
            for f in self.fields
        ]

        return result

    def _parse_header(self) -> Dict[str, str]:
        """解析文件头部"""
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

    def _extract_all_strings(self):
        """提取所有字符串"""
        pos = 0
        while pos < len(self.data) - 10:
            # 方法1: 0x07 0x02 模式
            if self.data[pos:pos+2] == b'\x07\x02':
                if pos + 10 <= len(self.data):
                    length = struct.unpack('<I', self.data[pos+6:pos+10])[0]
                    if 0 < length < 1000 and pos + 10 + length <= len(self.data):
                        str_data = self.data[pos+10:pos+10+length]
                        try:
                            value = str_data.decode('utf-8', errors='replace')
                            if value.strip():
                                self.strings[pos] = value.strip()
                        except:
                            pass
            pos += 1

    def _extract_double_values(self):
        """提取所有 0x06 + double 值"""
        pos = 0
        while pos < len(self.data) - 9:
            if self.data[pos] == 0x06:
                try:
                    value = struct.unpack('>d', self.data[pos+1:pos+9])[0]
                    if -1e15 < value < 1e15 and abs(value) > 1e-15:
                        # 尝试识别字段名
                        field_name = self._find_nearby_string(pos)
                        self.fields.append(PDMLField(
                            name=field_name or f'double_{len(self.fields)}',
                            offset=pos,
                            value=value,
                            value_type='double',
                            raw_bytes=self.data[pos:pos+9]
                        ))
                except:
                    pass
            pos += 1

    def _extract_typed_blocks(self):
        """提取所有 0x0C 0x03 类型块"""
        pos = 0
        while pos < len(self.data) - 6:
            if self.data[pos:pos+2] == b'\x0c\x03':
                type_code = struct.unpack('<H', self.data[pos+2:pos+4])[0]

                # 检查是否是 0x06 开头
                if pos + 4 < len(self.data) and self.data[pos+4] == 0x06:
                    # 06 + double
                    if pos + 12 <= len(self.data):
                        value = struct.unpack('>d', self.data[pos+5:pos+13])[0]
                        type_name = self.TYPE_CODES.get(type_code, f'type_0x{type_code:04X}')
                        self.fields.append(PDMLField(
                            name=type_name,
                            offset=pos,
                            value=value,
                            value_type='typed_double',
                            raw_bytes=self.data[pos:pos+13]
                        ))
                        pos += 13
                        continue
                else:
                    # 4 字节整数
                    if pos + 8 <= len(self.data):
                        int_val = struct.unpack('<I', self.data[pos+4:pos+8])[0]

                        # 转换枚举值
                        if int_val in self.ENUM_VALUES:
                            value = self.ENUM_VALUES[int_val]
                            value_type = 'enum'
                        else:
                            value = int_val
                            value_type = 'int'

                        type_name = self.TYPE_CODES.get(type_code, f'type_0x{type_code:04X}')
                        self.fields.append(PDMLField(
                            name=type_name,
                            offset=pos,
                            value=value,
                            value_type=value_type,
                            raw_bytes=self.data[pos:pos+8]
                        ))
                        pos += 8
                        continue
            pos += 1

    def _find_nearby_string(self, pos: int, search_range: int = 100) -> Optional[str]:
        """在附近查找字符串"""
        # 向前查找
        for offset in range(10, search_range, 10):
            check_pos = pos - offset
            if check_pos in self.strings:
                s = self.strings[check_pos]
                # 过滤掉 GUID
                if len(s) == 32 and all(c in '0123456789ABCDEFabcdef' for c in s):
                    continue
                if len(s) > 3:
                    return s
        return None

    def _identify_fields(self) -> List[Dict]:
        """识别已知字段"""
        identified = []

        # 已知字段映射: (值范围, 字段名, 单位)
        known_fields = [
            ((9.7, 9.9), 'gravity_value', 'm/s²'),
            ((299, 301), 'ambient_temperature', 'K'),
            ((499, 501), 'outer_iterations', ''),
            ((101320, 101330), 'datum_pressure', 'Pa'),
            ((0.99, 1.01), 'scale_factor', ''),
            ((0.19, 0.21), 'estimated_free_convection_velocity', 'm/s'),
            ((0.09, 0.11), 'relaxation_factor', ''),
            ((-1.1, -0.9), 'negative_direction', ''),
        ]

        for f in self.fields:
            if f.value_type == 'double':
                for (low, high), name, unit in known_fields:
                    if low <= f.value <= high:
                        identified.append({
                            'name': name,
                            'value': f.value,
                            'value_type': f.value_type,
                            'unit': unit,
                            'offset': hex(f.offset)
                        })
                        break

            # 识别类型代码对应的字段
            if f.value_type in ['enum', 'int', 'typed_double']:
                # 跳过大的无效整数
                if f.value_type == 'int' and isinstance(f.value, int) and f.value > 1000000:
                    continue

                identified.append({
                    'name': f.name,
                    'value': f.value,
                    'value_type': f.value_type,
                    'unit': '',
                    'offset': hex(f.offset)
                })

        return identified

    def _extract_config(self) -> Dict[str, Any]:
        """提取配置模板"""
        config = {
            'model': {
                'gravity': {
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
        }

        # 从识别的字段更新
        for f in self.fields:
            # gravity
            if isinstance(f.value, float) and 9.7 < f.value < 9.9:
                config['model']['gravity']['gravity_value'] = f.value

            # ambient_temperature
            if isinstance(f.value, (int, float)) and 299 < f.value < 301:
                config['model']['global']['ambient_temperature'] = f.value

            # datum_pressure
            if isinstance(f.value, (int, float)) and 101320 < f.value < 101330:
                config['model']['global']['datum_pressure'] = int(f.value)

            # outer_iterations
            if isinstance(f.value, (int, float)) and 499 < f.value < 501:
                config['solve']['overall_control']['outer_iterations'] = int(f.value)

        return config

    def print_summary(self):
        """打印摘要"""
        result = self.parse()

        print("=" * 70)
        print(f"PDML 完整解析: {self.filepath}")
        print("=" * 70)

        print(f"\n[头部]")
        for k, v in result['header'].items():
            print(f"  {k}: {v}")

        print(f"\n[识别的字段] ({len(result['fields'])} 个)")
        for f in result['fields'][:30]:
            print(f"  {f['name']}: {f['value']} ({f['value_type']}) @ {f['offset']}")

        print(f"\n[提取的配置]")
        print(json.dumps(result['extracted_config'], indent=2))


def main():
    if len(sys.argv) < 2:
        print("用法: python pdml_full_parser.py <file.pdml>")
        print("\n选项:")
        print("  --config    输出提取的配置")
        print("  --json      输出完整 JSON")
        print("  --fields    输出所有识别的字段")
        return 1

    filepath = sys.argv[1]
    parser = PDMLFullParser(filepath)

    if '--config' in sys.argv:
        result = parser.parse()
        print(json.dumps(result['extracted_config'], indent=2))
    elif '--json' in sys.argv:
        result = parser.parse()
        print(json.dumps(result, indent=2, ensure_ascii=False))
    elif '--fields' in sys.argv:
        result = parser.parse()
        for f in result['fields']:
            print(f"{f['name']}: {f['value']} ({f.get('value_type', 'unknown')})")
    else:
        parser.print_summary()

    return 0


if __name__ == "__main__":
    exit(main())
