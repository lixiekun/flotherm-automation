# FloTHERM 自动化工具

用于批量修改 ECXML/Pack 参数、自动求解和生成仿真案例的 Python 脚本。

**支持格式**：`.ecxml` | `.pack` | `.pdml` | `.prj`

兼容 **FloTHERM 2020.2** 及其他版本。

## ⚠️ 重要说明

**FloSCRIPT XML 和 FloXML 是两种完全不同的格式！**

| 格式 | 用途 | 使用方式 |
|-----|------|---------|
| **FloSCRIPT XML** | 自动化脚本 | `flotherm -b -f script.xml` |
| **FloXML** | 导入模型 | GUI 中 File → Import |
| **ECXML** | 行业标准模型交换 | JEDEC JEP181 格式 |

如果遇到错误 `Failed unknown file type No reader for this file type`，说明 XML 格式不正确。请使用 **GUI 录制宏** 的方式获取正确的 FloSCRIPT XML。

## 文件说明

| 文件 | 功能 |
|-----|------|
| `floscript_runner.py` | **⭐ 推荐使用** - 整合模型 + 录制宏，自动求解 |
| `simple_solver.py` | 简易求解脚本（支持 ECXML/Pack） |
| `pack_editor.py` | Pack 文件编辑器 |
| `ecxml_editor.py` | ECXML 文件解析和参数修改 |
| `batch_simulation.py` | 批量仿真案例生成器 |
| `create_floscript_guide.py` | FloSCRIPT 创建指南 |
| `power_config.json` | 功耗配置示例 |

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

## ⭐ 推荐工作流：ECXML + 录制宏

这是最可靠的自动化方式，结合了 ECXML 参数修改和 FloSCRIPT 宏。

### 步骤概览

```
┌─────────────────────────────────────────────────────────────┐
│  Step 1: 在 GUI 中录制宏（一次性）                           │
│  ─────────────────────────────────────────────────────────  │
│  1. 打开 FloTHERM GUI                                       │
│  2. 打开任意模型                                            │
│  3. Tools → Macro → Record                                  │
│  4. 执行: Reinitialize → Solve                              │
│  5. Tools → Macro → Stop Recording                          │
│  6. 保存为: solve_macro.xml                                 │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│  Step 2: 使用 Python 自动化                                 │
│  ─────────────────────────────────────────────────────────  │
│  # 修改 ECXML 功耗 + 自动求解                               │
│  python floscript_runner.py model.ecxml solve_macro.xml \   │
│      -o ./results --power U1_CPU 15.0                       │
│                                                             │
│  # 批量参数扫描                                             │
│  python floscript_runner.py model.ecxml solve_macro.xml \   │
│      -o ./results --power-range U1_CPU 5 10 15 20 25        │
└─────────────────────────────────────────────────────────────┘
```

### 使用示例

```bash
# 1. 基本用法：ECXML + 宏
python floscript_runner.py model.ecxml solve_macro.xml -o ./results

# 2. 修改功耗后求解
python floscript_runner.py model.ecxml solve_macro.xml -o ./results \
    --power U1_CPU 15.0 --power U2_GPU 25.0

# 3. 批量参数扫描（5个功耗点）
python floscript_runner.py model.ecxml solve_macro.xml -o ./results \
    --power-range U1_CPU 5 10 15 20 25

# 4. Pack 文件也支持
python floscript_runner.py model.pack solve_macro.xml -o ./results
```

### 输出目录结构

```
./results/
├── solver_script.xml      # 生成的完整 FloSCRIPT
├── simulation.log         # 求解日志
├── result.pack            # 求解结果
└── (批量时)
    ├── power_5W/
    ├── power_10W/
    ├── power_15W/
    └── ...
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
