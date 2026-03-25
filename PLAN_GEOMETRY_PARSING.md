# 几何层级解析完善计划

## 目标
完善 PDML 几何层级解析器，提取完整的嵌套装配体和立方体结构。

## 当前状态
- ✅ 基本字符串提取已实现
- ✅ 浮点数提取已实现
- ⚠️ 几何名称提取未成功（字符串格式问题）
- ⚠️ 嵌套结构解析未实现

## 问题分析
1. 字符串提取格式：`0x07 0x02` + offset(4B) + length(4B) + string_data
   - 实际测试发现 length 解析为 503316480（错误）
   - 原因：字节序问题，应使用大端序

2. 几何名称关键词：
   - coldplate, plate, block, cuboid, assembly, heatsink, fan, pcb

## 执行步骤

### Step 1: 修复字符串提取
- 修改 length 解析为大端序 `>I`
- 测试验证字符串提取

### Step 2: 集成到主转换器
- 更新 pdml_tools/pdml_to_floxml_converter.py 使用修复后的逻辑
- 提取几何名称并添加到 FloXML

### Step 3: 提取几何尺寸
- 在几何名称附近查找浮点数
- 过滤合理范围 (0.001 - 1.0)

### Step 4: 构建几何层级
- 创建根装配体
- 添加 cuboid 子节点

### Step 5: 测试验证
- 转换 3 个 PDML 文件
- 验证 FloXML 内容

### Step 6: 提交推送
- git add -A
- git commit
- git push

## 预期结果
- PDML 文件成功转换为 FloXML
- 几何名称正确提取
- FloTHERM 可打开生成的文件
