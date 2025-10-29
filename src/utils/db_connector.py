"""
Database connector utility for Snowflake and local data sources.
Supports both Snowflake connection and local CSV files.
"""

import os
import pandas as pd
from dotenv import load_dotenv
from typing import Optional, Dict, Any

# Make snowflake import optional for deployments without it
try:
    import snowflake.connector
    SNOWFLAKE_AVAILABLE = True
except ImportError:
    SNOWFLAKE_AVAILABLE = False

# Load environment variables
load_dotenv()


class DataConnector:
    """Handle data loading from Snowflake or local CSV files."""

    def __init__(self, use_local: bool = None):
        """
        Initialize the data connector.

        Args:
            use_local: If True, use local CSV files. If None, check environment variable.
        """
        if use_local is None:
            use_local = os.getenv('USE_LOCAL_DATA', 'false').lower() == 'true'

        self.use_local = use_local
        self.conn = None

        if not self.use_local:
            self._connect_snowflake()

    def _connect_snowflake(self):
        """Establish connection to Snowflake."""
        if not SNOWFLAKE_AVAILABLE:
            print("✗ Snowflake connector not available")
            print("  Falling back to local data mode...")
            self.use_local = True
            return

        try:
            # Build connection parameters
            conn_params = {
                'account': os.getenv('SNOWFLAKE_ACCOUNT'),
                'user': os.getenv('SNOWFLAKE_USER'),
                'warehouse': os.getenv('SNOWFLAKE_WAREHOUSE'),
                'database': os.getenv('SNOWFLAKE_DATABASE'),
                'schema': os.getenv('SNOWFLAKE_SCHEMA'),
                'role': os.getenv('SNOWFLAKE_ROLE')
            }

            # Add authenticator if specified (e.g., externalbrowser for SSO)
            authenticator = os.getenv('SNOWFLAKE_AUTHENTICATOR')
            if authenticator:
                conn_params['authenticator'] = authenticator
            else:
                # Use password authentication if no authenticator specified
                conn_params['password'] = os.getenv('SNOWFLAKE_PASSWORD')

            self.conn = snowflake.connector.connect(**conn_params)
            print("✓ Successfully connected to Snowflake")
        except Exception as e:
            print(f"✗ Failed to connect to Snowflake: {e}")
            print("  Falling back to local data mode...")
            self.use_local = True

    def execute_query(self, query: str) -> pd.DataFrame:
        """
        Execute a SQL query and return results as DataFrame.

        Args:
            query: SQL query string

        Returns:
            DataFrame with query results
        """
        if self.use_local:
            raise ValueError("Cannot execute custom queries in local mode")

        cursor = self.conn.cursor()
        cursor.execute(query)
        df = cursor.fetch_pandas_all()
        cursor.close()
        return df

    def load_users(self) -> pd.DataFrame:
        """Load users table."""
        if self.use_local:
            # Check if DATA_URL is set (for remote CSV files)
            data_url = os.getenv('DATA_URL')
            if data_url:
                file_path = f"{data_url}/users_cx.csv"
            else:
                file_path = os.path.join(
                    os.getenv('DATA_PATH', './data/raw/'),
                    'users_cx.csv'
                )
            df = pd.read_csv(file_path)
            # Convert date columns (handle DD/MM/YYYY format)
            df['signup_date'] = pd.to_datetime(df['signup_date'], dayfirst=True, format='mixed')
            df['renewal_due_date'] = pd.to_datetime(df['renewal_due_date'], dayfirst=True, format='mixed')
            return df
        else:
            query = "SELECT * FROM users_cx"
            return self.execute_query(query)

    def load_events(self) -> pd.DataFrame:
        """Load events table."""
        if self.use_local:
            # Check if DATA_URL is set (for remote CSV files)
            data_url = os.getenv('DATA_URL')
            if data_url:
                file_path = f"{data_url}/events_cx_clean.csv"
            else:
                file_path = os.path.join(
                    os.getenv('DATA_PATH', './data/raw/'),
                    'events_cx_clean.csv'
                )
            df = pd.read_csv(file_path)
            # Convert timestamp column (handle DD/MM/YYYY HH:MM:SS format)
            df['event_ts'] = pd.to_datetime(df['event_ts'], dayfirst=True, format='mixed')
            return df
        else:
            query = "SELECT * FROM events_cx_clean"
            return self.execute_query(query)

    def close(self):
        """Close database connection."""
        if self.conn:
            self.conn.close()
            print("✓ Snowflake connection closed")

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()


def test_connection():
    """Test the database connection."""
    with DataConnector() as db:
        try:
            users = db.load_users()
            events = db.load_events()
            print(f"\n✓ Successfully loaded data:")
            print(f"  - Users: {len(users):,} records")
            print(f"  - Events: {len(events):,} records")
            return True
        except Exception as e:
            print(f"\n✗ Error loading data: {e}")
            return False


if __name__ == "__main__":
    test_connection()
