# FloXML Tools 功能缺口分析

> 基于 `floxml_tools/` 代码与 `examples/DCIM Development Toolkit/Schema Files/FloXML/*.xsd` 对比
>
> 分析日期：2026-04-11

## 一、已实现功能

| 功能 | 覆盖内容 | 对应文件 |
|------|---------|---------|
| **Grid** | system_grid, patches, grid_constraints | `floxml_grid_parser.py`, `grid_config.py` |
| **Solve** | overall_control, variable_controls, solver_controls | `floxml_add_solve_settings.py` |
| **Model** | modeling, turbulence, gravity, global, transient, initial_variables | `floxml_add_solve_settings.py` |
| **Attributes** | materials, surfaces, surface_exchanges, radiations, resistances, fans, thermals, transients | `config_injector.py` |
| **Solution Domain** | size, position, basic boundary conditions | `wrap_geometry_floxml_as_project.py` |
| **Volume Regions** | region 创建、grid_constraint 应用 | `floxml_add_volume_regions.py` |
| **Geometry (ECXML)** | cuboid, assembly, source, monitor_point | `ecxml_to_floxml_converter.py` |

## 二、缺失功能：Geometry 几何对象

XSD `XmlGeometry.xsd` 在 `<geometry>` 下定义了 30+ 种几何对象，当前仅支持 4 种（来自 ECXML 转换）。

### 高优先级（常用）

| 对象 | 用途 | XSD 复杂度 |
|------|------|-----------|
| `cylinder` | 圆柱体（芯片电容等） | 低 |
| `heatsink` | 散热器（plate-fin / pin-fin） | 高 |
| `component2r` | 双热阻 IC 封装模型 | 中 |
| `enclosure` + `cutout` | 机箱围挡 + 开孔 | 中 |
| `fan` (几何体) | 风扇（含性能曲线） | 高 |

### 中优先级

| 对象 | 用途 |
|------|------|
| `fixed_flow` | 固定流量设备 |
| `supply` | 进风口 |
| `extract` | 出风口 |
| `heatpipe` | 热管 |
| `tec` | 热电冷却器 (TEC) |
| `pcb` | PCB 板 |
| `perforated_plate` | 冲孔板 |
| `resistance` (几何体) | 流阻（含公式） |

### 低优先级（特殊场景）

| 对象 | 用途 |
|------|------|
| `prism` | 三棱柱 |
| `tet` / `inverted_tet` | 四面体 |
| `sloping_block` | 斜面块 |
| `rack` | 机柜 |
| `cooler` | 冷却单元 |
| `component` (详细) | 详细封装模型（含热网络） |
| `die` | 芯片 Die（含功率分布） |
| `network_assembly` / `network_node` / `network_cuboid` | 热网络装配 |
| `recirc_device` | 回流设备 |
| `square_diffuser` | 方形散流器 |
| `thermostat` | 恒温器 |
| `controller` | 控制器 |
| `heat_exchanger` | 换热器 |
| `pdml` | 引用外部 .pdml 项目作为子装配 |
| `powermap` | 导入功率映射文件 |
| `material_map` | 导入材料映射文件 |
| `region` | 流体区域（独立定义） |

## 三、缺失功能：Attributes 属性

| 属性类型 | XSD 定义 | 说明 |
|----------|---------|------|
| `occupancies` | `occupancy_att` | 占用热源（occupancy level + activity） |
| `controls` | `control_att` | 控制曲线和频率设置 |

## 四、缺失功能：Model / Solution Domain 细节

| 缺失项 | 所属模块 | 说明 |
|--------|---------|------|
| `concentrations` | model | 最多 15 种浓度类型 |
| `solar_radiation` | model > modeling | 太阳辐射设置 |
| `joule_heating` | model > modeling | 焦耳加热选项 |
| `subdomains` | solution_domain | 子域定义（含初始条件） |

## 五、总结

- **Geometry 是最大缺口**：XSD 定义 30+ 种几何对象，当前仅支持 4 种
- **Attributes 缺口小**：仅差 `occupancies` 和 `controls` 两项
- **Model / Domain 缺口小**：主要是特殊物理场场景（太阳辐射、浓度、焦耳加热）
- **Solve / Grid 已完整覆盖**
