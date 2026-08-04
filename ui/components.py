"""Reusable visual components for all AED Operations pages."""
from __future__ import annotations

from html import escape
from typing import Iterable

import streamlit as st

Capability = tuple[str, str]


def _capability_cards(items: Iterable[Capability]) -> str:
    return "".join(
        '<div class="aed-capability-card">'
        f"<strong>{escape(title)}</strong>"
        f"<span>{escape(description)}</span>"
        "</div>"
        for title, description in items
    )


def page_header(
    title: str,
    subtitle: str = "",
    *,
    eyebrow: str = "AED OPERATIONS SYSTEM",
    chip: str = "",
    capabilities: Iterable[Capability] | None = None,
) -> None:
    chip_markup = f'<span class="aed-chip">{escape(chip)}</span>' if chip else ""
    st.markdown(
        '<section class="aed-hero">'
        f'<div class="aed-hero-eyebrow">{escape(eyebrow)}</div>'
        f'<h1>{escape(title)}</h1>'
        f'<p>{escape(subtitle)}</p>'
        f'{chip_markup}'
        '</section>',
        unsafe_allow_html=True,
    )
    cards = list(capabilities or ())
    if cards:
        st.markdown(
            f'<div class="aed-capability-cards">{_capability_cards(cards)}</div>',
            unsafe_allow_html=True,
        )


def dashboard_hero(
    title: str,
    subtitle: str,
    *,
    status_text: str,
    source_text: str,
) -> None:
    st.markdown(
        '<section class="dashboard-hero">'
        '<div class="dashboard-hero-grid">'
        '<div>'
        '<div class="dashboard-kicker">AED OPERATIONS · COMMAND VIEW</div>'
        f'<h1>{escape(title)}</h1>'
        f'<p>{escape(subtitle)}</p>'
        '</div>'
        '<div class="dashboard-system-state">'
        f'<span><i></i>{escape(status_text)}</span>'
        f'<small>{escape(source_text)}</small>'
        '</div>'
        '</div>'
        '</section>',
        unsafe_allow_html=True,
    )


def section_label(text: str) -> None:
    st.markdown(f'<div class="aed-section-label">{escape(text)}</div>', unsafe_allow_html=True)


def note_panel(label: str, text: str) -> None:
    st.markdown(
        '<div class="aed-note-panel">'
        f'<strong>{escape(label)}</strong>{escape(text)}'
        '</div>',
        unsafe_allow_html=True,
    )


def empty_state(message: str) -> None:
    st.info(message)
