# 示例文件说明

本目录包含用于测试 `excel_batch_simulation.py` 的示例文件。

## 文件列表

| 文件 | 说明 |
|-----|------|
| `example_template.ecxml` | 示例 ECXML 模板文件 |
| `example_config.xlsx` | 示例 Excel 配置文件 |

## 使用方法

### 1. 简单配置测试

```bash
# 使用"简单配置" Sheet
python excel_batch_simulation.py examples/example_template.ecxml examples/example_config.xlsx -o ./output --no-solve

# 使用"温度扫描" Sheet
python excel_batch_simulation.py examples/example_template.ecxml examples/example_config.xlsx -o ./output --sheet "温度扫描" --no-solve
```

### 2. 高级配置测试（路径格式）

```bash
python excel_batch_simulation.py examples/example_template.ecxml examples/example_config.xlsx -o ./output --sheet "高级配置" --no-solve
```

### 3. 实际求解（需要 FloTHERM）

```bash
python excel_batch_simulation.py examples/example_template.ecxml examples/example_config.xlsx -o ./output
```

## Excel 配置说明

### Sheet 1: 简单配置

| config_name | CPU | GPU | Ambient |
|-------------|-----|-----|---------|
| idle        | 5   | 2   | 25      |
| normal      | 15  | 10  | 25      |

- 列名对应 ECXML 中的器件名
- 自动识别：CPU/GPU → 功耗(W)，Ambient → 温度(°C)

### Sheet 2: 高级配置

| config_name | CPU | Heatsink.Material.density | CPU.Size@width |
|-------------|-----|---------------------------|----------------|
| aluminum    | 15  | 2700                      | 0.02           |

- `Heatsink.Material.density` → 多层路径，设置材料密度
- `CPU.Size@width` → 属性路径，设置尺寸属性

### Sheet 3: 温度扫描

用于测试不同环境温度对热性能的影响。

## 预期输出

运行后会在 `output/batch_YYYYMMDD_HHMMSS/` 目录生成：

```
output/batch_20260309_100000/
├── idle.ecxml          # 修改后的 ECXML
├── normal.ecxml
├── heavy.ecxml
├── ...
├── batch_report.txt    # 批量处理报告
└── summary.xlsx        # 汇总表格
```
