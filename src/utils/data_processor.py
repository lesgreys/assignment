"""
Data processing utilities for CX metrics calculation.
Transforms raw user and event data into actionable insights.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Tuple, Dict


class CXDataProcessor:
    """Process user and event data to calculate CX metrics."""

    def __init__(self, users_df: pd.DataFrame, events_df: pd.DataFrame):
        """
        Initialize with raw data.

        Args:
            users_df: Users table
            events_df: Events table
        """
        self.users = users_df.copy()
        self.events = events_df.copy()
        self._prepare_data()

    def _prepare_data(self):
        """Prepare and validate data."""
        # Ensure datetime columns
        if not pd.api.types.is_datetime64_any_dtype(self.users['signup_date']):
            self.users['signup_date'] = pd.to_datetime(self.users['signup_date'])
        if not pd.api.types.is_datetime64_any_dtype(self.users['renewal_due_date']):
            self.users['renewal_due_date'] = pd.to_datetime(self.users['renewal_due_date'])
        if not pd.api.types.is_datetime64_any_dtype(self.events['event_ts']):
            self.events['event_ts'] = pd.to_datetime(self.events['event_ts'])

        # Calculate derived user fields
        today = pd.Timestamp.now()
        self.users['account_age_days'] = (today - self.users['signup_date']).dt.days
        self.users['days_to_renewal'] = (self.users['renewal_due_date'] - today).dt.days

    def calculate_user_activity_metrics(self) -> pd.DataFrame:
        """Calculate user activity metrics from events."""
        today = pd.Timestamp.now()

        # Overall activity
        activity = self.events.groupby('user_id').agg({
            'event_id': 'count',
            'event_ts': ['min', 'max']
        }).reset_index()
        activity.columns = ['user_id', 'total_events', 'first_activity', 'last_activity']
        activity['days_since_last_activity'] = (today - activity['last_activity']).dt.days

        # Time-windowed activity
        for days in [30, 60, 90]:
            cutoff = today - timedelta(days=days)
            recent = self.events[self.events['event_ts'] >= cutoff]

            events_count = recent.groupby('user_id').size().reset_index(name=f'events_{days}d')
            activity = activity.merge(events_count, on='user_id', how='left')

            active_days = recent.groupby('user_id')['event_ts'].apply(
                lambda x: x.dt.date.nunique()
            ).reset_index(name=f'active_days_{days}d')
            activity = activity.merge(active_days, on='user_id', how='left')

        # Fill NaN with 0
        activity = activity.fillna(0)

        return activity

    def calculate_login_metrics(self) -> pd.DataFrame:
        """Calculate login-specific metrics."""
        logins = self.events[self.events['event_type'] == 'login'].copy()

        if len(logins) == 0:
            return pd.DataFrame(columns=['user_id', 'total_logins', 'logins_30d',
                                        'avg_session_length', 'avg_session_30d'])

        metrics = logins.groupby('user_id').agg({
            'event_id': 'count',
            'event_value_num': 'mean'
        }).reset_index()
        metrics.columns = ['user_id', 'total_logins', 'avg_session_length']

        # 30-day metrics
        today = pd.Timestamp.now()
        recent = logins[logins['event_ts'] >= today - timedelta(days=30)]
        recent_metrics = recent.groupby('user_id').agg({
            'event_id': 'count',
            'event_value_num': 'mean'
        }).reset_index()
        recent_metrics.columns = ['user_id', 'logins_30d', 'avg_session_30d']

        metrics = metrics.merge(recent_metrics, on='user_id', how='left')
        metrics = metrics.fillna(0)

        return metrics

    def calculate_core_actions(self) -> pd.DataFrame:
        """Calculate core product action metrics."""
        core_events = [
            'property_added', 'tenant_added', 'lease_signed',
            'rent_payment_received', 'maintenance_request_created',
            'report_generated'
        ]

        core = self.events[self.events['event_type'].isin(core_events)].copy()

        if len(core) == 0:
            return pd.DataFrame(columns=['user_id'] + [f'{e}_count' for e in core_events])

        # Count each event type
        pivot = core.pivot_table(
            index='user_id',
            columns='event_type',
            values='event_id',
            aggfunc='count',
            fill_value=0
        ).reset_index()

        # Rename columns
        pivot.columns = ['user_id'] + [f'{col}_count' for col in pivot.columns[1:]]

        # Calculate total rent collected
        if 'rent_payment_received' in self.events['event_type'].values:
            rent = self.events[self.events['event_type'] == 'rent_payment_received']
            rent_sum = rent.groupby('user_id')['event_value_num'].sum().reset_index()
            rent_sum.columns = ['user_id', 'total_rent_collected']
            pivot = pivot.merge(rent_sum, on='user_id', how='left')

        return pivot

    def calculate_feature_adoption(self) -> pd.DataFrame:
        """Calculate feature adoption metrics."""
        features = self.events[self.events['event_type'] == 'feature_adopted'].copy()

        if len(features) == 0:
            return pd.DataFrame(columns=['user_id', 'features_adopted',
                                        'unique_features'])

        metrics = features.groupby('user_id').agg({
            'event_id': 'count',
            'event_value_txt': lambda x: x.nunique()
        }).reset_index()
        metrics.columns = ['user_id', 'features_adopted', 'unique_features']

        return metrics

    def calculate_training_metrics(self) -> pd.DataFrame:
        """Calculate training attendance metrics."""
        training = self.events[self.events['event_type'] == 'training_attended'].copy()

        if len(training) == 0:
            return pd.DataFrame(columns=['user_id', 'trainings_attended',
                                        'unique_training_types'])

        metrics = training.groupby('user_id').agg({
            'event_id': 'count',
            'event_value_txt': lambda x: x.nunique()
        }).reset_index()
        metrics.columns = ['user_id', 'trainings_attended', 'unique_training_types']

        return metrics

    def calculate_health_scores(self, user_metrics: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate composite health scores.

        Args:
            user_metrics: DataFrame with all user metrics

        Returns:
            DataFrame with health scores added
        """
        df = user_metrics.copy()

        # Usage Score (0-100) - 40% weight
        df['login_score'] = np.minimum(100, (df.get('logins_30d', 0) / 20) * 100)
        df['session_score'] = np.minimum(100, (df.get('avg_session_30d', 0) / 30) * 100)

        core_actions = (df.get('property_added_count', 0) +
                       df.get('tenant_added_count', 0) +
                       df.get('lease_signed_count', 0))
        df['core_usage_score'] = pd.cut(core_actions, bins=[-1, 0, 1, 5, 10, np.inf],
                                        labels=[0, 25, 50, 75, 100]).astype(float)

        df['adoption_score'] = np.minimum(100, (df.get('unique_features', 0) / 5) * 100)

        recency_bins = [-1, 7, 14, 30, 60, 90, np.inf]
        recency_labels = [100, 80, 60, 40, 20, 0]
        df['recency_score'] = pd.cut(df.get('days_since_last_activity', 999),
                                     bins=recency_bins, labels=recency_labels).astype(float)

        df['usage_component'] = (
            df['login_score'] * 0.15 +
            df['session_score'] * 0.10 +
            df['core_usage_score'] * 0.30 +
            df['adoption_score'] * 0.25 +
            df['recency_score'] * 0.20
        )

        # Business Value Score (0-100) - 30% weight
        max_arr = df['annual_revenue'].max() if df['annual_revenue'].max() > 0 else 1
        df['arr_score'] = (df['annual_revenue'] / max_arr) * 100
        df['portfolio_score'] = np.minimum(100, (df['portfolio_size'] / 20) * 100)
        df['plan_score'] = df['plan_type'].map({
            'premium': 100, 'pro': 65, 'starter': 35
        }).fillna(0)

        df['business_value_component'] = (
            df['arr_score'] * 0.40 +
            df['portfolio_score'] * 0.30 +
            df['plan_score'] * 0.30
        )

        # Sentiment Score (0-100) - 20% weight
        df['nps_normalized'] = (df['nps_score'] + 100) / 2

        support_bins = [-1, 0, 2, 5, 10, 20, np.inf]
        support_labels = [100, 80, 60, 40, 20, 0]
        df['support_health'] = pd.cut(df['support_tickets_last_90d'],
                                      bins=support_bins, labels=support_labels).astype(float)

        df['sentiment_component'] = (
            df['nps_normalized'] * 0.60 +
            df['support_health'] * 0.40
        )

        # Engagement Score (0-100) - 10% weight
        df['training_score'] = np.minimum(100, (df.get('trainings_attended', 0) / 3) * 100)
        df['reporting_score'] = np.minimum(100, (df.get('report_generated_count', 0) / 10) * 100)
        df['consistency_score'] = (df.get('active_days_30d', 0) / 30) * 100

        df['engagement_component'] = (
            df['training_score'] * 0.30 +
            df['reporting_score'] * 0.30 +
            df['consistency_score'] * 0.40
        )

        # Overall Health Score
        df['health_score'] = (
            df['usage_component'] * 0.40 +
            df['business_value_component'] * 0.30 +
            df['sentiment_component'] * 0.20 +
            df['engagement_component'] * 0.10
        )

        # Ensure health score is within bounds and handle NaN
        df['health_score'] = df['health_score'].fillna(0).clip(0, 100)

        # Health Tier
        df['health_tier'] = pd.cut(df['health_score'],
                                   bins=[-0.01, 60, 80, 100.01],
                                   labels=['Red', 'Yellow', 'Green'])

        # Convert categorical to string and handle any remaining NaN
        df['health_tier'] = df['health_tier'].astype(str).replace('nan', 'Red')

        # Renewal Risk
        df['at_renewal_risk'] = (
            (df['days_to_renewal'] <= 90) &
            (df['health_score'] < 60)
        ).astype(int)

        return df

    def build_master_table(self) -> pd.DataFrame:
        """Build comprehensive user metrics table."""
        # Start with users
        master = self.users.copy()

        # Add activity metrics
        activity = self.calculate_user_activity_metrics()
        master = master.merge(activity, on='user_id', how='left')

        # Add login metrics
        logins = self.calculate_login_metrics()
        master = master.merge(logins, on='user_id', how='left')

        # Add core actions
        core = self.calculate_core_actions()
        master = master.merge(core, on='user_id', how='left')

        # Add feature adoption
        features = self.calculate_feature_adoption()
        master = master.merge(features, on='user_id', how='left')

        # Add training
        training = self.calculate_training_metrics()
        master = master.merge(training, on='user_id', how='left')

        # Fill NaN values
        master = master.fillna(0)

        # Calculate health scores
        master = self.calculate_health_scores(master)

        return master

    def calculate_cohort_retention(self) -> pd.DataFrame:
        """Calculate cohort retention analysis."""
        # Create cohort month
        self.users['cohort_month'] = self.users['signup_date'].dt.to_period('M')

        # Get monthly activity per user
        self.events['activity_month'] = self.events['event_ts'].dt.to_period('M')

        user_months = self.events.groupby(['user_id', 'activity_month']).size().reset_index(name='events')

        # Merge with cohort
        cohort_data = user_months.merge(
            self.users[['user_id', 'cohort_month']],
            on='user_id'
        )

        # Calculate months since signup
        cohort_data['months_since_signup'] = (
            (cohort_data['activity_month'] - cohort_data['cohort_month']).apply(lambda x: x.n)
        )

        # Calculate retention
        cohort_size = self.users.groupby('cohort_month').size().reset_index(name='cohort_users')

        retention = cohort_data.groupby(['cohort_month', 'months_since_signup']).agg({
            'user_id': 'nunique'
        }).reset_index()
        retention.columns = ['cohort_month', 'months_since_signup', 'active_users']

        retention = retention.merge(cohort_size, on='cohort_month')
        retention['retention_rate'] = (retention['active_users'] / retention['cohort_users']) * 100

        return retention
