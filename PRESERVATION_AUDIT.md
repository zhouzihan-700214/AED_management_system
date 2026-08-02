# Preservation Audit

This build was compared directly with the original
`Stage5_Direct_Table_Editing` ZIP and with the first integrated update.

## Problems found and corrected

1. The original Master Table had been renamed and absorbed into AED Management.
   It is now restored as an independent **Master Table** sidebar page.
2. The boss overview remains a separate **AED Management** page and no longer
   contains or replaces the complete editing workspace.
3. Dashboard master-record and Add/Edit actions now open the dedicated Master
   Table page.
4. The old `AED Master Data` route remains as a hidden compatibility alias so
   old sessions or links do not break.
5. Existing Service Type wording and ordering are preserved, with the three
   combined PM choices appended at the end.
6. Existing map status IDs, names and colours are preserved. New workflow roles
   use new IDs rather than overwriting the user's definitions.

## Sidebar functions present

- Operations Control
- PM Planning
- PM Checklist
- Report Issue
- Issues
- AED Management
- Master Table
- AED Map
- Service Records

## Master Table functions preserved

- Complete Master Table
- Keyword search and linked filters
- Reset Filters clearing results and filter selections
- Direct multi-cell table editing
- Difference review before save
- Conflict detection and safe Excel transaction
- Full AED details editing
- Add AED and Deactivate AED
- Audit/change, conflict, transaction and Excel write history

## Other original functions preserved

- Operations Dashboard
- PM Planning
- PM Checklist
- Report Issue
- Issue assignment, resolution and verification
- Service Records
- AED Map and Manage Statuses
- Data Source and manual refresh controls
- Operator Identity
- Map-to-PM and Map-to-Report-Issue navigation

## Automated audit results

- Missing original files: 0
- Removed original Python functions/classes: 0
- Original Excel workbook changed: No
- Original AED/PM/Issue/history data changed: No
- Original status rows preserved: Yes
- New statuses appended rather than replacing existing rows: Yes
- Expanded marker colours available: 15
- Automated tests passed: 60
- New runtime dependencies: 0
