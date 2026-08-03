"""Streamlit Community Cloud entrypoint."""
import streamlit as st

st.set_page_config(
    page_title="AED Operations Control Center",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

from app import main

main()
