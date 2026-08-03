import streamlit as st


def rerun_app() -> None:
    """Rerun the current Streamlit application."""

    if hasattr(st, "rerun"):
        st.rerun()
    else:
        st.experimental_rerun()
