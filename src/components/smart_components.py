"""
Smart Components
Self-documenting dashboard components that automatically inject info icons and configurations.
"""

import dash_bootstrap_components as dbc
from dash import dcc, html
import json
from pathlib import Path

from components.info_icon import create_info_icon
from utils.chart_config import CHART_CONFIG
from utils.code_extractor import generate_info_content_entry


# Load metadata once at module level
METADATA_PATH = Path(__file__).parent.parent / 'config' / 'component_metadata.json'
with open(METADATA_PATH, 'r') as f:
    COMPONENT_METADATA = json.load(f)


def get_component_metadata(component_id: str, page_id: str = None):
    """
    Retrieve metadata for a component.

    Args:
        component_id: ID of the component (e.g., 'kpi_total_arr', 'chart_health_distribution')
        page_id: Optional page ID (e.g., 'executive_overview'). If None, searches all pages.

    Returns:
        Component metadata dictionary or None if not found
    """
    if page_id:
        # Direct lookup
        page_data = COMPONENT_METADATA.get(page_id, {})
        return page_data.get(component_id)
    else:
        # Search all pages
        for pid, page_data in COMPONENT_METADATA.items():
            if pid.startswith('_'):  # Skip metadata keys
                continue
            if component_id in page_data:
                return page_data[component_id]
    return None


def SmartGraph(component_id, figure, page_id=None, config=None, **kwargs):
    """
    Smart Graph component with automatic chart configuration (watermark removal).

    Args:
        component_id: Unique ID for this chart (e.g., 'chart_health_distribution')
        figure: Plotly figure object
        page_id: Optional page ID for faster lookup
        config: Optional custom Plotly config (defaults to CHART_CONFIG to remove watermark)
        **kwargs: Additional arguments passed to dcc.Graph

    Returns:
        Dash component with graph (no info icon)
    """
    # Default config removes watermark
    if config is None:
        config = CHART_CONFIG

    # Create base graph with height constraint
    graph = dcc.Graph(figure=figure, config=config, style={"height": "100%"}, **kwargs)

    # Return card with graph only (no info icon) - with minHeight to prevent collapse
    return dbc.Card([
        dbc.CardBody([graph])
    ], className="shadow-sm", style={"minHeight": "450px"})


def SmartKPICard(component_id, title, value, subtitle="", icon="fas fa-chart-line", color="primary", page_id=None):
    """
    Smart KPI Card component (no info icon).

    Args:
        component_id: Unique ID for this KPI (e.g., 'kpi_total_arr')
        title: Display title
        value: KPI value to display
        subtitle: Optional subtitle text
        icon: Font Awesome icon class
        color: Bootstrap color (primary, success, warning, etc.)
        page_id: Optional page ID for faster lookup

    Returns:
        KPI card component (no info icon)
    """
    # Build title content (no info icon)
    title_content = [html.H6(title, className="text-muted mb-1", style={"height": "2.5rem", "overflow": "hidden", "textOverflow": "ellipsis", "whiteSpace": "nowrap"})]

    # Create card
    return dbc.Card([
        dbc.CardBody([
            html.Div([
                html.Div([
                    html.I(className=f"{icon} fa-2x", style={"color": f"var(--bs-{color})"})
                ], className="col-3 text-center"),
                html.Div([
                    html.Div(title_content),
                    html.H3(value, className="mb-0", style={"overflow": "hidden", "textOverflow": "ellipsis", "whiteSpace": "nowrap"}),
                    html.Small(subtitle, className="text-muted", style={"overflow": "hidden", "textOverflow": "ellipsis", "display": "block", "lineHeight": "1.2"})
                ], className="col-9")
            ], className="row align-items-center")
        ], style={"minHeight": "120px", "maxHeight": "140px", "overflow": "hidden"})
    ], className="mb-3 shadow-sm")


def SmartTable(component_id, table_component, title, page_id=None):
    """
    Smart Table component (no info icon).

    Args:
        component_id: Unique ID for this table (e.g., 'table_at_risk')
        table_component: The table component (dbc.Table or dash_table.DataTable)
        title: Table title
        page_id: Optional page ID for faster lookup

    Returns:
        Card with table (no info icon)
    """
    # Build header content (no info icon)
    header_content = [html.H5(title)]

    # Create card with proper overflow handling
    return dbc.Card([
        dbc.CardHeader(header_content),
        dbc.CardBody([
            html.Div([table_component], style={"width": "100%", "overflowX": "auto"})
        ], style={"padding": "1rem"})
    ], className="shadow-sm mb-4")


# Convenience function to check if metadata exists
def has_metadata(component_id: str, page_id: str = None) -> bool:
    """Check if metadata exists for a component."""
    return get_component_metadata(component_id, page_id) is not None
