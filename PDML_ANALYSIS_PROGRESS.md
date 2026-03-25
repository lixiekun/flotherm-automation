# PDML 二进制格式分析进度报告

## 概述

本文档记录了 PDML 到 FloXML 转换器的开发进度和关键发现。

## 分析日期
2024-03-24

## 关键发现

### 1. 字符串格式
```
07 02 XX XX 00 08 00 00 [length: 4 bytes BE] [string data]
```
- `07 02` 是字符串标记
- 后面 2 字节是长度（大端序）
- 然后是字符串数据

### 2. 几何体类型标识符
从 `07 02 XX XX` 中的 `XX XX` 字节可以识别几何体类型：

| type_code | FloXML 类型 | 示例 |
|---------|-------------|------|
| `0250` | cuboid | Block |
| `0280` | prism | Prism1 |
| `0731` | tet | Tet22 |
| `0732` | inverted_tet | ITET |
| `0380` | sloping_block | BAFFLE |
| `02c0` | source | Source-1 |
| `0290` | region | Region |
| `0270` | monitor_point | MP-01 |
| `0300` | cylinder | Cap |
| `02e0` | assembly | 1206 |
| `0310` | enclosure | Chassis |
| `0330` | fixed_flow | Fixed Flow |
| `05d0` | perforated_plate | Floor Tile |
| `0370` | recirc_device | Recirc-01 |
| `0380` | rack | Rack-001 |
| `0390` | cooler | Cooler-001 |
| `0320` | network_assembly | Network Assembly Example |
| `0380` | heatsink | Plate Fin / Pin Fin Heat Sink |
| `0390` | heatsink | Pin Fin Heat Sink |

### 3. 数值存储格式
- **double 值**: 大端序, 标记字节 `0x06`, 后面 8 字节为 IEEE 754 double
- **位置**: 在字符串名称后约 +0x00d8 到 +0x00ea
- **尺寸**: 在字符串名称后约 +0x00fd 到 +0x0110

### 4. Section 标记
```
0x14c: gravity
0x2c4: modeldata
1x20b: solution domain
0xf62: grid smooth
0x10a4: turbulence
0xf2ab: geometry
```

## 当前转换器状态

### 已实现功能
- [x] 基本框架和结构
- [x] 字符串提取（大端序长度）
- [x] double 值提取
- [x] Section 定位
- [x] model 设置基本输出
- [x] solve 设置基本输出
- [x] grid 设置基本输出
- [x] attributes 基本输出（材料、流体、环境）
- [x] geometry 基本输出（但类型识别不完整）
- [x] solution_domain 基本输出

### 待改进项
- [ ] 几何体类型识别 - 需要根据 type_code 输出正确的 XML 元素
- [ ] 属性引用提取 - 需要提取材料、热源、表面等属性的引用
- [ ] 特殊几何体支持
  - fan (需要提取 fan_curve, outer_diameter 等)
  - heatsink (需要提取 fin 参数)
  - pcb (需要提取组件信息)
  - enclosure (需要提取壁厚等)
- [ ] solution_domain 边界条件 - 需要正确识别 symmetry vs ambient
- [ ] model 设置完善
  - transient 设置
  - solar_radiation 设置
  - convergence 设置

## 测试结果

### 转换测试 (all.pdml -> test_improved.xml)
```
[INFO] 读取 PDML: all.pdml
[INFO] 项目: all
[INFO] 版本: Simcenter Flotherm 2504
[INFO] 重力: 9.81 m/s2
[INFO] 迭代: 500
[INFO] 温度: 300.0 K
[INFO] 输出 FloXML: test_improved.xml
```

生成的 XML 结构正确，但存在以下问题:
1. **项目名称**: 显示为 "all" 而非 "My Model"
2. **几何体类型**: 所有几何体都被输出为 `cuboid`，未区分类型
3. **部分数值不准确**: 如 Flow Resistance 的位置值显示异常

## 下一步计划

1. **短期**
   - 添加几何体类型识别逻辑
   - 改进数值提取精度
   - 揄取属性引用

2. **中期**
   - 支持特殊几何体类型 (fan, heatsink, pcb)
   - 完善 solution_domain 提取
   - 改进 model 设置提取

3. **长期**
   - 全面测试所有几何体类型
   - 添加错误处理和日志
   - 性能优化

## 代码位置

- 主转换器: `pdml_to_floxml_converter.py`
- 格式分析: `pdml_format_analysis.md` (本文档)
- 类型分析: `analyze_geometry_types.py`

## 参考资料

- 原始 FloXML: `All-Objects-Attributes-Settings-FullModel.xml`
- 导出的 PDML: `all.pdml`
