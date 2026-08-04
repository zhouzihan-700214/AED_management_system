"""Readable deployment validation for the runtime module contract."""
from __future__ import annotations

from collections.abc import Mapping, Sequence
from types import ModuleType

import streamlit as st


def missing_callables(contract: Mapping[ModuleType, Sequence[str]]) -> list[str]:
    missing: list[str] = []
    for module, names in contract.items():
        for name in names:
            if not callable(getattr(module, name, None)):
                missing.append(f"{module.__name__}.{name}")
    return missing


def stop_if_incompatible(contract: Mapping[ModuleType, Sequence[str]]) -> None:
    missing = missing_callables(contract)
    if not missing:
        return
    st.error("The deployed repository contains mixed application versions.")
    st.write("Replace the repository root with the complete ZIP contents, then reboot the app.")
    st.code("\n".join(missing), language="text")
    st.stop()
