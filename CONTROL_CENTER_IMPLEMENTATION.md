# Developer Implementation Notes

## Startup sequence

`app.py` now performs storage and schema preparation before rendering pages:

1. initialize PM CSV schemas;
2. initialize Issue CSV schemas;
3. add the default PM interval field to AED master data when missing;
4. load the grouped navigation;
5. dispatch to the selected view.

## Dashboard data flow

```text
CSV sources
→ services/dashboard_service.py
→ normalized queues and summaries
→ views/dashboard.py
→ ui/dashboard_components.py
```

Keep business calculations in `services/dashboard_service.py`. `views/dashboard.py` should remain a thin composition layer.

## Queue construction

Every source-specific builder returns the same internal columns. `Queue ID` is the stable identity used after a user selects a display row. Do not use the visible row number as identity because sorting and filtering change it.

Priority order is encoded in `Sort Score` and currently follows:

1. overdue PM;
2. urgent/high Issues;
3. pending verification;
4. PM due within 30 days;
5. consumables expired or due within 90 days;
6. missing or invalid operational data.

`Sort Score` and `Source Index` are internal and should not be displayed.

## Adding another queue type

1. Add a builder returning `DASHBOARD_QUEUE_COLUMNS`.
2. Assign a unique `Category` and stable `Queue ID` prefix.
3. Define priority and `Sort Score`.
4. Include it in `build_unified_work_queue()`.
5. Add selected-item rendering and navigation handling in `ui/dashboard_components.py`.
6. Add deterministic tests.

## PM scheduling

Do not calculate PM due dates independently in a view. Read `Next PM Date` for operational filtering. Only a service action that changes the maintenance baseline should recalculate it.

Use:

```python
calculate_next_pm_date(service_date, interval_months)
```

The AED-level `PM Interval Months` value must remain between 1 and 60.

## Empty CSV handling

Use the shared schema initialization functions. Do not create zero-byte files with `touch`, because `pandas.read_csv()` cannot infer columns from them.

## Page navigation from the dashboard

Before navigating, write the selected context to Session State:

```python
st.session_state["pm_target"] = {"Serial Number": serial_number}
st.session_state["selected_issue_id"] = issue_id
```

Then call the existing navigation callback. Destination pages consume the context and focus the correct record.

## Styling

Add new colours and spacing through CSS tokens in `ui/styles.py`; avoid hard-coded page-specific values. Keep dense data and forms on light surfaces. Reserve the dark palette for navigation and the compact control frame.

## Regression checks

Run:

```bash
python -m py_compile app.py config.py services/*.py ui/*.py views/*.py views/map_modules/*.py
pytest -q
```

Then manually confirm:

- row selection updates the details panel;
- each contextual button opens the correct record;
- filters persist through reruns;
- empty queues show useful empty states;
- the two-column layout stacks at narrower width;
- keyboard focus remains visible;
- 200% browser zoom remains usable.
