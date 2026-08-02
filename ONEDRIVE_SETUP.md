# Use the IB List from your own OneDrive

1. Create `AED System` inside the OneDrive folder shown in Windows File Explorer.
2. Copy `IB_list_TEST.xlsx` into that folder and wait for the green sync tick.
3. The system automatically checks these common locations:
   - `C:\Users\<name>\OneDrive\AED System\IB_list_TEST.xlsx`
   - `C:\Users\<name>\OneDrive - Personal\AED System\IB_list_TEST.xlsx`
4. When your path is different, copy `.streamlit/secrets.toml.example` to
   `.streamlit/secrets.toml` and change `[excel].file_path` to the exact path.
5. Open the same workbook from OneDrive in Excel for the web. Streamlit updates
   the local synchronized file; OneDrive uploads the new workbook version.

No new pip package is required. Browser refresh may occasionally be needed
because openpyxl updates the workbook file rather than joining Excel coauthoring.
