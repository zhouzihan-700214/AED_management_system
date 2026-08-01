# Excel Synchronization — Stage 1

This project now implements the first controlled integration stage:

```text
IB_list_TEST.xlsx
→ validated temporary snapshot
→ aed_data.csv local mirror
→ aed_repository.get_all_units()
→ every main Streamlit page
```

## What changed

- `config.py` now contains all Excel, CSV, temporary, backup and sync-state paths.
- `services/column_mapping.py` maps accepted Excel header aliases to stable app fields.
- `services/excel_sync_service.py` checks the Excel file signature, copies a stable read snapshot, validates it and atomically rebuilds `aed_data.csv`.
- `services/aed_repository.py` is the only master-data read gateway used by pages.
- Dashboard, AED Master Data, Map, PM Planning, PM Checklist, Service Records and Report Issue now obtain AED data through the Repository.
- The sidebar contains **Data Source → Refresh AED Data** and displays sync status.
- `openpyxl` was added to `requirements.txt` for `.xlsx` reading.

## How to use it

1. Put the real workbook at `external_data/IB_list_TEST.xlsx`.
2. Confirm its AED worksheet is named `IB List`.
3. When either name differs, edit only `EXCEL_FILE` or `EXCEL_SHEET` in `config.py`.
4. Run `python -m pip install -r requirements.txt`.
5. Start the app with `python -m streamlit run app.py`.
6. Open **Data Source** in the sidebar and press **Refresh AED Data**.

## Validation rules

The CSV mirror is replaced only when:

- the workbook can be copied without changing during the copy;
- the configured worksheet exists;
- at least one AED row exists;
- every row has a Serial Number;
- Serial Numbers are unique, case-insensitively;
- postal codes and dates can be normalized into the app format.

If validation fails, the existing valid `aed_data.csv` remains unchanged.

## Current boundary

This stage is intentionally **Excel → website only**. Existing website edit, add, delete and Checklist operations still write to `aed_data.csv`. They have not yet been connected to the external workbook.

The next stage should implement website → Excel updates with a lock, latest-version reread, field-level changes, temporary workbook validation, backup and atomic replacement.
