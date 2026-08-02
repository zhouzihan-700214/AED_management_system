# OneDrive Excel connection

The preferred deployment is now **browser-only**:

```text
Streamlit browser app <-> Microsoft Graph <-> OneDrive Excel for the web
```

No Windows OneDrive application or local VS Code session is required.

See `ONEDRIVE_BROWSER_SETUP.md` for the exact Streamlit Secrets and usage steps.
The existing local-path mode remains available only as a fallback when the
complete `[microsoft]` Secrets section is not configured.
