# FloTHERM 批量仿真工具

使用 FloSCRIPT 宏自动化操作 FloTHERM，实现参数修改和批量求解。

## 快速开始

```bash
# 生成 FloSCRIPT 脚本
python batch_sim.py generate config.json -o ./scripts

# 生成并执行（完整自动化）
python batch_sim.py run config.json

# 提取结果
python batch_sim.py extract solved.pack -o results.json

# 创建 FloXML 项目
python batch_sim.py create-floxml -o project.xml
```

---

## 配置文件格式

### 1. 基本配置

```json
{
    "input_pack": "model.pack",
    "output_pack": "output_{value}.pack",
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

### 3. Excel 配置

```json
{
    "config_source": "excel",
    "excel_file": "config.xlsx",
    "sheet": "Sheet1",
    "input_pack": "model.pack"
}
```

---

## 支持的修改类型

| 类型 | 属性 | 说明 |
|------|------|------|
| `power` | component, value | 修改组件功耗 (W) |
| `solver` | max_iterations | 求解器最大迭代次数 |
| `size` | x, y, z | 修改几何尺寸 |
| `position` | x, y, z | 修改位置 |
| `material` | component, material | 修改材料 |

---

## 命令详解

### generate - 生成脚本

```bash
python batch_sim.py generate config.json -o ./scripts

# 预览不生成
python batch_sim.py generate config.json --dry-run
```

输出：
- `./scripts/case_001.xml`
- `./scripts/case_002.xml`
- ...

### run - 生成并执行

```bash
python batch_sim.py run config.json

# 指定超时时间
python batch_sim.py run config.json --timeout 7200

# 预览不执行
python batch_sim.py run config.json --dry-run
```

执行流程：
1. 解析配置文件
2. 生成 FloSCRIPT 脚本
3. 自动检测 FloTHERM 安装路径
4. 逐个执行脚本
5. 输出执行结果

### extract - 提取结果

```bash
# JSON 格式
python batch_sim.py extract solved.pack -o results.json

# CSV 格式
python batch_sim.py extract solved.pack -o results.csv --format csv
```

### create-floxml - 创建 FloXML

```bash
python batch_sim.py create-floxml -n MyProject -o project.xml
```

---

## 工作流程

```
┌─────────────────────────────────────────────────────────────┐
│                     完整自动化流程                           │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  1. 准备配置文件 config.json                                │
│     ↓                                                       │
│  2. python batch_sim.py run config.json                     │
│     ├── 加载 Pack 文件                                      │
│     ├── 修改参数（功耗、温度等）                             │
│     ├── 求解                                                │
│     └── 保存结果 Pack                                       │
│     ↓                                                       │
│  3. python batch_sim.py extract output.pack -o results.json │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## FloSCRIPT 构建器 API

直接使用 Python 构建 FloSCRIPT：

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

### 支持的方法

| 方法 | 说明 |
|------|------|
| `project_load(path)` | 加载 Pack 文件 |
| `project_save()` | 保存项目 |
| `project_save_as(path)` | 另存为 |
| `project_delete()` | 关闭项目 |
| `set_power(name, value)` | 设置功耗 |
| `set_size(name, x, y, z)` | 设置尺寸 |
| `reset()` | 重置/重新初始化 |
| `solve_all()` | 求解所有场景 |
| `quit()` | 退出 FloTHERM |
| `comment(text)` | 添加注释 |
| `custom(xml)` | 添加自定义 XML |

---

## 执行器

```python
from floscript.executor import FlothermExecutor

executor = FlothermExecutor()

# 自动检测 FloTHERM 路径
executor.auto_detect_path()

# 执行脚本
success, elapsed, message = executor.execute(
    script_path="script.xml",
    timeout=3600
)

if success:
    print(f"完成，耗时 {elapsed:.1f} 秒")
else:
    print(f"失败: {message}")
```

---

## 目录结构

```
batch_simulation/
├── batch_sim.py           # 主入口
├── floscript/             # FloSCRIPT 模块
│   ├── __init__.py
│   ├── builder.py         # 脚本构建器
│   ├── batch_generator.py # 批量生成器
│   └── executor.py        # 执行器
├── config/                # 配置模块
│   ├── __init__.py
│   └── excel_config_reader.py
├── floxml/                # FloXML 模块
│   ├── __init__.py
│   └── creator.py
├── example_config.json    # 配置示例
├── example_param_sweep.json
└── tests/                 # 测试
    └── unit/
```

---

## 注意事项

1. **FloTHERM 版本**: 支持 2020.2 和 2504
2. **执行方式**: FloSCRIPT 需要 FloTHERM GUI 运行
3. **路径格式**: Windows 路径会自动转换为正斜杠
4. **超时设置**: 默认 3600 秒，可通过 `--timeout` 调整

---

## 常见问题

### Q: FloTHERM 未找到？

```bash
[ERROR] FloTHERM not found. Please install or set path.
```

解决：确保 FloTHERM 已安装，或手动设置路径：

```python
executor = FlothermExecutor()
executor.flotherm_path = r"C:\Program Files\Siemens\Simcenter Flotherm\2504\Bin\flotherm.exe"
```

### Q: 脚本执行失败？

检查生成的 FloSCRIPT XML 是否符合 Schema：
- `examples/FloSCRIPT/Schema/FloSCRIPTSchema.xsd`

### Q: 如何调试？

```bash
# 使用 --dry-run 预览
python batch_sim.py run config.json --dry-run

# 查看生成的脚本
python batch_sim.py generate config.json -o ./scripts
cat ./scripts/case_001.xml
```
