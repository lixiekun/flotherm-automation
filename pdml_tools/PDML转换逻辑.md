# PDML 二进制解析与 FloXML 转换逻辑

## 转换流程总览

```
PDML 二进制文件
    │
    ▼
┌─────────────────────────────────────┐
│  1. PDMLBinaryReader 解析           │
│     · 识别文件头 (#FFFB)            │
│     · 提取 tagged strings            │
│     · 检测 profile (布局类型)        │
└──────────────┬──────────────────────┘
               │
    ▼
┌─────────────────────────────────────┐
│  2. 几何记录提取                     │
│     · _find_geometry_records()       │
│     · 按类型码过滤几何节点           │
│     · 提取 level 字节                │
│     · 排除内部几何名和 Wall          │
└──────────────┬──────────────────────┘
               │
    ▼
┌─────────────────────────────────────┐
│  3. 节点构建                        │
│     · _build_geometry_node_from_record() │
│     · 提取 position / size / name   │
│     · 设置 node_type 和 orientation │
└──────────────┬──────────────────────┘
               │
    ▼
┌─────────────────────────────────────┐
│  4. Controller 折叠                  │
│     · _collapse_controller_children() │
│     · Source → XML source 元素       │
│     · Probe → monitor_points        │
└──────────────┬──────────────────────┘
               │
    ▼
┌─────────────────────────────────────┐
│  5. 层级构建 (按 profile 分派)      │
│     · _attach_assembly_children()    │
│     ┌─────────────────────────────┐ │
│     │ Feature-Rich → 名称匹配     │ │
│     │ Compact+Level → compact布局 │ │
│     │ Compact 无Level → heatsink  │ │
│     └─────────────────────────────┘ │
└──────────────┬──────────────────────┘
               │
    ▼
┌─────────────────────────────────────┐
│  6. 坐标转换                        │
│     · _convert_to_relative_positions() │
│     · 绝对坐标 → 父级相对坐标       │
│     · 递归减去父节点 position        │
└──────────────┬──────────────────────┘
               │
    ▼
┌─────────────────────────────────────┐
│  7. FloXML 生成                     │
│     · 遍历几何树生成 XML 节点        │
│     · 输出完整 FloXML 项目文件       │
└─────────────────────────────────────┘
```

## Profile 检测

| Profile | 检测标志 | 层级策略 |
|---------|---------|---------|
| `FEATURE_RICH_LAYOUT` (默认) | Functions-Example, Grid Constraint, Sub-Divided, VolumeHT 等 | 名称匹配 `_attach_by_name_match` |
| `COMPACT_FORCED_FLOW_LAYOUT` | Heat Sink Geometry + Ambient 同时存在 | 有 level → `_attach_compact_layout_children`；无 level → `_attach_heatsink_children` |

## 层级构建策略详解

### 1. 名称匹配（Feature-Rich Layout）

**方法**: `_attach_by_name_match()`

**原理**: FloTHERM PDML 中，属于某 assembly 的子节点，其名称包含 `[AssemblyName,` 模式。

**示例**:
```
节点名: "R22 [1206, 13-23825-07]"
正则匹配: \[([^,\]]+)  → 提取 "1206"
→ 该节点挂载到名为 "1206" 的 assembly 下
```

**流程**:
1. 收集所有 `node_type == 'assembly'` 的节点
2. 遍历所有节点，用正则提取方括号内第一个名称
3. 匹配到同名 assembly → 挂载为子节点
4. 未匹配节点保留在顶层，保持原始顺序

**局限**:
- 只匹配方括号内第一个名称（最近一层父级）
- 嵌套 assembly（如 `Part [Outer [Inner, ...]]`）只能匹配到 `Outer`
- 若 FloTHERM 对子 assembly 也遵循 `[ParentName,` 命名，则多层嵌套可工作；否则子 assembly 会留在顶层

### 2. Compact Layout（有 Level 信息）

**方法**: `_attach_compact_layout_children()`

**流程**:
1. `_consume_heatsink_scope()` — 找到 Heat Sink Geometry assembly，按 preorder 顺序分配 fin 与 cuboid
2. `_split_compact_tail_nodes()` — 分离尾部节点 (fixed_flow, source, monitor_point)
3. `_attach_compact_level_groups()` — 用 level 字节分组挂载
4. network_assembly 子节点提升到父级（它们只是分组包装器）
5. 尾部节点必须在顶层（Level 1）

### 3. Heatsink 简单模式（无 Level 信息）

**方法**: `_attach_heatsink_children()`

**适用**: windtunnel 样本导出的 heatsink 几何，记录按 preorder 排列。

**流程**:
1. 调用 `_consume_heatsink_scope()` 分离 heatsink 范围
2. 其余节点直接追加到顶层

## 坐标系统

### 绝对坐标 → 相对坐标转换

PDML 二进制中存储的是绝对坐标，但 FloXML 要求子节点 position 是相对于父级的位置。

**方法**: `_convert_to_relative_positions()`

```python
# 递归：每个子节点的 position 减去父节点的 position
for child in node.children:
    child.position = (cx - px, cy - py, cz - pz)
    self._convert_to_relative_positions(child)
```

**调用时机**: 层级构建完成后、赋值 `data.geometry` 前

**根节点**: position 固定为 `(0, 0, 0)`，因此顶层节点的坐标在减法后不变

### Position 提取

- 从二进制 record 中读取 double 值
- 搜索范围: offset 370-430
- 筛选条件: rel_min=380, rel_max=410 内取 3 个值
- 对应 (x, y, z) 三轴坐标

### Size 提取

- 搜索范围: offset 240-290
- 筛选条件: rel_min=250, rel_max=285 内取 3 个值
- 对应 (dx, dy, dz) 三维尺寸

## 特殊节点处理

| 节点类型 | 处理方式 |
|---------|---------|
| Controller | 折叠 Source/Probe 为子属性 |
| Fan | 提取 hub_diameter，生成 fan_geometry XML |
| Prism | 设置 material 和 thermal 元素 |
| Tet | 设置 material |
| Inverted Tet | 设置 active=False |
| Sloping Block | 提取 angle 和尺寸，使用 angle 值 |
| Network Assembly | compact 布局下提升子节点到父级 |

## 已修复问题

### PCB/Coldplate 模型层级丢失（已修复）

**原问题**: `_attach_by_name_match` 只能匹配名称含 `[AssemblyName,` 模式的节点。PCB 模型中父子关系通过 level 字节 + 顺序表达，导致 155 节点全扁平、45 个 assembly 全空。

**修复**: 改用两遍混合策略 `_attach_by_level_sequential`：
1. Pass 1: 名称匹配处理 `[AsmName,` 模式（如 `R22 [1206, ...]` → `1206` assembly）
2. Pass 2: level 字节 + 顺序分组处理无括号节点（如 `Layer 1` → `Layers` assembly）
3. Name-matched assembly 不参与 level-based stack，避免吞入无关节点

## 测试结果

| 测试文件 | 层级 | 状态 |
|---------|------|------|
| `all.pdml` | `1206` → 2 children, top=30 | 正确 |
| `Heatsink.pdml` | Heat Sink Geometry → 10 Fin → 各 5 cuboid | 正确 |
| `test_compare/all.pdml` | 同 all.pdml | 正确 |
| `PCB.pdml` | Layers=9, TopAttach=13, BottomAttach=21 | 正确 |
| `Coldplate.pdml` | Coldplate=2, Package=1 | 正确 |
| `PCB1.pdml` | 同 PCB.pdml | 正确 |

## Level 字节的层级编码规则（PCB 模型逆向）

通过 PCB.pdml 的 155 个节点分析，level 字节的含义：

| Level | 含义 | 示例 |
|-------|------|------|
| **L1** | 直接子节点，属于当前父级 | `Layer 1` cuboid 属于 `Layer 1` assembly |
| **L2** | 同层 sibling，关闭当前分组，开新分组 | `Layer 2` asm 是 `Layer 1` asm 的兄弟，都属于 `Layers` |
| **L3** | 更深层内容，或高层容器的开始 | `TopAttach` 以 L3 开始；`GR-U3` region 以 L3 结尾 |

**关键规则**:
1. L2/L3 assembly 开启新分组，后续 L1 节点属于该 assembly
2. L2 assembly 结束上一个 L3 组（如 `BottomAttach` L2 关闭 `TopAttach` L3 组）
3. 非assembly 节点的 L1/L3 表示它属于最近的父级 assembly
4. 这是 preorder 遍历，level 变化表示进入/退出子树

## 修复建议

### 方案: 名称匹配 + Level 回退混合策略

```python
def _attach_assembly_children(self, nodes):
    # 1. 先用名称匹配（处理 [AssemblyName, 模式）
    top_level = self._attach_by_name_match(nodes)

    # 2. 检查是否有空的 assembly 应该有子节点
    #    如果 level 信息可用，对未匹配的节点用 level 字节重新分组
    if any(n.level > 0 for n in nodes):
        top_level = self._attach_by_level_fallback(top_level)

    return top_level
```

### 清理死代码

`_attach_by_level()` 约 280 行代码目前未被调用，修复后如果复用则保留，否则清理。

## Controller 折叠依赖固定名称匹配

`_collapse_controller_children()` 通过名称匹配 Source 和 Probe，如果 FloTHERM 版本变更命名规则可能失效。

## 几何类型码映射

| 类型码 | 节点类型 |
|-------|---------|
| 0x0010 | pcb |
| 0x01D0 | resistance |
| 0x0250 | cuboid |
| 0x02E0 | assembly |
| 0x0360 | hollow_block |
| 0x0410 | prism |
| 0x0460 | tet |
| 0x0470 | inverted_tet |
| 0x0490 | sloping_block |
| 0x04B0 | fan |
| 0x0510 | network_assembly |
| 0x0530 | controller |
| 0x0580 | source |
