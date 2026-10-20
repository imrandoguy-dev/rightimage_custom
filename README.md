# Right Image Custom

Right Image's own setup, kept on top of the standard `hiper_solar` app.
**For `rightimage.hipersignerp.cloud` only** — installing it on any other site is refused.

## What it holds

| File (`rightimage_custom/data/`) | What |
|---|---|
| `doctype.json` | Order Confirmation, Work Allocation (+ settings and child tables), CRM Lead Document |
| `custom_field.json` | CRM Lead quick/detailed fields, document table, Order Confirmation / Work Allocation links, Solar Package sections, quotation print fields |
| `property_setter.json` | CRM Lead layout, Solar Package labels, default quotation print format |
| `client_script.json` | Lead Quick Enquiry, Document Cards, Quick vs Detailed, Create Menu, Order Confirmation, Work Allocation, Solar Package sections |
| `server_script.json` | Order confirm (lead → customer), Order Confirmation payments, Work Allocation costing and accounting |
| `print_format.json` | Right Image Quotation, Advance Payment Details, Solar Quotation |
| `custom_html_block.json` | Solar Dashboard (Leads card on CRM Lead) |
| `workspace_sidebar.json` | Solar sidebar (Lead → CRM Lead, Order Confirmation, Work Allocation) |

## How it works

After every `bench migrate` (site update, bench change) this app runs after
`hiper_solar` and writes the records above back to the site. Records that
already match are left alone. Anything else from `hiper_solar` still updates
normally.

## Install (rightimage only)

```bash
bench get-app https://github.com/imrandoguy-dev/rightimage_custom
bench --site rightimage.hipersignerp.cloud install-app rightimage_custom
```

On Frappe Press: add the app to the bench, then install it on the rightimage site only.

## Changing Right Image's workflow

Make the change on the site, then save it into the app so the next update keeps it:

```bash
# refresh everything already in the app
bench --site rightimage.hipersignerp.cloud execute rightimage_custom.sync.export_all
# add a new record
bench --site rightimage.hipersignerp.cloud execute rightimage_custom.sync.export_doc \
    --kwargs "{'doctype': 'Client Script', 'name': 'My Script'}"
```

Commit and push the `data/` folder.
