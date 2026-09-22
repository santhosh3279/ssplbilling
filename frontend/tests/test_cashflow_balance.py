"""Database-free checks for the cashflow closing-balance query."""
import ast
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import Mock


class CashflowBalanceTest(unittest.TestCase):
    def setUp(self):
        path = Path(__file__).resolve().parents[2] / 'ssplbilling/api/reports_api.py'
        tree = ast.parse(path.read_text())
        function = next(n for n in tree.body if isinstance(n, ast.FunctionDef)
                        and n.name == 'get_cashflow_report')
        function.decorator_list = []
        self.rows = [dict(account='Cash', inflow=150, outflow=40),
                     dict(account='Bank', inflow=25, outflow=60)]
        self.frappe = SimpleNamespace(
            utils=SimpleNamespace(cint=lambda value: int(value or 0)),
            get_all=Mock(return_value=['Cash', 'Bank']),
            db=SimpleNamespace(sql=Mock(return_value=self.rows)),
        )
        self.transfer = Mock(return_value='transfer_predicate')
        namespace = dict(frappe=self.frappe,
                         _cashflow_cheque_clearing_accounts=lambda: ('Pending',),
                         _cashflow_cleared_cheque_condition=lambda: 'cleared_predicate',
                         _cashflow_internal_transfer_condition=self.transfer)
        exec(compile(ast.Module(body=[function], type_ignores=[]), str(path), 'exec'), namespace)
        self.report = namespace['get_cashflow_report']

    def test_balances_use_one_query_without_transfer_classification(self):
        result = self.report('1000-01-01', '2026-09-22', 'Company', '1')
        self.frappe.db.sql.assert_called_once()
        sql, params = self.frappe.db.sql.call_args.args
        self.assertEqual(params, ('1000-01-01', '2026-09-22', ('Cash', 'Bank'), 'Company'))
        for condition in ('gle.is_cancelled = 0', 'gle.account IN %s',
                          'gle.company = %s', 'cleared_predicate', 'GROUP BY gle.account'):
            self.assertIn(condition, sql)
        self.transfer.assert_not_called()
        self.assertNotIn('transfer_predicate', sql)
        self.assertEqual(result['breakdown'], self.rows)
        self.assertEqual(sum(r['inflow'] - r['outflow'] for r in result['summary']), 75)
        self.assertEqual(result['internal_summary'], [])
        self.assertEqual(result['internal_breakdown'], [])

    def test_no_accounts_needs_no_query(self):
        self.frappe.get_all.return_value = []
        result = self.report('1000-01-01', '2026-09-22', 'Company', 1)
        self.assertEqual(result['summary'], [])
        self.assertEqual(result['breakdown'], [])
        self.frappe.db.sql.assert_not_called()

    def test_optional_company_has_matching_parameters(self):
        self.report('1000-01-01', '2026-09-22', balance_only=1)
        sql, params = self.frappe.db.sql.call_args.args
        self.assertNotIn('gle.company = %s', sql)
        self.assertEqual(len(params), 3)


if __name__ == '__main__':
    unittest.main()
