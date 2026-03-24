# FloTHERM 批量仿真工具

使用 FloSCRIPT 宏自动化操作 FloTHERM，实现参数修改和批量求解。

## 核心功能

- **直接操作 Pack 文件** - 无需导出 FloXML
- **参数修改** - 功耗、温度、尺寸等
- **参数扫描** - 自动批量运行多个配置
- **全自动求解** - 生成脚本 → 修改参数 → 求解 → 保存

---

## 快速开始

```bash
cd batch_simulation

# 1. 创建配置文件 (修改 config.json)
# 2. 生成并执行
python batch_sim.py run config.json

# 3. 提取结果
python batch_sim.py extract output.pack -o results.json
```

---

## 命令详解

### generate - 生成 FloSCRIPT 脚本

```bash
python batch_sim.py generate config.json -o ./scripts
```

### run - 生成并执行（推荐）

```bash
python batch_sim.py run config.json

# 带超时
python batch_sim.py run config.json --timeout 7200

# 预览不执行
python batch_sim.py run config.json --dry-run
```

### extract - 提取结果

```bash
python batch_sim.py extract solved.pack -o results.json
python batch_sim.py extract solved.pack -o results.csv --format csv
```

### create-floxml - 创建 FloXML 项目

```bash
python batch_sim.py create-floxml -n MyProject -o project.xml
```

---

## 配置文件格式

### 1. 单次修改

```json
{
    "input_pack": "model.pack",
    "output_pack": "output.pack",
    "modifications": [
        {"type": "power", "component": "U1_CPU", "value": 15.0},
        {"type": "power", "component": "U2_GPU", "value": 10.0},
        {"type": "solver", "max_iterations": 500}
    ],
    "solve": true
}
```

### 2. 参数扫描

```json
{
    "input_pack": "model.pack",
    "output_pack": "output_{value}.pack",
    "parameter_sweep": {
        "component": "U1_CPU",
        "parameter": "power",
        "values": [5.0, 10.0, 15.0, 20.0]
    },
    "solve": true
}
```

会自动生成 4 个脚本，分别求解功耗 5W/10W/15W/20W 的情况。

---

## 支持的修改类型

| 类型 | 属性 | 说明 |
|------|------|------|
| `power` | component, value | 修改功耗 (W) |
| `solver` | max_iterations | 求解器迭代次数 |
| `size` | x, y, z | 修改尺寸 |
| `position` | x, y, z | 修改位置 |

---

## 工作流程

```
┌─────────────────────────────────────────────────────────────┐
│                    完整自动化流程                            │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  1. 准备 Pack 文件 (model.pack)                             │
│     ↓                                                       │
│  2. 编写配置文件 (config.json)                              │
│     ↓                                                       │
│  3. python batch_sim.py run config.json                     │
│     ├── 自动生成 FloSCRIPT 脚本                            │
│     ├── 调用 FloTHERM 执行                                  │
│     ├── 加载 Pack → 修改参数 → 求解 → 保存                  │
│     └── 输出结果 Pack                                       │
│     ↓                                                       │
│  4. python batch_sim.py extract output.pack -o results.json │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 目录结构

```
batch_simulation/
├── batch_sim.py           # 主入口
├── README.md              # 本文档
├── config/                # 配置读取
│   ├── __init__.py
│   └── excel_config_reader.py
├── floscript/             # FloSCRIPT 生成和执行
│   ├── __init__.py
│   ├── builder.py         # 脚本构建器
│   ├── batch_generator.py # 批量生成
│   └── executor.py        # FloTHERM 执行器
├── floxml/                # FloXML 创建
│   ├── __init__.py
│   └── creator.py
├── example_config.json    # 配置示例
├── example_param_sweep.json
└── tests/                 # 单元测试
```

---

## FloSCRIPT 构建器 API

```python
from floscript.builder import FloScriptCommandBuilder

builder = FloScriptCommandBuilder()
xml = (
    builder
    .project_load("model.pack")
    .set_power("CPU", 15.0)
    .set_power("GPU", 10.0)
    .reset()
    .solve_all()
    .project_save_as("output.pack")
    .quit()
    .build()
)

# 保存脚本
with open("script.xml", "w") as f:
    f.write(xml)
```

---

## 注意事项

1. **需要 FloTHERM 已安装** - 脚本会自动检测安装路径
2. **FloTHERM 版本**: 支持 2020.2 和 2504
3. **执行方式**: FloSCRIPT 通过 FloTHERM GUI 运行

---

## 常见问题

### Q: FloTHERM 未找到？

```python
from floscript.executor import FlothermExecutor
executor = FlothermExecutor()
executor.flotherm_path = r"C:\Program Files\Siemens\...\flotherm.exe"
```

### Q: 如何调试？

```bash
# 预览生成的脚本
python batch_sim.py run config.json --dry-run

# 只生成不执行
python batch_sim.py generate config.json -o ./scripts
```

---

## 相关文档

- [BATCH_SIM_GUIDE.md](./BATCH_SIM_GUIDE.md) - 详细使用指南
- [FloSCRIPT Schema](../examples/FloSCRIPT/Schema/) - FloSCRIPT XML Schema
