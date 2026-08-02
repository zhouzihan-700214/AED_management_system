from pathlib import Path
import os
import tomllib
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parent
BASE_DIR = PROJECT_ROOT  # Backward-compatible alias used by older modules.

# ---------------------------------------------------------------------------
# AED master data and Excel mirror configuration
# ---------------------------------------------------------------------------
EXTERNAL_DATA_DIR = PROJECT_ROOT / "external_data"
DATA_DIR = PROJECT_ROOT / "data"


def _streamlit_secret_section(name: str) -> dict[str, Any]:
    """Read a Streamlit Cloud secret section without breaking CLI/tests."""
    try:
        import streamlit as st

        section = st.secrets.get(name, {})
        return dict(section) if section else {}
    except Exception:
        return {}


def _local_secret_section(name: str) -> dict[str, Any]:
    secrets_file = PROJECT_ROOT / ".streamlit" / "secrets.toml"
    if not secrets_file.exists():
        return {}
    try:
        with secrets_file.open("rb") as handle:
            payload = tomllib.load(handle)
        section = payload.get(name, {})
        return dict(section) if isinstance(section, dict) else {}
    except (OSError, ValueError, TypeError):
        return {}


def _microsoft_configuration() -> dict[str, str]:
    section = _streamlit_secret_section("microsoft") or _local_secret_section("microsoft")
    return {
        "client_id": str(section.get("client_id", "") or "").strip(),
        "client_secret": str(section.get("client_secret", "") or "").strip(),
        "authority": str(
            section.get("authority", "https://login.microsoftonline.com/consumers")
            or "https://login.microsoftonline.com/consumers"
        ).strip(),
        "redirect_uri": str(section.get("redirect_uri", "") or "").strip(),
        "onedrive_file_path": str(
            section.get("onedrive_file_path", "/AED System/IB_list_TEST.xlsx")
            or "/AED System/IB_list_TEST.xlsx"
        ).strip(),
    }


MICROSOFT_CONFIG = _microsoft_configuration()
ONEDRIVE_CLOUD_ENABLED = all(
    MICROSOFT_CONFIG.get(key)
    for key in ("client_id", "client_secret", "redirect_uri", "onedrive_file_path")
)
ONEDRIVE_CACHE_DIR = DATA_DIR / "onedrive_workbook_cache"
ONEDRIVE_SYNC_STATE_FILE = DATA_DIR / "onedrive_sync_state.json"
ONEDRIVE_PENDING_DIR = PROJECT_ROOT / "backups" / "onedrive_pending"


def _configured_excel_path() -> Path:
    """Resolve the local working copy of the IB List.

    In browser-only OneDrive mode, Graph downloads the official workbook into
    a private app cache. In local mode, the previous path-based behaviour is
    retained for backward compatibility.
    """
    if ONEDRIVE_CLOUD_ENABLED:
        file_name = Path(MICROSOFT_CONFIG["onedrive_file_path"]).name or "IB_list_TEST.xlsx"
        return ONEDRIVE_CACHE_DIR / file_name

    environment_value = os.getenv("AED_EXCEL_FILE", "").strip()
    if environment_value:
        return Path(environment_value).expanduser()

    secrets_file = PROJECT_ROOT / ".streamlit" / "secrets.toml"
    if secrets_file.exists():
        try:
            with secrets_file.open("rb") as handle:
                secrets = tomllib.load(handle)
            configured = str(
                secrets.get("excel", {}).get("file_path", "")
                or secrets.get("AED_EXCEL_FILE", "")
            ).strip()
            if configured:
                return Path(configured).expanduser()
        except (OSError, ValueError, TypeError):
            pass

    home = Path.home()
    candidates = [
        home / "OneDrive" / "AED System" / "IB_list_TEST.xlsx",
        home / "OneDrive - Personal" / "AED System" / "IB_list_TEST.xlsx",
    ]
    candidates.extend(
        folder / "AED System" / "IB_list_TEST.xlsx"
        for folder in home.glob("OneDrive*")
        if folder.is_dir()
    )
    for candidate in candidates:
        if candidate.exists():
            return candidate

    return EXTERNAL_DATA_DIR / "IB_list_TEST.xlsx"


EXCEL_FILE = _configured_excel_path()
EXCEL_SHEET = "Sheet1"

AED_CACHE_FILE = PROJECT_ROOT / "aed_data.csv"
AED_DATA_FILE = AED_CACHE_FILE  # Backward-compatible alias.
AED_HISTORY_FILE = PROJECT_ROOT / "aed_management_history.csv"
SYNC_STATE_FILE = DATA_DIR / "excel_sync_state.json"
EXCEL_OPERATION_LOCK_FILE = DATA_DIR / "excel_operation.lock"
SYNC_LOCK_FILE = EXCEL_OPERATION_LOCK_FILE  # Stage 4 unified lock
TEMP_DIR = PROJECT_ROOT / "temp"
CACHE_BACKUP_DIR = PROJECT_ROOT / "backups" / "aed_cache"
BACKUP_DIR = CACHE_BACKUP_DIR  # Backward-compatible alias.
LOCK_FILE = EXCEL_FILE.with_suffix(EXCEL_FILE.suffix + ".lock")

SERIAL_COLUMN = "Serial Number"

# During testing, rows already in aed_data.csv but absent from the supplied
# Excel are retained. Set this to False only after confirming the workbook is
# the complete official IB List.
PRESERVE_CACHE_ONLY_UNITS = True
MAX_CACHE_BACKUPS = 20

# Stage 3: safe website -> Excel write-back configuration
EXCEL_WRITE_LOCK_FILE = EXCEL_OPERATION_LOCK_FILE  # Stage 4 unified lock
EXCEL_WRITE_HISTORY_FILE = DATA_DIR / "excel_write_history.csv"
EXCEL_BACKUP_DIR = PROJECT_ROOT / "backups" / "excel"
EXCEL_HEADER_ROW = 1
EXCEL_DATA_START_ROW = 3
STAGING_SHEET_NAME = "__STAGING_UPDATE__"
MAX_EXCEL_BACKUPS = 20

# Stage 4: concurrency, transaction, recovery and lifecycle configuration
ACTIVE_TRANSACTION_FILE = DATA_DIR / "active_transaction.json"
TRANSACTION_HISTORY_FILE = DATA_DIR / "transaction_history.csv"
CONFLICT_HISTORY_FILE = DATA_DIR / "conflict_history.csv"
AUDIT_HISTORY_FILE = DATA_DIR / "audit_history.csv"
AED_LIFECYCLE_FILE = DATA_DIR / "aed_lifecycle_history.csv"
EXCEL_TRANSACTION_DIR = TEMP_DIR / "excel_transactions"
LOCK_WARNING_MINUTES = 5
LOCK_STALE_MINUTES = 15
MAX_SNAPSHOT_RETRIES = 3
AUDIT_USERS = ("Zihan", "Supervisor", "Technician 1", "Technician 2")

# PM data
PM_RESPONSES_FILE = PROJECT_ROOT / "pm_responses.csv"
PM_PLAN_FILE = PROJECT_ROOT / "pm_plan_records.csv"

# Issue data
ISSUE_RECORD_FILE = PROJECT_ROOT / "issue_records.csv"
ISSUE_HISTORY_FILE = PROJECT_ROOT / "issue_history.csv"
ISSUE_ATTACHMENTS_FILE = PROJECT_ROOT / "issue_attachments.csv"
ISSUE_RESOLUTION_FILE = PROJECT_ROOT / "issue_resolution_submissions.csv"
ISSUE_PHOTO_DIR = PROJECT_ROOT / "issue_photos"

# Map data
MAP_STATUS_FILE = PROJECT_ROOT / "map_status_definitions.csv"
MAP_UNIT_STATE_FILE = PROJECT_ROOT / "map_unit_state.csv"
MAP_COLOR_SETTINGS_FILE = PROJECT_ROOT / "map_color_settings.csv"


def ensure_project_directories() -> None:
    """Create directories used by the staged Excel synchronization workflow."""

    for directory in [
        EXTERNAL_DATA_DIR,
        DATA_DIR,
        TEMP_DIR,
        CACHE_BACKUP_DIR,
        EXCEL_BACKUP_DIR,
        EXCEL_TRANSACTION_DIR,
        ISSUE_PHOTO_DIR,
        ONEDRIVE_CACHE_DIR,
        ONEDRIVE_PENDING_DIR,
    ]:
        directory.mkdir(parents=True, exist_ok=True)
