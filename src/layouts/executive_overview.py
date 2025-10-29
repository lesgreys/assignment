"""
Executive Overview Dashboard
High-level KPIs and trends for CX leadership.
"""

import dash_bootstrap_components as dbc
from dash import dcc, html
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd

from components.smart_components import SmartKPICard, SmartGraph, SmartTable


def create_executive_overview(data_loader):
    """
    Create Executive Overview dashboard layout.

    Args:
        data_loader: DataLoader instance

    Returns:
        Dash layout component
    """
    # Get data
    df = data_loader.get_master_data()
    stats = data_loader.get_summary_stats()

    # Calculate churn rate
    churn_rate = (stats['inactive_users'] / stats['total_users']) * 100

    # KPI Cards with info icons
    kpi_row = dbc.Row([
        dbc.Col(SmartKPICard(
            "kpi_total_arr",
            "Total ARR",
            f"${stats['total_arr']:,.0f}",
            f"Avg: ${stats['avg_arr']:,.0f}",
            "fas fa-dollar-sign",
            "success",
            page_id="executive_overview"
        ), md=3),
        dbc.Col(SmartKPICard(
            "kpi_active_users",
            "Active Users",
            f"{stats['active_users']:,}",
            f"{stats['total_users']:,} total",
            "fas fa-users",
            "primary",
            page_id="executive_overview"
        ), md=3),
        dbc.Col(SmartKPICard(
            "kpi_churn_rate",
            "Churn Rate",
            f"{churn_rate:.1f}%",
            f"{stats['inactive_users']} inactive",
            "fas fa-exclamation-triangle",
            "warning",
            page_id="executive_overview"
        ), md=3),
        dbc.Col(SmartKPICard(
            "kpi_avg_nps",
            "Avg NPS",
            f"{stats['avg_nps']:.1f}",
            "Customer satisfaction",
            "fas fa-star",
            "info",
            page_id="executive_overview"
        ), md=3),
    ], className="mb-4")

    # Health distribution pie chart
    health_data = pd.DataFrame.from_dict(stats['health_distribution'], orient='index', columns=['count'])
    if len(health_data) > 0:
        health_fig = px.pie(
            health_data,
            values='count',
            names=health_data.index,
            title='Customer Health Distribution',
            color=health_data.index,
            color_discrete_map={'Green': '#27AE60', 'Yellow': '#F39C12', 'Red': '#E74C3C'}
        )
        health_fig.update_traces(textposition='inside', textinfo='percent+label')
    else:
        health_fig = go.Figure()
        health_fig.update_layout(title='No health data available')

    # Plan distribution
    plan_data = pd.DataFrame.from_dict(stats['plan_distribution'], orient='index', columns=['count'])
    plan_fig = px.bar(
        plan_data,
        x=plan_data.index,
        y='count',
        title='Users by Plan Type',
        labels={'x': 'Plan Type', 'count': 'Number of Users'},
        color=plan_data.index,
        color_discrete_map={'starter': '#3498DB', 'pro': '#9B59B6', 'premium': '#E67E22'}
    )

    # ARR by plan type
    arr_by_plan = df.groupby('plan_type')['annual_revenue'].sum().reset_index()
    arr_fig = px.bar(
        arr_by_plan,
        x='plan_type',
        y='annual_revenue',
        title='ARR by Plan Type',
        labels={'plan_type': 'Plan Type', 'annual_revenue': 'Annual Revenue'},
        color='plan_type',
        color_discrete_map={'starter': '#3498DB', 'pro': '#9B59B6', 'premium': '#E67E22'}
    )
    arr_fig.update_yaxes(tickprefix='$', tickformat=',.0f')

    # NPS distribution
    nps_fig = go.Figure()
    nps_fig.add_trace(go.Histogram(
        x=df['nps_score'],
        nbinsx=20,
        marker_color='#4A90E2',
        name='NPS Distribution'
    ))
    nps_fig.update_layout(
        title='NPS Score Distribution',
        xaxis_title='NPS Score',
        yaxis_title='Number of Users',
        showlegend=False
    )

    # At-risk accounts table
    at_risk = df[df['at_renewal_risk'] == 1].sort_values('annual_revenue', ascending=False).head(10)
    at_risk_table = dbc.Table.from_dataframe(
        at_risk[['user_id', 'plan_type', 'annual_revenue', 'health_score',
                'days_to_renewal', 'nps_score']].round(2),
        striped=True,
        bordered=True,
        hover=True,
        size='sm',
        className='mt-2'
    )

    # Churn risk distribution
    churn_risk_data = df['churn_risk_tier'].value_counts()
    churn_risk_fig = px.pie(
        values=churn_risk_data.values,
        names=churn_risk_data.index,
        title='Churn Risk Distribution',
        color=churn_risk_data.index,
        color_discrete_map={'Low': '#27AE60', 'Medium': '#F39C12', 'High': '#E74C3C'}
    )
    churn_risk_fig.update_traces(textposition='inside', textinfo='percent+label')

    # Layout
    layout = dbc.Container([
        html.H2("Executive Overview", className="mb-4"),

        # KPIs
        kpi_row,

        # Charts row 1 - with info icons
        dbc.Row([
            dbc.Col(SmartGraph("chart_health_distribution", health_fig, page_id="executive_overview"), md=6),
            dbc.Col(SmartGraph("chart_churn_risk_distribution", churn_risk_fig, page_id="executive_overview"), md=6),
        ], className="mb-4"),

        # Charts row 2 - with info icons
        dbc.Row([
            dbc.Col(SmartGraph("chart_users_by_plan", plan_fig, page_id="executive_overview"), md=4),
            dbc.Col(SmartGraph("chart_arr_by_plan", arr_fig, page_id="executive_overview"), md=4),
            dbc.Col(SmartGraph("chart_nps_distribution", nps_fig, page_id="executive_overview"), md=4),
        ], className="mb-4"),

        # At-risk accounts - with info icon
        dbc.Row([
            dbc.Col(SmartTable(
                "table_at_risk",
                at_risk_table if len(at_risk) > 0 else html.P("No at-risk accounts", className="text-muted"),
                "🚨 Top 10 At-Risk Accounts",
                page_id="executive_overview"
            ), md=12)
        ])

    ], fluid=True)

    return layout
