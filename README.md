# FloTHERM 自动化工具

用于批量修改 ECXML/Pack 参数、自动求解和生成仿真案例的 Python 脚本。

**支持格式**：`.ecxml` | `.pack` | `.pdml` | `.prj`

兼容 **FloTHERM 2020.2** 及其他版本。

## 文件说明

| 文件 | 功能 |
|-----|------|
| `simple_solver.py` | **简易求解脚本**（推荐，支持 ECXML/Pack） |
| `pack_editor.py` | **Pack 文件编辑器**（新增） |
| `flotherm_solver.py` | 完整求解脚本（生成 FloSCRIPT XML） |
| `ecxml_editor.py` | ECXML 文件解析和参数修改 |
| `batch_simulation.py` | 批量仿真案例生成器 |
| `power_config.json` | 功耗配置示例 |

---

## 快速开始

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
