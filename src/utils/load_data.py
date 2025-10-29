"""
Data loading and caching for the dashboard.
Loads data from Snowflake or local CSV and processes it.
"""

import os
import pandas as pd
import pickle
from pathlib import Path
from datetime import datetime, timedelta
from .db_connector import DataConnector
from .data_processor import CXDataProcessor

# Use simple churn model for serverless deployments (no sklearn)
USE_SIMPLE_CHURN = os.getenv('USE_SIMPLE_CHURN', 'true').lower() == 'true'

if USE_SIMPLE_CHURN:
    from .churn_model_simple import build_churn_predictions
else:
    try:
        from .churn_model import build_churn_predictions
    except ImportError:
        # Fallback to simple model if sklearn not available
        from .churn_model_simple import build_churn_predictions


class DataLoader:
    """Centralized data loading and caching."""

    def __init__(self):
        """Initialize data loader."""
        self.master_df = None
        self.churn_predictions = None
        self.cohort_retention = None
        self.events_df = None
        self.processor = None
        self.loaded = False
        self.loading_stage = ""
        self.loading_progress = 0

        # Cache directories
        self.cache_dir = Path('data/processed')
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        self.model_dir = Path('models')
        self.model_dir.mkdir(parents=True, exist_ok=True)

    def _is_cache_valid(self, cache_file: Path, max_age_hours: int = 24) -> bool:
        """Check if cache file exists and is recent enough."""
        if not cache_file.exists():
            return False

        file_age = datetime.now() - datetime.fromtimestamp(cache_file.stat().st_mtime)
        return file_age < timedelta(hours=max_age_hours)

    def _load_from_cache(self) -> bool:
        """Try to load processed data from cache."""
        try:
            master_cache = self.cache_dir / 'master_df.pkl'
            cohort_cache = self.cache_dir / 'cohort_retention.pkl'
            events_cache = self.cache_dir / 'events_df.pkl'
            churn_cache = self.cache_dir / 'churn_predictions.pkl'

            # Check if all cache files are valid
            if not all([
                self._is_cache_valid(master_cache),
                self._is_cache_valid(cohort_cache),
                self._is_cache_valid(events_cache),
                self._is_cache_valid(churn_cache)
            ]):
                return False

            print("Loading from cache...")
            self.loading_stage = "Loading from cache..."
            self.loading_progress = 50

            # Load cached data using pickle
            self.master_df = pd.read_pickle(master_cache)
            self.cohort_retention = pd.read_pickle(cohort_cache)
            self.events_df = pd.read_pickle(events_cache)
            self.churn_predictions = pd.read_pickle(churn_cache)

            self.loading_stage = "Cache loaded successfully!"
            self.loading_progress = 100
            self.loaded = True
            print("✓ Data loaded from cache!")
            return True

        except Exception as e:
            print(f"Cache load failed: {e}")
            return False

    def _save_to_cache(self):
        """Save processed data to cache."""
        try:
            self.master_df.to_pickle(self.cache_dir / 'master_df.pkl')
            self.cohort_retention.to_pickle(self.cache_dir / 'cohort_retention.pkl')
            self.events_df.to_pickle(self.cache_dir / 'events_df.pkl')
            self.churn_predictions.to_pickle(self.cache_dir / 'churn_predictions.pkl')
            print("✓ Data cached to disk")
        except Exception as e:
            print(f"Cache save failed: {e}")

    def load_all_data(self) -> bool:
        """
        Load all data and process metrics.

        Returns:
            True if successful, False otherwise
        """
        try:
            # Try to load from cache first
            if self._load_from_cache():
                return True

            self.loading_stage = "Initializing..."
            self.loading_progress = 0
            print("Loading data...")

            # Load raw data
            self.loading_stage = "Loading data files..."
            self.loading_progress = 20
            with DataConnector() as db:
                users_df = db.load_users()
                events_df = db.load_events()

            print(f"✓ Loaded {len(users_df):,} users and {len(events_df):,} events")

            # Process data
            self.loading_stage = "Processing user metrics..."
            self.loading_progress = 40
            self.processor = CXDataProcessor(users_df, events_df)

            # Build master metrics table
            print("Processing user metrics...")
            self.master_df = self.processor.build_master_table()

            # Calculate cohort retention
            self.loading_stage = "Calculating cohort retention..."
            self.loading_progress = 60
            print("Calculating cohort retention...")
            self.cohort_retention = self.processor.calculate_cohort_retention()

            # Build churn predictions
            self.loading_stage = "Building churn predictions..."
            self.loading_progress = 80
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

            self.loading_stage = "Saving to cache..."
            self.loading_progress = 95

            # Save to cache for next time
            self._save_to_cache()

            self.loading_stage = "Complete!"
            self.loading_progress = 100
            self.loaded = True
            print("✓ Data loading complete!")

            return True

        except Exception as e:
            self.loading_stage = f"Error: {str(e)}"
            self.loading_progress = 0
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

        # Calculate revenue retention metrics
        retention_metrics = self.processor.calculate_revenue_retention_metrics()

        return {
            'total_users': len(df),
            'active_users': df[df['is_active'] == 1].shape[0],
            'inactive_users': df[df['is_active'] == 0].shape[0],
            'total_arr': df['annual_revenue'].sum(),  # Sum across all users (active + inactive)
            'avg_arr': df['annual_revenue'].mean(),  # Average across all users (active + inactive)
            'avg_nps': df['nps_score'].mean(),
            'health_distribution': df['health_tier'].value_counts().to_dict(),
            'plan_distribution': df['plan_type'].value_counts().to_dict(),
            'high_risk_users': df[df['churn_risk_tier'] == 'High'].shape[0],
            'renewal_risk_users': df[df['at_renewal_risk'] == 1].shape[0],
            'grr': retention_metrics['overall_grr'],  # Gross Revenue Retention %
            'nrr': retention_metrics['overall_nrr'],  # Net Revenue Retention %
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
