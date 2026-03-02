# FloTHERM 自动化工具

用于批量修改 ECXML/Pack 参数、自动求解和生成仿真案例的 Python 脚本。

**支持格式**：`.prj` | `.floxml` | `.xml` (FloSCRIPT)

兼容 **FloTHERM 2020.2** 及其他版本。

## ⚠️ 调研结论

### 命令行参数（官方文档）

| 参数 | 功能 | 示例 |
|-----|------|------|
| `-batch` | 批处理模式 | `flotherm.exe -batch "project.prj"` |
| `-nogui` | 无界面模式 | `flotherm.exe -batch "project.prj" -nogui` |
| `-solve` | 强制求解 | `flotherm.exe -batch "project.prj" -solve` |
| `-out` | 日志输出 | `flotherm.exe -batch "project.prj" -out "log.txt"` |
| `-b` | 批处理/无头模式 | `flotherm -b model.floxml` |
| `-f` | 执行脚本文件 | `flotherm -b -f script.xml` |

### 文件格式支持

| 格式 | 说明 | 批处理命令 |
|-----|------|----------|
| **.prj** | 项目文件夹 | ✅ `flotherm -batch "project.prj" -nogui -solve` |
| **.floxml** | FloXML 模型文件 | ✅ `flotherm -b model.floxml` |
| **.xml** (FloSCRIPT) | 自动化脚本 | ✅ `flotherm -b -f script.xml` |
| **.pack** | Pack 打包文件 | ❓ 需要先导入到项目 |
| **.pdml** | PDML 模型文件 | ❓ 需要先导入到项目 |
| **.ecxml** | ECXML 格式 | ❓ 需要先导入到项目 |

### FloSCRIPT vs FloXML（重要！）

**这两种 XML 格式完全不同，不能混用！**

| 类型 | 用途 | 执行方式 |
|-----|------|---------|
| **FloSCRIPT** | 自动化脚本，包含操作命令 | `flotherm -b -f script.xml` |
| **FloXML** | 模型数据，包含几何和参数 | `flotherm -b model.floxml` |

**错误示例**：
```
ERROR E/11029 - Failed unknown file type No reader for this file type
```
这是因为 FloSCRIPT XML 不能通过 FloXML 模块导入。

### 推荐工作流

| 场景 | 推荐方案 |
|-----|---------|
| **有 .prj 项目文件** | `flotherm -batch "project.prj" -nogui -solve` |
| **有 .floxml 文件** | `flotherm -b model.floxml` |
| **有 .pack 文件** | 在 GUI 中录制宏，然后 `flotherm -b -f macro.xml` |
| **需要修改参数** | 使用 FloSCRIPT 宏或修改 FloXML |
| **多个 Pack 文件** | 使用 `batch_pack_solver.py` 批量处理 |

## 文件说明

| 文件 | 功能 |
|-----|------|
| `flotherm_batch_solver.py` | **⭐ 推荐使用** - 基于官方文档的批处理求解器 |
| `batch_pack_solver.py` | **🆕 批量 Pack 文件求解器** |
| `floscript_runner.py` | 整合模型 + 录制宏，自动求解 |
| `pack_to_floxml_converter.py` | Pack → FloXML 自动转换器 |
| `simple_solver.py` | 简易求解脚本（支持 ECXML/Pack） |
| `pack_editor.py` | Pack 文件编辑器 |
| `ecxml_editor.py` | ECXML 文件解析和参数修改 |
| `batch_simulation.py` | 批量仿真案例生成器 |
| `create_floscript_guide.py` | FloSCRIPT 创建指南 |
| `power_config.json` | 功耗配置示例 |

---

## 🆕 批量处理多个 Pack 文件

### 问题：宏录制需要先打开文件，如何批量处理？

**解决方案**：用 Python 动态生成 FloSCRIPT XML，替换文件路径

### 使用方法

```bash
# 批量处理多个 Pack 文件
python batch_pack_solver.py pack1.pack pack2.pack pack3.pack -o ./results

# 使用通配符
python batch_pack_solver.py *.pack -o ./results

# 并行执行（Windows）
python batch_pack_solver.py *.pack -o ./results --parallel 4

# 使用自定义宏模板
python batch_pack_solver.py *.pack -o ./results --template my_macro.xml
```

### 工作原理

```
┌─────────────────────────────────────────────────────────────┐
│  Step 1: 准备 FloSCRIPT 模板                                │
│  ─────────────────────────────────────────────────────────  │
│  <?xml version="1.0" encoding="UTF-8"?>                     │
│  <FloSCRIPT version="1.0">                                  │
│      <Command name="Open" file="{pack_file}"/>              │
│      <Command name="Reinitialize"/>                         │
│      <Command name="Solve"/>                                │
│      <Command name="Save" file="{output_file}"/>            │
│  </FloSCRIPT>                                               │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│  Step 2: Python 为每个 Pack 文件生成 FloSCRIPT              │
│  ─────────────────────────────────────────────────────────  │
│  floscript_model1.xml  →  打开 model1.pack → 求解 → 保存    │
│  floscript_model2.xml  →  打开 model2.pack → 求解 → 保存    │
│  floscript_model3.xml  →  打开 model3.pack → 求解 → 保存    │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│  Step 3: 批量执行                                           │
│  ─────────────────────────────────────────────────────────  │
│  flotherm -b -f floscript_model1.xml                        │
│  flotherm -b -f floscript_model2.xml                        │
│  flotherm -b -f floscript_model3.xml                        │
└─────────────────────────────────────────────────────────────┘
```

### 自定义宏模板

你可以录制一个宏作为模板，确保包含占位符：

```xml
<?xml version="1.0" encoding="UTF-8"?>
<FloSCRIPT version="1.0">
    <!-- {pack_file} 会被替换为实际 Pack 文件路径 -->
    <Command name="Open" file="{pack_file}"/>
    <Command name="Reinitialize"/>
    <Command name="Solve"/>
    <!-- {output_file} 会被替换为输出文件路径 -->
    <Command name="Save" file="{output_file}"/>
</FloSCRIPT>
```

### 输出目录结构

```
./results/
├── batch_report.txt           # 批量处理报告
├── model1/
│   ├── floscript_model1.xml   # 生成的 FloSCRIPT
│   ├── simulation.log         # 求解日志
│   └── model1_solved.pack     # 求解后的模型
├── model2/
│   └── ...
└── model3/
    └── ...
```

---

## 如何创建正确的 FloSCRIPT XML

### 方法1: 在 FloTHERM GUI 中录制宏（推荐）

1. 启动 FloTHERM GUI
2. 打开你的模型（.pack 或 .prj 文件）
3. 菜单 **Tools → Macro → Record...**
4. 执行你想要的操作：
   - Model → Reinitialize（重新初始化）
   - Model → Solve（求解）
   - File → Save As...（保存结果）
5. 菜单 **Tools → Macro → Stop Recording**
6. 测试录制的宏：
   ```bash
   flotherm -b -f recorded_macro.xml
   ```

### 方法2: 使用官方示例

官方示例位置：
```
# FloTHERM 2020.2
C:\Program Files\Siemens\SimcenterFlotherm\2020.2\examples\FloSCRIPT\

# Schema 文档
C:\Program Files\Siemens\SimcenterFlotherm\2020.2\docs\Schema-Documentation\FloSCRIPT\
```

### 方法3: 使用辅助脚本

```bash
# 显示 GUI 录制步骤
python create_floscript_guide.py --show-gui-steps

# 列出官方示例位置
python create_floscript_guide.py --list-examples

# 创建基本模板
python create_floscript_guide.py --create-template template.xml
```

---

## 🆕 Pack 到 FloXML 自动转换

由于 `flotherm -b` 只支持 FloXML 格式，Pack 文件需要先转换为 FloXML。

### 快速转换

```bash
# 单文件转换（自动尝试所有方法）
python pack_to_floxml_converter.py model.pack -o output.floxml

# 批量转换
python pack_to_floxml_converter.py *.pack --batch ./floxml_output/

# 仅显示手动转换指南
python pack_to_floxml_converter.py model.pack -o output.floxml --method guide
```

### 转换方法

| 方法 | 平台 | 说明 |
|-----|------|------|
| `auto` | 全部 | 自动尝试所有可用方法 |
| `cli` | 全部 | 尝试命令行参数转换 |
| `com` | Windows | 使用 COM 自动化控制 GUI |
| `applescript` | macOS | 使用 AppleScript 控制应用 |
| `guide` | 全部 | 显示手动转换指南 |

### 批量转换工作流

```bash
# 1. 生成批量转换脚本
python pack_to_floxml_converter.py *.pack --batch ./floxml_output/

# 2. 运行生成的辅助脚本（会依次打开每个 Pack 文件）
python ./floxml_output/batch_convert_helper.py

# 3. 在 GUI 中导出每个文件为 FloXML

# 4. 使用 floscript_runner.py 进行自动化求解
python floscript_runner.py ./floxml_output/model.floxml -o ./results
```

### Windows COM 自动化

如果你在 Windows 上安装了 `pywin32`，可以尝试 COM 自动化：

```bash
# 安装 pywin32
pip install pywin32

# 使用 COM 方法转换
python pack_to_floxml_converter.py model.pack -o output.floxml --method com
```

**注意**: COM 自动化需要 FloTHERM 正确注册 COM 组件，不同版本可能有所不同。

---

## ⭐ 推荐工作流：录制宏自动化

由于 FloTHERM GUI 没有 FloXML 导出功能，推荐使用宏录制方式进行自动化。

### 方法 1: 录制宏（推荐）

```
┌─────────────────────────────────────────────────────────────┐
│  Step 1: 在 GUI 中录制宏                                     │
│  ─────────────────────────────────────────────────────────  │
│  1. FloTHERM GUI → Tools → Macro → Record...               │
│  2. 打开 Pack 文件                                           │
│  3. Model → Reinitialize（重新初始化）                       │
│  4. Model → Solve（求解）                                    │
│  5. File → Save As... 保存结果                               │
│  6. Tools → Macro → Stop Recording                          │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│  Step 2: 批量执行宏                                          │
│  ─────────────────────────────────────────────────────────  │
│  flotherm -b -f recorded_macro.xml                          │
│                                                             │
│  或使用 Python 脚本批量处理：                                │
│  python floscript_runner.py model.pack -o ./results         │
└─────────────────────────────────────────────────────────────┘
```

### 方法 2: 如果你有 FloXML 文件

如果你通过某种方式获得了 FloXML 文件（例如从其他来源），可以直接使用：

```bash
# 直接执行 FloXML
python floscript_runner.py model.floxml -o ./results

# 修改功耗后执行
python floscript_runner.py model.floxml -o ./results \
    --power U1_CPU 15.0

# 批量参数扫描
python floscript_runner.py model.floxml -o ./results \
    --power-range U1_CPU 5 10 15 20 25
```

### 方法 3: 使用 ECXML（如果 GUI 支持导出）

部分版本的 FloTHERM 支持 ECXML 导出：

```bash
# 1. 在 GUI 中：File → Export → ECXML
# 2. 修改参数
python ecxml_editor.py model.ecxml --set-power U1_CPU 15.0 -o modified.ecxml

# 3. 尝试求解（可能需要 GUI）
python simple_solver.py modified.ecxml -o ./results
```

---

## 快速开始

### 0. 自动求解（使用录制的 FloSCRIPT）

```bash
# 使用录制的 FloSCRIPT XML（推荐，真正无头）
python simple_solver.py recorded_macro.xml -o ./results --mode floscript
```

### 1. 自动求解（最常用）

```bash
# ECXML 文件
python simple_solver.py model.ecxml -o ./results

# Pack 文件（自动解压并求解）
python simple_solver.py model.pack -o ./results

# 指定 FloTHERM 路径
python simple_solver.py model.pack -o ./results --flotherm "C:\Program Files\FloTHERM\v2020.2\bin\flotherm.exe"
```

**支持格式**：
- `.ecxml` - ECXML 格式
- `.pack` - Pack 格式（自动解压）
- `.pdml` - PDML 格式
- `.prj` - 项目文件

**特性**：
- ✅ 实时打印求解日志到命令行
- ✅ 自动保存日志到文件 (`simulation.log`)
- ✅ 统计输出文件
- ✅ 无需 GUI（无头模式）

**输出示例**：
```
============================================================
  FloTHERM 求解器
============================================================
  输入文件: model.ecxml
  输出目录: ./results
  日志文件: ./results/simulation.log
  FloTHERM: C:\Program Files\FloTHERM\v2020.2\bin\flotherm.exe
============================================================

------------------------------------------------------------
  实时日志
------------------------------------------------------------
  FloTHERM Version 2020.2
  Loading model...
  Reinitializing...
  Solving...
  Iteration 1: residual = 0.001234
  Iteration 2: residual = 0.000567
  ...
  Solution converged.
------------------------------------------------------------

[INFO] 进程返回码: 0
[INFO] 日志行数: 1234
[INFO] 总耗时: 125.3 秒
```

---

### 2. Pack 文件操作（新增）

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

---

### 3. 分析 ECXML 结构

首次使用时，先分析你的 ECXML 文件结构：

```bash
# 详细分析（推荐）
python ecxml_editor.py model.ecxml --analyze

# 查看基本信息
python ecxml_editor.py model.ecxml --info
```

---

### 3. 修改参数

```bash
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

---

### 4. 批量仿真

#### 参数化扫描
```bash
# CPU 功耗从 5W 到 25W，生成 5 个仿真案例
python batch_simulation.py template.ecxml \
    --component U1_CPU \
    --powers 5 10 15 20 25 \
    -o ./simulations
```

#### 多器件变化
创建 `multi_config.json`:
```json
{
    "cases": [
        {"name": "baseline", "powers": {"U1_CPU": 15, "U2_GPU": 20}},
        {"name": "high_power", "powers": {"U1_CPU": 25, "U2_GPU": 35}}
    ]
}
```

```bash
python batch_simulation.py template.ecxml --config multi_config.json -o ./simulations
```

#### 运行批量仿真
```bash
# Windows
./simulations/run_all.bat

# Linux
./simulations/run_all.sh
```

---

## 完整工作流示例

```bash
# 1. 导出 ECXML（在 FloTHERM GUI 中）
# File → Export → ECXML

# 2. 分析结构
python ecxml_editor.py model.ecxml --analyze

# 3. 修改参数
python ecxml_editor.py model.ecxml --set-power U1 20.0 -o modified.ecxml

# 4. 自动求解
python simple_solver.py modified.ecxml -o ./results

# 5. 查看结果
ls ./results/
# simulation.log  (求解日志)
# solved_project.pack  (求解后的项目)
```

---

## FloTHERM 命令行参数

| 参数 | 功能 |
|-----|------|
| `-batch` | 批处理模式 |
| `-nogui` | 无界面模式 |
| `-solve` | 执行求解 |
| `-out` | 日志输出路径 |
| `-macro` | 执行宏文件 |

---

## 注意事项

1. **首次使用**：先用 `--analyze` 查看 ECXML 结构，确认器件名称
2. **路径问题**：如果找不到 FloTHERM，使用 `--flotherm` 参数指定路径
3. **版本兼容**：ECXML 结构因版本不同可能有差异，脚本会自动检测

---

## 自定义修改

如果脚本无法正确解析你的 ECXML 文件，可能需要调整 `ecxml_editor.py` 中的解析逻辑：

```python
# 在 _parse_component 方法中调整选择器
power_elem = elem.find('.//Power')  # 根据实际标签名修改
```

运行 `--analyze` 后，你会看到实际的标签名，根据输出调整即可。
