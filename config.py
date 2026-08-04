"""Configuration for the independently reconstructed AED Operations project."""
from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping
import os
import tomllib

PROJECT_ROOT = Path(__file__).resolve().parent
BASE_DIR = PROJECT_ROOT
BUILD_ID = "2026-08-04-v10-SINGLE-ENTRY"
REWRITE_ID = "semantic-equivalence-rebuild-2026-08-04"

EXTERNAL_DATA_DIR = PROJECT_ROOT / "external_data"
DATA_DIR = PROJECT_ROOT / "data"
TEMP_DIR = PROJECT_ROOT / "temp"
BACKUPS_DIR = PROJECT_ROOT / "backups"


def _mapping(value: Any) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _streamlit_section(section_name: str) -> dict[str, Any]:
    try:
        import streamlit as st
        return _mapping(st.secrets.get(section_name, {}))
    except Exception:
        return {}


def _toml_section(section_name: str) -> dict[str, Any]:
    secret_path = PROJECT_ROOT / ".streamlit" / "secrets.toml"
    if not secret_path.exists():
        return {}
    try:
        with secret_path.open("rb") as stream:
            document = tomllib.load(stream)
        return _mapping(document.get(section_name, {}))
    except (OSError, ValueError, TypeError, tomllib.TOMLDecodeError):
        return {}


def secret_section(section_name: str) -> dict[str, Any]:
    return _streamlit_section(section_name) or _toml_section(section_name)


def _text(section: Mapping[str, Any], name: str, default: str = "") -> str:
    return str(section.get(name, default) or default).strip()


def _microsoft_settings() -> dict[str, str]:
    section = secret_section("microsoft")
    return {
        "client_id": _text(section, "client_id"),
        "client_secret": _text(section, "client_secret"),
        "authority": _text(section, "authority", "https://login.microsoftonline.com/consumers"),
        "redirect_uri": _text(section, "redirect_uri"),
        "onedrive_file_path": _text(section, "onedrive_file_path", "/AED System/IB_list_TEST.xlsx"),
        "system_state_path": _text(section, "system_state_path", "/AED System/AED_System_State.zip"),
    }


MICROSOFT_CONFIG = _microsoft_settings()
ONEDRIVE_CLOUD_ENABLED = all(
    MICROSOFT_CONFIG.get(field)
    for field in ("client_id", "client_secret", "redirect_uri", "onedrive_file_path")
)

ONEDRIVE_CACHE_DIR = DATA_DIR / "onedrive_workbook_cache"
ONEDRIVE_SYNC_STATE_FILE = DATA_DIR / "onedrive_sync_state.json"
ONEDRIVE_PENDING_DIR = BACKUPS_DIR / "onedrive_pending"
SYSTEM_STATE_SYNC_FILE = DATA_DIR / "system_state_sync.json"
SYSTEM_STATE_PENDING_DIR = BACKUPS_DIR / "system_state_pending"


def _official_workbook_path() -> Path:
    if ONEDRIVE_CLOUD_ENABLED:
        remote_name = Path(MICROSOFT_CONFIG["onedrive_file_path"]).name or "IB_list_TEST.xlsx"
        return ONEDRIVE_CACHE_DIR / remote_name

    environment_path = os.getenv("AED_EXCEL_FILE", "").strip()
    if environment_path:
        return Path(environment_path).expanduser()

    configured_path = _text(secret_section("excel"), "file_path")
    if configured_path:
        return Path(configured_path).expanduser()

    home = Path.home()
    candidates = [
        home / "OneDrive" / "AED System" / "IB_list_TEST.xlsx",
        home / "OneDrive - Personal" / "AED System" / "IB_list_TEST.xlsx",
    ]
    candidates.extend(
        candidate / "AED System" / "IB_list_TEST.xlsx"
        for candidate in home.glob("OneDrive*")
        if candidate.is_dir()
    )
    return next((candidate for candidate in candidates if candidate.exists()), EXTERNAL_DATA_DIR / "IB_list_TEST.xlsx")


EXCEL_FILE = _official_workbook_path()
EXCEL_SHEET = "Sheet1"
EXCEL_HEADER_ROW = 1
EXCEL_DATA_START_ROW = 3
SERIAL_COLUMN = "Serial Number"

AED_CACHE_FILE = PROJECT_ROOT / "aed_data.csv"
AED_DATA_FILE = AED_CACHE_FILE
AED_HISTORY_FILE = PROJECT_ROOT / "aed_management_history.csv"
AED_LIFECYCLE_FILE = DATA_DIR / "aed_lifecycle_history.csv"

SYNC_STATE_FILE = DATA_DIR / "excel_sync_state.json"
EXCEL_OPERATION_LOCK_FILE = DATA_DIR / "excel_operation.lock"
SYNC_LOCK_FILE = EXCEL_OPERATION_LOCK_FILE
EXCEL_WRITE_LOCK_FILE = EXCEL_OPERATION_LOCK_FILE
ACTIVE_TRANSACTION_FILE = DATA_DIR / "active_transaction.json"

CACHE_BACKUP_DIR = BACKUPS_DIR / "aed_cache"
BACKUP_DIR = CACHE_BACKUP_DIR
EXCEL_BACKUP_DIR = BACKUPS_DIR / "excel"
EXCEL_TRANSACTION_DIR = TEMP_DIR / "excel_transactions"
LOCK_FILE = EXCEL_FILE.with_suffix(EXCEL_FILE.suffix + ".lock")

PRESERVE_CACHE_ONLY_UNITS = True
MAX_CACHE_BACKUPS = 20
MAX_EXCEL_BACKUPS = 20
MAX_SNAPSHOT_RETRIES = 3
STAGING_SHEET_NAME = "__STAGING_UPDATE__"
LOCK_WARNING_MINUTES = 5
LOCK_STALE_MINUTES = 15

AUDIT_HISTORY_FILE = DATA_DIR / "audit_history.csv"
TRANSACTION_HISTORY_FILE = DATA_DIR / "transaction_history.csv"
CONFLICT_HISTORY_FILE = DATA_DIR / "conflict_history.csv"
EXCEL_WRITE_HISTORY_FILE = DATA_DIR / "excel_write_history.csv"
AUDIT_USERS = ("Zihan", "Supervisor", "Technician 1", "Technician 2")

PM_RESPONSES_FILE = PROJECT_ROOT / "pm_responses.csv"
PM_PLAN_FILE = PROJECT_ROOT / "pm_plan_records.csv"
MANUAL_SERVICE_RECORDS_FILE = PROJECT_ROOT / "manual_service_records.csv"

ISSUE_RECORD_FILE = PROJECT_ROOT / "issue_records.csv"
ISSUE_HISTORY_FILE = PROJECT_ROOT / "issue_history.csv"
ISSUE_ATTACHMENTS_FILE = PROJECT_ROOT / "issue_attachments.csv"
ISSUE_RESOLUTION_FILE = PROJECT_ROOT / "issue_resolution_submissions.csv"
ISSUE_PHOTO_DIR = PROJECT_ROOT / "issue_photos"

MAP_STATUS_FILE = PROJECT_ROOT / "map_status_definitions.csv"
MAP_UNIT_STATE_FILE = PROJECT_ROOT / "map_unit_state.csv"
MAP_COLOR_SETTINGS_FILE = PROJECT_ROOT / "map_color_settings.csv"

SYSTEM_STATE_PATHS = (
    AED_HISTORY_FILE,
    PM_RESPONSES_FILE,
    PM_PLAN_FILE,
    MANUAL_SERVICE_RECORDS_FILE,
    ISSUE_RECORD_FILE,
    ISSUE_HISTORY_FILE,
    ISSUE_ATTACHMENTS_FILE,
    ISSUE_RESOLUTION_FILE,
    MAP_STATUS_FILE,
    MAP_UNIT_STATE_FILE,
    MAP_COLOR_SETTINGS_FILE,
    AUDIT_HISTORY_FILE,
    TRANSACTION_HISTORY_FILE,
    CONFLICT_HISTORY_FILE,
    EXCEL_WRITE_HISTORY_FILE,
    AED_LIFECYCLE_FILE,
    ISSUE_PHOTO_DIR,
)


def ensure_project_directories() -> None:
    directories = {
        EXTERNAL_DATA_DIR,
        DATA_DIR,
        TEMP_DIR,
        CACHE_BACKUP_DIR,
        EXCEL_BACKUP_DIR,
        EXCEL_TRANSACTION_DIR,
        ISSUE_PHOTO_DIR,
        ONEDRIVE_CACHE_DIR,
        ONEDRIVE_PENDING_DIR,
        SYSTEM_STATE_PENDING_DIR,
    }
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)
