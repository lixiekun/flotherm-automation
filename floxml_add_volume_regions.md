# FloXML Volume Region Injector

`floxml_add_volume_regions.py` 用来给已有的 FloXML 项目文件追加一个或多个 `<region>`，也就是 FloTHERM 里的 volume region。

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

## 后续可扩展方向

如果后面需要，可以继续加：

- 已存在 region 时按名字更新
- 支持删除指定 region
- 支持控制插入顺序
- 支持从多个 bbox 组合生成不同层级的 region
