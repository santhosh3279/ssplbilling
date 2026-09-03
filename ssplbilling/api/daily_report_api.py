import frappe
from frappe.utils import flt, getdate

@frappe.whitelist()
def get_daily_reports(report_type, from_date, to_date, naming_series=None, company=None):
        """
        Returns a list of documents for a specific date range and type.
        report_type: 'Sales Invoice', 'Purchase Invoice', 'Payment', 'Journal', 'Quotation', 'Loading'
        """
        if not from_date: from_date = frappe.utils.today()
        if not to_date: to_date = frappe.utils.today()

        if report_type == 'Sales Invoice':
                filters = {
                        "posting_date": ["between", [from_date, to_date]],
                        "docstatus": ["<", 2]
                }
                if company:
                        filters["company"] = company
                if naming_series:
                        if isinstance(naming_series, str):
                                if naming_series.startswith("[") and naming_series.endswith("]"):
                                        import json
                                        try:
                                                naming_series = json.loads(naming_series)
                                        except Exception:
                                                pass
                        if isinstance(naming_series, list):
                                if len(naming_series) > 0:
                                        filters["naming_series"] = ["in", naming_series]
                        else:
                                filters["naming_series"] = naming_series

                return frappe.get_all(
                        "Sales Invoice",
                        filters=filters,
                        fields=["name", "customer_name", "grand_total", "total_taxes_and_charges", "docstatus", "posting_date", "posting_time", "naming_series"],
                        order_by="posting_date desc, posting_time desc"
                )

        elif report_type == 'Purchase Invoice':
                filters = {
                        "posting_date": ["between", [from_date, to_date]],
                        "docstatus": ["<", 2]
                }
                if company:
                        filters["company"] = company
                if naming_series:
                        if isinstance(naming_series, str):
                                if naming_series.startswith("[") and naming_series.endswith("]"):
                                        import json
                                        try:
                                                naming_series = json.loads(naming_series)
                                        except Exception:
                                                pass
                        if isinstance(naming_series, list):
                                if len(naming_series) > 0:
                                        filters["naming_series"] = ["in", naming_series]
                        else:
                                filters["naming_series"] = naming_series

                return frappe.get_all(
                        "Purchase Invoice",
                        filters=filters,
                        fields=["name", "supplier_name", "grand_total", "total_taxes_and_charges", "docstatus", "posting_date", "posting_time", "naming_series"],
                        order_by="posting_date desc, posting_time desc"
                )

        elif report_type == 'Payment':
                filters = {"posting_date": ["between", [from_date, to_date]], "docstatus": ["<", 2]}
                if company:
                        filters["company"] = company
                return frappe.get_all(
                        "Payment Entry",
                        filters=filters,
                        fields=["name", "party_name", "paid_amount", "received_amount", "mode_of_payment", "docstatus", "posting_date", "payment_type"],
                        order_by="posting_date desc, creation desc"
                )

        elif report_type == 'Journal':
                filters = {"posting_date": ["between", [from_date, to_date]], "docstatus": ["<", 2]}
                if company:
                        filters["company"] = company
                return frappe.get_all(
                        "Journal Entry",
                        filters=filters,
                        fields=["name", "voucher_type", "total_debit", "total_credit", "docstatus", "user_remark", "posting_date"],
                        order_by="posting_date desc, creation desc"
                )

        elif report_type == 'Quotation':
                filters = {"transaction_date": ["between", [from_date, to_date]], "docstatus": ["<", 2]}
                if company:
                        filters["company"] = company
                return frappe.get_all(
                        "Quotation",
                        filters=filters,
                        fields=["name", "customer_name", "grand_total", "docstatus", "status", "transaction_date"],
                        order_by="transaction_date desc, creation desc"
                )

        elif report_type == 'Loading':
                company_condition = ""
                params = [from_date, to_date]
                if company and frappe.get_meta("Loading Receipt").has_field("company"):
                        company_condition = " AND lr.company = %s"
                        params.append(company)
                return frappe.db.sql("""
                        SELECT 
                                lr.name, lr.date, lr.customer_name, lr.bill_no,
                                lri.item, lri.item_name, lri.qty, lri.rate, lri.amount
                        FROM `tabLoading Receipt` lr
                        JOIN `tabLoading Receipt Item` lri ON lri.parent = lr.name
                        WHERE lr.date BETWEEN %s AND %s{company_condition}
                        ORDER BY lr.date DESC, lr.creation DESC
                """.format(company_condition=company_condition), tuple(params), as_dict=True)

        return []

@frappe.whitelist()
def get_current_fiscal_year_dates():
        """
        Returns the year_start_date and year_end_date of the current Fiscal Year.
        """
        today = frappe.utils.today()
        fy = frappe.db.get_value("Fiscal Year", 
                {"year_start_date": ["<=", today], "year_end_date": [">=", today]}, 
                ["year_start_date", "year_end_date"], as_dict=True)
        
        if not fy:
                # Fallback to the latest fiscal year if today isn't covered
                fy = frappe.db.get_value("Fiscal Year", {}, ["year_start_date", "year_end_date"], 
                        order_by="year_start_date desc", as_dict=True)
        
        if fy:
                return {
                        "from": str(fy.year_start_date),
                        "to": str(fy.year_end_date)
                }
        return None
