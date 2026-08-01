# Excel Synchronization — Round 2: Real IB List

This version is configured against the uploaded `IB_list_TEST (1)(1).xlsx` and includes a renamed copy at:

```text
external_data/IB_list_TEST.xlsx
```

## Actual workbook structure

```text
Worksheet: Sheet1
Used range: A1:AC16
Main column header: row 1
Auxiliary labels: row 2
Data begins: row 3
Recognised AED records: 12
Unique key: SERIAL NUMBER
```

Excel rows 4 and 6 contain only continuation text in `Remarks`. They are merged into the preceding AED record and do not create blank-Serial units.

## Field conversion

```text
SERIAL NUMBER                    → Serial Number
Block / Locations + Street Name → Location
Level + Lift Lobby               → Lift Lobby
Adult CPR-D Padz                 → Adult Pads Expiry Date
Adult CPR-D Padz Lot Number      → Adult Pads Lot Number
Children Pedi-Padz               → Pediatric Pads Expiry Date
Children Pedi-Padz Lot Number    → Pediatric Pads Lot Number
Battery Replacement History      → Battery Replacement History
Battery Expiry Date              → Battery Expiry Date
PM Completed On                  → PM Completed Date
Next PM Due                      → Next PM Date
JOB TYPE                         → Job Type
Last done by                     → Last Done By
Service Report / e-SR            → Service Report e-SR
Remarks                          → Remarks
```

The Excel source does not contain `Model`, coordinates, OneMap address, geocoding status, or PM interval. For a matching Serial Number, those website-owned values are retained from the previous `aed_data.csv`.

Coordinates are retained only while the Postal Code is unchanged. When Excel changes a Postal Code, stale coordinates are cleared so the existing OneMap update workflow can obtain the new location.

## Refresh flow

```text
Detect Excel version
→ acquire short refresh lock
→ copy a stable temporary snapshot
→ read Sheet1
→ skip auxiliary header row
→ merge Remarks continuation rows
→ map and validate fields
→ merge website-only values by Serial Number
→ back up previous aed_data.csv
→ atomically replace aed_data.csv
→ save sync status
```

## Test result for the included workbook

```text
Imported units: 12
Continuation rows merged: 2
Existing coordinate sets retained: 9
New units without previous coordinates: 3
Duplicate Serial Numbers: 0
Blank parsed Serial Numbers: 0
```

The source workbook currently contains several date-formatted values that resolve to years 1930, 1934, or 1935. The system imports them unchanged and displays a warning. Review those source cells rather than correcting them silently in the website mirror.

## Run

```powershell
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

Open the sidebar and expand **Data Source**. Use **Refresh AED Data** after saving Excel changes.

## Boundary of this round

This version implements Excel → website only. Website edits, Add/Delete Unit, PM Planning changes, and Checklist submissions still write to the CSV mirror. They do not yet update Excel. The next round will add safe website → Excel writes, workbook backups, version conflict checks, and multi-user write locking.
