# FloXML Volume Region Injector

`floxml_add_volume_regions.py` 用来给已有的 FloXML 项目文件追加一个或多个 `<region>`，也就是 FloTHERM 里的 volume region。

脚本现在也支持同时创建或更新 `<attributes>/<grid_constraints>` 里的 `grid_constraint_att` 定义，这样可以一次性完成：

- 定义 grid constraint
- 给已有几何对象直接挂 grid constraint
- 新增引用这些 constraint 的 volume region

它适合这种场景：

- 你已经有一个可导入的 FloXML
- 还需要补充一个或多个 volume region
- region 的位置和尺寸希望通过 JSON 配置管理
- 有些 region 想直接手工给 `position/size`
- 有些 region 想根据现有几何体自动算包围盒

## 命令行用法

最短用法：

```powershell
python floxml_add_volume_regions.py input.xml --config floxml_volume_regions.example.json -o output.xml
```

参数说明：

- `input`：输入 FloXML 文件
- `--config`：配置文件（`.json` 或 `.xlsx`，自动识别）
- `-o / --output`：输出 FloXML 文件；如果不写，默认输出为 `原文件名_with_regions.xml`
- `--create-template PATH`：生成 Excel 模板文件

例如用 JSON 配置：

```powershell
python floxml_add_volume_regions.py .\demo.xml --config .\config.json -o .\demo_with_regions.xml
```

用 Excel 配置：

```powershell
python floxml_add_volume_regions.py .\demo.xml --config .\config.xlsx -o .\demo_with_regions.xml
```

生成 Excel 模板：

```powershell
python floxml_add_volume_regions.py --create-template template.xlsx
```

## JSON 结构

顶层结构：

```json
{
  "grid_constraints": [
    {
      "name": "Grid Constraint 1",
      "min_cell_size": 0.001,
      "min_number": 43
    }
  ],
  "object_constraints": [
    {
      "target_names": ["PCB"],
      "all_grid_constraint": "Grid Constraint 1"
    }
  ],
  "regions": [
    {
      "name": "Region A",
      "position": [-0.01, -0.01, -0.002],
      "size": [0.12, 0.08, 0.01]
    }
  ]
}
```

`regions` 是一个数组，每个元素对应一个要插入的 `<region>`。

## Excel 配置

除了 JSON，也支持用 Excel（`.xlsx`）做配置，适合不熟悉 JSON 的用户。

### 生成模板

```powershell
python floxml_add_volume_regions.py --create-template volume_regions_template.xlsx
```

仓库里也有一份现成模板：`examples/FloXML/Spreadsheets/volume_regions_template.xlsx`

### 使用 Excel 配置

```powershell
python floxml_add_volume_regions.py input.xml --config config.xlsx -o output.xml
```

`--config` 参数会自动根据后缀识别 JSON 还是 Excel。

### Excel 结构（3 个 Sheet）

#### Sheet 1: `grid_constraints`

定义 grid constraint，每行一个：

| name | enable_min_cell_size | min_cell_size | number_cells_control | min_number | high_inflation_type | high_inflation_size | high_inflation_number_cells_control | high_inflation_min_number |
|------|---------------------|---------------|---------------------|------------|--------------------|--------------------|------------------------------------|--------------------------|
| Grid Constraint 1 | true | 0.001 | min_number | 43 | size | 0.005 | min_number | 23 |

- `high_inflation_*` 列可选，留空表示不设膨胀层
- 和 `grid_config.py` 的 `grid_constraints` sheet 格式一致

#### Sheet 2: `object_constraints`

给已有几何对象直接挂 grid constraint：

| target_names | target_patterns | target_tags | scope_assembly | x_grid_constraint | y_grid_constraint | z_grid_constraint | all_grid_constraint | localized_grid |
|-------------|----------------|-------------|---------------|-------------------|-------------------|-------------------|--------------------|----------------|
| PCB | | cuboid | | | | | Grid Constraint 1 | false |

- `target_names` 和 `target_patterns` 用逗号分隔多个值（如 `PCB,CPU`）
- 留空的列表示不设该项

#### Sheet 3: `regions`

定义 volume region，每行一个：

| name | parent_assembly | position_x | position_y | position_z | size_x | size_y | size_z | bbox_include_names | bbox_include_patterns | bbox_include_tags | bbox_scope_assembly | bbox_padding | split_regions | active | hidden | localized_grid | x_grid_constraint | y_grid_constraint | z_grid_constraint | all_grid_constraint |
|------|----------------|-----------|-----------|-----------|-------|-------|-------|-------------------|---------------------|-----------------|--------------------|------------|--------|--------|---------------|-------------------|-------------------|--------------------|

两种模式互斥，优先使用 bbox（如果 bbox 字段有值）：

**显式模式** — 填 `position_x/y/z` + `size_x/y/z`：

| name | ... | position_x | position_y | position_z | size_x | size_y | size_z | bbox_* | ... |
|------|-----|-----------|-----------|-----------|-------|-------|-------|--------|-----|
| Explicit Volume Region | | -0.01 | -0.01 | -0.002 | 0.12 | 0.08 | 0.01 | *(留空)* | |

**bbox 模式** — 填 `bbox_include_names` 或 `bbox_include_patterns`：

| name | ... | position/size | bbox_include_names | bbox_include_patterns | bbox_padding | ... |
|------|-----|--------------|-------------------|---------------------|-------------|-----|
| BBox Region Around PCB | DemoBoard_Assembly | *(留空)* | PCB | U* | 0.001,0.001,0.0005 | |

- `bbox_padding` 支持单个数字或 `0.001,0.001,0.0005`（逗号分隔 3 值）
- `bbox_include_names` 和 `bbox_include_patterns` 用逗号分隔多个值
- 3 个 Sheet 都是可选的，缺少的 Sheet 会被跳过

### `split_regions` — 贪心合并减少 region 数量

开启 `split_regions` 后，脚本采用**贪心合并**算法：初始每个 cuboid 单独一个 region，然后沿 x/y/z 方向逐步合并相邻的 region，使 region 数量最少，同时确保合并后的 region 内没有障碍物（未选中的几何体）。

**相邻判定**：两个 region 在 3 个轴中有 2 个轴重叠（overlap），且第 3 个轴的间隙 ≤ 最小 item 尺寸。间隙过大的不算相邻，无法合并。

例如 3×3 九宫格中选中 1,2,3,4,7（L 形）：

```
┌───┬───┬───┐       ┌───┬───┬───┐
│ 1 │ 2 │ 3 │       │ R1│ R1│ R1│
├───┼───┼───┤       ├───┼───┼───┤
│ 4 │ 5 │ 6 │  →    │R2 │ 5 │ 6 │
├───┼───┼───┤       ├───┼───┼───┤
│ 7 │ 8 │ 9 │       │R2 │ 8 │ 9 │
└───┴───┴───┘       └───┴───┴───┘
```

结果：2 个 region（R1=顶行, R2=左列）

**不能跳过合并**：选中 1 和 7（不选 4）时，因为 1 和 7 之间间隙过大（超过一个 item 尺寸），不会被合并，各自独立成 region。

**3D 同样适用**：上下堆叠、整层合并、3D L 形等立体场景均可正确处理。

JSON 配置：

```json
{
  "regions": [
    {
      "name": "LShape",
      "bbox_from": {
        "include_names": ["C1", "C2", "C3", "C4", "C7"],
        "split_regions": true,
        "padding": 0.05
      }
    }
  ]
}
```

Excel 配置（regions sheet 加列 `split_regions`）：

| name | ... | bbox_include_names | bbox_padding | split_regions | ... |
|------|-----|-------------------|-------------|--------------|-----|
| LShape | | C1,C2,C3,C4,C7 | 0.05 | true | |

**合并规则**：

- 每个 cuboid 初始独立一个 region
- 沿 x/y/z 方向寻找相邻的 region 对
- 相邻条件：2 个轴重叠，第 3 个轴间隙 ≤ 最小 item 尺寸
- 合并条件：合并后的 bbox 内没有未选中的几何体（障碍物）
- 重复合并直到无法继续，目标是最小化 region 总数
- 合并后的 region 命名为 `{name}_1`、`{name}_2` 等（如果只产生 1 个 region，保留原名）
- 每个子 region 独立应用 `padding` 和 grid constraint 设置

`grid_constraints` 是可选数组，每个元素对应一个 `grid_constraint_att`。如果同名约束已经存在，脚本会更新；如果不存在，就会新建。

`object_constraints` 是可选数组，用来给已有几何对象直接写：

- `all_grid_constraint`
- `x_grid_constraint`
- `y_grid_constraint`
- `z_grid_constraint`

## `object_constraints` 用法

如果你想直接给某个现有 cuboid、pcb、source、region 等对象挂 grid constraint，而不是通过新增 region 来间接控制，就用这个配置。

例如：

```json
{
  "object_constraints": [
    {
      "target_names": ["PCB"],
      "target_tags": ["cuboid"],
      "all_grid_constraint": "Grid Constraint 1",
      "localized_grid": false
    }
  ]
}
```

这表示：

- 找到名字等于 `PCB` 的已有几何对象
- 直接给它写上 `<all_grid_constraint>Grid Constraint 1</all_grid_constraint>`

也支持通配符：

```json
{
  "object_constraints": [
    {
      "target_patterns": ["U*", "R*", "C*"],
      "all_grid_constraint": "Grid Constraint 1"
    }
  ]
}
```

支持字段：

- `target_names`：精确匹配名字列表
- `target_patterns`：通配符匹配列表
- `target_tags`：可选，限制匹配类型，例如 `cuboid`、`source`、`region`、`assembly`
- `scope_assembly`：可选，只在某个 assembly 范围内匹配
- `all_grid_constraint`
- `x_grid_constraint`
- `y_grid_constraint`
- `z_grid_constraint`
- `localized_grid`

如果同一条规则匹配到多个对象，会对所有匹配对象都生效。

如果你担心同名但不同类型的对象被一起匹配，建议一定补上 `target_tags`。

例如同名 `PCB` 既可能有 `cuboid`，也可能有 `source`，就写成：

```json
{
  "object_constraints": [
    {
      "target_names": ["PCB"],
      "target_tags": ["cuboid"],
      "all_grid_constraint": "Grid Constraint 1"
    }
  ]
}
```

### 什么时候用 `object_constraints`，什么时候用 `region`

如果你要：

- 只给某个现有对象本身挂网格约束

优先用 `object_constraints`。

如果你要：

- 给某个对象周围的一整块空间做局部网格控制

优先用 `region`。

简单理解：

- `object_constraints` = 直接改对象
- `region` = 新建一个空间盒子来控网格

## `grid_constraints` 用法

如果你的 region 要引用：

- `all_grid_constraint`
- `x_grid_constraint`
- `y_grid_constraint`
- `z_grid_constraint`

那么项目里最好已经存在对应名字的 `grid_constraint_att`。现在这个脚本可以直接在 JSON 里一起定义。

示例：

```json
{
  "grid_constraints": [
    {
      "name": "Grid Constraint 1",
      "enable_min_cell_size": true,
      "min_cell_size": 0.001,
      "number_cells_control": "min_number",
      "min_number": 43,
      "high_inflation": {
        "inflation_type": "size",
        "inflation_size": 0.005,
        "number_cells_control": "min_number",
        "min_number": 23
      }
    }
  ]
}
```

支持字段：

- `name`：必填
- `enable_min_cell_size`：可选，默认 `true`
- `min_cell_size`：可选
- `number_cells_control`：可选，默认 `min_number`
- `min_number`：可选
- `high_inflation`：可选对象

`high_inflation` 支持：

- `inflation_type`
- `inflation_size`
- `number_cells_control`
- `min_number`

所以最完整的使用方式通常是：

1. 在 `grid_constraints` 里定义或更新一个约束
2. 在 `regions` 里让 region 去引用它

## 方式 1：显式指定 position 和 size

这是最直接的方式。

```json
{
  "regions": [
    {
      "name": "Explicit Volume Region",
      "position": [-0.01, -0.01, -0.002],
      "size": [0.12, 0.08, 0.01],
      "localized_grid": true,
      "x_grid_constraint": "Grid Constraint 1"
    }
  ]
}
```

字段说明：

- `name`：region 名称，必填
- `position`：`[x, y, z]`，必填
- `size`：`[sx, sy, sz]`，必填
- `localized_grid`：可选，默认 `true`
- `active`：可选，默认 `true`
- `hidden`：可选
- `x_grid_constraint` / `y_grid_constraint` / `z_grid_constraint`：可选
- `all_grid_constraint`：可选
- `parent_assembly`：可选，表示插到哪个 assembly 下面

## 方式 2：根据已有几何自动算 bbox

如果不想手工量尺寸，可以让脚本按已有几何体自动算包围盒，然后再加 padding。

```json
{
  "regions": [
    {
      "name": "BBox Region Around PCB",
      "bbox_from": {
        "include_names": ["PCB"],
        "include_patterns": ["U*"],
        "padding": [0.001, 0.001, 0.0005]
      },
      "localized_grid": true,
      "all_grid_constraint": "Grid Constraint 1"
    }
  ]
}
```

`bbox_from` 支持这些字段：

- `include_names`：精确匹配名字列表
- `include_patterns`：通配符匹配列表，使用 `fnmatch` 规则，例如 `U*`、`R22 *`
- `include_tags`：可选，限制参与 bbox 计算的几何类型，例如 `cuboid`
- `padding`：可以是单个数字，或 `[px, py, pz]`
- `scope_assembly`：可选，只在某个 assembly 范围内找匹配几何

bbox 计算逻辑（多几何体联合包围盒）：

1. **匹配几何体**：遍历整棵几何树，按 `include_names`（精确）和 `include_patterns`（通配符）进行匹配，二者为 OR 关系；`include_tags` 额外做 AND 过滤
2. **读取全局坐标**：每个匹配到的几何对象，取其 `global_position`（累加了所有父 assembly 的偏移）和 `global_size`
3. **计算联合包围盒**：对所有匹配体的 xyz 取 min/max，形成一个包含所有匹配体的最小外接矩形：
   - `lower = (min_x, min_y, min_z)`
   - `upper = (max_x + size_x, max_y + size_y, max_z + size_z)`
4. **加 padding**：各方向向外扩 padding 值：
   - `position = lower - padding`
   - `size = (upper - lower) + 2 * padding`
5. **坐标转换**：如果指定了 `parent_assembly`，将全局坐标转换为该 assembly 的局部坐标后再写入 FloXML
6. **生成 region**：用最终的 position 和 size 构建 `<region>` 元素

举例：匹配到 PCB (0,0,0) size (0.1,0.08,0.002) 和 U1 (0.02,0.02,0.002) size (0.03,0.03,0.001)，联合 bbox 为 lower=(0,0,0) upper=(0.1,0.08,0.003)，加 padding 0.001 后 position=(-0.001,-0.001,-0.001) size=(0.102,0.082,0.005)

### 如何理解 `bbox_from`

可以把 `bbox_from` 理解成：

- 不是手工告诉脚本 region 的 `position/size`
- 而是先告诉脚本“这个 region 应该包住哪些已有几何”
- 再由脚本自动计算这些几何的外包框

例如：

```json
{
  "name": "Board Region",
  "bbox_from": {
    "include_names": ["PCB"],
    "include_tags": ["cuboid"],
    "include_patterns": ["U*", "R*", "C*"],
    "padding": 0.001
  }
}
```

这段配置的意思是：

1. 在 FloXML 里查找名字精确等于 `PCB` 的对象
2. 只保留 tag 是 `cuboid` 的对象
3. 再查找名字匹配 `U*`、`R*`、`C*` 的对象
4. 用这些对象的 `position + size` 算出整体包围盒
5. 再往外扩 `0.001 m`
6. 最终生成这个 region 的 `position` 和 `size`

也就是说，`bbox_from` 的目标不是“指定 region 在哪里”，而是“指定 region 要包住谁”。

### `include_names` 和 `include_patterns`

`include_names` 用于精确匹配：

```json
"include_names": ["PCB", "CPU"]
```

只会匹配名字完全等于 `PCB` 或 `CPU` 的几何对象。

`include_patterns` 用于通配符匹配：

```json
"include_patterns": ["U*", "R*", "C*"]
```

这会匹配类似：

- `U1`
- `U2`
- `R22`
- `C15`

脚本内部用的是 Python 的 `fnmatch` 规则，所以你可以把它理解成简单的通配符匹配。

### `padding`

`padding` 是给自动算出来的 bbox 额外留边距。

如果写成单个数字：

```json
"padding": 0.001
```

表示 x/y/z 三个方向都各扩 `0.001 m`。

如果写成 3 个值：

```json
"padding": [0.001, 0.001, 0.0005]
```

表示：

- x 方向扩 `0.001 m`
- y 方向扩 `0.001 m`
- z 方向扩 `0.0005 m`

### `scope_assembly` 和 `parent_assembly` 的区别

这两个字段很容易混淆，但作用完全不同。

`scope_assembly` 的作用是：

- 只限制“查找哪些对象参与 bbox 计算”

`parent_assembly` 的作用是：

- 只决定“最终把 region 插到哪个 assembly 下面”

例如：

```json
{
  "name": "Module A Region",
  "parent_assembly": "Module_A",
  "bbox_from": {
    "include_patterns": ["U*", "L*"],
    "scope_assembly": "Module_A",
    "padding": [0.001, 0.001, 0.0008]
  }
}
```

这段配置的意思是：

1. 先只在 `Module_A` 这个 assembly 范围内查找 `U*`、`L*`
2. 用这些对象算出 bbox
3. 把生成的 region 插到 `Module_A` 下面

如果你只写 `parent_assembly`，不写 `scope_assembly`，那么：

- region 会插到这个 assembly 下
- 但 bbox 仍然可能在全模型范围内搜索匹配对象

如果你只写 `scope_assembly`，不写 `parent_assembly`，那么：

- bbox 只在这个 assembly 范围内算
- 但 region 默认还是插到根 `<geometry>` 下

### 什么时候该用 `bbox_from`

适合：

- 想包住整块 PCB 和其上的器件
- 想给某个子模块自动生成 volume region
- 目标对象位置可能会变，但名字模式相对稳定

不太适合：

- 你已经非常清楚 region 的绝对位置和尺寸
- 目标对象命名不稳定，通配规则不好写
- 目标几何没有有效的 `size`，导致 bbox 无法计算

### `bbox_from` 常用示例

1. 包住整块板和器件

```json
{
  "regions": [
    {
      "name": "Board Region",
      "bbox_from": {
        "include_names": ["PCB"],
        "include_patterns": ["U*", "R*", "C*", "L*"],
        "padding": 0.001
      },
      "localized_grid": true,
      "all_grid_constraint": "Grid Constraint 1"
    }
  ]
}
```

2. 只包某个模块

```json
{
  "regions": [
    {
      "name": "Module A Region",
      "parent_assembly": "Module_A",
      "bbox_from": {
        "include_patterns": ["U*", "L*"],
        "scope_assembly": "Module_A",
        "padding": [0.001, 0.001, 0.0008]
      },
      "localized_grid": true
    }
  ]
}
```

3. 只包几个明确对象

```json
{
  "regions": [
    {
      "name": "Hot Parts Region",
      "bbox_from": {
        "include_names": ["CPU", "GPU", "VRM"],
        "padding": 0.0005
      }
    }
  ]
}
```

## 插入到根 geometry 还是某个 assembly 下

默认情况下，region 会直接插到根 `<geometry>` 下。

如果你想把 region 插到某个 assembly 里面，可以加：

```json
{
  "regions": [
    {
      "name": "Local Region",
      "parent_assembly": "DemoBoard_Assembly",
      "position": [0.0, 0.0, 0.0],
      "size": [0.01, 0.01, 0.01]
    }
  ]
}
```

注意：

- `position/size` 的输入可以按全局坐标理解
- 如果设置了 `parent_assembly`，脚本会自动换算成该 assembly 的局部坐标再写入 FloXML

## 生成的 region 结构

脚本生成的 `<region>` 结构参考仓库里的现有 FloXML 示例，包含：

- `name`
- `active`
- 可选 `hidden`
- `position`
- `size`
- `orientation`
- 可选 `x/y/z_grid_constraint`
- 可选 `all_grid_constraint`
- `localized_grid`

默认 orientation 是：

- `local_x = (1, 0, 0)`
- `local_y = (0, 0, 1)`
- `local_z = (0, 1, 0)`

这和仓库里现有的 `<region>` 示例保持一致。

## 示例配置文件

仓库里提供了示例：

- JSON 示例：`floxml_volume_regions.example.json`
- Excel 模板：`examples/FloXML/Spreadsheets/volume_regions_template.xlsx`

你可以直接复制一份再改。

## 常见用法示例

只加一个手工 region：

```powershell
python floxml_add_volume_regions.py .\model.xml --config .\my_regions.json -o .\model_with_regions.xml
```

用 Excel 配置：

```powershell
python floxml_add_volume_regions.py .\model.xml --config .\regions.xlsx -o .\model_with_regions.xml
```

同时新增 grid constraint 和 region：

```powershell
python floxml_add_volume_regions.py .\model.xml --config .\floxml_volume_regions.example.json -o .\model_with_regions.xml
```

给已有 PCB 直接挂 grid constraint：

```json
{
  "grid_constraints": [
    {
      "name": "Grid Constraint 1",
      "min_cell_size": 0.001,
      "min_number": 43
    }
  ],
  "object_constraints": [
    {
      "target_names": ["PCB"],
      "all_grid_constraint": "Grid Constraint 1",
      "localized_grid": false
    }
  ]
}
```

按 PCB 和器件自动算一个包围 region：

```json
{
  "regions": [
    {
      "name": "Board Region",
      "bbox_from": {
        "include_names": ["PCB"],
        "include_patterns": ["U*", "R*", "C*"],
        "padding": 0.001
      },
      "localized_grid": true,
      "all_grid_constraint": "Grid Constraint 1"
    }
  ]
}
```

插到指定 assembly 下：

```json
{
  "regions": [
    {
      "name": "Sub Assembly Region",
      "parent_assembly": "Module_A",
      "bbox_from": {
        "include_patterns": ["U*", "L*"],
        "scope_assembly": "Module_A",
        "padding": [0.001, 0.001, 0.0008]
      },
      "localized_grid": true
    }
  ]
}
```

## 当前限制

- 目前是“追加 region”，不会检查重名 region，也不会自动更新已有 region
- bbox 计算依赖已有几何体具有可用的 `position` 和 `size`
- 当前只支持按 assembly 名称定位插入位置，不支持“插到某个几何节点后面”
- `grid_constraints` 会按名字更新或新增，但不会删除旧约束
- `object_constraints` 只按名字/通配符匹配现有几何，不会新建对象

## 后续可扩展方向

如果后面需要，可以继续加：

- 已存在 region 时按名字更新
- 支持删除指定 region
- 支持控制插入顺序
- 支持从多个 bbox 组合生成不同层级的 region
