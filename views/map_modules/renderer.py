# Fresh semantic rebuild: generated from the validated runtime contract.
# The file was re-emitted into the new project rather than patched in place.

from __future__ import annotations
from typing import Any
from urllib.parse import urlencode
import folium
import pandas as pd
from folium.plugins import BeautifyIcon, Fullscreen, LocateControl
from streamlit_folium import st_folium
from utils.text_utils import clean_text
from views.map_modules.helpers import safe_html
from views.map_modules.status_service import COLOR_PALETTE, active_statuses, status_color_lookup

def marker_color_for_row(row: pd.Series, definitions: pd.DataFrame) -> str:
    override = clean_text(row.get('Color Override', '')).title()
    if override in COLOR_PALETTE:
        return override
    lookup = status_color_lookup(definitions)
    status = clean_text(row.get('PM Status', '')).casefold()
    return lookup.get(status, 'Gray')

def create_marker_icon(color_name: str, selected: bool) -> BeautifyIcon:
    color_hex = COLOR_PALETTE.get(color_name, COLOR_PALETTE['Gray'])
    return BeautifyIcon(icon_shape='marker', border_width=4 if selected else 2, border_color='#101828' if selected else '#FFFFFF', text_color='#101828' if color_name in {'Yellow', 'Lime', 'Cyan'} else '#FFFFFF', background_color=color_hex, number='+')

def create_popup(row: pd.Series) -> folium.Popup:
    serial = safe_html(row.get('Serial Number', ''))
    model = safe_html(row.get('Model', ''))
    location = safe_html(row.get('Location', ''))
    postal = safe_html(row.get('Postal Code', ''))
    status = safe_html(row.get('PM Status', ''))
    raw_serial = clean_text(row.get('Serial Number', ''))
    raw_postal = clean_text(row.get('Postal Code', ''))
    pm_query = urlencode({'page': 'PM Checklist', 'serial': raw_serial, 'postal_code': raw_postal})
    issue_query = urlencode({'page': 'Report Issue', 'serial': raw_serial, 'postal_code': raw_postal})
    popup_html = f"""\n    <div style="\n        width: 250px;\n        font-family: Arial, sans-serif;\n        color: #1f2937;\n        line-height: 1.45;\n    ">\n        <div style="\n            margin-bottom: 9px;\n            font-size: 17px;\n            font-weight: 700;\n        ">\n            {serial or 'AED Unit'}\n        </div>\n\n        <div style="font-size: 12px;">\n            <b>Model:</b> {model or '-'}<br>\n            <b>Location:</b> {location or '-'}<br>\n            <b>Postal Code:</b> {postal or '-'}<br>\n            <b>PM Status:</b> {status or '-'}\n        </div>\n\n        <div style="\n            display: grid;\n            grid-template-columns: 1fr 1fr;\n            gap: 7px;\n            margin-top: 12px;\n        ">\n            <a\n                href="?{pm_query}"\n                target="_top"\n                style="\n                    padding: 8px;\n                    border-radius: 6px;\n                    background: #1f5eea;\n                    color: white;\n                    font-size: 11px;\n                    font-weight: 700;\n                    text-align: center;\n                    text-decoration: none;\n                "\n            >\n                Start PM\n            </a>\n\n            <a\n                href="?{issue_query}"\n                target="_top"\n                style="\n                    padding: 8px;\n                    border: 1px solid #f04438;\n                    border-radius: 6px;\n                    background: white;\n                    color: #d92d20;\n                    font-size: 11px;\n                    font-weight: 700;\n                    text-align: center;\n                    text-decoration: none;\n                "\n            >\n                Report Issue\n            </a>\n        </div>\n    </div>\n    """
    return folium.Popup(popup_html, max_width=330)

def build_legend_html(dataframe: pd.DataFrame, definitions: pd.DataFrame) -> str:
    rows = []
    for _, status_row in active_statuses(definitions).iterrows():
        status_name = clean_text(status_row['Status Name'])
        count = int(dataframe['PM Status'].astype(str).str.casefold().eq(status_name.casefold()).sum())
        if count == 0:
            continue
        color_name = clean_text(status_row['Marker Color']).title()
        color_hex = COLOR_PALETTE.get(color_name, COLOR_PALETTE['Gray'])
        rows.append(f'\n            <div style="\n                display:flex;\n                align-items:center;\n                gap:7px;\n                margin:4px 0;\n            ">\n                <span style="\n                    width:10px;\n                    height:10px;\n                    border-radius:50%;\n                    background:{color_hex};\n                    display:inline-block;\n                "></span>\n                <span>{safe_html(status_name)} ({count})</span>\n            </div>\n            ')
    if not rows:
        return ''
    return f"""\n    <div style="\n        position: fixed;\n        right: 18px;\n        bottom: 20px;\n        z-index: 9999;\n        min-width: 145px;\n        padding: 10px 12px;\n        border: 1px solid #e4e7ec;\n        border-radius: 8px;\n        background: rgba(255,255,255,0.96);\n        box-shadow: 0 4px 16px rgba(16,24,40,0.12);\n        color: #344054;\n        font-family: Arial, sans-serif;\n        font-size: 11px;\n    ">\n        <div style="\n            margin-bottom: 5px;\n            color:#101828;\n            font-weight:700;\n        ">\n            Legend\n        </div>\n        {''.join(rows)}\n    </div>\n    """

def create_map(dataframe: pd.DataFrame, definitions: pd.DataFrame, selected_serial: str) -> folium.Map:
    mapped = dataframe.dropna(subset=['Latitude', 'Longitude']).copy()
    if mapped.empty:
        raise ValueError('No valid coordinates were found for the current selection.')
    map_object = folium.Map(location=[mapped['Latitude'].mean(), mapped['Longitude'].mean()], zoom_start=11, control_scale=True, tiles='OpenStreetMap')
    Fullscreen(position='topright').add_to(map_object)
    LocateControl(position='topright', strings={'title': 'Show my location'}).add_to(map_object)
    for _, row in mapped.iterrows():
        serial = clean_text(row.get('Serial Number', ''))
        color_name = marker_color_for_row(row, definitions)
        folium.Marker(location=[float(row['Latitude']), float(row['Longitude'])], tooltip=serial or 'AED', popup=create_popup(row), icon=create_marker_icon(color_name=color_name, selected=serial.casefold() == clean_text(selected_serial).casefold())).add_to(map_object)
    if len(mapped) > 1:
        map_object.fit_bounds(mapped[['Latitude', 'Longitude']].values.tolist(), padding=(28, 28))
    legend_html = build_legend_html(mapped, definitions)
    if legend_html:
        map_object.get_root().html.add_child(folium.Element(legend_html))
    return map_object

def render_folium(map_object: folium.Map, map_key: str) -> dict[str, Any]:
    try:
        result = st_folium(map_object, width=None, height=540, returned_objects=['last_object_clicked_tooltip'], key=map_key)
    except TypeError:
        result = st_folium(map_object, width=None, height=540, key=map_key)
    return result or {}
