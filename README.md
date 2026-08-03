# AED Operations Control Center — Full Rebuild v1

Build ID: `2026-08-03-FULL-REBUILD-v1`

This is a complete, coherent project package. It is not a partial patch. The
user-facing layout keeps the original dark sidebar, light workspace, white
panels, blue primary actions and existing page structure.

## Main pages

- **Operations Control** — boss overview with `Overview / PM / Issues / Unit Profiles` in the original top control row.
- **AED Management** — compact boss view with Unit Profiles placed immediately below the four KPI cards.
- **Master Table** — separate sidebar page retaining fuzzy search, linked filters, direct table editing, review-before-save, conflict protection, Add/Deactivate and audit histories.
- **AED Map** — many marker colours, editable status definitions and direct planning-colour auto-save.
- **PM Planning**
- **PM Checklist**
- **Report Issue**
- **Issues / Resolution / Verification**
- **Service Records**

## Unit Profile

Select an AED by Serial Number, model, location or postal code. The profile
opens in the same page with:

- Overview of all original IB List fields
- Direct Edit Details with Before/After review and confirmation
- Combined Service History
- Add Service with review and confirmation
- Issue History
- Quick links to PM Checklist, Report Issue and Master Table

## OneDrive design

Two separate files are used:

1. `/AED System/IB_list_TEST.xlsx` — official IB List fields.
2. `/AED System/AED_System_State.zip` — system-only colours, issues, PM records,
   histories and photos.

This keeps planning colours and workflow data out of the official Excel sheet
while making them persistent in browser-only Streamlit deployment.

The application automatically checks OneDrive every 10 seconds while the page
session is active. Excel changes are downloaded automatically; local system
record changes are uploaded automatically. A manual **Refresh now** button is
kept only as a recovery tool.

## Service Type order

The original `PM` and `Commissioning` positions are preserved. The final three
options are:

- `PM+batt`
- `PM+glass`
- `PM +batt +glass`

## Install

No new project dependency was added. The existing packages remain:

- Streamlit
- pandas
- openpyxl
- requests
- folium
- streamlit-folium

## Validation

- Python compile check: passed
- Automated tests: 83 passed
- Runtime source contains no `Asset readiness` label
- Deprecated `use_container_width` arguments removed

See `REQUIREMENTS_MATRIX.md` and `FULL_REBUILD_DEPLOY.md`.
