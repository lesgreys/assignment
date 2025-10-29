"""
Adoption & Engagement Dashboard
Track feature adoption, usage patterns, and engagement metrics.
"""

import dash_bootstrap_components as dbc
from dash import dcc, html, Input, Output, State, callback
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


# Callback to update all visualizations based on filter
@callback(
    [Output('adoption-engagement-kpi-cards', 'children'),
     Output('adoption-engagement-breadth-distribution', 'figure'),
     Output('adoption-engagement-breadth-by-plan', 'figure'),
     Output('adoption-engagement-breadth-by-portfolio', 'figure'),
     Output('adoption-engagement-breadth-by-csm', 'figure'),
     Output('adoption-engagement-feature-co-adoption', 'figure'),
     Output('adoption-engagement-adoption-funnel', 'figure'),
     Output('adoption-engagement-engagement-recency', 'figure'),
     Output('adoption-engagement-top-features', 'figure'),
     Output('adoption-engagement-session-length', 'figure'),
     Output('adoption-engagement-training-completion', 'figure'),
     Output('adoption-engagement-report-types', 'figure')],
    [Input('adoption-engagement-active-filter', 'value')],
    [State('adoption-engagement-data-store', 'data')],
    prevent_initial_call=False
)
def update_adoption_engagement_visuals(active_filter, stored_data):
    """Update all visualizations based on active status filter."""
    # Reconstruct dataframes
    df = pd.DataFrame(stored_data['users'])
    events_df = pd.DataFrame(stored_data['events'])

    # Apply active status filter
    if active_filter == 'active':
        df = df[df['is_active'] == 1]
    elif active_filter == 'inactive':
        df = df[df['is_active'] == 0]
    # 'all' means no filter

    # Filter events to match filtered users
    filtered_user_ids = set(df['user_id'].values)
    events_df = events_df[events_df['user_id'].isin(filtered_user_ids)]

    # ========== KPI CALCULATIONS ==========
    mean_features = df['total_features_adopted'].mean() if 'total_features_adopted' in df.columns else 0
    median_features = df['total_features_adopted'].median() if 'total_features_adopted' in df.columns else 0
    users_with_2plus = len(df[df['total_features_adopted'] >= 2]) if 'total_features_adopted' in df.columns else 0
    total_users = len(df)
    breadth_score_pct = (users_with_2plus / total_users * 100) if total_users > 0 else 0

    # KPI Cards
    kpi_cards = dbc.Row([
        dbc.Col(SmartKPICard(
            "kpi_users_adopted",
            "Users Adopted Features",
            f"{len(df[df['total_features_adopted'].fillna(0) > 0]) if 'total_features_adopted' in df.columns else 0:,}",
            "",
            "fas fa-rocket",
            "primary",
            page_id="adoption_engagement"
        ), md=3),
        dbc.Col(SmartKPICard(
            "kpi_avg_features",
            "Avg Features Adopted",
            f"{mean_features:.1f}",
            f"Median: {median_features:.0f}",
            "fas fa-chart-bar",
            "info",
            page_id="adoption_engagement"
        ), md=3),
        dbc.Col(SmartKPICard(
            "kpi_breadth_score",
            "Users with 2+ Features",
            f"{breadth_score_pct:.1f}%",
            f"{users_with_2plus:,} of {total_users:,}",
            "fas fa-star",
            "success",
            page_id="adoption_engagement"
        ), md=3),
        dbc.Col(SmartKPICard(
            "kpi_avg_session",
            "Avg Session Length",
            f"{df['avg_session_30d'].fillna(0).mean() if 'avg_session_30d' in df.columns else 0:.1f} min",
            "",
            "fas fa-clock",
            "warning",
            page_id="adoption_engagement"
        ), md=3),
    ])

    # ========== BREADTH OF ADOPTION ANALYSIS ==========

    # Define features for breadth analysis
    explicit_features = ['analytics_dashboard', 'auto_pay', 'maintenance_module', 'mobile_app']
    core_actions = ['property_added', 'tenant_added', 'lease_signed',
                   'rent_payment_received', 'maintenance_request_created', 'report_generated']
    all_feature_names = explicit_features + core_actions
    breadth_order = ['0', '1', '2', '3', '4', '5+']

    # 1. Distribution Histogram
    if 'adoption_breadth_score' in df.columns and len(df) > 0:
        breadth_distribution = df['adoption_breadth_score'].value_counts()
        breadth_distribution = breadth_distribution.reindex(breadth_order, fill_value=0)

        breadth_hist_fig = go.Figure(go.Bar(
            x=breadth_order,
            y=breadth_distribution.values,
            marker_color='#3498DB',
            text=breadth_distribution.values,
            textposition='outside'
        ))
        breadth_hist_fig.update_layout(
            title='Feature Adoption Breadth Distribution',
            xaxis_title='Number of Features Adopted',
            yaxis_title='Number of Users',
            height=400
        )
    else:
        breadth_hist_fig = go.Figure()
        breadth_hist_fig.update_layout(title='No breadth data available', height=400)

    # 2. Breadth by Plan Type
    if 'plan_type' in df.columns and 'adoption_breadth_score' in df.columns and len(df) > 0:
        plan_breadth = df.groupby(['plan_type', 'adoption_breadth_score']).size().reset_index(name='count')
        breadth_by_plan_fig = px.bar(
            plan_breadth,
            x='adoption_breadth_score',
            y='count',
            color='plan_type',
            barmode='group',
            title='Adoption Breadth by Plan Type',
            labels={'adoption_breadth_score': 'Features Adopted', 'count': 'Number of Users'},
            color_discrete_map={'starter': '#3498DB', 'pro': '#9B59B6', 'premium': '#E67E22'},
            category_orders={'adoption_breadth_score': breadth_order}
        )
        breadth_by_plan_fig.update_layout(height=400)
    else:
        breadth_by_plan_fig = go.Figure()
        breadth_by_plan_fig.update_layout(title='No plan data available', height=400)

    # 3. Breadth by Portfolio Size
    if 'portfolio_size' in df.columns and 'total_features_adopted' in df.columns and len(df) > 0:
        df_portfolio = df.copy()
        df_portfolio['portfolio_category'] = pd.cut(
            df_portfolio['portfolio_size'],
            bins=[0, 5, 10, 20, float('inf')],
            labels=['1-5', '6-10', '11-20', '20+']
        )
        portfolio_breadth = df_portfolio.groupby('portfolio_category', observed=True)['total_features_adopted'].mean().reset_index()

        breadth_by_portfolio_fig = px.bar(
            portfolio_breadth,
            x='portfolio_category',
            y='total_features_adopted',
            title='Avg Features Adopted by Portfolio Size',
            labels={'portfolio_category': 'Portfolio Size', 'total_features_adopted': 'Avg Features'},
            color='total_features_adopted',
            color_continuous_scale='Blues'
        )
        breadth_by_portfolio_fig.update_layout(height=400)
    else:
        breadth_by_portfolio_fig = go.Figure()
        breadth_by_portfolio_fig.update_layout(title='No portfolio data available', height=400)

    # 4. Breadth by CSM Assignment
    if ('csm_assigned' in df.columns or 'success_manager_assigned' in df.columns) and len(df) > 0:
        df_csm = df.copy()
        csm_col = 'csm_assigned' if 'csm_assigned' in df.columns else 'success_manager_assigned'
        df_csm['has_csm'] = df_csm[csm_col].apply(lambda x: 'Assigned' if x == 1 else 'Unassigned')
        csm_breadth = df_csm.groupby('has_csm')['total_features_adopted'].agg(['mean', 'count']).reset_index()
        csm_breadth.columns = ['CSM Status', 'Avg Features', 'User Count']

        breadth_by_csm_fig = go.Figure()
        breadth_by_csm_fig.add_trace(go.Bar(
            x=csm_breadth['CSM Status'],
            y=csm_breadth['Avg Features'],
            marker_color=['#E67E22', '#3498DB'],
            text=csm_breadth['Avg Features'].round(2),
            textposition='outside'
        ))
        breadth_by_csm_fig.update_layout(
            title='Avg Features Adopted by CSM Assignment',
            xaxis_title='CSM Status',
            yaxis_title='Average Features Adopted',
            height=400
        )
    else:
        breadth_by_csm_fig = go.Figure()
        breadth_by_csm_fig.update_layout(title='No CSM data available', height=400)

    # 5. Feature Co-Adoption Heatmap
    if 'features_list' in df.columns and len(df) > 0:
        df_features = df[df['features_list'].str.len() > 0].copy()
        if len(df_features) > 0:
            df_features['features_array'] = df_features['features_list'].str.split(', ')

            # Build co-occurrence matrix
            co_occurrence = pd.DataFrame(0, index=all_feature_names, columns=all_feature_names)

            for features_list in df_features['features_array']:
                for f1, f2 in combinations(features_list, 2):
                    if f1 in all_feature_names and f2 in all_feature_names:
                        co_occurrence.loc[f1, f2] += 1
                        co_occurrence.loc[f2, f1] += 1

            co_adoption_fig = px.imshow(
                co_occurrence,
                labels=dict(x="Feature", y="Feature", color="Co-Adoptions"),
                title='Feature Co-Adoption Heatmap',
                color_continuous_scale='Blues',
                aspect='auto'
            )
            co_adoption_fig.update_layout(height=500)
        else:
            co_adoption_fig = go.Figure()
            co_adoption_fig.update_layout(title='Insufficient data for co-adoption analysis', height=500)
    else:
        co_adoption_fig = go.Figure()
        co_adoption_fig.update_layout(title='No feature list data available', height=500)

    # ========== DETAILED FEATURE METRICS ==========

    # Feature adoption funnel
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
    funnel_fig.update_layout(title='Core Feature Adoption Funnel', height=400)

    # Engagement by recency
    engagement_metrics = pd.DataFrame({
        'Metric': ['Active Last 7 Days', 'Active Last 30 Days', 'Active Last 90 Days'],
        'Users': [
            len(df[df['days_since_last_activity'] <= 7]) if 'days_since_last_activity' in df.columns else 0,
            len(df[df['days_since_last_activity'] <= 30]) if 'days_since_last_activity' in df.columns else 0,
            len(df[df['days_since_last_activity'] <= 90]) if 'days_since_last_activity' in df.columns else 0
        ]
    })
    engagement_fig = px.bar(
        engagement_metrics, x='Metric', y='Users',
        title='User Engagement by Recency',
        color='Metric'
    )
    engagement_fig.update_layout(height=400)

    # Top features adopted
    if len(events_df) > 0 and 'feature_adopted' in events_df['event_type'].values:
        features = events_df[events_df['event_type'] == 'feature_adopted']['event_value_txt'].value_counts().head(10)
        features_fig = px.bar(
            x=features.values, y=features.index,
            orientation='h',
            title='Top 10 Adopted Features',
            labels={'x': 'Number of Adoptions', 'y': 'Feature'}
        )
        features_fig.update_layout(height=400)
    else:
        features_fig = go.Figure()
        features_fig.update_layout(title='No feature adoption data available', height=400)

    # Session length distribution
    session_fig = go.Figure()
    if 'avg_session_30d' in df.columns and len(df) > 0:
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
        yaxis_title='Number of Users',
        height=400
    )

    # Training completion
    if 'trainings_attended' in df.columns and len(df) > 0:
        training_data = df[df['trainings_attended'].fillna(0) > 0]
        if len(training_data) > 0:
            training_fig = px.histogram(
                training_data,
                x='trainings_attended',
                title='Training Completion Distribution',
                labels={'trainings_attended': 'Number of Trainings Attended'}
            )
            training_fig.update_layout(height=400)
        else:
            training_fig = go.Figure()
            training_fig.update_layout(title='No training data available', height=400)
    else:
        training_fig = go.Figure()
        training_fig.update_layout(title='No training data available', height=400)

    # Report generation by type
    if len(events_df) > 0 and 'report_generated' in events_df['event_type'].values:
        reports = events_df[events_df['event_type'] == 'report_generated']['event_value_txt'].value_counts()
        reports_fig = px.pie(
            values=reports.values,
            names=reports.index,
            title='Report Types Generated'
        )
        reports_fig.update_layout(height=400)
    else:
        reports_fig = go.Figure()
        reports_fig.update_layout(title='No report data available', height=400)

    return (kpi_cards, breadth_hist_fig, breadth_by_plan_fig, breadth_by_portfolio_fig,
            breadth_by_csm_fig, co_adoption_fig, funnel_fig, engagement_fig,
            features_fig, session_fig, training_fig, reports_fig)
