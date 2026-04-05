import re

with open('ssplbilling/api/dashboard_api.py', 'r') as f:
    content = f.read()

# Add Purchase Invoice handling to get_allowed_series
old_block = """        if doctype == "Sales Invoice":
            available = [r.series for r in settings.billing_series if r.series]
        elif doctype == "Quotation":
            from ssplbilling.api.quotation_api import get_naming_series
            available = get_naming_series()"""

new_block = """        if doctype == "Sales Invoice":
            # We fetch all from settings.billing_series, but we'll intersect later in the frontend,
            # or we can intersect right here. The prompt is easier fixed in frontend.
            available = [r.series for r in settings.billing_series if r.series]
        elif doctype == "Purchase Invoice":
            available = [r.series for r in settings.billing_series if r.series]
        elif doctype == "Quotation":
            from ssplbilling.api.quotation_api import get_naming_series
            available = get_naming_series()"""

if old_block in content:
    content = content.replace(old_block, new_block)
    with open('ssplbilling/api/dashboard_api.py', 'w') as f:
        f.write(content)
        print("Updated dashboard_api.py")
else:
    print("Could not find block in dashboard_api.py")
