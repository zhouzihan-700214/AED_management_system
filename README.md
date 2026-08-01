# AED Preventive Maintenance & Issue Management System

A Streamlit application for AED master-data control, preventive-maintenance planning and execution, Issue resolution, map readiness, consumable monitoring, and operational history.

Version 3 replaces the former navigation-card home page with **AED Operations Control Center**: a management workspace centred on priority work, current responsibility, progress, exceptions, and direct action.

## 1. Run the project

Open the extracted folder that directly contains:

```text
app.py
config.py
views/
services/
ui/
```

Windows PowerShell:

```powershell
python -m venv .venv
.venv\Scripts\activate
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

macOS or Linux:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

## 2. Excel master-data synchronization

Version 3 now has one shared AED read path:

```text
external_data/IB_list_TEST.xlsx (formal external master)
→ services/excel_sync_service.py
→ aed_data.csv (validated local mirror)
→ services/aed_repository.py
→ Dashboard / Master Data / Map / PM Planning / Checklist / Records / Issue
```

The supplied test workbook is already included and configured as:

```text
File: external_data/IB_list_TEST.xlsx
Worksheet: Sheet1
Range: A1:AC16
Main header: row 1
Auxiliary header: row 2
AED records: 12
```

Start the site and open **Data Source → Refresh AED Data** in the sidebar. The synchronizer understands the real two-row workbook structure, merges blank-Serial Remarks continuation rows, builds `Location` from Block and Street, keeps `Level` separate and formats the lobby value for display, preserves existing coordinates by Serial Number, and retains text histories containing multiple dates.

The synchronizer reads a stable temporary workbook snapshot, validates required columns and Serial Number uniqueness, creates a backup of the previous CSV mirror, and atomically replaces only `aed_data.csv`. Invalid Excel data never overwrites the last valid mirror. Dates outside 2000–2100 are imported but shown as warnings so the source cells can be reviewed.

When the workbook is absent, the application starts in **CSV fallback** mode. The current build adds controlled multi-user website → Excel updates through the same repository and transaction layer.

AED Master Data now has three safe editing paths:

```text
Browse and filter
→ Edit Current Results
→ modify several table cells
→ Review Changes
→ Confirm Save to Excel
```

```text
Edit Full Details
→ update fields that are too wide for the main table
→ save one AED through field-level conflict checks
```

```text
Add AED
→ enter a complete business record
→ validate required fields and Serial Number uniqueness
→ append one styled Excel row
```

The table editor never saves after each cell click and never overwrites Excel with a whole DataFrame. It sends only changed cells, grouped by Serial Number, into one protected Excel transaction. Serial Number and system-computed fields remain read-only. Filters and automatic refresh are paused during an edit session so unsaved changes are not discarded.

All write operations use the shared Excel operation lock, temporary workbook, hidden staging sheet, field-level conflict detection, two validation passes, automatic backup, atomic replacement, cache refresh, transaction journal and audit history. See `DIRECT_TABLE_EDITING_STAGE_5.md` for the user workflow and validation checklist.

## 3. OneMap configuration

The project does not include real OneMap credentials.

1. Copy `.streamlit/secrets.toml.example`.
2. Rename the copy to `.streamlit/secrets.toml`.
3. Enter your own `ONEMAP_EMAIL` and `ONEMAP_PASSWORD`.

Never commit or share `.streamlit/secrets.toml`.

## 4. Operations Control Center

The default page is no longer the editable AED table. It now answers the management questions that matter first:

- Which PM tasks are overdue or due soon?
- Which Issues require follow-up or verification?
- Which work has no assignee?
- Which pads or batteries are approaching expiry?
- Which master-data records are incomplete or implausible?
- What can the user do next from the selected item?

The main layout is:

```text
Compact dark control header
→ View / period / assignee / search toolbar
→ Context-sensitive management KPIs
→ Priority Work Queue + Selected Item panel
→ PM progress / Issue pipeline / Asset readiness
→ Recent activity / Data-source health
→ Compact quick actions
```

Available dashboard views:

```text
Overview | PM | Issues | Asset readiness
```

## 5. Navigation

```text
OVERVIEW
  Operations Control

WORK MANAGEMENT
  PM Planning
  PM Checklist
  Report Issue
  Issues

ASSET CONTROL
  AED Master Data
  AED Map

RECORDS
  Service Records
```

The existing session-state router is retained so map popups and context actions continue to open the correct workflow and selected record.

## 6. Visual system

The application uses a restrained enterprise control-centre style:

```text
Dark navy navigation and control frame
+
Light high-density workspace
+
White tables, forms and detail surfaces
+
Semantic danger / warning / success / information states
```

The redesign removes the large decorative dashboard Hero, floating ornaments, card wall, and duplicated module links. Work queues and decision context now have priority over decoration.

## 7. Main code structure

```text
app.py                              Application setup, storage initialization and dispatch
config.py                           Central Excel, CSV, sync-state and asset paths
services/aed_repository.py         Single AED read/write gateway used by pages
services/excel_sync_service.py      Excel snapshot, validation and CSV mirror refresh
services/excel_write_service.py     Workbook cell mapping and validation helpers
services/excel_transaction_service.py Unified lock, conflicts, transactions, batch/add/deactivate
services/excel_lock_service.py        Atomic shared operation lock and stale-lock inspection
services/conflict_service.py          Field-level optimistic concurrency checks
services/audit_service.py             Transaction, field and conflict audit records
services/recovery_service.py          Startup cleanup and post-replacement cache recovery
services/column_mapping.py          External workbook header aliases
services/dashboard_service.py      Dashboard sources, queues, KPIs, summaries and activity
services/pm_service.py              PM schema, interval rule, checklist submission and history
services/issue_service.py           Issue schema, transitions and resolution storage
services/aed_service.py             AED master-data validation, editing and persistence
ui/dashboard_components.py         Control Center UI components and contextual actions
ui/styles.py                        Shared design tokens and responsive CSS
ui/navigation.py                    Grouped sidebar and routing
views/dashboard.py                  Thin Operations Control page composition
views/registry.py                   Page renderer registry
views/                              Business workspaces
views/map_modules/                  Map filters, rendering, state and detail panel
utils/                              Shared text, date and Streamlit helpers
tests/                              Automated service and dashboard tests
```

## 8. PM date rule

`Next PM Date` is the shared operational source used by the dashboard and PM Planning.

Each AED now supports:

```text
PM Completed Date
+
PM Interval Months
=
Next PM Date
```

`PM Interval Months` defaults to `12` and can be edited in AED Master Data. A submitted PM checklist recalculates `Next PM Date` using that unit's interval. This removes the former conflict between six-month planning logic and twelve-month checklist logic.

## 9. Storage initialization

At startup the application verifies and initializes the schemas for:

- PM responses;
- PM plan records;
- AED management history;
- Issue records and history;
- Issue-resolution submissions.

Zero-byte or BOM-only files are converted into valid header-only CSV files instead of failing later during a workflow.

## 10. Tests

Install the development dependencies and run:

```powershell
python -m pip install -r requirements-dev.txt
pytest -q
```

The tests use temporary directories and do not modify the production CSV files.

Use `BASELINE_CHECKLIST.md` for browser regression checks after starting Streamlit.

## 11. Data safety

Stage 4 uses one atomic `data/excel_operation.lock` for refresh, single-unit updates, batch updates, additions, deactivation records and recovery. It preserves the page-opened field snapshot, re-reads the latest Excel row after acquiring the lock, and stops same-field conflicts while allowing different fields to merge safely.

Every write uses a temporary workbook, hidden staging sheet, validation passes, timestamped backup and atomic same-filesystem replacement. Active transaction journals allow startup recovery when Excel replacement succeeds but cache refresh does not. Audit records are stored in `data/transaction_history.csv`, `data/audit_history.csv` and `data/conflict_history.csv`.

See `EXCEL_MULTI_USER_STAGE_4.md` for deployment boundaries and browser acceptance tests. A transactional database remains preferable when users or write frequency increase.
