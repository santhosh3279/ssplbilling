"""Isolated API checks. No site, database or existing bills are changed."""
import datetime
import importlib.util
import pathlib
import sys
import types
import unittest
from unittest.mock import Mock, patch

frappe = types.ModuleType('frappe')
frappe.whitelist = lambda: lambda fn: fn
frappe.session = types.SimpleNamespace(user='test@example.com')
frappe.PermissionError = PermissionError

def throw(message, exception=ValueError):
    raise exception(message)

frappe.throw = throw
utils = types.ModuleType('frappe.utils')
utils.getdate = lambda value: datetime.date.fromisoformat(str(value))
utils.now = lambda: '2026-10-08 12:00:00'
utils.add_days = lambda value, days: str(utils.getdate(value) + datetime.timedelta(days=days))
accounts = types.ModuleType('erpnext.accounts.utils')
accounts.get_fiscal_year = lambda *args, **kwargs: ('2026',)
sys.modules.update({'frappe': frappe, 'frappe.utils': utils, 'erpnext.accounts.utils': accounts})
path = pathlib.Path(__file__).resolve().parents[2] / 'ssplbilling/api/modify_submitted_api.py'
spec = importlib.util.spec_from_file_location('modify_api', path)
api = importlib.util.module_from_spec(spec)
spec.loader.exec_module(api)

class Document:
    def __init__(self, doctype):
        self.doctype = doctype
        self.name = 'SAME-NUMBER'
        self.company = 'Company A'
        self.docstatus = 1
        self.transaction_date = '2026-10-07'
        self.posting_date = '2026-10-07'
        self.meta = types.SimpleNamespace(get_label=lambda field: field, has_field=lambda field: False)
        self.check_permission = Mock()
        self.add_comment = Mock()
        self.insert = Mock(side_effect=self.insert_named)
        self.set = Mock()
    def get(self, field):
        return getattr(self, field, None)
    def insert_named(self, set_name):
        self.name = set_name

class ApiTests(unittest.TestCase):
    def setUp(self):
        frappe.db = Mock()
        frappe.db.exists.return_value = True
        frappe.get_doc = Mock()
        frappe.clear_document_cache = Mock()
        frappe.copy_doc = Mock()
        frappe.get_meta = Mock(return_value=types.SimpleNamespace(has_field=lambda field: False))
        frappe.get_all = Mock(return_value=[])
    def test_fetch_all_five_with_explicit_type_and_read_permission(self):
        for kind in api.SUPPORTED_DOCTYPES:
            doc = Document(kind)
            frappe.get_doc.return_value = doc
            with patch.object(api, '_submitted_mirror_name', return_value=None):
                result = api.get_submitted_invoice(doc.name, kind)
            self.assertEqual(result['doctype'], kind)
            self.assertEqual(result['posting_date'], '2026-10-07')
            self.assertEqual(result['date_field'], 'posting_date' if kind in api.INVOICE_DOCTYPES else 'transaction_date')
            doc.check_permission.assert_called_once_with('read')
        with self.assertRaisesRegex(ValueError, 'multiple document types'):
            api.get_submitted_invoice('SAME-NUMBER')
    def test_read_and_write_denials(self):
        doc = Document('Sales Order')
        doc.check_permission.side_effect = PermissionError('Denied')
        frappe.get_doc.return_value = doc
        with self.assertRaises(PermissionError):
            api.get_submitted_invoice(doc.name, doc.doctype)
        with self.assertRaises(PermissionError):
            api.modify_submitted_bill_date(doc.name, '2026-10-08', doc.doctype)
        frappe.db.set_value.assert_not_called()
    def test_non_invoice_dates_only_update_transaction_date(self):
        for kind in ('Quotation', 'Sales Order', 'Purchase Order'):
            doc = Document(kind)
            frappe.get_doc.return_value = doc
            result = api.modify_submitted_bill_date(doc.name, '2026-10-08', kind)
            self.assertEqual(result['status'], 'success')
            args = frappe.db.set_value.call_args
            self.assertEqual(args.args[0], kind)
            self.assertEqual(args.args[2]['transaction_date'], '2026-10-08')
            self.assertNotIn('posting_date', args.args[2])
            frappe.db.sql.assert_not_called()
            doc.check_permission.assert_called_once_with('write')
    def test_date_constraints_and_submitted_state(self):
        doc = Document('Quotation')
        frappe.get_doc.return_value = doc
        doc.valid_till = '2026-10-07'
        with self.assertRaisesRegex(ValueError, 'valid_till'):
            api.modify_submitted_bill_date(doc.name, '2026-10-08', doc.doctype)
        frappe.db.set_value.assert_not_called()
        doc.valid_till = None
        doc.docstatus = 0
        with self.assertRaisesRegex(ValueError, 'submitted'):
            api.modify_submitted_bill_date(doc.name, '2026-10-08', doc.doctype)
    def test_draft_creation_for_all_five_uses_normal_cancel_and_permissions(self):
        for kind in api.SUPPORTED_DOCTYPES:
            doc, archived, draft = Document(kind), Document(kind), Document(kind)
            archived.name += '-1'
            frappe.get_doc.return_value = doc
            frappe.copy_doc.return_value = draft
            with patch.object(api, '_submitted_mirror_name', return_value=None), \
                 patch.object(api, '_linked_payment_vouchers', return_value=set()), \
                 patch.object(api, '_unlink_payments_and_cancel') as cancel, \
                 patch.object(api, '_archive_cancelled_invoice', return_value=archived):
                result = api.move_submitted_to_draft(doc.name, kind)
            cancel.assert_called_once_with(doc, set())
            self.assertEqual([call.args[0] for call in doc.check_permission.call_args_list], ['cancel', 'write'])
            draft.insert.assert_called_once_with(set_name=doc.name)
            self.assertEqual(draft.amended_from, archived.name)
            self.assertEqual(result['doctype'], kind)
            self.assertEqual(draft.docstatus, 0)
    def test_normal_cancel_link_checks_are_preserved(self):
        doc = Document('Sales Order')
        doc.reload = Mock()
        doc.cancel = Mock(side_effect=ValueError('Linked delivery blocks cancellation'))
        with self.assertRaisesRegex(ValueError, 'Linked delivery'):
            api._unlink_payments_and_cancel(doc, set())
        doc.reload.assert_called_once()
        doc.cancel.assert_called_once()
        frappe.copy_doc.assert_not_called()
    def test_order_advance_references(self):
        frappe.get_all.side_effect = [['PAY-1'], ['JV-1']]
        self.assertEqual(api._linked_payment_vouchers(Document('Sales Order')), {('Payment Entry', 'PAY-1'), ('Journal Entry', 'JV-1')})
        self.assertEqual(api._linked_payment_vouchers(Document('Quotation')), set())

if __name__ == '__main__':
    unittest.main()
