"""Session lifecycle and write-workspace detection."""
from __future__ import annotations

from typing import Any
import uuid

import streamlit as st

WRITE_WORKSPACE_PAGES = {"PM Planning", "PM Checklist", "Report Issue", "Issues", "AED Map"}


def _profile_form_active(state: Any) -> bool:
    for key, value in state.items():
        key_text = str(key)
        if key_text.startswith(("profile_edit_pending::", "profile_service_pending::")):
            return True
        if key_text.startswith("profile_section_") and value in {"Edit Details", "Add Service"}:
            return True
    return False


def user_is_editing() -> bool:
    page = str(st.session_state.get("page", ""))
    if page in WRITE_WORKSPACE_PAGES:
        return True
    if page == "AED Master Table":
        return str(st.session_state.get("aed_editor_mode", "browse")) != "browse"
    if page in {"AED Management", "Operations Dashboard"}:
        return _profile_form_active(st.session_state)
    return False


def initialise_user_session(config: Any) -> None:
    st.session_state.setdefault("session_id", str(uuid.uuid4()))
    users = tuple(getattr(config, "AUDIT_USERS", ()))
    st.session_state.setdefault("audit_user", users[0] if users else "")
    st.session_state.setdefault("page", "Operations Dashboard")
