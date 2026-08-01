# Stage 3: Safe Website → Excel Write-back

## Scope

This build writes changes from **AED Master Data** to the supplied `external_data/IB_list_TEST.xlsx`, then rebuilds `aed_data.csv` through the existing Stage 2 synchronizer.

Only one existing AED can be changed per save. The first enabled fields are:

```text
Block / Locations
Street Name
Postal Code
Next PM Date
```

The following remain read-only:

```text
Serial Number
Location (generated from Block + Street)
Remarks (contains continuation rows in the source workbook)
Latitude / Longitude / OneMap fields
```

Add AED and Delete AED are intentionally disabled in this build.

## Save flow

```text
AED Management form
→ aed_repository.update_unit()
→ acquire data/excel_write.lock
→ copy official workbook beside the source file
→ locate Sheet1 row by SERIAL NUMBER
→ create hidden __STAGING_UPDATE__ sheet
→ apply only supported target cells
→ save and reopen: validate structure + target values
→ remove staging sheet
→ save and reopen: validate again
→ back up the previous workbook to backups/excel/
→ os.replace temporary workbook over official workbook
→ run Excel → aed_data.csv synchronization
→ append data/excel_write_history.csv
→ rerun the page
```

The official workbook is never edited in place. Column numbers and row numbers are not hard-coded: headers are scanned from row 1 and the AED row is located by Serial Number from row 3 onward.

## Workbook protections

Validation confirms that:

- `Sheet1` still exists;
- original worksheets remain present and in the same order;
- first and second header rows remain unchanged;
- worksheet row and column counts remain unchanged;
- merged ranges remain unchanged;
- Serial Number rows remain unchanged;
- Remarks continuation rows remain unchanged;
- requested target cells contain the new values;
- `__STAGING_UPDATE__` is removed before replacement.

Every successful replacement creates a timestamped pre-change backup in `backups/excel/`. The newest 20 are retained.

## Data types

- Postal Code is written as a six-digit text value with Excel format `@`.
- Next PM Date is written as a true Excel date with format `dd/mm/yyyy`.
- Blank text values are written as empty cells.

After a Postal Code change, the Stage 2 synchronizer clears the old coordinates and sets geocoding to pending, preventing the map from retaining the old location.

## Audit history

Successful and failed attempts are recorded in:

```text
data/excel_write_history.csv
```

Each changed field records timestamp, user, source page, Serial Number, old value, new value, result, and message.

## Browser test

1. Start the project with `python -m streamlit run app.py`.
2. Open **AED Master Data**.
3. Filter or select `X18K075125`.
4. Enter a name in **Changed By**.
5. Change `Next PM Date` to a deliberate test date and save.
6. Confirm the value changed in Excel column `Next PM Due`.
7. Confirm the page reruns with the same new date.
8. Confirm a file appears in `backups/excel/`.
9. Confirm `data/excel_write_history.csv` contains the field change.
10. Confirm `__STAGING_UPDATE__` is not present in the official workbook.

Repeat with Block / Street and confirm generated `Location` changes after synchronization. Repeat with Postal Code and confirm old coordinates are removed before OneMap refresh.

## Stage boundary

This version is designed for one formal Streamlit instance and prevents simultaneous website write operations with an atomic lock file. It does not yet reject an update merely because an external user changed the same field after the page was opened. Original values are already passed into the service so Stage 4 can add field-level conflict detection without changing the page-service interface.
