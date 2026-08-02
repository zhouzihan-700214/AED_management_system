from __future__ import annotations

from pathlib import Path
from typing import Any
from datetime import date
import uuid

import pandas as pd
import streamlit as st

from config import (
    AUDIT_HISTORY_FILE,
    CONFLICT_HISTORY_FILE,
    EXCEL_WRITE_HISTORY_FILE,
    ISSUE_RECORD_FILE,
    MAP_STATUS_FILE,
    MAP_UNIT_STATE_FILE,
    PM_PLAN_FILE,
    TRANSACTION_HISTORY_FILE,
)
from services import aed_service
from services.aed_field_schema import (
    DATE_FIELDS,
    DETAIL_EDITABLE_COLUMNS,
    FIELD_LABELS,
    JOB_TYPE_OPTIONS,
    REPAIRED_OPTIONS,
    TABLE_EDITABLE_COLUMNS,
)
from services.aed_repository import (
    add_unit,
    batch_update_units,
    deactivate_unit,
    get_all_units,
    get_sync_status,
    update_unit,
)
from services.aed_table_edit_service import (
    build_cell_changes,
    group_changes_for_repository,
    normalize_value,
    prepare_editor_dataframe,
    validate_table_changes,
)
from services.excel_write_service import load_excel_write_history
from services.issue_service import load_issue_records
from ui.components import page_header, section_label
from utils.streamlit_utils import rerun_app
from utils.text_utils import clean_text
from views.map_modules.status_service import (
    COLOR_EMOJI,
    load_plan_records,
    load_status_definitions,
    load_unit_state,
    status_color_lookup,
)


MANAGEMENT_FILTER_KEYS = {
    "model": "management_model",
    "location": "management_location",
    "postal_code": "management_postal",
    "lift_lobby": "management_lift_lobby",
    "job_type": "management_job_type",
    "last_done_by": "management_last_done_by",
}

MANAGEMENT_DATE_FILTERS = [
    ("PM Completed Date", "pm_completed"),
    ("Next PM Date", "next_pm"),
    ("Battery Expiry Date", "battery_expiry"),
    ("Adult Pads Expiry Date", "adult_expiry"),
    ("Pediatric Pads Expiry Date", "pediatric_expiry"),
]

MIN_DATE = date(1900, 1, 1)
MAX_DATE = date(2100, 12, 31)

EDITOR_STATE_DEFAULTS = {
    "aed_editor_mode": "browse",
    "aed_editor_session_id": None,
    "aed_editor_base_df": None,
    "aed_editor_working_df": None,
    "aed_editor_base_signature": None,
    "aed_editor_changes": [],
    "aed_editor_errors": [],
    "aed_editor_warnings": [],
}


def initialise_table_editor_state() -> None:
    for key, value in EDITOR_STATE_DEFAULTS.items():
        if key not in st.session_state:
            st.session_state[key] = value


def clear_table_editor_state() -> None:
    for key, value in EDITOR_STATE_DEFAULTS.items():
        st.session_state[key] = value


def _management_date_ranges_from_state() -> dict[str, tuple[Any, Any]]:
    return {
        column: (
            st.session_state.get(f"{key_prefix}_from"),
            st.session_state.get(f"{key_prefix}_to"),
        )
        for column, key_prefix in MANAGEMENT_DATE_FILTERS
    }


def _management_filter_selections_from_state() -> dict[str, list[Any]]:
    selections: dict[str, list[Any]] = {}
    for filter_name, session_key in MANAGEMENT_FILTER_KEYS.items():
        value = st.session_state.get(session_key, [])
        if isinstance(value, (list, tuple, set)):
            selections[filter_name] = list(value)
        elif value:
            selections[filter_name] = [value]
        else:
            selections[filter_name] = []
    return selections


def _mark_management_filter_changed(filter_name: str) -> None:
    st.session_state["management_last_changed_filter"] = filter_name


def _normalise_management_filter_state(
    dataframe: pd.DataFrame,
    keyword: str,
    date_ranges: dict[str, tuple[Any, Any]],
) -> None:
    selections = _management_filter_selections_from_state()
    last_changed = st.session_state.get("management_last_changed_filter")

    if last_changed in MANAGEMENT_FILTER_KEYS:
        base_options = aed_service.linked_filter_options(
            dataframe=dataframe,
            target_filter=last_changed,
            keyword=keyword,
            selections={name: [] for name in MANAGEMENT_FILTER_KEYS},
            date_ranges=date_ranges,
        )
        allowed = set(base_options)
        valid = [value for value in selections[last_changed] if value in allowed]
        if valid != selections[last_changed]:
            selections[last_changed] = valid
            st.session_state[MANAGEMENT_FILTER_KEYS[last_changed]] = valid

    order = [name for name in MANAGEMENT_FILTER_KEYS if name != last_changed]
    if last_changed in MANAGEMENT_FILTER_KEYS:
        order.append(last_changed)

    for _ in range(len(MANAGEMENT_FILTER_KEYS) + 1):
        changed = False
        for filter_name in order:
            options = aed_service.linked_filter_options(
                dataframe=dataframe,
                target_filter=filter_name,
                keyword=keyword,
                selections=selections,
                date_ranges=date_ranges,
            )
            allowed = set(options)
            valid = [value for value in selections[filter_name] if value in allowed]
            if valid != selections[filter_name]:
                selections[filter_name] = valid
                st.session_state[MANAGEMENT_FILTER_KEYS[filter_name]] = valid
                changed = True
        if not changed:
            break


def reset_management_filters() -> None:
    defaults: dict[str, Any] = {
        "management_keyword": "",
        "management_model": [],
        "management_location": [],
        "management_postal": [],
        "management_lift_lobby": [],
        "management_job_type": [],
        "management_last_done_by": [],
        "management_sort_by": "Serial Number",
        "management_sort_order": "Ascending",
        "management_last_changed_filter": None,
    }
    for _, key_prefix in MANAGEMENT_DATE_FILTERS:
        defaults[f"{key_prefix}_from"] = None
        defaults[f"{key_prefix}_to"] = None
    for key, value in defaults.items():
        st.session_state[key] = value


def render_filters(dataframe: pd.DataFrame) -> dict[str, Any]:
    filter_state: dict[str, Any] = {}
    st.markdown("### Filters")
    keyword = st.session_state.get("management_keyword", "")
    date_ranges = _management_date_ranges_from_state()

    with st.expander("Basic Filters", expanded=True):
        filter_state["keyword"] = st.text_input(
            "Keyword Search",
            placeholder=(
                "Serial, model, location, postal code, lobby, PO, zone, "
                "lot number, e-SR or remarks"
            ),
            key="management_keyword",
        )
        keyword = filter_state["keyword"]
        _normalise_management_filter_state(dataframe, keyword, date_ranges)
        selections = _management_filter_selections_from_state()
        labels = {
            "model": "Model",
            "location": "Location",
            "postal_code": "Postal Code",
            "lift_lobby": "Lift Lobby",
            "job_type": "Job Type",
            "last_done_by": "Last Done By",
        }
        for filter_name, label in labels.items():
            options = aed_service.linked_filter_options(
                dataframe=dataframe,
                target_filter=filter_name,
                keyword=keyword,
                selections=selections,
                date_ranges=date_ranges,
            )
            filter_state[filter_name] = st.multiselect(
                label,
                options=options,
                key=MANAGEMENT_FILTER_KEYS[filter_name],
                on_change=_mark_management_filter_changed,
                args=(filter_name,),
            )
            selections[filter_name] = filter_state[filter_name]

    with st.expander("Date Filters"):
        date_ranges = {}
        for column, key_prefix in MANAGEMENT_DATE_FILTERS:
            st.markdown(f"**{column}**")
            from_col, to_col = st.columns(2)
            with from_col:
                start_value = st.date_input(
                    "From", value=None, format="DD-MM-YYYY", min_value=MIN_DATE, max_value=MAX_DATE, key=f"{key_prefix}_from"
                )
            with to_col:
                end_value = st.date_input(
                    "To", value=None, format="DD-MM-YYYY", min_value=MIN_DATE, max_value=MAX_DATE, key=f"{key_prefix}_to"
                )
            date_ranges[column] = (start_value, end_value)
        filter_state["date_ranges"] = date_ranges

    with st.expander("Sorting"):
        filter_state["sort_by"] = st.selectbox(
            "Sort By",
            options=aed_service.AED_COLUMNS,
            index=0,
            key="management_sort_by",
        )
        filter_state["ascending"] = (
            st.radio(
                "Order",
                options=["Ascending", "Descending"],
                horizontal=True,
                key="management_sort_order",
            )
            == "Ascending"
        )

    st.button(
        "Reset Filters",
        use_container_width=True,
        key="reset_management_filters_button",
        on_click=reset_management_filters,
    )
    return filter_state


def _unit_option_label(dataframe: pd.DataFrame, row_index: Any) -> str:
    row = dataframe.loc[row_index]
    serial = aed_service.clean_text(row.get("Serial Number", "")) or "No serial"
    location = aed_service.clean_text(row.get("Location", "")) or "No location"
    postal = aed_service.clean_text(row.get("Postal Code", "")) or "No postal code"
    return f"{serial} | {location} | {postal}"


def _date_input_value(value: Any):
    parsed = aed_service.parse_date(value)
    return None if parsed is None else parsed.date()


def _column_config(editor_df: pd.DataFrame | None = None) -> dict[str, Any]:
    job_options = list(JOB_TYPE_OPTIONS)
    repaired_options = list(REPAIRED_OPTIONS)
    if editor_df is not None:
        for value in editor_df.get("Job Type", pd.Series(dtype=str)).astype(str).str.strip().unique():
            if value and value not in job_options:
                job_options.append(value)
        for value in editor_df.get("Repaired?", pd.Series(dtype=str)).astype(str).str.strip().unique():
            if value and value not in repaired_options:
                repaired_options.append(value)
    return {
        "Serial Number": st.column_config.TextColumn(
            "Serial Number", help="Unique identifier; cannot be edited."
        ),
        "Model": st.column_config.TextColumn("Model / Related Object"),
        "Postal Code": st.column_config.TextColumn(
            "Postal Code", help="Six-digit postal code", max_chars=6
        ),
        "Adult Pads Expiry Date": st.column_config.DateColumn(
            "Adult Pads Expiry Date", format="DD/MM/YYYY"
        ),
        "Pediatric Pads Expiry Date": st.column_config.DateColumn(
            "Pediatric Pads Expiry Date", format="DD/MM/YYYY"
        ),
        "Battery Expiry Date": st.column_config.DateColumn(
            "Battery Expiry Date", format="DD/MM/YYYY"
        ),
        "PM Completed Date": st.column_config.DateColumn(
            "PM Completed Date", format="DD/MM/YYYY"
        ),
        "Next PM Date": st.column_config.DateColumn(
            "Next PM Date", format="DD/MM/YYYY", required=True
        ),
        "Job Type": st.column_config.SelectboxColumn(
            "Service Type", options=job_options
        ),
        "Repaired?": st.column_config.SelectboxColumn(
            "Repaired?", options=repaired_options
        ),
        "Service Report e-SR": st.column_config.TextColumn(
            "Service Report / e-SR"
        ),
    }


def render_browse_table(filtered: pd.DataFrame) -> None:
    display_columns = [
        column for column in aed_service.AED_COLUMNS if column in filtered.columns
    ]
    st.dataframe(
        filtered[display_columns],
        use_container_width=True,
        height=500,
        hide_index=True,
    )

    count = len(filtered)
    if count == 0:
        st.info("No AED units match the current filters.")
        return
    if count > 100:
        st.warning(
            "Narrow the filters to 100 AED units or fewer before entering table edit mode."
        )
        return

    if st.button(
        "Edit Current Results",
        type="primary",
        use_container_width=True,
        key="start_aed_table_edit",
    ):
        try:
            editor_df = prepare_editor_dataframe(filtered)
        except ValueError as error:
            st.error(str(error))
            return
        st.session_state.aed_editor_mode = "edit"
        st.session_state.aed_editor_session_id = uuid.uuid4().hex
        st.session_state.aed_editor_base_df = editor_df.copy()
        st.session_state.aed_editor_working_df = editor_df.copy()
        st.session_state.aed_editor_base_signature = get_sync_status().get("signature")
        st.session_state.aed_editor_changes = []
        st.session_state.aed_editor_errors = []
        st.session_state.aed_editor_warnings = []
        rerun_app()


def render_edit_mode() -> None:
    base_df = st.session_state.aed_editor_base_df
    working_df = st.session_state.aed_editor_working_df
    editor_id = st.session_state.aed_editor_session_id
    if base_df is None or working_df is None or not editor_id:
        clear_table_editor_state()
        st.error("The edit session was incomplete and has been reset.")
        return

    st.subheader(f"Editing {len(base_df)} AED unit(s)")
    st.info(
        "Filters and automatic Excel refresh are paused. Edit the cells, then review before saving."
    )
    with st.form(f"aed_table_form_{editor_id}"):
        edited_df = st.data_editor(
            working_df,
            use_container_width=True,
            height=650,
            hide_index=True,
            num_rows="fixed",
            disabled=["Serial Number"],
            column_config=_column_config(working_df),
            key=f"aed_table_editor_{editor_id}",
        )
        left, right = st.columns(2)
        review_clicked = left.form_submit_button(
            "Review Changes", type="primary", use_container_width=True
        )
        cancel_clicked = right.form_submit_button(
            "Cancel Editing", use_container_width=True
        )

    if cancel_clicked:
        clear_table_editor_state()
        rerun_app()
    if not review_clicked:
        return

    try:
        changes = build_cell_changes(base_df, edited_df)
        errors, warnings = validate_table_changes(base_df, changes)
    except ValueError as error:
        st.error(str(error))
        return
    if not changes:
        st.info("No changes were detected.")
        return

    st.session_state.aed_editor_working_df = edited_df.copy()
    st.session_state.aed_editor_changes = changes
    st.session_state.aed_editor_errors = errors
    st.session_state.aed_editor_warnings = warnings
    st.session_state.aed_editor_mode = "review"
    rerun_app()


def _changes_dataframe(changes: list[dict[str, str]]) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "Serial Number": change["serial_number"],
                "Field": FIELD_LABELS.get(change["field"], change["field"]),
                "Old Value": change["original_value"],
                "New Value": change["desired_value"],
            }
            for change in changes
        ]
    )


def _flatten_conflicts(conflicts: dict[str, Any]) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for serial, field_conflicts in conflicts.items():
        for field, values in field_conflicts.items():
            rows.append(
                {
                    "Serial Number": serial,
                    "Field": FIELD_LABELS.get(field, field),
                    "Opened Value": values.get("original", ""),
                    "Current Excel": values.get("current", ""),
                    "Your Value": values.get("desired", ""),
                }
            )
    return pd.DataFrame(rows)


def render_review_mode() -> None:
    changes = list(st.session_state.aed_editor_changes)
    errors = list(st.session_state.aed_editor_errors)
    warnings = list(st.session_state.aed_editor_warnings)
    affected = {change["serial_number"] for change in changes}

    st.subheader("Review Changes")
    st.write(f"{len(changes)} cell change(s) across {len(affected)} AED unit(s).")
    st.dataframe(_changes_dataframe(changes), use_container_width=True, hide_index=True)
    for warning in warnings:
        st.warning(warning)
    for error in errors:
        st.error(error)
    if errors:
        st.info("Return to editing and correct the errors before saving.")

    col1, col2, col3 = st.columns(3)
    confirm = col1.button(
        "Confirm Save to Excel",
        type="primary",
        disabled=bool(errors),
        use_container_width=True,
    )
    back = col2.button("Back to Editing", use_container_width=True)
    discard = col3.button("Discard Changes", use_container_width=True)

    if back:
        st.session_state.aed_editor_mode = "edit"
        rerun_app()
    if discard:
        clear_table_editor_state()
        rerun_app()
    if not confirm:
        return

    updates = group_changes_for_repository(changes)
    with st.spinner("Checking conflicts and updating Excel..."):
        result = batch_update_units(
            updates=updates,
            user=st.session_state.get("audit_user", ""),
            session_id=st.session_state.get("session_id", ""),
            source_page="AED Management Table",
        )
    if result.success:
        clear_table_editor_state()
        st.session_state["aed_writeback_notice"] = result.message
        st.session_state["aed_writeback_warnings"] = list(result.warnings)
        rerun_app()
    if result.status == "conflict":
        st.error(result.message)
        st.dataframe(
            _flatten_conflicts(result.conflicts),
            use_container_width=True,
            hide_index=True,
        )
        st.info("No part of this edit batch was saved.")
    elif result.status in {"already_applied", "no_changes"}:
        st.info(result.message)
    elif result.excel_updated:
        st.warning(result.message)
    else:
        st.error(result.message)


def _snapshot_value(field: str, value: Any) -> str:
    try:
        return normalize_value(field, value)
    except ValueError:
        return aed_service.clean_text(value)


def _select_options_with_current(options: list[str], current: str) -> list[str]:
    result = list(options)
    if current and current not in result:
        result.append(current)
    return result


def render_full_details_editor(filtered: pd.DataFrame) -> None:
    with st.expander("Edit Full Details", expanded=False):
        st.caption(
            "Use this form for fields that are too wide for the main table, including replacement history and Remarks."
        )
        if filtered.empty:
            st.info("No AED matches the current filters.")
            return
        indices = filtered.index.tolist()
        selected_index = st.selectbox(
            "Select an AED",
            options=indices,
            index=None,
            placeholder="Choose one matching AED",
            format_func=lambda index: _unit_option_label(filtered, index),
            key="full_detail_selected_index",
        )
        if selected_index is None:
            return
        selected = filtered.loc[selected_index]
        serial = aed_service.clean_text(selected.get("Serial Number", ""))
        snapshot_key = "full_detail_snapshot"
        if st.session_state.get("full_detail_snapshot_serial") != serial:
            st.session_state.full_detail_snapshot_serial = serial
            st.session_state[snapshot_key] = {
                field: _snapshot_value(field, selected.get(field, ""))
                for field in DETAIL_EDITABLE_COLUMNS
            }
        snapshot = dict(st.session_state.get(snapshot_key, {}))

        with st.form(f"full_detail_form_{serial}"):
            st.markdown("#### Basic Information")
            c1, c2 = st.columns(2)
            c1.text_input("Serial Number", value=serial, disabled=True)
            c2.text_input(
                "Audit User",
                value=st.session_state.get("audit_user", ""),
                disabled=True,
            )
            installation = c1.date_input(
                "Installation Date",
                value=_date_input_value(snapshot.get("Installation Date", "")),
                format="DD-MM-YYYY", min_value=MIN_DATE, max_value=MAX_DATE,
            )
            model = c2.text_input(
                "Model / Related Object", value=snapshot.get("Model", "")
            )
            phase = c1.text_input(
                "Installed Phase / Month",
                value=snapshot.get("Installed Phase / Month", ""),
            )
            po_number = c2.text_input("PO Number", value=snapshot.get("PO Number", ""))
            zone = c1.text_input("Zone", value=snapshot.get("Zone", ""))
            block = c2.text_input(
                "Block / Locations", value=snapshot.get("Block / Locations", "")
            )
            street = c1.text_input("Street Name", value=snapshot.get("Street Name", ""))
            postal = c2.text_input(
                "Postal Code", value=snapshot.get("Postal Code", ""), max_chars=6
            )
            level = c1.text_input("Level", value=snapshot.get("Level", ""))
            lobby = c2.text_input("Lift Lobby", value=snapshot.get("Lift Lobby", ""))

            st.markdown("#### Adult Pads")
            c1, c2, c3 = st.columns(3)
            adult_replacement = c1.date_input(
                "Adult Pads Replacement Date",
                value=_date_input_value(snapshot.get("Adult Pads Replacement Date", "")),
                format="DD-MM-YYYY", min_value=MIN_DATE, max_value=MAX_DATE,
            )
            adult_expiry = c2.date_input(
                "Adult Pads Expiry Date",
                value=_date_input_value(snapshot.get("Adult Pads Expiry Date", "")),
                format="DD-MM-YYYY", min_value=MIN_DATE, max_value=MAX_DATE,
            )
            adult_lot = c3.text_input(
                "Adult Pads Lot Number", value=snapshot.get("Adult Pads Lot Number", "")
            )

            st.markdown("#### Pediatric Pads")
            c1, c2, c3 = st.columns(3)
            pediatric_replacement = c1.date_input(
                "Pediatric Pads Replacement Date",
                value=_date_input_value(snapshot.get("Pediatric Pads Replacement Date", "")),
                format="DD-MM-YYYY", min_value=MIN_DATE, max_value=MAX_DATE,
            )
            pediatric_expiry = c2.date_input(
                "Pediatric Pads Expiry Date",
                value=_date_input_value(snapshot.get("Pediatric Pads Expiry Date", "")),
                format="DD-MM-YYYY", min_value=MIN_DATE, max_value=MAX_DATE,
            )
            pediatric_lot = c3.text_input(
                "Pediatric Pads Lot Number",
                value=snapshot.get("Pediatric Pads Lot Number", ""),
            )

            st.markdown("#### Battery")
            c1, c2 = st.columns(2)
            battery_expiry = c1.date_input(
                "Battery Expiry Date",
                value=_date_input_value(snapshot.get("Battery Expiry Date", "")),
                format="DD-MM-YYYY", min_value=MIN_DATE, max_value=MAX_DATE,
            )
            battery_history = c2.text_area(
                "Battery Replacement History",
                value=snapshot.get("Battery Replacement History", ""),
                height=90,
            )

            st.markdown("#### PM and Service")
            c1, c2 = st.columns(2)
            completed = c1.date_input(
                "PM Completed Date",
                value=_date_input_value(snapshot.get("PM Completed Date", "")),
                format="DD-MM-YYYY", min_value=MIN_DATE, max_value=MAX_DATE,
            )
            next_pm = c2.date_input(
                "Next PM Date",
                value=_date_input_value(snapshot.get("Next PM Date", "")),
                format="DD-MM-YYYY", min_value=MIN_DATE, max_value=MAX_DATE,
            )
            job_options = _select_options_with_current(
                JOB_TYPE_OPTIONS, snapshot.get("Job Type", "")
            )
            job_type = c1.selectbox(
                "Job Type",
                options=job_options,
                index=job_options.index(snapshot.get("Job Type", ""))
                if snapshot.get("Job Type", "") in job_options
                else 0,
            )
            last_done = c2.text_input(
                "Last Done By", value=snapshot.get("Last Done By", "")
            )
            report = c1.text_input(
                "Service Report / e-SR",
                value=snapshot.get("Service Report e-SR", ""),
            )
            repaired_options = _select_options_with_current(
                REPAIRED_OPTIONS, snapshot.get("Repaired?", "")
            )
            repaired = c2.selectbox(
                "Repaired?",
                options=repaired_options,
                index=repaired_options.index(snapshot.get("Repaired?", ""))
                if snapshot.get("Repaired?", "") in repaired_options
                else 0,
            )
            remarks = st.text_area(
                "Remarks",
                value=snapshot.get("Remarks", ""),
                height=150,
                help=(
                    "When saved, existing Remarks continuation text is consolidated into the main AED row."
                ),
            )
            submitted = st.form_submit_button(
                "Save Full Details to Excel",
                type="primary",
                use_container_width=True,
            )

        if not submitted:
            return
        entered: dict[str, Any] = {
            "Installation Date": aed_service.format_date(installation),
            "Model": model,
            "Installed Phase / Month": phase,
            "PO Number": po_number,
            "Zone": zone,
            "Block / Locations": block,
            "Street Name": street,
            "Postal Code": postal,
            "Level": level,
            "Lift Lobby": lobby,
            "Adult Pads Replacement Date": aed_service.format_date(adult_replacement),
            "Adult Pads Expiry Date": aed_service.format_date(adult_expiry),
            "Adult Pads Lot Number": adult_lot,
            "Pediatric Pads Replacement Date": aed_service.format_date(pediatric_replacement),
            "Pediatric Pads Expiry Date": aed_service.format_date(pediatric_expiry),
            "Pediatric Pads Lot Number": pediatric_lot,
            "Battery Replacement History": battery_history,
            "Battery Expiry Date": aed_service.format_date(battery_expiry),
            "PM Completed Date": aed_service.format_date(completed),
            "Next PM Date": aed_service.format_date(next_pm),
            "Job Type": job_type,
            "Last Done By": last_done,
            "Service Report e-SR": report,
            "Repaired?": repaired,
            "Remarks": remarks,
        }
        changes: dict[str, Any] = {}
        original_values: dict[str, Any] = {}
        try:
            for field, raw_value in entered.items():
                new_value = normalize_value(field, raw_value)
                old_value = snapshot.get(field, "")
                if new_value != old_value:
                    changes[field] = new_value
                    original_values[field] = old_value
        except ValueError as error:
            st.error(str(error))
            return
        if not changes:
            st.info("No changes were detected.")
            return
        result = update_unit(
            serial_number=serial,
            changes=changes,
            original_values=original_values,
            user=st.session_state.get("audit_user", ""),
            session_id=st.session_state.get("session_id", ""),
            source_page="AED Management Full Details",
        )
        if result.success:
            st.session_state.pop("full_detail_snapshot_serial", None)
            st.session_state.pop(snapshot_key, None)
            st.session_state["aed_writeback_notice"] = result.message
            st.session_state["aed_writeback_warnings"] = list(result.warnings)
            rerun_app()
        elif result.status == "conflict":
            st.error(result.message)
            rows = [
                {
                    "Field": FIELD_LABELS.get(field, field),
                    "Opened Value": values.get("original", ""),
                    "Current Excel": values.get("current", ""),
                    "Your Value": values.get("desired", ""),
                }
                for field, values in result.conflicts.items()
            ]
            st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
        elif result.status in {"no_changes", "already_applied"}:
            st.info(result.message)
        elif result.excel_updated:
            st.warning(result.message)
        else:
            st.error(result.message)


def _optional_date(label: str, key: str):
    return st.date_input(label, value=None, format="DD-MM-YYYY", min_value=MIN_DATE, max_value=MAX_DATE, key=key)


def render_add_and_deactivate(dataframe: pd.DataFrame) -> None:
    with st.expander("Add or Deactivate AED", expanded=False):
        add_tab, deactivate_tab = st.tabs(["Add AED", "Deactivate AED"])
        with add_tab:
            st.caption("Fields marked * are required; the remaining fields may be completed later.")
            with st.form("stage5_full_add_aed_form"):
                st.markdown("#### Basic Information")
                c1, c2 = st.columns(2)
                serial = c1.text_input("Serial Number*")
                model = c2.text_input("Model / Related Object*")
                installation = c1.date_input(
                    "Installation Date", value=None, format="DD-MM-YYYY", min_value=MIN_DATE, max_value=MAX_DATE
                )
                phase = c2.text_input("Installed Phase / Month")
                po_number = c1.text_input("PO Number")
                zone = c2.text_input("Zone")
                block = c1.text_input("Block / Locations*")
                street = c2.text_input("Street Name*")
                postal = c1.text_input("Postal Code*", max_chars=6)
                level = c2.text_input("Level")
                lobby = c1.text_input("Lift Lobby")

                st.markdown("#### Adult Pads")
                c1, c2, c3 = st.columns(3)
                adult_replacement = c1.date_input(
                    "Adult Pads Replacement Date", value=None, format="DD-MM-YYYY", min_value=MIN_DATE, max_value=MAX_DATE
                )
                adult_expiry = c2.date_input(
                    "Adult Pads Expiry Date", value=None, format="DD-MM-YYYY", min_value=MIN_DATE, max_value=MAX_DATE
                )
                adult_lot = c3.text_input("Adult Pads Lot Number")

                st.markdown("#### Pediatric Pads")
                c1, c2, c3 = st.columns(3)
                pediatric_replacement = c1.date_input(
                    "Pediatric Pads Replacement Date", value=None, format="DD-MM-YYYY", min_value=MIN_DATE, max_value=MAX_DATE
                )
                pediatric_expiry = c2.date_input(
                    "Pediatric Pads Expiry Date", value=None, format="DD-MM-YYYY", min_value=MIN_DATE, max_value=MAX_DATE
                )
                pediatric_lot = c3.text_input("Pediatric Pads Lot Number")

                st.markdown("#### Battery")
                c1, c2 = st.columns(2)
                battery_expiry = c1.date_input(
                    "Battery Expiry Date", value=None, format="DD-MM-YYYY", min_value=MIN_DATE, max_value=MAX_DATE
                )
                battery_history = c2.text_area("Battery Replacement History", height=90)

                st.markdown("#### PM and Service")
                c1, c2 = st.columns(2)
                completed = c1.date_input(
                    "PM Completed Date", value=None, format="DD-MM-YYYY", min_value=MIN_DATE, max_value=MAX_DATE
                )
                next_pm = c2.date_input(
                    "Next PM Date*", value=None, format="DD-MM-YYYY", min_value=MIN_DATE, max_value=MAX_DATE
                )
                job_type = c1.selectbox("Service Type", options=JOB_TYPE_OPTIONS)
                last_done = c2.text_input("Last Done By")
                report = c1.text_input("Service Report / e-SR")
                repaired = c2.selectbox("Repaired?", options=REPAIRED_OPTIONS)
                remarks = st.text_area("Remarks", height=140)
                add_clicked = st.form_submit_button(
                    "Add AED to Excel", type="primary", use_container_width=True
                )

            if add_clicked:
                values = {
                    "Serial Number": serial,
                    "Installation Date": aed_service.format_date(installation),
                    "Model": model,
                    "Installed Phase / Month": phase,
                    "PO Number": po_number,
                    "Zone": zone,
                    "Block / Locations": block,
                    "Street Name": street,
                    "Postal Code": postal,
                    "Level": level,
                    "Lift Lobby": lobby,
                    "Adult Pads Replacement Date": aed_service.format_date(adult_replacement),
                    "Adult Pads Expiry Date": aed_service.format_date(adult_expiry),
                    "Adult Pads Lot Number": adult_lot,
                    "Pediatric Pads Replacement Date": aed_service.format_date(pediatric_replacement),
                    "Pediatric Pads Expiry Date": aed_service.format_date(pediatric_expiry),
                    "Pediatric Pads Lot Number": pediatric_lot,
                    "Battery Replacement History": battery_history,
                    "Battery Expiry Date": aed_service.format_date(battery_expiry),
                    "PM Completed Date": aed_service.format_date(completed),
                    "Next PM Date": aed_service.format_date(next_pm),
                    "Job Type": job_type,
                    "Last Done By": last_done,
                    "Service Report e-SR": report,
                    "Repaired?": repaired,
                    "Remarks": remarks,
                }
                result = add_unit(
                    values=values,
                    user=st.session_state.get("audit_user", ""),
                    session_id=st.session_state.get("session_id", ""),
                    source_page="AED Management Add",
                )
                if result.success:
                    st.session_state["aed_writeback_notice"] = result.message
                    st.session_state["aed_writeback_warnings"] = list(result.warnings)
                    rerun_app()
                else:
                    st.error(result.message)

        with deactivate_tab:
            options = dataframe.index.tolist()
            selected_index = st.selectbox(
                "Select active AED",
                options=options,
                index=None,
                format_func=lambda index: _unit_option_label(dataframe, index),
                key="deactivate_aed_index",
            )
            reason = st.text_input("Reason", key="deactivate_reason")
            confirm = st.checkbox(
                "I confirm this unit should be hidden from active operational pages."
            )
            if st.button(
                "Deactivate AED",
                disabled=selected_index is None or not confirm,
                use_container_width=True,
            ):
                serial_value = aed_service.clean_text(
                    dataframe.loc[selected_index].get("Serial Number", "")
                )
                result = deactivate_unit(
                    serial_number=serial_value,
                    user=st.session_state.get("audit_user", ""),
                    session_id=st.session_state.get("session_id", ""),
                    reason=reason,
                    source_page="AED Management",
                )
                if result.success:
                    st.session_state["aed_writeback_notice"] = result.message
                    rerun_app()
                else:
                    st.error(result.message)


def _read_optional_csv(path: str | Path) -> pd.DataFrame:
    csv_path = Path(path)
    if not csv_path.exists() or csv_path.stat().st_size == 0:
        return pd.DataFrame()
    try:
        return pd.read_csv(
            csv_path, dtype=str, keep_default_na=False, encoding="utf-8-sig"
        )
    except (OSError, pd.errors.EmptyDataError):
        return pd.DataFrame()


def render_audit_log(history_file: str | Path) -> None:
    with st.expander("Transaction History", expanded=False):
        history = _read_optional_csv(TRANSACTION_HISTORY_FILE)
        if history.empty:
            st.info("No transactions have been recorded yet.")
        else:
            st.dataframe(
                history.tail(50).iloc[::-1], use_container_width=True, hide_index=True
            )

    with st.expander("Field Audit and Conflict History", expanded=False):
        audit = _read_optional_csv(AUDIT_HISTORY_FILE)
        conflicts = _read_optional_csv(CONFLICT_HISTORY_FILE)
        audit_tab, conflict_tab = st.tabs(["All field results", "Conflicts"])
        with audit_tab:
            if audit.empty:
                st.info("No field-level audit records are available.")
            else:
                st.dataframe(
                    audit.tail(100).iloc[::-1],
                    use_container_width=True,
                    hide_index=True,
                )
        with conflict_tab:
            if conflicts.empty:
                st.info("No edit conflicts have been recorded.")
            else:
                st.dataframe(
                    conflicts.tail(100).iloc[::-1],
                    use_container_width=True,
                    hide_index=True,
                )

    with st.expander("Earlier Excel Write History", expanded=False):
        rows = load_excel_write_history(EXCEL_WRITE_HISTORY_FILE)
        if not rows:
            st.info("No earlier website-to-Excel updates were recorded.")
        else:
            st.dataframe(
                pd.DataFrame(rows).tail(30).iloc[::-1],
                use_container_width=True,
                hide_index=True,
            )

    with st.expander("Legacy CSV Audit Log", expanded=False):
        history = aed_service.load_history(history_file)
        if history.empty:
            st.info("No earlier CSV master-data changes were recorded.")
        else:
            st.dataframe(history.head(20), use_container_width=True, hide_index=True)


def _navigate_management(page_name: str) -> None:
    st.session_state["page"] = page_name
    rerun_app()


def _open_master_table() -> None:
    reset_management_filters()
    st.session_state["page"] = "AED Master Table"


def _selection_rows(event: Any) -> list[int]:
    selection = getattr(event, "selection", None)
    if selection is None and isinstance(event, dict):
        selection = event.get("selection", {})
    if selection is None:
        return []
    if isinstance(selection, dict):
        return list(selection.get("rows", []))
    return list(getattr(selection, "rows", []) or [])


def _management_snapshot(dataframe: pd.DataFrame) -> dict[str, Any]:
    try:
        issues = load_issue_records(ISSUE_RECORD_FILE)
    except Exception:
        issues = pd.DataFrame()

    if not issues.empty and "Status" in issues.columns:
        open_issues = issues[
            ~issues["Status"].astype(str).str.casefold().isin({"closed", "resolved"})
        ].copy()
        pending_verification = open_issues[
            open_issues["Status"].astype(str).str.casefold().eq("pending verification")
        ].copy()
    else:
        open_issues = pd.DataFrame()
        pending_verification = pd.DataFrame()

    plans = load_plan_records(PM_PLAN_FILE)
    current_month = date.today().strftime("%Y-%m")
    current_plan = (
        plans[plans["Plan Month"].astype(str).eq(current_month)].copy()
        if not plans.empty and "Plan Month" in plans.columns
        else pd.DataFrame()
    )
    if current_plan.empty:
        completed_count = 0
        outstanding_count = 0
    else:
        completed_mask = current_plan["Completed Date"].astype(str).str.strip().ne("")
        completed_count = int(completed_mask.sum())
        outstanding_count = int((~completed_mask).sum())

    return {
        "issues": issues,
        "open_issues": open_issues,
        "pending_verification": pending_verification,
        "current_plan": current_plan,
        "completed_count": completed_count,
        "outstanding_count": outstanding_count,
        "total_units": len(dataframe),
        "current_month": current_month,
    }


def _render_management_kpis(snapshot: dict[str, Any]) -> None:
    columns = st.columns(4, gap="small")
    cards = [
        (
            "All AED Units",
            snapshot["total_units"],
            "Open the full Master Table workspace",
            "management_open_all_units",
            _open_master_table,
        ),
        (
            "PM Outstanding",
            snapshot["outstanding_count"],
            "Open the current PM plan",
            "management_open_pm",
            lambda: st.session_state.__setitem__("page", "PM Planning"),
        ),
        (
            "Open Issues",
            len(snapshot["open_issues"]),
            "Review unresolved operational risk",
            "management_open_issues",
            lambda: st.session_state.__setitem__("page", "Issues"),
        ),
        (
            "Pending Verification",
            len(snapshot["pending_verification"]),
            "Review submitted resolutions",
            "management_open_pending",
            lambda: st.session_state.__setitem__("page", "Issues"),
        ),
    ]

    for column, (label, value, note, key, action) in zip(columns, cards):
        with column:
            if st.button(
                f"{label}\n\n{value}\n\n{note}",
                use_container_width=True,
                key=key,
                type="secondary",
            ):
                action()
                rerun_app()


def _render_attention_required(snapshot: dict[str, Any]) -> None:
    section_label("ATTENTION REQUIRED")
    open_issues = snapshot["open_issues"].copy()
    if open_issues.empty:
        st.success("No unresolved Issues require management attention.")
        return

    priority_order = {"Urgent": 0, "High": 1, "Medium": 2, "Low": 3}
    open_issues["_priority"] = open_issues.get(
        "Priority", pd.Series(index=open_issues.index, dtype=str)
    ).map(priority_order).fillna(9)
    open_issues["_reported"] = pd.to_datetime(
        open_issues.get("Reported At", ""),
        format="%d-%m-%Y %H:%M:%S",
        errors="coerce",
    )
    open_issues = open_issues.sort_values(
        ["_priority", "_reported"], ascending=[True, True]
    ).head(5)

    display = open_issues.reindex(
        columns=[
            "Priority",
            "Issue ID",
            "Serial Number",
            "Location",
            "Issue Type",
            "Status",
            "Due Date",
        ]
    ).copy()
    event = st.dataframe(
        display,
        use_container_width=True,
        hide_index=True,
        height=min(250, 48 + 36 * len(display)),
        on_select="rerun",
        selection_mode="single-row",
        key="aed_management_attention_table",
    )
    selected_rows = _selection_rows(event)
    if selected_rows:
        selected_index = selected_rows[0]
        if 0 <= selected_index < len(open_issues):
            st.session_state["selected_issue_id"] = clean_text(
                open_issues.iloc[selected_index].get("Issue ID")
            )

    action_col, _ = st.columns([1.25, 4])
    with action_col:
        if st.button("Open Issue Management", use_container_width=True):
            _navigate_management("Issues")


def _render_pm_progress(snapshot: dict[str, Any]) -> None:
    section_label("THIS MONTH PM PROGRESS")
    planned = len(snapshot["current_plan"])
    completed = snapshot["completed_count"]
    outstanding = snapshot["outstanding_count"]
    ratio = completed / planned if planned else 0.0

    with st.container(border=True):
        metric_col, progress_col, action_col = st.columns([1.15, 3.8, 1.15])
        with metric_col:
            st.metric("Completed", f"{completed} / {planned}")
        with progress_col:
            st.progress(ratio, text=f"{ratio:.0%} complete · {outstanding} outstanding")
            st.caption(
                "The progress bar uses the current month's saved PM plan. "
                "Planning details remain in PM Planning."
            )
        with action_col:
            if st.button("View PM Plan", use_container_width=True):
                _navigate_management("PM Planning")


def _render_quick_aed_view(dataframe: pd.DataFrame) -> None:
    section_label("AED QUICK VIEW")
    search_col, action_col = st.columns([5, 1.25], gap="small")
    with search_col:
        keyword = st.text_input(
            "Quick AED search",
            placeholder="Search serial number, location or postal code",
            label_visibility="collapsed",
            key="management_overview_search",
        )
    with action_col:
        if st.button("Open Master Table", use_container_width=True):
            _navigate_management("AED Master Table")

    filtered = dataframe.copy()
    search_text = clean_text(keyword).casefold()
    if search_text:
        mask = pd.Series(False, index=filtered.index)
        for column in ["Serial Number", "Location", "Postal Code"]:
            if column in filtered.columns:
                mask |= filtered[column].astype(str).str.casefold().str.contains(
                    search_text, regex=False, na=False
                )
        filtered = filtered.loc[mask]

    state = load_unit_state(MAP_UNIT_STATE_FILE)
    definitions = load_status_definitions(MAP_STATUS_FILE)
    if not state.empty:
        filtered = filtered.merge(
            state[["Serial Number", "Status", "Color Override"]],
            on="Serial Number",
            how="left",
        )
    else:
        filtered["Status"] = ""
        filtered["Color Override"] = ""

    colour_lookup = status_color_lookup(definitions)
    filtered["Marker"] = filtered.apply(
        lambda row: (
            f"{COLOR_EMOJI.get(clean_text(row.get('Color Override')).title(), '●')} "
            f"{clean_text(row.get('Color Override')).title()}"
            if clean_text(row.get("Color Override"))
            else f"{COLOR_EMOJI.get(colour_lookup.get(clean_text(row.get('Status')).casefold(), 'Gray'), '●')} "
            f"{clean_text(row.get('Status')) or 'Pending'}"
        ),
        axis=1,
    )
    display = filtered.reindex(
        columns=[
            "Serial Number",
            "Location",
            "Postal Code",
            "Job Type",
            "Next PM Date",
            "Marker",
        ]
    ).head(10).copy()
    display = display.rename(columns={"Job Type": "Service Type"})
    if display.empty:
        st.info("No AED units match the quick search.")
    else:
        st.dataframe(display, use_container_width=True, hide_index=True, height=390)


def _render_management_overview(dataframe: pd.DataFrame) -> None:
    snapshot = _management_snapshot(dataframe)
    _render_management_kpis(snapshot)
    st.markdown("<div style='height:0.35rem'></div>", unsafe_allow_html=True)
    _render_attention_required(snapshot)
    _render_pm_progress(snapshot)
    _render_quick_aed_view(dataframe)


def _render_full_management_workspace(
    dataframe: pd.DataFrame,
    history_file: str | Path,
) -> None:
    table_col, filter_col = st.columns([4.4, 1.35], gap="large")
    with filter_col:
        filters = render_filters(dataframe)

    filtered = aed_service.apply_filters(
        dataframe=dataframe,
        keyword=filters["keyword"],
        model=filters["model"],
        location=filters["location"],
        postal_code=filters["postal_code"],
        lift_lobby=filters["lift_lobby"],
        job_type=filters["job_type"],
        last_done_by=filters["last_done_by"],
        date_ranges=filters["date_ranges"],
        sort_by=filters["sort_by"],
        ascending=filters["ascending"],
    )

    with table_col:
        metric_col1, metric_col2, _ = st.columns([1, 1, 3])
        metric_col1.metric("Total AED Units", len(dataframe))
        metric_col2.metric("Matching Units", len(filtered))
        render_browse_table(filtered)
        st.divider()
        render_full_details_editor(filtered)

    with st.expander("Add or Deactivate AED", expanded=False):
        render_add_and_deactivate(dataframe)
    with st.expander("Audit and Change History", expanded=False):
        render_audit_log(history_file)


def _render_writeback_messages() -> None:
    writeback_notice = st.session_state.pop("aed_writeback_notice", "")
    if writeback_notice:
        st.success(writeback_notice)
    for warning in st.session_state.pop("aed_writeback_warnings", []):
        st.warning(warning)


def _load_management_dataframe() -> pd.DataFrame | None:
    try:
        return get_all_units()
    except Exception as error:
        st.error(f"Failed to load AED data: {error}")
        return None


def render_aed_management(
    aed_data_file: str | Path,
    history_file: str | Path,
) -> None:
    """Render the compact management overview for supervisors and bosses."""

    del aed_data_file, history_file
    page_header(
        "AED Management",
        "Review fleet condition, PM progress and unresolved risk without opening the detailed Master Table.",
        eyebrow="ASSET CONTROL · MANAGEMENT OVERVIEW",
        chip="BOSS OVERVIEW",
    )

    dataframe = _load_management_dataframe()
    if dataframe is None:
        return

    snapshot = _management_snapshot(dataframe)
    _render_management_kpis(snapshot)

    overview_left, overview_right = st.columns([1.45, 1], gap="large")
    with overview_left:
        _render_attention_required(snapshot)
    with overview_right:
        _render_pm_progress(snapshot)

    _render_quick_aed_view(dataframe)


def render_aed_master_table(
    aed_data_file: str | Path,
    history_file: str | Path,
) -> None:
    """Render the complete original Master Table as its own sidebar page."""

    del aed_data_file
    initialise_table_editor_state()

    page_header(
        "AED Master Table",
        "Search, filter, edit several cells directly, review every difference and save safely to the IB List.",
        eyebrow="ASSET CONTROL · DIRECT TABLE EDITING",
        chip="REVIEW BEFORE SAVE",
        capabilities=[
            ("Direct cell editing", "Edit filtered AED rows without opening each unit."),
            ("Review changes", "See every old and new value before confirming."),
            ("Conflict protection", "Same-field conflicts stop the whole transaction."),
        ],
    )

    _render_writeback_messages()

    mode = st.session_state.aed_editor_mode
    if mode == "edit":
        render_edit_mode()
        return
    if mode == "review":
        render_review_mode()
        return
    if mode != "browse":
        clear_table_editor_state()
        st.error("Unknown editor state. The page was reset.")
        return

    dataframe = _load_management_dataframe()
    if dataframe is None:
        return

    # Keep the original Master Table workflow complete and visible on this
    # dedicated page. The boss overview is a separate sidebar route.
    table_col, filter_col = st.columns([4.4, 1.35], gap="large")
    with filter_col:
        filters = render_filters(dataframe)

    filtered = aed_service.apply_filters(
        dataframe=dataframe,
        keyword=filters["keyword"],
        model=filters["model"],
        location=filters["location"],
        postal_code=filters["postal_code"],
        lift_lobby=filters["lift_lobby"],
        job_type=filters["job_type"],
        last_done_by=filters["last_done_by"],
        date_ranges=filters["date_ranges"],
        sort_by=filters["sort_by"],
        ascending=filters["ascending"],
    )

    with table_col:
        metric_col1, metric_col2, _ = st.columns([1, 1, 3])
        metric_col1.metric("Total AED Units", len(dataframe))
        metric_col2.metric("Matching Units", len(filtered))
        render_browse_table(filtered)
        st.divider()
        render_full_details_editor(filtered)

    st.divider()
    render_add_and_deactivate(dataframe)
    render_audit_log(history_file)
