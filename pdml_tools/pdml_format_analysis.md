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
- **Level 3**: 新子组的**第一个**元素（开始嵌套）
- **Level 2**: 同组的**后续兄弟**元素

#### 示例
```
Heat Sink Geometry (L3) ← Heat Sink 的新子组
  Base (L3)             ← Heat Sink Geometry 的新子组
  Fin 1 (L2)            ← Base 的兄弟（同属 Heat Sink Geometry）
    Low A - 1 (L3)      ← Fin 1 的新子组
    Low B - 1 (L2)      ← Low A - 1 的兄弟
  Fin 2 (L2)            ← Fin 1 的兄弟（同属 Heat Sink Geometry）
```

#### 层级检测算法（栈实现）

```python
parent_stack = []  # 跟踪父级层级
last_assembly = None

for node in nodes:
    if node 是装配体:
        if level == 3:
            # L3 装配体: 作为当前父级的子节点，压入栈
            parent_stack[-1].children.append(node)
            parent_stack.append(node)
        elif level == 2:
            # L2 装配体: 是上一个装配体的兄弟，回退一级
            parent_stack.pop()  # 弹出上一个装配体
            parent_stack[-1].children.append(node)  # 添加到共同的父级
            parent_stack.append(node)
    else:
        # 非装配体节点: 作为当前父级的子节点
        parent_stack[-1].children.append(node)
```

#### 容器名称模式
用于识别顶层分组: `Layers`, `Attach`, `Assembly`, `Power`, `Electrical`, `Vias`, `Board`, `Parts`, `Components`, `Domain`, `Solution`, `Model`

### 4. 同名节点处理

PDML 中可能存在多个同名节点（如多个 "Block" cuboid 在不同装配体中）。

**注意事项**：
- 不能用名称作为唯一标识符
- 应使用 offset 位置区分不同节点
- 使用 `list` 存储记录，`set` 跟踪已处理的 offset

### 5. 属性编码与值位置模式
- 属性名后的值出现在 `+0x10` 位置（在 modeldata section）
- 使用类型码 `0x01d0` 区分属性定义和几何体

### 6. 数值解析
- 使用大端序 double 的相对偏移提取 size/position
- 名称位置相对固定（约 `+0x0d-0x00f`）
- position 值在 `+0x00f-0x01a` 附近

## 待完成

- [ ] 深入分析 solution 域边界条件
- [ ] 改进 `_extract_solution_domain` 提取逻辑
- [ ] 验证 orientation 和 local_z 提取