"""Database-free regression tests against the installed ERPNext rate validator.

Run from frontend: python3 -m unittest discover -s tests -p 'test_*.py'
"""
import ast
from pathlib import Path
from types import SimpleNamespace
import unittest

APP = Path(__file__).resolve().parents[2]
ERP = APP.parent / 'erpnext/erpnext/controllers/taxes_and_totals.py'


def flt(value, precision=None):
    value = float(value or 0)
    return round(value, precision) if precision is not None else value


def load_functions(path, names, namespace):
    tree = ast.parse(path.read_text())
    functions = [node for node in ast.walk(tree)
                 if isinstance(node, ast.FunctionDef) and node.name in names]
    assert {node.name for node in functions} == set(names)
    exec(compile(ast.Module(body=functions, type_ignores=[]), str(path), 'exec'), namespace)


@unittest.skipUnless(ERP.exists(), 'Requires the sibling ERPNext checkout')
class DiscountRoundTripTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ns = {'flt': flt, 'frappe': SimpleNamespace(utils=SimpleNamespace(flt=flt))}
        load_functions(APP / 'ssplbilling/api/sales.py', ['_preserve_percentage_rate'], cls.ns)
        load_functions(ERP, ['calculate_item_rate', 'get_rate_with_margin',
                             'remove_discount', 'remove_margin'], cls.ns)

    def row(self, base, gross, discount):
        return SimpleNamespace(
            price_list_rate=base, rate=round(gross * (1 - discount / 100), 2),
            discount_percentage=discount, discount_amount=0,
            margin_type=None, margin_rate_or_amount=0, pricing_rules=None,
            precision=lambda field: 2,
        )

    def validate(self, row):
        self.ns['calculate_item_rate'](SimpleNamespace(
            doc=SimpleNamespace(ignore_pricing_rule=1)), row)

    def test_original_modifier_bug(self):
        row = self.row(100, 90, 10)
        self.validate(row)
        self.assertEqual(row.rate, 81)
        self.assertEqual(row.discount_percentage, 0)

    def test_repeated_edits_preserve_percentage_and_gross_rate(self):
        # Flat/tiered/custom percentages all use the same saved percentage field.
        for base, gross, discount in [(100, 90, 10), (100, 120, 15),
                                      (100, 100, 10), (100, 73.57, 12.5),
                                      (100, 90, 100), (0, 90, 10)]:
            with self.subTest(base=base, gross=gross, discount=discount):
                expected = round(gross - round(gross * discount / 100, 2), 2)
                for _ in range(10):
                    row = self.row(base, gross, discount)
                    self.validate(row)  # Missing-value processing may already normalize the row.
                    self.ns['_preserve_percentage_rate'](row, {'gross_rate': gross, 'discount': discount})
                    self.validate(row)
                    self.validate(row)  # calculate + save validation
                    self.assertEqual(row.discount_percentage, discount)
                    self.assertEqual(row.rate, expected)
                    self.assertEqual(row.rate_with_margin, gross)
                    gross = row.rate_with_margin  # API load -> frontend save

    def test_free_rows_and_legacy_payloads_unchanged(self):
        for gross, discount, payload in [(0, 0, {'gross_rate': 0}), (90, 10, {})]:
            row = self.row(100, gross, discount)
            before = vars(row).copy()
            self.ns['_preserve_percentage_rate'](row, payload)
            self.assertEqual(vars(row), before)


if __name__ == '__main__':
    unittest.main()
