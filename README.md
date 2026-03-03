# FloTHERM 自动化工具

用于批量修改 ECXML/Pack 参数、自动求解和生成仿真案例的 Python 脚本。

**兼容 FloTHERM 2020.2**

---

## ⚠️ 实际测试结论

### 核心发现

经过实际测试，**FloTHERM 2020.2 的自动化能力非常有限**：

| 方式 | 可行性 | 说明 |
|-----|--------|------|
| 命令行无头模式 | ❌ 不行 | 只支持 `.prj` 和 `.floxml`，Pack/PDML/ECXML 都会打开 GUI |
| COM API | ❌ 不可用 | 2020.2 版本不支持 |
| Python API | ❌ 不可用 | 2020.2 版本不支持 |
| FloSCRIPT 宏 | ⚠️ 部分可用 | **需要打开 GUI，然后手动点击运行** |

### 唯一可行方案：FloSCRIPT 宏 + 手动执行

**实际工作流程**：
1. 打开 FloTHERM GUI
2. 加载录制的 FloSCRIPT 宏
3. **手动点击运行按钮**
4. 宏自动执行：打开文件 → 求解 → 保存

**限制**：
- 必须打开 GUI
- 必须手动点击运行（无法通过命令行自动触发）
- 每次只能处理一个文件

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

| 文件 | 功能 | 状态 |
|-----|------|------|
| `pack_editor.py` | Pack 文件编辑器（解压、查看、修改功耗） | ✅ 可用 |
| `ecxml_editor.py` | ECXML 文件解析和参数修改 | ✅ 可用 |
| `batch_simulation.py` | 批量仿真案例生成器 | ✅ 可用（生成文件） |
| `batch_pack_solver.py` | 批量生成 FloSCRIPT 宏 | ⚠️ 需配合手动执行 |
| `flotherm_batch_solver.py` | 命令行批处理求解器 | ❌ 实际不可用 |
| `simple_solver.py` | 简易求解脚本 | ❌ 实际不可用 |

---

## 可用功能

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

## 官方文档位置

FloSCRIPT 相关文档在 FloTHERM 安装目录中：

```
# 示例脚本
C:\Program Files\Siemens\SimcenterFlotherm\2020.2\examples\FloSCRIPT\

# Schema 文档
C:\Program Files\Siemens\SimcenterFlotherm\2020.2\docs\Schema-Documentation\FloSCRIPT\
```

---

## 学习资源

| 资源 | 说明 | 链接 |
|-----|------|------|
| **热设计网** | 国内 Flotherm 教程和经验分享 | [resheji.com](https://www.resheji.com) |
| **Siemens 社区** | 官方技术文章 | [community.sw.siemens.com](https://community.sw.siemens.com) |

**QQ 交流群**：热设计网 319322744

---

## 总结

**FloTHERM 2020.2 自动化现状**：

- ❌ 无法真正无头运行 Pack/PDML/ECXML 文件
- ❌ COM/Python API 不可用
- ⚠️ FloSCRIPT 宏可用，但需要手动点击运行
- ✅ 可以用 Python 脚本修改参数、生成案例文件

**推荐工作流**：
1. 用 Python 脚本批量修改参数、生成多个案例文件
2. 在 FloTHERM GUI 中逐个打开并手动运行宏求解
3. 或者升级到更新版本的 Simcenter Flotherm（可能支持更好的自动化）
