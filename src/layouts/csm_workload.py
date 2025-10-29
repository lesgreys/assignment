"""
CSM Workload Dashboard
Track Customer Success Manager workload and account distribution.
"""

import dash_bootstrap_components as dbc
from dash import dcc, html, dash_table
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from components.smart_components import SmartKPICard, SmartGraph, SmartTable


def create_csm_workload(data_loader):
    """Create CSM Workload dashboard."""
    df = data_loader.get_master_data()

    # Filter to users with CSM
    csm_df = df[df['success_manager_assigned'] == 1].copy()

    if len(csm_df) == 0:
        return dbc.Container([
            html.H2("CSM Workload", className="mb-4"),
            dbc.Alert("No CSM assignments found in the data", color="info")
        ], fluid=True)

    # Accounts per CSM
    csm_counts = csm_df.groupby('csm_id').agg({
        'user_id': 'count',
        'annual_revenue': 'sum',
        'health_score': 'mean'
    }).reset_index()
    csm_counts.columns = ['csm_id', 'account_count', 'total_arr', 'avg_health_score']
    csm_counts = csm_counts.sort_values('account_count', ascending=False)

    accounts_fig = px.bar(
        csm_counts, x='csm_id', y='account_count',
        title='Accounts per CSM',
        labels={'account_count': 'Number of Accounts', 'csm_id': 'CSM ID'},
        color='account_count',
        color_continuous_scale='Blues'
    )

    # ARR per CSM
    arr_fig = px.bar(
        csm_counts, x='csm_id', y='total_arr',
        title='Total ARR per CSM',
        labels={'total_arr': 'Total ARR ($)', 'csm_id': 'CSM ID'},
        color='total_arr',
        color_continuous_scale='Greens'
    )
    arr_fig.update_yaxes(tickprefix='$', tickformat=',.0f')

    # Health score by CSM
    health_fig = px.bar(
        csm_counts, x='csm_id', y='avg_health_score',
        title='Average Health Score by CSM',
        labels={'avg_health_score': 'Avg Health Score', 'csm_id': 'CSM ID'},
        color='avg_health_score',
        color_continuous_scale='RdYlGn'
    )

    # At-risk accounts by CSM
    at_risk_by_csm = csm_df.groupby('csm_id').agg({
        'at_renewal_risk': 'sum',
        'health_tier': lambda x: (x == 'Red').sum()
    }).reset_index()
    at_risk_by_csm.columns = ['csm_id', 'renewal_risk_count', 'red_health_count']

    risk_fig = go.Figure(data=[
        go.Bar(name='Renewal Risk', x=at_risk_by_csm['csm_id'], y=at_risk_by_csm['renewal_risk_count'],
              marker_color='#F39C12'),
        go.Bar(name='Red Health', x=at_risk_by_csm['csm_id'], y=at_risk_by_csm['red_health_count'],
              marker_color='#E74C3C')
    ])
    risk_fig.update_layout(
        title='At-Risk Accounts by CSM',
        xaxis_title='CSM ID',
        yaxis_title='Number of Accounts',
        barmode='group'
    )

    # Portfolio breakdown by CSM
    portfolio_by_csm = csm_df.groupby(['csm_id', 'plan_type']).size().reset_index(name='count')
    portfolio_fig = px.bar(
        portfolio_by_csm, x='csm_id', y='count',
        color='plan_type',
        title='Account Mix by CSM',
        labels={'count': 'Number of Accounts', 'csm_id': 'CSM ID'},
        barmode='stack'
    )

    # CSM performance table
    csm_performance = csm_df.groupby('csm_id').agg({
        'user_id': 'count',
        'annual_revenue': ['sum', 'mean'],
        'health_score': 'mean',
        'nps_score': 'mean',
        'at_renewal_risk': 'sum',
        'support_tickets_last_90d': 'sum'
    }).reset_index()
    csm_performance.columns = ['CSM ID', 'Accounts', 'Total ARR', 'Avg ARR',
                               'Avg Health', 'Avg NPS', 'At Risk', 'Support Tickets']

    csm_table = dash_table.DataTable(
        data=csm_performance.round(2).to_dict('records'),
        columns=[
            {'name': 'CSM ID', 'id': 'CSM ID'},
            {'name': 'Accounts', 'id': 'Accounts'},
            {'name': 'Total ARR', 'id': 'Total ARR', 'type': 'numeric', 'format': {'specifier': '$,.0f'}},
            {'name': 'Avg ARR', 'id': 'Avg ARR', 'type': 'numeric', 'format': {'specifier': '$,.0f'}},
            {'name': 'Avg Health', 'id': 'Avg Health', 'type': 'numeric', 'format': {'specifier': '.1f'}},
            {'name': 'Avg NPS', 'id': 'Avg NPS', 'type': 'numeric', 'format': {'specifier': '.1f'}},
            {'name': 'At Risk', 'id': 'At Risk'},
            {'name': 'Support Tickets', 'id': 'Support Tickets'},
        ],
        style_table={'width': '100%', 'minWidth': '100%'},
        style_cell={'textAlign': 'left', 'padding': '10px', 'overflow': 'hidden', 'textOverflow': 'ellipsis'},
        style_header={'backgroundColor': '#4A90E2', 'color': 'white', 'fontWeight': 'bold'},
        style_data_conditional=[
            {'if': {'column_id': 'Avg Health', 'filter_query': '{Avg Health} < 60'},
             'backgroundColor': '#FADBD8'},
            {'if': {'column_id': 'At Risk', 'filter_query': '{At Risk} > 5'},
             'backgroundColor': '#FCF3CF'}
        ],
        sort_action='native',
        filter_action='native'
    )

    # Users without CSM
    no_csm = df[df['success_manager_assigned'] == 0]
    no_csm_high_value = no_csm[no_csm['annual_revenue'] > no_csm['annual_revenue'].median()]

    # Layout
    layout = dbc.Container([
        html.H2("CSM Workload Dashboard", className="mb-4"),

        # Summary cards
        dbc.Row([
            dbc.Col(SmartKPICard(
                "kpi_active_csms",
                "Active CSMs",
                f"{csm_df['csm_id'].nunique():,}",
                "",
                "fas fa-users",
                "primary",
                page_id="csm_workload"
            ), md=3),
            dbc.Col(SmartKPICard(
                "kpi_avg_accounts_per_csm",
                "Avg Accounts per CSM",
                f"{csm_counts['account_count'].mean():.1f}",
                "",
                "fas fa-user-friends",
                "info",
                page_id="csm_workload"
            ), md=3),
            dbc.Col(SmartKPICard(
                "kpi_avg_arr_per_csm",
                "Avg ARR per CSM",
                f"${csm_counts['total_arr'].mean():,.0f}",
                "",
                "fas fa-dollar-sign",
                "success",
                page_id="csm_workload"
            ), md=3),
            dbc.Col(SmartKPICard(
                "kpi_high_value_no_csm",
                "High-Value w/o CSM",
                f"{len(no_csm_high_value):,}",
                "",
                "fas fa-exclamation-triangle",
                "warning",
                page_id="csm_workload"
            ), md=3),
        ], className="mb-4"),

        # Charts row 1
        dbc.Row([
            dbc.Col(SmartGraph("chart_accounts_per_csm", accounts_fig, page_id="csm_workload"), md=6),
            dbc.Col(SmartGraph("chart_arr_per_csm", arr_fig, page_id="csm_workload"), md=6),
        ], className="mb-4"),

        # Charts row 2
        dbc.Row([
            dbc.Col(SmartGraph("chart_health_by_csm", health_fig, page_id="csm_workload"), md=6),
            dbc.Col(SmartGraph("chart_risk_by_csm", risk_fig, page_id="csm_workload"), md=6),
        ], className="mb-4"),

        # Portfolio mix
        dbc.Row([
            dbc.Col(SmartGraph("chart_account_mix", portfolio_fig, page_id="csm_workload"), md=12)
        ], className="mb-4"),

        # Performance table
        dbc.Row([
            dbc.Col(SmartTable(
                "table_csm_performance",
                csm_table,
                "CSM Performance Summary",
                page_id="csm_workload"
            ), md=12)
        ])

    ], fluid=True)

    return layout
