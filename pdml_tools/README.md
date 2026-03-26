# PDML Tools

这个目录集中存放项目里和 `PDML` 解析、逆向、转换直接相关的文件。

主要入口：
- `pdml_to_floxml_converter.py`：当前正式的 `PDML -> FloXML` 转换器
- `compare_geometry_hierarchy.py`：用 `ECXML/FloXML` 对照几何层级
- `pdml_record_dump.py`：导出结构化 PDML 记录 JSON 和人类可读摘要
- `pdml_construct_schema.py`：二进制结构扫描器
- `PDML_REVERSE_TOOLING.md`：当前逆向方法与验证流程记录

常用命令：

```powershell
python pdml_tools/pdml_to_floxml_converter.py all.pdml -o test_v2.xml
python pdml_tools/compare_geometry_hierarchy.py test_level.ecxml test_level_converted.xml
python pdml_tools/pdml_record_dump.py test_level.pdml --summary-only
python pdml_tools/pdml_construct_schema.py Heatsink.pdml --mode geometry --limit 80
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
