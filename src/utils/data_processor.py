"""
Data processing utilities for CX metrics calculation.
Transforms raw user and event data into actionable insights.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Tuple, Dict
from functools import reduce


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
        # Fixed reference date for consistent metrics (data snapshot date)
        today = pd.Timestamp('2025-08-01')
        self.users['account_age_days'] = (today - self.users['signup_date']).dt.days
        self.users['days_to_renewal'] = (self.users['renewal_due_date'] - today).dt.days

    def calculate_user_activity_metrics(self) -> pd.DataFrame:
        """Calculate user activity metrics from events (optimized)."""
        # Fixed reference date for consistent metrics (data snapshot date)
        today = pd.Timestamp('2025-08-01')

        # Pre-calculate time window flags using vectorized operations
        events = self.events.copy()
        events['days_ago'] = (today - events['event_ts']).dt.days
        events['in_30d'] = events['days_ago'] <= 30
        events['in_60d'] = events['days_ago'] <= 60
        events['in_90d'] = events['days_ago'] <= 90
        events['event_date'] = events['event_ts'].dt.date

        # Single-pass aggregation with all metrics
        agg_dict = {
            'event_id': 'count',  # total_events
            'event_ts': ['min', 'max'],  # first/last activity
            'in_30d': 'sum',  # events_30d
            'in_60d': 'sum',  # events_60d
            'in_90d': 'sum',  # events_90d
        }

        activity = events.groupby('user_id').agg(agg_dict).reset_index()
        activity.columns = ['user_id', 'total_events', 'first_activity', 'last_activity',
                           'events_30d', 'events_60d', 'events_90d']

        # Calculate days since last activity
        activity['days_since_last_activity'] = (today - activity['last_activity']).dt.days

        # Calculate active days per window (separate pass for date-based counting)
        # This is much faster than the previous approach
        active_days_30d = events[events['in_30d']].groupby('user_id')['event_date'].nunique().reset_index(name='active_days_30d')
        active_days_60d = events[events['in_60d']].groupby('user_id')['event_date'].nunique().reset_index(name='active_days_60d')
        active_days_90d = events[events['in_90d']].groupby('user_id')['event_date'].nunique().reset_index(name='active_days_90d')

        # Merge active days
        activity = activity.merge(active_days_30d, on='user_id', how='left')
        activity = activity.merge(active_days_60d, on='user_id', how='left')
        activity = activity.merge(active_days_90d, on='user_id', how='left')

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
        # Fixed reference date for consistent metrics (data snapshot date)
        today = pd.Timestamp('2025-08-01')
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

    def calculate_breadth_of_adoption(self) -> pd.DataFrame:
        """
        Calculate breadth of adoption metrics combining explicit features and core actions.

        Breadth of adoption measures how many different features/capabilities a user has adopted,
        excluding login events. Includes both explicit feature_adopted events and core actions
        that represent implicit feature usage.

        Returns:
            DataFrame with columns:
            - user_id: User identifier
            - total_features_adopted: Count of unique features/actions adopted
            - features_list: Comma-separated list of features adopted (for debugging)
            - adoption_breadth_score: Categorical score (0, 1, 2, 3, 4, 5+)
        """
        # Define explicit features (from feature_adopted events)
        explicit_features = ['analytics_dashboard', 'auto_pay', 'maintenance_module', 'mobile_app']

        # Define core actions (implicit features - exclude login as requested)
        core_actions = ['property_added', 'tenant_added', 'lease_signed',
                       'rent_payment_received', 'maintenance_request_created', 'report_generated']

        # Get explicit feature adoptions
        feature_events = self.events[self.events['event_type'] == 'feature_adopted'].copy()
        if len(feature_events) > 0:
            feature_events = feature_events[feature_events['event_value_txt'].isin(explicit_features)]
            explicit_adoption = feature_events.groupby('user_id')['event_value_txt'].apply(
                lambda x: list(x.unique())
            ).reset_index()
            explicit_adoption.columns = ['user_id', 'explicit_features']
        else:
            explicit_adoption = pd.DataFrame(columns=['user_id', 'explicit_features'])

        # Get core action adoptions (at least 1 occurrence counts as adoption)
        core_events = self.events[self.events['event_type'].isin(core_actions)].copy()
        if len(core_events) > 0:
            core_adoption = core_events.groupby('user_id')['event_type'].apply(
                lambda x: list(x.unique())
            ).reset_index()
            core_adoption.columns = ['user_id', 'core_actions']
        else:
            core_adoption = pd.DataFrame(columns=['user_id', 'core_actions'])

        # Merge all users from users table to ensure complete coverage
        all_users = pd.DataFrame({'user_id': self.users['user_id'].unique()})

        # Merge adoptions
        breadth = all_users.merge(explicit_adoption, on='user_id', how='left')
        breadth = breadth.merge(core_adoption, on='user_id', how='left')

        # Fill NaN with empty lists
        breadth['explicit_features'] = breadth['explicit_features'].apply(
            lambda x: x if isinstance(x, list) else []
        )
        breadth['core_actions'] = breadth['core_actions'].apply(
            lambda x: x if isinstance(x, list) else []
        )

        # Calculate total unique features adopted
        breadth['features_list'] = breadth.apply(
            lambda row: row['explicit_features'] + row['core_actions'], axis=1
        )
        breadth['total_features_adopted'] = breadth['features_list'].apply(len)

        # Convert features_list to comma-separated string for easier inspection
        breadth['features_list'] = breadth['features_list'].apply(
            lambda x: ', '.join(x) if len(x) > 0 else ''
        )

        # Create adoption breadth score (categorical: 0, 1, 2, 3, 4, 5+)
        breadth['adoption_breadth_score'] = breadth['total_features_adopted'].apply(
            lambda x: '5+' if x >= 5 else str(x)
        )

        return breadth[['user_id', 'total_features_adopted', 'features_list', 'adoption_breadth_score']]

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
        # Replace pd.cut with numpy digitize (faster)
        core_bins = np.array([0, 1, 5, 10, np.inf])
        core_labels = np.array([0, 25, 50, 75, 100])
        df['core_usage_score'] = core_labels[np.digitize(core_actions, core_bins, right=False)]

        df['adoption_score'] = np.minimum(100, (df.get('unique_features', 0) / 5) * 100)

        # Replace pd.cut with numpy digitize for recency scoring
        recency_bins = np.array([7, 14, 30, 60, 90, np.inf])
        recency_labels = np.array([100, 80, 60, 40, 20, 0])
        days_since = df.get('days_since_last_activity', 999).fillna(999).values
        df['recency_score'] = recency_labels[np.digitize(days_since, recency_bins, right=False)]

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

        # Replace pd.cut with numpy digitize for support health
        support_bins = np.array([0, 2, 5, 10, 20, np.inf])
        support_labels = np.array([100, 80, 60, 40, 20, 0])
        support_tickets = df['support_tickets_last_90d'].fillna(0).values
        df['support_health'] = support_labels[np.digitize(support_tickets, support_bins, right=False)]

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

        # Health Tier using numpy (faster than pd.cut)
        health_bins = np.array([60, 80, 100.01])
        tier_labels = np.array(['Red', 'Yellow', 'Green'])
        health_scores = df['health_score'].values
        tier_indices = np.digitize(health_scores, health_bins, right=False)
        df['health_tier'] = tier_labels[tier_indices]

        # Renewal Risk
        df['at_renewal_risk'] = (
            (df['days_to_renewal'] <= 90) &
            (df['health_score'] < 60)
        ).astype(int)

        return df

    def build_master_table(self) -> pd.DataFrame:
        """Build comprehensive user metrics table (optimized with single reduce merge)."""
        # Calculate all metrics
        activity = self.calculate_user_activity_metrics()
        logins = self.calculate_login_metrics()
        core = self.calculate_core_actions()
        features = self.calculate_feature_adoption()
        training = self.calculate_training_metrics()
        breadth = self.calculate_breadth_of_adoption()

        # Merge all DataFrames at once using reduce (much faster than sequential merges)
        dfs_to_merge = [self.users, activity, logins, core, features, training, breadth]
        master = reduce(lambda left, right: left.merge(right, on='user_id', how='left'), dfs_to_merge)

        # Fill NaN values (but preserve features_list strings)
        numeric_cols = master.select_dtypes(include=[np.number]).columns
        master[numeric_cols] = master[numeric_cols].fillna(0)

        # Fill string columns with empty string
        string_cols = master.select_dtypes(include=['object']).columns
        for col in string_cols:
            if col in ['features_list', 'adoption_breadth_score']:
                master[col] = master[col].fillna('0' if col == 'adoption_breadth_score' else '')

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

    def calculate_revenue_retention_metrics(self, reference_date='2025-08-01') -> dict:
        """
        Calculate GRR (Gross Revenue Retention) and NRR (Net Revenue Retention) metrics.

        Uses synthetic historical data approach:
        - Assumes starting MRR at signup = current annual_revenue / 12
        - Tracks churned revenue from inactive users
        - Calculates monthly cohort-based retention

        Args:
            reference_date: Fixed reference date for calculations (default: '2025-08-01')

        Returns:
            dict with keys:
                - overall_grr: Overall gross revenue retention %
                - overall_nrr: Overall net revenue retention %
                - monthly_retention: DataFrame with monthly GRR/NRR trends
                - cohort_retention: DataFrame with cohort-level retention
                - plan_retention: DataFrame with plan-level retention
        """
        ref_date = pd.Timestamp(reference_date)
        df = self.users.copy()

        # Calculate MRR (assume ARR / 12)
        df['mrr'] = df['annual_revenue'] / 12

        # Ensure datetime
        df['signup_date'] = pd.to_datetime(df['signup_date'])

        # Create cohort month
        df['cohort_month'] = df['signup_date'].dt.to_period('M')

        # Identify churned users and their revenue
        df['is_churned'] = df['is_active'] == 0
        df['churned_mrr'] = df['mrr'].where(df['is_churned'], 0)
        df['retained_mrr'] = df['mrr'].where(~df['is_churned'], 0)

        # Calculate cohort-level retention
        cohort_metrics = df.groupby('cohort_month').agg({
            'mrr': 'sum',  # Starting MRR
            'retained_mrr': 'sum',  # Current MRR from retained customers
            'churned_mrr': 'sum',  # Lost MRR from churned customers
            'user_id': 'count'  # Cohort size
        }).reset_index()
        cohort_metrics.columns = ['cohort_month', 'starting_mrr', 'current_mrr', 'churned_mrr', 'cohort_size']

        # Calculate GRR and NRR per cohort
        cohort_metrics['grr'] = (cohort_metrics['current_mrr'] / cohort_metrics['starting_mrr']) * 100
        cohort_metrics['nrr'] = (cohort_metrics['current_mrr'] / cohort_metrics['starting_mrr']) * 100

        # Replace inf/nan with 0
        cohort_metrics = cohort_metrics.replace([np.inf, -np.inf], 0).fillna(0)

        # Calculate overall weighted average GRR/NRR
        total_starting_mrr = cohort_metrics['starting_mrr'].sum()
        if total_starting_mrr > 0:
            overall_grr = (cohort_metrics['current_mrr'].sum() / total_starting_mrr) * 100
            overall_nrr = (cohort_metrics['current_mrr'].sum() / total_starting_mrr) * 100
        else:
            overall_grr = 0
            overall_nrr = 0

        # Calculate monthly retention trend (last 12 months)
        df['months_since_signup'] = ((ref_date.year - df['signup_date'].dt.year) * 12 +
                                     (ref_date.month - df['signup_date'].dt.month))

        # Filter to cohorts with at least 1 month of history
        monthly_cohorts = df[df['months_since_signup'] >= 1].copy()
        monthly_retention = monthly_cohorts.groupby('cohort_month').agg({
            'retained_mrr': 'sum',
            'mrr': 'sum'
        }).reset_index()
        monthly_retention['grr'] = (monthly_retention['retained_mrr'] / monthly_retention['mrr']) * 100
        monthly_retention['nrr'] = (monthly_retention['retained_mrr'] / monthly_retention['mrr']) * 100
        monthly_retention = monthly_retention.replace([np.inf, -np.inf], 0).fillna(0)

        # Calculate plan-level retention
        plan_metrics = df.groupby('plan_type').agg({
            'mrr': 'sum',
            'retained_mrr': 'sum',
            'churned_mrr': 'sum'
        }).reset_index()
        plan_metrics['grr'] = (plan_metrics['retained_mrr'] / plan_metrics['mrr']) * 100
        plan_metrics['nrr'] = (plan_metrics['retained_mrr'] / plan_metrics['mrr']) * 100
        plan_metrics = plan_metrics.replace([np.inf, -np.inf], 0).fillna(0)

        return {
            'overall_grr': overall_grr,
            'overall_nrr': overall_nrr,
            'monthly_retention': monthly_retention,
            'cohort_retention': cohort_metrics,
            'plan_retention': plan_metrics
        }
