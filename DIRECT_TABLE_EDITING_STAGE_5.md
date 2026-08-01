# Stage 5 — Direct Table Editing and Complete AED Forms

## What changed

AED Master Data now supports direct cell editing without returning to unsafe whole-table CSV writes.

```text
Browse / filter
→ Edit Current Results
→ edit one or more cells
→ Review Changes
→ Confirm Save to Excel
→ one protected Excel transaction
```

The edit session freezes the selected rows and temporarily pauses filters and automatic Excel refresh. `Serial Number` cannot be edited and rows cannot be inserted or deleted from the table editor.

## Fields editable in the main table

- Model / Related Object
- Block / Locations
- Street Name
- Postal Code
- Level
- Lift Lobby
- Adult Pads Expiry Date and Lot Number
- Pediatric Pads Expiry Date and Lot Number
- Battery Expiry Date
- PM Completed Date and Next PM Date
- Job Type
- Last Done By
- Service Report / e-SR
- Repaired?

## Full Details form

`Edit Full Details` adds fields that are unsuitable for a wide table:

- Installation Date
- Installed Phase / Month
- PO Number
- Zone
- Adult and Pediatric Pads Replacement Dates
- Battery Replacement History
- Remarks

Saving Remarks consolidates any legacy blank-Serial continuation text into the main AED row. The blank continuation rows remain in the workbook, but their old Remarks cells are cleared so the website does not duplicate the text.

## Complete Add AED form

Add AED now includes Basic Information, Adult Pads, Pediatric Pads, Battery, PM and Service, and Remarks. Required fields are:

- Serial Number
- Model / Related Object
- Block / Locations
- Street Name
- Postal Code
- Next PM Date

Location, coordinates, audit identity and operation identifiers remain system-controlled.

## Safety rules retained

- One shared Excel operation lock
- Field-level conflict detection
- Any conflict stops the whole table-edit batch
- Only changed cells are written
- Temporary workbook and hidden staging sheet
- Two workbook validation passes
- Excel backup before replacement
- `os.replace()` atomic replacement
- Excel → website resynchronisation after success
- Transaction, field audit and conflict history
- Postal Code changes clear stale coordinates

## Browser acceptance test

1. Filter to two or three AEDs.
2. Select **Edit Current Results**.
3. Change several cells across two AEDs.
4. Select **Review Changes** and verify every old/new value.
5. Select **Confirm Save to Excel**.
6. Verify Excel, the website table and audit history show the same values.
7. Repeat with two browser windows changing the same field to confirm the second save is blocked.
8. Open **Edit Full Details** and test one replacement date and Remarks.
9. Add a test AED with the complete Add AED form, then deactivate it.
