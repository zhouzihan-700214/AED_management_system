"""Sidebar identity, authentication and data-source controls."""
from __future__ import annotations

from pathlib import Path
from typing import Any

import streamlit as st


def render_identity_control(config: Any) -> None:
    with st.sidebar.expander("Operator Identity", expanded=False):
        st.selectbox(
            "Audit user",
            options=list(config.AUDIT_USERS),
            key="audit_user",
            help="Used in audit records; this is separate from Microsoft sign-in.",
        )
        st.caption(f"Session: {st.session_state['session_id'][:8]}")


def render_microsoft_connection_control(config: Any, microsoft_auth_service: Any) -> None:
    if not config.ONEDRIVE_CLOUD_ENABLED:
        return
    status = microsoft_auth_service.get_authentication_status()
    with st.sidebar.expander("Microsoft OneDrive", expanded=True):
        if status.authenticated:
            st.success("Connected")
            st.caption(status.account_name)
            st.caption(config.MICROSOFT_CONFIG.get("onedrive_file_path", ""))
            st.caption(config.MICROSOFT_CONFIG.get("system_state_path", ""))
            if st.button("Sign out", width="stretch", key="microsoft_sign_out"):
                microsoft_auth_service.sign_out()
                st.rerun()
        else:
            st.warning("Not connected")
            st.link_button("Sign in with Microsoft", microsoft_auth_service.build_sign_in_url(), width="stretch")


def render_data_sync_control(
    *,
    config: Any,
    aed_repository: Any,
    excel_lock_service: Any,
    system_state_service: Any,
) -> None:
    status = aed_repository.get_sync_status()
    raw_status = str(status.get("status", ""))
    label = {
        "synced": "Synced",
        "up_to_date": "Up to date",
        "csv_fallback": "CSV fallback",
        "failed": "Needs attention",
        "not_checked": "Not checked",
    }.get(raw_status, raw_status or "Unknown")

    with st.sidebar.expander("Data Source", expanded=False):
        st.caption(f"Excel: {Path(config.EXCEL_FILE).name}")
        st.caption(f"Worksheet: {config.EXCEL_SHEET}")
        if status.get("onedrive_enabled", False):
            st.success("Browser OneDrive mode")
            remote_path = status.get("onedrive_remote_path") or config.MICROSOFT_CONFIG.get("onedrive_file_path", "")
            st.caption(f"Official workbook: {remote_path}")
            state_path = config.MICROSOFT_CONFIG.get("system_state_path", "/AED System/AED_System_State.zip")
            st.caption(f"System records: {state_path}")
        else:
            st.info("Local workbook mode")
            st.caption(str(config.EXCEL_FILE))
        st.caption(f"Status: {label}")

        lock = excel_lock_service.inspect_lock()
        if lock.get("exists"):
            payload = lock.get("payload", {})
            st.warning(
                "Excel operation in progress: "
                f"{payload.get('operation_type', 'Unknown')} by {payload.get('user', 'Unknown')}."
            )
            if lock.get("confirmed_stale") and st.button("Remove confirmed stale lock", width="stretch"):
                if excel_lock_service.remove_confirmed_stale_lock():
                    st.success("Confirmed stale lock removed.")
                    st.rerun()

        if st.button("Refresh now", width="stretch", key="refresh_external_aed_data"):
            result = aed_repository.refresh_from_excel()
            if result.status == "failed":
                st.error(result.message)
                return
            state_result = None
            if config.ONEDRIVE_CLOUD_ENABLED:
                try:
                    state_result = system_state_service.sync_system_state()
                except Exception as error:
                    st.warning(f"System-record refresh needs attention: {error}")
            st.session_state["aed_sync_notice"] = result.message
            if state_result and state_result.message:
                st.session_state["system_state_notice"] = state_result.message
            st.rerun()
