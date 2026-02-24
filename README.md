# 数据标准化项目

名字→编码 规则转化工具：ERP 产品 10 位编码、员工 NIK 11 位编码。

- **name_to_code.py**：转化入口（精确表匹配 + 组分解析）
- **claude.md**：技术向匹配规则说明
- **匹配规则说明-客户确认.md**：供客户确认的完整匹配逻辑
- **run_process_item_list.py**：批量处理 Excel 生成新编码列
- **tests/**：规则示例与组分解析测试

规则来源：01_规则文档（Complete ERP Product Code List、Employee Identification Number generation rule）。
