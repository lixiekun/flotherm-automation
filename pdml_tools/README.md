# PDML Tools

这个目录集中存放项目里和 `PDML` 解析、逆向、转换直接相关的文件。

主要入口：
- `pdml_to_floxml_converter.py`：当前正式的 `PDML -> FloXML` 转换器
- `compare_geometry_hierarchy.py`：用 `ECXML/FloXML` 对照几何层级
- `pdml_record_dump.py`：导出结构化 PDML 记录 JSON 和人类可读摘要
- `pdml_hierarchy_candidates.py`：对指定 assembly 打印多种候选层级树
- `pdml_structure_signal_probe.py`：并排比较多个 assembly 周围的原始字节和整数信号
- `pdml_construct_schema.py`：二进制结构扫描器
- `PDML_REVERSE_TOOLING.md`：当前逆向方法与验证流程记录

常用命令：

```powershell
python pdml_tools/pdml_to_floxml_converter.py all.pdml -o test_v2.xml
python pdml_tools/compare_geometry_hierarchy.py test_level.ecxml test_level_converted.xml
python pdml_tools/pdml_record_dump.py test_level.pdml --summary-only
python pdml_tools/pdml_hierarchy_candidates.py your_model.pdml
python pdml_tools/pdml_structure_signal_probe.py your_model.pdml --all-records
python pdml_tools/pdml_construct_schema.py Heatsink.pdml --mode geometry --limit 80
```

默认直接列出所有装配体，并打印每种候选规则下的父节点摘要：

```powershell
python pdml_tools/pdml_hierarchy_candidates.py your_model.pdml
```

针对单个 assembly 对比候选层级树：

```powershell
python pdml_tools/pdml_hierarchy_candidates.py your_model.pdml "Baltimoreudp" --depth 6 --context 12
```

如果你不想输名字，可以先看上面输出里的 `gidx`，再用编号直接查看：

```powershell
python pdml_tools/pdml_hierarchy_candidates.py your_model.pdml --assembly-index 12 --depth 6 --context 12
```

如果层级候选树都不靠谱，直接退回原始信号对比：

```powershell
python pdml_tools/pdml_structure_signal_probe.py your_model.pdml --all-records
```

如果连这个都太长，改用压缩摘要：

```powershell
python pdml_tools/pdml_structure_signal_probe.py your_model.pdml --all-records --summary-only
```

如果目标 assembly 不在 `geometry` section，而是在 `grid` 等其它 section 被扫出来，补上：

```powershell
python pdml_tools/pdml_hierarchy_candidates.py your_model.pdml "1206" --all-records --depth 6 --context 12
```

`pdml_record_dump.py` 常用查看方式：

1. 先导出结构化 dump

```powershell
python pdml_tools/pdml_record_dump.py your_model.pdml -o tmp.dump.json -s tmp.dump.md
```

2. 只看真正的 `geometry` 记录

```powershell
$j = Get-Content .\tmp.dump.json -Raw | ConvertFrom-Json
$j.geometry_records |
  Where-Object { $_.section_guess -eq 'geometry' } |
  Select-Object index,node_type_guess,name,level,offset_hex |
  Format-Table -AutoSize
```

3. 只看某个 assembly 前后相邻记录

```powershell
$j = Get-Content .\tmp.dump.json -Raw | ConvertFrom-Json
$records = @($j.geometry_records | Where-Object { $_.section_guess -eq 'geometry' })
$hit = $records | Where-Object { $_.name -like '*Baltimoreudp*' } | Select-Object -First 1
$idx = [array]::IndexOf($records, $hit)
$from = [Math]::Max(0, $idx - 8)
$to = [Math]::Min($records.Count - 1, $idx + 12)
$records[$from..$to] |
  Select-Object index,node_type_guess,name,level,offset_hex |
  Format-Table -AutoSize
```

4. 直接看每条记录的原始层级探针

```powershell
$j = Get-Content .\tmp.dump.json -Raw | ConvertFrom-Json
$j.geometry_records |
  Where-Object { $_.section_guess -eq 'geometry' } |
  Select-Object index,name,node_type_guess,
    @{n='off6';e={$_.raw_level_probe.offset_minus_6_level_guess}},
    @{n='off4be';e={$_.raw_level_probe.offset_minus_4_be_level_guess}},
    @{n='off4le';e={$_.raw_level_probe.offset_minus_4_le_level_guess}},
    @{n='prefix';e={$_.raw_level_probe.prefix_hex}} |
  Format-Table -AutoSize
```
