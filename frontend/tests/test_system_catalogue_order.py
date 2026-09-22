"""Permission and pricing regression checks for System User catalogue orders."""
import ast
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock
import unittest

SOURCE = Path(__file__).resolve().parents[2] / 'ssplbilling/api/catalogue_order_api.py'

class SystemCatalogueOrderTest(unittest.TestCase):
    def setUp(self):
        names = {'_is_system_user', '_order_context', 'get_order_options', 'get_system_order_context', 'get_customer_offer', 'get_cart_preview', 'place_order'}
        functions = [n for n in ast.parse(SOURCE.read_text()).body if isinstance(n, ast.FunctionDef) and n.name in names]
        for fn in functions: fn.decorator_list = []
        self.customer = SimpleNamespace(name='CUST-1', customer_name='Customer One', default_price_list='Retail', disabled=0, check_permission=Mock())
        self.prices = SimpleNamespace(name='Wholesale', enabled=1, selling=1, check_permission=Mock())
        self.frappe = SimpleNamespace(session=Session(user='staff'), get_cached_value=Mock(return_value='System User'),
            has_permission=Mock(), get_doc=Mock(side_effect=lambda dt, name: self.customer if dt == 'Customer' else self.prices),
            throw=Mock(side_effect=ValueError('Rejected')), PermissionError=PermissionError)
        self.website_context = Mock(return_value={'customer': 'Linked', 'price_list': 'Website'})
        self.ns = {'frappe': self.frappe, '_customer_context': self.website_context, 'flt': float,
                   'today': lambda: '2026-09-22', 'add_days': lambda day, days: '2026-09-29'}
        exec(compile(ast.Module(body=functions, type_ignores=[]), str(SOURCE), 'exec'), self.ns)

    def test_system_user_selects_customer_and_price_list(self):
        result = self.ns['_order_context']('CUST-1', 'Wholesale')
        self.assertEqual(result, {'customer': 'CUST-1', 'customer_name': 'Customer One', 'price_list': 'Wholesale'})
        self.frappe.has_permission.assert_called_once_with('Sales Order', 'create', throw=True)
        self.customer.check_permission.assert_called_once_with('read')
        self.prices.check_permission.assert_called_once_with('read')
        self.frappe.get_doc.assert_any_call('Price List', 'Wholesale')

    def test_default_customer_price_list_is_used(self):
        self.ns['_order_context']('CUST-1')
        self.frappe.get_doc.assert_any_call('Price List', 'Retail')

    def test_website_user_cannot_override_linked_customer_or_price_list(self):
        self.frappe.get_cached_value.return_value = 'Website User'
        self.assertEqual(self.ns['_order_context']('Other Customer', 'Secret List'), self.website_context.return_value)
        self.frappe.get_doc.assert_not_called()

    def test_guest_uses_existing_rejecting_website_auth(self):
        self.frappe.session.user = 'Guest'
        self.website_context.side_effect = PermissionError()
        with self.assertRaises(PermissionError): self.ns['_order_context']('CUST-1', 'Wholesale')

    def test_invalid_customer_or_price_list_rejected(self):
        with self.assertRaises(ValueError): self.ns['_order_context']()
        self.customer.disabled = 1
        with self.assertRaises(ValueError): self.ns['_order_context']('CUST-1', 'Wholesale')
        self.customer.disabled = 0
        self.prices.selling = 0
        with self.assertRaises(ValueError): self.ns['_order_context']('CUST-1', 'Wholesale')
        self.prices.selling = 1
        self.prices.enabled = 0
        with self.assertRaises(ValueError): self.ns['_order_context']('CUST-1', 'Wholesale')

    def test_create_permission_is_required(self):
        self.frappe.has_permission.side_effect = PermissionError()
        with self.assertRaises(PermissionError): self.ns['_order_context']('CUST-1', 'Wholesale')

    def test_offer_uses_selected_list_for_every_barcode(self):
        self.ns['get_offer_details'] = lambda page: {'items': [{'itemcode': 'A', 'barcode': '1', 'barcode_prices': [{'barcode': '1'}, {'barcode': '2'}]}]}
        self.ns['_order_price'] = Mock(return_value=(None, 'Nos', 12))
        result = self.ns['get_customer_offer']('offers', 'CUST-1', 'Wholesale')
        self.assertEqual(result['offer']['price_lists'], [{'price_list': 'Wholesale'}])
        self.assertEqual(result['offer']['items'][0]['barcode_prices'][1]['prices'], {'Wholesale': 12})
        self.assertTrue(all(call.args[1] == 'Wholesale' for call in self.ns['_order_price'].call_args_list))

    def test_party_options_are_permission_filtered_and_system_only(self):
        self.frappe.get_list = Mock(return_value=[])
        result = self.ns['get_order_options']('Customer')
        self.assertEqual(result, {'customers': [], 'price_lists': []})
        self.assertEqual(self.frappe.get_list.call_args_list[0].args, ('Customer',))
        self.assertEqual(self.frappe.get_list.call_args_list[1].kwargs['filters'], {'enabled': 1, 'selling': 1})
        self.frappe.get_cached_value.return_value = 'Website User'
        with self.assertRaises(ValueError): self.ns['get_order_options']('Customer')
        with self.assertRaises(ValueError): self.ns['get_system_order_context']('CUST-1', 'Wholesale')

    def test_order_uses_selected_context_without_admin_escalation(self):
        self.ns['_preview'] = Mock(return_value={'customer': 'CUST-1', 'price_list': 'Wholesale', 'items': []})
        self.frappe.get_cached_doc = Mock(return_value=SimpleNamespace(online_order_company='Company', online_order_series='SO-', online_order_warehouse='WH', online_order_cost_center='CC'))
        self.frappe.db = SimpleNamespace(get_value=Mock(side_effect=lambda dt, name, field: 'Company' if field == 'company' else 0), set_value=Mock())
        order = SimpleNamespace(insert=Mock(), append=Mock(), name='SO-1', grand_total=12)
        self.frappe.new_doc = Mock(return_value=order)
        self.frappe.set_user = Mock()
        self.ns['place_order']([], 'CUST-1', 'Wholesale')
        self.ns['_preview'].assert_called_once_with([], 'CUST-1', 'Wholesale')
        self.assertEqual(order.customer, 'CUST-1')
        self.assertEqual(order.selling_price_list, 'Wholesale')
        order.insert.assert_called_once_with()
        self.frappe.set_user.assert_not_called()

class Session(dict):
    __getattr__ = dict.get
    __setattr__ = dict.__setitem__

if __name__ == '__main__': unittest.main()
