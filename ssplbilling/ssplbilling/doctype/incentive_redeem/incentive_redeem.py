# Copyright (c) 2026, SSPL and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt, nowdate
from erpnext.accounts.party import get_party_account


class IncentiveRedeem(Document):
        def before_insert(self):
                if not self.incentive_ledger:
                        self.incentive_ledger = frappe.db.get_single_value("Incentive Rule", "incentive_ledger")

	def validate(self):
		balance = flt(frappe.db.get_value("Employee", self.employee, "balance_incentive"))
		self.balance_points = balance
		if flt(self.redeem_points) <= 0:
			frappe.throw(_("Redeem Points must be greater than zero."))
		if flt(self.redeem_points) > balance:
			frappe.throw(
				_("Redeem Points ({0}) cannot exceed Balance Points ({1}).").format(
					self.redeem_points, balance
				)
			)

	def on_submit(self):
		pe = self._create_payment_entry()
		self.db_set("payment_entry", pe.name)
		self._update_employee_redeemed(multiplier=1)

	def on_cancel(self):
		if self.payment_entry:
			pe = frappe.get_doc("Payment Entry", self.payment_entry)
			if pe.docstatus == 1:
				pe.cancel()
		self._update_employee_redeemed(multiplier=-1)

	def _create_payment_entry(self):
		company_currency = frappe.db.get_value("Company", self.company, "default_currency")
		party_account = get_party_account("Employee", self.employee, self.company)
		conversion_factor = flt(frappe.db.get_single_value("Incentive Rule", "conversion_factor")) or 4.0
		amount = flt(self.redeem_points) / conversion_factor

		pe = frappe.get_doc(
			{
				"doctype": "Payment Entry",
				"payment_type": "Pay",
				"party_type": "Employee",
				"party": self.employee,
				"party_name": self.employee_name,
				"company": self.company,
				"posting_date": self.posting_date or nowdate(),
				"cost_center": self.cost_center,
				"paid_from": self.incentive_ledger,
				"paid_from_account_currency": company_currency,
				"paid_to": party_account,
				"paid_to_account_currency": company_currency,
				"paid_amount": amount,
				"received_amount": amount,
				"reference_no": self.name,
				"reference_date": self.posting_date or nowdate(),
				"remarks": "Incentive redemption for {0}".format(self.employee),
			}
		)
		pe.insert(ignore_permissions=True)
		pe.submit()
		return pe

	def _update_employee_redeemed(self, multiplier):
		current = frappe.db.get_value(
			"Employee",
			self.employee,
			["total_incentive", "redeemed_incentive"],
			as_dict=True,
		)
		new_redeemed = flt(current.redeemed_incentive) + multiplier * flt(self.redeem_points)
		new_balance = flt(current.total_incentive) - new_redeemed
		frappe.db.set_value(
			"Employee",
			self.employee,
			{
				"redeemed_incentive": flt(new_redeemed, 2),
				"balance_incentive": flt(new_balance, 2),
			},
		)
