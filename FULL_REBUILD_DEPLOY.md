# Deploy the Full Rebuild

## Recommended clean replacement

The earlier repository received many partial patches. Replace it with this full
package rather than uploading another patch.

1. Keep a backup of the old repository.
2. In the GitHub repository root, remove old application code folders/files.
3. Upload the **contents of this ZIP root** so GitHub directly shows:

```text
streamlit_app.py
app.py
config.py
requirements.txt
services/
views/
ui/
utils/
.streamlit/
```

Do not create an extra outer folder.

4. Commit to the exact branch used by Streamlit, normally `main`.
5. In Streamlit App settings confirm:
   - Repository: the updated repository
   - Branch: `main`
   - Main file path: `streamlit_app.py`
6. Reboot the app.
7. Confirm the sidebar displays:

```text
AED Operations · 2026-08-03-FULL-REBUILD-v1
```

If the marker is absent, the webpage is not running this code, regardless of
what GitHub files appear to contain.

## Secrets

Keep one `[onemap]` section and one `[microsoft]` section. The optional
`system_state_path` can be omitted because the code has a default.

Never commit a completed `secrets.toml` file.

## Microsoft redirect URI

The `redirect_uri` in Streamlit Secrets must exactly match the Web redirect URI
registered in Microsoft Entra, including the final `/`.

## Security action

An older repository version contained live-looking credentials in
`.streamlit/secrets.toml.example`. Rotate the OneMap password and Microsoft
Client Secret, then update Streamlit Secrets. The rebuilt example contains
placeholders only.
