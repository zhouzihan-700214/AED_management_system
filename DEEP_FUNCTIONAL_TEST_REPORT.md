# Deep Functional Write-Back Test Report

Test date: 2026-08-04

## Result

- Repository test suite: **138 passed**
- Isolated end-to-end write checks: **110 passed, 0 failed**
- Python compilation: **passed**
- Raw Excel inspection after writes: **passed**

The end-to-end test was executed on a complete isolated copy of the project, so the supplied production CSV and Excel data in this package were not polluted by test records.

## What was actually written and verified

### Master Table / Full Details / Unit Profile field editing

An existing AED was updated through the protected Excel transaction gateway. The following fields were filled with unique test values and checked after Excel-to-cache synchronization:

- Installation Date
- Model / Related Object
- Installed Phase / Month
- PO Number
- Zone
- Block / Locations
- Street Name
- Postal Code, including a leading-zero value
- Level
- Lift Lobby
- Adult pads replacement date, expiry date and lot number
- Pediatric pads replacement date, expiry date and lot number
- Battery replacement history and expiry date
- PM completed date and next PM date
- Job Type
- Last Done By
- Service Report / e-SR
- Repaired?
- Remarks

The derived `Location` field was also recalculated from Block and Street Name. A raw workbook inspection confirmed the values were written into the correct official IB List columns, rather than only appearing correctly in `aed_data.csv`.

### Conflict and transaction safety

- A stale page value was deliberately submitted and correctly returned a conflict.
- The newer Excel value was not overwritten.
- Excel backups were created.
- Field audit and transaction history rows were written with the correct serial number and operation type.
- A two-unit Next PM Date batch update committed atomically and both correct units changed.

### Add and deactivate AED

- A new AED was created with all available Add AED fields.
- Every entered value appeared in the Excel-generated cache under the correct field.
- Postal code leading zeros were preserved.
- Deactivation hid the unit from normal active views while preserving its Excel row and full data.
- The lifecycle history recorded the correct serial and `Inactive` status.

### PM Planning and PM Checklist

- A monthly PM plan was created for the selected AED.
- Duplicate creation for the same Plan ID and serial was prevented.
- The actual PM Checklist commit helper was called with reviewed form values.
- PM master fields were written to the selected AED only.
- Service Type `PM+batt` mapped to the official Job Type field.
- Battery replacement history was appended once.
- The PM response was saved once and remained idempotent on retry.
- The matching monthly plan was marked Completed and linked to the PM Response ID.
- A failed checklist field created one linked Issue with the correct PM Response ID, source field and source value.

### Report Issue, resolution and verification

- A Report Issue submission wrote the correct issue fields.
- Report evidence metadata and the physical photo file were both saved.
- Assignment, start work and progress updates were retained in Issue history.
- Resolution attempt 1 was submitted with test details and evidence.
- Rejection changed the Issue to Reopened.
- Resolution attempt 2 was retained separately and approved.
- Approval closed the Issue.
- Both resolution attempts and their verification results remained available.
- Marker state changed through Issue → Pending Verification → Completed.
- Every attachment path in the metadata resolved to an existing file.

### Unit Profile Add Service and Service Records

- A completed Unit Profile service updated only the intended latest-service fields.
- The durable manual service record was written with its operation link.
- A pending service was blocked from updating completed master fields.
- Service Records included the PM Checklist record, Unit Profile service record and both Issue resolution attempts.
- Resolution evidence counts and links were retained.
- All Records / Matched / Mismatch / Loaner scope counts reconciled.
- The Unit Profile combined service history included the manual service record.

## Defect found and fixed

A real write-blocking defect was found during the first deep run:

- The Excel cell for `Battery Replacement History` can be stored as a real Excel date.
- The website cache displays that value as `DD-MM-YYYY`.
- Conflict checking previously converted the Excel value to a timestamp string such as `2023-01-21 00:00:00`.
- This incorrectly looked like an external edit and could block an otherwise valid Full Details, Master Table or PM save.

The write service now normalizes a single Excel date in `Battery Replacement History` to `DD-MM-YYYY`, while preserving multi-date history text. A regression test was added.

## External limitations

The following require the deployment environment and cannot be proven from this offline container:

- Real browser rendering and manual clicking of Streamlit widgets, because Streamlit 1.51 was unavailable in the test package index.
- Real Microsoft sign-in and OneDrive upload/download against the user's account, because no Microsoft credentials or remote workbook were available.
- Live OneMap network responses.

The local write paths used after form confirmation, the exact PM commit helper, data contracts, import graph and mocked OneDrive conflict/upload behavior are covered by the automated tests.
