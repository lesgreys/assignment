"""
Adoption & Engagement Dashboard
Track feature adoption, usage patterns, and engagement metrics.
"""

import dash_bootstrap_components as dbc
from dash import dcc, html
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from components.smart_components import SmartKPICard, SmartGraph


def create_adoption_engagement(data_loader):
    """Create Adoption & Engagement dashboard."""
    df = data_loader.get_master_data()
    events_df = data_loader.get_events_data()

    # Feature adoption funnel - use .get() with fillna for missing columns
    adoption_metrics = {
        'Logged In': len(df[df['total_logins'].fillna(0) > 0]) if 'total_logins' in df.columns else 0,
        'Added Property': len(df[df['property_added_count'].fillna(0) > 0]) if 'property_added_count' in df.columns else 0,
        'Added Tenant': len(df[df['tenant_added_count'].fillna(0) > 0]) if 'tenant_added_count' in df.columns else 0,
        'Signed Lease': len(df[df['lease_signed_count'].fillna(0) > 0]) if 'lease_signed_count' in df.columns else 0,
        'Received Payment': len(df[df['payments_received'].fillna(0) > 0]) if 'payments_received' in df.columns else 0
    }

    funnel_fig = go.Figure(go.Funnel(
        y=list(adoption_metrics.keys()),
        x=list(adoption_metrics.values()),
        textinfo="value+percent initial",
        marker={"color": ["#3498DB", "#9B59B6", "#E67E22", "#1ABC9C", "#27AE60"]}
    ))
    funnel_fig.update_layout(title='Core Feature Adoption Funnel')

    # DAU/WAU/MAU trend (simulated from active days)
    engagement_metrics = pd.DataFrame({
        'Metric': ['Active Last 7 Days', 'Active Last 30 Days', 'Active Last 90 Days'],
        'Users': [
            len(df[df['days_since_last_activity'] <= 7]),
            len(df[df['days_since_last_activity'] <= 30]),
            len(df[df['days_since_last_activity'] <= 90])
        ]
    })
    engagement_fig = px.bar(
        engagement_metrics, x='Metric', y='Users',
        title='User Engagement by Recency',
        color='Metric'
    )

    # Top features adopted
    if 'feature_adopted' in events_df['event_type'].values:
        features = events_df[events_df['event_type'] == 'feature_adopted']['event_value_txt'].value_counts().head(10)
        features_fig = px.bar(
            x=features.values, y=features.index,
            orientation='h',
            title='Top 10 Adopted Features',
            labels={'x': 'Number of Adoptions', 'y': 'Feature'}
        )
    else:
        features_fig = go.Figure()
        features_fig.update_layout(title='No feature adoption data available')

    # Session length distribution
    session_fig = go.Figure()
    if 'avg_session_30d' in df.columns:
        session_data = df[df['avg_session_30d'].fillna(0) > 0]['avg_session_30d']
        if len(session_data) > 0:
            session_fig.add_trace(go.Histogram(
                x=session_data,
                nbinsx=30,
                marker_color='#4A90E2'
            ))
    session_fig.update_layout(
        title='Average Session Length Distribution (Last 30 Days)',
        xaxis_title='Session Length (minutes)',
        yaxis_title='Number of Users'
    )

    # Training completion
    if 'trainings_attended' in df.columns:
        training_data = df[df['trainings_attended'].fillna(0) > 0]
        if len(training_data) > 0:
            training_fig = px.histogram(
                training_data,
                x='trainings_attended',
                title='Training Completion Distribution',
                labels={'trainings_attended': 'Number of Trainings Attended'}
            )
        else:
            training_fig = go.Figure()
            training_fig.update_layout(title='No training data available')
    else:
        training_fig = go.Figure()
        training_fig.update_layout(title='No training data available')

    # Report generation by type
    if 'report_generated' in events_df['event_type'].values:
        reports = events_df[events_df['event_type'] == 'report_generated']['event_value_txt'].value_counts()
        reports_fig = px.pie(
            values=reports.values,
            names=reports.index,
            title='Report Types Generated'
        )
    else:
        reports_fig = go.Figure()
        reports_fig.update_layout(title='No report data available')

    # Layout
    layout = dbc.Container([
        html.H2("Adoption & Engagement", className="mb-4"),

        # Summary cards
        dbc.Row([
            dbc.Col(SmartKPICard(
                "kpi_users_adopted",
                "Users Adopted Features",
                f"{len(df[df['unique_features'].fillna(0) > 0]) if 'unique_features' in df.columns else 0:,}",
                "",
                "fas fa-rocket",
                "primary",
                page_id="adoption_engagement"
            ), md=3),
            dbc.Col(SmartKPICard(
                "kpi_avg_logins",
                "Avg Logins (30d)",
                f"{df['logins_30d'].fillna(0).mean() if 'logins_30d' in df.columns else 0:.1f}",
                "",
                "fas fa-sign-in-alt",
                "info",
                page_id="adoption_engagement"
            ), md=3),
            dbc.Col(SmartKPICard(
                "kpi_avg_session",
                "Avg Session Length",
                f"{df['avg_session_30d'].fillna(0).mean() if 'avg_session_30d' in df.columns else 0:.1f} min",
                "",
                "fas fa-clock",
                "success",
                page_id="adoption_engagement"
            ), md=3),
            dbc.Col(SmartKPICard(
                "kpi_training_attendees",
                "Training Attendees",
                f"{len(df[df['trainings_attended'].fillna(0) > 0]) if 'trainings_attended' in df.columns else 0:,}",
                "",
                "fas fa-graduation-cap",
                "warning",
                page_id="adoption_engagement"
            ), md=3),
        ], className="mb-4"),

        # Charts
        dbc.Row([
            dbc.Col(SmartGraph("chart_adoption_funnel", funnel_fig, page_id="adoption_engagement"), md=6),
            dbc.Col(SmartGraph("chart_engagement_recency", engagement_fig, page_id="adoption_engagement"), md=6),
        ], className="mb-4"),

        dbc.Row([
            dbc.Col(SmartGraph("chart_top_features", features_fig, page_id="adoption_engagement"), md=6),
            dbc.Col(SmartGraph("chart_session_length", session_fig, page_id="adoption_engagement"), md=6),
        ], className="mb-4"),

        dbc.Row([
            dbc.Col(SmartGraph("chart_training_completion", training_fig, page_id="adoption_engagement"), md=6),
            dbc.Col(SmartGraph("chart_report_types", reports_fig, page_id="adoption_engagement"), md=6),
        ])

    ], fluid=True)

    return layout
