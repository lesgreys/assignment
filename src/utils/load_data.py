"""
Data loading and caching for the dashboard.
Loads data from Snowflake or local CSV and processes it.
"""

import os
import pandas as pd
from .db_connector import DataConnector
from .data_processor import CXDataProcessor
from .churn_model import build_churn_predictions


class DataLoader:
    """Centralized data loading and caching."""

    def __init__(self):
        """Initialize data loader."""
        self.master_df = None
        self.churn_predictions = None
        self.cohort_retention = None
        self.events_df = None
        self.loaded = False

    def load_all_data(self) -> bool:
        """
        Load all data and process metrics.

        Returns:
            True if successful, False otherwise
        """
        try:
            print("Loading data...")

            # Load raw data
            with DataConnector() as db:
                users_df = db.load_users()
                events_df = db.load_events()

            print(f"✓ Loaded {len(users_df):,} users and {len(events_df):,} events")

            # Process data
            processor = CXDataProcessor(users_df, events_df)

            # Build master metrics table
            print("Processing user metrics...")
            self.master_df = processor.build_master_table()

            # Calculate cohort retention
            print("Calculating cohort retention...")
            self.cohort_retention = processor.calculate_cohort_retention()

            # Build churn predictions
            print("Training churn prediction model...")
            self.churn_predictions, self.churn_model, self.churn_metrics = build_churn_predictions(
                self.master_df
            )

            # Merge churn predictions into master
            self.master_df = self.master_df.merge(
                self.churn_predictions[['user_id', 'churn_probability', 'churn_risk_tier']],
                on='user_id',
                how='left'
            )

            # Store events for detailed analysis
            self.events_df = events_df

            self.loaded = True
            print("✓ Data loading complete!")

            return True

        except Exception as e:
            print(f"✗ Error loading data: {e}")
            import traceback
            traceback.print_exc()
            return False

    def get_master_data(self) -> pd.DataFrame:
        """Get master user metrics table."""
        if not self.loaded:
            self.load_all_data()
        return self.master_df

    def get_events_data(self) -> pd.DataFrame:
        """Get events data."""
        if not self.loaded:
            self.load_all_data()
        return self.events_df

    def get_cohort_retention(self) -> pd.DataFrame:
        """Get cohort retention data."""
        if not self.loaded:
            self.load_all_data()
        return self.cohort_retention

    def get_summary_stats(self) -> dict:
        """Get summary statistics."""
        if not self.loaded:
            self.load_all_data()

        df = self.master_df

        return {
            'total_users': len(df),
            'active_users': df[df['is_active'] == 1].shape[0],
            'inactive_users': df[df['is_active'] == 0].shape[0],
            'total_arr': df['annual_revenue'].sum(),
            'avg_arr': df['annual_revenue'].mean(),
            'avg_nps': df['nps_score'].mean(),
            'health_distribution': df['health_tier'].value_counts().to_dict(),
            'plan_distribution': df['plan_type'].value_counts().to_dict(),
            'high_risk_users': df[df['churn_risk_tier'] == 'High'].shape[0],
            'renewal_risk_users': df[df['at_renewal_risk'] == 1].shape[0],
        }


# Global data loader instance
_data_loader = None


def get_data_loader() -> DataLoader:
    """Get or create global data loader instance."""
    global _data_loader
    if _data_loader is None:
        _data_loader = DataLoader()
    return _data_loader


if __name__ == "__main__":
    # Test data loading
    loader = DataLoader()
    if loader.load_all_data():
        print("\n=== Summary Stats ===")
        stats = loader.get_summary_stats()
        for key, value in stats.items():
            print(f"{key}: {value}")
