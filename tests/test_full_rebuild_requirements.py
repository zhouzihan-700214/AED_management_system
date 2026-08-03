from __future__ import annotations

import ast
from pathlib import Path

from config import BUILD_ID, MICROSOFT_CONFIG
from services.aed_field_schema import JOB_TYPE_OPTIONS
from views.map_modules.status_service import COLOR_PALETTE


RUNTIME_ROOTS = [Path("app.py"), Path("streamlit_app.py"), Path("ui"), Path("views"), Path("services")]


def _runtime_python_text() -> str:
    parts: list[str] = []
    for root in RUNTIME_ROOTS:
        if root.is_file():
            parts.append(root.read_text(encoding="utf-8"))
        else:
            for path in root.rglob("*.py"):
                parts.append(path.read_text(encoding="utf-8"))
    return "\n".join(parts)


def test_full_rebuild_has_unique_deployment_marker() -> None:
    assert BUILD_ID == "2026-08-03-FULL-REBUILD-v1"
    navigation = Path("ui/navigation.py").read_text(encoding="utf-8")
    assert "build_id" in navigation


def test_streamlit_entrypoint_is_not_a_duplicate_application() -> None:
    source = Path("streamlit_app.py").read_text(encoding="utf-8")
    tree = ast.parse(source)
    assert len(source.splitlines()) <= 18
    assert "from app import main" in source
    assert "main()" in source
    assert not any(isinstance(node, ast.FunctionDef) for node in tree.body)


def test_old_asset_readiness_wording_is_not_in_runtime_code() -> None:
    runtime = _runtime_python_text().casefold()
    assert "asset readiness" not in runtime


def test_unit_profiles_replace_the_old_home_scope() -> None:
    dashboard_service = Path("services/dashboard_service.py").read_text(encoding="utf-8")
    dashboard_view = Path("views/dashboard.py").read_text(encoding="utf-8")
    dashboard_ui = Path("ui/dashboard_components.py").read_text(encoding="utf-8")
    assert 'DASHBOARD_VIEWS = ["Overview", "PM", "Issues", "Unit Profiles"]' in dashboard_service
    assert 'filters["view"] == "Unit Profiles"' in dashboard_view
    assert "Open selected profile" in dashboard_ui
    assert "Browse all profiles" in dashboard_ui


def test_aed_management_places_profiles_before_secondary_summaries() -> None:
    source = Path("views/aed_management.py").read_text(encoding="utf-8")
    start = source.index("def render_aed_management(")
    end = source.index("def render_aed_master_table(", start)
    block = source[start:end]
    assert block.index("render_dashboard_unit_profiles(dataframe)") < block.index("_render_attention_required(snapshot)")
    assert block.index("render_dashboard_unit_profiles(dataframe)") < block.index("_render_pm_progress(snapshot)")


def test_unit_profile_is_directly_selectable_and_fully_operational() -> None:
    source = Path("views/aed_management.py").read_text(encoding="utf-8")
    for required in [
        "Select AED unit",
        "Overview",
        "Edit Details",
        "Service History",
        "Add Service",
        "Issues",
        "Confirm and update Excel",
        "Review new service record",
        "Fill PM Checklist",
        "Report Issue",
        "Open in Master Table",
    ]:
        assert required in source


def test_master_table_remains_a_separate_sidebar_page() -> None:
    navigation = Path("ui/navigation.py").read_text(encoding="utf-8")
    registry = Path("views/registry.py").read_text(encoding="utf-8")
    assert '("AED Management", "▣  AED Management")' in navigation
    assert '("AED Master Table", "▦  Master Table")' in navigation
    assert '"AED Master Table": partial(' in registry
    assert "render_aed_master_table" in registry


def test_service_type_order_matches_business_request() -> None:
    assert JOB_TYPE_OPTIONS[1] == "PM"
    assert JOB_TYPE_OPTIONS[2] == "Commissioning"
    assert JOB_TYPE_OPTIONS[-3:] == ["PM+batt", "PM+glass", "PM +batt +glass"]


def test_map_keeps_many_user_definable_colours() -> None:
    assert len(COLOR_PALETTE) >= 15
    for colour in ["Blue", "Green", "Red", "Yellow", "Purple", "Pink", "Teal", "Black"]:
        assert colour in COLOR_PALETTE
    source = Path("views/aed_map.py").read_text(encoding="utf-8") + Path("views/map_modules/status_service.py").read_text(encoding="utf-8")
    assert "Manage Statuses" in source
    assert "Color Override" in source


def test_official_excel_and_system_state_are_separate_onedrive_files() -> None:
    assert MICROSOFT_CONFIG["onedrive_file_path"].endswith("IB_list_TEST.xlsx")
    assert MICROSOFT_CONFIG["system_state_path"].endswith("AED_System_State.zip")
    assert MICROSOFT_CONFIG["onedrive_file_path"] != MICROSOFT_CONFIG["system_state_path"]


def test_cloud_auto_refresh_covers_excel_and_system_records() -> None:
    source = Path("app.py").read_text(encoding="utf-8")
    assert '@st.fragment(run_every=AUTO_REFRESH_INTERVAL)' in source
    assert "ensure_cache_current(force=False)" in source
    assert "sync_system_state()" in source


def test_secret_example_contains_only_placeholders() -> None:
    source = Path(".streamlit/secrets.toml.example").read_text(encoding="utf-8")
    assert "REPLACE_WITH_ONEMAP_EMAIL" in source
    assert "REPLACE_WITH_ONEMAP_PASSWORD" in source
    assert "REPLACE_WITH_APPLICATION_CLIENT_ID" in source
    assert "REPLACE_WITH_CLIENT_SECRET_VALUE" in source


def test_deprecated_streamlit_width_argument_removed() -> None:
    assert "use_container_width" not in _runtime_python_text()
