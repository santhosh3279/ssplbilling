import frappe
from india_compliance.gst_india.utils.gstin_info import _get_gstin_info

@frappe.whitelist()
def validate_gstin(gstin):
    """
    Wrapper for India Compliance's _get_gstin_info to bypass desk access check.
    Returns GSTIN info including business name and addresses.
    """
    try:
        info = _get_gstin_info(gstin, throw_error=True)
        return info
    except Exception as e:
        frappe.throw(str(e))
