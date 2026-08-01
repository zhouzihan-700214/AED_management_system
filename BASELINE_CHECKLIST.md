# AED Operations Control Center — Browser Regression Checklist

Run this checklist after installing `requirements.txt` and starting Streamlit.

## Operations Control

- [ ] Application opens on **Operations Control**, not AED Master Data
- [ ] Dark compact header and light workspace render correctly
- [ ] `Overview`, `PM`, `Issues`, and `Asset readiness` views work
- [ ] Period, assignee, and search filters update the work queue
- [ ] Reset / empty filter states remain usable
- [ ] Selecting one queue row updates the right-hand detail panel
- [ ] PM actions open the correct AED in PM Checklist or PM Planning
- [ ] Issue actions open and focus the correct Issue
- [ ] AED actions open AED Master Data or Report Issue with the correct serial
- [ ] KPI values change appropriately with the selected management view
- [ ] PM progress, Issue pipeline, readiness, activity, and source health load
- [ ] An empty queue shows a useful empty state
- [ ] At approximately 950px width, the two-column layout remains usable
- [ ] At 200% browser zoom, controls and content remain reachable
- [ ] Keyboard focus is visible on interactive controls

## AED Master Data

- [ ] Page opens and AED data loads
- [ ] Keyword Search works
- [ ] Model, Location, Postal Code, Lift Lobby, Job Type and Last Done By filters work
- [ ] Multiple filters remain linked
- [ ] Reset Filters clears every visible selection
- [ ] Date filters and sorting work
- [ ] Table edits save to `aed_data.csv`
- [ ] Editing PM Completed Date recalculates Next PM Date
- [ ] Editing PM Interval Months recalculates Next PM Date
- [ ] PM Interval Months only accepts values from 1 to 60
- [ ] Add AED defaults PM Interval Months to 12
- [ ] Duplicate non-empty Serial Numbers are rejected
- [ ] Delete AED search and confirmation work
- [ ] Audit Log records changes

## AED Map

- [ ] Map and markers load
- [ ] Marker positions, colours, popups and legend display correctly
- [ ] Linked map filters and Reset work
- [ ] Unit Status and marker colour changes save
- [ ] Status Editor can add, rename, disable and recolour statuses
- [ ] Marker/detail navigation opens the correct PM Checklist AED
- [ ] Marker/detail navigation pre-fills Report Issue

## PM Planning

- [ ] Year and month selection work
- [ ] Candidate AEDs are based on Next PM Date
- [ ] Missing Next PM Date uses the temporary shared interval fallback only
- [ ] Monthly plan can be generated and saved
- [ ] Saved plan reloads correctly
- [ ] Planning CSV export works

## PM Checklist

- [ ] Search by Serial Number, Location and Postal Code works
- [ ] Dashboard handoff loads the selected AED
- [ ] Matching AED selection loads master data
- [ ] Checklist can be completed and submitted
- [ ] Submission appends to `pm_responses.csv`
- [ ] Non-loaner submission updates `aed_data.csv`
- [ ] Next PM Date uses the selected AED's PM Interval Months
- [ ] Audit history is recorded
- [ ] Report Issue handoff works

## Service Records

- [ ] PM records load
- [ ] Linked filters and Reset work
- [ ] Record details open
- [ ] CSV export works

## Report Issue and Issues

- [ ] AED search, map pre-fill, and dashboard pre-fill work
- [ ] Issue type, priority, description and photo upload work
- [ ] Issue ID is created
- [ ] Dashboard-selected Issue opens first
- [ ] Assign, Start Work and Progress Update work
- [ ] Resolution submission requires completion evidence
- [ ] Pending Verification appears separately in Operations Control
- [ ] Verify and Close works
- [ ] Reject and Reopen works
- [ ] Issue history and evidence display correctly

## Storage and failure states

- [ ] Header-only PM and Issue CSV files load without error
- [ ] Temporarily missing optional history files show source-health warnings
- [ ] Invalid dates appear as data exceptions rather than crashing the page
- [ ] OneMap credentials are read only from local Streamlit secrets

## Stage 3 website → Excel write-back regression

- [ ] AED Master Data table is read-only and no longer shows **Save Table Changes**.
- [ ] A single AED can be selected below the filtered table.
- [ ] Only Block / Locations, Street Name, Postal Code, and Next PM Date are editable.
- [ ] Serial Number, generated Location, and Remarks are visibly read-only.
- [ ] Changed By is required.
- [ ] Saving a changed value updates `external_data/IB_list_TEST.xlsx`.
- [ ] A pre-change workbook appears in `backups/excel/`.
- [ ] The official workbook does not contain `__STAGING_UPDATE__` after saving.
- [ ] `aed_data.csv` is rebuilt and the page shows the new value after rerun.
- [ ] Block or Street changes regenerate Location.
- [ ] Postal Code changes clear the old coordinates before OneMap refresh.
- [ ] `data/excel_write_history.csv` records each changed field.
- [ ] Clicking Save without changing a value does not modify Excel.
- [ ] Add and Delete show the Stage 3 disabled notice.
