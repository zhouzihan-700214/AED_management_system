"""Operational storage bootstrap and automatic coordinate refresh."""
from __future__ import annotations

from pathlib import Path
from typing import Any

import streamlit as st


def initialise_operational_storage(
    *,
    config: Any,
    aed_repository: Any,
    recovery_service: Any,
    system_state_service: Any,
    pm_service: Any,
    manual_service_storage: Any,
    issue_service: Any,
    allow_remote_refresh: bool = True,
) -> None:
    config.ensure_project_directories()

    if config.ONEDRIVE_CLOUD_ENABLED and not st.session_state.get("_system_state_bootstrapped", False):
        try:
            result = system_state_service.bootstrap_system_state()
            st.session_state["_system_state_bootstrapped"] = True
            if result.changed:
                st.session_state["system_state_notice"] = result.message
        except Exception as error:
            st.session_state["system_state_error"] = str(error)

    if not st.session_state.get("_recovery_checked", False):
        recovery = recovery_service.recover_incomplete_transaction()
        st.session_state["_recovery_checked"] = True
        status = recovery.get("status")
        if status in {"recovered", "cleaned"}:
            st.session_state["recovery_notice"] = recovery.get("message", "")
        elif status == "failed":
            st.session_state["recovery_error"] = recovery.get("message", "")

    if allow_remote_refresh or not Path(config.AED_DATA_FILE).exists():
        aed_repository.ensure_cache_current(force=False)
    pm_service.ensure_pm_storage()
    manual_service_storage.ensure_manual_service_storage()
    issue_service.ensure_issue_storage(config.ISSUE_RECORD_FILE)
    pm_service.ensure_aed_pm_fields(config.AED_DATA_FILE)


def refresh_coordinates_if_source_changed(*, config: Any, coordinate_service: Any) -> None:
    signature_key = "_checked_aed_coordinate_file_signature"
    current_signature = coordinate_service.file_signature(config.AED_DATA_FILE)
    if current_signature is None or st.session_state.get(signature_key) == current_signature:
        return
    try:
        summary = coordinate_service.update_missing_coordinates(config.AED_DATA_FILE, create_backup=False)
        st.session_state[signature_key] = coordinate_service.file_signature(config.AED_DATA_FILE)
        if summary["updated"] > 0:
            st.toast(f"Added or refreshed coordinates for {summary['updated']} AED unit(s).")
        if summary["failed"] > 0:
            st.warning(
                f"{summary['failed']} AED unit(s) still have no valid coordinates. "
                "Check their Postal Code and OneMap credentials."
            )
    except Exception as error:
        st.session_state[signature_key] = current_signature
        st.warning(f"Automatic coordinate update could not finish: {error}")
