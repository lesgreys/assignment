"""
DoorLoop CX Dashboard
Main Dash application for Customer Success analytics.
"""

import os
import dash
from dash import dcc, html, Input, Output, State
import dash_bootstrap_components as dbc
from datetime import datetime

# Import layouts
from layouts.executive_overview import create_executive_overview
from layouts.health_risk import create_health_risk_monitor
from layouts.adoption_engagement import create_adoption_engagement
from layouts.retention_analysis import create_retention_analysis
from layouts.revenue_analytics import create_revenue_analytics
from layouts.csm_workload import create_csm_workload
from layouts.user_flow import create_user_flow
from layouts.raw_data import create_raw_data_view

# Import data loader
from utils.load_data import get_data_loader

# Initialize Dash app
app = dash.Dash(
    __name__,
    external_stylesheets=[dbc.themes.BOOTSTRAP, dbc.icons.FONT_AWESOME],
    suppress_callback_exceptions=True,
    title="DoorLoop CX Dashboard"
)

# Define color scheme
COLORS = {
    'primary': '#4A90E2',
    'success': '#7ED321',
    'warning': '#F5A623',
    'danger': '#D0021B',
    'dark': '#2C3E50',
    'light': '#ECF0F1',
    'green': '#27AE60',
    'yellow': '#F39C12',
    'red': '#E74C3C'
}

# Sidebar navigation
sidebar = dbc.Nav(
    [
        dbc.NavLink([html.I(className="fas fa-chart-line me-2"), "Executive Overview"],
                   href="/", active="exact", className="mb-2"),
        dbc.NavLink([html.I(className="fas fa-heartbeat me-2"), "Health & Risk Monitor"],
                   href="/health-risk", active="exact", className="mb-2"),
        dbc.NavLink([html.I(className="fas fa-rocket me-2"), "Adoption & Engagement"],
                   href="/adoption", active="exact", className="mb-2"),
        dbc.NavLink([html.I(className="fas fa-stream me-2"), "User Flow & Timeline"],
                   href="/user-flow", active="exact", className="mb-2"),
        dbc.NavLink([html.I(className="fas fa-redo me-2"), "Retention Analysis"],
                   href="/retention", active="exact", className="mb-2"),
        dbc.NavLink([html.I(className="fas fa-dollar-sign me-2"), "Revenue Analytics"],
                   href="/revenue", active="exact", className="mb-2"),
        dbc.NavLink([html.I(className="fas fa-users me-2"), "CSM Workload"],
                   href="/csm-workload", active="exact", className="mb-2"),
        html.Hr(className="my-3"),
        dbc.NavLink([html.I(className="fas fa-database me-2"), "Raw Data Tables"],
                   href="/raw-data", active="exact", className="mb-2"),
    ],
    vertical=True,
    pills=True,
    className="bg-light",
    style={"position": "fixed", "top": "80px", "left": 0, "width": "250px", "height": "100%",
           "padding": "20px", "z-index": 1}
)

# Header
header = dbc.Navbar(
    dbc.Container([
        dbc.Row([
            dbc.Col([
                html.Div([
                    html.H2("DoorLoop CX Dashboard", className="mb-0 text-white"),
                    html.Small("Customer Success Analytics", className="text-light")
                ])
            ], width=6),
            dbc.Col([
                html.Div([
                    html.Span(f"Last Updated: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
                             className="text-light float-end")
                ])
            ], width=6)
        ], className="w-100 align-items-center")
    ], fluid=True),
    color="primary",
    dark=True,
    className="mb-4",
    style={"position": "fixed", "top": 0, "width": "100%", "z-index": 2}
)

# Main layout
app.layout = dbc.Container([
    dcc.Location(id='url', refresh=False),
    header,
    dbc.Row([
        dbc.Col(sidebar, width=2, style={"padding": 0}),
        dbc.Col([
            html.Div(id='page-content', style={"margin-top": "80px"})
        ], width=10, style={"margin-left": "250px"})
    ])
], fluid=True, style={"padding": 0})


# Routing callback
@app.callback(
    Output('page-content', 'children'),
    [Input('url', 'pathname')]
)
def display_page(pathname):
    """Route to appropriate page based on URL."""
    try:
        # Load data
        loader = get_data_loader()

        # Display loading message if data not loaded
        if not loader.loaded:
            return dbc.Container([
                dbc.Row([
                    dbc.Col([
                        dbc.Spinner([
                            html.Div([
                                html.H3("Loading data..."),
                                html.P("Please wait while we load and process the data.")
                            ], className="text-center mt-5")
                        ], color="primary", type="border")
                    ], width=12)
                ])
            ], fluid=True)

        # Route to pages
        if pathname == '/health-risk':
            return create_health_risk_monitor(loader)
        elif pathname == '/adoption':
            return create_adoption_engagement(loader)
        elif pathname == '/user-flow':
            return create_user_flow(loader)
        elif pathname == '/retention':
            return create_retention_analysis(loader)
        elif pathname == '/revenue':
            return create_revenue_analytics(loader)
        elif pathname == '/csm-workload':
            return create_csm_workload(loader)
        elif pathname == '/raw-data':
            return create_raw_data_view(loader)
        else:  # Default to executive overview
            return create_executive_overview(loader)

    except Exception as e:
        return dbc.Alert([
            html.H4("Error Loading Dashboard", className="alert-heading"),
            html.P(f"An error occurred: {str(e)}"),
            html.Hr(),
            html.P("Please check that data files are available and configuration is correct.",
                  className="mb-0")
        ], color="danger")


# Modal toggle callbacks for info icons
# AUTO-REGISTER all modals from metadata.json
import json
from pathlib import Path

# Load component metadata
metadata_path = Path(__file__).parent / 'config' / 'component_metadata.json'
with open(metadata_path, 'r') as f:
    component_metadata = json.load(f)

# Extract all component IDs from metadata
MODAL_IDS = []
for page_id, components in component_metadata.items():
    if page_id.startswith('_'):  # Skip metadata keys like _schema_version, _template
        continue
    for component_id in components.keys():
        MODAL_IDS.append(component_id)

print(f"\n✓ Auto-registered {len(MODAL_IDS)} modal callbacks from metadata")
print(f"  Pages: {[k for k in component_metadata.keys() if not k.startswith('_')]}")

# Helper function to create modal toggle callbacks
def create_modal_callback(modal_id):
    """Create a modal toggle callback for a specific modal ID."""
    @app.callback(
        Output(f"{modal_id}-modal", "is_open"),
        [Input(f"{modal_id}-icon", "n_clicks"),
         Input(f"{modal_id}-modal-close", "n_clicks")],
        [State(f"{modal_id}-modal", "is_open")],
        prevent_initial_call=True
    )
    def toggle_modal(icon_clicks, close_clicks, is_open):
        """Toggle modal open/close state."""
        if icon_clicks or close_clicks:
            return not is_open
        return is_open


# Register callbacks for each modal
for modal_id in MODAL_IDS:
    create_modal_callback(modal_id)


if __name__ == '__main__':
    # Load data on startup
    print("Initializing DoorLoop CX Dashboard...")
    loader = get_data_loader()

    if loader.load_all_data():
        print("\n✓ Dashboard ready!")
        print("  Starting server on http://localhost:8050")

        debug_mode = os.getenv('DASH_DEBUG', 'true').lower() == 'true'
        port = int(os.getenv('DASH_PORT', 8050))

        app.run_server(debug=debug_mode, host='0.0.0.0', port=port)
    else:
        print("\n✗ Failed to load data. Please check configuration and data files.")
