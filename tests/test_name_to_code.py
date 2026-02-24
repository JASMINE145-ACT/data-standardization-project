# -*- coding: utf-8 -*-
"""用规则文档中的转化例子评估 name_to_code 转化工具能力。"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from name_to_code import (
    transform,
    get_erp_examples,
    get_nik_examples,
    erp_name_to_code,
    load_lookup_table,
    NIK_EXAMPLES,
    _erp_parse_and_compose,
)


class TestERPProductCode:
    @pytest.mark.parametrize("name,expected_code", get_erp_examples())
    def test_erp_name_to_code_exact(self, name, expected_code):
        got = erp_name_to_code(name, exact_only=False)
        assert got == expected_code, f"name={name!r} -> got {got!r}, expected {expected_code!r}"

    def test_erp_exact_only_matches_table(self):
        name, code = get_erp_examples()[0]
        assert erp_name_to_code(name, exact_only=True) == code
        assert erp_name_to_code("Unknown Product XYZ", exact_only=True) is None

    def test_erp_via_transform(self):
        for name, expected in get_erp_examples()[:5]:
            assert transform(name, "erp_product") == expected


class TestNIK:
    @pytest.mark.parametrize("expected_code,description", get_nik_examples())
    def test_nik_description_to_code(self, expected_code, description):
        got = transform(description, "nik_description")
        assert got == expected_code, f"desc={description!r} -> got {got!r}, expected {expected_code!r}"


class TestERPCompose:
    @pytest.mark.parametrize("name,expected", [
        ("PVC-U Pipe 20mm White PN10 GB (Metric)", "1101110101"),
        ("PE Pipe 20mm Black PN10 GB (Metric)", "1101314101"),
        ("PPR Pipe 20mm Blue PN20 GB (Metric)", "1101412101"),
        ("PVC-U Pipe 1/2\" White PN10 ASTM (Imperial)", "1101140151"),
        ("Socket PVC-U 20mm PN10 GB (Metric)", "1102010101"),
        ("Elbow 90° PVC-U 20mm PN10 SNI (Metric)", "1102021101"),
        ("Tee PVC-U 1/2\" PN10 JIS (Imperial)", "1102043151"),
        ("Valve PVC-U 25mm PN16 ASTM (Metric)", "1102084202"),
        ("Socket PVC-C 20mm PN16 GB (Metric)", "1102010201"),
        ("Elbow 90° PVC-C 20mm PN16 SNI (Metric)", "1102021201"),
        ("Socket PE 20mm PN10 GB (Metric)", "1102010301"),
        ("Tee PE 25mm PN10 SNI (Metric)", "1102041302"),
    ])
    def test_compose_path(self, name, expected):
        got = _erp_parse_and_compose(name)
        assert got == expected, f"compose({name!r}) -> {got!r}, expected {expected!r}"


class TestAdaptability:
    def test_erp_whitespace_normalized(self):
        name, code = get_erp_examples()[0]
        spaced = name.replace(" ", "  ")
        assert transform(spaced, "erp_product") == code

    def test_erp_case_insensitive(self):
        name, code = get_erp_examples()[0]
        assert erp_name_to_code(name.lower()) == code
        assert erp_name_to_code(name.upper()) == code
        mixed = "PVC-u Pipe 20mm WHITE pn10 GB (Metric)"
        assert erp_name_to_code(mixed) == code

    def test_lookup_table_override(self):
        custom = [("My Custom Product", "CUSTOM001")]
        assert transform("My Custom Product", "lookup", lookup_table=custom) == "CUSTOM001"
        assert transform("My Custom Product", "erp_product", lookup_table=custom) == "CUSTOM001"

    def test_unknown_erp_returns_none(self):
        assert transform("Random Thing 123", "erp_product") is None or isinstance(transform("Random Thing 123", "erp_product"), str)

    def test_load_lookup_table_empty_path(self):
        table = load_lookup_table(__file__ + ".nonexistent.xlsx")
        assert table == []
