# Stage 4 — Multi-user Excel Bidirectional Control

This build upgrades the Stage 3 single-instance write-back workflow into a conflict-aware, auditable workflow suitable for a small internal team with low-to-medium update frequency.

## Implemented architecture

```text
External Excel edits
    -> unified Excel operation lock
    -> stable snapshot (signature before/after copy)
    -> validation
    -> aed_data.csv mirror

Website edits
    -> original page snapshot
    -> unified Excel operation lock
    -> latest Excel row re-read
    -> field-level conflict check
    -> temporary workbook + hidden staging sheet
    -> validation + backup + os.replace
    -> Excel-to-website refresh without reacquiring the same lock
    -> transaction/audit history
```

## Unified operation lock

All active refreshes and writes use:

```text
data/excel_operation.lock
```

The lock records operation ID, operation type, user, session ID, affected serial numbers, hostname, PID, and start time. Atomic creation uses `O_CREAT | O_EXCL`. A lock from the same host whose PID no longer exists can be identified as confirmed stale and removed from the Data Source panel.

## Conflict behavior

For every field the service compares:

```text
value when the form opened
current value in Excel
user's desired value
```

Results:

- Current equals opened: safe to apply.
- Current equals desired: already applied; no rewrite needed.
- Current differs from both: conflict; the whole single-unit save stops.

Batch PM updates are all-or-nothing. One conflict stops the full batch.

## Transaction and recovery files

```text
data/active_transaction.json
data/transaction_history.csv
data/audit_history.csv
data/conflict_history.csv
```

The active journal records the last completed step. If Excel was replaced but the cache refresh did not finish, startup recovery refreshes the website mirror without writing Excel a second time. If failure occurred before replacement, the temporary workbook is removed and the official workbook remains unchanged.

## AED Management

Supported:

- conflict-aware single-unit editing;
- Block / Locations;
- Street Name;
- Postal Code;
- Next PM Date;
- safe append of a new AED;
- deactivation without deleting the Excel row;
- transaction, field and conflict history display.

The user selects an audit identity from `AUDIT_USERS` in `config.py`. This is audit identification, not authentication.

## Add AED

A new AED is appended after the last meaningful data row. The service:

1. obtains the unified lock;
2. checks Serial Number uniqueness again inside the lock;
3. copies style and row height from the latest normal AED row;
4. writes mapped fields;
5. validates the temporary workbook;
6. removes the staging sheet;
7. backs up and replaces Excel;
8. refreshes the website mirror.

## Deactivate AED

The supplied IB List has no lifecycle columns. Therefore deactivation is stored in:

```text
data/aed_lifecycle_history.csv
```

The Excel row and all PM/Issue history remain intact. Active operational pages hide the latest `Inactive` record by default.

## PM Planning

The page now includes **Batch Update Next PM Date**. Selected rows are updated in one Excel transaction. Successful rescheduling records use the same Operation ID in `pm_plan_records.csv`.

## PM Checklist

For non-loaner units:

1. validate the checklist;
2. update Excel through the Stage 4 transaction service;
3. refresh the website mirror;
4. only then save `pm_responses.csv`;
5. store Operation ID, Submission Status, Excel Update Status and Submitted By.

If Excel update fails or conflicts, the PM response is not marked committed.

## Main configuration

Edit `config.py` before team use:

```python
AUDIT_USERS = ("Zihan", "Supervisor", "Technician 1", "Technician 2")
LOCK_WARNING_MINUTES = 5
LOCK_STALE_MINUTES = 15
```

Replace placeholder user names with the real approved staff list.

## Browser acceptance tests

1. Two browsers edit different AEDs: both should succeed sequentially.
2. Two browsers edit different fields on the same AED: both should succeed.
3. Two browsers edit the same field differently: the later save must show a conflict table.
4. Two browsers target the same final value: the later save should report already applied.
5. Save in one browser while Refresh is clicked in another: Refresh should wait/fail safely rather than read a write in progress.
6. Batch PM update with one conflict: no selected unit should change.
7. Add the same Serial Number from two sessions: only the first should succeed.
8. Deactivate a unit: its Excel row remains and it disappears from active pages.
9. Confirm no final workbook contains `__STAGING_UPDATE__`.
10. Confirm backups appear in `backups/excel/` after writes.

## Deployment boundary

This design is appropriate for a small number of users and low-to-medium write frequency on one Streamlit server instance accessing one shared workbook. For higher concurrency, MySQL or another transactional database should become the official source, with Excel limited to import, export and reporting.
