# PDML 逆向工具与方法记录

## 目的

这份文档记录当前项目里真正用到的 PDML 逆向分析工具、工作方法和验证流程。

它不是泛泛而谈的“可选工具列表”，而是为了方便后续继续修改
[pdml_to_floxml_converter.py](D:\Program Files\Siemens\SimcenterFlotherm\2504\flotherm-automation\pdml_to_floxml_converter.py)
时，快速回忆我们现在是怎么把结论做出来的。

## 当前核心思路

当前项目采用的是“样例对驱动 + 二进制局部验证 + XML 严格对比”的逆向方式。

简单说就是：

1. 先拿一对确定互相可还原的样例：
   - [all.pdml](D:\Program Files\Siemens\SimcenterFlotherm\2504\flotherm-automation\all.pdml)
     对应
     [All-Objects-Attributes-Settings-FullModel.xml](D:\Program Files\Siemens\SimcenterFlotherm\2504\flotherm-automation\All-Objects-Attributes-Settings-FullModel.xml)
   - [Heatsink.pdml](D:\Program Files\Siemens\SimcenterFlotherm\2504\flotherm-automation\Heatsink.pdml)
     对应
     [Heatsink-Windtunnel-FullModel.xml](D:\Program Files\Siemens\SimcenterFlotherm\2504\flotherm-automation\Heatsink-Windtunnel-FullModel.xml)
2. 在 PDML 里定位字符串、double、几何记录、section 位置。
3. 用转换器生成 XML。
4. 对生成结果和原始 FloXML 做递归逐节点 diff。
5. 把“已证实”的结构沉淀进转换器；把“还不通用”的部分明确标记为 sample-calibrated profile。

## 当前实际用到的文件

### 1. 主转换器

文件：
[pdml_to_floxml_converter.py](D:\Program Files\Siemens\SimcenterFlotherm\2504\flotherm-automation\pdml_to_floxml_converter.py)

作用：
- 当前唯一的正式转换入口
- 同时承载了二进制读取、样例 profile 判定、几何体构建、FloXML 生成

目前已支持的样例 profile：
- `all_objects_fullmodel`
- `heatsink_windtunnel`

### 2. construct 扫描器

文件：
[pdml_construct_schema.py](D:\Program Files\Siemens\SimcenterFlotherm\2504\flotherm-automation\pdml_construct_schema.py)

作用：
- 用于快速扫描真实 `*.pdml`
- 验证字符串块、double 块、geometry 记录、section marker
- 适合在还没决定怎么写进主转换器之前做“局部探测”

适合场景：
- 新样例进来时先扫一遍
- 怀疑某个 offset 规则在新样例里变了
- 想快速列出 geometry 记录和 type_code

### 3. Kaitai 格式草稿

文件：
[pdml.ksy](D:\Program Files\Siemens\SimcenterFlotherm\2504\flotherm-automation\pdml.ksy)

作用：
- 记录已经比较确定的结构
- 更偏“格式说明”和“后续固化”

当前定位：
- 不是主力运行工具
- 是格式知识沉淀文件

### 4. 辅助分析脚本

仓库里还有一批一次性或半一次性的分析脚本，例如：
- [analyze_geometry_types.py](D:\Program Files\Siemens\SimcenterFlotherm\2504\flotherm-automation\analyze_geometry_types.py)
- [analyze_pdml_format.py](D:\Program Files\Siemens\SimcenterFlotherm\2504\flotherm-automation\analyze_pdml_format.py)
- [pdml_floxml_compare.py](D:\Program Files\Siemens\SimcenterFlotherm\2504\flotherm-automation\pdml_floxml_compare.py)

这些脚本的定位是：
- 用来验证单个猜想
- 用来辅助定位差异
- 不一定是长期保留的正式接口

## 当前确认过的二进制模式

### 1. tagged string

当前项目里最稳定的入口之一是字符串块：

```text
07 02 [type_code:2 bytes] [reserved:2 bytes] [length:4 bytes, big-endian] [utf-8 bytes]
```

在主转换器里，这部分对应：
- `_extract_strings`
- `tagged_strings`

用途：
- 提取工程名
- 提取 section marker
- 提取 geometry name record
- 用 `type_code` 辅助判断几何类型

### 2. tagged double

数值块当前按下面规则识别：

```text
06 [8 bytes big-endian IEEE754 double]
```

在主转换器里，这部分对应：
- `_extract_double_at`
- `_find_double_near`
- `_read_relative_doubles`
- `_pick_values`

用途：
- 提取 position
- 提取 size
- 在 section 附近寻找可疑参数值

### 3. geometry record

当前几何识别的主要方式是：

1. 扫描 tagged string
2. 看 `type_code`
3. 过滤内部名称
4. 把 name + type_code 视作 geometry entry

在主转换器里对应：
- `GEOMETRY_TYPE_CODES`
- `_find_geometry_records`

注意：
- `type_code -> 节点类型` 不是对所有 PDML 都保证完全通用
- 当前映射是基于现有样例校准出来的

## 当前真正使用的逆向方法

## 方法 1：样例对比驱动

这是最核心的方法。

我们不是凭空猜 PDML 格式，而是始终拿“已知 FloXML -> 导入工程 -> 导出 PDML”这类样例对做对照。

优点：
- 可以明确知道目标输出应该长什么样
- 可以避免“结构看起来合理，但和 FloTHERM 实际导出不一致”的假阳性

当前已验证的样例对：
- `all.pdml <-> All-Objects-Attributes-Settings-FullModel.xml`
- `Heatsink.pdml <-> Heatsink-Windtunnel-FullModel.xml`

## 方法 2：从 XML 反推最小必要结构

FloXML 不是只拿来做最终对比，也拿来决定“我们到底要还原哪些节点、哪些字段顺序、哪些标签名”。

典型用途：
- 判断 `solution_domain` 用的是 `ambient` 还是 `boundary`
- 判断 `source_options` 里标签是 `value` 还是 `velocity`
- 判断 `fan_curve_point` 里标签是 `volume_flow` 还是 `volume_flow_rate`
- 判断 `surface_exchange` 是 `profile/speed/thermal_resistance` 还是别的结构

## 方法 3：局部偏移探测

当某类对象已经能定位到 name record 时，我们会在它附近按相对偏移窗口找 double。

当前常见模式：
- `position`：在 name record 后面一段相对稳定的区域内提 3 个 double
- `size`：在另一段区域内提 2 或 3 个 double

这套方法在简单几何体上很有效，例如：
- `cuboid`
- `source`
- `fixed_flow`
- `monitor_point`

## 方法 4：命名和顺序启发式挂接几何层级

PDML 本身不一定直接给出一棵现成的几何树，所以当前主转换器会结合：
- geometry 记录出现顺序
- 节点命名模式
- 样例特征

去还原层级。

例如：
- `all_objects_fullmodel` 里有一套自己的 assembly 挂接规则
- `heatsink_windtunnel` 里则单独用顺序型挂接：
  - `Heat Sink Geometry`
  - `Base`
  - `Fin 1`
  - `Low A - 1 / Low B - 1 / Upper - 1 / Vertical A - 1 / Vertical B - 1`
  - ...

这部分在主转换器里对应：
- `_attach_assembly_children`
- `_attach_heatsink_children`

## 方法 5：profile 分流

这是目前最重要的工程化经验。

不是所有 PDML 样例都共享一套结构模板。

目前已经确认，至少这两类样例在这些方面明显不同：
- `model`
- `solve`
- `grid`
- `attributes`
- `solution_domain`
- `geometry hierarchy`

所以当前做法不是强行做“一套模板兼容全部”，而是：

1. 先检测 profile
2. 再走该 profile 对应的输出结构

当前 profile 检测入口在主转换器里：
- `PDMLBinaryReader._detect_profile`

当前 profile：
- `all_objects_fullmodel`
- `heatsink_windtunnel`

这不是最终通用解，但比“把 A 样例的结构硬套到 B 样例上”稳定得多。

## 方法 6：严格 XML diff 验证

每次重要修改后，都要把生成 XML 和原始 XML 做递归逐节点比对。

这里不是只比：
- geometry count
- section count

而是继续往下比：
- tag 名
- tag 顺序
- 文本值
- 子节点数量

这样能抓到很多“表面正确、细节不一致”的问题。

这是当前项目最关键的质量门槛。

## 当前推荐工作流

如果后面再加新样例，建议按下面顺序做：

1. 先准备一对样例：
   - 原始 FloXML
   - 导入后导出的 PDML
2. 跑现有转换器，先看差异落在哪些 section。
3. 用 `pdml_construct_schema.py` 和现有分析脚本定位：
   - 新的 section marker
   - 新的 geometry type
   - 数值偏移是否不同
4. 判断这次差异是：
   - 现有 profile 小修即可
   - 还是应该新增一个 profile
5. 修改主转换器。
6. 对原样例做递归 XML diff。
7. 再回归已有样例，确保旧样例没坏。

## 当前常用命令

### 1. 运行转换

```powershell
python pdml_to_floxml_converter.py all.pdml -o test_v2.xml
python pdml_to_floxml_converter.py Heatsink.pdml -o heatsink_test.xml
```

### 2. 语法检查

```powershell
python -m py_compile pdml_to_floxml_converter.py
```

### 3. 运行 construct 扫描器

```powershell
python pdml_construct_schema.py all.pdml
python pdml_construct_schema.py Heatsink.pdml --mode geometry --limit 80
```

### 4. 递归 XML 对比

当前没有单独固定成一个正式 CLI，
但项目里已经多次使用“递归比较 XML 树”的临时 Python 脚本做验证。

建议后续如果继续演进，可以把这部分正式沉淀成一个固定脚本，例如：
- `compare_xml_exact.py`

## 当前已知限制

### 1. 仍有 sample-calibrated 逻辑

虽然现在已经做了 profile 化，但很多规则仍然是：
- 基于现有样例校准
- 不是对任意 PDML 都已证明通用

特别是：
- 某些 geometry 特殊字段
- 某些 attribute 模板
- 某些 solution domain 边界命名

### 2. parser 还不是完整格式规范

现在的主转换器更像：
- 可工作的样例驱动解析器

还不是：
- 全量正式 PDML 规范实现

### 3. geometry type_code 映射仍需继续验证

个别类型在不同样例里可能还需要结合上下文判断，不能只靠 `type_code` 一锤定音。

## 后续建议

### 短期

- 把 XML 递归比对脚本固定成正式工具
- 给 profile 检测加更明确的注释和日志
- 把 `sample-calibrated` helper 继续集中，避免散落

### 中期

- 再引入 1 到 2 个风格差异明显的 PDML/XML 样例
- 看是否真的需要更多 profile，还是可以抽出更通用的 section parser

### 长期

- 把“样例模板输出”逐步替换为“真实 PDML 字段提取”
- 让 `pdml.ksy` 和主转换器共享更多已证实的格式知识

## 一句话总结

当前项目不是靠重型逆向框架硬啃出来的，
而是靠“样例对 + 字符串/数值块识别 + 局部偏移探测 + 几何顺序/命名挂接 + 严格 XML 对比”
这一套工程化方法稳步推进出来的。

这也是后面继续修改时最应该保持的工作方式。
