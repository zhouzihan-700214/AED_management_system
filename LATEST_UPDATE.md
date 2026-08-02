# Latest integrated update — separate Master Table restored

This build keeps the original navigation style, spacing, blue/white visual
language and page switching. It adds the confirmed August 2026 requirements
without adding a new Python dependency.

## Sidebar structure

The Master Table is restored as a complete, independent sidebar function. It is
not hidden inside the boss page and is not reduced to a homepage control.

Under **ASSET CONTROL**, the sidebar now contains:

- **AED Management** — compact boss overview only
- **Master Table** — complete original master-data workspace
- **AED Map** — map, marker interaction and Manage Statuses

The former internal route `AED Master Data` is retained as a hidden compatibility
alias so older sessions and links still open the Master Table.

## AED Management

The AED Management page is deliberately compact and aimed at management:

- total AED units
- PM outstanding
- open Issues
- pending verification
- attention-required records
- current-month PM progress
- a short searchable AED quick view

It does not contain the full editing workspace and does not add a Data
Quality/Data Service section.

## Master Table

The dedicated Master Table page retains the original functions:

- keyword search and linked filters
- complete filter reset
- direct multi-cell table editing
- difference review before save
- conflict detection and safe Excel transaction
- full AED details editing
- Add AED and Deactivate AED
- audit, conflict, transaction and Excel write history

Dashboard actions such as **Add / edit AED** and **Open AED master record** now
open this dedicated page.

## PM, Issues and marker colours

- PM Checklist, Report Issue, Resolution Submission and Resolution Verification
  use review/confirmation before formal records are committed.
- Failed PM checklist items can create traceable Issue records.
- Issue workflow controls operational marker status:
  Issue -> Pending Verification -> Completed only when no unresolved Issue remains.
- Planning/custom marker colours save immediately, without a Save button or
  confirmation, and remain system-only rather than being written into the company
  Excel workbook.
- Marker palette includes Blue, Green, Red, Orange, Yellow, Purple, Gray, Pink,
  Teal, Cyan, Indigo, Lime, Brown, Maroon and Black.
- Existing custom status definitions are preserved. `Pending Verification` and
  `Out of Service` are appended with new IDs rather than replacing existing rows.
- Status names, colours and workflow definitions remain editable in Manage Statuses.

## Service Type

The existing `PM` and `Commissioning` positions are retained. These choices are
appended at the end of every relevant Service Type list:

- `PM+batt`
- `PM+glass`
- `PM +batt +glass`

Confirmed PM submission updates the master Excel `Job Type` field, shown in the
website as `Service Type`.

## OneDrive

The system can use `IB_list_TEST.xlsx` from the user's own synchronized OneDrive
folder. See `ONEDRIVE_SETUP.md` and `.streamlit/secrets.toml.example`.

## Verification

- Python compile check passed.
- 60 automated tests passed.
- All original project files remain present.
- No original Python function or class was removed.
- The original Excel workbook and operational CSV records were not modified.
- Original operational pages remain available.
- `requirements.txt` and `requirements-dev.txt` are unchanged; no new pip package
  is required.

## Browser-only OneDrive Excel — latest update

The same project now supports direct two-way synchronization with the personal
OneDrive workbook configured in Streamlit Secrets:

- Microsoft sign-in is shown before operational pages load.
- `Refresh AED Data` downloads `/AED System/IB_list_TEST.xlsx` through Microsoft Graph.
- Confirmed Master Table, PM and planning changes update the private working copy
  and upload it back to the same OneDrive drive item.
- OneDrive eTag comparison stops a save when the browser workbook changed after
  the website loaded it.
- A failed cloud upload is preserved in `backups/onedrive_pending` and the site
  reloads the official remote workbook instead of silently overwriting it.
- The existing project-local Excel mode remains available when `[microsoft]`
  Secrets are absent.
- No new runtime package was added; the integration uses the existing `requests`
  dependency.
- Streamlit Community Cloud can continue using `streamlit_app.py` as its entry point.
- 65 automated tests pass, including OneDrive path, download, upload and conflict tests.
