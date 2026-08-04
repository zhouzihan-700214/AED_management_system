"""Microsoft sign-in gate, periodic cloud refresh and user notices."""
from __future__ import annotations

from typing import Any, Callable

import streamlit as st

AUTO_REFRESH_INTERVAL = "10s"


def render_microsoft_sign_in_gate(config: Any, microsoft_auth_service: Any) -> None:
    if not config.ONEDRIVE_CLOUD_ENABLED:
        return
    microsoft_auth_service.handle_auth_callback()
    status = microsoft_auth_service.get_authentication_status()
    if status.authenticated:
        return
    st.title("Connect Microsoft OneDrive")
    remote_path = config.MICROSOFT_CONFIG.get("onedrive_file_path", "/AED System/IB_list_TEST.xlsx")
    st.write(f"Sign in with the Microsoft account that owns `{remote_path}`.")
    if status.message:
        st.error(status.message)
    st.link_button(
        "Sign in with Microsoft",
        microsoft_auth_service.build_sign_in_url(),
        type="primary",
        width="content",
    )
    st.caption(
        "The system uses delegated Files.ReadWrite permission to read and update "
        "the selected workbook and a separate system-state archive."
    )
    st.stop()


def make_auto_refresh(
    *,
    config: Any,
    microsoft_auth_service: Any,
    aed_repository: Any,
    system_state_service: Any,
    user_is_editing: Callable[[], bool],
):
    @st.fragment(run_every=AUTO_REFRESH_INTERVAL)
    def auto_refresh_cloud_data() -> None:
        if not config.ONEDRIVE_CLOUD_ENABLED:
            return
        if not microsoft_auth_service.get_authentication_status().authenticated:
            return

        should_rerun = False
        editing = user_is_editing()
        if editing:
            st.session_state.pop("aed_auto_sync_error", None)
        else:
            excel_result = aed_repository.ensure_cache_current(force=False)
            if excel_result.status == "failed":
                st.session_state["aed_auto_sync_error"] = excel_result.message
            else:
                st.session_state.pop("aed_auto_sync_error", None)
                if excel_result.changed:
                    st.session_state["aed_sync_notice"] = (
                        "A newer OneDrive Excel version was detected and loaded automatically."
                    )
                    should_rerun = True

        try:
            state_result = system_state_service.sync_system_state(allow_download=not editing)
            if state_result.status == "conflict":
                st.session_state["system_state_error"] = state_result.message
            elif state_result.status == "deferred":
                st.session_state.pop("system_state_error", None)
            else:
                st.session_state.pop("system_state_error", None)
                if state_result.downloaded:
                    st.session_state["system_state_notice"] = state_result.message
                    should_rerun = True
        except Exception as error:
            st.session_state["system_state_error"] = str(error)

        if should_rerun:
            st.rerun()
    return auto_refresh_cloud_data


def render_notices() -> None:
    transient = {
        "recovery_notice": st.success,
        "recovery_error": st.error,
        "aed_sync_notice": st.success,
        "system_state_notice": st.success,
    }
    persistent = {
        "system_state_error": st.error,
        "aed_auto_sync_error": st.warning,
    }
    for key, renderer in transient.items():
        message = st.session_state.pop(key, "")
        if message:
            renderer(message)
    for key, renderer in persistent.items():
        message = st.session_state.get(key, "")
        if message:
            renderer(message)
    for warning in st.session_state.pop("aed_sync_warnings", []):
        st.warning(warning)
