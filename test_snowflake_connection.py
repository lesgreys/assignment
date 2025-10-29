#!/usr/bin/env python3
"""
Test Snowflake connection with different configurations.
Run this to troubleshoot connection issues.
"""

import os
from dotenv import load_dotenv

load_dotenv()

def test_connection_method(account_format, description):
    """Test a specific connection configuration."""
    print(f"\n{'='*60}")
    print(f"Testing: {description}")
    print(f"Account: {account_format}")
    print('='*60)

    try:
        import snowflake.connector

        conn = snowflake.connector.connect(
            account=account_format,
            user=os.getenv('SNOWFLAKE_USER'),
            authenticator='externalbrowser',
            warehouse=os.getenv('SNOWFLAKE_WAREHOUSE'),
            database=os.getenv('SNOWFLAKE_DATABASE'),
            schema=os.getenv('SNOWFLAKE_SCHEMA'),
            role=os.getenv('SNOWFLAKE_ROLE')
        )

        print("✓ Connection successful!")

        # Test query
        cursor = conn.cursor()
        cursor.execute("SELECT CURRENT_VERSION()")
        version = cursor.fetchone()[0]
        print(f"✓ Snowflake version: {version}")

        # Check tables
        cursor.execute("SHOW TABLES")
        tables = cursor.fetchall()
        print(f"✓ Found {len(tables)} tables in {os.getenv('SNOWFLAKE_DATABASE')}.{os.getenv('SNOWFLAKE_SCHEMA')}")

        for table in tables:
            print(f"  - {table[1]}")  # table name

        cursor.close()
        conn.close()

        print(f"\n✓✓✓ SUCCESS with account format: {account_format} ✓✓✓")
        print(f"\nUpdate your .env file to use:")
        print(f"SNOWFLAKE_ACCOUNT={account_format}")
        return True

    except Exception as e:
        print(f"✗ Failed: {e}")
        return False


def main():
    """Test different account identifier formats."""
    print("Snowflake Connection Troubleshooter")
    print("=" * 60)

    user = os.getenv('SNOWFLAKE_USER')
    database = os.getenv('SNOWFLAKE_DATABASE')

    print(f"User: {user}")
    print(f"Database: {database}")
    print(f"Authentication: externalbrowser (SSO)")

    # Try different account formats
    test_configs = [
        ("HEWZYWQ", "Account locator only (common for SSO)"),
        ("HEWZYWQ.LXC32669", "Account locator with region (dot separator)"),
        ("HEWZYWQ-LXC32669", "Full account identifier (hyphen separator)"),
    ]

    success = False
    for account, description in test_configs:
        if test_connection_method(account, description):
            success = True
            break

    if not success:
        print("\n" + "="*60)
        print("❌ All connection attempts failed")
        print("="*60)
        print("\nPossible solutions:")
        print("\n1. Check your Snowflake account URL")
        print("   - Log into Snowflake web UI")
        print("   - The URL format is: https://<account_identifier>.snowflakecomputing.com")
        print("   - Use the account identifier from the URL")

        print("\n2. Verify SSO configuration")
        print("   - Contact your Snowflake admin to confirm SSO is enabled")
        print("   - Verify your user has 'externalbrowser' authentication enabled")

        print("\n3. Try username/password authentication")
        print("   - In .env, remove: SNOWFLAKE_AUTHENTICATOR=externalbrowser")
        print("   - Add: SNOWFLAKE_PASSWORD=your_password")

        print("\n4. Use local CSV files instead")
        print("   - Export your Snowflake tables to CSV")
        print("   - Place in data/raw/ directory")
        print("   - In .env, set: USE_LOCAL_DATA=true")

        print("\n5. Check the original config file")
        print("   - The config you provided had: HEWZYWQ-LXC32669")
        print("   - Try checking Snowflake SnowSQL config or connection strings")


if __name__ == "__main__":
    main()
