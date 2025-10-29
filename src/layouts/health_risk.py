"""
Health & Risk Monitor Dashboard
Monitor customer health scores and identify at-risk accounts.
"""

import dash_bootstrap_components as dbc
from dash import dcc, html, dash_table, Input, Output, State, callback
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from components.smart_components import SmartKPICard, SmartGraph, SmartTable


def create_health_risk_monitor(data_loader):
    """Create Health & Risk Monitor dashboard."""
    df = data_loader.get_master_data()

    # Layout
    layout = dbc.Container([
        html.H2("Health & Risk Monitor", className="mb-4"),

        # Filter controls
        dbc.Row([
            dbc.Col([
                html.Label("Active Status:", className="fw-bold mb-1"),
                dbc.RadioItems(
                    id='health-risk-active-filter',
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
        html.Div(id='health-risk-kpi-cards', className="mb-4"),

        # Charts
        dbc.Row([
            dbc.Col(dcc.Graph(id='health-risk-health-score-distribution'), md=6),
            dbc.Col(dcc.Graph(id='health-risk-health-components'), md=6),
        ], className="mb-4"),

        dbc.Row([
            dbc.Col(dcc.Graph(id='health-risk-renewal-pipeline'), md=6),
            dbc.Col(dcc.Graph(id='health-risk-support-vs-health'), md=6),
        ], className="mb-4"),

        # Tables
        html.Div(id='health-risk-red-accounts-table', className="mb-4"),
        html.Div(id='health-risk-detractors-table'),

        # Store data for callbacks
        dcc.Store(id='health-risk-data-store', data=df.to_dict('records'))

    ], fluid=True)

    return layout


# Callback to update all visualizations based on filter
@callback(
    [Output('health-risk-kpi-cards', 'children'),
     Output('health-risk-health-score-distribution', 'figure'),
     Output('health-risk-health-components', 'figure'),
     Output('health-risk-renewal-pipeline', 'figure'),
     Output('health-risk-support-vs-health', 'figure'),
     Output('health-risk-red-accounts-table', 'children'),
     Output('health-risk-detractors-table', 'children')],
    [Input('health-risk-active-filter', 'value')],
    [State('health-risk-data-store', 'data')],
    prevent_initial_call=False
)
def update_health_risk_visuals(active_filter, stored_data):
    """Update all visualizations based on active status filter."""
    # Reconstruct dataframe
    df = pd.DataFrame(stored_data)

    # Apply active status filter
    if active_filter == 'active':
        df = df[df['is_active'] == 1]
    elif active_filter == 'inactive':
        df = df[df['is_active'] == 0]
    # 'all' means no filter

    # ========== KPI CALCULATIONS ==========
    detractors = df[df['nps_score'] < 0]

    # KPI Cards
    kpi_cards = dbc.Row([
        dbc.Col(SmartKPICard(
            "kpi_red_health",
            "Red Health Accounts",
            f"{len(df[df['health_tier']=='Red']):,}",
            "",
            "fas fa-exclamation-triangle",
            "danger",
            page_id="health_risk"
        ), md=3),
        dbc.Col(SmartKPICard(
            "kpi_renewal_risk",
            "At Renewal Risk",
            f"{len(df[df['at_renewal_risk']==1]):,}",
            "",
            "fas fa-calendar-times",
            "warning",
            page_id="health_risk"
        ), md=3),
        dbc.Col(SmartKPICard(
            "kpi_nps_detractors",
            "NPS Detractors",
            f"{len(detractors):,}",
            "",
            "fas fa-thumbs-down",
            "info",
            page_id="health_risk"
        ), md=3),
        dbc.Col(SmartKPICard(
            "kpi_avg_health_score",
            "Avg Health Score",
            f"{df['health_score'].mean():.1f}" if len(df) > 0 else "0.0",
            "",
            "fas fa-heartbeat",
            "success",
            page_id="health_risk"
        ), md=3),
    ])

    # ========== CHARTS ==========

    # Health score distribution
    health_fig = go.Figure()
    tier_colors = {'Green': '#27AE60', 'Yellow': '#F39C12', 'Red': '#E74C3C'}
    if len(df) > 0:
        for tier in ['Red', 'Yellow', 'Green']:
            tier_data = df[df['health_tier'] == tier]
            if len(tier_data) > 0:
                health_fig.add_trace(go.Histogram(
                    x=tier_data['health_score'],
                    name=tier,
                    marker_color=tier_colors[tier],
                    opacity=0.7
                ))
    health_fig.update_layout(
        title='Health Score Distribution by Tier',
        xaxis_title='Health Score',
        yaxis_title='Number of Users',
        barmode='overlay',
        height=400
    )

    # Health components breakdown
    if len(df) > 0:
        components = df[['usage_component', 'business_value_component',
                        'sentiment_component', 'engagement_component']].mean()
        components_fig = go.Figure(go.Bar(
            x=components.values,
            y=['Usage (40%)', 'Business Value (30%)', 'Sentiment (20%)', 'Engagement (10%)'],
            orientation='h',
            marker_color=['#3498DB', '#9B59B6', '#E67E22', '#1ABC9C']
        ))
        components_fig.update_layout(
            title='Average Health Component Scores',
            xaxis_title='Score (0-100)',
            yaxis_title='Component',
            height=400
        )
    else:
        components_fig = go.Figure()
        components_fig.update_layout(title='No data available', height=400)

    # Renewal pipeline
    renewal_fig = go.Figure()
    if len(df) > 0:
        renewal_30 = df[df['days_to_renewal'] <= 30]
        renewal_60 = df[(df['days_to_renewal'] > 30) & (df['days_to_renewal'] <= 60)]
        renewal_90 = df[(df['days_to_renewal'] > 60) & (df['days_to_renewal'] <= 90)]

        for period, period_df, color in [
            ('0-30 days', renewal_30, '#E74C3C'),
            ('31-60 days', renewal_60, '#F39C12'),
            ('61-90 days', renewal_90, '#F4D03F')
        ]:
            health_counts = period_df.groupby('health_tier').size()
            renewal_fig.add_trace(go.Bar(
                name=period,
                x=['Red', 'Yellow', 'Green'],
                y=[health_counts.get('Red', 0), health_counts.get('Yellow', 0), health_counts.get('Green', 0)],
                marker_color=color
            ))

    renewal_fig.update_layout(
        title='Renewal Pipeline by Health Status',
        xaxis_title='Health Tier',
        yaxis_title='Number of Accounts',
        barmode='group',
        height=400
    )

    # Support tickets vs health
    if len(df) > 0:
        df_plot = df.copy()
        df_plot['health_tier'] = df_plot['health_tier'].astype(str)

        support_fig = px.scatter(
            df_plot,
            x='support_tickets_last_90d',
            y='health_score',
            color='health_tier',
            size='annual_revenue',
            hover_data=['user_id', 'plan_type', 'nps_score'],
            color_discrete_map={'Green': '#27AE60', 'Yellow': '#F39C12', 'Red': '#E74C3C'},
            title='Support Tickets vs Health Score',
            category_orders={'health_tier': ['Red', 'Yellow', 'Green']}
        )
        support_fig.update_xaxes(title='Support Tickets (Last 90 days)')
        support_fig.update_yaxes(title='Health Score')
        support_fig.update_layout(height=400)
    else:
        support_fig = go.Figure()
        support_fig.update_layout(title='No data available', height=400)

    # ========== TABLES ==========

    # Red accounts table
    if len(df) > 0:
        red_accounts = df[df['health_tier'] == 'Red'].sort_values('annual_revenue', ascending=False)
        if len(red_accounts) > 0:
            red_table = dash_table.DataTable(
                data=red_accounts[['user_id', 'plan_type', 'annual_revenue', 'health_score',
                                  'days_to_renewal', 'nps_score', 'support_tickets_last_90d']].head(20).to_dict('records'),
                columns=[
                    {'name': 'User ID', 'id': 'user_id'},
                    {'name': 'Plan', 'id': 'plan_type'},
                    {'name': 'ARR', 'id': 'annual_revenue', 'type': 'numeric', 'format': {'specifier': '$,.0f'}},
                    {'name': 'Health Score', 'id': 'health_score', 'type': 'numeric', 'format': {'specifier': '.1f'}},
                    {'name': 'Days to Renewal', 'id': 'days_to_renewal'},
                    {'name': 'NPS', 'id': 'nps_score'},
                    {'name': 'Support Tickets', 'id': 'support_tickets_last_90d'},
                ],
                style_table={'width': '100%', 'minWidth': '100%'},
                style_cell={'textAlign': 'left', 'padding': '10px', 'overflow': 'hidden', 'textOverflow': 'ellipsis'},
                style_header={'backgroundColor': '#E74C3C', 'color': 'white', 'fontWeight': 'bold'},
                style_data_conditional=[
                    {'if': {'column_id': 'health_score', 'filter_query': '{health_score} < 40'},
                     'backgroundColor': '#FADBD8', 'color': '#78281F'}
                ],
                page_size=10
            )
            red_table_component = SmartTable(
                "table_red_accounts",
                red_table,
                "Red Health Accounts (Top 20 by ARR)",
                page_id="health_risk"
            )
        else:
            red_table_component = html.P("No red health accounts")
    else:
        red_table_component = html.P("No data available")

    # NPS detractors table
    if len(detractors) > 0:
        detractors_sorted = detractors.sort_values('annual_revenue', ascending=False).head(10)
        detractors_table = dbc.Table.from_dataframe(
            detractors_sorted[['user_id', 'plan_type', 'annual_revenue', 'nps_score', 'health_score']],
            striped=True, bordered=True, hover=True, size='sm'
        )
        detractors_component = SmartTable(
            "table_nps_detractors",
            detractors_table,
            "Top NPS Detractors",
            page_id="health_risk"
        )
    else:
        detractors_component = SmartTable(
            "table_nps_detractors",
            html.P("No detractors"),
            "Top NPS Detractors",
            page_id="health_risk"
        )

    return (kpi_cards, health_fig, components_fig, renewal_fig, support_fig,
            red_table_component, detractors_component)
