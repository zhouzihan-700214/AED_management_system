from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import pandas as pd

from services.csv_storage import read_csv_safe
from utils.text_utils import clean_text


SERVICE_HISTORY_COLUMNS = [
    "Service Date",
    "Service Type",
    "Source",
    "Technician",
    "Reference",
    "Status",
    "Details",
]


MANUAL_SERVICE_PREFIX = "[SERVICE]"


def format_manual_service_remark(
    *,
    service_date: str,
    service_type: str,
    technician: str = "",
    reference: str = "",
    status: str = "Completed",
    details: str = "",
) -> str:
    """Create one stable, human-readable service-history line for Remarks."""
    parts = [
        f"{MANUAL_SERVICE_PREFIX} {clean_text(service_date)}",
        f"Type: {clean_text(service_type) or 'Service'}",
    ]
    if clean_text(technician):
        parts.append(f"Technician: {clean_text(technician)}")
    if clean_text(reference):
        parts.append(f"Reference: {clean_text(reference)}")
    if clean_text(status):
        parts.append(f"Status: {clean_text(status)}")
    if clean_text(details):
        compact = re.sub(r"\s+", " ", clean_text(details))
        parts.append(f"Details: {compact}")
    return " | ".join(parts)


def append_manual_service_remark(existing_remarks: str, service_line: str) -> str:
    """Append one service-history line without altering earlier Remarks text."""
    existing = clean_text(existing_remarks)
    line = clean_text(service_line)
    if not existing:
        return line
    if not line or line in existing.splitlines():
        return existing
    return f"{existing.rstrip()}\n{line}"


def _parse_structured_service_remark(piece: str) -> dict[str, str] | None:
    value = clean_text(piece)
    if not value.startswith(MANUAL_SERVICE_PREFIX):
        return None

    chunks = [clean_text(chunk) for chunk in value.split("|") if clean_text(chunk)]
    if not chunks:
        return None

    fields: dict[str, str] = {}
    first = chunks[0].removeprefix(MANUAL_SERVICE_PREFIX).strip()
    for chunk in chunks[1:]:
        if ":" not in chunk:
            continue
        key, raw = chunk.split(":", 1)
        fields[clean_text(key).casefold()] = clean_text(raw)

    return {
        "Service Date": _extract_date(first) or first,
        "Service Type": fields.get("type", "Service"),
        "Source": "Profile Service Record",
        "Technician": fields.get("technician", ""),
        "Reference": fields.get("reference", ""),
        "Status": fields.get("status", "Recorded"),
        "Details": fields.get("details", ""),
    }


_DATE_PATTERNS = [
    re.compile(r"\b\d{1,2}[-/]\d{1,2}[-/]\d{2,4}\b"),
    re.compile(
        r"\b\d{1,2}\s+(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|"
        r"May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|"
        r"Nov(?:ember)?|Dec(?:ember)?)\s+\d{4}\b",
        flags=re.IGNORECASE,
    ),
]


def _matching_rows(
    dataframe: pd.DataFrame,
    serial: str,
    columns: tuple[str, ...],
) -> pd.DataFrame:
    if dataframe.empty:
        return dataframe.copy()

    target = clean_text(serial).casefold()
    if not target:
        return dataframe.iloc[0:0].copy()

    mask = pd.Series(False, index=dataframe.index)
    for column in columns:
        if column in dataframe.columns:
            mask |= dataframe[column].astype(str).str.strip().str.casefold().eq(target)
    return dataframe.loc[mask].copy()


def _extract_date(text: str) -> str:
    value = clean_text(text)
    for pattern in _DATE_PATTERNS:
        match = pattern.search(value)
        if match:
            parsed = pd.to_datetime(match.group(0), dayfirst=True, errors="coerce")
            if not pd.isna(parsed):
                return parsed.strftime("%d-%m-%Y")
    return ""


def _extract_reference(text: str) -> str:
    value = clean_text(text)
    match = re.search(r"\be[- ]?SR\s*[-:]?\s*\d+\b", value, flags=re.IGNORECASE)
    if not match:
        return ""
    return re.sub(r"\s+", "", match.group(0)).replace("ESR", "e-SR")


def _infer_service_type(text: str) -> str:
    value = clean_text(text).casefold()
    if "commission" in value:
        return "Commissioning"
    if "battery" in value and "glass" in value:
        return "PM + Battery + Glass"
    if "battery" in value:
        return "PM + Battery"
    if "glass" in value:
        return "PM + Glass"
    if "repair" in value:
        return "Repair"
    if "incoming" in value:
        return "Incoming Check"
    if "outgoing" in value:
        return "Outgoing Check"
    if "activation" in value:
        return "Activation"
    if "pm" in value or "preventive" in value:
        return "PM"
    return "Legacy Service"


def _legacy_remark_rows(master_row: pd.Series) -> list[dict[str, str]]:
    remarks = clean_text(master_row.get("Remarks"))
    if not remarks:
        return []

    pieces = [
        clean_text(piece).strip(" ,-/")
        for piece in re.split(
            r"\s*/\s*|[\r\n]+|\s*;\s*|"
            r"(?=\bPM\s+(?:completed|done)\b)|"
            r"(?=\bCommissioning\b)|(?=\bRepair(?:ed)?\b)|"
            r"(?=\bIncoming Check\b)|(?=\bOutgoing Check\b)",
            remarks,
            flags=re.IGNORECASE,
        )
        if clean_text(piece).strip(" ,-/")
    ]
    if not pieces:
        pieces = [remarks]

    rows: list[dict[str, str]] = []
    for piece in pieces:
        structured = _parse_structured_service_remark(piece)
        if structured is not None:
            rows.append(structured)
            continue
        rows.append(
            {
                "Service Date": _extract_date(piece),
                "Service Type": _infer_service_type(piece),
                "Source": "IB List Remarks",
                "Technician": "",
                "Reference": _extract_reference(piece),
                "Status": "Historical",
                "Details": piece,
            }
        )
    return rows


def _pm_response_rows(pm_responses: pd.DataFrame, serial: str) -> list[dict[str, str]]:
    matches = _matching_rows(
        pm_responses,
        serial,
        ("AED Serial Number", "Original Serial Number"),
    )
    rows: list[dict[str, str]] = []
    for _, row in matches.iterrows():
        detail_parts = []
        for label, column in [
            ("Battery replaced", "Battery Replaced"),
            ("Cabinet", "Cabinet Inspection"),
            ("Alarm", "Cabinet Alarm"),
            ("Self test", "Self Test Result"),
            ("Final check", "Final Check"),
        ]:
            value = clean_text(row.get(column))
            if value:
                detail_parts.append(f"{label}: {value}")

        rows.append(
            {
                "Service Date": clean_text(row.get("Service Date"))
                or clean_text(row.get("Submitted At")),
                "Service Type": clean_text(row.get("Service Type")) or "PM",
                "Source": "PM Checklist",
                "Technician": clean_text(row.get("Technician"))
                or clean_text(row.get("Submitted By")),
                "Reference": clean_text(row.get("PM Response ID"))
                or clean_text(row.get("Operation ID")),
                "Status": clean_text(row.get("Submission Status")) or "Submitted",
                "Details": " · ".join(detail_parts),
            }
        )
    return rows


def _master_latest_service_row(master_row: pd.Series) -> list[dict[str, str]]:
    service_date = clean_text(master_row.get("PM Completed Date"))
    service_type = clean_text(master_row.get("Job Type"))
    reference = clean_text(master_row.get("Service Report e-SR"))
    technician = clean_text(master_row.get("Last Done By"))
    if not any([service_date, service_type, reference, technician]):
        return []

    return [
        {
            "Service Date": service_date,
            "Service Type": service_type or "Latest Service",
            "Source": "IB List Current Record",
            "Technician": technician,
            "Reference": reference,
            "Status": "Recorded",
            "Details": "Latest service information currently stored in the IB List.",
        }
    ]


def _resolution_rows(
    issues: pd.DataFrame,
    resolutions: pd.DataFrame,
    serial: str,
) -> list[dict[str, str]]:
    issue_matches = _matching_rows(issues, serial, ("Serial Number",))
    if issue_matches.empty or resolutions.empty or "Issue ID" not in resolutions.columns:
        return []

    issue_lookup = {
        clean_text(row.get("Issue ID")): row
        for _, row in issue_matches.iterrows()
        if clean_text(row.get("Issue ID"))
    }
    if not issue_lookup:
        return []

    matches = resolutions[
        resolutions["Issue ID"].astype(str).str.strip().isin(issue_lookup)
    ].copy()
    rows: list[dict[str, str]] = []
    for _, row in matches.iterrows():
        issue_id = clean_text(row.get("Issue ID"))
        issue = issue_lookup.get(issue_id, pd.Series(dtype=object))
        details = []
        for label, column in [
            ("Issue", "Issue Type"),
            ("Action", "Action Taken"),
            ("Parts", "Parts Replaced"),
            ("Test", "Test Performed"),
            ("Result", "Test Result"),
            ("Notes", "Resolution Notes"),
        ]:
            source_row = issue if column == "Issue Type" else row
            value = clean_text(source_row.get(column))
            if value:
                details.append(f"{label}: {value}")

        rows.append(
            {
                "Service Date": clean_text(row.get("Submitted At"))
                or clean_text(issue.get("Resolved At"))
                or clean_text(issue.get("Closed At")),
                "Service Type": "Issue Resolution",
                "Source": "Issue Management",
                "Technician": clean_text(row.get("Submitted By"))
                or clean_text(issue.get("Resolved By")),
                "Reference": clean_text(row.get("Submission ID")) or issue_id,
                "Status": clean_text(row.get("Verification Result"))
                or clean_text(issue.get("Status")),
                "Details": " · ".join(details),
            }
        )
    return rows


def _sort_service_history(dataframe: pd.DataFrame) -> pd.DataFrame:
    if dataframe.empty:
        return dataframe

    parsed = pd.to_datetime(dataframe["Service Date"], dayfirst=True, errors="coerce")
    dataframe = dataframe.assign(_sort_date=parsed)
    dataframe = dataframe.sort_values(
        ["_sort_date", "Source"],
        ascending=[False, True],
        na_position="last",
    )
    return dataframe.drop(columns=["_sort_date"]).reset_index(drop=True)


def build_service_history(
    master_row: pd.Series,
    serial: str,
    *,
    pm_responses_file: str | Path,
    issue_record_file: str | Path,
    resolution_file: str | Path,
) -> pd.DataFrame:
    pm_responses = read_csv_safe(pm_responses_file)
    issues = read_csv_safe(issue_record_file)
    resolutions = read_csv_safe(resolution_file)

    rows: list[dict[str, str]] = []
    rows.extend(_pm_response_rows(pm_responses, serial))
    rows.extend(_resolution_rows(issues, resolutions, serial))
    rows.extend(_master_latest_service_row(master_row))
    rows.extend(_legacy_remark_rows(master_row))

    if not rows:
        return pd.DataFrame(columns=SERVICE_HISTORY_COLUMNS)

    history = pd.DataFrame(rows, columns=SERVICE_HISTORY_COLUMNS).fillna("")
    history = history.drop_duplicates(
        subset=["Service Date", "Service Type", "Reference", "Details"],
        keep="first",
    )
    return _sort_service_history(history)


def load_unit_issues(
    serial: str,
    *,
    issue_record_file: str | Path,
) -> pd.DataFrame:
    issues = read_csv_safe(issue_record_file)
    matches = _matching_rows(issues, serial, ("Serial Number",))
    if matches.empty:
        return matches

    if "Reported At" in matches.columns:
        parsed = pd.to_datetime(
            matches["Reported At"],
            dayfirst=True,
            errors="coerce",
        )
        matches = matches.assign(_sort_date=parsed).sort_values(
            "_sort_date", ascending=False, na_position="last"
        ).drop(columns=["_sort_date"])
    return matches.reset_index(drop=True)
