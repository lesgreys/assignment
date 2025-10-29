"""
User Flow & Timeline Dashboard
Visualize user journeys, event sequences, and time-series patterns.
Enhanced with user-specific filtering and interactive exploration.
"""

import dash_bootstrap_components as dbc
from dash import dcc, html, dash_table, Input, Output, State, callback
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np
from datetime import datetime, timedelta


def create_user_flow(data_loader):
    """Create User Flow & Timeline dashboard with user filtering."""
    df = data_loader.get_master_data()
    events_df = data_loader.get_events_data()

    # Prepare user options for dropdown
    user_options = [{'label': 'All Users (Aggregate View)', 'value': 'ALL'}]

    # Add top 100 most active users to dropdown
    top_users = events_df.groupby('user_id').size().reset_index(name='event_count')
    top_users = top_users.sort_values('event_count', ascending=False).head(100)

    # Merge with user data for richer labels
    top_users_info = top_users.merge(
        df[['user_id', 'plan_type', 'health_score', 'annual_revenue']],
        on='user_id',
        how='left'
    )

    for _, row in top_users_info.iterrows():
        label = f"{row['user_id']} | {row['plan_type']} | {row['event_count']} events | Health: {row['health_score']:.0f}"
        user_options.append({'label': label, 'value': row['user_id']})

    # Layout
    layout = dbc.Container([
        # Header
        dbc.Row([
            dbc.Col([
                html.H2("User Flow & Event Timeline", className="mb-2"),
                html.P("Explore user journeys, event patterns, and activity over time",
                       className="text-muted mb-3")
            ], md=12)
        ], className="mb-3"),

        # Filter controls
        dbc.Row([
            dbc.Col([
                html.Label("Active Status:", className="fw-bold mb-1", style={'fontSize': '0.9rem'}),
                dbc.RadioItems(
                    id='user-flow-active-filter',
                    options=[
                        {'label': 'All', 'value': 'all'},
                        {'label': 'Active', 'value': 'active'},
                        {'label': 'Inactive', 'value': 'inactive'}
                    ],
                    value='all',
                    inline=True,
                    className="mt-1"
                )
            ], md=3),
            dbc.Col([
                html.Label("Plan Type:", className="fw-bold mb-1", style={'fontSize': '0.9rem'}),
                dcc.Dropdown(
                    id='user-flow-plan-filter',
                    options=[
                        {'label': 'All Plans', 'value': 'all'},
                        {'label': 'Starter', 'value': 'starter'},
                        {'label': 'Pro', 'value': 'pro'},
                        {'label': 'Premium', 'value': 'premium'}
                    ],
                    value='all',
                    clearable=False,
                    style={'fontSize': '0.9rem'}
                )
            ], md=3),
            dbc.Col([
                html.Label("Health Tier:", className="fw-bold mb-1", style={'fontSize': '0.9rem'}),
                dcc.Dropdown(
                    id='user-flow-health-filter',
                    options=[
                        {'label': 'All Tiers', 'value': 'all'},
                        {'label': '🔴 Red', 'value': 'Red'},
                        {'label': '🟡 Yellow', 'value': 'Yellow'},
                        {'label': '🟢 Green', 'value': 'Green'}
                    ],
                    value='all',
                    clearable=False,
                    style={'fontSize': '0.9rem'}
                )
            ], md=3),
            dbc.Col([
                html.Label("CSM:", className="fw-bold mb-1", style={'fontSize': '0.9rem'}),
                dcc.Dropdown(
                    id='user-flow-csm-filter',
                    options=[{'label': 'All CSMs', 'value': 'all'}],
                    value='all',
                    clearable=False,
                    style={'fontSize': '0.9rem'}
                )
            ], md=3)
        ], className="mb-3 p-3 bg-light rounded"),

        # User selector
        dbc.Row([
            dbc.Col([
                html.Label("Select User:", className="fw-bold mb-2"),
                dcc.Dropdown(
                    id='user-flow-selector',
                    options=user_options,
                    value='ALL',
                    clearable=False,
                    searchable=True,
                    placeholder="Search by User ID...",
                    className="mb-3"
                )
            ], md=12)
        ], className="mb-4"),

        # Filter status and stats (dynamically updated)
        html.Div(id='user-flow-filter-status', className="mb-4"),

        # User info card (hidden for ALL, shown for specific user)
        html.Div(id='user-info-card', className="mb-4"),

        # Summary cards
        html.Div(id='user-flow-summary-cards', className="mb-4"),

        # Main timeline
        dbc.Row([
            dbc.Col(dbc.Card([
                dbc.CardHeader(html.H5("📈 Event Volume Over Time")),
                dbc.CardBody([
                    dcc.Graph(id='user-flow-timeline')
                ])
            ], className="shadow-sm"), md=12)
        ], className="mb-4"),

        # Lifecycle trends (signups/cancellations) - shown for aggregate view
        html.Div(id='user-flow-lifecycle-chart', className="mb-4"),

        # Event types and patterns
        dbc.Row([
            dbc.Col(dbc.Card([
                dbc.CardHeader(html.H5("📊 Event Types Distribution")),
                dbc.CardBody([
                    dcc.Graph(id='user-flow-event-types')
                ])
            ], className="shadow-sm"), md=12),
        ], className="mb-4"),

        # User journey and patterns
        dbc.Row([
            dbc.Col(dbc.Card([
                dbc.CardHeader(html.H5("🔀 User Journey Flow")),
                dbc.CardBody([
                    html.P("First 3 events in user journeys", className="text-muted mb-3"),
                    dcc.Graph(id='user-flow-sankey')
                ])
            ], className="shadow-sm"), md=12)
        ], className="mb-4"),

        # Detailed patterns
        dbc.Row([
            dbc.Col(dbc.Card([
                dbc.CardHeader(html.H5("📅 Activity by Day of Week")),
                dbc.CardBody([
                    dcc.Graph(id='user-flow-dow')
                ])
            ], className="shadow-sm"), md=6),
            dbc.Col(dbc.Card([
                dbc.CardHeader(html.H5("🔥 Recent Activity (Last 7 Days)")),
                dbc.CardBody([
                    dcc.Graph(id='user-flow-recent')
                ])
            ], className="shadow-sm"), md=6),
        ], className="mb-4"),

        # Event timeline table (for specific user)
        html.Div(id='user-event-timeline-table', className="mb-4"),

        # Store data for callbacks
        dcc.Store(id='user-flow-data-store', data={
            'events': events_df.to_dict('records'),
            'users': df[['user_id', 'plan_type', 'annual_revenue', 'health_score',
                        'health_tier', 'nps_score', 'signup_date', 'is_active', 'csm_id']].to_dict('records')
        })

    ], fluid=True)

    return layout


# Callback to update user dropdown and filter status based on filters
@callback(
    [Output('user-flow-selector', 'options'),
     Output('user-flow-csm-filter', 'options'),
     Output('user-flow-filter-status', 'children')],
    [Input('user-flow-active-filter', 'value'),
     Input('user-flow-plan-filter', 'value'),
     Input('user-flow-health-filter', 'value'),
     Input('user-flow-csm-filter', 'value')],
    [State('user-flow-data-store', 'data')],
    prevent_initial_call=True
)
def update_user_dropdown_filters(active_filter, plan_filter, health_filter, csm_filter, stored_data):
    """Filter user dropdown based on selected filters."""
    # Reconstruct dataframes
    events_df = pd.DataFrame(stored_data['events'])
    users_df = pd.DataFrame(stored_data['users'])

    # Apply filters
    filtered_users = users_df.copy()

    # Active status filter
    if active_filter == 'active':
        filtered_users = filtered_users[filtered_users['is_active'] == 1]
    elif active_filter == 'inactive':
        filtered_users = filtered_users[filtered_users['is_active'] == 0]

    # Plan type filter
    if plan_filter != 'all':
        filtered_users = filtered_users[filtered_users['plan_type'] == plan_filter]

    # Health tier filter
    if health_filter != 'all':
        filtered_users = filtered_users[filtered_users['health_tier'] == health_filter]

    # CSM filter (convert to string for comparison due to mixed types)
    if csm_filter != 'all' and 'csm_id' in filtered_users.columns:
        filtered_users = filtered_users[filtered_users['csm_id'].astype(str) == csm_filter]

    # Count events per user
    event_counts = events_df.groupby('user_id').size().reset_index(name='event_count')
    filtered_users = filtered_users.merge(event_counts, on='user_id', how='left')
    filtered_users['event_count'] = filtered_users['event_count'].fillna(0)

    # Sort by event count descending
    filtered_users = filtered_users.sort_values('event_count', ascending=False)

    # Create user options with improved labels
    user_options = [{'label': 'All Users (Aggregate View)', 'value': 'ALL'}]

    for _, row in filtered_users.iterrows():
        status = "✓ Active" if row['is_active'] == 1 else "✗ Inactive"
        label = f"{row['user_id']} | {row['plan_type'].title()} | {status} | {int(row['event_count'])} events | Health: {row['health_score']:.0f}"
        user_options.append({'label': label, 'value': row['user_id']})

    # Create CSM options
    csm_options = [{'label': 'All CSMs', 'value': 'all'}]
    if 'csm_id' in users_df.columns:
        # Convert to string and sort to handle mixed types
        unique_csms = users_df['csm_id'].dropna().astype(str).unique()
        unique_csms = sorted(unique_csms)
        for csm in unique_csms:
            csm_options.append({'label': csm, 'value': csm})

    # Create filter status display
    filters_active = []
    if active_filter != 'all':
        status_label = {'active': '✓ Active Only', 'inactive': '✗ Inactive Only'}
        filters_active.append(dbc.Badge(status_label[active_filter], color="primary", className="me-2 px-3 py-2"))
    if plan_filter != 'all':
        filters_active.append(dbc.Badge(f"📋 {plan_filter.title()}", color="info", className="me-2 px-3 py-2"))
    if health_filter != 'all':
        health_colors = {'Red': 'danger', 'Yellow': 'warning', 'Green': 'success'}
        health_icons = {'Red': '🔴', 'Yellow': '🟡', 'Green': '🟢'}
        filters_active.append(dbc.Badge(f"{health_icons[health_filter]} {health_filter} Health",
                                       color=health_colors[health_filter], className="me-2 px-3 py-2"))
    if csm_filter != 'all':
        filters_active.append(dbc.Badge(f"👤 CSM: {csm_filter}", color="secondary", className="me-2 px-3 py-2"))

    # Calculate aggregate stats for filtered users
    filtered_count = len(filtered_users)
    total_count = len(users_df)
    filtered_arr = filtered_users['annual_revenue'].sum() if len(filtered_users) > 0 else 0
    avg_health = filtered_users['health_score'].mean() if len(filtered_users) > 0 else 0

    # Calculate signup and cancellation counts for filtered users
    total_signups = len(filtered_users)
    filtered_user_ids_list = filtered_users['user_id'].tolist()
    total_cancellations = len(events_df[
        (events_df['event_type'] == 'subscription_cancelled') &
        (events_df['user_id'].isin(filtered_user_ids_list))
    ])

    # Create filter status component
    if filters_active:
        filter_status = dbc.Card([
            dbc.CardBody([
                dbc.Row([
                    dbc.Col([
                        html.Div([
                            html.Strong("Active Filters: ", className="me-2"),
                            *filters_active
                        ], className="mb-3")
                    ], md=12),
                ]),
                dbc.Row([
                    dbc.Col(dbc.Card([dbc.CardBody([
                        html.H4(f"{filtered_count:,}", className="text-primary mb-0"),
                        html.Small(f"of {total_count:,} users match", className="text-muted")
                    ])], className="text-center bg-light"), md=2),
                    dbc.Col(dbc.Card([dbc.CardBody([
                        html.H4(f"${filtered_arr:,.0f}", className="text-success mb-0"),
                        html.Small("Total ARR", className="text-muted")
                    ])], className="text-center bg-light"), md=2),
                    dbc.Col(dbc.Card([dbc.CardBody([
                        html.H4(f"{avg_health:.1f}", className="text-info mb-0"),
                        html.Small("Avg Health Score", className="text-muted")
                    ])], className="text-center bg-light"), md=2),
                    dbc.Col(dbc.Card([dbc.CardBody([
                        html.H4(f"{len(filtered_users[filtered_users['is_active']==1]):,}", className="text-warning mb-0"),
                        html.Small("Active Users", className="text-muted")
                    ])], className="text-center bg-light"), md=2),
                    dbc.Col(dbc.Card([dbc.CardBody([
                        html.H4(f"🟢 {total_signups:,}", className="mb-0", style={'color': '#27AE60'}),
                        html.Small("Signups", className="text-muted")
                    ])], className="text-center bg-light"), md=2),
                    dbc.Col(dbc.Card([dbc.CardBody([
                        html.H4(f"🔴 {total_cancellations:,}", className="mb-0", style={'color': '#E74C3C'}),
                        html.Small("Cancellations", className="text-muted")
                    ])], className="text-center bg-light"), md=2),
                ])
            ])
        ], className="shadow-sm border-primary")
    else:
        filter_status = html.Div()

    return user_options, csm_options, filter_status


def create_daily_hover_text(filtered_events, daily_events):
    """Create hover text showing all events for each day chronologically with timestamps."""
    hover_texts = []

    for _, day_row in daily_events.iterrows():
        day_date = day_row['event_date'].date() if hasattr(day_row['event_date'], 'date') else day_row['event_date']

        # Get all events for this day
        day_events = filtered_events[filtered_events['event_date'] == day_date].copy()

        # Sort by timestamp (chronological order)
        day_events = day_events.sort_values('event_ts')

        # Build hover text
        hover_parts = [
            f"<b>{day_date.strftime('%A, %B %d, %Y')}</b>",
            f"<b>Total: {len(day_events)} events</b>",
            ""
        ]

        # List events with timestamps (limit to 12 for readability)
        for idx, (_, event) in enumerate(day_events.head(12).iterrows()):
            time_str = event['event_ts'].strftime('%H:%M')
            event_name = event['event_type'].replace('_', ' ').title()
            hover_parts.append(f"• {event_name} ({time_str})")

        if len(day_events) > 12:
            hover_parts.append(f"<i>... {len(day_events) - 12} more events</i>")

        hover_texts.append("<br>".join(hover_parts))

    return hover_texts


# Callbacks for user flow filtering
@callback(
    [Output('user-info-card', 'children'),
     Output('user-flow-summary-cards', 'children'),
     Output('user-flow-timeline', 'figure'),
     Output('user-flow-lifecycle-chart', 'children'),
     Output('user-flow-event-types', 'figure'),
     Output('user-flow-sankey', 'figure'),
     Output('user-flow-dow', 'figure'),
     Output('user-flow-recent', 'figure'),
     Output('user-event-timeline-table', 'children')],
    [Input('user-flow-selector', 'value'),
     Input('user-flow-active-filter', 'value'),
     Input('user-flow-plan-filter', 'value'),
     Input('user-flow-health-filter', 'value'),
     Input('user-flow-csm-filter', 'value')],
    [State('user-flow-data-store', 'data')]
)
def update_user_flow(selected_user, active_filter, plan_filter, health_filter, csm_filter, stored_data):
    """Update all visualizations based on selected user and active filters."""

    # Reconstruct dataframes from stored data
    events_df = pd.DataFrame(stored_data['events'])
    users_df = pd.DataFrame(stored_data['users'])

    # Apply filters to users dataframe FIRST (for aggregate views)
    filtered_users_df = users_df.copy()

    if active_filter == 'active':
        filtered_users_df = filtered_users_df[filtered_users_df['is_active'] == 1]
    elif active_filter == 'inactive':
        filtered_users_df = filtered_users_df[filtered_users_df['is_active'] == 0]

    if plan_filter != 'all':
        filtered_users_df = filtered_users_df[filtered_users_df['plan_type'] == plan_filter]

    if health_filter != 'all':
        filtered_users_df = filtered_users_df[filtered_users_df['health_tier'] == health_filter]

    if csm_filter != 'all' and 'csm_id' in filtered_users_df.columns:
        filtered_users_df = filtered_users_df[filtered_users_df['csm_id'].astype(str) == csm_filter]

    # Convert timestamp
    events_df['event_ts'] = pd.to_datetime(events_df['event_ts'])
    events_df['event_date'] = events_df['event_ts'].dt.date
    events_df['hour'] = events_df['event_ts'].dt.hour
    events_df['day_of_week'] = events_df['event_ts'].dt.day_name()

    # Filter events based on user selection and active filters
    if selected_user != 'ALL':
        # Specific user selected
        filtered_events = events_df[events_df['user_id'] == selected_user].copy()
        user_info = users_df[users_df['user_id'] == selected_user].iloc[0] if len(users_df[users_df['user_id'] == selected_user]) > 0 else None
        title_suffix = f" - User {selected_user}"
    else:
        # Aggregate view - filter events by filtered users
        filtered_user_ids = filtered_users_df['user_id'].tolist()
        filtered_events = events_df[events_df['user_id'].isin(filtered_user_ids)].copy()
        user_info = None

        # Create descriptive title based on active filters
        filter_parts = []
        if active_filter != 'all':
            filter_parts.append({'active': 'Active', 'inactive': 'Inactive'}[active_filter])
        if plan_filter != 'all':
            filter_parts.append(plan_filter.title())
        if health_filter != 'all':
            filter_parts.append(f"{health_filter} Health")
        if csm_filter != 'all':
            filter_parts.append(f"CSM {csm_filter}")

        if filter_parts:
            title_suffix = f" - {' | '.join(filter_parts)} Users"
        else:
            title_suffix = " - All Users"

    # === USER INFO CARD (for specific user only) ===
    if user_info is not None:
        # Check for cancellation
        cancellation_events = filtered_events[filtered_events['event_type'] == 'subscription_cancelled']
        cancellation_date = None
        if len(cancellation_events) > 0:
            cancellation_date = cancellation_events['event_ts'].iloc[0].strftime('%Y-%m-%d')

        # Build profile columns
        profile_cols = [
            dbc.Col([
                html.Strong("Plan Type: "),
                html.Span(user_info['plan_type'].upper(),
                         className="badge bg-primary ms-2")
            ], md=2),
            dbc.Col([
                html.Strong("Health Score: "),
                html.Span(f"{user_info['health_score']:.1f}",
                         className=f"badge bg-{'success' if user_info['health_tier']=='Green' else 'warning' if user_info['health_tier']=='Yellow' else 'danger'} ms-2")
            ], md=2),
            dbc.Col([
                html.Strong("ARR: "),
                html.Span(f"${user_info['annual_revenue']:,.0f}",
                         className="badge bg-info ms-2")
            ], md=2),
            dbc.Col([
                html.Strong("NPS Score: "),
                html.Span(f"{user_info['nps_score']}",
                         className=f"badge bg-{'success' if user_info['nps_score']>0 else 'danger'} ms-2")
            ], md=2),
            dbc.Col([
                html.Strong("Signup: "),
                html.Span(str(user_info['signup_date'])[:10],
                         className="badge bg-secondary ms-2")
            ], md=2),
        ]

        # Add cancellation date if exists
        if cancellation_date:
            profile_cols.append(
                dbc.Col([
                    html.Strong("Cancelled: "),
                    html.Span(cancellation_date,
                             className="badge bg-danger ms-2")
                ], md=2)
            )

        info_card = dbc.Card([
            dbc.CardHeader(html.H5(f"👤 User Profile: {selected_user}")),
            dbc.CardBody([
                dbc.Row(profile_cols)
            ])
        ], className="shadow-sm bg-light")
    else:
        info_card = html.Div()

    # === SUMMARY CARDS ===
    total_events = len(filtered_events)
    unique_users = filtered_events['user_id'].nunique()
    avg_events = total_events / unique_users if unique_users > 0 else 0
    date_range = (filtered_events['event_ts'].max() - filtered_events['event_ts'].min()).days if len(filtered_events) > 0 else 0
    unique_event_types = filtered_events['event_type'].nunique() if len(filtered_events) > 0 else 0

    summary_cards = dbc.Row([
        dbc.Col(dbc.Card([dbc.CardBody([
            html.H4(f"{total_events:,}", className="text-primary"),
            html.P("Total Events")
        ])], className="text-center shadow-sm"), md=2),
        dbc.Col(dbc.Card([dbc.CardBody([
            html.H4(f"{unique_users:,}", className="text-info"),
            html.P("Active Users" if selected_user == 'ALL' else "Selected User")
        ])], className="text-center shadow-sm"), md=2),
        dbc.Col(dbc.Card([dbc.CardBody([
            html.H4(f"{avg_events:.1f}", className="text-success"),
            html.P("Avg Events/User" if selected_user == 'ALL' else "Events This User")
        ])], className="text-center shadow-sm"), md=2),
        dbc.Col(dbc.Card([dbc.CardBody([
            html.H4(f"{date_range}", className="text-warning"),
            html.P("Days of Activity")
        ])], className="text-center shadow-sm"), md=2),
        dbc.Col(dbc.Card([dbc.CardBody([
            html.H4(f"{unique_event_types}", className="text-danger"),
            html.P("Event Types")
        ])], className="text-center shadow-sm"), md=2),
        dbc.Col(dbc.Card([dbc.CardBody([
            html.H4(f"{len(filtered_events[filtered_events['event_date'] >= (pd.Timestamp('2025-08-01') - timedelta(days=7)).date()]):,}" if len(filtered_events) > 0 else "0"),
            html.P("Last 7 Days")
        ])], className="text-center shadow-sm"), md=2),
    ])

    # === TIMELINE FIGURE ===
    if len(filtered_events) > 0:
        daily_events = filtered_events.groupby('event_date').size().reset_index(name='event_count')
        daily_events['event_date'] = pd.to_datetime(daily_events['event_date'])

        timeline_fig = go.Figure()

        # Generate detailed hover text only for specific users (performance optimization)
        if selected_user != 'ALL':
            # Detailed hover with event-level details for single user
            hover_texts = create_daily_hover_text(filtered_events, daily_events)
            timeline_fig.add_trace(go.Scatter(
                x=daily_events['event_date'],
                y=daily_events['event_count'],
                mode='lines+markers',
                name='Events',
                line=dict(color='#4A90E2', width=3),
                marker=dict(size=6),
                fill='tozeroy',
                fillcolor='rgba(74, 144, 226, 0.2)',
                text=hover_texts,
                hovertemplate='%{text}<extra></extra>'
            ))
        else:
            # Simple hover for aggregate view (much faster)
            timeline_fig.add_trace(go.Scatter(
                x=daily_events['event_date'],
                y=daily_events['event_count'],
                mode='lines+markers',
                name='Events',
                line=dict(color='#4A90E2', width=3),
                marker=dict(size=6),
                fill='tozeroy',
                fillcolor='rgba(74, 144, 226, 0.2)',
                hovertemplate='<b>%{x|%B %d, %Y}</b><br>Total Events: %{y:,}<extra></extra>'
            ))

        # Add signup marker (green dot) - only for specific users
        if selected_user != 'ALL' and user_info is not None:
            signup_date = pd.to_datetime(user_info['signup_date'])
            signup_date_only = signup_date.date() if hasattr(signup_date, 'date') else signup_date

            # Get y-position for signup marker
            signup_match = daily_events[daily_events['event_date'].dt.date == signup_date_only]
            signup_y = signup_match['event_count'].iloc[0] if len(signup_match) > 0 else 0

            timeline_fig.add_trace(go.Scatter(
                x=[signup_date],
                y=[signup_y],
                mode='markers',
                name='Signup',
                marker=dict(
                    size=15,
                    color='green',
                    symbol='circle',
                    line=dict(color='darkgreen', width=2)
                ),
                hovertemplate='<b>🎉 Signup Date</b><br>%{x|%Y-%m-%d}<extra></extra>'
            ))

            # Add cancellation marker (red X) - only if user cancelled
            cancellation_events = filtered_events[filtered_events['event_type'] == 'subscription_cancelled']
            if len(cancellation_events) > 0:
                cancel_date = cancellation_events['event_ts'].iloc[0]
                cancel_date_only = cancel_date.date() if hasattr(cancel_date, 'date') else cancel_date

                # Get y-position for cancellation marker
                cancel_match = daily_events[daily_events['event_date'].dt.date == cancel_date_only]
                cancel_y = cancel_match['event_count'].iloc[0] if len(cancel_match) > 0 else 0

                timeline_fig.add_trace(go.Scatter(
                    x=[cancel_date],
                    y=[cancel_y],
                    mode='markers',
                    name='Cancelled',
                    marker=dict(
                        size=15,
                        color='red',
                        symbol='x',
                        line=dict(color='darkred', width=2)
                    ),
                    hovertemplate='<b>❌ Subscription Cancelled</b><br>%{x|%Y-%m-%d}<extra></extra>'
                ))

        timeline_fig.update_layout(
            title=f'Daily Event Volume{title_suffix}',
            xaxis_title='Date',
            yaxis_title='Number of Events',
            hovermode='closest',
            height=400,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            )
        )
    else:
        timeline_fig = go.Figure()
        timeline_fig.update_layout(title='No events data available')

    # === EVENT TYPES FIGURE ===
    if len(filtered_events) > 0:
        event_type_counts = filtered_events['event_type'].value_counts().head(15)
        event_types_fig = go.Figure(go.Bar(
            x=event_type_counts.values,
            y=event_type_counts.index,
            orientation='h',
            marker=dict(
                color=event_type_counts.values,
                colorscale='Blues',
                showscale=False
            ),
            hovertemplate='<b>%{y}</b><br>Count: %{x}<extra></extra>'
        ))
        event_types_fig.update_layout(
            title=f'Top Event Types{title_suffix}',
            xaxis_title='Count',
            yaxis_title='Event Type',
            height=500,
            yaxis={'categoryorder': 'total ascending'}
        )
    else:
        event_types_fig = go.Figure()
        event_types_fig.update_layout(title='No events data available')

    # === SANKEY DIAGRAM ===
    if len(filtered_events) > 0:
        # For specific user, show their journey; for all users, sample
        if selected_user != 'ALL':
            sample_events = filtered_events.sort_values('event_ts')
        else:
            sample_users = filtered_events['user_id'].unique()[:500]
            sample_events = filtered_events[filtered_events['user_id'].isin(sample_users)]

        user_sequences = []
        for user_id in sample_events['user_id'].unique():
            user_events = sample_events[sample_events['user_id'] == user_id].sort_values('event_ts')
            if len(user_events) >= 2:
                events_list = user_events['event_type'].head(3).tolist()
                if len(events_list) >= 2:
                    user_sequences.append({
                        'first': events_list[0],
                        'second': events_list[1],
                        'third': events_list[2] if len(events_list) > 2 else None
                    })

        if user_sequences:
            seq_df = pd.DataFrame(user_sequences)
            first_second = seq_df.groupby(['first', 'second']).size().reset_index(name='count')

            all_nodes = list(set(seq_df['first'].tolist() + seq_df['second'].tolist()))
            node_dict = {node: idx for idx, node in enumerate(all_nodes)}

            source = [node_dict[row['first']] for _, row in first_second.iterrows()]
            target = [node_dict[row['second']] for _, row in first_second.iterrows()]
            value = first_second['count'].tolist()

            sankey_fig = go.Figure(go.Sankey(
                node=dict(
                    pad=15,
                    thickness=20,
                    line=dict(color='black', width=0.5),
                    label=all_nodes,
                    color='#4A90E2'
                ),
                link=dict(
                    source=source,
                    target=target,
                    value=value,
                    color='rgba(74, 144, 226, 0.3)'
                )
            ))
            sankey_fig.update_layout(
                title=f'User Journey (First 2 Events){title_suffix}',
                font=dict(size=10),
                height=500
            )
        else:
            sankey_fig = go.Figure()
            sankey_fig.update_layout(title='Insufficient data for journey flow')
    else:
        sankey_fig = go.Figure()
        sankey_fig.update_layout(title='No events data available')

    # === DAY OF WEEK ===
    if len(filtered_events) > 0:
        dow_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        dow_events = filtered_events.groupby('day_of_week').size().reset_index(name='count')
        dow_events['day_of_week'] = pd.Categorical(dow_events['day_of_week'], categories=dow_order, ordered=True)
        dow_events = dow_events.sort_values('day_of_week')

        dow_fig = go.Figure()
        dow_fig.add_trace(go.Bar(
            x=dow_events['day_of_week'],
            y=dow_events['count'],
            marker_color='#E67E22',
            hovertemplate='<b>%{x}</b><br>Events: %{y}<extra></extra>'
        ))
        dow_fig.update_layout(
            title=f'Activity by Day{title_suffix}',
            xaxis_title='Day of Week',
            yaxis_title='Events',
            height=400
        )
    else:
        dow_fig = go.Figure()
        dow_fig.update_layout(title='No events data available')

    # === RECENT ACTIVITY ===
    if len(filtered_events) > 0:
        # Fixed reference date for consistent metrics (data snapshot date)
        cutoff_date = pd.Timestamp('2025-08-01') - timedelta(days=7)
        recent_events = filtered_events[filtered_events['event_ts'] >= cutoff_date]
        recent_daily = recent_events.groupby('event_date').size().reset_index(name='count')
        recent_daily['event_date'] = pd.to_datetime(recent_daily['event_date'])

        recent_fig = go.Figure()
        recent_fig.add_trace(go.Bar(
            x=recent_daily['event_date'],
            y=recent_daily['count'],
            marker_color='#1ABC9C',
            hovertemplate='<b>%{x|%Y-%m-%d}</b><br>Events: %{y}<extra></extra>'
        ))
        recent_fig.update_layout(
            title=f'Last 7 Days{title_suffix}',
            xaxis_title='Date',
            yaxis_title='Events',
            height=400
        )
    else:
        recent_fig = go.Figure()
        recent_fig.update_layout(title='No recent events')

    # === EVENT TIMELINE TABLE (for specific user) ===
    if selected_user != 'ALL' and len(filtered_events) > 0:
        timeline_data = filtered_events[['event_ts', 'event_type', 'event_value_num', 'event_value_txt']].copy()
        timeline_data['event_ts'] = timeline_data['event_ts'].dt.strftime('%Y-%m-%d %H:%M:%S')
        timeline_data = timeline_data.sort_values('event_ts', ascending=False).head(100)

        event_table = dbc.Card([
            dbc.CardHeader(html.H5(f"📋 Event Timeline - {selected_user} (Most Recent 100 Events)")),
            dbc.CardBody([
                dash_table.DataTable(
                    data=timeline_data.to_dict('records'),
                    columns=[
                        {'name': 'Timestamp', 'id': 'event_ts'},
                        {'name': 'Event Type', 'id': 'event_type'},
                        {'name': 'Value (Numeric)', 'id': 'event_value_num', 'type': 'numeric', 'format': {'specifier': ',.2f'}},
                        {'name': 'Value (Text)', 'id': 'event_value_txt'},
                    ],
                    style_table={'width': '100%', 'minWidth': '100%'},
                    style_cell={'textAlign': 'left', 'padding': '10px', 'overflow': 'hidden', 'textOverflow': 'ellipsis'},
                    style_header={'backgroundColor': '#4A90E2', 'color': 'white', 'fontWeight': 'bold'},
                    style_data_conditional=[
                        {
                            'if': {'column_id': 'event_type', 'filter_query': '{event_type} = "login"'},
                            'backgroundColor': '#D5F4E6'
                        },
                        {
                            'if': {'column_id': 'event_type', 'filter_query': '{event_type} = "subscription_cancelled"'},
                            'backgroundColor': '#FADBD8',
                            'fontWeight': 'bold'
                        },
                    ],
                    page_size=20,
                    sort_action='native',
                    filter_action='native'
                )
            ])
        ], className="shadow-sm")
    else:
        event_table = html.Div()

    # === LIFECYCLE CHART (Signups & Cancellations) ===
    # Show for aggregate view, hide for individual user
    if selected_user == 'ALL' and len(filtered_users_df) > 0:
        # Get signup dates for filtered users
        signup_data = filtered_users_df.copy()
        signup_data['signup_date'] = pd.to_datetime(signup_data['signup_date'])
        signups_by_date = signup_data.groupby(signup_data['signup_date'].dt.date).size().reset_index(name='signup_count')
        signups_by_date['signup_date'] = pd.to_datetime(signups_by_date['signup_date'])

        # Get cancellation dates from events for filtered users
        filtered_user_ids = filtered_users_df['user_id'].tolist()
        cancellation_events = events_df[
            (events_df['event_type'] == 'subscription_cancelled') &
            (events_df['user_id'].isin(filtered_user_ids))
        ].copy()

        if len(cancellation_events) > 0:
            cancellations_by_date = cancellation_events.groupby(
                cancellation_events['event_ts'].dt.date
            ).size().reset_index(name='cancellation_count')
            cancellations_by_date.columns = ['cancel_date', 'cancellation_count']
            cancellations_by_date['cancel_date'] = pd.to_datetime(cancellations_by_date['cancel_date'])
        else:
            cancellations_by_date = pd.DataFrame(columns=['cancel_date', 'cancellation_count'])

        # Create lifecycle figure
        lifecycle_fig = go.Figure()

        # Add signups trace
        lifecycle_fig.add_trace(go.Scatter(
            x=signups_by_date['signup_date'],
            y=signups_by_date['signup_count'],
            mode='lines+markers',
            name='Signups',
            line=dict(color='#27AE60', width=2),
            marker=dict(size=6, color='#27AE60'),
            fill='tozeroy',
            fillcolor='rgba(39, 174, 96, 0.1)',
            hovertemplate='<b>Signups</b><br>Date: %{x|%Y-%m-%d}<br>Count: %{y}<extra></extra>'
        ))

        # Add cancellations trace if data exists
        if len(cancellations_by_date) > 0:
            lifecycle_fig.add_trace(go.Scatter(
                x=cancellations_by_date['cancel_date'],
                y=cancellations_by_date['cancellation_count'],
                mode='lines+markers',
                name='Cancellations',
                line=dict(color='#E74C3C', width=2),
                marker=dict(size=6, color='#E74C3C'),
                fill='tozeroy',
                fillcolor='rgba(231, 76, 60, 0.1)',
                hovertemplate='<b>Cancellations</b><br>Date: %{x|%Y-%m-%d}<br>Count: %{y}<extra></extra>'
            ))

        # Calculate net growth
        all_dates = pd.DataFrame({
            'date': pd.concat([signups_by_date['signup_date'], cancellations_by_date['cancel_date']]).unique()
        })
        all_dates['date'] = pd.to_datetime(all_dates['date'])
        all_dates = all_dates.sort_values('date')

        all_dates = all_dates.merge(
            signups_by_date.rename(columns={'signup_date': 'date'}),
            on='date', how='left'
        ).fillna(0)

        all_dates = all_dates.merge(
            cancellations_by_date.rename(columns={'cancel_date': 'date'}),
            on='date', how='left'
        ).fillna(0)

        all_dates['net_growth'] = all_dates['signup_count'] - all_dates['cancellation_count']

        # Add net growth trace
        lifecycle_fig.add_trace(go.Scatter(
            x=all_dates['date'],
            y=all_dates['net_growth'],
            mode='lines',
            name='Net Growth',
            line=dict(color='#3498DB', width=2, dash='dash'),
            hovertemplate='<b>Net Growth</b><br>Date: %{x|%Y-%m-%d}<br>Net: %{y}<extra></extra>'
        ))

        lifecycle_fig.update_layout(
            title=f'Customer Lifecycle Trends{title_suffix}',
            xaxis_title='Date',
            yaxis_title='Count',
            hovermode='x unified',
            height=400,
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )

        lifecycle_chart = dbc.Row([
            dbc.Col(dbc.Card([
                dbc.CardHeader(html.H5("📊 Signups & Cancellations Over Time")),
                dbc.CardBody([dcc.Graph(figure=lifecycle_fig)])
            ], className="shadow-sm"), md=12)
        ])
    else:
        lifecycle_chart = html.Div()

    return (info_card, summary_cards, timeline_fig, lifecycle_chart, event_types_fig,
            sankey_fig, dow_fig, recent_fig, event_table)
