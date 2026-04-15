# FloXML XSD Schema 说明

XSD（XML Schema Definition）定义了 FloXML 文件的结构规范——标签、属性、类型、嵌套关系、必填/可选等。

## 文件概览

```
FloXML/
├── xmlSchema.xsd          # 主入口，定义 <xml_case> 整体结构
├── XmlDefinitions.xsd     # 公共类型定义（基础库）
├── XmlAttributes.xsd      # 属性定义（材料、热源、环境等）
├── XmlEntities.xsd        # 求解/网格/模型配置
└── XmlGeometry.xsd        # 几何体定义（cuboid、plate 等）
```

## 各文件详细说明

### 1. xmlSchema.xsd — 主入口

定义 FloXML 根元素 `<xml_case>` 的完整结构：

```xml
<xml_case>
  <name/>              <!-- 必填 -->
  <title/>             <!-- 可选 -->
  <model/>             <!-- 求解模式配置 -->
  <solve/>             <!-- 求解器配置 -->
  <grid/>              <!-- 网格配置 -->
  <attributes>         <!-- 所有属性定义 -->
    <materials/>       <!-- 材料库 -->
    <surfaces/>        <!-- 表面属性 -->
    <surface_exchanges/> <!-- 表面换热 -->
    <thermals/>        <!-- 热模型 -->
    <sources/>         <!-- 热源 -->
    <occupancies/>     <!-- 占据率 -->
    <resistances/>     <!-- 流阻 -->
    <fans/>            <!-- 风扇 -->
    <ambients/>        <!-- 环境条件 -->
    <fluids/>          <!-- 流体属性 -->
    <grid_constraints/> <!-- 网格约束 -->
    <radiations/>      <!-- 辐射模型 -->
    <transients/>      <!-- 瞬态函数 -->
    <controls/>        <!-- 控制曲线 -->
  </attributes>
  <solution_domain/>   <!-- 求解域边界 -->
  <geometry/>          <!-- 必填，几何模型 -->
</xml_case>
```

通过 `<xs:include>` 引入其他三个 XSD。

### 2. XmlDefinitions.xsd — 公共类型

所有 XSD 共用的基础类型定义：

| 类型 | 说明 |
|------|------|
| `doubleGTZero` | 大于 0 的浮点数 |
| `doubleGTEZero` | 大于等于 0 的浮点数 |
| `doubleGTEZeroLTEOne` | 0~1 之间的浮点数 |
| `trueFalse` | "true" / "false" |
| `ratio` | 0.0~1.0 |
| `percentage` | 0.0~100.0 |
| `triplet` | `<x/><y/><z/>` 三维坐标 |
| `global_coords` | `<i/><j/><k/>` 全局坐标 |
| `coord2d` | `<x/><y/>` 二维坐标 |
| `direction` | x_direction / y_direction / z_direction |
| `position` | low_face / mid_face / high_face |
| `variable_types` | temperature / pressure / x_velocity 等求解变量 |

曲线类型（用于风扇曲线、热沉曲线等）：

| 类型 | 数据点 |
|------|--------|
| `fan_curve_points` | volume_flow + pressure |
| `heat_sink_curve_points` | speed + thermal_resistance |
| `capacity_curve_points` | temperature + power |
| `power_temp_curve_points` | temperature + power |
| `conductivity_curve_points` | temperature + conductivity |

### 3. XmlAttributes.xsd — 属性定义

定义 `<attributes>` 下所有属性的具体字段：

#### 材料类
| 属性 | 说明 |
|------|------|
| `isotropic_material_att` | 各向同性材料（导热率、密度、比热） |
| `orthotropic_material_att` | 正交各向异性材料（x/y/z 三个方向导热率） |
| `biaxial_material_att` | 双轴材料（in_plane + normal，如 PCB） |
| `temperature_dependant_material_att` | 温度相关材料 |

#### 边界条件类
| 属性 | 说明 |
|------|------|
| `surface_att` | 表面属性（emissivity、roughness、display_settings） |
| `surface_exchange_att` | 表面换热（calculated / constant / profile） |
| `thermal_att` | 热模型（conduction / fixed_heat_flow / fixed_temperature / joule_heating） |
| `source_att` | 热源（total / volume / area / fixed / linear / non_linear） |
| `radiation_att` | 辐射模型（non_radiating / single_radiating / subdivided_radiating） |
| `ambient_att` | 环境条件（temperature、pressure、velocity、concentration 等） |

#### 其他
| 属性 | 说明 |
|------|------|
| `resistance_att` | 流阻（planar / volume，含 free_area_ratio、loss_coefficient） |
| `fan_att` | 风扇（normal / angled / swirl / circular，支持 fan_curve） |
| `fluid_att` | 流体属性（导热率、粘度、密度、比热） |
| `grid_constraint_att` | 网格约束（min_cell_size、max_size、inflation） |
| `transient_att` | 瞬态函数（profile / function，含 linear、exponential、sinusoidal 等 7 种子函数） |
| `control_att` | 控制曲线（frequency_curves，含 temp_low/temp_high/power_temp_curve） |

### 4. XmlEntities.xsd — 求解/网格/模型配置

#### model（求解模式）
| 字段 | 选项 |
|------|------|
| solution | flow_heat / flow_only / conduction_only |
| dimensionality | 2d / 3d |
| radiation | off / on / high_accuracy |
| turbulence | laminar / turbulent（含多种湍流模型） |
| gravity | off / normal / angled |
| solar_radiation | 太阳辐射参数 |

#### solve（求解器控制）
| 字段 | 说明 |
|------|------|
| overall_control | 求解器选项、外迭代次数、收敛判据 |
| variable_controls | 各求解变量的 false_time_step、terminal_residual |
| solver_controls | 松弛因子、误差计算频率 |

#### grid（网格）
| 字段 | 说明 |
|------|------|
| system_grid | 系统网格 x/y/z 方向（min_size、min_number、max_size） |
| patches | 局部网格加密（applies_to、start/end_location、cell_distribution） |

### 5. XmlGeometry.xsd — 几何体定义

#### 几何类型
| 类型 | 说明 |
|------|------|
| `cuboid` | 长方体（最常用，支持 holes） |
| `plate` | 薄板（collapse 展开方式） |
| `prism` | 棱柱体 |
| `tet` | 四面体 |
| `inverted_tet` | 倒四面体 |
| `sloping_block` | 斜块 |
| `assembly` | 装配体（嵌套子 geometry） |
| `fan` | 风扇几何 |
| `vent` | 通风口 |
| `opening` | 开口 |
| `source` | 热源几何 |
| `monitor_point` | 监控点 |

#### 几何体通用字段
每个几何体都可以按名称引用 attributes 中定义的属性：

| 字段 | 引用的属性 |
|------|-----------|
| `material` | isotropic/orthotropic/biaxial material |
| `thermal` | thermal_att |
| `x_high_surface` 等 | surface_att（按面指定） |
| `all_surface` | surface_att（所有面） |
| `x_high_radiation` 等 | radiation_att（按面指定） |
| `x_high_surface_exchange` 等 | surface_exchange_att（按面指定） |
| `x_grid_constraint` 等 | grid_constraint_att |
| `source` | source_att |
| `fan` | fan_att |
| `ambient` | ambient_att |
| `resistance` | resistance_att |

## 推荐阅读顺序

```
XmlDefinitions.xsd   ← 先看，理解基础类型（triplet、枚举值等）
       ↓
XmlAttributes.xsd    ← 看属性有哪些字段和合法枚举值
       ↓
XmlEntities.xsd      ← 看求解/网格配置结构
       ↓
XmlGeometry.xsd      ← 看几何体字段（哪些面可以挂什么属性）
       ↓
xmlSchema.xsd        ← 最后看，把上面串起来理解完整结构
```

## XSD 阅读要点

| 语法 | 含义 |
|------|------|
| `minOccurs="0"` | 可选字段 |
| `minOccurs="1"` | 必填字段 |
| `<xs:enumeration value="xxx"/>` | 合法枚举值 |
| `<xs:restriction>` | 值约束（范围、类型） |
| `type="xs:string"` | 字符串，通常是引用属性名 |
| `<xs:all>` | 子元素无序，最多出现一次 |
| `<xs:sequence>` | 子元素有序 |
| `<xs:choice>` | 多选一 |
| `maxOccurs="unbounded"` | 可出现任意次 |
