# SSPL Billing — product website

Marketing + user-guide site built with [VitePress](https://vitepress.dev). Separate from the
`frontend/` app; it has its own `package.json` and does not touch Frappe.

## Where to edit

| What | File |
|---|---|
| Plan rates / extras (**placeholders — set real prices**) | `.vitepress/data/plans.js` |
| Landing page | `index.md` |
| Pricing page | `pricing.md` |
| Contact details (**placeholders**) | `contact.md` |
| User guide | `guide/*.md` |
| Nav / sidebar | `.vitepress/config.mjs` |
| Module list | read live from `../licensing_features_by_category.json` |

## Commands

```bash
npm install
npm run dev       # dev server on 0.0.0.0:5175, hot reload
npm run build     # static site → .vitepress/dist/
npm run preview   # serve the built site on :5176
```

Serving under a sub-path (e.g. `https://erp.example.com/site/`): build with
`SITE_BASE=/site/ npm run build` (or start dev with the same variable).

## nginx

### Dev mode (proxy to the VitePress dev server)

Keep `npm run dev` running (e.g. in tmux or a systemd unit), then:

```nginx
server {
    listen 80;
    server_name billing.example.com;

    location / {
        proxy_pass http://127.0.0.1:5175;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header Upgrade $http_upgrade;     # hot-reload websocket
        proxy_set_header Connection "upgrade";
    }
}
```

### Production (static files, no Node process)

```nginx
server {
    listen 80;
    server_name billing.example.com;

    root /home/erpdev/frappe/frappe-bench-v16/apps/ssplbilling/website/.vitepress/dist;
    index index.html;

    location / {
        try_files $uri $uri.html $uri/ =404;
    }

    location /assets/ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    error_page 404 /404.html;
}
```

nginx's user (often `www-data`) needs read + execute on every directory in that path.
Reload with `sudo nginx -t && sudo systemctl reload nginx`.
