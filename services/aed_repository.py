"""Single read/write gateway for AED master data used by every Streamlit page."""
from __future__ import annotations

from datetime import datetime
from typing import Any, Mapping, Sequence

import pandas as pd

from config import AED_CACHE_FILE, EXCEL_FILE, EXCEL_SHEET, SYNC_STATE_FILE
from services.aed_service import load_aed_data
from services.excel_sync_service import SyncResult, get_excel_signature, load_sync_state, sync_excel_to_cache
from services.excel_transaction_service import (
    OperationResult,
    execute_add_unit,
    execute_batch_updates,
    execute_deactivate_unit,
    execute_unit_update,
    load_latest_lifecycle_status,
)
from utils.text_utils import clean_text

_last_result: SyncResult | None = None


def ensure_cache_current(*, force: bool = False) -> SyncResult:
    global _last_result
    try:
        _last_result = sync_excel_to_cache(force=force)
    except Exception as error:
        _last_result = SyncResult(
            status="failed", message=str(error), source_exists=EXCEL_FILE.exists(),
            changed=False, row_count=0,
        )
    return _last_result


def get_all_units(*, refresh: bool = True, include_inactive: bool = False) -> pd.DataFrame:
    """Return the latest validated AED table, hiding inactive units by default."""
    if refresh:
        ensure_cache_current(force=False)
    try:
        dataframe = load_aed_data(AED_CACHE_FILE)
    except Exception:
        if refresh and EXCEL_FILE.exists():
            ensure_cache_current(force=True)
            dataframe = load_aed_data(AED_CACHE_FILE)
        else:
            raise

    if include_inactive or dataframe.empty:
        return dataframe
    lifecycle = load_latest_lifecycle_status()
    if not lifecycle:
        return dataframe
    inactive = {serial for serial, status in lifecycle.items() if status.casefold() != "active"}
    if not inactive:
        return dataframe
    return dataframe[
        ~dataframe["Serial Number"].astype(str).str.strip().str.casefold().isin(inactive)
    ].copy()


def get_unit_by_serial(serial_number: str, *, refresh: bool = True, include_inactive: bool = True) -> pd.Series | None:
    serial = clean_text(serial_number).casefold()
    if not serial:
        return None
    dataframe = get_all_units(refresh=refresh, include_inactive=include_inactive)
    matches = dataframe[dataframe["Serial Number"].astype(str).str.strip().str.casefold().eq(serial)]
    return None if matches.empty else matches.iloc[0].copy()


def refresh_from_excel() -> SyncResult:
    return ensure_cache_current(force=True)


def get_sync_status() -> dict[str, Any]:
    state = load_sync_state(SYNC_STATE_FILE)
    result = _last_result
    signature = get_excel_signature(EXCEL_FILE)
    signature_dict = (
        {"modified_time_ns": signature.modified_time_ns, "size": signature.size}
        if signature is not None else None
    )
    update_available = bool(signature_dict and signature_dict != state.get("last_successful_signature"))
    excel_last_modified = ""
    if signature is not None:
        excel_last_modified = datetime.fromtimestamp(
            signature.modified_time_ns / 1_000_000_000
        ).astimezone().strftime("%d-%m-%Y %H:%M:%S")
    return {
        "excel_file": str(EXCEL_FILE), "excel_sheet": EXCEL_SHEET,
        "cache_file": str(AED_CACHE_FILE), "source_exists": EXCEL_FILE.exists(),
        "status": result.status if result is not None else state.get("sync_status", "not_checked"),
        "message": result.message if result is not None else state.get("sync_message", ""),
        "last_sync_time": state.get("last_sync_time", ""),
        "excel_last_modified": excel_last_modified, "update_available": update_available,
        "row_count": state.get("row_count", 0),
        "warnings": list(result.warnings) if result is not None else list(state.get("warnings", []) or []),
        "signature": signature_dict,
    }


def update_unit(
    *, serial_number: str, changes: Mapping[str, Any], original_values: Mapping[str, Any],
    user: str, source_page: str, session_id: str = "unknown-session",
) -> OperationResult:
    return execute_unit_update(
        serial_number=serial_number, desired_values=changes, original_values=original_values,
        user=user, session_id=session_id, source_page=source_page,
    )


def batch_update_units(
    *, updates: Sequence[Mapping[str, Any]], user: str, source_page: str,
    session_id: str = "unknown-session",
) -> OperationResult:
    return execute_batch_updates(
        updates=updates, user=user, session_id=session_id, source_page=source_page,
    )


def add_unit(*, values: Mapping[str, Any], user: str, source_page: str, session_id: str = "unknown-session") -> OperationResult:
    return execute_add_unit(values=values, user=user, session_id=session_id, source_page=source_page)


def deactivate_unit(*, serial_number: str, user: str, reason: str, source_page: str, session_id: str = "unknown-session") -> OperationResult:
    return execute_deactivate_unit(
        serial_number=serial_number, user=user, session_id=session_id,
        source_page=source_page, reason=reason,
    )
