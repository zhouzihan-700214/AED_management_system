from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Any

import pandas as pd
import streamlit as st

from services.aed_repository import get_all_units
from ui.components import page_header
from utils.text_utils import clean_text


PRIORITY_COLUMNS = [
    "Service Date",
    "Technician",
    "Service Type",
    "AED Serial Number",
    "AED Model",
    "AED Location",
    "Postal Code",
    "Lift Lobby",
    "Battery Replaced",
    "Submitted At",
]

CHECKLIST_FIELDS = [
    (1, "Service Date", "Service Date"),
    (2, "Technician", "Technician"),
    (3, "Service Type", "Service Type"),
    (4, "Customer / Location", "Customer / Location"),
    (5, "Postal Code", "Postal Code"),
    (6, "Lift Lobby", "Lift Lobby"),
    (7, "Is this a loaner unit?", "Loaner Unit"),
    (8, "Cabinet Inspection", "Cabinet Inspection"),
    (9, "Cabinet Alarm", "Cabinet Alarm"),
    (10, "AED Serial Number", "AED Serial Number"),
    (11, "AED Physical Condition", "AED Physical Condition"),
    (12, "Self Test Result", "Self Test Result"),
    (13, "Battery Expiry Date", "Battery Expiry Date"),
    (14, "AED Cover", "AED Cover"),
    (15, "Adult Pads Expiry Date", "Adult Pads Expiry Date"),
    (16, "Adult Pads Lot Number", "Adult Pads Lot Number"),
    (
        17,
        "Adult Pads Within Expiry Date",
        "Adult Pads Within Expiry Date",
    ),
    (18, "Pediatric Pads Expiry Date", "Pediatric Pads Expiry Date"),
    (19, "Pediatric Pads Lot Number", "Pediatric Pads Lot Number"),
    (
        20,
        "Pediatric Pads Within Expiry Date",
        "Pediatric Pads Within Expiry Date",
    ),
    (21, "AED Signage", "AED Signage"),
    (22, "Final Check", "Final Check"),
]

SUPPLEMENTARY_FIELDS = [
    "PM Response ID",
    "Original Serial Number",
    "AED Model",
    "AED Location",
    "Battery Replaced",
    "Master Data Updated",
    "Submitted At",
]


SERVICE_RECORD_FILTER_KEYS = {
    "month": "service_records_month",
    "technician": "service_records_technician",
    "service_type": "service_records_service_type",
    "battery_replaced": "service_records_battery",
    "model": "service_records_model",
}

SERVICE_RECORD_FILTER_COLUMNS = {
    "technician": "Technician",
    "service_type": "Service Type",
    "battery_replaced": "Battery Replaced",
    "model": "AED Model",
}


def parse_service_date_series(series: pd.Series) -> pd.Series:
    return pd.to_datetime(
        series.astype(str).str.strip(),
        format="%d-%m-%Y",
        errors="coerce",
    )


def parse_submitted_at_series(series: pd.Series) -> pd.Series:
    return pd.to_datetime(
        series.astype(str).str.strip(),
        format="%d-%m-%Y %H:%M:%S",
        errors="coerce",
    )


def load_aed_lookup(aed_csv_file: str | Path | None = None) -> pd.DataFrame:
    del aed_csv_file
    dataframe = get_all_units().copy()

    for column in ["Serial Number", "Model", "Location"]:
        if column not in dataframe.columns:
            dataframe[column] = ""

        dataframe[column] = (
            dataframe[column]
            .astype(str)
            .str.strip()
        )

    return dataframe[
        ["Serial Number", "Model", "Location"]
    ].copy()


def create_lookup_map(
    dataframe: pd.DataFrame,
    value_column: str,
) -> dict[str, str]:
    lookup: dict[str, str] = {}

    for _, row in dataframe.iterrows():
        serial = clean_text(row.get("Serial Number", ""))
        value = clean_text(row.get(value_column, ""))

        if serial and serial.casefold() not in lookup:
            lookup[serial.casefold()] = value

    return lookup


def load_service_records(
    response_csv_file: str | Path,
    aed_csv_file: str | Path,
) -> pd.DataFrame:
    response_path = Path(response_csv_file)

    if not response_path.exists():
        return pd.DataFrame()

    records = pd.read_csv(
        response_path,
        dtype=str,
        keep_default_na=False,
        encoding="utf-8-sig",
    ).fillna("")

    required_columns = {
        "Service Date",
        "Technician",
        "Service Type",
        "Postal Code",
        "Lift Lobby",
        "AED Serial Number",
        "Battery Replaced",
        "Adult Pads Lot Number",
        "Pediatric Pads Lot Number",
        "AED Location",
        "Submitted At",
        "PM Response ID",
        "Original Serial Number",
    }

    for column in required_columns:
        if column not in records.columns:
            records[column] = ""

    if "AED Model" not in records.columns:
        records["AED Model"] = ""

    aed_lookup = load_aed_lookup(aed_csv_file)
    model_lookup = create_lookup_map(aed_lookup, "Model")
    location_lookup = create_lookup_map(aed_lookup, "Location")

    for row_index, row in records.iterrows():
        current_serial = clean_text(
            row.get("AED Serial Number", "")
        )
        original_serial = clean_text(
            row.get("Original Serial Number", "")
        )

        serial_keys = [
            serial.casefold()
            for serial in [current_serial, original_serial]
            if serial
        ]

        if not clean_text(row.get("AED Model", "")):
            for serial_key in serial_keys:
                model = model_lookup.get(serial_key, "")
                if model:
                    records.at[row_index, "AED Model"] = model
                    break

        if not clean_text(row.get("AED Location", "")):
            for serial_key in serial_keys:
                location = location_lookup.get(serial_key, "")
                if location:
                    records.at[row_index, "AED Location"] = location
                    break

    records["_Service Date Parsed"] = parse_service_date_series(
        records["Service Date"]
    )
    records["_Submitted At Parsed"] = parse_submitted_at_series(
        records["Submitted At"]
    )
    records["_Original Row Index"] = records.index

    return records


def unique_values(
    dataframe: pd.DataFrame,
    column: str,
) -> list[str]:
    if column not in dataframe.columns:
        return []

    values = {
        clean_text(value)
        for value in dataframe[column].tolist()
        if clean_text(value)
    }

    return sorted(values, key=str.casefold)


def available_months(
    dataframe: pd.DataFrame,
) -> list[tuple[str, str]]:
    if "_Service Date Parsed" not in dataframe.columns:
        return []

    valid_dates = dataframe["_Service Date Parsed"].dropna()

    month_values = sorted(
        {
            timestamp.strftime("%Y-%m")
            for timestamp in valid_dates
        },
        reverse=True,
    )

    return [
        (
            month_value,
            pd.Timestamp(
                f"{month_value}-01"
            ).strftime("%B %Y"),
        )
        for month_value in month_values
    ]


def apply_filters(
    dataframe: pd.DataFrame,
    keyword: str,
    start_date: date | None,
    end_date: date | None,
    selected_month: str,
    technicians: list[str],
    service_types: list[str],
    battery_replaced_values: list[str],
    models: list[str],
) -> pd.DataFrame:
    filtered = dataframe.copy()

    keyword_text = clean_text(keyword).casefold()

    if keyword_text:
        keyword_columns = [
            "AED Serial Number",
            "AED Location",
            "Postal Code",
            "Lift Lobby",
            "Adult Pads Lot Number",
            "Pediatric Pads Lot Number",
        ]

        keyword_mask = pd.Series(
            False,
            index=filtered.index,
        )

        for column in keyword_columns:
            if column not in filtered.columns:
                continue

            keyword_mask |= (
                filtered[column]
                .astype(str)
                .str.casefold()
                .str.contains(
                    keyword_text,
                    regex=False,
                    na=False,
                )
            )

        filtered = filtered.loc[keyword_mask]

    if start_date is not None:
        filtered = filtered.loc[
            filtered["_Service Date Parsed"]
            >= pd.Timestamp(start_date)
        ]

    if end_date is not None:
        filtered = filtered.loc[
            filtered["_Service Date Parsed"]
            <= pd.Timestamp(end_date)
        ]

    if selected_month:
        filtered = filtered.loc[
            filtered["_Service Date Parsed"]
            .dt.strftime("%Y-%m")
            .eq(selected_month)
        ]

    filter_pairs = [
        ("Technician", technicians),
        ("Service Type", service_types),
        ("Battery Replaced", battery_replaced_values),
        ("AED Model", models),
    ]

    for column, selected_values in filter_pairs:
        if selected_values:
            filtered = filtered.loc[
                filtered[column]
                .astype(str)
                .isin(selected_values)
            ]

    filtered = filtered.sort_values(
        by=[
            "_Service Date Parsed",
            "_Submitted At Parsed",
        ],
        ascending=[False, False],
        na_position="last",
    )

    return filtered


def _service_record_filter_selections_from_state() -> dict[str, list[str]]:
    """Return the current Service Records filter selections as lists."""

    selections: dict[str, list[str]] = {}

    for filter_name, session_key in SERVICE_RECORD_FILTER_KEYS.items():
        value = st.session_state.get(session_key, "" if filter_name == "month" else [])

        if isinstance(value, (list, tuple, set)):
            selections[filter_name] = [
                clean_text(item)
                for item in value
                if clean_text(item)
            ]
        elif clean_text(value):
            selections[filter_name] = [clean_text(value)]
        else:
            selections[filter_name] = []

    return selections


def _set_service_record_filter_state(
    filter_name: str,
    values: list[str],
) -> None:
    """Write a normalised filter value back to Streamlit session state."""

    session_key = SERVICE_RECORD_FILTER_KEYS[filter_name]

    if filter_name == "month":
        st.session_state[session_key] = values[0] if values else ""
    else:
        st.session_state[session_key] = values


def _mark_service_record_filter_changed(filter_name: str) -> None:
    """Remember the newest choice so it wins over incompatible older choices."""

    st.session_state["service_records_last_changed_filter"] = filter_name


def linked_service_record_options(
    dataframe: pd.DataFrame,
    target_filter: str,
    keyword: str,
    start_date: date | None,
    end_date: date | None,
    selections: dict[str, list[str]] | None = None,
) -> list[str]:
    """Return one filter's options after applying every other active filter."""

    if target_filter not in SERVICE_RECORD_FILTER_KEYS:
        valid_names = ", ".join(SERVICE_RECORD_FILTER_KEYS)
        raise ValueError(
            f"Unknown Service Records filter '{target_filter}'. "
            f"Expected one of: {valid_names}."
        )

    active = {
        name: list(values or [])
        for name, values in (selections or {}).items()
        if name in SERVICE_RECORD_FILTER_KEYS
    }

    for name in SERVICE_RECORD_FILTER_KEYS:
        active.setdefault(name, [])

    # Exclude the target itself. This keeps all values that are compatible
    # with the other filters and allows a multiselect to retain several values.
    active[target_filter] = []

    selected_month = active["month"][0] if active["month"] else ""

    filtered = apply_filters(
        dataframe=dataframe,
        keyword=keyword,
        start_date=start_date,
        end_date=end_date,
        selected_month=selected_month,
        technicians=active["technician"],
        service_types=active["service_type"],
        battery_replaced_values=active["battery_replaced"],
        models=active["model"],
    )

    if target_filter == "month":
        return [
            month_value
            for month_value, _ in available_months(filtered)
        ]

    return unique_values(
        filtered,
        SERVICE_RECORD_FILTER_COLUMNS[target_filter],
    )


def _normalise_service_record_filter_state(
    dataframe: pd.DataFrame,
    keyword: str,
    start_date: date | None,
    end_date: date | None,
) -> None:
    """Clear choices that no longer match the other Service Records filters."""

    selections = _service_record_filter_selections_from_state()
    last_changed = st.session_state.get(
        "service_records_last_changed_filter"
    )

    # First validate the newest choice against the keyword/date scope alone.
    # This preserves the user's newest action and clears incompatible older
    # choices from other filters instead of immediately undoing the new choice.
    if last_changed in SERVICE_RECORD_FILTER_KEYS:
        empty_selections = {
            name: []
            for name in SERVICE_RECORD_FILTER_KEYS
        }
        base_options = linked_service_record_options(
            dataframe=dataframe,
            target_filter=last_changed,
            keyword=keyword,
            start_date=start_date,
            end_date=end_date,
            selections=empty_selections,
        )
        allowed = set(base_options)
        valid = [
            value
            for value in selections[last_changed]
            if value in allowed
        ]

        if valid != selections[last_changed]:
            selections[last_changed] = valid
            _set_service_record_filter_state(last_changed, valid)

    order = [
        name
        for name in SERVICE_RECORD_FILTER_KEYS
        if name != last_changed
    ]

    if last_changed in SERVICE_RECORD_FILTER_KEYS:
        order.append(last_changed)

    # Several passes settle chains such as Model -> Technician -> Month.
    for _ in range(len(SERVICE_RECORD_FILTER_KEYS) + 1):
        changed = False

        for filter_name in order:
            options = linked_service_record_options(
                dataframe=dataframe,
                target_filter=filter_name,
                keyword=keyword,
                start_date=start_date,
                end_date=end_date,
                selections=selections,
            )
            allowed = set(options)
            valid = [
                value
                for value in selections[filter_name]
                if value in allowed
            ]

            # Service Month is a single-select filter.
            if filter_name == "month":
                valid = valid[:1]

            if valid != selections[filter_name]:
                selections[filter_name] = valid
                _set_service_record_filter_state(filter_name, valid)
                changed = True

        if not changed:
            break


def reset_service_record_filters() -> None:
    """Restore every Service Records filter to its initial value."""

    defaults: dict[str, Any] = {
        "service_records_keyword": "",
        "service_records_date_from": None,
        "service_records_date_to": None,
        "service_records_month": "",
        "service_records_technician": [],
        "service_records_service_type": [],
        "service_records_battery": [],
        "service_records_model": [],
        "service_records_last_changed_filter": None,
    }

    for key, value in defaults.items():
        st.session_state[key] = value

    # The old selected detail record may not exist after the filters reset.
    st.session_state.pop("selected_service_record", None)


def record_label(
    dataframe: pd.DataFrame,
    row_index: int,
) -> str:
    row = dataframe.loc[row_index]

    service_date = (
        clean_text(row.get("Service Date", ""))
        or "No service date"
    )
    serial = (
        clean_text(row.get("AED Serial Number", ""))
        or "No serial"
    )
    location = (
        clean_text(row.get("AED Location", ""))
        or "No location"
    )
    technician = (
        clean_text(row.get("Technician", ""))
        or "No technician"
    )

    return (
        f"{service_date} | {serial} | "
        f"{location} | {technician}"
    )


def export_dataframe(
    dataframe: pd.DataFrame,
) -> bytes:
    helper_columns = [
        "_Service Date Parsed",
        "_Submitted At Parsed",
        "_Original Row Index",
    ]

    export_columns = [
        column
        for column in dataframe.columns
        if column not in helper_columns
    ]

    return dataframe[
        export_columns
    ].to_csv(
        index=False,
        encoding="utf-8-sig",
    ).encode("utf-8-sig")


def render_record_details(row: pd.Series) -> None:
    st.subheader("Service Record Details")
    st.caption(
        "This is a view-only record saved from PM Checklist."
    )

    general_left, general_right = st.columns(2)

    with general_left:
        st.markdown(
            f"**PM Response ID:** "
            f"{clean_text(row.get('PM Response ID', '')) or '—'}"
        )
        st.markdown(
            f"**Service Date:** "
            f"{clean_text(row.get('Service Date', '')) or '—'}"
        )
        st.markdown(
            f"**Technician:** "
            f"{clean_text(row.get('Technician', '')) or '—'}"
        )
        st.markdown(
            f"**Service Type:** "
            f"{clean_text(row.get('Service Type', '')) or '—'}"
        )
        st.markdown(
            f"**Submitted At:** "
            f"{clean_text(row.get('Submitted At', '')) or '—'}"
        )

    with general_right:
        st.markdown(
            f"**AED Serial Number:** "
            f"{clean_text(row.get('AED Serial Number', '')) or '—'}"
        )
        st.markdown(
            f"**AED Model:** "
            f"{clean_text(row.get('AED Model', '')) or '—'}"
        )
        st.markdown(
            f"**AED Location:** "
            f"{clean_text(row.get('AED Location', '')) or '—'}"
        )
        st.markdown(
            f"**Battery Replaced:** "
            f"{clean_text(row.get('Battery Replaced', '')) or '—'}"
        )
        st.markdown(
            f"**Master Data Updated:** "
            f"{clean_text(row.get('Master Data Updated', '')) or '—'}"
        )

    checklist_rows = []

    for item_number, label, column in CHECKLIST_FIELDS:
        checklist_rows.append(
            {
                "Item": item_number,
                "Checklist Field": label,
                "Recorded Response": (
                    clean_text(row.get(column, ""))
                    or "—"
                ),
            }
        )

    checklist_dataframe = pd.DataFrame(checklist_rows)

    st.markdown("#### Full Checklist")
    st.dataframe(
        checklist_dataframe,
        width="stretch",
        hide_index=True,
    )

    with st.expander("Additional Saved Information"):
        additional_rows = []

        for field in SUPPLEMENTARY_FIELDS:
            additional_rows.append(
                {
                    "Field": field,
                    "Value": (
                        clean_text(row.get(field, ""))
                        or "—"
                    ),
                }
            )

        st.dataframe(
            pd.DataFrame(additional_rows),
            width="stretch",
            hide_index=True,
        )


def render_service_records_page(
    response_csv_file: str | Path = "pm_responses.csv",
    aed_csv_file: str | Path = "aed_data.csv",
) -> None:
    page_header(
        "Service Records",
        "Search, filter, review and export completed PM Checklist submissions without changing the original record.",
        eyebrow="MAINTENANCE · TRACE",
        chip="SUBMISSION HISTORY",
        capabilities=[
            ("Linked filters", "Narrow records by service date, technician, model and checklist result."),
            ("Record detail", "Open one submission and review every captured inspection field."),
            ("Export view", "Download the currently filtered result for reporting or follow-up."),
        ],
    )

    try:
        records = load_service_records(
            response_csv_file=response_csv_file,
            aed_csv_file=aed_csv_file,
        )
    except pd.errors.EmptyDataError:
        st.info("pm_responses.csv is currently empty.")
        return
    except Exception as error:
        st.error(f"Failed to load Service Records: {error}")
        return

    if records.empty:
        st.info(
            "No Service Records have been submitted yet. "
            "A record will appear here after PM Checklist is submitted."
        )
        return

    table_column, filter_column = st.columns(
        [4.35, 1.45],
        gap="large",
    )

    with filter_column:
        st.markdown("### Filters")

        keyword = st.text_input(
            "Keyword Search",
            placeholder=(
                "Serial, location, postal code, "
                "lift lobby or pads lot number"
            ),
            key="service_records_keyword",
        )

        with st.expander("Service Date", expanded=True):
            start_column, end_column = st.columns(2)

            with start_column:
                start_date = st.date_input(
                    "From",
                    value=None,
                    format="DD-MM-YYYY",
                    key="service_records_date_from",
                )

            with end_column:
                end_date = st.date_input(
                    "To",
                    value=None,
                    format="DD-MM-YYYY",
                    key="service_records_date_to",
                )

            _normalise_service_record_filter_state(
                dataframe=records,
                keyword=keyword,
                start_date=start_date,
                end_date=end_date,
            )
            selections = _service_record_filter_selections_from_state()

            dynamic_month_values = linked_service_record_options(
                dataframe=records,
                target_filter="month",
                keyword=keyword,
                start_date=start_date,
                end_date=end_date,
                selections=selections,
            )
            all_month_labels = dict(available_months(records))
            month_labels = {
                "": "All months",
                **{
                    month_value: all_month_labels.get(
                        month_value,
                        month_value,
                    )
                    for month_value in dynamic_month_values
                },
            }

            selected_month = st.selectbox(
                "Service Month",
                options=list(month_labels.keys()),
                format_func=lambda value: month_labels[value],
                key="service_records_month",
                on_change=_mark_service_record_filter_changed,
                args=("month",),
            )
            selections["month"] = (
                [selected_month]
                if selected_month
                else []
            )

        with st.expander("Record Filters", expanded=True):
            selected_filters: dict[str, list[str]] = {}
            filter_labels = {
                "technician": "Technician",
                "service_type": "Service Type",
                "battery_replaced": "Battery Replaced",
                "model": "Model",
            }

            for filter_name, label in filter_labels.items():
                options = linked_service_record_options(
                    dataframe=records,
                    target_filter=filter_name,
                    keyword=keyword,
                    start_date=start_date,
                    end_date=end_date,
                    selections=selections,
                )

                selected_filters[filter_name] = st.multiselect(
                    label,
                    options=options,
                    key=SERVICE_RECORD_FILTER_KEYS[filter_name],
                    on_change=_mark_service_record_filter_changed,
                    args=(filter_name,),
                )
                selections[filter_name] = selected_filters[filter_name]

            technicians = selected_filters["technician"]
            service_types = selected_filters["service_type"]
            battery_replaced_values = selected_filters[
                "battery_replaced"
            ]
            models = selected_filters["model"]

        st.button(
            "Reset Filters",
            width="stretch",
            key="reset_service_record_filters_button",
            on_click=reset_service_record_filters,
        )

    filtered = apply_filters(
        dataframe=records,
        keyword=keyword,
        start_date=start_date,
        end_date=end_date,
        selected_month=selected_month,
        technicians=technicians,
        service_types=service_types,
        battery_replaced_values=battery_replaced_values,
        models=models,
    )

    with table_column:
        metric_left, metric_right, metric_space = st.columns(
            [1, 1, 3]
        )
        metric_left.metric(
            "Total Records",
            len(records),
        )
        metric_right.metric(
            "Matching Records",
            len(filtered),
        )

        display_columns = [
            column
            for column in PRIORITY_COLUMNS
            if column in filtered.columns
        ]

        st.dataframe(
            filtered[display_columns],
            width="stretch",
            hide_index=True,
            height=430,
        )

        export_name = (
            f"service_records_"
            f"{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.csv"
        )

        st.download_button(
            "Export Filtered Records",
            data=export_dataframe(filtered),
            file_name=export_name,
            mime="text/csv",
            disabled=filtered.empty,
            width="content",
        )

    st.divider()

    if filtered.empty:
        st.info(
            "No Service Records match the current filters."
        )
        return

    valid_record_indices = filtered.index.tolist()
    if st.session_state.get("selected_service_record") not in valid_record_indices:
        st.session_state.pop("selected_service_record", None)

    selected_index = st.selectbox(
        "Select a Service Record",
        options=valid_record_indices,
        format_func=lambda row_index: record_label(
            filtered,
            row_index,
        ),
        key="selected_service_record",
    )

    render_record_details(
        filtered.loc[selected_index]
    )
