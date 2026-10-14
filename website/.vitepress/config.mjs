import { defineConfig } from 'vitepress'

// Set SITE_BASE=/docs/ when nginx serves the site under a sub-path instead of its own domain.
const base = process.env.SITE_BASE || '/'

export default defineConfig({
  base,
  lang: 'en-IN',
  title: 'SSPL Billing',
  description: 'Fast wholesale billing and ERP front-end built on Frappe / ERPNext',
  cleanUrls: true,
  lastUpdated: true,
  head: [['link', { rel: 'icon', type: 'image/png', href: `${base}favicon.png` }]],

  vite: {
    server: {
      // Requests arrive through nginx with the public host name; allow them in dev mode.
      allowedHosts: true,
      // The module list is read from ../licensing_features_by_category.json in the app root.
      fs: { allow: ['..'] },
    },
  },

  themeConfig: {
    logo: '/favicon.png',
    nav: [
      { text: 'Pricing', link: '/pricing' },
      { text: 'Guide', link: '/guide/getting-started' },
      { text: 'Features', link: '/features' },
      { text: 'FAQ', link: '/faq' },
      { text: 'Contact', link: '/contact' },
    ],
    sidebar: {
      '/guide/': [
        {
          text: 'Start here',
          items: [
            { text: 'Getting started', link: '/guide/getting-started' },
            { text: 'Dashboard & navigation', link: '/guide/dashboard' },
            { text: 'Keyboard shortcuts', link: '/guide/shortcuts' },
          ],
        },
        {
          text: 'Daily work',
          items: [
            { text: 'Sales & billing', link: '/guide/sales' },
            { text: 'Cashier desk', link: '/guide/cashier' },
            { text: 'Purchase', link: '/guide/purchase' },
            { text: 'Inventory & stock', link: '/guide/stock' },
            { text: 'Payments & ledgers', link: '/guide/accounts' },
          ],
        },
        {
          text: 'More modules',
          items: [
            { text: 'Pricing, discounts & offers', link: '/guide/discounts' },
            { text: 'GST & compliance', link: '/guide/gst' },
            { text: 'Incentives & loyalty', link: '/guide/incentives' },
            { text: 'HRMS & attendance', link: '/guide/hrms' },
            { text: 'Reports', link: '/guide/reports' },
          ],
        },
        {
          text: 'Administration',
          items: [
            { text: 'Users, access & settings', link: '/guide/admin' },
            { text: 'Printing', link: '/guide/printing' },
          ],
        },
      ],
    },
    search: { provider: 'local' },
    outline: [2, 3],
    footer: {
      message: 'SSPL Billing — built on Frappe / ERPNext v16',
      copyright: `© ${new Date().getFullYear()} Sundaram and Sons Private Ltd.`,
    },
  },
})
