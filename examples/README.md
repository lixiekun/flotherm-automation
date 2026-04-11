# Examples 目录说明

## 整体结构

```
examples/
├── DCIM Development Toolkit/     ← 数据中心基础设施管理（DCIM）开发工具包
├── Demonstration Models/         ← 演示模型（PCB、FCBGA、Superposition 等）
├── FloSCRIPT/                    ← FloSCRIPT 宏脚本 Schema
├── FloXML/                       ← FloXML 示例文件和 Excel 模板
│   ├── FloXML Files/
│   │   ├── Assembly FloXML Examples/   # 子装配级 FloXML（Block、Resistance 等）
│   │   └── Project FloXML Examples/    # 完整项目级 FloXML
│   └── Spreadsheets/                   # .xlsm 宏工作簿模板
├── MCAD Files/                   ← MCAD 几何文件（.igs, .sat）
├── Schema/                       ← XSD Schema 定义
│   └── PlugIns/                  # ECXML、CTMXML、EROM、PTD 插件 Schema
├── Training Material/            ← 培训材料（.floeda, .csv, .stp）
└── settings_example.json         # 配置示例
```

## DCIM Development Toolkit

### VBA 模块（`.cls` / `.bas`）

`.cls` 文件是 **VBA 类模块**（Visual Basic for Applications Class Module），属于 Excel VBA 宏代码。它们是 Siemens 官方提供的示例，用于在 Excel 中通过宏自动化生成 FloTHERM/FloVENT 的 FloXML 模型文件。

| 文件 | 类型 | 用途 |
|------|------|------|
| `DC_Class.cls` | 类模块 | 数据中心操作 — 调用 `flotherm.bat -p` 启动项目，创建穿孔地板（perforated_plate）等几何对象 |
| `FloXMLServer.cls` | 类模块 | FloXML 服务 — 生成热属性（thermal_att）、材料属性等 XML 节点，提供文件路径工具函数 |
| `FloSCRIPT_Rack.cls` | 类模块 | 机架操作 — 通过 FloSCRIPT XML 控制机架装配层级，移动几何节点到根装配 |
| `Class_XML_Subs_FCv11.cls` | 类模块 | **核心 FloXML 生成类** — 用 VBA 逐行写入完整 FloXML 项目文件（模型设置、求解器、网格、几何） |
| `XML_Subs_FloCOREv11.bas` | 标准模块 | FloCORE XML 子过程 — 辅助生成 FloXML 节点 |

### Excel 宏工作簿（`.xlsm`）

| 文件 | 用途 |
|------|------|
| `DataCenter_Builder.xlsm` | 数据中心建模 |
| `DataCenter_Power_Update.xlsm` | 数据中心功耗更新 |
| `FloXML_DataCenter.xlsm` | 数据中心 FloXML 生成 |
| `Rack_Builder.xlsm` | 机架建模 |
| `Server_Builder.xlsm` | 服务器建模 |

### Schema 文件

- **FloSCRIPT Schema**（`.xsd`）：定义 FloSCRIPT 宏命令的 XML 结构（CC、Core、EDA、ParaMCAD 等模块）
- **FloXML Schema**（`.xsd`）：定义 FloXML 的 XML 结构（Attributes、Definitions、Entities、Geometry）

## Demonstration Models

| 目录 | 内容 |
|------|------|
| Detailed Model Calibration | IGBT 模型标定（`.xlsm` + `.flocalibration`） |
| Detailed PCB and Power Map | 详细 PCB 和功率映射（`.floeda`, `.sat`, `.csv`） |
| Detailed PCB in Set Top Box | 机顶盒中的详细 PCB（`.floeda`, `.stp`） |
| Detailed_FCBGA | 详细 FCBGA 封装建模（`.xlsm` + 基板图像） |
| ODB++ | ODB++ 格式 PCB 导入（`.tgz`, `.csv`, `.IGS`） |
| Superposition | 叠加法示例 |
| T3Ster CTM Coldplate Characterisation | T3Ster 瞬态测试和冷板特性标定 |

## FloXML 示例

### Assembly FloXML（子装配级，仅含 `<attributes>` + `<geometry>`）

- `2R-Model.xml` — 双热阻模型
- `Advanced-Resistance.xml` — 高级热阻
- `Block.xml` — 简单方块
- `Nested-Assemblies.xml` — 嵌套装配

### Project FloXML（完整项目级，含 `<model>`, `<solve>`, `<grid>` 等）

- `All-Objects-Attributes-Settings-FullModel.xml` — 全对象全属性示例
- `Default.xml` — 默认项目
- `Heatsink-Windtunnel-FullModel.xml` — 散热器风洞
- `PDML-Referencing-FullModel.xml` — 引用 PDML 的项目

## Schema 插件

| 目录 | Schema | 说明 |
|------|--------|------|
| CTMXML_PLUGIN_SCHEMA | `xCTMToFloThermSchema.xsd` | 紧凑热模型（CTM）转换 |
| ECXML_PLUGIN_SCHEMA | `ECXML.xsd` | JEDEC ECXML 设备热模型 |
| EROM_SCHEMA | `Common.xsd`, `EromSpecification.xsd` | EROM 规范 |
| PTD_PLUGIN_SCHEMA | `JEP30-*.xsd` | JEDEC JEP30 零件模型（热、电、封装等） |

## 与本项目的关系

本项目 `flotherm-automation` 中的 Python 工具本质上是将这些 VBA 宏的功能用 Python 重新实现：

- `excel_floxml_generator.py` — 替代 VBA `.cls` 模块生成 FloXML
- `floxml_tools/ecxml_to_floxml_converter.py` — ECXML 转 FloXML
- `excel_batch_simulation.py` — Excel 批量仿真
- `ecxml_editor.py` — ECXML 编辑
