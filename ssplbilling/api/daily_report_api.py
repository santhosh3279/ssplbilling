import frappe
from frappe.utils import flt

@frappe.whitelist()
def get_daily_reports(report_type, from_date, to_date, naming_series=None):
        """
        Returns a list of documents for a specific date range and type.
        report_type: 'Invoice', 'Payment', 'Journal', 'Quotation', 'Loading'
        """
        if not from_date: from_date = frappe.utils.today()
        if not to_date: to_date = frappe.utils.today()

        if report_type == 'Invoice':
                filters = {
                        "posting_date": ["between", [from_date, to_date]],
                        "docstatus": ["<", 2]
                }
                if naming_series:
                        filters["naming_series"] = naming_series

                return frappe.get_all(
                        "Sales Invoice",
                        filters=filters,
                        fields=["name", "customer_name", "grand_total", "docstatus", "posting_date", "posting_time", "naming_series"],
                        order_by="posting_date desc, posting_time desc"
                )

        elif report_type == 'Payment':
                return frappe.get_all(
                        "Payment Entry",
                        filters={"posting_date": ["between", [from_date, to_date]], "docstatus": ["<", 2]},
                        fields=["name", "party_name", "paid_amount", "received_amount", "mode_of_payment", "docstatus", "posting_date", "payment_type"],
                        order_by="posting_date desc, creation desc"
                )

        elif report_type == 'Journal':
                return frappe.get_all(
                        "Journal Entry",
                        filters={"posting_date": ["between", [from_date, to_date]], "docstatus": ["<", 2]},
                        fields=["name", "voucher_type", "total_debit", "total_credit", "docstatus", "user_remark", "posting_date"],
                        order_by="posting_date desc, creation desc"
                )

        elif report_type == 'Quotation':
                return frappe.get_all(
                        "Quotation",
                        filters={"transaction_date": ["between", [from_date, to_date]], "docstatus": ["<", 2]},
                        fields=["name", "customer_name", "grand_total", "docstatus", "status", "transaction_date"],
                        order_by="transaction_date desc, creation desc"
                )

        elif report_type == 'Loading':
                return frappe.db.sql("""
                        SELECT 
                                lr.name, lr.date, lr.customer_name, lr.bill_no,
                                lri.item, lri.item_name, lri.qty, lri.rate, lri.amount
                        FROM `tabLoading Receipt` lr
                        JOIN `tabLoading Receipt Item` lri ON lri.parent = lr.name
                        WHERE lr.date BETWEEN %s AND %s
                        ORDER BY lr.date DESC, lr.creation DESC
                """, (from_date, to_date), as_dict=True)

        return []
