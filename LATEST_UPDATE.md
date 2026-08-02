# Latest integrated update

This build keeps the original navigation, spacing, blue/white visual language and
page switching. It adds the requirements confirmed in the August 2026 design
conversation without adding any new Python dependency.

## AED Management

- `Boss Overview`: total units, PM outstanding, open issues, pending verification,
  attention-required items, monthly PM progress and a compact AED quick view.
- `Manage Units`: the original detailed filter, direct table editing, review,
  confirmation, add/deactivate and audit functions remain available.
- No Data Quality/Data Service dashboard section was added.

## PM, issues and marker colours

- PM Checklist, Report Issue, Resolution Submission and Resolution Verification
  now use review/confirmation before formal records are committed.
- A failed PM item creates its own issue record.
- Issue workflow automatically controls operational marker status:
  Issue -> Pending Verification -> Completed only when no unresolved issue remains.
- Planning/custom marker colours save immediately, without a Save button or
  confirmation, and are kept in system map files rather than the Excel sheet.
- Marker palette expanded to Blue, Green, Red, Orange, Yellow, Purple, Gray,
  Pink, Teal, Cyan, Indigo, Lime, Brown, Maroon and Black.
- Status names, colours and workflow definitions remain editable in Manage Statuses.

## Service Type

The existing `PM` and `Commissioning` positions are retained. These options are
appended to the end of the list:

- PM + Battery
- PM + Glass
- PM + Battery + Glass

Confirmed PM submission updates the master Excel `Job Type` field shown in the
system as `Service Type`.

## OneDrive

The system can use `IB_list_TEST.xlsx` from the user's own synchronized OneDrive
folder. See `ONEDRIVE_SETUP.md` and `.streamlit/secrets.toml.example`.

## Verification

- Python compile check passed.
- 54 automated tests passed.
- `requirements.txt` is unchanged; no new pip package is required.
