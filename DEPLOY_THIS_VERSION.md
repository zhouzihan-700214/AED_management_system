# Deploy this version

Your Microsoft Entra registration and Streamlit **Settings > Secrets** are
already configured. Do not add the secret values to GitHub.

## Replace the repository code

Upload the contents of this project folder to the existing GitHub repository,
replacing files with the same names. Keep the repository root layout unchanged.
Streamlit Community Cloud may continue to use:

```text
streamlit_app.py
```

The included `streamlit_app.py` starts the existing `app.py` application.

## Do not replace these external settings

- Do not delete or recreate Streamlit Secrets.
- Do not change the Entra redirect URI or API permissions.
- Do not replace the OneDrive workbook if it is already located at
  `/AED System/IB_list_TEST.xlsx`.

## First validation after redeployment

1. Open the app and choose **Sign in with Microsoft**.
2. The sidebar should show **Microsoft OneDrive — Connected**.
3. Open **Data Source** and choose **Refresh AED Data**.
4. Confirm it displays `/AED System/IB_list_TEST.xlsx` rather than `/mount/src/.../external_data/...`.
5. Change one test Service Type in Master Table and confirm the save.
6. Refresh the Excel for the web tab and check the same row.
7. Change it back in Excel for the web, wait for `Saved`, and click **Refresh AED Data** in the app.
