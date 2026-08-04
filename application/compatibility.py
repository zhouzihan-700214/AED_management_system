"""Apply safe defaults before any runtime service imports are evaluated."""
from __future__ import annotations

from pathlib import Path
from typing import Any


def configure_legacy_defaults(config: Any) -> None:
    root = Path(getattr(config, "PROJECT_ROOT", getattr(config, "BASE_DIR", Path.cwd())))
    data = Path(getattr(config, "DATA_DIR", root / "data"))
    temp = Path(getattr(config, "TEMP_DIR", root / "temp"))
    external = Path(getattr(config, "EXTERNAL_DATA_DIR", root / "external_data"))
    backups = root / "backups"

    path_defaults = {
        "PROJECT_ROOT": root,
        "BASE_DIR": root,
        "DATA_DIR": data,
        "TEMP_DIR": temp,
        "EXTERNAL_DATA_DIR": external,
        "AED_CACHE_FILE": root / "aed_data.csv",
        "AED_DATA_FILE": root / "aed_data.csv",
        "AED_HISTORY_FILE": root / "aed_management_history.csv",
        "AED_LIFECYCLE_FILE": data / "aed_lifecycle_history.csv",
        "AUDIT_HISTORY_FILE": data / "audit_history.csv",
        "TRANSACTION_HISTORY_FILE": data / "transaction_history.csv",
        "CONFLICT_HISTORY_FILE": data / "conflict_history.csv",
        "ACTIVE_TRANSACTION_FILE": data / "active_transaction.json",
        "SYNC_STATE_FILE": data / "excel_sync_state.json",
        "EXCEL_OPERATION_LOCK_FILE": data / "excel_operation.lock",
        "EXCEL_WRITE_HISTORY_FILE": data / "excel_write_history.csv",
        "EXCEL_BACKUP_DIR": backups / "excel",
        "CACHE_BACKUP_DIR": backups / "aed_cache",
        "PM_RESPONSES_FILE": root / "pm_responses.csv",
        "PM_PLAN_FILE": root / "pm_plan_records.csv",
        "MANUAL_SERVICE_RECORDS_FILE": root / "manual_service_records.csv",
        "ISSUE_RECORD_FILE": root / "issue_records.csv",
        "ISSUE_HISTORY_FILE": root / "issue_history.csv",
        "ISSUE_ATTACHMENTS_FILE": root / "issue_attachments.csv",
        "ISSUE_RESOLUTION_FILE": root / "issue_resolution_submissions.csv",
        "ISSUE_PHOTO_DIR": root / "issue_photos",
        "MAP_STATUS_FILE": root / "map_status_definitions.csv",
        "MAP_UNIT_STATE_FILE": root / "map_unit_state.csv",
        "MAP_COLOR_SETTINGS_FILE": root / "map_color_settings.csv",
        "ONEDRIVE_CACHE_DIR": data / "onedrive_workbook_cache",
        "ONEDRIVE_SYNC_STATE_FILE": data / "onedrive_sync_state.json",
        "ONEDRIVE_PENDING_DIR": backups / "onedrive_pending",
        "SYSTEM_STATE_SYNC_FILE": data / "system_state_sync.json",
        "SYSTEM_STATE_PENDING_DIR": backups / "system_state_pending",
    }
    for name, value in path_defaults.items():
        if not hasattr(config, name):
            setattr(config, name, value)

    if not hasattr(config, "MICROSOFT_CONFIG"):
        config.MICROSOFT_CONFIG = {
            "client_id": "",
            "client_secret": "",
            "authority": "https://login.microsoftonline.com/consumers",
            "redirect_uri": "",
            "onedrive_file_path": "/AED System/IB_list_TEST.xlsx",
            "system_state_path": "/AED System/AED_System_State.zip",
        }
    config.MICROSOFT_CONFIG.setdefault("onedrive_file_path", "/AED System/IB_list_TEST.xlsx")
    config.MICROSOFT_CONFIG.setdefault("system_state_path", "/AED System/AED_System_State.zip")

    scalar_defaults = {
        "BUILD_ID": "2026-08-04-v10-SINGLE-ENTRY",
        "AUDIT_USERS": ("Zihan", "Supervisor", "Technician 1", "Technician 2"),
        "ONEDRIVE_CLOUD_ENABLED": False,
        "EXCEL_FILE": external / "IB_list_TEST.xlsx",
        "EXCEL_SHEET": "Sheet1",
        "EXCEL_HEADER_ROW": 1,
        "EXCEL_DATA_START_ROW": 3,
        "SERIAL_COLUMN": "Serial Number",
        "LOCK_WARNING_MINUTES": 5,
        "LOCK_STALE_MINUTES": 15,
        "MAX_CACHE_BACKUPS": 20,
        "MAX_EXCEL_BACKUPS": 20,
        "PRESERVE_CACHE_ONLY_UNITS": True,
        "STAGING_SHEET_NAME": "__STAGING_UPDATE__",
    }
    for name, value in scalar_defaults.items():
        if not hasattr(config, name):
            setattr(config, name, value)

    config.EXCEL_WRITE_LOCK_FILE = getattr(config, "EXCEL_WRITE_LOCK_FILE", config.EXCEL_OPERATION_LOCK_FILE)
    config.SYNC_LOCK_FILE = getattr(config, "SYNC_LOCK_FILE", config.EXCEL_OPERATION_LOCK_FILE)

    state_paths = tuple(getattr(config, "SYSTEM_STATE_PATHS", ()))
    required = (
        config.AED_HISTORY_FILE,
        config.PM_RESPONSES_FILE,
        config.PM_PLAN_FILE,
        config.MANUAL_SERVICE_RECORDS_FILE,
        config.ISSUE_RECORD_FILE,
        config.ISSUE_HISTORY_FILE,
        config.ISSUE_ATTACHMENTS_FILE,
        config.ISSUE_RESOLUTION_FILE,
        config.MAP_STATUS_FILE,
        config.MAP_UNIT_STATE_FILE,
        config.MAP_COLOR_SETTINGS_FILE,
        config.AUDIT_HISTORY_FILE,
        config.TRANSACTION_HISTORY_FILE,
        config.CONFLICT_HISTORY_FILE,
        config.EXCEL_WRITE_HISTORY_FILE,
        config.AED_LIFECYCLE_FILE,
        config.ISSUE_PHOTO_DIR,
    )
    config.SYSTEM_STATE_PATHS = tuple(dict.fromkeys((*state_paths, *required)))

    if not callable(getattr(config, "ensure_project_directories", None)):
        def ensure_project_directories() -> None:
            for directory in (
                config.EXTERNAL_DATA_DIR,
                config.DATA_DIR,
                config.TEMP_DIR,
                config.CACHE_BACKUP_DIR,
                config.EXCEL_BACKUP_DIR,
                config.ISSUE_PHOTO_DIR,
                config.ONEDRIVE_CACHE_DIR,
                config.ONEDRIVE_PENDING_DIR,
                config.SYSTEM_STATE_PENDING_DIR,
            ):
                Path(directory).mkdir(parents=True, exist_ok=True)
        config.ensure_project_directories = ensure_project_directories
