"""Allocation planning tests; no accounting documents are posted."""
import unittest
from unittest.mock import Mock, patch

from ssplbilling.api import reconcile_api as api


def entry(name, amount, doctype='Payment Entry', date='2026-01-01', **extra):
    return dict(name=name, amount=amount, doctype=doctype, posting_date=date, reference_row=None, **extra)


def summary(plan):
    return [(p['name'], i['name'], amount, kind) for p, i, amount, kind in plan]


class TestStagedAutoReconcile(unittest.TestCase):
    def test_return_goes_to_its_own_invoice(self):
        note = entry('RET1', 300, 'Sales Invoice', '2026-01-05', return_against='INV2')
        invoices = [entry('INV1', 300, 'Sales Invoice'), entry('INV2', 500, 'Sales Invoice', '2026-01-02')]
        self.assertEqual(summary(api._plan_allocations([note], invoices)), [('RET1', 'INV2', 300, 'return')])

    def test_exact_amount_beats_older_bill(self):
        payments = [entry('P1', 400)]
        invoices = [entry('I1', 1000, 'Sales Invoice'), entry('I2', 400, 'Sales Invoice', '2026-01-03')]
        self.assertEqual(summary(api._plan_allocations(payments, invoices))[0], ('P1', 'I2', 400, 'exact'))

    def test_reference_in_remarks(self):
        payments = [entry('P1', 700, remarks='Against SINV-0012 and SINV-0001')]
        invoices = [
            entry('SINV-00012', 900, 'Sales Invoice'),
            entry('SINV-0012', 500, 'Sales Invoice', '2026-01-02'),
        ]
        plan = summary(api._plan_allocations(payments, invoices))
        # SINV-0012 matched by reference (whole token only), rest oldest-first
        self.assertEqual(plan, [('P1', 'SINV-0012', 500, 'reference'), ('P1', 'SINV-00012', 200, 'oldest_first')])

    def test_combo_of_bills(self):
        payments = [entry('P1', 900)]
        invoices = [entry('I1', 100, 'Sales Invoice'), entry('I2', 300, 'Sales Invoice'), entry('I3', 600, 'Sales Invoice')]
        plan = summary(api._plan_allocations(payments, invoices))
        self.assertEqual(plan, [('P1', 'I2', 300, 'combo'), ('P1', 'I3', 600, 'combo')])

    def test_oldest_first_partial_and_paise(self):
        payments = [entry('P1', 10.15), entry('P2', 20.25, date='2026-01-02')]
        invoices = [entry('I1', 15.30, 'Purchase Invoice'), entry('I2', 15.11, 'Purchase Invoice', '2026-01-02')]
        plan = api._plan_allocations(payments, invoices)
        self.assertTrue(all(kind == 'oldest_first' for *_, kind in plan))
        self.assertEqual([amount for *_, amount, _ in plan], [10.15, 5.15, 15.10])
        self.assertEqual(payments[0]['amount'], 10.15)  # inputs untouched

    def test_no_self_reconciliation(self):
        je = entry('JE', 100, 'Journal Entry')
        self.assertEqual(api._plan_allocations([je], [dict(je)]), [])

    def test_preview_rows_carry_match_type(self):
        payments = [entry('P1', 200), entry('P2', 1000)]
        invoices = [entry('I1', 600, 'Sales Invoice'), entry('I2', 200, 'Sales Invoice')]
        with patch.object(api, '_build_reconcile_sides', return_value=(payments, invoices)):
            result = api.preview_auto_reconcile('Customer', 'C')
        kinds = [r['match_type'] for r in result['proposals']]
        self.assertEqual(kinds, ['exact', 'oldest_first'])
        self.assertEqual(result['total_amount'], 800)

    def test_changed_ledger_blocks_posting(self):
        fake = Mock()
        fake.throw.side_effect = ValueError('changed')
        row = dict(party_type='Customer', party='C', payment_type='Payment Entry', payment_name='P', invoice_type='Sales Invoice', invoice_name='I', amount=100, match_type='exact')
        sides = ([entry('P', 50)], [entry('I', 100, 'Sales Invoice')])
        with patch.object(api, 'frappe', fake), patch.object(api, '_build_reconcile_sides', return_value=sides), patch.object(api, 'post_reconciliation') as post:
            result = api.run_auto_reconcile([row])
        post.assert_not_called()
        fake.db.rollback.assert_called_once_with(save_point='auto_reconcile')
        self.assertEqual(result['reconciled'], 0)
        self.assertEqual(len(result['failures']), 1)
