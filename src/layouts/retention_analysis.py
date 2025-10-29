"""
Retention Analysis Dashboard
Cohort analysis, churn tracking, and retention metrics.
"""

import dash_bootstrap_components as dbc
from dash import dcc, html
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np
from components.smart_components import SmartKPICard, SmartGraph


def create_retention_analysis(data_loader):
    """Create Retention Analysis dashboard."""
    df = data_loader.get_master_data()
    cohort_df = data_loader.get_cohort_retention()

    # Cohort retention heatmap
    if len(cohort_df) > 0:
        pivot_df = cohort_df.pivot(
            index='cohort_month',
            columns='months_since_signup',
            values='retention_rate'
        )

        # Limit to recent cohorts for readability
        pivot_df = pivot_df.tail(12)

        cohort_fig = go.Figure(data=go.Heatmap(
            z=pivot_df.values,
            x=[f'Month {i}' for i in pivot_df.columns],
            y=[str(idx) for idx in pivot_df.index],
            colorscale='RdYlGn',
            text=np.round(pivot_df.values, 1),
            texttemplate='%{text}%',
            textfont={"size": 10},
            colorbar=dict(title="Retention %")
        ))
        cohort_fig.update_layout(
            title='Cohort Retention Heatmap (Last 12 Cohorts)',
            xaxis_title='Months Since Signup',
            yaxis_title='Signup Cohort'
        )
    else:
        cohort_fig = go.Figure()
        cohort_fig.update_layout(title='Insufficient data for cohort analysis')

    # Churn by plan type
    churn_by_plan = df.groupby('plan_type').agg({
        'user_id': 'count',
        'is_active': lambda x: (x == 0).sum()
    }).reset_index()
    churn_by_plan['churn_rate'] = (churn_by_plan['is_active'] / churn_by_plan['user_id']) * 100
    churn_by_plan.columns = ['plan_type', 'total_users', 'churned_users', 'churn_rate']

    churn_plan_fig = px.bar(
        churn_by_plan, x='plan_type', y='churn_rate',
        title='Churn Rate by Plan Type',
        labels={'churn_rate': 'Churn Rate (%)', 'plan_type': 'Plan Type'},
        color='plan_type'
    )

    # Account age distribution
    age_fig = px.histogram(
        df, x='account_age_days',
        nbins=30,
        title='Account Age Distribution',
        labels={'account_age_days': 'Account Age (days)'}
    )

    # Churn prediction distribution
    # Ensure categorical columns are strings
    df_plot = df.copy()
    df_plot['churn_risk_tier'] = df_plot['churn_risk_tier'].astype(str)
    df_plot['health_tier'] = df_plot['health_tier'].astype(str)

    churn_risk_by_tier = df_plot.groupby(['churn_risk_tier', 'health_tier']).size().reset_index(name='count')
    churn_risk_fig = px.bar(
        churn_risk_by_tier,
        x='churn_risk_tier',
        y='count',
        color='health_tier',
        title='Churn Risk by Health Tier',
        barmode='stack',
        color_discrete_map={'Green': '#27AE60', 'Yellow': '#F39C12', 'Red': '#E74C3C'},
        category_orders={'churn_risk_tier': ['Low', 'Medium', 'High'], 'health_tier': ['Red', 'Yellow', 'Green']}
    )

    # Churn drivers analysis
    churned_users = df[df['is_active'] == 0]
    active_users = df[df['is_active'] == 1]

    drivers_data = pd.DataFrame({
        'Metric': ['Avg Health Score', 'Avg NPS', 'Avg Logins (30d)', 'Avg Features'],
        'Churned': [
            churned_users['health_score'].mean() if len(churned_users) > 0 else 0,
            churned_users['nps_score'].mean() if len(churned_users) > 0 else 0,
            churned_users['logins_30d'].mean() if len(churned_users) > 0 else 0,
            churned_users['unique_features'].mean() if len(churned_users) > 0 else 0
        ],
        'Active': [
            active_users['health_score'].mean(),
            active_users['nps_score'].mean(),
            active_users['logins_30d'].mean(),
            active_users['unique_features'].mean()
        ]
    })

    drivers_fig = go.Figure(data=[
        go.Bar(name='Churned', x=drivers_data['Metric'], y=drivers_data['Churned'], marker_color='#E74C3C'),
        go.Bar(name='Active', x=drivers_data['Metric'], y=drivers_data['Active'], marker_color='#27AE60')
    ])
    drivers_fig.update_layout(
        title='Churn Drivers: Churned vs Active Users',
        barmode='group'
    )

    # Layout
    layout = dbc.Container([
        html.H2("Retention Analysis", className="mb-4"),

        # Summary cards
        dbc.Row([
            dbc.Col(SmartKPICard(
                "kpi_churn_rate",
                "Overall Churn Rate",
                f"{(df['is_active']==0).sum() / len(df) * 100:.1f}%",
                "",
                "fas fa-user-slash",
                "danger",
                page_id="retention_analysis"
            ), md=3),
            dbc.Col(SmartKPICard(
                "kpi_high_churn_risk",
                "High Churn Risk",
                f"{len(df[df['churn_risk_tier']=='High']):,}",
                "",
                "fas fa-exclamation-circle",
                "warning",
                page_id="retention_analysis"
            ), md=3),
            dbc.Col(SmartKPICard(
                "kpi_avg_account_age",
                "Avg Account Age",
                f"{df['account_age_days'].mean():.0f} days",
                "",
                "fas fa-calendar",
                "info",
                page_id="retention_analysis"
            ), md=3),
            dbc.Col(SmartKPICard(
                "kpi_retained_users",
                "Retained Users",
                f"{len(df[df['is_active']==1]):,}",
                "",
                "fas fa-user-check",
                "success",
                page_id="retention_analysis"
            ), md=3),
        ], className="mb-4"),

        # Cohort heatmap
        dbc.Row([
            dbc.Col(SmartGraph("chart_cohort_retention", cohort_fig, page_id="retention_analysis"), md=12)
        ], className="mb-4"),

        # Charts
        dbc.Row([
            dbc.Col(SmartGraph("chart_churn_by_plan", churn_plan_fig, page_id="retention_analysis"), md=6),
            dbc.Col(SmartGraph("chart_churn_risk_by_health", churn_risk_fig, page_id="retention_analysis"), md=6),
        ], className="mb-4"),

        dbc.Row([
            dbc.Col(SmartGraph("chart_account_age", age_fig, page_id="retention_analysis"), md=6),
            dbc.Col(SmartGraph("chart_churn_drivers", drivers_fig, page_id="retention_analysis"), md=6),
        ])

    ], fluid=True)

    return layout
