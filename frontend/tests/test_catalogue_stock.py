"""Database-free checks for public catalogue stock scope and draft adjustments."""
import ast
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch
import unittest

APP = Path(__file__).resolve().parents[2]

class CatalogueStockTest(unittest.TestCase):
    def setUp(self):
        source = APP / 'ssplbilling/api/offer_api.py'
        tree = ast.parse(source.read_text())
        functions = [n for n in tree.body if isinstance(n, ast.FunctionDef)
                     and n.name in ('_catalogue_stock', 'get_offer_stock')]
        for function in functions:
            function.decorator_list = []
        self.settings = {'online_order_warehouse': 'Online', 'online_order_company': 'Company'}
        self.warehouse = SimpleNamespace(company='Company', is_group=0, disabled=0)
        self.frappe = SimpleNamespace(
            get_single=Mock(return_value=self.settings),
            get_cached_doc=Mock(return_value=self.warehouse),
            get_all=Mock(return_value=[SimpleNamespace(item_code='A', actual_qty=10)]),
            db=SimpleNamespace(get_value=Mock(return_value='Catalogue')),
            get_doc=Mock(),
        )
        self.sales = Mock(return_value={('A', 'Online'): 3, ('B', 'Online'): 4, ('A', 'Other'): 99})
        self.purchases = Mock(return_value={('A', 'Online'): 2, ('C', 'Online'): 5})
        self.namespace = {'frappe': self.frappe}
        exec(compile(ast.Module(body=functions, type_ignores=[]), str(source), 'exec'), self.namespace)
        self.module = SimpleNamespace(get_draft_invoice_qtys_batch=self.sales, get_draft_purchase_qtys_batch=self.purchases)

    def calculate(self, codes):
        with patch.dict('sys.modules', {'ssplbilling.api.stock_utils': self.module}):
            return self.namespace['_catalogue_stock'](codes)

    def test_db_minus_draft_sales_plus_draft_purchases(self):
        self.assertEqual(self.calculate(['A', 'B', 'C']), {'A': 9, 'B': -4, 'C': 5})
        self.sales.assert_called_once_with('Online')
        self.purchases.assert_called_once_with('Online')
        self.assertEqual(self.frappe.get_all.call_args.kwargs['filters'],
                         {'item_code': ['in', ['A', 'B', 'C']], 'warehouse': 'Online'})

    def test_returns_and_fractional_quantities(self):
        self.sales.return_value = {('A', 'Online'): -1.5}
        self.purchases.return_value = {('A', 'Online'): -0.25}
        self.assertEqual(self.calculate(['A']), {'A': 11.25})

    def test_unconfigured_or_invalid_warehouse_is_unavailable(self):
        self.settings['online_order_warehouse'] = None
        self.assertEqual(self.calculate(['A']), {})
        self.settings['online_order_warehouse'] = 'Online'
        self.warehouse.company = 'Other Company'
        self.assertEqual(self.calculate(['A']), {})
        self.frappe.get_all.assert_not_called()

    def test_public_refresh_only_reads_enabled_catalogue_items(self):
        class Row(dict):
            @property
            def itemcode(self): return self['itemcode']
        self.frappe.get_doc.return_value = SimpleNamespace(items=[Row(itemcode='A'), Row(itemcode='B', disabled=1)])
        with patch.dict('sys.modules', {'ssplbilling.api.stock_utils': self.module}):
            self.assertEqual(self.namespace['get_offer_stock']('offers'), {'A': 9})
        self.frappe.db.get_value.assert_called_once_with('Offer-Items', {'pageaddress': 'offers'}, 'name')

    def test_unknown_catalogue_does_not_expose_stock(self):
        self.frappe.db.get_value.return_value = None
        self.assertEqual(self.namespace['get_offer_stock']('missing'), {})
        self.frappe.get_all.assert_not_called()

if __name__ == '__main__':
    unittest.main()
