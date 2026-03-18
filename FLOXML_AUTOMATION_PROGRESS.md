# FloXML 自动化生成方案总结

## 目标

实现 **FloXML 自动化生成**，用于批量创建 FloTHERM 热仿真模型。

---

## 背景

### FloXML 是什么？

FloXML 是 FloTHERM/Simcenter Flotherm 的一种 **XML 格式**，用于：
- 批量创建模型（几何、材料、热源等）
- 参数化仿真
- 从外部程序生成仿真案例

### FloXML 生成方式

| 方式 | 说明 |
|------|------|
| **官方 Excel 模板** | 在 Excel 中填写数据，运行 VBA 宏生成 FloXML |
| **手动编写 XML** | 直接按照 Schema 编写 XML |
| **程序生成** | 用 Python 等程序生成 XML |

### FloXML 导出问题

经过测试，**FloTHERM 不支持直接导出 FloXML**：
- `project_export export_type="FloXML"` 命令不生成文件
- FloXML 是“导入专用”格式，设计用于从外部创建模型

---

## 当前实现的方案

### 方案1：Excel + VBA（官方方式）

**流程**：
```text
Python 写 Excel 数据
→ Excel VBA 宏生成 FloXML
```

**文件**：
- `excel_floxml_generator.py` - 已验证的 Excel 转 FloXML 主脚本
- `auto_generate_floxml.ps1` - PowerShell 自动化尝试
- `auto_generate_floxml.vbs` - VBScript 自动化尝试
- `auto_floxml_generator.py` - 早期完整自动化脚本

**状态**：✅ 已验证可自动生成 FloXML

**2026-03-19 实测结论**：
- `Materials.xlsm` 可以通过 Python + Excel COM 自动生成 FloXML
- 不需要再手动添加 `Auto_Open`
- 模板真实按钮宏名不是 `CREATEMATERIALS`
- `Materials.xlsm` 中按钮绑定的实际宏为 `create_all_materials`
- Python 脚本已改成自动检测按钮绑定宏并执行

**已验证命令**：
```powershell
python "D:\Program Files\Siemens\SimcenterFlotherm\2504\flotherm-automation\excel_floxml_generator.py" materials --data "D:\Program Files\Siemens\SimcenterFlotherm\2504\flotherm-automation\test_materials.json" -o "D:\Program Files\Siemens\SimcenterFlotherm\2504\flotherm-automation\floxml_output\materials_auto_generated.xml" --timeout 30
```

**已验证输出**：
- `floxml_output/materials_auto_generated.xml`

---

### 方案2：纯 Python 生成

**流程**：
```text
Python 直接生成 FloXML（模仿 VBA 逻辑）
```

**文件**：
- `floxml_builder.py` - 完整 FloXML 构建器
- `python_floxml_generator.py` - 材料生成器
- `demo_model.json` - 示例模型数据

**状态**：⚠️ 生成的 FloXML 格式仍有问题，导入失败

**已修复的问题**：
- ✅ `solution_domain` 不能放在 geometry 里
- ✅ 正交材料元素名：`x_conductivity` 而不是 `conductivity_x`
- ❓ 还有其他格式问题待排查

---

## 当前结论

### 结论1：推荐方案已经明确

当前推荐方案不是“纯 Python 拼 XML”，而是：

```text
Python 写 Excel 数据
→ Python 解析 .xlsm 按钮绑定的真实宏名
→ Python 拉起独立 Excel COM 实例
→ Excel VBA 生成官方格式 FloXML
→ Python 等待 XML 落盘并清理 Excel 进程
```

原因：
- FloXML 最终格式由 Siemens 官方模板 VBA 负责
- Python 不需要猜 Schema 细节
- Python 只负责“填表 + 找宏 + 执行 + 等结果”
- 这条链路已经在当前机器上实测成功

### 结论2：Excel 自动化不是完全不可行

旧判断里认为“命令行环境下 Excel 自动化基本不可用”，这个结论现在要修正。

**当前结论**：
- Excel 仍然需要 GUI 环境
- 但在当前机器上，`Excel.Application` COM 是可用的
- 真正的问题不是“完全不能自动化”，而是：
  - 之前宏名猜错了
  - Excel/COM 在退出阶段可能卡住
  - 需要把 Excel 放到独立 helper 子进程里执行并清理进程

### 结论3：模板宏名已经确认

**已确认**：
- `XML_Subs_FloCOREv11.bas` 中存在公共宏 `CREATEMODEL`
- `Materials.xlsm` 的按钮绑定宏不是 `CREATEMATERIALS`
- 通过解析 `.xlsm` 内部 `xl/drawings/*.xml`，确认按钮绑定为：
  - `[0]!create_all_materials`
- Python 中归一化后实际执行的宏名：
  - `create_all_materials`

**结论**：
- 不应再靠猜测宏名
- 应直接从 `.xlsm` 包内的 drawing XML 读取按钮的 `macro="..."` 属性

---

## `excel_floxml_generator.py` 当前逻辑

### 总体流程

```text
读取 JSON 材料数据
→ 复制官方 Materials.xlsm 模板
→ 把输出 XML 路径写入 B1
→ 从第 4 行开始写材料数据
→ 把 .xlsm 当 zip 包读取，解析 xl/drawings/*.xml
→ 找到按钮绑定宏 create_all_materials
→ 启动 helper 子进程
→ helper 中创建独立 Excel.Application
→ 打开工作簿并执行 'workbook'!create_all_materials
→ 主进程轮询等待 XML 文件生成
→ 成功后结束 helper 并清理 Excel 进程
```

### Python 在这条链路中的职责

Python 不是负责手写 FloXML，而是负责自动化“填表”和“点按钮”。

也就是：

```text
Python 填 Excel
→ Python 找出按钮绑定哪个宏
→ Python 让 Excel 自己执行这个宏
→ Excel 输出 FloXML
```

### 关键设计

#### 1. 为什么不再用 `Auto_Open`

- `Auto_Open` 方案依赖手动改模板
- 宏名之前还猜错了
- 维护成本高，不适合作为主方案

#### 2. 为什么要解析 `.xlsm` 内部 XML

- `.xlsm` 本质上是 zip 包
- 按钮宏绑定信息在 `xl/drawings/*.xml`
- 这样能直接拿到真实宏名，而不是猜 `CREATEMATERIALS`

#### 3. 为什么要用 helper 子进程

- 实测 Excel 宏执行后 XML 会成功生成
- 但 Excel/COM 在关闭阶段可能卡住
- 把 Excel 放进子进程后，主进程可以：
  - 轮询输出文件
  - 超时后终止 helper
  - 强制清理残留 Excel 进程

---

## 当前卡住的地方

### 问题1：更多模板尚未完成适配

`Materials.xlsm` 已经跑通，但其他模板还没有逐个验证：
- `Advanced-Resistance.xlsm`
- `Data_Center_SI_Units.xlsm`
- `Data_Center_US_Units.xlsm`
- `Heatpipe-LShaped.xlsm`
- `IGBT-Creator.xlsm`

这些模板还需要分别确认：
- 数据写入区在哪
- 按钮绑定宏是什么
- 生成的是 Project FloXML 还是 Assembly FloXML

### 问题2：纯 Python 生成的 FloXML 格式问题

**现象**：
```text
ERROR E/11059 - Import Error Geometry file detected
WARN Schema validation error
```

**可能原因**：
1. Assembly FloXML vs Project FloXML 格式差异
2. 某些元素缺失或顺序不对
3. 与官方模板输出仍存在结构差异

---

## 下一步计划

### 短期

1. **把 Materials 模板流程固定为正式方案**
   - 保留 `excel_floxml_generator.py` 作为主入口
   - 不再依赖 `Auto_Open`
   - 默认走“自动检测宏 + Excel COM 执行”

2. **补充导入验证**
   - 用 FloTHERM 实际导入 `materials_auto_generated.xml`
   - 确认材料属性与 Excel 输入一致

3. **整理输入格式**
   - 统一 `test_materials.json` 的字段规范
   - 为批量材料生成准备更稳定的数据模板

### 中期

1. **扩展到更多官方模板**
   - `Advanced-Resistance.xlsm`
   - `Data_Center_SI_Units.xlsm`
   - `Heatpipe-LShaped.xlsm`
   - 分别确认每个模板的数据区和按钮宏

2. **校验 Python 生成的 FloXML**
   - 用 Excel 生成的 FloXML 作为参考
   - 对比格式差异
   - 逐步修复 Python 生成器

### 长期

1. **整合到 flotherm-automation 项目**
2. **添加更多 FloXML 元素支持**
3. **提供 CLI 和 API**

---

## 文件清单

```text
flotherm-automation/
├── excel_floxml_generator.py         # 已验证的 Excel->FloXML 自动化主脚本
├── auto_floxml_generator.py          # 早期完整自动化脚本
├── auto_generate_floxml.ps1          # PowerShell 自动化尝试
├── auto_generate_floxml.vbs          # VBScript 自动化尝试
├── run_excel_macro.ps1               # PowerShell 宏运行器
├── run_excel_macro.vbs               # VBScript 宏运行器
│
├── floxml_builder.py                 # 方案2: 纯 Python 生成
├── python_floxml_generator.py        # 方案2: 材料生成
├── demo_model.json                   # 示例模型数据
│
├── test_materials.json               # 测试数据
├── generate_floxml.bat               # 批处理启动器
│
└── floxml_output/                    # 输出目录
    ├── floxml_generator.xlsm         # Excel 模板副本
    ├── materials_auto.xlsm           # 自动化运行生成的工作簿
    ├── materials_auto_generated.xml  # 已验证成功的自动生成输出
    ├── demo_assembly.xml             # Python 生成的 FloXML
    └── python_materials.xml          # Python 生成的材料 FloXML
```

---

## 参考资料

### 官方文件
- `examples/FloXML/Spreadsheets/*.xlsm` - Excel 模板
- `examples/FloXML/Spreadsheets/XML_Subs_FloCOREv11.bas` - VBA 源码
- `examples/FloXML/FloXML Files/` - FloXML 示例

### Schema 文件
- `examples/DCIM Development Toolkit/Schema Files/FloXML/` - FloXML Schema
- `examples/FloSCRIPT/Schema/` - FloSCRIPT Schema

---

## 更新日志

### 2026-03-18
- 创建项目结构
- 实现方案1（Excel + VBA）
- 实现方案2（纯 Python）
- 发现 FloTHERM 不支持导出 FloXML
- 发现命令行环境下 Excel 自动化受限
- 添加 Auto_Open 宏到模板
- 待确认：模板中正确的宏名称

### 2026-03-19
- 验证 `Materials.xlsm` 可通过 Python + Excel COM 自动生成 FloXML
- 确认模板按钮实际宏名为 `create_all_materials`
- 确认不需要再依赖手动 `Auto_Open`
- 重写 `excel_floxml_generator.py`
- 新脚本已支持：
  - 自动复制模板
  - 自动写入材料表
  - 自动检测按钮绑定宏
  - 通过 helper 子进程执行 Excel 宏
  - 等待 XML 生成并清理 Excel 进程
- 成功生成：
  - `floxml_output/materials_auto_generated.xml`
