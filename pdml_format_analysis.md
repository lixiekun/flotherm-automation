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
通过对比原始 FloXML 和 PDML 中的几何体类型，已确认以下类型编码:

| type_code | FloXML 类型 | 说明 |
|-----------|-------------|------|
| `0x0250` | cuboid | 标准长方体 |
| `0x0260` | cutout | 切口 |
| `0x0270` | monitor_point | 监控点 (MP-01) |
| `0x0280` | prism | 棱柱 |
| `0x0290` | region | 区域 |
| `0x02A0` | resistance | 流阻 |
| `0x02B0` | fan | 风扇 |
| `0x02C0` | source | 热源 (Source-1) |
| `0x02D0` | heatsink | 散热器 |
| `0x02E0` | assembly | 装配体 |
| `0x02F0` | cuboid | 备用长方体类型码 |
| `0x0300` | cylinder | 圆柱体 |
| `0x0310` | enclosure | 机箱/外壳 |
| `0x0330` | fixed_flow | 固定流量 |
| `0x0340` | recirc_device | 再循环设备 |
| `0x0370` | perforated_plate | 穿孔板 |
| `0x0380` | sloping_block | 斜块 |
| `0x0390` | cooler | 冷却器 |
| `0x0731` | tet | 四面体 |
| `0x0732` | inverted_tet | 反向四面体 |

### 3. 层级编码规则

PDML 使用 level 字段表示节点层级关系:
- **Level 2**: 可以是顶层节点或子节点（取决于上下文）
- **Level 3**: 通常是子节点

#### 层级检测启发式规则

通过命名模式区分顶层装配体和子装配体:

**顶层容器特征**:
- 名称包含: `Layers`, `Attach`, `Assembly`, `Power` 等

**子装配体特征**:
- 名称以 `Layer `, `U`, `R`, `C`, `P`, `GR-`, `MP-` 开头
- 名称包含 `[` 和 `]`（如 `U3 [SO20W]`）

#### 附加逻辑
- Level 3 装配体 → 作为当前父节点的子节点
- Level 2 装配体 → 根据命名判断是顶层还是子节点
- 非装配体节点 → 附加到最近的装配体

### 4. 属性编码与值位置模式
- 属性名后的值出现在 `+0x10` 位置（在 modeldata section）
- 使用类型码 `0x01d0` 区分属性定义和几何体

### 5. 数值解析
- 使用大端序 double 的相对偏移提取 size/position
- 名称位置相对固定（约 `+0x0d-0x00f`）
- position 值在 `+0x00f-0x01a` 附近

## 待完成

- [ ] 深入分析 solution 域边界条件
- [ ] 改进 `_extract_solution_domain` 提取逻辑
- [ ] 验证 orientation 和 local_z 提取