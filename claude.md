# 数据标准化项目：名字→编码 匹配规则说明

本文档描述 `name_to_code.py` 中所有匹配与编码规则逻辑，便于维护与扩展。

---

## 1. 项目结构

- **name_to_code.py**：硬编码转化入口（ERP 产品编码、员工 NIK、lookup 表）
- **01_规则文档/**：规则来源（Complete ERP Product Code List、Employee Identification Number generation rule 等）
- **02_待处理数据/**：如 item-list-slim.xlsx；输出带「新编码」列的文件
- **tests/test_name_to_code.py**：规则示例与适配性测试

---

## 2. 通用匹配约定

- **空白**：规整为单空格、去首尾空。
- **ERP 名称**：在 normalize 基础上统一引号（如 `1/2 "` → `1/2"`）。
- **大小写**：所有 ERP 表匹配与组分解析均**大小写不敏感**。
- **材质词边界**：材质（如 PE）用词边界匹配，避免误匹配 "pipe" 等子串。

---

## 3. ERP 产品编码规则（10 位）

**结构**：`1(Division) + 3(Middle) + 2(Sub) + 4(Serial)` = 10 位。

- **Division**：固定 `1`（PIPE SYSTEM）。
- **Middle**：`101` = Pipes，`102` = Pipe Fittings。
- **Sub**（管道）：Material(1) + Standard(1)。**Sub**（管件）：Fitting Type(2)。
- **Serial**（管道）：Color(1) + Pressure相对(1) + Size(2)。**Serial**（管件）：FittingStdCode(1) + max(MaterialCode, PressureCode)(1) + Size(2)。

### 3.1 匹配流程

1. **精确表匹配**：与 ERP_NAME_TO_CODE 中每条比较（大小写不敏感），相等则返回对应编码。
2. **组分解析**：未命中时根据名称判断 Pipe / Fitting，再按查表拼码；任一必要字段缺失则返回 None。

### 3.2 管道 / 管件判定

- **Pipe**：`"pipe" in norm_lower and "fitting" not in norm_lower`。
- **Fitting**：`"fitting" in norm_lower` 或 socket, elbow, tee, valve, union, flange, reducer, cross, clamp, cap, bridge 任一在 norm_lower 中。

### 3.3 查表

MATERIAL_CODE, STANDARD_CODE, COLOR_CODE, PRESSURE_CODE, MATERIAL_PRESSURE_CODE（管道压力相对码）, SIZE_METRIC_CODE, SIZE_IMPERIAL_CODE, FITTING_TYPE_CODE, FITTING_STANDARD_CODE。详见 name_to_code.py。

### 3.4 管道 Serial = Color(1) + Pressure相对(1) + Size(2)

### 3.5 管件 Serial = FittingStdCode(1) + max(Material, Pressure)(1) + Size(2)

---

## 4. 员工 NIK 规则（11 位）

**结构**：2(部门) + 2(年) + 2(月) + 1(岗位类型) + 2(职级) + 2(序号)。

NIK_DEPARTMENT, NIK_JOB, NIK_POSITION 查表；NIK_EXAMPLES 18 条描述行精确匹配。

---

## 5. 统一入口与扩展

transform(name, scheme="erp_product"|"nik_description"|"lookup", lookup_table=..., exact_only=...)；load_lookup_table；process_excel_add_code_column。

---

## 6. 历史修复要点

管件 Serial 公式；材质词边界；管道 MATERIAL_PRESSURE_CODE；10 位；NIK 18 条；TestERPCompose。

以上为当前全部匹配规则与逻辑；代码实现以 `name_to_code.py` 为准。
