"""Startup-safe storage bootstrap for manual service records.

This module is deliberately independent from ``unit_profile_service`` so the
application entrypoint can initialise the CSV even when Streamlit Cloud has a
stale cached copy of that larger service module.
"""
from __future__ import annotations

import csv
import os
import uuid
from pathlib import Path

from config import MANUAL_SERVICE_RECORDS_FILE


MANUAL_SERVICE_RECORD_COLUMNS = [
    "Service Record ID",
    "Created At",
    "Created By",
    "AED Serial Number",
    "AED Model",
    "AED Location",
    "Postal Code",
    "Lift Lobby",
    "Service Date",
    "Service Type",
    "Technician",
    "Reference",
    "Status",
    "Details",
    "Master Data Updated",
    "PM Dates Updated",
    "Battery Replaced",
    "Battery History Updated",
    "PM Interval Months Used",
    "Linked Plan ID",
    "Master Operation ID",
    "Source",
]


def ensure_manual_service_storage(
    path: str | Path = MANUAL_SERVICE_RECORDS_FILE,
) -> Path:
    """Create the manual-service CSV and its header when it is missing."""
    record_path = Path(path)
    record_path.parent.mkdir(parents=True, exist_ok=True)
    if not record_path.exists() or record_path.stat().st_size == 0:
        temp = record_path.with_name(f".{record_path.name}.{uuid.uuid4().hex}.tmp")
        with temp.open("w", newline="", encoding="utf-8-sig") as handle:
            writer = csv.DictWriter(handle, fieldnames=MANUAL_SERVICE_RECORD_COLUMNS)
            writer.writeheader()
        os.replace(temp, record_path)
    return record_path
