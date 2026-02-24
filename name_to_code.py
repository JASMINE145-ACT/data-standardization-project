# -*- coding: utf-8 -*-
"""
名字→编码 硬编码转化工具（基于规则文档）
- 支持 ERP 产品编码、员工 NIK 等规则
- 用规则文档中的转化例子作为能力边界，适配性强：可扩展映射表、多语言/别名、外部表查找
"""
from __future__ import annotations

import re
from typing import Any, Optional

# ---------- ERP 产品编码规则（来自 Complete ERP Product Code List）----------
# 10 位：1(Division) + 3(Middle) + 2(Sub: Material+Standard 或 管件类型) + 4(Serial: Color+Pressure+Size 或 管件专用)

MATERIAL_CODE = {"PVC-U": "1", "PVC-C": "2", "PE": "3", "PPR": "4"}
STANDARD_CODE = {"GB": "1", "SNI": "2", "JIS": "3", "ASTM": "4", "EN": "5"}
COLOR_CODE = {"White": "0", "Grey": "1", "Blue": "2", "Green": "3", "Black": "4", "Cream": "5", "Other": "9"}
PRESSURE_CODE = {"PN10": "1", "PN16": "2", "PN20": "3", "PN25": "4", "PN32": "5"}
# 管道 Serial 中各材质的相对压力码（从该材质最低常用规格起计 1）
MATERIAL_PRESSURE_CODE: dict[str, dict[str, str]] = {
    "PVC-U": {"PN10": "1", "PN16": "2"},
    "PVC-C": {"PN16": "1", "PN20": "2"},
    "PE":    {"PN10": "1", "PN16": "2", "PN20": "3"},
    "PPR":   {"PN20": "1", "PN25": "2", "PN32": "3"},
}
SIZE_METRIC_CODE = {"20mm": "01", "25mm": "02", "32mm": "03", "40mm": "04", "50mm": "05", "63mm": "06"}
SIZE_IMPERIAL_CODE = {'1/2"': "51", '3/4"': "52", '1"': "53", "1-1/4\"": "54", "1-1/2\"": "55", '2"': "56"}
FITTING_TYPE_CODE = {
    "Socket (Direct)": "01", "Socket": "01",
    "Elbow 90°": "02", "90° Elbow": "02",
    "Elbow 45°": "03", "45° Elbow": "03",
    "Tee": "04", "Cross": "05", "Reducer Socket": "06", "Reducer Tee": "07",
    "Valve": "08", "Union": "09", "Flange": "10",
    "Clamp (Pipe Clip)": "11", "Pipe Clamp": "11", "Pipe Clip": "11",
    "End Cap (Pipe Cap)": "12", "End Cap": "12", "Pipe Cap": "12",
    "Bridge Bend": "13",
}
FITTING_STANDARD_CODE = {"GB": "0", "SNI": "1", "JIS": "3", "ASTM": "4", "EN": "5"}

ERP_NAME_TO_CODE: list[tuple[str, str]] = [
    ("PVC-U Pipe 20mm White PN10 GB (Metric)", "1101110101"),
    ("PVC-U Pipe 20mm Grey PN10 GB (Metric)", "1101111101"),
    ("PVC-U Pipe 20mm White PN10 SNI (Metric)", "1101120101"),
    ("PVC-U Pipe 20mm White PN10 JIS (Metric)", "1101130101"),
    ("PVC-U Pipe 1/2\" White PN10 ASTM (Imperial)", "1101140151"),
    ("PVC-U Pipe 25mm White PN10 EN (Metric)", "1101150102"),
    ("PVC-U Pipe 32mm White PN16 GB (Metric)", "1101110203"),
    ("PVC-C Pipe 20mm White PN16 GB (Metric)", "1101210101"),
    ("PVC-C Pipe 20mm White PN16 SNI (Metric)", "1101220101"),
    ("PVC-C Pipe 1/2\" White PN16 ASTM (Imperial)", "1101240151"),
    ("PVC-C Pipe 25mm Grey PN20 EN (Metric)", "1101250202"),
    ("PE Pipe 20mm Black PN10 GB (Metric)", "1101314101"),
    ("PE Pipe 20mm Black PN10 SNI (Metric)", "1101324101"),
    ("PE Pipe 3/4\" Black PN16 ASTM (Imperial)", "1101344252"),
    ("PE Pipe 32mm Black PN20 EN (Metric)", "1101354303"),
    ("PPR Pipe 20mm White PN20 GB (Metric)", "1101410101"),
    ("PPR Pipe 20mm Blue PN20 GB (Metric)", "1101412101"),
    ("PPR Pipe 20mm White PN20 SNI (Metric)", "1101420101"),
    ("PPR Pipe 1/2\" White PN25 ASTM (Imperial)", "1101440251"),
    ("PPR Pipe 25mm White PN32 EN (Metric)", "1101450302"),
    ("Socket PVC-U 20mm PN10 GB (Metric)", "1102010101"),
    ("Elbow 90° PVC-U 20mm PN10 SNI (Metric)", "1102021101"),
    ("Tee PVC-U 1/2\" PN10 JIS (Imperial)", "1102043151"),
    ("Valve PVC-U 25mm PN16 ASTM (Metric)", "1102084202"),
    ("Socket PVC-C 20mm PN16 GB (Metric)", "1102010201"),
    ("Elbow 90° PVC-C 20mm PN16 SNI (Metric)", "1102021201"),
    ("Socket PE 20mm PN10 GB (Metric)", "1102010301"),
    ("Tee PE 25mm PN10 SNI (Metric)", "1102041302"),
]

NIK_DEPARTMENT = {
    "Board of Directors": "01",
    "Finance, Accounting, & Tax Department": "02", "Finance, Accounting, & Tax Dept": "02",
    "Procurement Department": "03", "Customer Service Department": "04",
    "Marketing Department": "05", "Warehouse Department": "06",
    "General Service Department": "07", "Human Resources Department": "08",
}
NIK_JOB = {"Full Time": "0", "Part Time": "1", "Internship": "2"}
NIK_POSITION = {
    "Director": "01", "Commissioner": "02", "Manager": "03",
    "Supervisor": "04", "Officer / Staff": "05", "Officer": "05", "Staff": "05",
    "Intern": "06",
}
NIK_EXAMPLES: list[tuple[str, str]] = [
    ("01250300101", "Board of Directors / Yang Quanshe / Director / 25/03/2025"),
    ("01240900202", "Board of Directors / Yang Yaobin / Commissioner / 01/09/2024"),
    ("02241000401", "Finance, Accounting, & Tax Dept / Huda Asriati / Accounting and Tax Supervisor / 01/10/2024"),
    ("02260100501", "Finance, Accounting, & Tax Dept / Andri Hidayat / Finance Staff / 26/01/2026"),
    ("03210100401", "Procurement Department / Putri Rubi Dwi Fadlilah / Procurement Supervisor / 20/01/2021"),
    ("03211200502", "Procurement Department / Irfan Syahputra / Procurement Staff / 06/12/2021"),
    ("04250700401", "Customer Service Department / Ma Jinjin (Frida) / Quotation Supervisor / 21/07/2025"),
    ("04221100402", "Customer Service Department / Annisa Putri Aulia / Sales Supervisor / 01/11/2022"),
    ("04250700503", "Customer Service Department / Yane Fahira Rustian / Sales Staff / 21/07/2025"),
    ("04260100601", "Customer Service Department / Qiu Peisong / Intern / 05/01/2026"),
    ("04260100602", "Customer Service Department / Chai Jing / Intern / 05/01/2026"),
    ("05250300501", "Marketing Department / Yang Yaobin / Marketing Staff / 25/03/2025"),
    ("05240900302", "Marketing Department / Yang Quanshe / Marketing Manager / 01/09/2024"),
    ("06220300401", "Warehouse Department / Yoyo Rianto / Warehouse Supervisor / 26/03/2022"),
    ("06250700502", "Warehouse Department / Ahmad Faizih / Warehouse Staff / 08/07/2025"),
    ("07251200503", "General Service Department / Taryati / Housekeeper / 01/12/2025"),
    ("07221200503", "General Service Department / Hendra / Driver / 01/12/2022"),
    ("08260100501", "Human Resources Department / Andri Hidayat / HR Staff / 26/01/2026"),
]


def _normalize(s: str) -> str:
    if not s or not isinstance(s, str):
        return ""
    return " ".join(s.split()).strip()


def _normalize_for_erp(s: str) -> str:
    s = _normalize(s)
    s = re.sub(r'\s*"\s*', '"', s)
    return s


def erp_name_to_code(name: str, *, exact_only: bool = False) -> Optional[str]:
    norm = _normalize_for_erp(name)
    norm_lower = norm.lower()
    for doc_name, code in ERP_NAME_TO_CODE:
        if _normalize_for_erp(doc_name).lower() == norm_lower:
            return code
    if exact_only:
        return None
    return _erp_parse_and_compose(norm, norm_lower)


def _erp_parse_and_compose(norm: str, norm_lower: Optional[str] = None) -> Optional[str]:
    if norm_lower is None:
        norm_lower = norm.lower()
    div = "1"
    mid = None
    material = standard = color = size_code = None
    material_name = pressure_name = None
    is_pipe = "pipe" in norm_lower and "fitting" not in norm_lower
    fitting_keywords = ["socket", "elbow", "tee", "valve", "union", "flange", "reducer", "cross", "clamp", "cap", "bridge"]
    is_fitting = "fitting" in norm_lower or any(f in norm_lower for f in fitting_keywords)
    if is_pipe:
        mid = "101"
    elif is_fitting:
        mid = "102"
    if not mid:
        return None
    for mat, c in MATERIAL_CODE.items():
        if re.search(r'\b' + re.escape(mat.lower()) + r'\b', norm_lower):
            material = c
            material_name = mat
            break
    for std, c in STANDARD_CODE.items():
        if std.lower() in norm_lower:
            standard = c
            break
    for col, c in COLOR_CODE.items():
        if col.lower() in norm_lower:
            color = c
            break
    for pr in PRESSURE_CODE:
        if pr.lower() in norm_lower:
            pressure_name = pr
            break
    for sz, c in SIZE_METRIC_CODE.items():
        if sz.lower() in norm_lower:
            size_code = c
            break
    if size_code is None:
        for sz, c in SIZE_IMPERIAL_CODE.items():
            if sz.lower() in norm_lower:
                size_code = c
                break
    if not material:
        return None
    if color is None:
        color = "0"
    if size_code is None:
        size_code = "01"
    if is_fitting:
        fitting = None
        for ft, fc in FITTING_TYPE_CODE.items():
            if ft.lower() in norm_lower:
                fitting = fc
                break
        if fitting is None:
            fitting = "01"
        fitting_std = "0"
        for std, c in FITTING_STANDARD_CODE.items():
            if std.lower() in norm_lower:
                fitting_std = c
                break
        press_code = PRESSURE_CODE.get(pressure_name, "1") if pressure_name else "1"
        grade = max(material, press_code)
        sub = fitting
        serial = fitting_std + grade + size_code
    else:
        if not standard:
            return None
        mat_press_map = MATERIAL_PRESSURE_CODE.get(material_name or "", {})
        pressure = mat_press_map.get(pressure_name, "1") if pressure_name else "1"
        sub = material + standard
        serial = color + pressure + size_code
    return div + mid + sub + serial


def nik_attributes_to_code(department: str, year_joined: str | int, month_joined: str | int, job: str, position: str, serial: str | int) -> Optional[str]:
    dept = NIK_DEPARTMENT.get(_normalize(department)) or NIK_DEPARTMENT.get(department)
    j = NIK_JOB.get(_normalize(job)) or NIK_JOB.get(job)
    pos = NIK_POSITION.get(_normalize(position)) or NIK_POSITION.get(position)
    if not dept or j is None or not pos:
        return None
    yy = str(year_joined).strip()[-2:]
    mm = str(month_joined).strip().zfill(2)[:2]
    ss = str(serial).strip().zfill(2)[-2:]
    return f"{dept}{yy}{mm}{j}{pos}{ss}"


def nik_example_description_to_code(description: str) -> Optional[str]:
    for code, desc in NIK_EXAMPLES:
        if _normalize(desc) == _normalize(description):
            return code
    return None


def transform(name: str, scheme: str = "erp_product", *, lookup_table: Optional[list[tuple[str, str]]] = None, exact_only: bool = False) -> Optional[str]:
    name = _normalize(name)
    if not name:
        return None
    if scheme == "erp_product":
        if lookup_table:
            name_norm_lower = _normalize_for_erp(name).lower()
            for n, c in lookup_table:
                if _normalize_for_erp(n).lower() == name_norm_lower:
                    return c
        return erp_name_to_code(name, exact_only=exact_only)
    if scheme == "nik_description":
        return nik_example_description_to_code(name)
    if scheme == "lookup" and lookup_table:
        for n, c in lookup_table:
            if _normalize(n) == name:
                return c
        for n, c in lookup_table:
            if name in _normalize(n) or _normalize(n) in name:
                return c
    return None


def get_erp_examples() -> list[tuple[str, str]]:
    return list(ERP_NAME_TO_CODE)


def get_nik_examples() -> list[tuple[str, str]]:
    return list(NIK_EXAMPLES)


def load_lookup_table(path: str, *, name_columns: Optional[list[str]] = None, code_column: str = "Item Code", sheet_name: Any = 0) -> list[tuple[str, str]]:
    try:
        import pandas as pd
    except ImportError:
        return []
    try:
        df = pd.read_excel(path, sheet_name=sheet_name)
    except Exception:
        return []
    if code_column not in df.columns:
        return []
    cols = name_columns or [df.columns[0]]
    out: list[tuple[str, str]] = []
    for _, row in df.iterrows():
        code = row.get(code_column)
        if pd.isna(code):
            continue
        code = str(code).strip()
        parts = [str(row.get(c, "")).strip() for c in cols if c in df.columns and not pd.isna(row.get(c))]
        name = " ".join(p for p in parts if p)
        if name:
            out.append((name, code))
    return out


def process_excel_add_code_column(input_path: str, output_path: Optional[str] = None, *, name_columns: Optional[list[str]] = None, code_column: str = "Item Code", new_column: str = "新编码", scheme: str = "erp_product", fallback_to_original: bool = True, only_encoded_rows: bool = False, sheet_name: Any = 0) -> str:
    try:
        import pandas as pd
    except ImportError:
        raise ImportError("需要 pandas 和 openpyxl 处理 Excel")
    if output_path is None:
        import os
        base, ext = os.path.splitext(input_path)
        output_path = f"{base}_with_std_code{ext}"
    df = pd.read_excel(input_path, sheet_name=sheet_name)
    cols = name_columns or [c for c in ["Item Name", "Chinese name", "Item Code"] if c in df.columns]
    if not cols:
        cols = [df.columns[0]]
    if code_column not in df.columns:
        code_column = df.columns[0]
    lookup_table = load_lookup_table(input_path, name_columns=name_columns, code_column=code_column, sheet_name=sheet_name) if scheme == "lookup" else None
    codes = []
    for _, row in df.iterrows():
        name = None
        for c in cols:
            v = row.get(c)
            if pd.notna(v) and str(v).strip():
                name = str(v).strip()
                break
        if not name:
            codes.append("" if not fallback_to_original else str(row.get(code_column, "")))
            continue
        code = transform(name, scheme=scheme, lookup_table=lookup_table)
        if code is None and fallback_to_original:
            code = str(row.get(code_column, ""))
        codes.append(code if code is not None else "")
    df[new_column] = codes
    if only_encoded_rows:
        mask = df[new_column].astype(str).str.strip() != ""
        df = df.loc[mask].copy()
    try:
        sheet_name_to_use = pd.ExcelFile(input_path).sheet_names[0] if sheet_name == 0 else str(sheet_name)
    except Exception:
        sheet_name_to_use = "Item"
    df.to_excel(output_path, index=False, sheet_name=sheet_name_to_use)
    return output_path


if __name__ == "__main__":
    import os
    _dir = os.path.dirname(os.path.abspath(__file__))
    _input = os.path.join(_dir, "02_待处理数据", "item-list-slim.xlsx")
    _out = os.path.join(_dir, "02_待处理数据", "item-list-slim_with_std_code.xlsx")
    if not os.path.isfile(_input):
        print("未找到:", _input)
        raise SystemExit(1)
    out_path = process_excel_add_code_column(_input, output_path=_out, name_columns=["Item Name", "Chinese name"], code_column="Item Code", new_column="新编码", scheme="erp_product", fallback_to_original=False, only_encoded_rows=True)
    print("已写出:", out_path)
