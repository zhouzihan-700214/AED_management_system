# Validation Report

Build: `2026-08-03-FULL-REBUILD-v1`

## Completed checks

- All Python source compiled successfully.
- Automated test suite: **83 passed**.
- Master Table remains a separate sidebar page.
- Unit Profiles are present in the Operations Control scope and placed above
  secondary summaries on AED Management.
- Runtime Python source contains no `Asset readiness` label.
- Service Type order is verified.
- 15 map colours and editable status definitions are verified.
- PM/Issue colour workflow tests pass.
- OneDrive Excel download/upload and ETag conflict tests pass.
- Separate system-state archive creation and round-trip tests pass.
- Real credentials are absent from the repository example file.
- Deprecated `use_container_width` arguments are absent from runtime Python.

## Boundary of validation

Microsoft sign-in, the user's actual OneDrive account, OneMap credentials and
Streamlit Cloud routing cannot be exercised without the user's private account.
The package includes a visible build marker so deployment can be verified
without guessing.
