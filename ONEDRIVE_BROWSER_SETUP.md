# Browser-only OneDrive Excel connection

This version reads and updates the same workbook in personal OneDrive without
requiring the Windows OneDrive application or a local VS Code session.

## Required Streamlit Secrets

Keep the values already added under **App Settings > Secrets**:

```toml
[microsoft]
client_id = "..."
client_secret = "..."
authority = "https://login.microsoftonline.com/consumers"
redirect_uri = "https://YOUR-APP.streamlit.app/"
onedrive_file_path = "/AED System/IB_list_TEST.xlsx"
```

The `redirect_uri` must exactly match the Web redirect URI registered in
Microsoft Entra. `client_secret` must be the secret **Value**, not Secret ID.

## Expected use

1. Open the Streamlit site and choose **Sign in with Microsoft**.
2. Use the Microsoft account that owns `/AED System/IB_list_TEST.xlsx`.
3. **Refresh AED Data** downloads the latest OneDrive workbook into the app.
4. Confirmed Master Table, PM and planning updates are uploaded back to the
   same OneDrive file.
5. After editing the Excel file in Excel for the web, wait for `Saved`, then
   click **Refresh AED Data** in the system.
6. After saving from the system, refresh the Excel browser tab to display the
   new workbook version.

## Conflict protection

The system records the OneDrive eTag at download. It refuses to upload if the
workbook has changed in OneDrive since that download. Refresh the AED data and
repeat the edit instead of overwriting a newer version.

## Data separation

The official Excel fields are synchronized. Map colours, issue workflow state,
and other system-only CSV data remain separate and are not added to the IB List.
