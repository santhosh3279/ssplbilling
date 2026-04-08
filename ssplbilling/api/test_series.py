import frappe
from frappe.model.naming import parse_naming_series

def get_next_number(series):
    if ".#" in series:
        prefix, hashes = series.rsplit(".#", 1)
        hashes = "#" + hashes
    elif "#" in series:
        prefix, hashes = series.rsplit("#", 1)
        hashes = "#" + hashes
    else:
        prefix = series
        hashes = "#####"

    parsed_prefix = parse_naming_series(prefix)
    current = frappe.db.sql("select `current` from `tabSeries` where name=%s", (parsed_prefix,))
    current = current[0][0] if current else 0
    return f"{parsed_prefix}{str(current + 1).zfill(len(hashes))}"

def test():
    print(get_next_number("EOW-.YYYY.-"))
    print(get_next_number("EOW-.YYYY.-.####"))
