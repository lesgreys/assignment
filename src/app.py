"""
CX Analytics Dashboard
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
    title="CX Analytics Dashboard"
)

# Expose Flask server for WSGI servers (like Vercel)
server = app.server

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
                    html.H2("CX Analytics Dashboard", className="mb-0 text-white"),
                    html.Small("Customer Success Analytics", className="text-light")
                ])
            ], width=6),
            dbc.Col([
                html.Div([
                    # Only show PDF export button in local development (not on Vercel)
                    dbc.Button([
                        html.I(className="fas fa-file-pdf me-2"),
                        "Export to PDF"
                    ], id="export-pdf-button", color="light", outline=True, size="sm",
                       className="me-3", style={"display": "none" if os.environ.get('VERCEL') == '1' else "inline-block"}),
                    html.Span(f"Last Updated: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
                             className="text-light")
                ], className="float-end")
            ], width=6)
        ], className="w-100 align-items-center")
    ], fluid=True),
    color="primary",
    dark=True,
    className="mb-4",
    style={"position": "fixed", "top": 0, "width": "100%", "z-index": 2}
)

# PDF Export Modal
pdf_export_modal = dbc.Modal([
    dbc.ModalHeader("Generating PDF Report"),
    dbc.ModalBody([
        html.Div([
            html.I(className="fas fa-file-pdf fa-3x text-primary mb-3"),
            html.H5("Exporting Dashboard to PDF...", className="mb-3"),
            dbc.Progress(value=100, striped=True, animated=True, color="primary", className="mb-3"),
            html.P([
                html.I(className="fas fa-circle-notch fa-spin me-2"),
                "This may take 10-30 seconds. Please wait..."
            ], className="text-muted")
        ], className="text-center")
    ]),
], id="pdf-export-modal", is_open=False, centered=True, backdrop="static", keyboard=False)

# Main layout
app.layout = dbc.Container([
    dcc.Location(id='url', refresh=False),
    dcc.Interval(id='loading-interval', interval=1000, n_intervals=0, disabled=True),  # Disabled - using synchronous loading
    dcc.Store(id='data-loaded-store', storage_type='session'),  # Stores data load status
    dcc.Download(id="download-pdf"),  # PDF download component
    dcc.Store(id='pdf-export-status', data={'exporting': False}),  # Track export status
    pdf_export_modal,  # PDF export loading modal
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
    [Input('url', 'pathname'),
     Input('data-loaded-store', 'data')]
)
def display_page(pathname, data_loaded_flag):
    """Route to appropriate page based on URL."""
    try:
        # Load data
        loader = get_data_loader()

        # Load data synchronously if not already loaded
        # Redis cache makes this fast (~1-2s from cache, ~10s on first load)
        if not loader.loaded:
            loader.load_all_data()

        # If still not loaded (error occurred), show error
        if not loader.loaded:
            return dbc.Container([
                dbc.Alert([
                    html.H4([
                        html.I(className="fas fa-exclamation-triangle me-2"),
                        "Failed to Load Dashboard Data"
                    ], className="alert-heading"),
                    html.P(f"Loading stage: {loader.loading_stage}"),
                    html.Hr(),
                    html.P([
                        "The dashboard failed to load data. This could be due to:",
                        html.Ul([
                            html.Li("Missing data files in data/raw/"),
                            html.Li("Redis connection issues"),
                            html.Li("Data processing errors")
                        ])
                    ]),
                    html.P("Check the server logs for more details.", className="mb-0")
                ], color="danger", className="mt-5")
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


# Note: Loading interval callback removed - using synchronous loading instead
# Data loads synchronously in display_page() callback, so no need for polling


# PDF Export - Open modal when button clicked
@app.callback(
    Output("pdf-export-modal", "is_open"),
    Input("export-pdf-button", "n_clicks"),
    State("pdf-export-modal", "is_open"),
    prevent_initial_call=True
)
def toggle_export_modal(n_clicks, is_open):
    """Open modal when export button is clicked."""
    if n_clicks:
        return True
    return is_open


# PDF Export - Generate and download
@app.callback(
    [Output("download-pdf", "data"),
     Output("pdf-export-modal", "is_open", allow_duplicate=True)],
    Input("export-pdf-button", "n_clicks"),
    prevent_initial_call=True
)
def export_dashboard_pdf(n_clicks):
    """Generate and download PDF report of the entire dashboard."""
    if n_clicks is None:
        return dash.no_update, dash.no_update

    try:
        # Import PDF export utility - only available in local environment
        # Skip on Vercel to reduce bundle size
        if os.environ.get('VERCEL') == '1':
            print("PDF export not available on Vercel deployment")
            return dash.no_update, False

        from utils.pdf_export import PDFExporter
        import tempfile

        print(f"\n{'='*60}")
        print(f"PDF EXPORT STARTED - Click #{n_clicks}")
        print(f"{'='*60}")

        # Get data loader
        loader = get_data_loader()

        # Ensure data is loaded
        if not loader.loaded:
            print("Data not loaded, loading now...")
            loader.load_all_data()
        else:
            print("Data already loaded")

        # Generate PDF with timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        temp_path = tempfile.mktemp(suffix='.pdf', prefix=f'dashboard_export_{timestamp}_')

        print(f"Generating PDF at: {temp_path}")

        # Create PDF
        exporter = PDFExporter(loader, temp_path)
        pdf_path = exporter.generate_pdf()

        print(f"PDF generated successfully: {pdf_path}")
        print(f"File size: {os.path.getsize(pdf_path) / 1024 / 1024:.2f} MB")

        # Read PDF content
        with open(pdf_path, 'rb') as f:
            pdf_content = f.read()

        # Clean up temp file
        try:
            os.remove(pdf_path)
            print("Temp file cleaned up")
        except Exception as e:
            print(f"Could not remove temp file: {e}")

        print(f"Returning PDF for download: dashboard_export_{timestamp}.pdf")
        print(f"{'='*60}\n")

        # Return PDF for download and close modal
        return dcc.send_bytes(
            pdf_content,
            filename=f"dashboard_export_{timestamp}.pdf"
        ), False

    except Exception as e:
        print(f"\n{'='*60}")
        print(f"ERROR GENERATING PDF EXPORT")
        print(f"{'='*60}")
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        print(f"{'='*60}\n")
        return dash.no_update, False  # Close modal on error


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
    print("Initializing CX Analytics Dashboard...")
    loader = get_data_loader()

    if loader.load_all_data():
        print("\n✓ Dashboard ready!")
        print("  Starting server on http://localhost:8050")

        debug_mode = os.getenv('DASH_DEBUG', 'true').lower() == 'true'
        port = int(os.getenv('DASH_PORT', 8050))

        app.run_server(debug=debug_mode, host='0.0.0.0', port=port)
    else:
        print("\n✗ Failed to load data. Please check configuration and data files.")
