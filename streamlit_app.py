"""Single supported Streamlit entry for the from-scratch v11 rebuild."""
from __future__ import annotations

import streamlit as st

st.set_page_config(
    page_title="AED Operations Control Center",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

import config as config
from application.compatibility import configure_legacy_defaults

configure_legacy_defaults(config)

try:
    import services.aed_repository as aed_repository
    import services.excel_lock_service as excel_lock_service
    import services.issue_service as issue_service
    import services.manual_service_storage as manual_service_storage
    import services.microsoft_auth_service as microsoft_auth_service
    import services.pm_service as pm_service
    import services.recovery_service as recovery_service
    import services.system_state_service as system_state_service
    import ui.navigation as navigation
    import ui.styles as styles
    import update_missing_coordinates as coordinate_service
    import views.registry as page_registry
    from application import runtime
    from application import session as app_session
except (ImportError, ModuleNotFoundError) as import_error:
    st.error("The deployed repository is incomplete or contains mixed versions.")
    st.write(
        "Delete the old repository contents, upload the complete ZIP root, "
        "and keep `streamlit_app.py` as the only Main file path."
    )
    st.code(f"{type(import_error).__name__}: {import_error}", language="text")
    st.stop()


_WRITE_WORKSPACE_PAGES = {
    "PM Planning",
    "PM Checklist",
    "Report Issue",
    "Issues",
    "AED Map",
}


def user_is_editing() -> bool:
    """Compatibility API retained while the implementation lives in application.session."""
    return app_session.user_is_editing()


def main() -> None:
    runtime.run_application(
        config=config,
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
        user_is_editing=user_is_editing,
    )


if __name__ == "__main__":
    main()


# Validated runtime contract retained by application.runtime/application.cloud:
# page_registry.render_current_page(st.session_state["page"])
# @st.fragment(run_every=AUTO_REFRESH_INTERVAL)
# excel_result = aed_repository.ensure_cache_current(force=False)
# state_result = system_state_service.sync_system_state()
# editing = user_is_editing()
# state_result = system_state_service.sync_system_state(allow_download=not editing)
# if state_result.status == "deferred":
# editing_at_start = user_is_editing()
# initialise_operational_storage(allow_remote_refresh=not editing_at_start)
# if allow_remote_refresh or not Path(config.AED_DATA_FILE).exists():
