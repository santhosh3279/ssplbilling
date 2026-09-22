"""Search endpoint checks without a database."""
import ast
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch
import unittest

class Row(dict):
    __getattr__ = dict.get
    __setattr__ = dict.__setitem__

class CatalogueSearchTest(unittest.TestCase):
    def setUp(self):
        source = Path(__file__).resolve().parents[2] / 'ssplbilling/api/catalogue_order_api.py'
        function = next(n for n in ast.parse(source.read_text()).body if isinstance(n, ast.FunctionDef) and n.name == 'search_catalogue_items')
        function.decorator_list = []
        self.rows = [Row(item_code=str(i), barcode='123', stock_uom='Nos') for i in range(31)]
        self.frappe = SimpleNamespace(session=SimpleNamespace(user='Guest'),
            db=SimpleNamespace(sql=Mock(return_value=self.rows)), get_cached_value=Mock(return_value='Website User'))
        self.price = Mock(return_value=(None, 'Nos', 42))
        self.context = Mock(return_value={'price_list': 'Customer Prices'})
        self.stock = Mock(return_value={'0': 7})
        namespace = {'frappe': self.frappe, '_order_price': self.price, '_customer_context': self.context}
        exec(compile(ast.Module(body=[function], type_ignores=[]), str(source), 'exec'), namespace)
        self.search = namespace['search_catalogue_items']
        self.modules = {'frappe.utils': SimpleNamespace(cint=lambda n: int(n or 0)),
                        'ssplbilling.api.offer_api': SimpleNamespace(_catalogue_stock=self.stock)}

    def run_search(self, query, start=0):
        with patch.dict('sys.modules', self.modules):
            return self.search(query, start)

    def test_guest_search_is_limited_and_has_no_customer_prices(self):
        result = self.run_search('soap', 30)
        self.assertEqual(len(result['items']), 30)
        self.assertTrue(result['has_more'])
        self.assertEqual(result['items'][0].available_stock, 7)
        self.assertIsNone(result['items'][0].order_rate)
        self.context.assert_not_called()
        self.price.assert_not_called()
        sql, params = self.frappe.db.sql.call_args.args
        self.assertEqual(params, {'query': '%soap%', 'start': 30})
        for condition in ('line.disabled', 'item.disabled = 0', 'item.is_sales_item = 1', 'tabItem Barcode', 'LIMIT 31'):
            self.assertIn(condition, sql)

    def test_website_user_gets_customer_price(self):
        self.frappe.session.user = 'customer@example.com'
        result = self.run_search('123')
        self.assertEqual(result['items'][0].order_rate, 42)
        self.price.assert_any_call('0', 'Customer Prices', '123')
        self.context.assert_called_once()

    def test_blank_query_skips_database(self):
        self.assertEqual(self.run_search('   '), {'items': [], 'has_more': False})
        self.frappe.db.sql.assert_not_called()

    def test_wildcards_are_literal_and_offset_is_nonnegative(self):
        self.run_search('10%_off', -10)
        self.assertEqual(self.frappe.db.sql.call_args.args[1], {'query': '%10\\%\\_off%', 'start': 0})

if __name__ == '__main__':
    unittest.main()
