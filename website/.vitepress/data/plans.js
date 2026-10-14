// ─────────────────────────────────────────────────────────────────────────────
// PRICING — edit this file to change the rates shown on the home and pricing pages.
// All prices below are PLACEHOLDERS. Replace `price` with real figures before going live.
// Set `price: null` to show "Contact us" instead of a number.
// ─────────────────────────────────────────────────────────────────────────────

export const currency = '₹'
export const billingNote = 'Prices exclude GST. Billed per company, per year.'

export const plans = [
  {
    id: 'starter',
    name: 'Starter',
    tagline: 'Single counter shops getting off paper',
    price: null, // TODO: set yearly price, e.g. 15000
    period: '/ year',
    users: 'Up to 3 users',
    stores: '1 store / warehouse',
    modules: ['Sales & Customers', 'Cashier & Financials'],
    highlights: [
      'Keyboard-first Sales Entry',
      'Cashier Desk with split payments',
      'Customer ledger & payment receipts',
      'Barcode billing & label printing',
      'Daily report',
    ],
    cta: 'Talk to us',
  },
  {
    id: 'business',
    name: 'Business',
    tagline: 'Wholesale traders with stock and purchase',
    price: null, // TODO: set yearly price
    period: '/ year',
    users: 'Up to 10 users',
    stores: 'Up to 3 stores',
    featured: true,
    modules: [
      'Sales & Customers',
      'Cashier & Financials',
      'Purchase & Suppliers',
      'Inventory & Stock',
      'Tax & Reporting',
    ],
    highlights: [
      'Everything in Starter',
      'Purchase invoices, orders & landed cost',
      'Store transfer, repack & stock reconciliation',
      'Discount rules & customer pricing',
      'GST ledger, E-Way Bill & 15+ reports',
    ],
    cta: 'Book a demo',
  },
  {
    id: 'enterprise',
    name: 'Enterprise',
    tagline: 'Multi-store groups with staff and loyalty',
    price: null, // TODO: set yearly price, or keep null for "Contact us"
    period: '/ year',
    users: 'Unlimited users',
    stores: 'Unlimited stores',
    modules: 'all',
    highlights: [
      'Everything in Business',
      'HRMS, attendance & biometric devices',
      'Incentive earn / redeem program',
      'Live bill panels & real-time sync',
      'Priority support & on-site training',
    ],
    cta: 'Contact sales',
  },
]

// One-time and optional charges shown under the plan cards.
export const extras = [
  { item: 'Implementation, data migration & setup', price: null, unit: 'one-time' }, // TODO
  { item: 'On-site staff training (per day)', price: null, unit: 'per day' }, // TODO
  { item: 'Additional user', price: null, unit: 'per user / year' }, // TODO
  { item: 'Additional store / warehouse', price: null, unit: 'per store / year' }, // TODO
  { item: 'Annual support & updates after year 1', price: null, unit: 'per year' }, // TODO
]

export function formatPrice(value) {
  if (value === null || value === undefined) return 'Contact us'
  return currency + Number(value).toLocaleString('en-IN')
}
