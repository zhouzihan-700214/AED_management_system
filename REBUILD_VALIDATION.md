# Rebuild Validation

Validation date: 2026-08-04

## Source reconstruction

- Production Python files compared with the supplied project: 58
- Byte-identical production Python files: 0
- New application-shell Python modules: 8
- Original data, photos, workbook and business records were retained without rewriting their contents.

## Automated verification

```text
python -m compileall -q .   PASSED
pytest -q                    138 PASSED
```

In addition, an isolated destructive-write simulation completed 110/110 checks and independently inspected the resulting workbook column placement.

The test suite covers Excel synchronization and safe writeback, locks, conflicts, recovery, audit histories, PM planning/checklist workflows, issue resolution and verification, Unit Profiles, dashboard queues, map status rules, OneDrive state separation, responsive profile behavior and Service Records scopes.

## Runtime entry

- `streamlit_app.py` is the only executable Streamlit entrypoint.
- No `app.py` exists.
- Configuration compatibility is applied before runtime business modules load.
- Cloud downloads are deferred while write workspaces are active.

## Visual preservation

The complete shared CSS selector set and responsive rules are retained, but are emitted through a newly composed style module. Navigation groups, page names, hero sections, profile layouts and record scopes remain compatible with the validated UI contract.

## Environment limitation during this rebuild

The package index available to the container did not provide the required Streamlit runtime version, so a live browser render was not launched here. Compilation and all 137 repository tests passed; deployment should still be smoke-tested in the user's normal Streamlit environment with the actual Microsoft account and secrets.
