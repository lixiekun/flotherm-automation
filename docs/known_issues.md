# Known Issues

## PDML 二进制转换 solution type 硬编码为 flow_heat

**状态**: 未修复

**问题**: `pdml_tools/pdml_to_floxml_converter.py` 的 `_apply_sample_model_defaults()` 硬编码 `model.solution = "flow_heat"`，导致所有二进制 PDML 转换后 solution type 都是 `flow_heat`，无法正确保留 `conduction_only` 或 `flow_only`。

**影响范围**:
- `pdml_to_floxml_converter.py` — PDML → FloXML 转换
- `pdml_extract_model_solve.py` — 从二进制 PDML 提取 model/solve 设置
- `pdml_extract_solve_settings.py` — 从二进制 PDML 提取求解设置到 JSON

**临时方案**:
- 用 FloTHERM 将 PDML 导出为 FloXML XML，再从 XML 提取（XML 路径正确）
- 或手动修改转换后的 FloXML 中 `<solution>` 值

**根因分析**:
- PDML 二进制格式的 modeling section（type_code `0x00C0`）payload 为 3 个 4 字节整数：`[1, 1, 2]`
- 推测编码：`[flow_mode, radiation, dimensionality]`，其中 `1=flow_heat, 0=conduction_only`
- 但项目中所有示例 PDML 都是 `flow_heat`，无法对比确认编码映射
- XSD 合法值：`flow_heat`、`flow_only`、`conduction_only`（见 `XmlEntities.xsd` 第 185-191 行）

**修复方案**:
- 获取 `conduction_only` 模式的 PDML 文件，对比 `0x00C0` section payload 差异
- 确认编码映射后修改 `_extract_model_settings()` 从二进制读取 solution type
- 同理可能需要验证 radiation、dimensionality、transient 的编码

---

## PDML 二进制转换 model 设置（已修复的部分）

**状态**: 已修复

**修复内容**: 新增 `_parse_section_subfields()` 结构化解析方法，替代启发式 double 搜索。

**已修复字段**:

| 字段 | 修复前 | 修复后 |
|------|--------|--------|
| `datum_pressure` | 硬编码/启发式搜索 | 从 `global` section (0x0060) field 1 结构化提取 |
| `ambient_temperature` | 硬编码/启发式搜索 | 从 `global` section field 3 提取，**正确做 °C → K 转换** |
| `radiant_temperature` | 硬编码/与 ambient 共用 | 从 `global` section field 2 独立提取，**正确做 °C → K 转换** |
| `gravity_value` | 搜索 11.5-12.5 范围 double（无法区分 9.81） | 从 `gravity` section (0x0070) field 5 精确提取 |
| `gravity_direction` | 按布局硬编码 neg_z/neg_y | 从 `gravity` section field 2 ref value 枚举映射 |

**仍为默认值的字段**（需要 conduction PDML 样本才能修复）:

| 字段 | 默认值 |
|------|--------|
| `solution` | flow_heat |
| `radiation` | off |
| `transient` | False |
| `turbulence_type` | turbulent |
| `turbulence_model` | auto_algebraic |
| `dimensionality` | 3d |
