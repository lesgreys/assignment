"""
Revenue Analytics Dashboard
ARR analysis, revenue metrics, and expansion opportunities.
"""

import dash_bootstrap_components as dbc
from dash import dcc, html
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from components.smart_components import SmartKPICard, SmartGraph, SmartTable


def create_revenue_analytics(data_loader):
    """Create Revenue Analytics dashboard."""
    df = data_loader.get_master_data()

    # ARR by plan type
    arr_by_plan = df.groupby('plan_type')['annual_revenue'].agg(['sum', 'mean', 'count']).reset_index()
    arr_by_plan.columns = ['plan_type', 'total_arr', 'avg_arr', 'user_count']

    arr_fig = px.bar(
        arr_by_plan, x='plan_type', y='total_arr',
        title='Total ARR by Plan Type',
        labels={'total_arr': 'Total ARR ($)', 'plan_type': 'Plan Type'},
        color='plan_type',
        text='total_arr'
    )
    arr_fig.update_traces(texttemplate='$%{text:,.0f}', textposition='outside')
    arr_fig.update_yaxes(tickprefix='$', tickformat=',.0f')

    # ARR per user by plan
    arr_per_user_fig = px.bar(
        arr_by_plan, x='plan_type', y='avg_arr',
        title='Average ARR per User by Plan',
        labels={'avg_arr': 'Avg ARR ($)', 'plan_type': 'Plan Type'},
        color='plan_type'
    )
    arr_per_user_fig.update_yaxes(tickprefix='$', tickformat=',.0f')

    # Portfolio size vs ARR
    portfolio_fig = px.scatter(
        df, x='portfolio_size', y='annual_revenue',
        color='plan_type',
        size='health_score',
        hover_data=['user_id', 'nps_score'],
        title='Portfolio Size vs ARR',
        labels={'portfolio_size': 'Portfolio Size (# Properties)', 'annual_revenue': 'Annual Revenue ($)'}
    )
    portfolio_fig.update_yaxes(tickprefix='$', tickformat=',.0f')

    # Revenue at risk (low health + high ARR)
    revenue_at_risk = df[df['health_tier'].isin(['Red', 'Yellow'])].groupby('health_tier')['annual_revenue'].sum()
    risk_fig = px.pie(
        values=revenue_at_risk.values,
        names=revenue_at_risk.index,
        title='ARR at Risk by Health Tier',
        color=revenue_at_risk.index,
        color_discrete_map={'Yellow': '#F39C12', 'Red': '#E74C3C'}
    )
    risk_fig.update_traces(textposition='inside', textinfo='percent+label+value',
                          texttemplate='%{label}<br>$%{value:,.0f}')

    # Expansion opportunities (starter/pro on green health)
    expansion = df[(df['health_tier'] == 'Green') & (df['plan_type'].isin(['starter', 'pro']))]
    expansion_arr = expansion['annual_revenue'].sum()

    # ARR distribution
    arr_bins = [0, 1000, 5000, 10000, 25000, 50000, 100000, float('inf')]
    arr_labels = ['<$1K', '$1-5K', '$5-10K', '$10-25K', '$25-50K', '$50-100K', '>$100K']
    df['arr_bucket'] = pd.cut(df['annual_revenue'], bins=arr_bins, labels=arr_labels)

    arr_dist_fig = px.histogram(
        df, x='arr_bucket',
        title='ARR Distribution',
        labels={'arr_bucket': 'ARR Range', 'count': 'Number of Users'},
        color='plan_type'
    )

    # Revenue per property
    df['revenue_per_property'] = df['annual_revenue'] / df['portfolio_size'].replace(0, 1)
    rev_per_prop_fig = px.box(
        df[df['portfolio_size'] > 0],
        x='plan_type',
        y='revenue_per_property',
        title='Revenue per Property by Plan Type',
        labels={'revenue_per_property': 'Revenue per Property ($)', 'plan_type': 'Plan Type'},
        color='plan_type'
    )
    rev_per_prop_fig.update_yaxes(tickprefix='$', tickformat=',.0f')

    # Expansion opportunity table
    expansion_table = dbc.Table.from_dataframe(
        expansion.nlargest(10, 'annual_revenue')[['user_id', 'plan_type', 'annual_revenue',
                                                   'health_score', 'portfolio_size', 'nps_score']],
        striped=True, bordered=True, hover=True, size='sm'
    )

    # Layout
    layout = dbc.Container([
        html.H2("Revenue Analytics", className="mb-4"),

        # Summary cards
        dbc.Row([
            dbc.Col(SmartKPICard(
                "kpi_total_arr_revenue",
                "Total ARR",
                f"${df['annual_revenue'].sum():,.0f}",
                "",
                "fas fa-dollar-sign",
                "primary",
                page_id="revenue_analytics"
            ), md=3),
            dbc.Col(SmartKPICard(
                "kpi_avg_arr",
                "Average ARR",
                f"${df['annual_revenue'].mean():,.0f}",
                "",
                "fas fa-chart-line",
                "info",
                page_id="revenue_analytics"
            ), md=3),
            dbc.Col(SmartKPICard(
                "kpi_arr_at_risk",
                "ARR at Risk",
                f"${revenue_at_risk.sum():,.0f}",
                "",
                "fas fa-exclamation-triangle",
                "warning",
                page_id="revenue_analytics"
            ), md=3),
            dbc.Col(SmartKPICard(
                "kpi_expansion_opportunity",
                "Expansion Opportunity",
                f"${expansion_arr:,.0f}",
                "",
                "fas fa-arrow-up",
                "success",
                page_id="revenue_analytics"
            ), md=3),
        ], className="mb-4"),

        # Charts
        dbc.Row([
            dbc.Col(SmartGraph("chart_arr_by_plan_revenue", arr_fig, page_id="revenue_analytics"), md=6),
            dbc.Col(SmartGraph("chart_avg_arr_by_plan", arr_per_user_fig, page_id="revenue_analytics"), md=6),
        ], className="mb-4"),

        dbc.Row([
            dbc.Col(SmartGraph("chart_portfolio_vs_arr", portfolio_fig, page_id="revenue_analytics"), md=8),
            dbc.Col(SmartGraph("chart_arr_at_risk_breakdown", risk_fig, page_id="revenue_analytics"), md=4),
        ], className="mb-4"),

        dbc.Row([
            dbc.Col(SmartGraph("chart_arr_distribution", arr_dist_fig, page_id="revenue_analytics"), md=6),
            dbc.Col(SmartGraph("chart_revenue_per_property", rev_per_prop_fig, page_id="revenue_analytics"), md=6),
        ], className="mb-4"),

        # Expansion opportunities
        dbc.Row([
            dbc.Col(SmartTable(
                "table_expansion_opportunities",
                expansion_table if len(expansion) > 0 else html.P("No expansion opportunities"),
                "Top 10 Expansion Opportunities (Green Health, Starter/Pro Plans)",
                page_id="revenue_analytics"
            ), md=12)
        ])

    ], fluid=True)

    return layout
