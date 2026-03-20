# FloTHERM 自动化工具

用于批量修改 ECXML/Pack 参数、自动求解和生成仿真案例的 Python 脚本。

**兼容 FloTHERM 2020.2**

---

## ⚠️ 实际测试结论

### 核心发现

经过实际测试，**FloTHERM 2020.2 的自动化能力**：

| 方式 | 可行性 | 说明 |
|-----|--------|------|
| **`-z` 参数求解** | ✅ **可行** | `flotherm -b model.ecxml -z output.pack` |
| 命令行无头模式 | ⚠️ 部分支持 | 只支持 `.prj` 和 `.floxml` 完全无头 |
| COM API | ❌ 不可用 | 2020.2 版本不支持 |
| Python API | ❌ 不可用 | 2020.2 版本不支持 |
| FloSCRIPT 宏 | ⚠️ 部分可用 | 需要打开 GUI，手动点击运行 |

### ✅ 推荐方案：`-z` 参数批量求解

**命令格式**：
```bash
flotherm -b model.ecxml -z output.pack
```

**说明**：
- `-b` 批处理模式
- `-z` 指定输出 PACK 文件
- 会打开 GUI 窗口，求解完成后自动关闭
- 结果保存到指定的 PACK 文件

**批量处理**：
```bash
python batch_ecxml_solver.py input_folder -o output_folder
```

### ⚠️ 备选方案：FloSCRIPT 宏 + 手动执行

如果 `-z` 参数不可用，可以使用 FloSCRIPT 宏：

**工作流程**：
1. 打开 FloTHERM GUI
2. 加载录制的 FloSCRIPT 宏
3. **手动点击运行按钮**
4. 宏自动执行：打开文件 → 求解 → 保存

**限制**：
- 必须打开 GUI
- 必须手动点击运行

---

## FloSCRIPT 宏使用方法

### 录制宏

1. 启动 FloTHERM GUI
2. 打开你的模型（.pack 或 .prj 文件）
3. 菜单 **Tools → Macro → Record...**
4. 执行你想要的操作：
   - Model → Reinitialize（重新初始化）
   - Model → Solve（求解）
   - File → Save As...（保存结果）
5. 菜单 **Tools → Macro → Stop Recording**
6. 保存宏文件（.xml）

### 运行宏

1. 打开 FloTHERM GUI
2. 菜单 **Tools → Macro → Play...**
3. 选择录制的宏文件
4. **点击运行**

### 宏文件示例

```xml
<?xml version="1.0" encoding="UTF-8"?>
<FloSCRIPT version="1.0">
    <Command name="Open" file="C:\path\to\model.pack"/>
    <Command name="Reinitialize"/>
    <Command name="Solve"/>
    <Command name="Save" file="C:\path\to\model_solved.pack"/>
</FloSCRIPT>
```

### 批量处理（半自动）

用 Python 脚本生成多个宏文件，然后逐个手动运行：

```bash
# 生成多个宏文件
python batch_pack_solver.py pack1.pack pack2.pack pack3.pack -o ./macros

# 然后在 GUI 中逐个手动运行每个宏
```

---

## 文件说明

### 核心脚本

| 文件 | 功能 | 状态 |
|-----|------|------|
| `excel_batch_simulation.py` | **⭐⭐ Excel 多配置批量仿真（推荐）** | ✅ 可用 |
| `batch_ecxml_solver.py` | **⭐ ECXML 批量求解器（使用 -z 参数）** | ✅ 可用 |
| `test_flotherm_api.py` | FloTHERM API 可用性测试脚本 | ✅ 可用 |
| `batch_simulation.py` | 批量仿真案例生成器 | ✅ 可用 |
| `batch_pack_solver.py` | 批量生成 FloSCRIPT 宏 | ⚠️ 需配合手动执行 |
| `flotherm_batch_solver.py` | 命令行批处理求解器 | ❌ 实际不可用 |

### 文件解析器

| 文件 | 支持格式 | 功能 |
|-----|---------|------|
| `ecxml_editor.py` | **ECXML** | JEDEC JEP181 标准器件热模型解析和修改 |
| `pdml_parser.py` | **PDML** | FloTHERM 原生 PDML 项目文件解析 |
| `floxml_grid_parser.py` | **FloXML** | FloXML 网格设置解析 (支持 high_inflation) |
| `pack_editor.py` | **Pack** | Pack 压缩包解压、查看、修改功耗 |

### 格式转换器

| 文件 | 功能 | 状态 |
|-----|------|------|
| `ecxml_to_floxml_converter.py` | **⭐ ECXML → FloXML 转换器** | ✅ 可用 |
| `wrap_geometry_floxml_as_project.py` | Assembly FloXML → Project FloXML 包装 | ✅ 可用 |

---

## 可用功能

### ⭐⭐ Excel 多配置批量仿真（推荐）

从 Excel 读取多个配置，自动修改 ECXML 模板并批量求解：

```bash
# 基本用法
python excel_batch_simulation.py template.ecxml config.xlsx -o ./output

# 指定 FloTHERM 路径
python excel_batch_simulation.py template.ecxml config.xlsx -o ./output --flotherm "C:\...\flotherm.exe"

# 仅生成 ECXML，不求解
python excel_batch_simulation.py template.ecxml config.xlsx -o ./output --no-solve

# 使用指定 sheet
python excel_batch_simulation.py template.ecxml config.xlsx -o ./output --sheet "配置1"

# 仅预览配置（不执行）
python excel_batch_simulation.py template.ecxml config.xlsx -o ./output --dry-run
```

#### Excel 格式

**简单格式（推荐）**：

| config_name | U1_CPU | U2_GPU | Ambient |
|-------------|--------|--------|---------|
| case1       | 10     | 5      | 25      |
| case2       | 15     | 8      | 35      |
| case3       | 20     | 10     | 40      |

- 第一列必须是 `config_name`（配置名称）
- 其他列名对应 ECXML 中的器件名或边界条件名
- 数值自动识别：功耗（W）或温度（°C）

#### 流程图

```mermaid
flowchart LR
    A[📊 Excel 配置] --> B[📝 修改 ECXML 模板]
    B --> C[⚙️ 批量求解]
    C --> D[📋 生成报告]

    style A fill:#e8f5e9
    style B fill:#fff3e0
    style C fill:#e3f2fd
    style D fill:#f3e5f5
```

#### 输出目录结构

```
output/
└── batch_20260309_100000/
    ├── case1.ecxml          # 修改后的 ECXML
    ├── case1.pack           # 求解结果
    ├── case1_report.html    # 单个报告
    ├── case2.ecxml
    ├── case2.pack
    ├── case2_report.html
    ├── ...
    ├── batch_report.txt     # 批量求解报告
    └── summary.xlsx         # 配置+结果汇总
```

#### 依赖

```bash
pip install openpyxl  # 或
pip install pandas
```

---

### ⭐ 批量 ECXML 求解（推荐）

使用 `-z` 参数批量求解 ECXML 文件：

```bash
# 单文件求解
flotherm -b model.ecxml -z output.pack -r report.html

# 批量求解（Python 脚本）
python batch_ecxml_solver.py ./input_folder -o ./output_folder

# 指定 FloTHERM 路径
python batch_ecxml_solver.py ./input -o ./output --flotherm "C:\Program Files\Siemens\SimcenterFlotherm\2020.2\bin\flotherm.exe"

# 仅查看将要处理的文件（不执行）
python batch_ecxml_solver.py ./input -o ./output --dry-run
```

#### 流程图

```mermaid
flowchart TB
    A[📁 输入文件夹<br/>包含多个 .ecxml 文件] --> B[🔍 扫描文件]
    B --> C[⚙️ 逐个求解]
    C --> D["执行命令:<br/>flotherm -b model.ecxml<br/>-z output.pack<br/>-r report.html"]
    D --> E[📋 实时日志输出]
    E --> F{求解完成?}
    F -->|是| G[📊 生成报告]
    F -->|否| C
    G --> H[📁 输出结果]

    style A fill:#e3f2fd
    style C fill:#f3e5f5
    style D fill:#fff3e0
    style H fill:#c8e6c9
```

**命令参数说明：**

| 参数 | 说明 |
|-----|------|
| `flotherm` | FloTHERM 可执行文件 |
| `-b` | 批处理模式 |
| `-z output.pack` | 指定输出 PACK 文件路径 |
| `-r report.html` | 指定输出 HTML 报告路径 |

#### 输出目录结构

```
output_folder/
└── batch_20260304_153045/          # 带时间戳的子文件夹
    ├── model1.pack                 # 求解结果
    ├── model1_report.html          # HTML 求解报告
    ├── model2.pack
    ├── model2_report.html
    ├── ...
    └── batch_report.txt            # 批量求解总结报告
```

#### 输出示例

```
============================================================
  [1/5] 正在求解: model1.ecxml
============================================================
  输入: ./input/model1.ecxml
  输出: ./output/batch_20260304_153045/model1.pack
  开始时间: 2026-03-04 15:30:45
  (命令行会等待求解完成，请勿关闭)

  ⠋ 求解中... 15秒
    📋 Solving iteration 150...
    📋 Convergence: 0.00123

  ✅ 求解完成!
     耗时: 125.3 秒
     文件大小: 15.23 MB
```

### 1. Pack 文件操作

```bash
# 列出 pack 文件内容
python pack_editor.py model.pack --list

# 解压 pack 文件
python pack_editor.py model.pack --extract ./extracted

# 提取 XML 文件
python pack_editor.py model.pack --to-ecxml output.xml

# 修改 pack 中的功耗
python pack_editor.py model.pack --set-power U1_CPU 15.0 -o modified.pack

# 批量修改功耗
python pack_editor.py model.pack --power-config power.json -o modified.pack
```

### 2. ECXML 文件操作

```bash
# 分析结构
python ecxml_editor.py model.ecxml --analyze

# 查看基本信息
python ecxml_editor.py model.ecxml --info

# 修改单个器件功耗
python ecxml_editor.py model.ecxml --set-power U1_CPU 15.0 -o modified.ecxml

# 批量修改（从配置文件）
python ecxml_editor.py model.ecxml --power-config power_config.json -o modified.ecxml

# 导出器件列表到 CSV
python ecxml_editor.py model.ecxml --export-csv components.csv
```

**power_config.json 格式**：
```json
{
    "U1_CPU": 15.0,
    "U2_GPU": 25.0,
    "U3_DDR": 5.0
}
```

### 3. 批量生成仿真案例

```bash
# CPU 功耗从 5W 到 25W，生成 5 个仿真案例
python batch_simulation.py template.ecxml \
    --component U1_CPU \
    --powers 5 10 15 20 25 \
    -o ./simulations
```

**注意**：生成的案例文件需要手动在 FloTHERM GUI 中打开并求解。

---

## ECXML to FloXML 转换器

将 JEDEC JEP181 ECXML 器件热模型转换为完整的 FloTHERM FloXML 项目文件。

### 背景

ECXML 是器件级热模型交换格式，缺少：
- 网格设置 (grid)
- 求解器配置 (solve)
- 模型设置 (model)
- 求解域 (solution_domain)

本工具自动补充这些配置，生成可直接导入 FloTHERM 的完整项目文件。

### 使用方法

```bash
# 单文件转换
python ecxml_to_floxml_converter.py input.ecxml -o output.xml

# 批量转换
python ecxml_to_floxml_converter.py *.ecxml --output-dir ./floxml/

# 自定义参数
python ecxml_to_floxml_converter.py input.ecxml -o output.xml \
    --padding-ratio 0.15 \
    --ambient-temp 308.15 \
    --outer-iterations 1000
```

### CLI 参数

| 参数 | 说明 | 默认值 |
|-----|------|--------|
| `-o, --output` | 输出文件路径 | `<input>_floxml.xml` |
| `--output-dir` | 输出目录 (批量模式) | 当前目录 |
| `--padding-ratio` | 求解域 padding 比例 | 0.1 |
| `--minimum-padding` | 最小 padding (米) | 0.01 |
| `--ambient-temp` | 环境温度 (K) | 300 |
| `--outer-iterations` | 求解迭代次数 | 500 |
| `-v, --verbose` | 详细输出 | - |

### 转换映射

| ECXML | FloXML | 说明 |
|-------|--------|------|
| `Component/@name` | `cuboid/name` | 组件名称 |
| `Position/@x,y,z` | `position/x,y,z` | 位置坐标 |
| `Size/@width,height,depth` | `size/x,y,z` | 尺寸 |
| `powerDissipation` | `source` 属性 | 热源 |
| `Material/@name` | `material` 引用 | 材料 |

### 输出结构

```xml
<xml_case>
  <name>{project_name}_Project</name>
  <model>...</model>           <!-- 自动生成 -->
  <solve>...</solve>           <!-- 自动生成 -->
  <grid>...</grid>             <!-- 根据求解域自动计算 -->
  <attributes>...</attributes> <!-- 材料、热源、环境、流体 -->
  <geometry>...</geometry>     <!-- 从 ECXML 转换 -->
  <solution_domain>...</solution_domain> <!-- 自动计算边界框+padding -->
</xml_case>
```

---

## FloXML 包装工具

有些官方 Excel 模板导出的不是完整项目 FloXML，而是 `geometry/assembly FloXML`。

典型现象：
- 文件里只有 `<attributes>` 和 `<geometry>`
- 直接按“项目 FloXML”导入会报 `Geometry file detected`

这时可以用：

```bash
python wrap_geometry_floxml_as_project.py input.xml -o output_project.xml
```

### 输入文件要求

这个脚本的 **输入必须满足**：

1. 必须是 `.xml`
2. 必须是 FloXML 文件，根节点要是 `<xml_case>`
3. 必须包含 `<geometry>`
4. 适合输入“几何级/装配级 FloXML”
5. **不能输入** Excel 文件，比如 `.xlsm/.xlsx`
6. **不能输入** 已经是完整项目的 FloXML

### 哪些文件可以输入

可以：
- `Advanced-Resistance.xlsm` 导出的 `.xml`
- `Windtunnel-AdvancedResistance.xlsm` 导出的 `.xml`
- 官方 `Assembly FloXML Examples/*.xml`

不可以：
- `Windtunnel-AdvancedResistance.xlsm` 这种 Excel 模板本身
- 已经带有 `<model>`、`<solve>`、`<grid>`、`<solution_domain>` 的 project FloXML

### 输出文件是什么

输出是一个最小可用的 **project FloXML**，脚本会：
- 保留原来的 `<attributes>`
- 保留原来的 `<geometry>`
- 自动补上 `<model>`
- 自动补上 `<solve>`
- 自动补上 `<grid>`
- 自动补上 `<solution_domain>`
- 如果缺少环境/流体定义，会自动补一个默认 `Ambient` 和 `Air`

### 示例

```bash
python wrap_geometry_floxml_as_project.py ^
  "D:\Program Files\Siemens\SimcenterFlotherm\2504\flotherm-automation\floxml_output\windtunnel_advres\PCB_ADV_RES.xml" ^
  -o "D:\Program Files\Siemens\SimcenterFlotherm\2504\flotherm-automation\floxml_output\windtunnel_advres\PCB_ADV_RES_project.xml"
```

---

## 文件格式对比：ECXML vs FloXML

### 基本定位

| 特性 | ECXML | FloXML |
|------|-------|--------|
| **全称** | Electronics Cooling eXtensible Markup Language | FloTHERM XML |
| **标准** | **JEDEC JEP181** (行业标准) | **Siemens/Mentor 私有格式** |
| **目的** | 电子器件热模型**交换** | FloTHERM **项目/装配体**定义 |
| **受众** | 芯片供应商 → 系统工程师 | FloTHERM 软件用户 |
| **范围** | **器件级** (Package, Die, PCB) | **系统级** (完整仿真项目) |
| **扩展名** | `.ecxml` | `.xml` |

### 功能对比

| 功能 | ECXML | FloXML |
|------|:-----:|:------:|
| 器件封装描述 | ✅ 核心功能 | ⚠️ 基本支持 |
| Die/芯片细节 | ✅ 详细 | ❌ 无 |
| 热阻网络 (CTM) | ✅ 支持 | ❌ 无 |
| 求解器设置 | ❌ 无 | ✅ 完整 |
| 网格设置 | ❌ 无 | ✅ 完整 |
| 流体/风扇 | ❌ 无 | ✅ 完整 |
| 边界条件 | ⚠️ 基础 | ✅ 完整 |
| 瞬态分析 | ⚠️ 基础 | ✅ 完整 |
| 辐射模型 | ❌ 无 | ✅ 支持 |
| 跨软件兼容 | ✅ **行业标准** | ❌ 仅 FloTHERM |

### 结构示例

**ECXML** (器件热模型)：
```xml
<ecxml xmlns="http://www.jedec.org/ecxml">
  <Component name="CPU_Package">
    <Geometry>
      <Size width="0.017" height="0.017" depth="0.001"/>
    </Geometry>
    <Material>
      <Conductivity>150</Conductivity>
    </Material>
    <PowerDissipation>5.0</PowerDissipation>
    <Die>
      <Size width="0.006" height="0.005"/>
    </Die>
  </Component>
</ecxml>
```

**FloXML** (完整仿真项目)：
```xml
<xml_case>
  <name>My_Thermal_Simulation</name>
  <model>
    <modeling>
      <solution>flow_heat</solution>
      <radiation>on</radiation>
    </modeling>
  </model>
  <grid>
    <system_grid>
      <x_grid><min_size>0.001</min_size></x_grid>
    </system_grid>
  </grid>
  <solve>
    <overall_control>
      <outer_iterations>500</outer_iterations>
    </overall_control>
  </solve>
  <attributes>
    <materials>...</materials>
  </attributes>
  <solution_domain>
    <size><x>0.3</x><y>0.2</y><z>0.1</z></size>
  </solution_domain>
  <geometry>
    <cuboid>
      <name>HeatSink</name>
      <material>Aluminum</material>
    </cuboid>
  </geometry>
</xml_case>
```

### 使用场景

```
┌─────────────────────────────────────────────────────────────┐
│                     供应链流程                               │
├─────────────────────────────────────────────────────────────┤
│   芯片供应商                      系统集成商                  │
│  ┌──────────┐                    ┌──────────┐               │
│  │ 芯片设计  │                    │ PCB设计   │               │
│  │ 热测试    │  ──ECXML──►        │ 系统仿真  │               │
│  └──────────┘                    └──────────┘               │
│                                                             │
│                    ┌──────────────────────┐                 │
│                    │  FloTHERM 仿真项目    │                 │
│                    │  (FloXML 格式)        │                 │
│                    │  - 导入 ECXML 器件    │                 │
│                    │  - 求解域、网格       │                 │
│                    │  - 边界条件、风扇     │                 │
│                    └──────────────────────┘                 │
└─────────────────────────────────────────────────────────────┘
```

### FloXML Schema 文件

本项目的 `examples/` 目录包含完整的 FloXML Schema 定义：

```
examples/DCIM Development Toolkit/Schema Files/FloXML/
├── xmlSchema.xsd         # 基础类型定义
├── XmlDefinitions.xsd    # 根元素定义
├── XmlAttributes.xsd     # 属性定义 (材料、表面、热源等)
├── XmlGeometry.xsd       # 几何实体 (cuboid, prism, cylinder等)
└── XmlEntities.xsd       # 模型/求解/网格设置
```

### FloXML 两种类型

| 类型 | 说明 | 根元素内容 |
|------|------|-----------|
| **Assembly FloXML** | 几何装配体 | 仅 `<attributes>` + `<geometry>` |
| **Project FloXML** | 完整项目 | `<model>` + `<solve>` + `<grid>` + `<attributes>` + `<geometry>` + `<solution_domain>` |

**注意**：Assembly FloXML 需要包装成 Project FloXML 才能作为项目导入。

---

## 总结

**FloTHERM 2020.2 自动化现状**：

- ✅ **`-z` 参数求解 ECXML**：`flotherm -b model.ecxml -z output.pack`
- ⚠️ 会打开 GUI，但求解完成后自动关闭
- ✅ 可以用 Python 脚本批量处理
- ❌ COM/Python API 不可用
- ⚠️ FloSCRIPT 宏可用，但需要手动点击运行

**推荐工作流**：
1. 用 `batch_ecxml_solver.py` 批量求解 ECXML 文件
2. 或者用 Python 脚本修改参数后批量求解
3. 升级到更新版本可能支持更好的自动化
