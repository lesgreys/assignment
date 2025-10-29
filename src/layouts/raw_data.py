"""
Raw Data Tables View
View and filter raw users and events data.
"""

import dash_bootstrap_components as dbc
from dash import dcc, html, dash_table
import pandas as pd
from components.smart_components import SmartKPICard, SmartTable


def create_raw_data_view(data_loader):
    """Create Raw Data Tables view."""
    users_df = data_loader.get_master_data()
    events_df = data_loader.get_events_data()

    # Users table - select key columns
    users_columns = [
        'user_id', 'signup_date', 'plan_type', 'portfolio_size',
        'annual_revenue', 'is_active', 'nps_score', 'support_tickets_last_90d',
        'health_score', 'health_tier', 'churn_probability', 'churn_risk_tier',
        'csm_id', 'renewal_due_date', 'days_to_renewal'
    ]

    # Filter to only existing columns
    available_users_cols = [col for col in users_columns if col in users_df.columns]
    users_display = users_df[available_users_cols].copy()

    # Format dates for display
    for col in users_display.columns:
        if users_display[col].dtype == 'datetime64[ns]':
            users_display[col] = users_display[col].dt.strftime('%Y-%m-%d')

    # Events table - select key columns
    events_columns = [
        'event_id', 'user_id', 'event_ts', 'event_type',
        'event_value_num', 'event_value_txt'
    ]

    available_events_cols = [col for col in events_columns if col in events_df.columns]
    events_display = events_df[available_events_cols].copy()

    # Format timestamp for display
    if 'event_ts' in events_display.columns:
        events_display['event_ts'] = pd.to_datetime(events_display['event_ts']).dt.strftime('%Y-%m-%d %H:%M:%S')

    # Sort events by timestamp descending
    if 'event_ts' in events_display.columns:
        events_display = events_display.sort_values('event_ts', ascending=False)

    # Users DataTable
    users_table = dash_table.DataTable(
        id='users-table',
        data=users_display.to_dict('records'),
        columns=[
            {
                'name': col.replace('_', ' ').title(),
                'id': col,
                'type': 'numeric' if users_display[col].dtype in ['int64', 'float64'] else 'text',
                'format': {
                    'specifier': '$,.0f' if col == 'annual_revenue' else
                                 ',.1f' if col in ['health_score', 'churn_probability'] else
                                 ',.0f' if users_display[col].dtype in ['int64', 'float64'] else ''
                }
            }
            for col in available_users_cols
        ],
        filter_action='native',
        sort_action='native',
        sort_mode='multi',
        page_action='native',
        page_current=0,
        page_size=50,
        style_table={'width': '100%', 'minWidth': '100%'},
        style_cell={
            'textAlign': 'left',
            'padding': '10px',
            'minWidth': '100px',
            'maxWidth': '300px',
            'whiteSpace': 'normal',
            'height': 'auto',
            'overflow': 'hidden',
            'textOverflow': 'ellipsis'
        },
        style_header={
            'backgroundColor': '#4A90E2',
            'color': 'white',
            'fontWeight': 'bold',
            'position': 'sticky',
            'top': 0,
            'zIndex': 1
        },
        style_data_conditional=[
            {
                'if': {'filter_query': '{is_active} = 0'},
                'backgroundColor': '#FADBD8',
                'color': '#78281F'
            },
            {
                'if': {'filter_query': '{health_tier} = "Red"'},
                'backgroundColor': '#FADBD8'
            },
            {
                'if': {'filter_query': '{health_tier} = "Green"'},
                'backgroundColor': '#D5F4E6'
            },
            {
                'if': {'column_id': 'churn_risk_tier', 'filter_query': '{churn_risk_tier} = "High"'},
                'backgroundColor': '#FADBD8',
                'fontWeight': 'bold'
            },
        ],
        export_format='csv',
        export_headers='display'
    )

    # Events DataTable
    events_table = dash_table.DataTable(
        id='events-table',
        data=events_display.to_dict('records'),
        columns=[
            {
                'name': col.replace('_', ' ').title(),
                'id': col,
                'type': 'numeric' if events_display[col].dtype in ['int64', 'float64'] else 'text',
                'format': {
                    'specifier': ',.2f' if col == 'event_value_num' else ''
                }
            }
            for col in available_events_cols
        ],
        filter_action='native',
        sort_action='native',
        sort_mode='multi',
        page_action='native',
        page_current=0,
        page_size=50,
        style_table={'width': '100%', 'minWidth': '100%'},
        style_cell={
            'textAlign': 'left',
            'padding': '10px',
            'minWidth': '100px',
            'maxWidth': '300px',
            'whiteSpace': 'normal',
            'height': 'auto',
            'overflow': 'hidden',
            'textOverflow': 'ellipsis'
        },
        style_header={
            'backgroundColor': '#9B59B6',
            'color': 'white',
            'fontWeight': 'bold',
            'position': 'sticky',
            'top': 0,
            'zIndex': 1
        },
        style_data_conditional=[
            {
                'if': {'column_id': 'event_type', 'filter_query': '{event_type} = "subscription_cancelled"'},
                'backgroundColor': '#FADBD8',
                'fontWeight': 'bold'
            },
            {
                'if': {'column_id': 'event_type', 'filter_query': '{event_type} = "login"'},
                'backgroundColor': '#D5F4E6'
            },
        ],
        export_format='csv',
        export_headers='display'
    )

    # Layout
    layout = dbc.Container([
        html.H2("Raw Data Tables", className="mb-4"),

        # Summary cards
        dbc.Row([
            dbc.Col(SmartKPICard(
                "kpi_total_users",
                "Total Users",
                f"{len(users_df):,}",
                "",
                "fas fa-users",
                "primary",
                page_id="raw_data"
            ), md=3),
            dbc.Col(SmartKPICard(
                "kpi_total_events",
                "Total Events",
                f"{len(events_df):,}",
                "",
                "fas fa-stream",
                "info",
                page_id="raw_data"
            ), md=3),
            dbc.Col(SmartKPICard(
                "kpi_user_attributes",
                "User Attributes",
                f"{len(available_users_cols)}",
                "",
                "fas fa-database",
                "success",
                page_id="raw_data"
            ), md=3),
            dbc.Col(SmartKPICard(
                "kpi_event_types",
                "Event Types",
                f"{events_df['event_type'].nunique() if 'event_type' in events_df.columns else 0}",
                "",
                "fas fa-tags",
                "warning",
                page_id="raw_data"
            ), md=3),
        ], className="mb-4"),

        # Users table
        dbc.Row([
            dbc.Col(SmartTable(
                "table_users",
                users_table,
                f"Users Table ({len(users_df):,} records)",
                page_id="raw_data"
            ), md=12)
        ], className="mb-4"),

        # Events table
        dbc.Row([
            dbc.Col(SmartTable(
                "table_events",
                events_table,
                f"Events Table ({len(events_df):,} records)",
                page_id="raw_data"
            ), md=12)
        ])

    ], fluid=True)

    return layout
