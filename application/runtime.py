"""Top-level orchestration for the reconstructed Streamlit application."""
from __future__ import annotations

from typing import Any, Callable

import streamlit as st

from application import cloud, contracts, session, sidebar, storage


def runtime_contract(
    *,
    aed_repository: Any,
    excel_lock_service: Any,
    issue_service: Any,
    manual_service_storage: Any,
    microsoft_auth_service: Any,
    pm_service: Any,
    recovery_service: Any,
    system_state_service: Any,
    navigation: Any,
    styles: Any,
    coordinate_service: Any,
    page_registry: Any,
) -> dict[Any, tuple[str, ...]]:
    return {
        aed_repository: ("ensure_cache_current", "get_sync_status", "refresh_from_excel"),
        excel_lock_service: ("inspect_lock", "remove_confirmed_stale_lock"),
        issue_service: ("ensure_issue_storage",),
        manual_service_storage: ("ensure_manual_service_storage",),
        microsoft_auth_service: (
            "build_sign_in_url",
            "get_authentication_status",
            "handle_auth_callback",
            "sign_out",
        ),
        pm_service: ("ensure_aed_pm_fields", "ensure_pm_storage"),
        recovery_service: ("recover_incomplete_transaction",),
        system_state_service: ("bootstrap_system_state", "sync_system_state"),
        navigation: ("consume_map_navigation", "render_navigation"),
        styles: ("apply_global_styles",),
        coordinate_service: ("file_signature", "update_missing_coordinates"),
        page_registry: ("render_current_page",),
    }


def run_application(
    *,
    config: Any,
    aed_repository: Any,
    excel_lock_service: Any,
    issue_service: Any,
    manual_service_storage: Any,
    microsoft_auth_service: Any,
    pm_service: Any,
    recovery_service: Any,
    system_state_service: Any,
    navigation: Any,
    styles: Any,
    coordinate_service: Any,
    page_registry: Any,
    user_is_editing: Callable[[], bool],
) -> None:
    styles.apply_global_styles()
    contracts.stop_if_incompatible(
        runtime_contract(
            aed_repository=aed_repository,
            excel_lock_service=excel_lock_service,
            issue_service=issue_service,
            manual_service_storage=manual_service_storage,
            microsoft_auth_service=microsoft_auth_service,
            pm_service=pm_service,
            recovery_service=recovery_service,
            system_state_service=system_state_service,
            navigation=navigation,
            styles=styles,
            coordinate_service=coordinate_service,
            page_registry=page_registry,
        )
    )

    session.initialise_user_session(config)
    cloud.render_microsoft_sign_in_gate(config, microsoft_auth_service)

    try:
        storage.initialise_operational_storage(
            config=config,
            aed_repository=aed_repository,
            recovery_service=recovery_service,
            system_state_service=system_state_service,
            pm_service=pm_service,
            manual_service_storage=manual_service_storage,
            issue_service=issue_service,
            allow_remote_refresh=not user_is_editing(),
        )
    except Exception as error:
        st.error(f"Operational storage initialisation failed: {error}")
        st.stop()

    storage.refresh_coordinates_if_source_changed(config=config, coordinate_service=coordinate_service)
    navigation.consume_map_navigation()
    navigation.render_navigation(config.ISSUE_RECORD_FILE, build_id=config.BUILD_ID)
    sidebar.render_microsoft_connection_control(config, microsoft_auth_service)
    sidebar.render_identity_control(config)
    sidebar.render_data_sync_control(
        config=config,
        aed_repository=aed_repository,
        excel_lock_service=excel_lock_service,
        system_state_service=system_state_service,
    )

    auto_refresh = cloud.make_auto_refresh(
        config=config,
        microsoft_auth_service=microsoft_auth_service,
        aed_repository=aed_repository,
        system_state_service=system_state_service,
        user_is_editing=user_is_editing,
    )
    auto_refresh()
    cloud.render_notices()
    page_registry.render_current_page(st.session_state["page"])
