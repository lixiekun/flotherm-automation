# PDML 格式深度分析结果

## 关键发现

### 1. 字符串格式
```
07 02 XX XX 00 08 00 00 [length] [string data]
```
- `07 02` 是字符串标记
- `XX XX` (2字节) 可能是类型标识符
- 大端序 4 字节是长度
- 后面是字符串数据

### 2. 类型标识符模式
通过对比原始 FloXML 和 PDML 中的几何体类型:
 我发现了以下类型编码模式:

| type_code | FloXML 类型 | 说明 |
|---------|-------------|------|
| `0250` | cuboid | Block |
| `0280` | prism (Prism1) |
| `0731` | tet (Tet22) |
| `0732` | inverted_tet (ITET) |
| `0380` | sloping_block (BAFFLE) |
| `02c0` | source (Source-1) |
| `02a0` | resistance (Flow Resistance geometry) |
| `01d0` | resistance attribute (Flow Resistance in modeldata) |
| `0290` | region |
| `0270` | monitor_point (MP-01) |
| `0300` | cylinder (Cap) |
| `02e0` | assembly (1206) |
| `0310` | enclosure (Chassis) |
| `0330` | fixed_flow |
| `05d0` | perforated_plate (Floor Tile) |
| `02f0` | cuboid (Block with Holes) |
| `0370` | recirc_device (Recirc-01) |
| `0380` | rack (Rack-001) |
| `0390` | cooler (Cooler-001) |
| `0320` | network_assembly | `0330` | cuboid (Network Assembly Example - 袙为assembly错误 |
| `0380` | heatsink (Plate Fin Heat Sink) - 锆 缠成 inverted_tet

| `0390` | heatsink (Pin Fin Heat Sink) - 混合 |
| `0310` 和 `0380` 都是是 tet 类型，我原来的是 inverted_tet 也是被视为 tet!

  - BAFFLE 虽然是 sloping_block,但实际尺寸不匹配（斜边)
  - position和 size 数据存在，但可以提取到，  size 寽请确认!

  - 名称前数值位置相对固定（约 +0x0d-0x00f）
  - position 值在 +0x00f-0x00g 附近 (约 +0x00d8-0x00g)
  - size 噪： fan-1 的位置和尺寸是| position: (0, 0, 0) | size: (0.15, 0.15, 0.01) - 完全正确！
 - orientation 和 local_z 没有直接提取（都在 _extract_nearby_values 中）

}

}

}
```

### 2. **属性编码与值位置模式**
属性名后的值也出现在 +0x10 位置（在 modeldata section）。**解决方案**
改进属性提取逻辑:
1. 在 `_extract_geometry_entries` 中，类型识别正确处理 `01d0` 类型（属性）
时使用 `01d0` 类型映射
2. 在 `geometry section` 中添加了两个特殊的属性类型
而不是将其所有东西都当作 `cuboid`:
 使用 `01d0` 类型映射来区分属性定义和几何体

3. 改进数值解析：使用大端序 double 的相对偏移来提取 size/位置，现在使用固定的相对偏移范围

4. 继续深入分析 solution域边界条件。改进 `_extract_all_strings` 方法，使用类型码来验证

5. 改进 `_extract_solution_domain` 以正确提取 solution域

## 下一步

改进转换器以识别几何类型。正确提取属性。改进数值解析逻辑。让我先更新转换器并测试。