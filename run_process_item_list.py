# -*- coding: utf-8 -*-
"""处理 02_待处理数据/item-list-slim.xlsx，生成带「新编码」列的 Excel。"""
import os
import sys

_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _DIR)

from name_to_code import process_excel_add_code_column

INPUT = os.path.join(_DIR, "02_待处理数据", "item-list-slim.xlsx")
OUTPUT = os.path.join(_DIR, "02_待处理数据", "item-list-slim_with_std_code.xlsx")

if __name__ == "__main__":
    if not os.path.isfile(INPUT):
        print("未找到:", INPUT)
        sys.exit(1)
    out_path = process_excel_add_code_column(
        INPUT,
        output_path=OUTPUT,
        name_columns=["Item Name", "Chinese name"],
        code_column="Item Code",
        new_column="新编码",
        scheme="erp_product",
        fallback_to_original=False,
        only_encoded_rows=True,
    )
    print("已写出:", out_path)
