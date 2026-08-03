# Requirements Matrix

## Layout and navigation

- Original visual style retained.
- Original top control row retained.
- AED Management is boss-focused and not overloaded.
- Master Table is an independent sidebar page.
- No Data Service/Data Quality card is placed in the main boss layout.
- `Asset readiness` is removed from runtime UI and replaced by `Unit Profiles`.

## Master Table

- Partial-text search across Serial, model, location and postal code.
- Linked filters.
- Reset clears both results and selected filter values.
- Direct cell editing.
- Before/After review.
- Confirmation before Excel write.
- Conflict protection, locks, backup and audit history.
- Add AED and Deactivate AED preserved.

## Unit Profile

- Direct selector on Operations Control and AED Management.
- All original unit information.
- Direct editing with review and confirmation.
- Service History combining PM, resolution, current IB List and Remarks.
- Direct Add Service with review and confirmation.
- Issue History.
- Quick actions for PM, Issue and Master Table.

## Service Type

- Existing PM and Commissioning positions unchanged.
- `PM+batt`, `PM+glass`, `PM +batt +glass` at the end.
- PM Checklist updates the official Service Type field.

## Colours and map

- 15 available marker colours.
- Status names, definitions, workflow roles and colours remain editable.
- Planning colour is changed directly and auto-saved; no Save/Confirm step.
- Planning colour stays outside the official IB List.
- Open Issue controls red; pending verification controls yellow; fully closed
  unit returns to green only when no unresolved issue remains.

## Confirmed workflows

- PM Checklist: confirmation before formal submit.
- Failed PM items: individual issue candidates.
- Report Issue: confirmation before creation.
- Submit Resolution: confirmation.
- Verify/Close: confirmation and remaining-issue check.
- Ordinary formal field changes: review before Excel save.

## OneDrive

- Browser-only Microsoft sign-in.
- Official workbook download and upload through Graph.
- ETag conflict detection.
- Automatic 10-second workbook refresh.
- Separate OneDrive state archive for system-only data.
- Existing OneMap support retained.
- Local workbook fallback retained.
