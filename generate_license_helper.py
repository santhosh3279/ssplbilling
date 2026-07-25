#!/usr/bin/env python3
import sys
import os
import json
import argparse
from datetime import datetime

# Set up paths so we can import ssplbilling API without full bench context if needed,
# or run it within the bench environment.
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "ssplbilling")))

# Import signature function
try:
    from ssplbilling.api.license_api import calculate_signature
except ImportError:
    # Fallback definition if run outside of Python path
    import hmac
    import hashlib
    LICENSE_SECRET = "ssplbilling_secure_license_key_2026_santhosh"
    def calculate_signature(customer_name, expiry_date, features):
        sorted_features = sorted(features)
        message = f"{customer_name}|{expiry_date}|{','.join(sorted_features)}"
        return hmac.new(
            LICENSE_SECRET.encode("utf-8"),
            message.encode("utf-8"),
            hashlib.sha256
        ).hexdigest()

def main():
    parser = argparse.ArgumentParser(description="Generate signed license.json file for SSPL Billing App")
    parser.add_argument("--customer", required=True, help="Customer name (e.g. 'Sundaram and Sons Private Ltd')")
    parser.add_argument("--expiry", required=True, help="Expiry date in YYYY-MM-DD format")
    parser.add_argument("--features", default="all", help="Comma-separated list of features, or 'all' to include all tiles")
    parser.add_argument("--output", help="Output file path (saves JSON to this file)")

    args = parser.parse_args()

    # Validate date
    try:
        datetime.strptime(args.expiry, "%Y-%m-%d")
    except ValueError:
        print("Error: Expiry date must be in YYYY-MM-DD format", file=sys.stderr)
        sys.exit(1)

    all_possible_features = [
        'sales', 'purchase-invoice', 'quotation', 'sales-order', 'cashier', 
        'purchase-submit', 'ledger', 'general-ledger', 'purchase-order', 
        'journal-contra', 'stock-reconciliation', 'payment', 'expense', 
        'pricelist-update', 'barcode-print', 'incentive-ledger', 
        'incentive-redeem', 'incentive-entry', 'reports', 'store-sale-report', 
        'cost-center-sale-report', 'stock-status-report', 'stock-aging-report', 
        'outstanding-customers-report', 'Cashier-Management', 'cancellation', 
        'pricing-rules', 'discount-rules', 'loading-receipt', 
        'customer-enquiry', 'parcel-address', 'gst-dummy-ledger', 
        'gst-ledger', 'daily-report', 'stock-ledger', 
        'payment-reconciliation', 'store-transfer', 'repack', 'single-entry', 
        'naming-settings', 'invoice-template', 'stock-template', 
        'ssplbillingsettings', 'offer-display', 'catelogue', 'unreconciled', 
        'cheques', 'ledger-sales-purchase-report', 'item-sales-summary', 
        'store-wise-item-sales', 'fast-moving-items', 
        'material-transfer-report', 'land-cost-voucher'
    ]

    if args.features.lower() == "all":
        features = all_possible_features
    else:
        features = [f.strip() for f in args.features.split(",") if f.strip()]

    # Calculate signature
    sig = calculate_signature(args.customer, args.expiry, features)

    license_data = {
        "customer_name": args.customer,
        "expiry_date": args.expiry,
        "features": features,
        "signature": sig
    }

    output_json = json.dumps(license_data, indent=4)
    print(output_json)

    if args.output:
        try:
            with open(args.output, "w") as f:
                f.write(output_json)
            print(f"\nLicense successfully written to: {args.output}")
        except Exception as e:
            print(f"Error saving to file: {e}", file=sys.stderr)

if __name__ == "__main__":
    main()
