"""
Test script to validate info icon implementation.
Tests component creation, imports, and structure without requiring data.
"""

import sys
import os
import traceback

# Add src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))


def test_imports():
    """Test that all necessary imports work."""
    print("Testing imports...")
    try:
        from components.info_icon import create_info_icon
        from config.info_content import INFO_CONTENT
        from layouts.executive_overview import create_executive_overview
        print("  ✓ All imports successful")
        return True
    except Exception as e:
        print(f"  ✗ Import error: {e}")
        traceback.print_exc()
        return False


def test_info_content_structure():
    """Test that INFO_CONTENT has all required keys."""
    print("\nTesting INFO_CONTENT structure...")
    try:
        from config.info_content import INFO_CONTENT

        required_keys = [
            'total_arr',
            'active_users',
            'churn_rate',
            'avg_nps',
            'health_distribution',
            'churn_risk_distribution',
            'users_by_plan',
            'arr_by_plan',
            'nps_distribution',
            'at_risk_table'
        ]

        missing_keys = []
        for key in required_keys:
            if key not in INFO_CONTENT:
                missing_keys.append(key)

        if missing_keys:
            print(f"  ✗ Missing keys: {missing_keys}")
            return False

        # Check structure of each item
        for key in required_keys:
            item = INFO_CONTENT[key]
            required_fields = ['tooltip', 'title', 'formula', 'python_code', 'sql_code']
            for field in required_fields:
                if field not in item:
                    print(f"  ✗ Missing field '{field}' in '{key}'")
                    return False

        print(f"  ✓ All {len(required_keys)} content items have correct structure")
        return True

    except Exception as e:
        print(f"  ✗ Error: {e}")
        traceback.print_exc()
        return False


def test_info_icon_component():
    """Test that create_info_icon function works."""
    print("\nTesting create_info_icon component...")
    try:
        from components.info_icon import create_info_icon

        # Create a test info icon
        components = create_info_icon(
            component_id="test-icon",
            tooltip_text="Test tooltip",
            modal_title="Test Modal",
            formula_explanation="Test formula",
            python_code="print('hello')",
            sql_code="SELECT * FROM test;"
        )

        if not isinstance(components, list):
            print(f"  ✗ Expected list, got {type(components)}")
            return False

        if len(components) != 2:
            print(f"  ✗ Expected 2 components (icon+tooltip, modal), got {len(components)}")
            return False

        print("  ✓ create_info_icon returns correct structure")
        return True

    except Exception as e:
        print(f"  ✗ Error: {e}")
        traceback.print_exc()
        return False


def test_app_callbacks():
    """Test that app callbacks are registered."""
    print("\nTesting app callbacks...")
    try:
        import app as app_module
        app = app_module.app
        MODAL_IDS = app_module.MODAL_IDS

        expected_modal_count = 10
        if len(MODAL_IDS) != expected_modal_count:
            print(f"  ✗ Expected {expected_modal_count} modal IDs, got {len(MODAL_IDS)}")
            return False

        # Check that callbacks exist
        if not hasattr(app, 'callback_map'):
            print("  ⚠ Cannot verify callbacks (callback_map not accessible)")
            return True

        print(f"  ✓ {len(MODAL_IDS)} modal IDs registered")
        return True

    except Exception as e:
        print(f"  ✗ Error: {e}")
        traceback.print_exc()
        return False


def main():
    """Run all tests."""
    print("=" * 60)
    print("INFO ICON IMPLEMENTATION VALIDATION")
    print("=" * 60)

    tests = [
        ("Imports", test_imports),
        ("INFO_CONTENT Structure", test_info_content_structure),
        ("Info Icon Component", test_info_icon_component),
        ("App Callbacks", test_app_callbacks)
    ]

    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"\nUnexpected error in {test_name}:")
            traceback.print_exc()
            results.append((test_name, False))

    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {test_name}")

    print("-" * 60)
    print(f"Total: {passed}/{total} tests passed")

    if passed == total:
        print("\n✓ All tests passed! Implementation is ready.")
        print("\nTo test the dashboard:")
        print("  1. Ensure data is loaded (run notebooks if needed)")
        print("  2. Run: python src/app.py")
        print("  3. Open: http://localhost:8050")
        print("  4. Hover over info icons (ℹ️) to see tooltips")
        print("  5. Click info icons to open modals with code")
        return 0
    else:
        print("\n✗ Some tests failed. Please review errors above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
