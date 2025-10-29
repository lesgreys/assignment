"""
Adoption & Engagement Dashboard
Track feature adoption, usage patterns, and engagement metrics.
"""

import dash_bootstrap_components as dbc
from dash import dcc, html, Input, Output, callback
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np
from itertools import combinations
from components.smart_components import SmartKPICard, SmartGraph


def create_adoption_engagement(data_loader):
    """Create Adoption & Engagement dashboard."""
    df = data_loader.get_master_data()
    events_df = data_loader.get_events_data()

    # Layout
    layout = dbc.Container([
        html.H2("Adoption & Engagement", className="mb-4"),

        # Filter controls
        dbc.Row([
            dbc.Col([
                html.Label("Active Status:", className="fw-bold mb-1"),
                dbc.RadioItems(
                    id='adoption-engagement-active-filter',
                    options=[
                        {'label': 'All', 'value': 'all'},
                        {'label': 'Active', 'value': 'active'},
                        {'label': 'Inactive', 'value': 'inactive'}
                    ],
                    value='all',
                    inline=True
                )
            ], md=3),
        ], className="mb-3 p-3 bg-light rounded"),

        # Summary cards (will be updated by callback)
        html.Div(id='adoption-engagement-kpi-cards', className="mb-4"),

        # New Section: Breadth of Adoption Analysis
        html.H4("Breadth of Adoption Analysis", className="mt-4 mb-3"),
        html.P("Measures how many different features each user has adopted (excluding login)",
               className="text-muted mb-3"),

        dbc.Row([
            dbc.Col(dcc.Graph(id='adoption-engagement-breadth-distribution'), md=6),
            dbc.Col(dcc.Graph(id='adoption-engagement-breadth-by-plan'), md=6),
        ], className="mb-4"),

        dbc.Row([
            dbc.Col(dcc.Graph(id='adoption-engagement-breadth-by-portfolio'), md=6),
            dbc.Col(dcc.Graph(id='adoption-engagement-breadth-by-csm'), md=6),
        ], className="mb-4"),

        dbc.Row([
            dbc.Col(dcc.Graph(id='adoption-engagement-feature-co-adoption'), md=12),
        ], className="mb-4"),

        # Original Section: Detailed Feature Metrics
        html.H4("Detailed Feature Metrics", className="mt-5 mb-3"),

        dbc.Row([
            dbc.Col(dcc.Graph(id='adoption-engagement-adoption-funnel'), md=6),
            dbc.Col(dcc.Graph(id='adoption-engagement-engagement-recency'), md=6),
        ], className="mb-4"),

        dbc.Row([
            dbc.Col(dcc.Graph(id='adoption-engagement-top-features'), md=6),
            dbc.Col(dcc.Graph(id='adoption-engagement-session-length'), md=6),
        ], className="mb-4"),

        dbc.Row([
            dbc.Col(dcc.Graph(id='adoption-engagement-training-completion'), md=6),
            dbc.Col(dcc.Graph(id='adoption-engagement-report-types'), md=6),
        ]),

        # Store data for callbacks
        dcc.Store(id='adoption-engagement-data-store', data={
            'users': df.to_dict('records'),
            'events': events_df.to_dict('records')
        })

    ], fluid=True)

    return layout
