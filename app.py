"""Streamlit entry point: configuration, shared UI and page routing only."""

from __future__ import annotations

import uuid

import streamlit as st

from config import (
    AED_DATA_FILE,
    EXCEL_FILE,
    EXCEL_SHEET,
    ISSUE_RECORD_FILE,
    AUDIT_USERS,
    MICROSOFT_CONFIG,
    ONEDRIVE_CLOUD_ENABLED,
    ensure_project_directories,
)
from services.aed_repository import (
    ensure_cache_current,
    get_sync_status,
    refresh_from_excel,
)
from services.issue_service import ensure_issue_storage
from services.microsoft_auth_service import (
    build_sign_in_url,
    get_authentication_status,
    handle_auth_callback,
    sign_out,
)
from services.excel_lock_service import inspect_lock, remove_confirmed_stale_lock
from services.recovery_service import recover_incomplete_transaction
from services.pm_service import ensure_aed_pm_fields, ensure_pm_storage
from ui.navigation import consume_map_navigation, render_navigation
from ui.styles import apply_global_styles
from update_missing_coordinates import (
    file_signature,
    update_missing_coordinates,
)
from views.registry import render_current_page


st.set_page_config(
    page_title="AED Operations Control Center",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)




def initialise_user_session() -> None:
    if "session_id" not in st.session_state:
        st.session_state["session_id"] = str(uuid.uuid4())
    if "audit_user" not in st.session_state:
        st.session_state["audit_user"] = AUDIT_USERS[0] if AUDIT_USERS else ""


def render_identity_control() -> None:
    with st.sidebar.expander("Operator Identity", expanded=False):
        st.selectbox(
            "Audit user",
            options=list(AUDIT_USERS),
            key="audit_user",
            help="This identifies the operator in audit records; it is not a login system.",
        )
        st.caption(f"Session: {st.session_state['session_id'][:8]}")


def render_microsoft_sign_in_gate() -> None:
    """Require Microsoft sign-in when browser-only OneDrive mode is configured."""
    if not ONEDRIVE_CLOUD_ENABLED:
        return
    handle_auth_callback()
    status = get_authentication_status()
    if status.authenticated:
        return

    st.title("Connect Microsoft OneDrive")
    st.write(
        "Sign in with the Microsoft account that owns "
        f"`{MICROSOFT_CONFIG.get('onedrive_file_path', '/AED System/IB_list_TEST.xlsx')}`."
    )
    if status.message:
        st.error(status.message)
    st.link_button(
        "Sign in with Microsoft",
        build_sign_in_url(),
        type="primary",
        use_container_width=False,
    )
    st.caption(
        "The system requests Files.ReadWrite only so it can refresh and update the selected OneDrive workbook."
    )
    st.stop()


def render_microsoft_connection_control() -> None:
    if not ONEDRIVE_CLOUD_ENABLED:
        return
    status = get_authentication_status()
    with st.sidebar.expander("Microsoft OneDrive", expanded=True):
        if status.authenticated:
            st.success("Connected")
            st.caption(status.account_name)
            st.caption(MICROSOFT_CONFIG.get("onedrive_file_path", ""))
            if st.button("Sign out", use_container_width=True, key="microsoft_sign_out"):
                sign_out()
                st.rerun()
        else:
            st.warning("Not connected")
            st.link_button(
                "Sign in with Microsoft",
                build_sign_in_url(),
                use_container_width=True,
            )


def initialise_operational_storage() -> None:
    """Create stable CSV headers and the shared PM interval field."""

    try:
        ensure_project_directories()
        if not st.session_state.get("_recovery_checked", False):
            recovery = recover_incomplete_transaction()
            st.session_state["_recovery_checked"] = True
            if recovery.get("status") in {"recovered", "cleaned"}:
                st.session_state["recovery_notice"] = recovery.get("message", "")
            elif recovery.get("status") == "failed":
                st.session_state["recovery_error"] = recovery.get("message", "")
        ensure_cache_current(force=False)
        ensure_pm_storage()
        ensure_issue_storage(ISSUE_RECORD_FILE)
        ensure_aed_pm_fields(AED_DATA_FILE)
    except Exception as error:
        st.warning(f"Operational storage initialisation needs attention: {error}")


def render_data_sync_control() -> None:
    """Show the configured source and provide a deliberate manual refresh."""

    status = get_sync_status()
    status_label = {
        "synced": "Synced",
        "up_to_date": "Up to date",
        "csv_fallback": "CSV fallback",
        "failed": "Needs attention",
        "not_checked": "Not checked",
    }.get(str(status.get("status", "")), str(status.get("status", "Unknown")))

    with st.sidebar.expander("Data Source", expanded=False):
        st.caption(f"Excel: {EXCEL_FILE.name}")
        st.caption(f"Worksheet: {EXCEL_SHEET}")
        if status.get("onedrive_enabled", False):
            st.success("Connected through Microsoft OneDrive API.")
            st.caption(f"OneDrive: {status.get('onedrive_remote_path') or MICROSOFT_CONFIG.get('onedrive_file_path', '')}")
            last_download = str(status.get("onedrive_last_download", "")).strip()
            last_upload = str(status.get("onedrive_last_upload", "")).strip()
            if last_download:
                st.caption(f"Last OneDrive refresh: {last_download}")
            if last_upload:
                st.caption(f"Last OneDrive update: {last_upload}")
        else:
            st.caption(f"Local path: {EXCEL_FILE}")
            st.info("Using the local workbook mode.")
        st.caption(f"Status: {status_label}")

        excel_modified = str(status.get("excel_last_modified", "")).strip()
        if excel_modified:
            st.caption(f"Excel modified: {excel_modified}")

        last_sync = str(status.get("last_sync_time", "")).strip()
        if last_sync:
            st.caption(f"Last synced: {last_sync}")

        if status.get("update_available", False):
            st.warning("A newer Excel version is available.")

        lock_status = inspect_lock()
        if lock_status.get("exists"):
            payload = lock_status.get("payload", {})
            st.warning(
                "Excel operation in progress: "
                f"{payload.get('operation_type', 'Unknown')} by "
                f"{payload.get('user', 'Unknown')}."
            )
            if lock_status.get("confirmed_stale"):
                if st.button("Remove confirmed stale lock", use_container_width=True):
                    if remove_confirmed_stale_lock():
                        st.success("Confirmed stale lock removed.")
                        st.rerun()

        if not status.get("source_exists", False):
            st.info(
                "The Excel workbook has not been downloaded yet. "
                "Click Refresh AED Data after connecting OneDrive."
            )
        elif status.get("status") == "failed":
            st.warning(str(status.get("message", "Excel sync failed.")))

        if st.button(
            "Refresh AED Data",
            use_container_width=True,
            key="refresh_external_aed_data",
        ):
            result = refresh_from_excel()
            if result.status == "failed":
                st.error(result.message)
            elif result.changed:
                st.session_state["aed_sync_notice"] = result.message
                st.session_state["aed_sync_warnings"] = list(result.warnings)
                st.rerun()
            else:
                st.info(result.message)


def sync_coordinates_after_csv_change() -> None:
    """
    Check aed_data.csv once for each detected file version.

    Direct edits made in VS Code bypass the website's normal save function.
    On the next Streamlit rerun, this check refreshes rows with missing
    coordinates or coordinates belonging to an old postal code.
    """

    state_key = "_checked_aed_coordinate_file_signature"
    current_signature = file_signature(AED_DATA_FILE)

    if current_signature is None:
        return

    if st.session_state.get(state_key) == current_signature:
        return

    try:
        summary = update_missing_coordinates(
            AED_DATA_FILE,
            create_backup=False,
        )

        # A successful coordinate save rewrites the CSV, so remember the final
        # signature instead of the signature from before the update.
        st.session_state[state_key] = file_signature(AED_DATA_FILE)

        if summary["updated"] > 0:
            st.toast(
                f"Added or refreshed coordinates for "
                f"{summary['updated']} AED unit(s)."
            )

        if summary["failed"] > 0:
            st.warning(
                f"{summary['failed']} AED unit(s) still have no valid "
                "coordinates. Check their Postal Code and OneMap credentials."
            )

    except Exception as error:
        # Do not repeat the same failing batch on every widget rerun. A new
        # CSV edit changes the signature and allows another attempt.
        st.session_state[state_key] = current_signature
        st.warning(
            "Automatic coordinate update could not finish: "
            f"{error}"
        )


apply_global_styles()
initialise_user_session()
render_microsoft_sign_in_gate()
initialise_operational_storage()
sync_coordinates_after_csv_change()
consume_map_navigation()
render_navigation(ISSUE_RECORD_FILE)
render_microsoft_connection_control()
render_identity_control()
render_data_sync_control()

recovery_notice = st.session_state.pop("recovery_notice", "")
if recovery_notice:
    st.success(recovery_notice)
recovery_error = st.session_state.pop("recovery_error", "")
if recovery_error:
    st.error(recovery_error)

sync_notice = st.session_state.pop("aed_sync_notice", "")
if sync_notice:
    st.success(sync_notice)

for sync_warning in st.session_state.pop("aed_sync_warnings", []):
    st.warning(sync_warning)

render_current_page(st.session_state["page"])
