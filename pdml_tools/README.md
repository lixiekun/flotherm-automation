# PDML Tools

这个目录集中存放项目里和 `PDML` 解析、逆向、转换直接相关的文件。

主要入口：
- `pdml_to_floxml_converter.py`：当前正式的 `PDML -> FloXML` 转换器
- `compare_geometry_hierarchy.py`：用 `ECXML/FloXML` 对照几何层级
- `pdml_construct_schema.py`：二进制结构扫描器
- `PDML_REVERSE_TOOLING.md`：当前逆向方法与验证流程记录

常用命令：

```powershell
python pdml_tools/pdml_to_floxml_converter.py all.pdml -o test_v2.xml
python pdml_tools/compare_geometry_hierarchy.py test_level.ecxml test_level_converted.xml
python pdml_tools/pdml_construct_schema.py Heatsink.pdml --mode geometry --limit 80
```
