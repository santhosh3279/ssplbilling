"""Allocation planning tests; no accounting documents are posted."""
import unittest
from unittest.mock import Mock, patch

from ssplbilling.api import reconcile_api as api


def entry(name, amount, doctype='Payment Entry', date='2026-01-01'):
    return dict(name=name, amount=amount, doctype=doctype, posting_date=date, reference_row=None)


class TestZeroBalanceAutoReconcile(unittest.TestCase):
    def test_one_payment_multiple_invoices(self):
        pay = entry('PAY', 1000)
        invoices = [entry('INV2', 400, 'Sales Invoice', '2026-01-02'), entry('INV1', 600, 'Sales Invoice')]
        pairs = api._match_balanced_ledger([pay], invoices)
        self.assertEqual([(i['name'], amount) for _, i, amount in pairs], [('INV1', 600), ('INV2', 400)])
        self.assertEqual(pay['amount'], 1000)

    def test_many_to_many_and_paise(self):
        payments = [entry('P1', 10.15), entry('P2', 20.25)]
        invoices = [entry('I1', 15.30, 'Purchase Invoice'), entry('I2', 15.10, 'Purchase Invoice')]
        pairs = api._match_balanced_ledger(payments, invoices)
        self.assertEqual([amount for _, _, amount in pairs], [10.15, 5.15, 15.10])
        for row in payments:
            self.assertAlmostEqual(sum(a for p, _, a in pairs if p['name'] == row['name']), row['amount'])
        for row in invoices:
            self.assertAlmostEqual(sum(a for _, i, a in pairs if i['name'] == row['name']), row['amount'])

    def test_unbalanced_or_empty_sides_do_not_split(self):
        self.assertEqual(api._match_balanced_ledger([entry('P', 100)], [entry('I', 99.99)]), [])
        self.assertEqual(api._match_balanced_ledger([], []), [])

    def test_no_self_reconciliation(self):
        self.assertEqual(api._match_balanced_ledger([entry('JE', 100, 'Journal Entry')], [entry('JE', 100, 'Journal Entry')]), [])

    def test_preview_requires_zero_ledger_balance(self):
        payments = [entry('P1', 1000), entry('P2', 200)]
        invoices = [entry('I1', 600, 'Sales Invoice'), entry('I2', 400, 'Sales Invoice'), entry('I3', 200, 'Sales Invoice')]
        with patch.object(api, '_build_reconcile_sides', return_value=(payments, invoices)), patch.object(api, '_ledger_is_zero', return_value=False):
            result = api.preview_auto_reconcile('Customer', 'C')
        self.assertEqual(len(result['proposals']), 1)
        self.assertEqual(result['proposals'][0]['amount'], 200)
        self.assertEqual(result['proposals'][0]['match_type'], 'equal_amount')
        with patch.object(api, '_build_reconcile_sides', return_value=(payments, invoices)), patch.object(api, '_ledger_is_zero', return_value=True):
            result = api.preview_auto_reconcile('Supplier', 'S')
        self.assertEqual(len(result['proposals']), 3)
        self.assertEqual(result['total_amount'], 1200)
        self.assertTrue(all(r['match_type'] == 'zero_balance' for r in result['proposals']))

    def test_changed_balance_blocks_posting(self):
        fake = Mock()
        fake.throw.side_effect = ValueError('Ledger balance changed')
        row = dict(party_type='Customer', party='C', payment_type='Payment Entry', payment_name='P', invoice_type='Sales Invoice', invoice_name='I', amount=100, match_type='zero_balance')
        with patch.object(api, 'frappe', fake), patch.object(api, '_ledger_is_zero', return_value=False), patch.object(api, 'post_reconciliation') as post:
            result = api.run_auto_reconcile([row])
        post.assert_not_called()
        fake.db.rollback.assert_called_once_with(save_point='auto_reconcile')
        self.assertEqual(result['reconciled'], 0)
        self.assertEqual(len(result['failures']), 1)

    def test_zero_check_rejects_multiple_accounts(self):
        from types import SimpleNamespace
        fake = Mock()
        with patch.object(api, 'frappe', fake), patch.object(api, '_get_company', return_value='Company'), patch.object(api, '_get_party_account', return_value='Debtors'):
            fake.db.sql.return_value = [SimpleNamespace(account='Debtors', balance=0)]
            self.assertTrue(api._ledger_is_zero('Customer', 'C'))
            fake.db.sql.return_value = [SimpleNamespace(account='Debtors', balance=100), SimpleNamespace(account='Other', balance=-100)]
            self.assertFalse(api._ledger_is_zero('Customer', 'C'))
            fake.db.sql.return_value = [SimpleNamespace(account='Debtors', balance=0.01)]
            self.assertFalse(api._ledger_is_zero('Customer', 'C'))
