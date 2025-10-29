"""
Churn Prediction Model
Predicts customer churn risk using machine learning.
"""

import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import classification_report, roc_auc_score, confusion_matrix
from typing import Tuple, Dict


class ChurnPredictor:
    """Build and apply churn prediction model."""

    def __init__(self, model_type='random_forest'):
        """
        Initialize churn predictor.

        Args:
            model_type: 'random_forest' or 'logistic_regression'
        """
        self.model_type = model_type
        self.model = None
        self.scaler = StandardScaler()
        self.feature_columns = None
        self.feature_importance = None

    def prepare_features(self, master_df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.Series]:
        """
        Prepare features for modeling.

        Args:
            master_df: Master user metrics table

        Returns:
            Tuple of (features DataFrame, target Series)
        """
        df = master_df.copy()

        # Define churn: inactive users or those who cancelled
        # For this dataset, use is_active as proxy for churn
        df['churned'] = (df['is_active'] == 0).astype(int)

        # Feature selection
        feature_cols = [
            # Demographics
            'account_age_days',
            'portfolio_size',
            'annual_revenue',
            'success_manager_assigned',

            # Usage metrics
            'active_days_30d',
            'active_days_60d',
            'active_days_90d',
            'logins_30d',
            'avg_session_30d',
            'total_events',
            'events_30d',
            'events_60d',
            'days_since_last_activity',

            # Core actions
            'property_added_count',
            'tenant_added_count',
            'lease_signed_count',
            'payments_received',
            'report_generated_count',

            # Engagement
            'unique_features',
            'trainings_attended',

            # Sentiment
            'nps_score',
            'support_tickets_last_90d',

            # Health scores
            'health_score',
            'usage_component',
            'business_value_component',
            'sentiment_component',
            'engagement_component',
        ]

        # Add plan type dummies
        plan_dummies = pd.get_dummies(df['plan_type'], prefix='plan')
        df = pd.concat([df, plan_dummies], axis=1)
        feature_cols.extend(plan_dummies.columns.tolist())

        # Calculate engagement decline
        df['engagement_declining'] = (df['events_30d'] < df['events_60d']).astype(int)
        feature_cols.append('engagement_declining')

        # Filter to only include available columns
        available_cols = [col for col in feature_cols if col in df.columns]
        self.feature_columns = available_cols

        X = df[available_cols].fillna(0)
        y = df['churned']

        return X, y

    def train(self, X: pd.DataFrame, y: pd.Series) -> Dict:
        """
        Train the churn prediction model.

        Args:
            X: Features
            y: Target (churned)

        Returns:
            Dictionary with model performance metrics
        """
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.3, random_state=42, stratify=y
        )

        # Scale features
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)

        # Train model
        if self.model_type == 'random_forest':
            self.model = RandomForestClassifier(
                n_estimators=100,
                max_depth=10,
                min_samples_split=20,
                random_state=42,
                class_weight='balanced'
            )
        else:
            self.model = LogisticRegression(
                random_state=42,
                max_iter=1000,
                class_weight='balanced'
            )

        self.model.fit(X_train_scaled, y_train)

        # Evaluate
        y_pred = self.model.predict(X_test_scaled)
        y_pred_proba = self.model.predict_proba(X_test_scaled)[:, 1]

        # Calculate metrics
        metrics = {
            'accuracy': self.model.score(X_test_scaled, y_test),
            'roc_auc': roc_auc_score(y_test, y_pred_proba),
            'classification_report': classification_report(y_test, y_pred, output_dict=True),
            'confusion_matrix': confusion_matrix(y_test, y_pred).tolist()
        }

        # Feature importance
        if self.model_type == 'random_forest':
            self.feature_importance = pd.DataFrame({
                'feature': X.columns,
                'importance': self.model.feature_importances_
            }).sort_values('importance', ascending=False)
        else:
            self.feature_importance = pd.DataFrame({
                'feature': X.columns,
                'importance': np.abs(self.model.coef_[0])
            }).sort_values('importance', ascending=False)

        return metrics

    def predict(self, X: pd.DataFrame) -> pd.DataFrame:
        """
        Predict churn probability for users.

        Args:
            X: Features DataFrame

        Returns:
            DataFrame with user_id, churn_probability, risk_tier
        """
        if self.model is None:
            raise ValueError("Model not trained. Call train() first.")

        # Ensure features match training
        X_pred = X[self.feature_columns].fillna(0)
        X_scaled = self.scaler.transform(X_pred)

        # Predict probabilities
        proba = self.model.predict_proba(X_scaled)[:, 1]

        # Create results DataFrame
        results = pd.DataFrame({
            'churn_probability': proba
        })

        # Classify risk tier
        results['churn_risk_tier'] = pd.cut(
            results['churn_probability'],
            bins=[-0.01, 0.4, 0.7, 1.0],
            labels=['Low', 'Medium', 'High']
        )

        return results

    def get_feature_importance(self, top_n=15) -> pd.DataFrame:
        """Get top N most important features."""
        if self.feature_importance is None:
            raise ValueError("Model not trained yet.")

        return self.feature_importance.head(top_n)

    def get_model_summary(self) -> Dict:
        """Get model configuration summary."""
        return {
            'model_type': self.model_type,
            'n_features': len(self.feature_columns) if self.feature_columns else 0,
            'features': self.feature_columns,
            'is_trained': self.model is not None
        }


def build_churn_predictions(master_df: pd.DataFrame) -> pd.DataFrame:
    """
    Build churn predictions for all users.

    Args:
        master_df: Master user metrics table

    Returns:
        DataFrame with churn predictions
    """
    predictor = ChurnPredictor(model_type='random_forest')

    # Prepare data
    X, y = predictor.prepare_features(master_df)

    # Train model
    metrics = predictor.train(X, y)

    print("\n=== Churn Model Performance ===")
    print(f"ROC-AUC Score: {metrics['roc_auc']:.3f}")
    print(f"Accuracy: {metrics['accuracy']:.3f}")
    print("\nTop 10 Important Features:")
    print(predictor.get_feature_importance(10))

    # Predict on all users
    predictions = predictor.predict(X)

    # Add user_id
    predictions['user_id'] = master_df['user_id'].values

    return predictions, predictor, metrics
