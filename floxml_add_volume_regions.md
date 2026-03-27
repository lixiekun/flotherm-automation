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
- `--config`：JSON 配置文件
- `-o / --output`：输出 FloXML 文件；如果不写，默认输出为 `原文件名_with_regions.xml`

例如：

```powershell
python floxml_add_volume_regions.py .\demo.xml --config .\floxml_volume_regions.example.json -o .\demo_with_regions.xml
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
- `scope_assembly`：可选，只在某个 assembly 范围内匹配
- `all_grid_constraint`
- `x_grid_constraint`
- `y_grid_constraint`
- `z_grid_constraint`
- `localized_grid`

如果同一条规则匹配到多个对象，会对所有匹配对象都生效。

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
- `padding`：可以是单个数字，或 `[px, py, pz]`
- `scope_assembly`：可选，只在某个 assembly 范围内找匹配几何

bbox 计算逻辑：

1. 找到所有匹配的几何对象
2. 读取它们的 `position + size`
3. 计算整体包围盒
4. 按 `padding` 向外扩
5. 生成 region 的 `position` 和 `size`

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
    "include_patterns": ["U*", "R*", "C*"],
    "padding": 0.001
  }
}
```

这段配置的意思是：

1. 在 FloXML 里查找名字精确等于 `PCB` 的对象
2. 再查找名字匹配 `U*`、`R*`、`C*` 的对象
3. 用这些对象的 `position + size` 算出整体包围盒
4. 再往外扩 `0.001 m`
5. 最终生成这个 region 的 `position` 和 `size`

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

仓库里提供了一个示例：

- [floxml_volume_regions.example.json](/D:/Program%20Files/Siemens/SimcenterFlotherm/2504/flotherm-automation/floxml_volume_regions.example.json)

你可以直接复制一份再改。

## 常见用法示例

只加一个手工 region：

```powershell
python floxml_add_volume_regions.py .\model.xml --config .\my_regions.json -o .\model_with_regions.xml
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
