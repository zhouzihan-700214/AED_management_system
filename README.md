# AED Operations Control System — Fresh Semantic Rebuild

This project is a clean-folder reconstruction of the validated AED Operations system. It preserves the existing visual language, routes, data files, Excel/OneDrive safeguards, PM and issue workflows, Unit Profiles, map controls and Service Records scope while using a newly separated application shell.

## Run locally

```bash
python -m pip install -r requirements.txt
python -m streamlit run streamlit_app.py
```

`streamlit_app.py` is the only supported executable entrypoint. Do not create or select `app.py`.

## Streamlit Cloud

Set **Main file path** to:

```text
streamlit_app.py
```

Copy `.streamlit/secrets.toml.example` to `.streamlit/secrets.toml` and replace only the placeholders required for OneMap or Microsoft OneDrive. Never commit real credentials.

## Data modes

Without Microsoft secrets, the project uses the local workbook in `external_data/IB_list_TEST.xlsx` and the local CSV cache. With valid Microsoft secrets, the official workbook is synchronized through OneDrive and application-owned records are synchronized separately in `AED_System_State.zip`.

## Main pages

- Operations Control
- PM Planning
- PM Checklist
- Report Issue
- Issues / Resolution / Verification
- AED Management and Unit Profiles
- AED Map
- Service Records

## Rebuild structure

The startup lifecycle is separated into `application/` modules for configuration compatibility, session state, runtime contracts, storage bootstrap, sidebar controls and cloud refresh. Existing service and page module interfaces remain compatible so every validated workflow and data format continues to work.

See `PROMPT_REBUILD_AED_SYSTEM.md` for the complete reusable generation specification and `REBUILD_VALIDATION.md` for verification results.

## Verified write-back status

- 138 repository tests pass.
- 110 isolated end-to-end write checks pass.
- A Battery Replacement History date-normalisation conflict bug found during deep testing was fixed.
- See `DEEP_FUNCTIONAL_TEST_REPORT.md` for the exact fields and workflow chains tested.
