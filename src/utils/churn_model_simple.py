"""
Simple Rule-Based Churn Prediction
Lightweight alternative to ML-based prediction for Vercel deployment.
"""

import pandas as pd
import numpy as np
from typing import Tuple, Dict


def build_churn_predictions(master_df: pd.DataFrame) -> Tuple[pd.DataFrame, None, Dict]:
    """
    Build churn predictions using simple rule-based logic.

    This is a lightweight alternative to the ML-based approach that doesn't
    require scikit-learn, making it suitable for serverless deployments.

    Args:
        master_df: Master dataframe with user metrics

    Returns:
        Tuple of (predictions_df, None, metrics_dict)
    """

    # Create predictions dataframe
    predictions = master_df[['user_id']].copy()

    # Calculate churn risk score based on multiple factors
    risk_score = 0

    # Factor 1: Low engagement (30%)
    if 'days_since_last_activity' in master_df.columns:
        days_inactive = master_df['days_since_last_activity'].fillna(0)
        risk_score += (days_inactive / days_inactive.max()) * 0.3

    # Factor 2: Low usage (25%)
    if 'avg_events_per_day' in master_df.columns:
        usage = master_df['avg_events_per_day'].fillna(0)
        max_usage = usage.max()
        if max_usage > 0:
            risk_score += (1 - (usage / max_usage)) * 0.25

    # Factor 3: Declining activity trend (20%)
    if 'activity_trend' in master_df.columns:
        trend = master_df['activity_trend'].fillna(0)
        # Negative trend increases risk
        risk_score += np.where(trend < 0, abs(trend) * 0.2, 0)

    # Factor 4: Near renewal date (15%)
    if 'days_to_renewal' in master_df.columns:
        days_to_renewal = master_df['days_to_renewal'].fillna(365)
        # Risk increases as renewal approaches
        risk_score += np.where(
            days_to_renewal < 30,
            (30 - days_to_renewal) / 30 * 0.15,
            0
        )

    # Factor 5: Low feature adoption (10%)
    if 'unique_events' in master_df.columns:
        features = master_df['unique_events'].fillna(0)
        max_features = features.max()
        if max_features > 0:
            risk_score += (1 - (features / max_features)) * 0.1

    # Normalize to 0-1 range
    predictions['churn_probability'] = np.clip(risk_score, 0, 1)

    # Assign risk tiers
    predictions['churn_risk_tier'] = pd.cut(
        predictions['churn_probability'],
        bins=[0, 0.3, 0.6, 1.0],
        labels=['Low', 'Medium', 'High']
    )

    # Calculate metrics
    metrics = {
        'model_type': 'rule_based',
        'high_risk_count': (predictions['churn_risk_tier'] == 'High').sum(),
        'medium_risk_count': (predictions['churn_risk_tier'] == 'Medium').sum(),
        'low_risk_count': (predictions['churn_risk_tier'] == 'Low').sum(),
        'avg_churn_probability': predictions['churn_probability'].mean()
    }

    return predictions, None, metrics
