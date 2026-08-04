from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_entrypoints_fallback_when_user_is_editing_is_missing() -> None:
    for filename in ("app.py", "streamlit_app.py"):
        source = (PROJECT_ROOT / filename).read_text(encoding="utf-8")
        assert "try:\n    from utils.streamlit_utils import user_is_editing" in source
        assert "except (ImportError, AttributeError):" in source
        assert "def user_is_editing() -> bool:" in source
        assert '"Issues",' in source
