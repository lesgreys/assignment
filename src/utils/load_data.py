"""
Data loading and caching for the dashboard (Optimized for serverless).
Implements tiered loading with Redis cache and Parquet format.
"""

import os
import pandas as pd
import pickle
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, Dict, Tuple
import logging

from .db_connector import DataConnector
from .data_processor import CXDataProcessor
from .cache_manager import get_cache_manager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
    """
    Centralized data loading with tiered caching.

    Tier 0 (Critical): Summary stats, health distribution (~100KB, <1s)
    Tier 1 (Essential): User table basic metrics (~2MB, 1-2s)
    Tier 2 (Analytics): Full metrics, cohort data, charts (~10MB, 2-3s)
    """

    # Cache namespaces
    CACHE_SUMMARY = "summary"
    CACHE_USERS = "users"
    CACHE_MASTER = "master"
    CACHE_COHORT = "cohort"
    CACHE_CHURN = "churn"
    CACHE_EVENTS = "events"
    CACHE_RAW = "raw"

    def __init__(self):
        """Initialize data loader with cache manager."""
        # Data storage
        self.master_df = None
        self.churn_predictions = None
        self.cohort_retention = None
        self.events_df = None
        self.users_df = None
        self.processor = None

        # Loading state
        self.loaded = False
        self.tier0_loaded = False  # Summary stats
        self.tier1_loaded = False  # User table
        self.tier2_loaded = False  # Full analytics
        self.loading_stage = ""
        self.loading_progress = 0

        # Cache manager (Redis + in-memory)
        self.cache = get_cache_manager()

        # Disk cache for local development (Parquet format)
        self.use_disk_cache = not os.getenv('VERCEL', False)
        if self.use_disk_cache:
            self.cache_dir = Path('data/processed')
            self.cache_dir.mkdir(parents=True, exist_ok=True)

    def _save_to_parquet(self, df: pd.DataFrame, filename: str):
        """Save DataFrame to Parquet format (50-70% smaller than pickle)."""
        if not self.use_disk_cache:
            return

        try:
            filepath = self.cache_dir / f'{filename}.parquet'
            # Convert object columns to string to avoid mixed type issues
            df_to_save = df.copy()
            for col in df_to_save.select_dtypes(include=['object']).columns:
                df_to_save[col] = df_to_save[col].astype(str)
            df_to_save.to_parquet(filepath, compression='snappy', index=False)
            size_mb = filepath.stat().st_size / (1024 * 1024)
            logger.info(f"Saved {filename}.parquet ({size_mb:.2f}MB)")
        except Exception as e:
            logger.error(f"Failed to save {filename}.parquet: {e}")

    def _load_from_parquet(self, filename: str, max_age_hours: int = 24) -> Optional[pd.DataFrame]:
        """Load DataFrame from Parquet format with age validation."""
        if not self.use_disk_cache:
            return None

        try:
            filepath = self.cache_dir / f'{filename}.parquet'
            if not filepath.exists():
                return None

            # Check age
            file_age = datetime.now() - datetime.fromtimestamp(filepath.stat().st_mtime)
            if file_age >= timedelta(hours=max_age_hours):
                logger.info(f"{filename}.parquet expired ({file_age.total_seconds()/3600:.1f}h old)")
                return None

            df = pd.read_parquet(filepath)
            logger.info(f"Loaded {filename}.parquet from disk cache - shape {df.shape}")
            return df
        except Exception as e:
            logger.error(f"Failed to load {filename}.parquet: {e}")
            return None

    def load_tier0_summary(self) -> Dict:
        """
        Load Tier 0: Critical summary statistics (fastest tier).

        Target: <1 second
        Size: ~100KB
        """
        if self.tier0_loaded:
            return self.get_summary_stats()

        logger.info("Loading Tier 0: Summary statistics...")
        self.loading_stage = "Loading summary..."
        self.loading_progress = 10

        # Try Redis cache first
        summary = self.cache.get(self.CACHE_SUMMARY, 'stats')
        if summary:
            logger.info("✓ Tier 0 loaded from Redis cache")
            self.tier0_loaded = True
            self.loading_progress = 33
            return summary

        # If not in cache, need to compute from master data
        # This will trigger full load
        return None

    def load_tier1_users(self) -> pd.DataFrame:
        """
        Load Tier 1: User table with basic metrics.

        Target: 1-2 seconds
        Size: ~2MB
        """
        if self.tier1_loaded and self.master_df is not None:
            return self.master_df

        logger.info("Loading Tier 1: User table...")
        self.loading_stage = "Loading users..."
        self.loading_progress = 20

        # Try Redis cache
        master_df = self.cache.get_dataframe(self.CACHE_MASTER, 'data')
        if master_df is not None:
            self.master_df = master_df
            self.tier1_loaded = True
            self.loading_progress = 66
            logger.info(f"✓ Tier 1 loaded from Redis - {len(master_df):,} users")
            return master_df

        # Try Parquet disk cache
        master_df = self._load_from_parquet('master_df', max_age_hours=24)
        if master_df is not None:
            self.master_df = master_df
            self.tier1_loaded = True
            self.loading_progress = 66

            # Populate Redis for next time
            self.cache.set_dataframe(self.CACHE_MASTER, 'data', master_df,
                                    ttl=self.cache.TTL_ESSENTIAL, to_memory=True)
            logger.info(f"✓ Tier 1 loaded from disk - {len(master_df):,} users")
            return master_df

        # Not in cache, return None to trigger full load
        return None

    def load_tier2_analytics(self) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        Load Tier 2: Full analytics (cohort retention, events).

        Target: 2-3 seconds
        Size: ~10MB
        """
        if self.tier2_loaded:
            return self.cohort_retention, self.events_df

        logger.info("Loading Tier 2: Full analytics...")
        self.loading_stage = "Loading analytics..."
        self.loading_progress = 70

        # Try Redis cache for cohort data
        cohort_df = self.cache.get_dataframe(self.CACHE_COHORT, 'data')
        events_df = self.cache.get_dataframe(self.CACHE_EVENTS, 'data')

        if cohort_df is not None and events_df is not None:
            self.cohort_retention = cohort_df
            self.events_df = events_df
            self.tier2_loaded = True
            self.loading_progress = 100
            logger.info("✓ Tier 2 loaded from Redis cache")
            return cohort_df, events_df

        # Try Parquet disk cache
        cohort_df = self._load_from_parquet('cohort_retention', max_age_hours=24)
        events_df = self._load_from_parquet('events_df', max_age_hours=24)

        if cohort_df is not None and events_df is not None:
            self.cohort_retention = cohort_df
            self.events_df = events_df
            self.tier2_loaded = True
            self.loading_progress = 100

            # Populate Redis
            self.cache.set_dataframe(self.CACHE_COHORT, 'data', cohort_df,
                                    ttl=self.cache.TTL_ANALYTICS, to_memory=False)
            self.cache.set_dataframe(self.CACHE_EVENTS, 'data', events_df,
                                    ttl=self.cache.TTL_ANALYTICS, to_memory=False)
            logger.info("✓ Tier 2 loaded from disk cache")
            return cohort_df, events_df

        # Not in cache, return None
        return None, None

    def load_all_data(self, force_recompute: bool = False) -> bool:
        """
        Load all data with tiered caching strategy.

        Args:
            force_recompute: If True, bypass all caches and recompute

        Returns:
            True if successful, False otherwise
        """
        try:
            # Check if already loaded
            if self.loaded and not force_recompute:
                return True

            logger.info("=" * 60)
            logger.info("DATA LOADING PIPELINE START")
            logger.info("=" * 60)

            # Try tiered cache loading first
            if not force_recompute:
                master_df = self.load_tier1_users()
                if master_df is not None:
                    # Tier 1 loaded, try Tier 2
                    cohort_df, events_df = self.load_tier2_analytics()

                    # Try Tier 0
                    summary = self.load_tier0_summary()

                    if cohort_df is not None and events_df is not None:
                        # All tiers loaded from cache!
                        logger.info("=" * 60)
                        logger.info("✓ ALL DATA LOADED FROM CACHE (2-3s)")
                        logger.info("=" * 60)
                        self.loaded = True
                        self.tier0_loaded = True
                        self.tier1_loaded = True
                        self.tier2_loaded = True
                        self.loading_progress = 100
                        self.loading_stage = "Complete (from cache)!"

                        # Recreate processor if needed
                        users_df = self.cache.get_dataframe(self.CACHE_RAW, 'users')
                        if users_df is not None and events_df is not None:
                            self.users_df = users_df
                            self.processor = CXDataProcessor(users_df, events_df)

                        return True

            # Cache miss or force recompute - full pipeline
            logger.info("Cache miss - running full data processing pipeline")
            self.loading_stage = "Initializing..."
            self.loading_progress = 0

            # Load raw data
            self.loading_stage = "Loading data files..."
            self.loading_progress = 10
            logger.info("Loading raw CSV files...")

            with DataConnector() as db:
                users_df = db.load_users()
                events_df = db.load_events()

            logger.info(f"✓ Loaded {len(users_df):,} users and {len(events_df):,} events")
            self.users_df = users_df
            self.events_df = events_df

            # Cache raw data
            self.cache.set_dataframe(self.CACHE_RAW, 'users', users_df,
                                    ttl=self.cache.TTL_HISTORICAL, to_memory=False)

            # Process data
            self.loading_stage = "Processing user metrics..."
            self.loading_progress = 30
            logger.info("Processing user metrics...")

            self.processor = CXDataProcessor(users_df, events_df)
            self.master_df = self.processor.build_master_table()

            logger.info(f"✓ Processed {len(self.master_df):,} user records")

            # Calculate cohort retention
            self.loading_stage = "Calculating cohort retention..."
            self.loading_progress = 60
            logger.info("Calculating cohort retention...")
            self.cohort_retention = self.processor.calculate_cohort_retention()

            # Build churn predictions
            self.loading_stage = "Building churn predictions..."
            self.loading_progress = 75
            logger.info("Building churn predictions...")
            self.churn_predictions, self.churn_model, self.churn_metrics = build_churn_predictions(
                self.master_df
            )

            # Merge churn predictions into master
            self.master_df = self.master_df.merge(
                self.churn_predictions[['user_id', 'churn_probability', 'churn_risk_tier']],
                on='user_id',
                how='left'
            )

            # Cache all tiers
            self.loading_stage = "Caching data..."
            self.loading_progress = 90
            logger.info("Caching processed data...")

            # Tier 1: Master DataFrame (Redis + Disk)
            self.cache.set_dataframe(self.CACHE_MASTER, 'data', self.master_df,
                                    ttl=self.cache.TTL_ESSENTIAL, to_redis=True, to_memory=True)
            self._save_to_parquet(self.master_df, 'master_df')

            # Tier 2: Analytics DataFrames (Redis + Disk)
            self.cache.set_dataframe(self.CACHE_COHORT, 'data', self.cohort_retention,
                                    ttl=self.cache.TTL_ANALYTICS, to_redis=True, to_memory=False)
            self._save_to_parquet(self.cohort_retention, 'cohort_retention')

            self.cache.set_dataframe(self.CACHE_EVENTS, 'data', events_df,
                                    ttl=self.cache.TTL_ANALYTICS, to_redis=True, to_memory=False)
            self._save_to_parquet(events_df, 'events_df')

            # Churn predictions (smaller, keep in memory)
            self.cache.set_dataframe(self.CACHE_CHURN, 'predictions', self.churn_predictions,
                                    ttl=self.cache.TTL_ESSENTIAL, to_redis=True, to_memory=True)
            self._save_to_parquet(self.churn_predictions, 'churn_predictions')

            # Additional data for cache recreation
            self._save_to_parquet(users_df, 'users_df')

            # Tier 0: Summary stats (very small, cache in Redis)
            summary = self._compute_summary_stats()
            self.cache.set(self.CACHE_SUMMARY, 'stats', summary,
                          ttl=self.cache.TTL_CRITICAL, to_redis=True, to_memory=True)

            # Mark all tiers as loaded
            self.tier0_loaded = True
            self.tier1_loaded = True
            self.tier2_loaded = True
            self.loaded = True
            self.loading_stage = "Complete!"
            self.loading_progress = 100

            logger.info("=" * 60)
            logger.info("✓ DATA LOADING COMPLETE")
            logger.info(f"  Users: {len(self.master_df):,}")
            logger.info(f"  Events: {len(events_df):,}")
            logger.info(f"  Cohorts: {len(self.cohort_retention):,}")
            logger.info(f"  Cache: {self.cache.get_stats()}")
            logger.info("=" * 60)

            return True

        except Exception as e:
            self.loading_stage = f"Error: {str(e)}"
            self.loading_progress = 0
            logger.error(f"✗ Error loading data: {e}")
            import traceback
            traceback.print_exc()
            return False

    def _compute_summary_stats(self) -> Dict:
        """Compute summary statistics (Tier 0)."""
        df = self.master_df

        # Ensure processor is available
        if self.processor is None and self.users_df is not None and self.events_df is not None:
            self.processor = CXDataProcessor(self.users_df, self.events_df)

        # Calculate revenue retention metrics
        retention_metrics = self.processor.calculate_revenue_retention_metrics()

        return {
            'total_users': int(len(df)),
            'active_users': int(df[df['is_active'] == 1].shape[0]),
            'inactive_users': int(df[df['is_active'] == 0].shape[0]),
            'total_arr': float(df['annual_revenue'].sum()),
            'avg_arr': float(df['annual_revenue'].mean()),
            'avg_nps': float(df['nps_score'].mean()),
            'health_distribution': {k: int(v) for k, v in df['health_tier'].value_counts().to_dict().items()},
            'plan_distribution': {k: int(v) for k, v in df['plan_type'].value_counts().to_dict().items()},
            'high_risk_users': int(df[df['churn_risk_tier'] == 'High'].shape[0]),
            'renewal_risk_users': int(df[df['at_renewal_risk'] == 1].shape[0]),
            'grr': float(retention_metrics['overall_grr']),
            'nrr': float(retention_metrics['overall_nrr']),
        }

    def get_master_data(self) -> pd.DataFrame:
        """Get master user metrics table (Tier 1)."""
        if not self.tier1_loaded:
            self.load_all_data()
        return self.master_df

    def get_events_data(self) -> pd.DataFrame:
        """Get events data (Tier 2)."""
        if not self.tier2_loaded:
            self.load_all_data()
        return self.events_df

    def get_cohort_retention(self) -> pd.DataFrame:
        """Get cohort retention data (Tier 2)."""
        if not self.tier2_loaded:
            self.load_all_data()
        return self.cohort_retention

    def get_summary_stats(self) -> Dict:
        """Get summary statistics (Tier 0)."""
        # Try cache first
        if self.tier0_loaded:
            summary = self.cache.get(self.CACHE_SUMMARY, 'stats')
            if summary:
                return summary

        # Otherwise compute
        if not self.loaded:
            self.load_all_data()

        return self._compute_summary_stats()

    def invalidate_cache(self):
        """Invalidate all caches (force reload on next access)."""
        logger.info("Invalidating all caches...")
        self.cache.invalidate_namespace(self.CACHE_SUMMARY)
        self.cache.invalidate_namespace(self.CACHE_USERS)
        self.cache.invalidate_namespace(self.CACHE_MASTER)
        self.cache.invalidate_namespace(self.CACHE_COHORT)
        self.cache.invalidate_namespace(self.CACHE_CHURN)
        self.cache.invalidate_namespace(self.CACHE_EVENTS)
        self.cache.invalidate_namespace(self.CACHE_RAW)

        self.loaded = False
        self.tier0_loaded = False
        self.tier1_loaded = False
        self.tier2_loaded = False
        logger.info("✓ Cache invalidated")

    def get_cache_stats(self) -> Dict:
        """Get cache performance statistics."""
        return self.cache.get_stats()


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
    import time

    loader = DataLoader()

    print("\n" + "=" * 60)
    print("TESTING DATA LOADER")
    print("=" * 60)

    # Test cold start
    start = time.time()
    if loader.load_all_data():
        elapsed = time.time() - start
        print(f"\n✓ Cold start completed in {elapsed:.2f}s")

        print("\n=== Summary Stats ===")
        stats = loader.get_summary_stats()
        for key, value in stats.items():
            print(f"{key}: {value}")

        print(f"\n=== Cache Stats ===")
        cache_stats = loader.get_cache_stats()
        for key, value in cache_stats.items():
            print(f"{key}: {value}")

    # Test warm start (simulate new instance)
    print("\n" + "=" * 60)
    print("TESTING WARM START (NEW INSTANCE)")
    print("=" * 60)

    loader2 = DataLoader()
    start = time.time()
    if loader2.load_all_data():
        elapsed = time.time() - start
        print(f"\n✓ Warm start completed in {elapsed:.2f}s")
        print(f"   Target: <5s, Achieved: {elapsed:.2f}s {'✓' if elapsed < 5 else '✗'}")
