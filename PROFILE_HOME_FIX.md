# AED Unit Profile homepage fix

This version is based directly on the uploaded GitHub repository state.

## What was wrong

The editable profile code already existed, but it was easy to miss:

- On **AED Management**, the profile workspace appeared below Attention Required and PM Progress.
- On **Operations Control**, the former Asset Readiness area only showed an entry button, not a direct AED selector.

This made a successful code update look unchanged during normal use.

## What changed

### AED Management

The AED Unit Profiles workspace now appears immediately after the four management KPI cards.

- Searchable AED selector (type serial, model, location or postal code)
- Selected AED opens inline without leaving the page
- Overview, Edit Details, Service History, Add Service and Issues remain available
- Attention Required and PM Progress remain below the profile workspace
- Master Table remains an independent sidebar page

### Operations Control

The former Asset Readiness summary position now contains a direct AED profile selector.

- Select one AED inside the card
- Open the selected profile directly
- Or browse all unit profiles

## Preserved

OneDrive two-way sync, automatic OneDrive checking, OneMap, map colours, PM, Issues, Service Records, Master Table and all existing data files are preserved.

## Validation

- Python compile check passed
- 65 pytest tests passed
